"""
Emlak Teknoloji Platformu - Transaction Router

Odeme islem kayitlari (transaction) API endpoint'leri.

Prefix: /api/v1/transactions
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser dependency).
Tenant izolasyonu: office_id otomatik olarak JWT'den alinir.

Endpoint'ler:
    GET /transactions                → Islem listesi (filtreleme + sayfalama)
    GET /transactions/{id}           → Islem detayi
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import func, select

if TYPE_CHECKING:
    import uuid

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.transaction import Transaction
from src.modules.auth.dependencies import ActiveUser
from src.modules.payments.transaction_schemas import (
    TransactionListResponse,
    TransactionResponse,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["transactions"],
)


def _to_response(txn: Transaction) -> TransactionResponse:
    """Transaction entity'sini response modeline donusturur."""
    return TransactionResponse(
        id=str(txn.id),
        payment_id=str(txn.payment_id),
        office_id=str(txn.office_id),
        type=txn.type,
        amount=float(txn.amount),
        status=txn.status,
        external_transaction_id=txn.external_transaction_id,
        metadata=txn.metadata_ if txn.metadata_ else {},
        error_message=txn.error_message,
        created_at=txn.created_at,
        updated_at=txn.updated_at,
    )


# ---------- GET /transactions ----------


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="Islem listesi",
    description="Ofise ait odeme islemlerini filtreleme ve sayfalama ile listeler.",
)
async def list_transactions(
    db: DBSession,
    current_user: ActiveUser,
    page: int = Query(default=1, ge=1, description="Sayfa numarasi"),
    per_page: int = Query(
        default=20, ge=1, le=100, description="Sayfa basina kayit (max 100)"
    ),
    payment_id: str | None = Query(
        default=None, description="Odeme UUID filtresi"
    ),
    type: str | None = Query(
        default=None,
        description="Islem tipi filtresi: charge, refund, void, adjustment",
    ),
    status: str | None = Query(
        default=None, description="Durum filtresi: pending, completed, failed"
    ),
) -> TransactionListResponse:
    """
    Ofise ait islemleri listeler.

    - Sonuclar varsayilan olarak en yeniden en eskiye siralanir
    - Filtreler: payment_id, type, status
    - Pagination: page + per_page
    """
    office_id = current_user.office_id

    base_filter = [Transaction.office_id == office_id]

    if payment_id:
        base_filter.append(Transaction.payment_id == payment_id)
    if type:
        base_filter.append(Transaction.type == type)
    if status:
        base_filter.append(Transaction.status == status)

    # Total count
    count_query = select(func.count(Transaction.id)).where(*base_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginated results (en yeniden en eskiye)
    offset = (page - 1) * per_page
    query = (
        select(Transaction)
        .where(*base_filter)
        .order_by(Transaction.created_at.desc())
        .limit(per_page)
        .offset(offset)
    )
    result = await db.execute(query)
    transactions = list(result.scalars().all())

    return TransactionListResponse(
        items=[_to_response(txn) for txn in transactions],
        total=total,
        page=page,
        per_page=per_page,
    )


# ---------- GET /transactions/{id} ----------


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Islem detayi",
    description="Belirtilen odeme isleminin detaylarini dondurur.",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> TransactionResponse:
    """
    Islem detayini getirir.

    - Sadece kendi ofisinin islemleri gorulebilir (tenant isolation)
    - Islem bulunamazsa 404
    """
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.office_id == current_user.office_id,
        )
    )
    txn = result.scalar_one_or_none()

    if txn is None:
        raise NotFoundError(resource="Transaction", resource_id=str(transaction_id))

    return _to_response(txn)
