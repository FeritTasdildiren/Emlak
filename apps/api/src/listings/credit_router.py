"""
Emlak Teknoloji Platformu - Credit Router

Kredi satin alma ve bakiye sorgulama endpoint'leri.

Prefix: /api/v1/credits
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser).
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from src.core.exceptions import ValidationError
from src.dependencies import DBSession  # noqa: TC001 — FastAPI runtime
from src.models.subscription import Subscription
from src.modules.auth.dependencies import ActiveUser  # noqa: TC001 — FastAPI runtime
from src.modules.valuations.quota_service import (
    QuotaType,
    add_credits,
    get_credit_balance,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/credits",
    tags=["credits"],
)


# ---------- Schemas ----------


class CreditPurchaseRequest(BaseModel):
    """Kredi satin alma istegi."""

    quota_type: str = Field(
        ...,
        description="Kota tipi: valuation, listing, staging, photo",
        examples=["valuation"],
    )
    amount: int = Field(
        ...,
        gt=0,
        le=1000,
        description="Satin alinacak kredi miktari (1-1000)",
    )


class CreditPurchaseResponse(BaseModel):
    """Kredi satin alma yaniti."""

    new_balance: int = Field(..., description="Guncel kredi bakiyesi")
    purchased: int = Field(..., description="Satin alinan miktar")


class CreditBalanceResponse(BaseModel):
    """Kredi bakiye yaniti."""

    credit_balance: int = Field(..., description="Mevcut kredi bakiyesi")
    plan_type: str = Field(..., description="Aktif abonelik plani")


# ---------- Yardimci ----------


async def _get_plan_type(db: DBSession, office_id: str) -> str:
    """Ofis'in aktif abonelik planini dondurur. Bulunamazsa 'starter' varsayar."""
    from sqlalchemy import select

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


# ---------- Endpoints ----------


@router.post(
    "/purchase",
    response_model=CreditPurchaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Kredi satin al",
    description=(
        "Belirtilen miktarda kredi satin alir. "
        "Kredi, kota asiminda ek islem yapabilmek icin kullanilir."
    ),
)
async def purchase_credits(
    body: CreditPurchaseRequest,
    db: DBSession,
    user: ActiveUser,
) -> CreditPurchaseResponse:
    """
    Kredi satin alma endpoint'i.

    Akis:
        1. quota_type dogrulamasi
        2. Plan tipini bul
        3. credit_balance'a ekleme yap
        4. Yeni bakiyeyi dondur
    """
    # quota_type dogrulama
    try:
        QuotaType(body.quota_type)
    except ValueError as exc:
        valid = [qt.value for qt in QuotaType]
        raise ValidationError(
            detail=f"Gecersiz kota tipi: '{body.quota_type}'. Gecerli degerler: {valid}",
        ) from exc

    office_id = str(user.office_id)
    plan_type = await _get_plan_type(db, office_id)

    quota = await add_credits(
        db=db,
        office_id=user.office_id,
        plan=plan_type,
        amount=body.amount,
    )

    logger.info(
        "credits_purchased",
        user_id=str(user.id),
        office_id=office_id,
        amount=body.amount,
        new_balance=quota.credit_balance,
    )

    return CreditPurchaseResponse(
        new_balance=quota.credit_balance,
        purchased=body.amount,
    )


@router.get(
    "/balance",
    response_model=CreditBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Kredi bakiyesi sorgula",
    description="Mevcut kredi bakiyesini ve aktif plan bilgisini dondurur.",
)
async def get_balance(
    db: DBSession,
    user: ActiveUser,
) -> CreditBalanceResponse:
    """
    Kredi bakiye sorgulama endpoint'i.

    Akis:
        1. Plan tipini bul
        2. credit_balance'i getir
        3. CreditBalanceResponse dondur
    """
    office_id = str(user.office_id)
    plan_type = await _get_plan_type(db, office_id)

    balance = await get_credit_balance(
        db=db,
        office_id=user.office_id,
        plan=plan_type,
    )

    return CreditBalanceResponse(
        credit_balance=balance,
        plan_type=plan_type,
    )
