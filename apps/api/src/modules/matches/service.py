"""
Emlak Teknoloji Platformu - Match Service

İlan-Müşteri eşleştirme iş mantığı katmanı: listeleme, detay, durum güncelleme.

Güvenlik:
    - Tüm sorgular office_id filtresi içerir (tenant isolation)
    - RLS: DB seviyesinde ek güvenlik katmanı

Kullanım:
    matches, total = await MatchService.list_matches(db, office_id)
    match = await MatchService.get_by_id(db, match_id, office_id)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from src.core.exceptions import NotFoundError

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession
from src.models.match import PropertyCustomerMatch

logger = structlog.get_logger(__name__)


class MatchService:
    """
    Eşleştirme CRUD servisi.

    Tüm metodlar static — state tutmaz, DB session dışarıdan alınır.
    Tenant izolasyonu: Her sorgu office_id filtresi içerir.
    """

    # ---------- List ----------

    @staticmethod
    async def list_matches(
        db: AsyncSession,
        office_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
        customer_id: uuid.UUID | None = None,
        property_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[PropertyCustomerMatch], int]:
        """
        Ofise ait eşleştirmeleri sayfalama ile listeler.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            page: Sayfa numarası (1-based).
            per_page: Sayfa başına kayıt sayısı.
            customer_id: Müşteri ID filtresi (opsiyonel).
            property_id: İlan ID filtresi (opsiyonel).
            status: Durum filtresi (opsiyonel).

        Returns:
            (eşleştirme listesi, toplam sayı) tuple'ı.
        """
        base_filter = [PropertyCustomerMatch.office_id == office_id]

        if customer_id:
            base_filter.append(PropertyCustomerMatch.customer_id == customer_id)
        if property_id:
            base_filter.append(PropertyCustomerMatch.property_id == property_id)
        if status:
            base_filter.append(PropertyCustomerMatch.status == status)

        # Total count
        count_query = select(func.count(PropertyCustomerMatch.id)).where(*base_filter)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated results
        offset = (page - 1) * per_page
        query = (
            select(PropertyCustomerMatch)
            .where(*base_filter)
            .order_by(PropertyCustomerMatch.score.desc())
            .limit(per_page)
            .offset(offset)
        )
        result = await db.execute(query)
        matches = list(result.scalars().all())

        return matches, total

    # ---------- Get by ID ----------

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        match_id: uuid.UUID,
        office_id: uuid.UUID,
    ) -> PropertyCustomerMatch:
        """
        Eşleştirmeyi ID ile getirir.

        Args:
            db: Async database session.
            match_id: Eşleştirme UUID.
            office_id: Tenant (ofis) UUID.

        Returns:
            PropertyCustomerMatch entity'si.

        Raises:
            NotFoundError: Eşleştirme bulunamadı.
        """
        result = await db.execute(
            select(PropertyCustomerMatch).where(
                PropertyCustomerMatch.id == match_id,
                PropertyCustomerMatch.office_id == office_id,
            )
        )
        match = result.scalar_one_or_none()

        if match is None:
            raise NotFoundError(resource="Eslestirme", resource_id=str(match_id))

        return match

    # ---------- Update Status ----------

    @staticmethod
    async def update_status(
        db: AsyncSession,
        match_id: uuid.UUID,
        office_id: uuid.UUID,
        new_status: str,
        notes: str | None = None,
    ) -> PropertyCustomerMatch:
        """
        Eşleştirme durumunu günceller.

        Args:
            db: Async database session.
            match_id: Eşleştirme UUID.
            office_id: Tenant (ofis) UUID.
            new_status: Yeni durum.
            notes: Opsiyonel not.

        Returns:
            Güncellenen PropertyCustomerMatch entity'si.

        Raises:
            NotFoundError: Eşleştirme bulunamadı.
        """
        match = await MatchService.get_by_id(db, match_id, office_id)

        old_status = match.status
        match.status = new_status
        match.responded_at = datetime.now(UTC)

        if notes is not None:
            match.notes = notes

        await db.flush()

        logger.info(
            "match_status_updated",
            match_id=str(match_id),
            office_id=str(office_id),
            old_status=old_status,
            new_status=new_status,
        )

        return match
