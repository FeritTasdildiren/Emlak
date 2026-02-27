"""
Emlak Teknoloji Platformu - Audit Router

KVKK denetim kayitlari API endpoint'leri.

Prefix: /api/v1/audit
Guvenlik: Tum endpoint'ler JWT + platform_admin rolu gerektirir.
Tenant izolasyonu: office_id otomatik olarak JWT'den alinir.

Endpoint'ler:
    GET /audit/logs          → Filtrelenebilir audit log listesi
    GET /audit/logs/{id}     → Audit log detayi
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

if TYPE_CHECKING:
    import uuid

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.audit_log import AuditLog
from src.modules.audit.audit_schemas import (
    AuditActionFilter,
    AuditLogListResponse,
    AuditLogResponse,
)
from src.modules.auth.dependencies import ActiveUser, require_role

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["audit"],
)

# Platform admin rolu gerekli — tum endpoint'ler bu dependency'yi kullanir
_require_admin = Depends(require_role("platform_admin"))


def _to_response(log: AuditLog) -> AuditLogResponse:
    """AuditLog entity'sini response modeline donusturur."""
    return AuditLogResponse(
        id=str(log.id),
        user_id=str(log.user_id),
        office_id=str(log.office_id),
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        old_value=log.old_value,
        new_value=log.new_value,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at,
    )


# ---------- GET /audit/logs ----------


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="Audit log listesi",
    description=(
        "KVKK denetim kayitlarini filtreleme ve sayfalama ile listeler. "
        "Sadece platform_admin rolu erisebilir."
    ),
    dependencies=[_require_admin],
)
async def list_audit_logs(
    db: DBSession,
    current_user: ActiveUser,
    page: int = Query(default=1, ge=1, description="Sayfa numarasi"),
    per_page: int = Query(
        default=50, ge=1, le=200, description="Sayfa basina kayit (max 200)"
    ),
    action: AuditActionFilter | None = Query(  # noqa: B008
        default=None, description="Eylem tipi filtresi"
    ),
    entity_type: str | None = Query(
        default=None, description="Varlik tipi filtresi (orn: Customer, Property)"
    ),
    entity_id: str | None = Query(
        default=None, description="Varlik UUID filtresi"
    ),
    user_id: str | None = Query(
        default=None, description="Kullanici UUID filtresi"
    ),
) -> AuditLogListResponse:
    """
    Audit log listesini filtrelerle getirir.

    - Sadece platform_admin erisebilir
    - Filtreler: action, entity_type, entity_id, user_id
    - Pagination: page + per_page
    - Siralama: created_at DESC (en yeni ilk)
    """
    office_id = current_user.office_id

    base_filter = [AuditLog.office_id == office_id]

    if action:
        base_filter.append(AuditLog.action == action)
    if entity_type:
        base_filter.append(AuditLog.entity_type == entity_type)
    if entity_id:
        base_filter.append(AuditLog.entity_id == entity_id)
    if user_id:
        base_filter.append(AuditLog.user_id == user_id)

    # Total count
    count_query = select(func.count(AuditLog.id)).where(*base_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginated results (en yeniden en eskiye)
    offset = (page - 1) * per_page
    query = (
        select(AuditLog)
        .where(*base_filter)
        .order_by(AuditLog.created_at.desc())
        .limit(per_page)
        .offset(offset)
    )
    result = await db.execute(query)
    logs = list(result.scalars().all())

    return AuditLogListResponse(
        items=[_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
    )


# ---------- GET /audit/logs/{id} ----------


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogResponse,
    summary="Audit log detayi",
    description="Belirtilen audit log kaydinin detaylarini dondurur.",
    dependencies=[_require_admin],
)
async def get_audit_log(
    log_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> AuditLogResponse:
    """
    Audit log detayini getirir.

    - Sadece platform_admin erisebilir
    - Sadece kendi ofisinin kayitlari gorulebilir (tenant isolation)
    - Kayit bulunamazsa 404
    """
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.id == log_id,
            AuditLog.office_id == current_user.office_id,
        )
    )
    log = result.scalar_one_or_none()

    if log is None:
        raise NotFoundError(resource="AuditLog", resource_id=str(log_id))

    return _to_response(log)
