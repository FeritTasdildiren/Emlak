"""
Emlak Teknoloji Platformu - Showcase Service

Vitrin is mantigi katmani: CRUD islemleri, slug olusturma, public erisim.

Guvenlik:
    - Tum sorgular office_id filtresi icerir (tenant isolation)
    - RLS: DB seviyesinde ek guvenlik katmani
    - Public endpoint'ler (get_by_slug, increment_views) tenant filtresi KULLANMAZ

Kullanim:
    showcase = await ShowcaseService.create(db, office_id, agent_id, data)
    showcases, total = await ShowcaseService.list_by_agent(db, office_id, agent_id)
"""

from __future__ import annotations

import re
import uuid
from typing import TYPE_CHECKING
from urllib.parse import quote

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.core.turkish import normalize_turkish
from src.models.property import Property
from src.models.showcase import Showcase

logger = structlog.get_logger(__name__)


class ShowcaseService:
    """
    Vitrin CRUD servisi.

    Tum metodlar static — state tutmaz, DB session disaridan alinir.
    Tenant izolasyonu: Her sorgu (public haric) office_id filtresi icerir.
    """

    # ---------- Slug Olusturma ----------

    @staticmethod
    async def generate_slug(db: AsyncSession, title: str) -> str:
        """
        Basliktan benzersiz slug olusturur.

        Turkce karakterleri ASCII'ye cevirir, kebab-case yapar,
        benzersizlik kontrolu yapar. Cakisma varsa rastgele suffix ekler.

        Args:
            db: Async database session.
            title: Vitrin basligi.

        Returns:
            Benzersiz slug string.
        """
        # Turkce karakterleri ASCII'ye cevir ve kucuk harfe al
        normalized = normalize_turkish(title)

        # Alfanumerik olmayan karakterleri tire ile degistir
        slug = re.sub(r"[^a-z0-9]+", "-", normalized)
        # Baslangic/bitis tirelerini temizle
        slug = slug.strip("-")
        # Bos slug kontrolu
        if not slug:
            slug = "vitrin"
        # Slug uzunluk siniri (100 char, suffix icin 8 karakter birakalim)
        slug = slug[:90]

        # Benzersizlik kontrolu
        base_slug = slug
        result = await db.execute(select(func.count(Showcase.id)).where(Showcase.slug == slug))
        count = result.scalar_one()

        if count > 0:
            # Cakisma var, rastgele suffix ekle
            suffix = uuid.uuid4().hex[:6]
            slug = f"{base_slug}-{suffix}"

        return slug

    # ---------- Create ----------

    @staticmethod
    async def create(
        db: AsyncSession,
        office_id: uuid.UUID,
        agent_id: uuid.UUID,
        data: dict,
    ) -> Showcase:
        """
        Yeni vitrin olusturur.

        Slug otomatik olarak basliktan olusturulur.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            agent_id: Danisman UUID.
            data: Vitrin verileri (ShowcaseCreate schema'dan).

        Returns:
            Olusturulan Showcase entity'si.
        """
        title = data.pop("title")
        slug = await ShowcaseService.generate_slug(db, title)

        showcase = Showcase(
            office_id=office_id,
            agent_id=agent_id,
            title=title,
            slug=slug,
            **data,
        )
        db.add(showcase)
        await db.flush()

        logger.info(
            "showcase_created",
            showcase_id=str(showcase.id),
            office_id=str(office_id),
            agent_id=str(agent_id),
            slug=slug,
        )

        return showcase

    # ---------- Get by ID ----------

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        showcase_id: uuid.UUID,
        office_id: uuid.UUID,
    ) -> Showcase:
        """
        Vitrini ID ile getirir.

        Args:
            db: Async database session.
            showcase_id: Vitrin UUID.
            office_id: Tenant (ofis) UUID.

        Returns:
            Showcase entity'si.

        Raises:
            NotFoundError: Vitrin bulunamadi.
        """
        result = await db.execute(
            select(Showcase).where(
                Showcase.id == showcase_id,
                Showcase.office_id == office_id,
            )
        )
        showcase = result.scalar_one_or_none()

        if showcase is None:
            raise NotFoundError(resource="Vitrin", resource_id=str(showcase_id))

        return showcase

    # ---------- List by Agent ----------

    @staticmethod
    async def list_by_agent(
        db: AsyncSession,
        office_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> tuple[list[Showcase], int]:
        """
        Danismanin ofise ait vitrinlerini listeler.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            agent_id: Danisman UUID.

        Returns:
            (vitrin listesi, toplam sayi) tuple'i.
        """
        base_filter = [
            Showcase.office_id == office_id,
            Showcase.agent_id == agent_id,
        ]

        # Total count
        count_query = select(func.count(Showcase.id)).where(*base_filter)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Results (en yeniden en eskiye)
        query = select(Showcase).where(*base_filter).order_by(Showcase.created_at.desc())
        result = await db.execute(query)
        showcases = list(result.scalars().all())

        return showcases, total

    # ---------- Update ----------

    @staticmethod
    async def update(
        db: AsyncSession,
        showcase_id: uuid.UUID,
        office_id: uuid.UUID,
        data: dict,
    ) -> Showcase:
        """
        Vitrini gunceller. Sadece gonderilen alanlar guncellenir.

        Baslik degisirse slug yeniden olusturulur.

        Args:
            db: Async database session.
            showcase_id: Vitrin UUID.
            office_id: Tenant (ofis) UUID.
            data: Guncellenecek alanlar (ShowcaseUpdate schema'dan, exclude_unset).

        Returns:
            Guncellenen Showcase entity'si.

        Raises:
            NotFoundError: Vitrin bulunamadi.
        """
        showcase = await ShowcaseService.get_by_id(db, showcase_id, office_id)

        # Baslik degistiyse slug'i da guncelle
        if "title" in data and data["title"] != showcase.title:
            data["slug"] = await ShowcaseService.generate_slug(db, data["title"])

        for field, value in data.items():
            setattr(showcase, field, value)

        await db.flush()

        logger.info(
            "showcase_updated",
            showcase_id=str(showcase_id),
            office_id=str(office_id),
            updated_fields=list(data.keys()),
        )

        return showcase

    # ---------- Delete ----------

    @staticmethod
    async def delete(
        db: AsyncSession,
        showcase_id: uuid.UUID,
        office_id: uuid.UUID,
    ) -> bool:
        """
        Vitrini siler (hard delete).

        Args:
            db: Async database session.
            showcase_id: Vitrin UUID.
            office_id: Tenant (ofis) UUID.

        Returns:
            True: Basarili.

        Raises:
            NotFoundError: Vitrin bulunamadi.
        """
        showcase = await ShowcaseService.get_by_id(db, showcase_id, office_id)

        await db.delete(showcase)
        await db.flush()

        logger.info(
            "showcase_deleted",
            showcase_id=str(showcase_id),
            office_id=str(office_id),
        )

        return True

    # ---------- List Shared (Paylasim Agi) ----------

    @staticmethod
    async def list_shared(
        db: AsyncSession,
        exclude_office_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Showcase], int]:
        """
        Paylasima acik vitrinleri listeler (kendi ofisi haric).

        Sadece aktif ve en az 1 ilan secili olan vitrinler dondurulur.
        Agent ve office iliskileri eager load edilir.

        Args:
            db: Async database session.
            exclude_office_id: Haric tutulacak ofis UUID (kullanicinin ofisi).
            skip: Sayfalama offset.
            limit: Sayfa basi kayit sayisi.

        Returns:
            (vitrin listesi, toplam sayi) tuple'i.
        """
        base_filter = [
            Showcase.office_id != exclude_office_id,
            Showcase.is_active.is_(True),
            func.jsonb_array_length(Showcase.selected_properties) > 0,
        ]

        # Total count
        count_query = select(func.count(Showcase.id)).where(*base_filter)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Results (en yeniden en eskiye) — agent ve office eager load
        query = (
            select(Showcase)
            .where(*base_filter)
            .options(
                selectinload(Showcase.agent),
                selectinload(Showcase.office),
            )
            .order_by(Showcase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        showcases = list(result.scalars().all())

        logger.info(
            "shared_showcases_listed",
            exclude_office_id=str(exclude_office_id),
            total=total,
            skip=skip,
            limit=limit,
        )

        return showcases, total

    # ---------- Get by Slug (PUBLIC) ----------

    @staticmethod
    async def get_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> Showcase:
        """
        Vitrini slug ile getirir. PUBLIC — tenant filtresi YOK.

        Sadece aktif vitrinler dondurulur.

        Args:
            db: Async database session.
            slug: Public URL slug.

        Returns:
            Showcase entity'si.

        Raises:
            NotFoundError: Vitrin bulunamadi veya aktif degil.
        """
        result = await db.execute(
            select(Showcase)
            .where(
                Showcase.slug == slug,
                Showcase.is_active.is_(True),
            )
            .options(selectinload(Showcase.agent))
        )
        showcase = result.scalar_one_or_none()

        if showcase is None:
            raise NotFoundError(resource="Vitrin", resource_id=slug)

        return showcase

    # ---------- Get Properties for Showcase ----------

    @staticmethod
    async def get_showcase_properties(
        db: AsyncSession,
        property_ids: list,
    ) -> list[Property]:
        """
        Vitrine ait ilanlari getirir.

        Args:
            db: Async database session.
            property_ids: Ilan UUID listesi (JSONB'den gelen).

        Returns:
            Property entity listesi.
        """
        if not property_ids:
            return []

        # String UUID'leri UUID objesine cevir
        uuids = []
        for pid in property_ids:
            try:
                uuids.append(uuid.UUID(str(pid)))
            except ValueError:
                continue

        if not uuids:
            return []

        result = await db.execute(select(Property).where(Property.id.in_(uuids)))
        return list(result.scalars().all())

    # ---------- Increment Views (PUBLIC) ----------

    @staticmethod
    async def increment_views(
        db: AsyncSession,
        slug: str,
    ) -> int:
        """
        Vitrin goruntulenme sayacini arttirir. PUBLIC — tenant filtresi YOK.

        Args:
            db: Async database session.
            slug: Public URL slug.

        Returns:
            Guncel goruntulenme sayisi.

        Raises:
            NotFoundError: Vitrin bulunamadi.
        """
        result = await db.execute(
            select(Showcase).where(
                Showcase.slug == slug,
                Showcase.is_active.is_(True),
            )
        )
        showcase = result.scalar_one_or_none()

        if showcase is None:
            raise NotFoundError(resource="Vitrin", resource_id=slug)

        showcase.views_count = (showcase.views_count or 0) + 1
        await db.flush()

        logger.info(
            "showcase_view_incremented",
            slug=slug,
            views_count=showcase.views_count,
        )

        return showcase.views_count

    # ---------- WhatsApp Click-to-Chat Link (PUBLIC) ----------

    @staticmethod
    def generate_whatsapp_link(
        phone: str,
        showcase_title: str,
        slug: str,
    ) -> str:
        """
        WhatsApp click-to-chat linki olusturur.

        Telefon numarasini normalize eder (+90 prefix, sadece rakam),
        mesaj sablonu ile URL encode eder.

        Args:
            phone: Danisman telefon numarasi (orn: +90 532 123 4567).
            showcase_title: Vitrin basligi (mesaj sablonunda kullanilir).
            slug: Vitrin slug'i (URL olusturmak icin).

        Returns:
            WhatsApp click-to-chat URL'i.

        Raises:
            ValueError: Gecersiz telefon numarasi.
        """
        # Telefon normalize: sadece rakam, + isareti haric
        cleaned = re.sub(r"[^0-9]", "", phone)

        # +90 prefix kontrolu
        if cleaned.startswith("90") and len(cleaned) >= 12:
            # Zaten 90 ile basliyor
            pass
        elif cleaned.startswith("0") and len(cleaned) == 11:
            # 05xx -> 905xx
            cleaned = "90" + cleaned[1:]
        elif len(cleaned) == 10:
            # 5xx -> 905xx
            cleaned = "90" + cleaned
        else:
            raise ValueError(f"Gecersiz telefon numarasi: {phone}")

        base_url = "https://emlak.app"
        message = (
            f"Merhaba! {showcase_title} vitrinindeki ilanlari inceledim.\n"
            f"Detayli bilgi almak istiyorum.\n"
            f"{base_url}/vitrin/{slug}"
        )
        encoded_message = quote(message)

        return f"https://wa.me/{cleaned}?text={encoded_message}"
