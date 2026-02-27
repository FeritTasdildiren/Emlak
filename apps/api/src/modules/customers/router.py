"""
Emlak Teknoloji Platformu - Customers Router

Müşteri CRUD API endpoint'leri + Not sistemi + Timeline.

Prefix: /api/v1/customers
Güvenlik: Tüm endpoint'ler JWT gerektirir (ActiveUser dependency).
Tenant izolasyonu: office_id otomatik olarak JWT'den alınır.

Endpoint'ler:
    POST   /customers                       → Yeni müşteri oluştur
    GET    /customers                       → Müşteri listesi (sayfalama + filtre + gelişmiş arama)
    GET    /customers/{id}                  → Müşteri detay
    PATCH  /customers/{id}                  → Müşteri güncelle
    DELETE /customers/{id}                  → Müşteri sil (soft delete)
    PATCH  /customers/{id}/status           → Lead status güncelle
    POST   /customers/{id}/notes            → Not ekle
    GET    /customers/{id}/notes            → Notları listele
    GET    /customers/{id}/timeline         → Birleşik aktivite akışı
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid

from fastapi import APIRouter, Query, Request, status
from sqlalchemy import select

from src.core.exceptions import PermissionDenied
from src.core.plan_policy import get_customer_quota
from src.dependencies import DBSession
from src.models.subscription import Subscription
from src.modules.audit.audit_service import AuditService
from src.modules.auth.dependencies import ActiveUser
from src.modules.customers.schemas import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
    LeadStatusUpdate,
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    TimelineResponse,
)
from src.modules.customers.service import CustomerService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/customers",
    tags=["customers"],
)


async def _get_plan_type(db: DBSession, office_id: object) -> str:
    """Ofis'in aktif abonelik planını döndürür. Bulunamazsa 'starter' varsayar."""
    stmt = (
        select(Subscription.plan_type)
        .where(
            Subscription.office_id == office_id,
            Subscription.status.in_(["active", "trial"]),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    return plan if plan else "starter"


def _to_response(customer) -> CustomerResponse:
    """Customer entity'sini response modeline dönüştürür."""
    return CustomerResponse(
        id=str(customer.id),
        full_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        customer_type=customer.customer_type,
        budget_min=float(customer.budget_min) if customer.budget_min is not None else None,
        budget_max=float(customer.budget_max) if customer.budget_max is not None else None,
        desired_rooms=customer.desired_rooms,
        desired_area_min=customer.desired_area_min,
        desired_area_max=customer.desired_area_max,
        desired_districts=customer.desired_districts or [],
        tags=customer.tags or [],
        lead_status=customer.lead_status,
        source=customer.source,
        last_contact_at=customer.last_contact_at,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
    )


# ---------- POST /customers ----------


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni müşteri oluştur",
    description="Authenticated kullanıcının ofisine yeni müşteri ekler. Kota kontrolü yapılır.",
)
async def create_customer(
    request: Request,
    body: CustomerCreate,
    db: DBSession,
    current_user: ActiveUser,
) -> CustomerResponse:
    """
    Yeni müşteri oluşturur.

    - office_id JWT'den otomatik alınır
    - Plan bazlı müşteri kota kontrolü yapılır
    - Kota aşımında HTTP 403 döner
    """
    office_id = current_user.office_id

    # --- Kota kontrolü ---
    current_count = await CustomerService.count_for_office(db, office_id)

    # Kullanıcının ofisinin plan tipini ayrı sorgu ile al (subscription ilişkisi
    # Office modelinde tanımlı değil — doğrudan Subscription tablosundan sorgula)
    plan_type = await _get_plan_type(db, office_id)
    quota = get_customer_quota(plan_type)

    if quota != -1 and current_count >= quota:
        raise PermissionDenied(
            detail=(
                f"Musteri kotaniz doldu. "
                f"Mevcut: {current_count}/{quota}. "
                f"Plan yukseltmesi icin /pricing sayfasini ziyaret edin."
            ),
        )

    customer = await CustomerService.create(
        db=db,
        office_id=office_id,
        data=body.model_dump(),
    )

    # KVKK Audit: Müşteri oluşturma kaydı
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=office_id,
        action="CREATE",
        entity_type="Customer",
        entity_id=str(customer.id),
        new_value=body.model_dump(),
        request=request,
    )

    # Eşleştirme tetikle (buyer/renter müşteriler için, async Celery task)
    if customer.customer_type in ("buyer", "renter"):
        try:
            from src.modules.matches.matching_service import (
                trigger_matching_after_customer_create,
            )

            trigger_matching_after_customer_create(customer.id, office_id)
        except Exception:
            logger.warning(
                "matching_trigger_failed",
                customer_id=str(customer.id),
                exc_info=True,
            )

    return _to_response(customer)


# ---------- GET /customers ----------


@router.get(
    "",
    response_model=CustomerListResponse,
    summary="Müşteri listesi",
    description="Ofise ait müşterileri sayfalama ve filtrelerle listeler.",
)
async def list_customers(
    db: DBSession,
    current_user: ActiveUser,
    page: int = Query(default=1, ge=1, description="Sayfa numarası"),
    per_page: int = Query(default=20, ge=1, le=100, description="Sayfa başına kayıt (max 100)"),
    lead_status: str | None = Query(default=None, description="Lead durumu filtresi"),
    customer_type: str | None = Query(default=None, description="Müşteri tipi filtresi"),
    search: str | None = Query(default=None, description="Ad/telefon/email ile arama"),
    budget_min_from: float | None = Query(default=None, ge=0, description="Minimum bütçe alt sınır filtresi"),
    budget_min_to: float | None = Query(default=None, ge=0, description="Maksimum bütçe üst sınır filtresi"),
    desired_district: str | None = Query(default=None, description="İlçe filtresi (desired_districts JSONB)"),
    tag: str | None = Query(default=None, description="Etiket filtresi (tags JSONB)"),
    sort_by: str | None = Query(default=None, description="Sıralama: created_at, last_contact_at, full_name"),
    sort_order: str | None = Query(default=None, description="Sıralama yönü: asc, desc"),
) -> CustomerListResponse:
    """
    Ofise ait müşterileri listeler.

    - Sonuçlar varsayılan olarak en yeniden en eskiye sıralanır
    - Pagination: page + per_page
    - Filtreler: lead_status, customer_type, search (ad/telefon/email)
    - Gelişmiş filtreler: budget_min_from, budget_min_to, desired_district, tag
    - Sıralama: sort_by + sort_order
    """
    customers, total = await CustomerService.list_customers(
        db=db,
        office_id=current_user.office_id,
        page=page,
        per_page=per_page,
        lead_status=lead_status,
        customer_type=customer_type,
        search=search,
        budget_min_from=budget_min_from,
        budget_min_to=budget_min_to,
        desired_district=desired_district,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return CustomerListResponse(
        items=[_to_response(c) for c in customers],
        total=total,
        page=page,
        per_page=per_page,
    )


# ---------- GET /customers/{id} ----------


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Müşteri detay",
    description="Belirtilen müşterinin detaylarını döndürür.",
)
async def get_customer(
    customer_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> CustomerResponse:
    """
    Müşteri detayını getirir.

    - Sadece kendi ofisinin müşterileri görülebilir (tenant isolation)
    - Müşteri bulunamazsa 404
    """
    customer = await CustomerService.get_by_id(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
    )
    return _to_response(customer)


# ---------- PATCH /customers/{id} ----------


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Müşteri güncelle",
    description="Belirtilen müşterinin bilgilerini günceller. Sadece gönderilen alanlar değişir.",
)
async def update_customer(
    request: Request,
    customer_id: uuid.UUID,
    body: CustomerUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> CustomerResponse:
    """
    Müşteriyi günceller.

    - Partial update: sadece gönderilen alanlar güncellenir
    - Müşteri bulunamazsa 404
    """
    update_data = body.model_dump(exclude_unset=True)
    customer = await CustomerService.update(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
        data=update_data,
    )

    # KVKK Audit: Müşteri güncelleme kaydı
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="UPDATE",
        entity_type="Customer",
        entity_id=str(customer_id),
        new_value=update_data,
        request=request,
    )

    return _to_response(customer)


# ---------- DELETE /customers/{id} ----------


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Müşteri sil (soft delete)",
    description="Belirtilen müşteriyi soft-delete yapar. Lead status 'lost' olarak işaretlenir.",
)
async def delete_customer(
    request: Request,
    customer_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> None:
    """
    Müşteriyi soft-delete yapar.

    - Fiziksel silme yapılmaz, lead_status='lost' olarak set edilir
    - Müşteri bulunamazsa 404
    """
    await CustomerService.delete(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
    )

    # KVKK Audit: Müşteri silme kaydı
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="DELETE",
        entity_type="Customer",
        entity_id=str(customer_id),
        request=request,
    )


# ---------- PATCH /customers/{id}/status ----------


@router.patch(
    "/{customer_id}/status",
    response_model=CustomerResponse,
    summary="Lead status güncelle",
    description="Müşterinin lead durumunu günceller. Geçiş kuralları validate edilir.",
)
async def update_lead_status(
    customer_id: uuid.UUID,
    body: LeadStatusUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> CustomerResponse:
    """
    Lead status'unu günceller.

    Geçerli geçişler:
    - cold → warm, hot
    - warm → cold, hot, converted, lost
    - hot → warm, converted, lost
    - converted → (terminal — geçiş yok)
    - lost → warm (yeniden kazanma)

    Geçersiz geçişte 422 döner.
    """
    customer = await CustomerService.update_lead_status(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
        new_status=body.status,
    )
    return _to_response(customer)


# ---------- POST /customers/{id}/notes ----------


@router.post(
    "/{customer_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Müşteriye not ekle",
    description="Belirtilen müşteriye yeni bir not ekler. last_contact_at otomatik güncellenir.",
)
async def add_note(
    customer_id: uuid.UUID,
    body: NoteCreate,
    db: DBSession,
    current_user: ActiveUser,
) -> NoteResponse:
    """
    Müşteriye not ekler.

    - Not tipleri: note, call, meeting, email
    - Oluşturan kullanıcı JWT'den otomatik alınır
    - Müşterinin last_contact_at alanı güncellenir
    """
    note = await CustomerService.add_note(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
        user_id=current_user.id,
        data=body.model_dump(),
    )

    return NoteResponse(
        id=str(note.id),
        content=note.content,
        note_type=note.note_type,
        user_id=str(note.user_id) if note.user_id else None,
        created_at=note.created_at,
    )


# ---------- GET /customers/{id}/notes ----------


@router.get(
    "/{customer_id}/notes",
    response_model=NoteListResponse,
    summary="Müşteri notlarını listele",
    description="Belirtilen müşterinin notlarını sayfalama ile listeler.",
)
async def list_notes(
    customer_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
    page: int = Query(default=1, ge=1, description="Sayfa numarası"),
    per_page: int = Query(default=20, ge=1, le=100, description="Sayfa başına kayıt (max 100)"),
) -> NoteListResponse:
    """
    Müşterinin notlarını listeler.

    - En yeniden en eskiye sıralanır
    - Pagination: page + per_page
    """
    notes, total = await CustomerService.list_notes(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
        page=page,
        per_page=per_page,
    )

    return NoteListResponse(
        items=[
            NoteResponse(
                id=str(n.id),
                content=n.content,
                note_type=n.note_type,
                user_id=str(n.user_id) if n.user_id else None,
                created_at=n.created_at,
            )
            for n in notes
        ],
        total=total,
    )


# ---------- GET /customers/{id}/timeline ----------


@router.get(
    "/{customer_id}/timeline",
    response_model=TimelineResponse,
    summary="Müşteri timeline",
    description="Müşterinin birleşik aktivite akışını getirir (notlar + eşleştirmeler).",
)
async def get_timeline(
    customer_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
    page: int = Query(default=1, ge=1, description="Sayfa numarası"),
    per_page: int = Query(default=20, ge=1, le=100, description="Sayfa başına kayıt (max 100)"),
) -> TimelineResponse:
    """
    Müşterinin birleşik aktivite akışını getirir.

    - Notlar ve eşleştirmeler birleştirilir
    - Timestamp'e göre en yeniden en eskiye sıralanır
    - Pagination: page + per_page
    """
    items, total = await CustomerService.get_timeline(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
        page=page,
        per_page=per_page,
    )

    return TimelineResponse(items=items, total=total)
