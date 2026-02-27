"""
Emlak Teknoloji Platformu - Notification Service

Bildirim is mantigi katmani: CRUD islemleri, okundu/okunmadi yonetimi.

Guvenlik:
    - Kullanici sadece KENDI bildirimlerini gorebilir (user_id filtresi)
    - Soft delete: Silinen bildirimler fiziksel olarak silinmez (deleted_at set edilir)
    - RLS: Tenant izolasyonu DB seviyesinde uygulanir (office_id)

Kullanim:
    notifications = await NotificationService.list_for_user(db, user_id)
    await NotificationService.mark_read(db, notification_id, user_id)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notification import Notification
from src.modules.realtime.event_emitter import emit_event
from src.modules.realtime.events import EventType

logger = structlog.get_logger(__name__)


class NotificationService:
    """
    Bildirim CRUD servisi.

    Tum metodlar static — state tutmaz, DB session disaridan alinir.
    Kullanici izolasyonu: Her sorgu user_id + is_deleted=False filtresi icerir.
    """

    # ---------- Create ----------

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: uuid.UUID,
        office_id: uuid.UUID,
        type: str,
        title: str,
        body: str | None = None,
        data: dict | None = None,
    ) -> Notification:
        """
        Yeni bildirim olusturur.

        Args:
            db: Async database session.
            user_id: Hedef kullanici UUID.
            office_id: Tenant (ofis) UUID.
            type: Bildirim tipi (new_match, new_message vb.).
            title: Bildirim basligi.
            body: Bildirim detay metni (opsiyonel).
            data: Ek JSON veriler (opsiyonel).

        Returns:
            Olusturulan Notification entity'si.
        """
        notification = Notification(
            user_id=user_id,
            office_id=office_id,
            type=type,
            title=title,
            body=body,
            data=data or {},
        )
        db.add(notification)
        await db.flush()

        logger.info(
            "notification_created",
            notification_id=str(notification.id),
            user_id=str(user_id),
            type=type,
        )

        # --- WebSocket: Gercek zamanli bildirim gonder (opsiyonel, fire-and-forget) ---
        try:
            await emit_event(
                user_id=str(user_id),
                event_type=EventType.NOTIFICATION,
                payload={
                    "notification_id": str(notification.id),
                    "type": type,
                    "title": title,
                    "body": body,
                },
            )
        except Exception as ws_exc:
            # WebSocket hatasi bildirim olusturmayi ENGELLEMEMELI
            logger.warning(
                "notification_ws_emit_failed",
                notification_id=str(notification.id),
                error=str(ws_exc),
            )

        return notification

    # ---------- List ----------

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Notification]:
        """
        Kullanicinin bildirimlerini listeler.

        Silinmis bildirimler (is_deleted=True) otomatik filtrelenir.
        Sonuclar olusturulma zamanina gore azalan sirada doner.

        Args:
            db: Async database session.
            user_id: Hedef kullanici UUID.
            unread_only: True ise sadece okunmamis bildirimler doner.
            limit: Sayfa basi kayit sayisi (varsayilan 20).
            offset: Atlanacak kayit sayisi (pagination).

        Returns:
            Notification listesi.
        """
        query = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_deleted == False,  # noqa: E712 — SQLAlchemy filter
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712

        result = await db.execute(query)
        return list(result.scalars().all())

    # ---------- Count (total, for pagination) ----------

    @staticmethod
    async def count_for_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        unread_only: bool = False,
    ) -> int:
        """
        Kullanicinin bildirim sayisini dondurur (pagination total icin).

        Args:
            db: Async database session.
            user_id: Hedef kullanici UUID.
            unread_only: True ise sadece okunmamis bildirimleri sayar.

        Returns:
            Bildirim sayisi.
        """
        query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_deleted == False,  # noqa: E712
        )

        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712

        result = await db.execute(query)
        return result.scalar_one()

    # ---------- Mark Read ----------

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Tek bildirimi okundu olarak isaretler.

        Guvenlik: Sadece bildirimin sahibi (user_id) isaretleyebilir.

        Args:
            db: Async database session.
            notification_id: Bildirim UUID.
            user_id: Istek yapan kullanici UUID.

        Returns:
            True: Basarili. False: Bildirim bulunamadi veya baska kullaniciya ait.
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.is_deleted == False,  # noqa: E712
            )
            .values(is_read=True)
        )

        success = result.rowcount > 0

        if success:
            logger.info(
                "notification_marked_read",
                notification_id=str(notification_id),
                user_id=str(user_id),
            )

        return success

    # ---------- Mark All Read ----------

    @staticmethod
    async def mark_all_read(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> int:
        """
        Kullanicinin tum okunmamis bildirimlerini okundu yapar.

        Args:
            db: Async database session.
            user_id: Hedef kullanici UUID.

        Returns:
            Guncellenen bildirim sayisi.
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
                Notification.is_deleted == False,  # noqa: E712
            )
            .values(is_read=True)
        )

        updated_count = result.rowcount

        logger.info(
            "notifications_marked_all_read",
            user_id=str(user_id),
            updated_count=updated_count,
        )

        return updated_count

    # ---------- Unread Count ----------

    @staticmethod
    async def unread_count(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> int:
        """
        Kullanicinin okunmamis bildirim sayisini dondurur.

        Args:
            db: Async database session.
            user_id: Hedef kullanici UUID.

        Returns:
            Okunmamis bildirim sayisi.
        """
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
                Notification.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one()

    # ---------- Delete (soft) ----------

    @staticmethod
    async def delete(
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Bildirimi soft-delete yapar (deleted_at + is_deleted set eder).

        Guvenlik: Sadece bildirimin sahibi (user_id) silebilir.
        Fiziksel silme YAPILMAZ — is_deleted=True, deleted_at=now() set edilir.

        Args:
            db: Async database session.
            notification_id: Bildirim UUID.
            user_id: Istek yapan kullanici UUID.

        Returns:
            True: Basarili. False: Bildirim bulunamadi veya baska kullaniciya ait.
        """
        now = datetime.now(UTC)

        result = await db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.is_deleted == False,  # noqa: E712
            )
            .values(is_deleted=True, deleted_at=now)
        )

        success = result.rowcount > 0

        if success:
            logger.info(
                "notification_soft_deleted",
                notification_id=str(notification_id),
                user_id=str(user_id),
            )

        return success
