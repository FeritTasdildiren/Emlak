"""
Emlak Teknoloji Platformu - Appointments Router

Randevu CRUD API endpoint'leri.

Prefix: /api/v1/appointments
Güvenlik: Tüm endpoint'ler JWT gerektirir (ActiveUser dependency).
Tenant izolasyonu: office_id otomatik olarak JWT'den alınır.

Endpoint'ler:
    POST   /appointments           → Yeni randevu oluştur
    GET    /appointments           → Randevu listesi (sayfalama + filtre)
    GET    /appointments/upcoming  → Yaklaşan randevular
    GET    /appointments/{id}      → Randevu detay
    PATCH  /appointments/{id}      → Randevu güncelle
    DELETE /appointments/{id}      → Randevu sil
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid

from datetime import datetime

from fastapi import APIRouter, Query, status

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentUpdate,
)
from src.modules.appointments.service import AppointmentService
from src.modules.auth.dependencies import ActiveUser

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/appointments",
    tags=["appointments"],
)


def _to_response(appointment) -> AppointmentResponse:
    """Appointment entity'sini response modeline dönüştürür."""
    # İlişkili nesnelerden isimleri güvenli şekilde al
    user_name = ""
    if appointment.user:
        user_name = getattr(appointment.user, "full_name", "") or ""

    customer_name = None
    if appointment.customer:
        customer_name = getattr(appointment.customer, "full_name", None)

    property_title = None
    if appointment.property:
        property_title = getattr(appointment.property, "title", None)

    return AppointmentResponse(
        id=str(appointment.id),
        title=appointment.title,
        description=appointment.description,
        appointment_date=appointment.appointment_date,
        duration_minutes=appointment.duration_minutes,
        status=appointment.status,
        location=appointment.location,
        notes=appointment.notes,
        customer_id=str(appointment.customer_id) if appointment.customer_id else None,
        property_id=str(appointment.property_id) if appointment.property_id else None,
        user_id=str(appointment.user_id),
        user_name=user_name,
        customer_name=customer_name,
        property_title=property_title,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )


# ---------- POST /appointments ----------


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni randevu oluştur",
    description="Authenticated kullanıcının ofisine yeni randevu ekler.",
)
async def create_appointment(
    body: AppointmentCreate,
    db: DBSession,
    current_user: ActiveUser,
) -> AppointmentResponse:
    """
    Yeni randevu oluşturur.

    - office_id ve user_id JWT'den otomatik alınır
    - customer_id ve property_id opsiyonel bağlantılar
    """
    appointment = await AppointmentService.create_appointment(
        db=db,
        office_id=current_user.office_id,
        user_id=current_user.id,
        data=body.model_dump(),
    )

    return _to_response(appointment)


# ---------- GET /appointments ----------


@router.get(
    "",
    response_model=AppointmentListResponse,
    summary="Randevu listesi",
    description="Ofise ait randevuları sayfalama ve filtrelerle listeler.",
)
async def list_appointments(
    db: DBSession,
    current_user: ActiveUser,
    skip: int = Query(default=0, ge=0, description="Atlanan kayıt sayısı"),
    limit: int = Query(default=20, ge=1, le=100, description="Sayfa başına kayıt (max 100)"),
    status: str | None = Query(default=None, description="Durum filtresi: scheduled, completed, cancelled, no_show"),
    date_from: datetime | None = Query(default=None, description="Başlangıç tarihi filtresi (ISO 8601)"),
    date_to: datetime | None = Query(default=None, description="Bitiş tarihi filtresi (ISO 8601)"),
) -> AppointmentListResponse:
    """
    Ofise ait randevuları listeler.

    - Sonuçlar varsayılan olarak en yeni randevudan en eskiye sıralanır
    - Pagination: skip + limit
    - Filtreler: status, date_from, date_to
    """
    appointments, total = await AppointmentService.list_appointments(
        db=db,
        office_id=current_user.office_id,
        skip=skip,
        limit=limit,
        status_filter=status,
        date_from=date_from,
        date_to=date_to,
    )

    return AppointmentListResponse(
        items=[_to_response(a) for a in appointments],
        total=total,
        skip=skip,
        limit=limit,
    )


# ---------- GET /appointments/upcoming ----------
# KRİTİK: Bu statik path, parametrik /{appointment_id}'den ÖNCE tanımlanmalı!


@router.get(
    "/upcoming",
    response_model=list[AppointmentResponse],
    summary="Yaklaşan randevular",
    description="Bugünden itibaren planlanan (scheduled) randevuları getirir.",
)
async def get_upcoming_appointments(
    db: DBSession,
    current_user: ActiveUser,
    limit: int = Query(default=5, ge=1, le=50, description="Maksimum randevu sayısı"),
) -> list[AppointmentResponse]:
    """
    Yaklaşan randevuları getirir.

    - Sadece status='scheduled' ve tarih >= bugün olan randevular
    - Tarihe göre ASC sıralı (en yakın randevu önce)
    """
    appointments = await AppointmentService.get_upcoming(
        db=db,
        office_id=current_user.office_id,
        limit=limit,
    )

    return [_to_response(a) for a in appointments]


# ---------- GET /appointments/{appointment_id} ----------


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Randevu detay",
    description="Belirtilen randevunun detaylarını döndürür.",
)
async def get_appointment(
    appointment_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> AppointmentResponse:
    """
    Randevu detayını getirir.

    - Sadece kendi ofisinin randevuları görülebilir (tenant isolation)
    - Randevu bulunamazsa 404
    """
    appointment = await AppointmentService.get_appointment(
        db=db,
        office_id=current_user.office_id,
        appointment_id=appointment_id,
    )
    if appointment is None:
        raise NotFoundError(resource="Randevu", resource_id=str(appointment_id))

    return _to_response(appointment)


# ---------- PATCH /appointments/{appointment_id} ----------


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Randevu güncelle",
    description="Belirtilen randevunun bilgilerini günceller. Sadece gönderilen alanlar değişir.",
)
async def update_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> AppointmentResponse:
    """
    Randevuyu günceller.

    - Partial update: sadece gönderilen alanlar güncellenir
    - Randevu bulunamazsa 404
    """
    update_data = body.model_dump(exclude_unset=True)
    appointment = await AppointmentService.update_appointment(
        db=db,
        office_id=current_user.office_id,
        appointment_id=appointment_id,
        data=update_data,
    )

    return _to_response(appointment)


# ---------- DELETE /appointments/{appointment_id} ----------


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Randevu sil",
    description="Belirtilen randevuyu kalıcı olarak siler.",
)
async def delete_appointment(
    appointment_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> None:
    """
    Randevuyu siler.

    - Kalıcı silme (hard delete)
    - Randevu bulunamazsa 404
    """
    await AppointmentService.delete_appointment(
        db=db,
        office_id=current_user.office_id,
        appointment_id=appointment_id,
    )
