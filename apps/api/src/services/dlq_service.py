"""
Emlak Teknoloji Platformu - Dead Letter Queue (DLQ) Service

Dead letter durumundaki outbox event'lerini yoneten servis.
Admin panelden DLQ event'lerini listeleme, retry ve temizleme isleri.

KIRMIZI CIZGILER:
    - retry_single/retry_all: retry_count SIFIRLANMAZ (toplam deneme korunmali)
    - purge: older_than_hours parametresi ZORUNLU (yeni event'ler silinmesin)
    - RLS: Admin endpoint'leri RLS bypass'li session kullanir
      (platform_admin tum tenant'larin DLQ'sunu gorebilmeli)

Kullanim:
    dlq_service = DLQService(async_session_factory)
    dead_letters = await dlq_service.list_dead_letters(limit=50, offset=0)

Referans: TASK-041
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class DLQService:
    """
    Dead Letter Queue yonetim servisi.

    Sorumluluklar:
        - DLQ event'lerini listeleme ve sayma
        - Tek/toplu retry (retry_count KORUNUR)
        - Eski event'leri temizleme (older_than_hours ile guvenli purge)
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_dead_letters(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: str | None = None,
    ) -> list[dict]:
        """
        Dead letter durumundaki event'leri listeler.

        Args:
            limit: Sayfa basina kayit sayisi (max 100).
            offset: Baslangic noktasi.
            event_type: Opsiyonel filtre — sadece belirli event tipi.

        Returns:
            Dead letter event listesi (dict).
        """
        limit = min(limit, 100)

        # Dinamik WHERE filtresi
        where_clause = "WHERE status = 'dead_letter'"
        params: dict = {"limit": limit, "offset": offset}

        if event_type:
            where_clause += " AND event_type = :event_type"
            params["event_type"] = event_type

        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                text(
                    f"SELECT id, office_id, event_type, aggregate_type, "
                    f"       aggregate_id, payload, status, retry_count, "
                    f"       max_retries, error_message, created_at, updated_at "
                    f"FROM outbox_events "
                    f"{where_clause} "
                    f"ORDER BY created_at DESC "
                    f"LIMIT :limit OFFSET :offset"
                ),
                params,
            )
            rows = result.fetchall()

        return [
            {
                "id": str(row.id),
                "office_id": str(row.office_id),
                "event_type": row.event_type,
                "aggregate_type": row.aggregate_type,
                "aggregate_id": str(row.aggregate_id),
                "payload": row.payload,
                "status": row.status,
                "retry_count": row.retry_count,
                "max_retries": row.max_retries,
                "error_message": row.error_message,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ]

    async def count_dead_letters(
        self,
        event_type: str | None = None,
    ) -> dict:
        """
        Dead letter event sayisini dondurur.

        Args:
            event_type: Opsiyonel filtre.

        Returns:
            {"total": int, "by_event_type": {str: int}}
        """
        async with self._session_factory() as session, session.begin():
            # Toplam sayi
            where_clause = "WHERE status = 'dead_letter'"
            params: dict = {}

            if event_type:
                where_clause += " AND event_type = :event_type"
                params["event_type"] = event_type

            total_result = await session.execute(
                text(
                    f"SELECT COUNT(*) as total FROM outbox_events "
                    f"{where_clause}"
                ),
                params,
            )
            total = total_result.scalar() or 0

            # Event tipi bazinda dagilim
            breakdown_result = await session.execute(
                text(
                    "SELECT event_type, COUNT(*) as count "
                    "FROM outbox_events "
                    "WHERE status = 'dead_letter' "
                    "GROUP BY event_type "
                    "ORDER BY count DESC"
                ),
            )
            by_event_type = {
                row.event_type: row.count
                for row in breakdown_result.fetchall()
            }

        return {
            "total": total,
            "by_event_type": by_event_type,
        }

    async def retry_single(self, event_id: str) -> bool:
        """
        Tek bir dead letter event'i retry'a geri gonderir.

        ONEMLI: retry_count SIFIRLANMAZ!
            Toplam deneme sayisi korunur. Sadece status 'pending'e
            donusturulur ve worker bir sonraki poll'da alir.

        Args:
            event_id: Retry edilecek event UUID'si.

        Returns:
            True basarili, False event bulunamadi veya dead_letter degil.
        """
        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                text(
                    "UPDATE outbox_events "
                    "SET status = 'pending', "
                    "    next_retry_at = NULL, "
                    "    locked_at = NULL, "
                    "    locked_by = NULL, "
                    "    error_message = error_message || ' [DLQ retry at "
                    "' || now()::text || ']' "
                    "WHERE id = :event_id "
                    "  AND status = 'dead_letter' "
                    "RETURNING id"
                ),
                {"event_id": event_id},
            )
            updated = result.fetchone()

        if updated:
            logger.info("DLQ retry: event_id=%s pending'e donduruldu", event_id)
            return True

        logger.warning(
            "DLQ retry basarisiz: event_id=%s bulunamadi veya dead_letter degil",
            event_id,
        )
        return False

    async def retry_all(
        self,
        event_type: str | None = None,
    ) -> int:
        """
        Tum dead letter event'leri retry'a geri gonderir.

        ONEMLI: retry_count SIFIRLANMAZ!
            Toplam deneme sayisi korunur. Worker'lar event'leri
            aldiginda, kalan retry hakki kadar deneyecek.

        Args:
            event_type: Opsiyonel filtre — sadece belirli event tipi.

        Returns:
            Retry'a gonderilen event sayisi.
        """
        where_clause = "WHERE status = 'dead_letter'"
        params: dict = {}

        if event_type:
            where_clause += " AND event_type = :event_type"
            params["event_type"] = event_type

        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                text(
                    f"UPDATE outbox_events "
                    f"SET status = 'pending', "
                    f"    next_retry_at = NULL, "
                    f"    locked_at = NULL, "
                    f"    locked_by = NULL, "
                    f"    error_message = error_message || ' [DLQ bulk retry at "
                    f"' || now()::text || ']' "
                    f"{where_clause} "
                    f"RETURNING id"
                ),
                params,
            )
            updated_rows = result.fetchall()
            count = len(updated_rows)

        logger.info(
            "DLQ bulk retry: %d event pending'e donduruldu (filtre=%s)",
            count,
            event_type or "*",
        )
        return count

    async def purge(
        self,
        older_than_hours: int = 168,
        event_type: str | None = None,
    ) -> int:
        """
        Eski dead letter event'leri kalici olarak siler.

        GUVENLIK: older_than_hours parametresi ZORUNLU.
            Yeni event'lerin yanlis silinmesini engeller.
            Varsayilan: 168 saat (7 gun) — bir haftadan eski event'ler silinir.

        Args:
            older_than_hours: Bu saatten eski event'ler silinir (min: 1).
            event_type: Opsiyonel filtre.

        Returns:
            Silinen event sayisi.
        """
        # Guvenlik: minimum 1 saat
        older_than_hours = max(older_than_hours, 1)

        where_clause = (
            "WHERE status = 'dead_letter' "
            "  AND created_at < now() - interval '1 hour' * :hours"
        )
        params: dict = {"hours": older_than_hours}

        if event_type:
            where_clause += " AND event_type = :event_type"
            params["event_type"] = event_type

        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                text(
                    f"DELETE FROM outbox_events "
                    f"{where_clause} "
                    f"RETURNING id"
                ),
                params,
            )
            deleted_rows = result.fetchall()
            count = len(deleted_rows)

        logger.info(
            "DLQ purge: %d event silindi (older_than_hours=%d, filtre=%s)",
            count,
            older_than_hours,
            event_type or "*",
        )
        return count
