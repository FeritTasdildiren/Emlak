"""
Emlak Teknoloji Platformu - Appointment Service

Randevu iş mantığı katmanı: CRUD işlemleri, filtreleme, yaklaşan randevular.

Güvenlik:
    - Tüm sorgular office_id filtresi içerir (tenant isolation)
    - RLS: DB seviyesinde ek güvenlik katmanı

Kullanım:
    appointment = await AppointmentService.create_appointment(db, office_id, user_id, data)
    appointments, total = await AppointmentService.list_appointments(db, office_id)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.models.appointment import Appointment

logger = structlog.get_logger(__name__)


class AppointmentService:
    """
    Randevu CRUD servisi.

    Tüm metodlar static — state tutmaz, DB session dışarıdan alınır.
    Tenant izolasyonu: Her sorgu office_id filtresi içerir.
    """

    # ---------- Create ----------

    @staticmethod
    async def create_appointment(
        db: AsyncSession,
        office_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict,
    ) -> Appointment:
        """
        Yeni randevu oluşturur.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            user_id: Randevuyu oluşturan danışman UUID.
            data: Randevu verileri (AppointmentCreate schema'dan).

        Returns:
            Oluşturulan Appointment entity'si.
        """
        # customer_id ve property_id string olarak gelebilir, UUID'ye dönüştür
        if data.get("customer_id"):
            data["customer_id"] = uuid.UUID(data["customer_id"])
        else:
            data.pop("customer_id", None)

        if data.get("property_id"):
            data["property_id"] = uuid.UUID(data["property_id"])
        else:
            data.pop("property_id", None)

        appointment = Appointment(
            office_id=office_id,
            user_id=user_id,
            **data,
        )
        db.add(appointment)
        await db.flush()

        # İlişkileri yükle (user, customer, property)
        await db.refresh(appointment, ["user", "customer", "property"])

        logger.info(
            "appointment_created",
            appointment_id=str(appointment.id),
            office_id=str(office_id),
            user_id=str(user_id),
            title=appointment.title,
        )

        return appointment

    # ---------- List ----------

    @staticmethod
    async def list_appointments(
        db: AsyncSession,
        office_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status_filter: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[Appointment], int]:
        """
        Ofise ait randevuları sayfalama ve filtrelerle listeler.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            skip: Atlanan kayıt sayısı.
            limit: Sayfa başına kayıt limiti.
            status_filter: Randevu durumuna göre filtre (opsiyonel).
            date_from: Başlangıç tarihi filtresi (opsiyonel).
            date_to: Bitiş tarihi filtresi (opsiyonel).

        Returns:
            (randevu listesi, toplam sayı) tuple'ı.
        """
        base_filter = [Appointment.office_id == office_id]

        if status_filter:
            base_filter.append(Appointment.status == status_filter)
        if date_from:
            base_filter.append(Appointment.appointment_date >= date_from)
        if date_to:
            base_filter.append(Appointment.appointment_date <= date_to)

        # Total count
        count_query = select(func.count(Appointment.id)).where(*base_filter)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated results (en yeniden en eskiye)
        query = (
            select(Appointment)
            .where(*base_filter)
            .order_by(Appointment.appointment_date.desc())
            .limit(limit)
            .offset(skip)
        )
        result = await db.execute(query)
        appointments = list(result.scalars().all())

        return appointments, total

    # ---------- Get Upcoming ----------

    @staticmethod
    async def get_upcoming(
        db: AsyncSession,
        office_id: uuid.UUID,
        limit: int = 5,
    ) -> list[Appointment]:
        """
        Bugünden itibaren yaklaşan scheduled randevuları getirir.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            limit: Maksimum döndürülecek randevu sayısı.

        Returns:
            Yaklaşan randevu listesi (tarihe göre ASC sıralı).
        """
        now = datetime.now(UTC)
        query = (
            select(Appointment)
            .where(
                Appointment.office_id == office_id,
                Appointment.status == "scheduled",
                Appointment.appointment_date >= now,
            )
            .order_by(Appointment.appointment_date.asc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    # ---------- Get by ID ----------

    @staticmethod
    async def get_appointment(
        db: AsyncSession,
        office_id: uuid.UUID,
        appointment_id: uuid.UUID,
    ) -> Appointment | None:
        """
        Randevuyu ID ile getirir.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            appointment_id: Randevu UUID.

        Returns:
            Appointment entity'si veya None.
        """
        result = await db.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.office_id == office_id,
            )
        )
        return result.scalar_one_or_none()

    # ---------- Update ----------

    @staticmethod
    async def update_appointment(
        db: AsyncSession,
        office_id: uuid.UUID,
        appointment_id: uuid.UUID,
        data: dict,
    ) -> Appointment:
        """
        Randevuyu günceller. Sadece gönderilen alanlar güncellenir.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            appointment_id: Randevu UUID.
            data: Güncellenecek alanlar (AppointmentUpdate schema'dan, exclude_unset).

        Returns:
            Güncellenen Appointment entity'si.

        Raises:
            NotFoundError: Randevu bulunamadı.
        """
        appointment = await AppointmentService.get_appointment(
            db, office_id, appointment_id,
        )
        if appointment is None:
            raise NotFoundError(resource="Randevu", resource_id=str(appointment_id))

        # customer_id ve property_id string olarak gelebilir, UUID'ye dönüştür
        if "customer_id" in data:
            if data["customer_id"]:
                data["customer_id"] = uuid.UUID(data["customer_id"])
            else:
                data["customer_id"] = None

        if "property_id" in data:
            if data["property_id"]:
                data["property_id"] = uuid.UUID(data["property_id"])
            else:
                data["property_id"] = None

        for field, value in data.items():
            setattr(appointment, field, value)

        await db.flush()

        # İlişkileri yeniden yükle
        await db.refresh(appointment, ["user", "customer", "property"])

        logger.info(
            "appointment_updated",
            appointment_id=str(appointment_id),
            office_id=str(office_id),
            updated_fields=list(data.keys()),
        )

        return appointment

    # ---------- Delete ----------

    @staticmethod
    async def delete_appointment(
        db: AsyncSession,
        office_id: uuid.UUID,
        appointment_id: uuid.UUID,
    ) -> bool:
        """
        Randevuyu kalıcı olarak siler.

        Args:
            db: Async database session.
            office_id: Tenant (ofis) UUID.
            appointment_id: Randevu UUID.

        Returns:
            True: Başarılı silme.

        Raises:
            NotFoundError: Randevu bulunamadı.
        """
        appointment = await AppointmentService.get_appointment(
            db, office_id, appointment_id,
        )
        if appointment is None:
            raise NotFoundError(resource="Randevu", resource_id=str(appointment_id))

        await db.delete(appointment)
        await db.flush()

        logger.info(
            "appointment_deleted",
            appointment_id=str(appointment_id),
            office_id=str(office_id),
        )

        return True
