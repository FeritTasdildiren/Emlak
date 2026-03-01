"""Kredi hesaplayici schemalar — request / response modelleri."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Pydantic runtime'da gerekli
from decimal import Decimal

from pydantic import BaseModel, Field

# ---------- Request ----------


class CreditCalculationRequest(BaseModel):
    """Kredi hesaplama istegi."""

    property_price: Decimal = Field(..., gt=0, description="Konut fiyati (TL)")
    down_payment_percent: Decimal = Field(
        default=Decimal("20"),
        ge=0,
        le=100,
        description="Pesinat yuzdesi",
    )
    annual_interest_rate: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Yillik faiz orani (%)",
    )
    term_months: int = Field(..., gt=0, le=360, description="Vade suresi (ay)")


# ---------- Response ----------


class AmortizationRow(BaseModel):
    """Amortisman tablosu tek satiri."""

    month: int = Field(..., description="Taksit no")
    payment: Decimal = Field(..., description="Aylik odeme (TL)")
    principal_part: Decimal = Field(..., description="Anapara payi (TL)")
    interest_part: Decimal = Field(..., description="Faiz payi (TL)")
    remaining_balance: Decimal = Field(..., description="Kalan borc (TL)")


class CreditCalculationResponse(BaseModel):
    """Kredi hesaplama sonucu."""

    property_price: Decimal = Field(..., description="Konut fiyati (TL)")
    down_payment_amount: Decimal = Field(..., description="Pesinat tutari (TL)")
    loan_amount: Decimal = Field(..., description="Kredi tutari (TL)")
    monthly_payment: Decimal = Field(..., description="Aylik taksit (TL)")
    total_payment: Decimal = Field(..., description="Toplam odeme (TL)")
    total_interest: Decimal = Field(..., description="Toplam faiz (TL)")
    interest_ratio: Decimal = Field(
        ...,
        ge=0,
        le=1,
        description="Faiz / toplam odeme orani (0-1)",
    )
    amortization_table: list[AmortizationRow] = Field(
        ...,
        description="Amortisman tablosu",
    )


# ---------- Banka Faiz ----------


class BankRate(BaseModel):
    """Tek banka faiz bilgisi."""

    model_config = {"from_attributes": True}

    bank_name: str = Field(..., description="Banka adi")
    annual_rate: Decimal = Field(..., description="Yillik faiz orani (%)")
    min_term: int = Field(..., description="Minimum vade (ay)")
    max_term: int = Field(..., description="Maksimum vade (ay)")
    min_amount: Decimal = Field(..., description="Minimum kredi tutari (TL)")
    max_amount: Decimal = Field(..., description="Maksimum kredi tutari (TL)")
    is_active: bool = Field(default=True, description="Aktif mi")
    update_source: str = Field(default="manual", description="Guncelleme kaynagi")
    updated_at: datetime = Field(..., description="Son guncelleme tarihi")


class BankRatesResponse(BaseModel):
    """Banka faiz oranları listesi."""

    rates: list[BankRate] = Field(..., description="Banka faiz oranlari")
    source: str = Field(..., description="Veri kaynagi")
    last_updated: datetime = Field(..., description="Son guncelleme tarihi")


# ---------- Banka Karsilastirma ----------


class BankRateUpdateRequest(BaseModel):
    """Admin tek banka faiz orani guncelleme istegi (PUT /admin/bank-rates/{bank_name})."""

    annual_rate: Decimal | None = Field(
        default=None, gt=0, le=100, description="Yillik faiz orani (%)"
    )
    min_term: int | None = Field(
        default=None, gt=0, le=360, description="Minimum vade (ay)"
    )
    max_term: int | None = Field(
        default=None, gt=0, le=360, description="Maksimum vade (ay)"
    )
    min_amount: Decimal | None = Field(
        default=None, gt=0, description="Minimum kredi tutari (TL)"
    )
    max_amount: Decimal | None = Field(
        default=None, gt=0, description="Maksimum kredi tutari (TL)"
    )
    is_active: bool | None = Field(default=None, description="Aktif mi")


class BankRateUpdateItem(BaseModel):
    """Toplu guncelleme icin tek banka bilgisi."""

    bank_name: str = Field(..., description="Banka adi")
    annual_rate: Decimal = Field(..., gt=0, le=100, description="Yillik faiz orani (%)")
    min_term: int | None = Field(default=None, description="Minimum vade (ay)")
    max_term: int | None = Field(default=None, description="Maksimum vade (ay)")
    min_amount: Decimal | None = Field(default=None, description="Minimum kredi tutari (TL)")
    max_amount: Decimal | None = Field(default=None, description="Maksimum kredi tutari (TL)")
    is_active: bool | None = Field(default=None, description="Aktif mi")


class BankRateBulkUpdateRequest(BaseModel):
    """Admin toplu banka faiz orani guncelleme istegi (PUT /admin/bank-rates)."""

    rates: list[BankRateUpdateItem] = Field(
        ..., min_length=1, description="Guncellenecek banka oranlari"
    )


class BankComparisonRequest(BaseModel):
    """Banka karsilastirma istegi."""

    property_price: Decimal = Field(..., gt=0, description="Konut fiyati (TL)")
    down_payment_percent: Decimal = Field(
        default=Decimal("20"),
        ge=0,
        le=100,
        description="Pesinat yuzdesi",
    )
    term_months: int = Field(..., gt=0, le=360, description="Vade suresi (ay)")


class BankComparisonItem(BaseModel):
    """Tek banka icin kredi karsilastirma sonucu."""

    bank_name: str = Field(..., description="Banka adi")
    annual_rate: Decimal = Field(..., description="Yillik faiz orani (%)")
    monthly_payment: Decimal = Field(..., description="Aylik taksit (TL)")
    total_payment: Decimal = Field(..., description="Toplam odeme (TL)")
    total_interest: Decimal = Field(..., description="Toplam faiz (TL)")


class BankComparisonResponse(BaseModel):
    """Tum bankalarin kredi karsilastirma sonucu."""

    property_price: Decimal = Field(..., description="Konut fiyati (TL)")
    loan_amount: Decimal = Field(..., description="Kredi tutari (TL)")
    term_months: int = Field(..., description="Vade suresi (ay)")
    comparisons: list[BankComparisonItem] = Field(
        ...,
        description="Banka bazinda karsilastirma sonuclari",
    )
