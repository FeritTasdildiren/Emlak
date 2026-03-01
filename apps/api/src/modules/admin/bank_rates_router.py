"""
Emlak Teknoloji Platformu - Admin Bank Rates Router

Banka faiz oranlari yonetim endpoint'leri.

Prefix: /admin/bank-rates
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser + platform_admin rolu).
          PUBLIC_PATHS'e EKLENMEZ — TenantMiddleware JWT dogrulamasi zorunlu.

Endpoint'ler:
    GET    /admin/bank-rates               -> Tum banka oranlarini listele (aktif + pasif)
    PUT    /admin/bank-rates/{bank_name}   -> Tek banka oranini guncelle
    PUT    /admin/bank-rates               -> Toplu banka orani guncelleme

Referans: TASK-193
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.bank_rate import BankRate as BankRateModel
from src.modules.auth.dependencies import require_role
from src.modules.calculator.calculator_schemas import (
    BankRate,
    BankRateBulkUpdateRequest,
    BankRateUpdateRequest,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/admin/bank-rates",
    tags=["admin", "bank-rates"],
    # Tum endpoint'ler platform_admin rolu gerektirir
    dependencies=[Depends(require_role("platform_admin"))],
)


# ---------- GET /admin/bank-rates ----------


@router.get(
    "",
    response_model=list[BankRate],
    summary="Tum banka faiz oranlari (admin)",
    description="Aktif ve pasif tum banka oranlarini listeler. Admin only.",
)
async def list_all_bank_rates(
    db: DBSession,
) -> list[BankRate]:
    """Tum banka oranlarini getirir (aktif + pasif).

    Admin panelinde oran yonetimi icin kullanilir.
    """
    stmt = select(BankRateModel).order_by(BankRateModel.annual_rate.asc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    logger.info("admin_bank_rates_listed", count=len(rows))

    return [BankRate.model_validate(row) for row in rows]


# ---------- PUT /admin/bank-rates/{bank_name} ----------


@router.put(
    "/{bank_name}",
    response_model=BankRate,
    summary="Tek banka faiz orani guncelle",
    description="Belirtilen bankanin faiz oranini ve diger parametrelerini gunceller.",
)
async def update_bank_rate(
    bank_name: str,
    body: BankRateUpdateRequest,
    db: DBSession,
) -> BankRate:
    """Tek banka faiz oranini gunceller.

    Sadece gonderilen alanlar guncellenir (partial update).
    update_source otomatik olarak 'manual' set edilir.
    """
    stmt = select(BankRateModel).where(BankRateModel.bank_name == bank_name)
    result = await db.execute(stmt)
    rate = result.scalar_one_or_none()

    if rate is None:
        raise NotFoundError(detail=f"Banka bulunamadi: {bank_name}")

    # Partial update — sadece gonderilen alanlar
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rate, field, value)

    # Meta alanlar
    rate.update_source = "manual"
    rate.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(rate)

    logger.info(
        "admin_bank_rate_updated",
        bank_name=bank_name,
        updated_fields=list(update_data.keys()),
    )

    return BankRate.model_validate(rate)


# ---------- PUT /admin/bank-rates ----------


@router.put(
    "",
    response_model=list[BankRate],
    summary="Toplu banka faiz orani guncelle",
    description="Birden fazla bankanin faiz oranlarini tek seferde gunceller (UPSERT).",
)
async def bulk_update_bank_rates(
    body: BankRateBulkUpdateRequest,
    db: DBSession,
) -> list[BankRate]:
    """Toplu banka faiz orani guncelleme.

    UPSERT mantigi: mevcut banka varsa guncelle, yoksa yeni kayit olustur.
    update_source otomatik olarak 'manual' set edilir.
    """
    updated_rates: list[BankRate] = []

    for item in body.rates:
        stmt = select(BankRateModel).where(BankRateModel.bank_name == item.bank_name)
        result = await db.execute(stmt)
        rate = result.scalar_one_or_none()

        if rate is None:
            # Yeni banka ekle
            rate = BankRateModel(
                bank_name=item.bank_name,
                annual_rate=item.annual_rate,
                min_term=item.min_term or 12,
                max_term=item.max_term or 120,
                min_amount=item.min_amount or 100_000,
                max_amount=item.max_amount or 10_000_000,
                is_active=item.is_active if item.is_active is not None else True,
                update_source="manual",
                updated_at=datetime.now(UTC),
            )
            db.add(rate)
        else:
            # Mevcut banka guncelle
            rate.annual_rate = item.annual_rate
            if item.min_term is not None:
                rate.min_term = item.min_term
            if item.max_term is not None:
                rate.max_term = item.max_term
            if item.min_amount is not None:
                rate.min_amount = item.min_amount
            if item.max_amount is not None:
                rate.max_amount = item.max_amount
            if item.is_active is not None:
                rate.is_active = item.is_active
            rate.update_source = "manual"
            rate.updated_at = datetime.now(UTC)

        await db.flush()
        await db.refresh(rate)
        updated_rates.append(BankRate.model_validate(rate))

    logger.info(
        "admin_bank_rates_bulk_updated",
        count=len(updated_rates),
        banks=[r.bank_name for r in updated_rates],
    )

    return updated_rates
