"""Kredi hesaplayici router — calculator endpoint'leri."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import structlog
from fastapi import APIRouter, HTTPException

from src.modules.auth.dependencies import ActiveUser
from src.modules.calculator.bank_rates import get_bank_rates
from src.modules.calculator.calculator_schemas import (
    BankComparisonItem,
    BankComparisonRequest,
    BankComparisonResponse,
    BankRatesResponse,
    CreditCalculationRequest,
    CreditCalculationResponse,
)
from src.modules.calculator.calculator_service import CreditCalculatorService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/calculator",
    tags=["Calculator"],
)


# ---------- POST /credit ----------


@router.post(
    "/credit",
    response_model=CreditCalculationResponse,
    summary="Kredi hesaplama",
    description="Konut kredisi aylik taksit, toplam odeme, faiz ve amortisman tablosu hesaplar.",
)
async def calculate_credit(
    body: CreditCalculationRequest,
    user: ActiveUser,
) -> CreditCalculationResponse:
    """Kredi hesaplama endpoint'i.

    JWT zorunlu, tenant bagimsiz.
    """
    service = CreditCalculatorService

    # 1) Pesinat ve kredi tutarini hesapla
    down = service.calculate_down_payment(body.property_price, body.down_payment_percent)
    loan_amount: Decimal = down["loan_amount"]
    down_payment_amount: Decimal = down["down_payment_amount"]

    if loan_amount <= Decimal("0"):
        raise HTTPException(
            status_code=400,
            detail="Kredi tutari sifir veya negatif olamaz. Pesinat yuzdesini kontrol edin.",
        )

    # 2) Aylik taksit
    monthly_payment = service.calculate_monthly_payment(
        loan_amount,
        body.annual_interest_rate,
        body.term_months,
    )

    # 3) Toplam odeme ve faiz
    total_payment = service.calculate_total_payment(monthly_payment, body.term_months)
    total_interest = service.calculate_total_interest(total_payment, loan_amount)

    # 4) Faiz orani (faiz / toplam odeme)
    interest_ratio = (total_interest / total_payment).quantize(Decimal("0.0001"))

    # 5) Amortisman tablosu
    amortization_table = service.generate_amortization_table(
        loan_amount,
        body.annual_interest_rate,
        body.term_months,
    )

    logger.info(
        "credit_calculated",
        user_id=str(user.id),
        property_price=str(body.property_price),
        term_months=body.term_months,
    )

    return CreditCalculationResponse(
        property_price=body.property_price,
        down_payment_amount=down_payment_amount,
        loan_amount=loan_amount,
        monthly_payment=monthly_payment,
        total_payment=total_payment,
        total_interest=total_interest,
        interest_ratio=interest_ratio,
        amortization_table=amortization_table,
    )


# ---------- GET /rates ----------


@router.get(
    "/rates",
    response_model=BankRatesResponse,
    summary="Banka faiz oranlari",
    description="Guncel banka konut kredisi faiz oranlarini listeler.",
)
async def list_bank_rates(
    user: ActiveUser,
) -> BankRatesResponse:
    """Banka faiz oranlari endpoint'i.

    JWT zorunlu, tenant bagimsiz.
    """
    rates = get_bank_rates()

    logger.info("bank_rates_listed", user_id=str(user.id))

    return BankRatesResponse(
        rates=rates,
        source="seed_data",
        last_updated=datetime(2025, 2, 1, tzinfo=UTC),
    )


# ---------- POST /compare ----------


@router.post(
    "/compare",
    response_model=BankComparisonResponse,
    summary="Banka karsilastirma",
    description="Tum bankalarin faiz oranlariyla kredi hesaplamasi yapar ve karsilastirir.",
)
async def compare_banks(
    body: BankComparisonRequest,
    user: ActiveUser,
) -> BankComparisonResponse:
    """Banka karsilastirma endpoint'i.

    Tum bankalarin guncel faiz oranlariyla aylik taksit, toplam odeme ve
    toplam faiz hesaplar. JWT zorunlu, tenant bagimsiz.
    """
    service = CreditCalculatorService

    # 1) Pesinat ve kredi tutarini hesapla
    down = service.calculate_down_payment(body.property_price, body.down_payment_percent)
    loan_amount: Decimal = down["loan_amount"]

    if loan_amount <= Decimal("0"):
        raise HTTPException(
            status_code=400,
            detail="Kredi tutari sifir veya negatif olamaz. Pesinat yuzdesini kontrol edin.",
        )

    # 2) Tum bankalar icin hesaplama
    rates = get_bank_rates()
    comparisons: list[BankComparisonItem] = []

    for rate in rates:
        # Vade, bankanin min/max araligi disindaysa atla
        if body.term_months < rate.min_term or body.term_months > rate.max_term:
            continue

        # Kredi tutari, bankanin min/max araligi disindaysa atla
        if loan_amount < rate.min_amount or loan_amount > rate.max_amount:
            continue

        monthly = service.calculate_monthly_payment(
            loan_amount,
            rate.annual_rate,
            body.term_months,
        )
        total = service.calculate_total_payment(monthly, body.term_months)
        interest = service.calculate_total_interest(total, loan_amount)

        comparisons.append(
            BankComparisonItem(
                bank_name=rate.bank_name,
                annual_rate=rate.annual_rate,
                monthly_payment=monthly,
                total_payment=total,
                total_interest=interest,
            )
        )

    # En dusuk taksit sirala
    comparisons.sort(key=lambda c: c.monthly_payment)

    logger.info(
        "bank_comparison_done",
        user_id=str(user.id),
        property_price=str(body.property_price),
        term_months=body.term_months,
        bank_count=len(comparisons),
    )

    return BankComparisonResponse(
        property_price=body.property_price,
        loan_amount=loan_amount,
        term_months=body.term_months,
        comparisons=comparisons,
    )
