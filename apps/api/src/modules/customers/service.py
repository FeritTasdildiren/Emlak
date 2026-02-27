"""
Emlak Teknoloji Platformu - Customer Service

Müşteri iş mantığı katmanı: CRUD işlemleri, lead status yönetimi, kota kontrolü.

Güvenlik:
    - Tüm sorgular office_id filtresi içerir (tenant isolation)
    - RLS: DB seviyesinde ek güvenlik katmanı
    - Lead status geçişleri validate edilir

Kullanım:
    customer = await CustomerService.create(db, office_id, data)
    customers, total = await CustomerService.list_customers(db, office_id, page, per_page)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from src.core.exceptions import NotFoundError, ValidationError
from src.models.customer import Customer
from src.models.customer_note import CustomerNote
from src.models.match import PropertyCustomerMatch

logger = structlog.get_logger(__name__)

# ================================================================
# Lead Status Geçiş Kuralları
# ================================================================
# Anahtar: mevcut durum → Değer: geçilebilecek durumlar kümesi
VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "cold": {"warm", "hot"},
    "warm": {"cold", "hot", "converted", "lost"},
    "hot": {"warm", "converted", "lost"},
    "converted": set(),  # Terminal durum — geçiş yok
    "lost": {"warm"},  # Yeniden kazanma
}


def validate_status_transition(current: str, new: str) -> None:
    """
    Lead status geçişini doğrular.

    Args:
        current: Mevcut lead durumu.
        new: Hedef lead durumu.

    Raises:
        ValidationError: Geçersiz geçiş.
    """
    allowed = VALID_STATUS_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise ValidationError(
            detail=(
                f"Gecersiz lead status gecisi: '{current}' → '{new}'. "
                f"Izin verilen gecisler: {sorted(allowed) if allowed else 'yok (terminal durum)'}."
            ),
        )


class CustomerService:
    """
    Müşteri CRUD servisi.

    Tüm metodlar static — state tutmaz, DB session dışarıdan alınır.
    Tenant izolasyonu: Her sorgu office_id filtresi içerir.
    """

    # ---------- Create ----------

    @staticmethod
    async def create(
        db: AsyncSession,
        office_id: uuid.UUID,
        data: dict,
    ) -> Customer:
        """
        Yeni müşteri oluşturur.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            data: Müşteri verileri (CustomerCreate schema'dan).

        Returns:
            Oluşturulan Customer entity'si.
        """
        customer = Customer(
            office_id=office_id,
            **data,
        )
        db.add(customer)
        await db.flush()

        logger.info(
            "customer_created",
            customer_id=str(customer.id),
            office_id=str(office_id),
            customer_type=customer.customer_type,
        )

        return customer

    # ---------- List ----------

    @staticmethod
    async def list_customers(
        db: AsyncSession,
        office_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
        lead_status: str | None = None,
        customer_type: str | None = None,
        search: str | None = None,
        budget_min_from: float | None = None,
        budget_min_to: float | None = None,
        desired_district: str | None = None,
        tag: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[Customer], int]:
        """
        Ofise ait müşterileri sayfalama ile listeler.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            page: Sayfa numarası (1-based).
            per_page: Sayfa başına kayıt sayısı.
            lead_status: Lead durumuna göre filtre (opsiyonel).
            customer_type: Müşteri tipine göre filtre (opsiyonel).
            search: Ad/telefon/email ile arama (opsiyonel).
            budget_min_from: Müşterinin budget_min >= bu değer (opsiyonel).
            budget_min_to: Müşterinin budget_max <= bu değer (opsiyonel).
            desired_district: İlçe filtresi — JSONB @> ile arama (opsiyonel).
            tag: Etiket filtresi — JSONB @> ile arama (opsiyonel).
            sort_by: Sıralama alanı: created_at, last_contact_at, full_name (opsiyonel).
            sort_order: Sıralama yönü: asc, desc (opsiyonel).

        Returns:
            (müşteri listesi, toplam sayı) tuple'ı.
        """
        base_filter = [Customer.office_id == office_id]

        if lead_status:
            base_filter.append(Customer.lead_status == lead_status)
        if customer_type:
            base_filter.append(Customer.customer_type == customer_type)
        if search:
            like_pattern = f"%{search}%"
            base_filter.append(
                Customer.full_name.ilike(like_pattern)
                | Customer.phone.ilike(like_pattern)
                | Customer.email.ilike(like_pattern)
            )

        # Gelişmiş arama filtreleri
        if budget_min_from is not None:
            base_filter.append(Customer.budget_min >= budget_min_from)
        if budget_min_to is not None:
            base_filter.append(Customer.budget_max <= budget_min_to)
        if desired_district:
            # JSONB @> operatörü: desired_districts dizisi bu değeri içeriyor mu
            base_filter.append(
                Customer.desired_districts.op("@>")(f'["{desired_district}"]')
            )
        if tag:
            # JSONB @> operatörü: tags dizisi bu değeri içeriyor mu
            base_filter.append(
                Customer.tags.op("@>")(f'["{tag}"]')
            )

        # Total count
        count_query = select(func.count(Customer.id)).where(*base_filter)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Sıralama
        sort_column = Customer.created_at  # varsayılan
        if sort_by == "last_contact_at":
            sort_column = Customer.last_contact_at
        elif sort_by == "full_name":
            sort_column = Customer.full_name

        order = sort_column.asc() if sort_order == "asc" else sort_column.desc()

        # Paginated results
        offset = (page - 1) * per_page
        query = (
            select(Customer)
            .where(*base_filter)
            .order_by(order)
            .limit(per_page)
            .offset(offset)
        )
        result = await db.execute(query)
        customers = list(result.scalars().all())

        return customers, total

    # ---------- Get by ID ----------

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
    ) -> Customer:
        """
        Müşteriyi ID ile getirir.

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.

        Returns:
            Customer entity'si.

        Raises:
            NotFoundError: Müşteri bulunamadı.
        """
        result = await db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.office_id == office_id,
            )
        )
        customer = result.scalar_one_or_none()

        if customer is None:
            raise NotFoundError(resource="Musteri", resource_id=str(customer_id))

        return customer

    # ---------- Update ----------

    @staticmethod
    async def update(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
        data: dict,
    ) -> Customer:
        """
        Müşteriyi günceller. Sadece gönderilen alanlar güncellenir.

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.
            data: Güncellenecek alanlar (CustomerUpdate schema'dan, exclude_unset).

        Returns:
            Güncellenen Customer entity'si.

        Raises:
            NotFoundError: Müşteri bulunamadı.
        """
        customer = await CustomerService.get_by_id(db, customer_id, office_id)

        for field, value in data.items():
            setattr(customer, field, value)

        await db.flush()

        logger.info(
            "customer_updated",
            customer_id=str(customer_id),
            office_id=str(office_id),
            updated_fields=list(data.keys()),
        )

        return customer

    # ---------- Soft Delete ----------

    @staticmethod
    async def delete(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
    ) -> bool:
        """
        Müşteriyi soft-delete yapar (lead_status='lost' olarak işaretler).

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.

        Returns:
            True: Başarılı.

        Raises:
            NotFoundError: Müşteri bulunamadı.
        """
        customer = await CustomerService.get_by_id(db, customer_id, office_id)

        # Soft delete: lead_status'u lost yap
        customer.lead_status = "lost"

        await db.flush()

        logger.info(
            "customer_soft_deleted",
            customer_id=str(customer_id),
            office_id=str(office_id),
        )

        return True

    # ---------- Update Lead Status ----------

    @staticmethod
    async def update_lead_status(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
        new_status: str,
    ) -> Customer:
        """
        Lead status'unu günceller. Geçiş kuralları validate edilir.

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.
            new_status: Yeni lead durumu.

        Returns:
            Güncellenen Customer entity'si.

        Raises:
            NotFoundError: Müşteri bulunamadı.
            ValidationError: Geçersiz status geçişi.
        """
        customer = await CustomerService.get_by_id(db, customer_id, office_id)

        validate_status_transition(customer.lead_status, new_status)

        old_status = customer.lead_status
        customer.lead_status = new_status
        customer.last_contact_at = datetime.now(UTC)

        await db.flush()

        logger.info(
            "customer_lead_status_updated",
            customer_id=str(customer_id),
            office_id=str(office_id),
            old_status=old_status,
            new_status=new_status,
        )

        return customer

    # ---------- Count (for quota) ----------

    @staticmethod
    async def count_for_office(
        db: AsyncSession,
        office_id: uuid.UUID,
    ) -> int:
        """
        Ofise ait toplam müşteri sayısını döndürür (kota kontrolü için).

        Terminal durumlar (lost) hariç tutulmaz — tüm müşteriler sayılır.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.

        Returns:
            Müşteri sayısı.
        """
        result = await db.execute(
            select(func.count(Customer.id)).where(
                Customer.office_id == office_id,
            )
        )
        return result.scalar_one()

    # ---------- Notes ----------

    @staticmethod
    async def add_note(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict,
    ) -> CustomerNote:
        """
        Müşteriye yeni not ekler ve last_contact_at günceller.

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.
            user_id: Notu oluşturan kullanıcı UUID.
            data: Not verileri (NoteCreate schema'dan).

        Returns:
            Oluşturulan CustomerNote entity'si.

        Raises:
            NotFoundError: Müşteri bulunamadı.
        """
        # Müşterinin var olduğunu ve ofise ait olduğunu doğrula
        customer = await CustomerService.get_by_id(db, customer_id, office_id)

        note = CustomerNote(
            office_id=office_id,
            customer_id=customer_id,
            user_id=user_id,
            **data,
        )
        db.add(note)

        # last_contact_at güncelle
        customer.last_contact_at = datetime.now(UTC)

        await db.flush()

        logger.info(
            "customer_note_added",
            note_id=str(note.id),
            customer_id=str(customer_id),
            office_id=str(office_id),
            note_type=note.note_type,
        )

        return note

    @staticmethod
    async def list_notes(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[CustomerNote], int]:
        """
        Müşteriye ait notları sayfalama ile listeler.

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.
            page: Sayfa numarası (1-based).
            per_page: Sayfa başına kayıt sayısı.

        Returns:
            (not listesi, toplam sayı) tuple'ı.

        Raises:
            NotFoundError: Müşteri bulunamadı.
        """
        # Müşterinin var olduğunu doğrula
        await CustomerService.get_by_id(db, customer_id, office_id)

        base_filter = [
            CustomerNote.customer_id == customer_id,
            CustomerNote.office_id == office_id,
        ]

        # Total count
        count_query = select(func.count(CustomerNote.id)).where(*base_filter)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated results (en yeniden en eskiye)
        # noload("*") — ilişkili nesneler yüklenmez, sadece not alanları döner
        offset = (page - 1) * per_page
        query = (
            select(CustomerNote)
            .options(noload("*"))
            .where(*base_filter)
            .order_by(CustomerNote.created_at.desc())
            .limit(per_page)
            .offset(offset)
        )
        result = await db.execute(query)
        notes = list(result.scalars().all())

        return notes, total

    # ---------- Timeline ----------

    @staticmethod
    async def get_timeline(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Müşterinin birleşik aktivite akışını getirir.

        Notlar (customer_notes) ve eşleştirmeler (property_customer_matches)
        birleştirilerek timestamp'e göre DESC sıralanır.

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.
            page: Sayfa numarası (1-based).
            per_page: Sayfa başına kayıt sayısı.

        Returns:
            (timeline öğeleri listesi, toplam sayı) tuple'ı.

        Raises:
            NotFoundError: Müşteri bulunamadı.
        """
        # Müşterinin var olduğunu doğrula
        await CustomerService.get_by_id(db, customer_id, office_id)

        # Notları al — noload("*") ile ilişkili nesneler yüklenmez
        notes_query = (
            select(CustomerNote)
            .options(noload("*"))
            .where(
                CustomerNote.customer_id == customer_id,
                CustomerNote.office_id == office_id,
            )
        )
        notes_result = await db.execute(notes_query)
        notes = list(notes_result.scalars().all())

        # Eşleştirmeleri al — noload("*") ile ilişkili nesneler yüklenmez
        matches_query = (
            select(PropertyCustomerMatch)
            .options(noload("*"))
            .where(
                PropertyCustomerMatch.customer_id == customer_id,
                PropertyCustomerMatch.office_id == office_id,
            )
        )
        matches_result = await db.execute(matches_query)
        matches = list(matches_result.scalars().all())

        # Timeline öğelerini oluştur
        timeline_items: list[dict] = []

        for note in notes:
            timeline_items.append({
                "type": "note",
                "content": note.content,
                "timestamp": note.created_at,
                "metadata": {
                    "note_id": str(note.id),
                    "note_type": note.note_type,
                    "user_id": str(note.user_id) if note.user_id else None,
                },
            })

        for match in matches:
            timeline_items.append({
                "type": "match",
                "content": f"Eslesme skoru: {match.score:.1f} — Durum: {match.status}",
                "timestamp": match.matched_at,
                "metadata": {
                    "match_id": str(match.id),
                    "property_id": str(match.property_id),
                    "score": match.score,
                    "status": match.status,
                },
            })

        # Timestamp'e göre DESC sırala
        timeline_items.sort(key=lambda x: x["timestamp"], reverse=True)

        # Toplam sayı
        total = len(timeline_items)

        # Sayfalama uygula
        offset = (page - 1) * per_page
        paginated_items = timeline_items[offset : offset + per_page]

        return paginated_items, total
