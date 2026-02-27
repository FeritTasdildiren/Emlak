"""
Emlak Teknoloji Platformu - Fiyat Anomali Tespiti Servisi

Degerleme sonucundaki fiyati bolge ortalamasi ile karsilastirip
istatistiksel anomali tespiti yapar (z-score yontemi).

Veri kaynaklari (oncelik sirasina gore):
  1. AreaAnalysis tablosu — ilce bazinda m2 ortalama satis fiyati
  2. PredictionLog tablosu — son 50 tahmin kaydindan hesaplanan ortalama (fallback)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import Float, cast, select
from sqlalchemy import func as sa_func

from src.models.area_analysis import AreaAnalysis
from src.models.prediction_log import PredictionLog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


# =====================================================================
# Result Model
# =====================================================================


class AnomalyResult(BaseModel):
    """Fiyat anomali tespit sonucu."""

    is_anomaly: bool = Field(description="Anomali tespit edildi mi?")
    z_score: float = Field(description="Z-score degeri (|z| > 2.0 → anomali)")
    district_avg_sqm_price: float = Field(
        description="Ilce ortalama m2 fiyati (TL)"
    )
    anomaly_reason: str | None = Field(
        default=None,
        description="Anomali aciklamasi (anomali yoksa None)",
    )


# =====================================================================
# Z-Score Esik Degeri
# =====================================================================

_Z_SCORE_THRESHOLD = 2.0

# Fallback icin PredictionLog'dan cekilecek maksimum kayit sayisi
_FALLBACK_LOG_LIMIT = 50


# =====================================================================
# Ana Fonksiyon
# =====================================================================


async def check_price_anomaly(
    predicted_price: float,
    district: str,
    net_sqm: float,
    session: AsyncSession,
) -> AnomalyResult:
    """
    Tahmin edilen fiyati bolge ortalamasi ile karsilastirip anomali tespit eder.

    Algoritma:
        1. AreaAnalysis tablosundan ilce m2 ortalama satis fiyatini cek.
        2. AreaAnalysis yoksa PredictionLog'dan son N kaydin ortalamasini hesapla.
        3. Z-score hesapla: |predicted_sqm - avg_sqm| / std_sqm
        4. |z| > 2.0 ise anomali olarak isaretler.

    Args:
        predicted_price: ML modelin tahmini fiyat (TL).
        district: Ilce adi.
        net_sqm: Mulkun net metrekaresi.
        session: Async DB session.

    Returns:
        AnomalyResult: Anomali durumu, z-score ve aciklama.
    """
    predicted_sqm_price = predicted_price / max(net_sqm, 1.0)

    # --- 1. AreaAnalysis'ten ilce ortalama m2 fiyatini cek ---
    avg_sqm_price, std_sqm_price = await _get_area_stats(district, session)

    source = "area_analysis"

    # --- 2. Fallback: PredictionLog ---
    if avg_sqm_price is None:
        avg_sqm_price, std_sqm_price = await _get_prediction_log_stats(
            district, session
        )
        source = "prediction_log"

    # --- 3. Veri yoksa anomali tespit edilemez ---
    if avg_sqm_price is None or avg_sqm_price <= 0:
        logger.info(
            "anomaly_check_no_data",
            district=district,
        )
        return AnomalyResult(
            is_anomaly=False,
            z_score=0.0,
            district_avg_sqm_price=0.0,
            anomaly_reason=None,
        )

    # std_sqm_price 0 veya None ise z-score hesaplanamaz
    if std_sqm_price is None or std_sqm_price <= 0:
        # Standart sapma yoksa ortalamadan yuzde sapma ile basit kontrol
        pct_diff = abs(predicted_sqm_price - avg_sqm_price) / avg_sqm_price * 100
        z_score = pct_diff / 50.0  # %100 sapma ≈ z=2
    else:
        z_score = abs(predicted_sqm_price - avg_sqm_price) / std_sqm_price

    is_anomaly = z_score > _Z_SCORE_THRESHOLD

    anomaly_reason: str | None = None
    if is_anomaly:
        pct = round(
            (predicted_sqm_price - avg_sqm_price) / avg_sqm_price * 100, 1
        )
        direction = "yukarida" if pct > 0 else "asagida"
        anomaly_reason = (
            f"Tahmin edilen m2 fiyati ({predicted_sqm_price:,.0f} TL) "
            f"bolge ortalamasindan ({avg_sqm_price:,.0f} TL) "
            f"%{abs(pct)} {direction} sapma gosteriyor."
        )

    logger.info(
        "anomaly_check_completed",
        district=district,
        predicted_sqm_price=round(predicted_sqm_price, 2),
        avg_sqm_price=round(avg_sqm_price, 2),
        z_score=round(z_score, 4),
        is_anomaly=is_anomaly,
        source=source,
    )

    return AnomalyResult(
        is_anomaly=is_anomaly,
        z_score=round(z_score, 4),
        district_avg_sqm_price=round(avg_sqm_price, 2),
        anomaly_reason=anomaly_reason,
    )


# =====================================================================
# Yardimci Fonksiyonlar
# =====================================================================


async def _get_area_stats(
    district: str,
    session: AsyncSession,
) -> tuple[float | None, float | None]:
    """
    AreaAnalysis tablosundan ilce bazinda m2 ortalama satis fiyatini ceker.

    Ayni ilcenin birden fazla kaydi (mahalle bazinda) olabilir,
    bu nedenle AVG ile birlestiriyoruz.

    Returns:
        (avg_sqm_price, std_sqm_price) — veri yoksa (None, None).
    """
    stmt = select(
        sa_func.avg(AreaAnalysis.avg_price_sqm_sale).label("avg_sqm"),
        sa_func.stddev_pop(AreaAnalysis.avg_price_sqm_sale).label("std_sqm"),
    ).where(
        sa_func.lower(AreaAnalysis.district) == sa_func.lower(district),
        AreaAnalysis.avg_price_sqm_sale.is_not(None),
    )

    result = await session.execute(stmt)
    row = result.one_or_none()

    if row is None or row.avg_sqm is None:
        return None, None

    avg_val = float(row.avg_sqm)
    std_val = float(row.std_sqm) if row.std_sqm is not None else None

    return avg_val, std_val


async def _get_prediction_log_stats(
    district: str,
    session: AsyncSession,
) -> tuple[float | None, float | None]:
    """
    PredictionLog tablosundan son N kaydin m2 fiyat istatistiklerini hesaplar.

    input_data JSONB icerisinden 'district' ve 'net_sqm' alanlari,
    output_data'dan 'estimated_price' alani kullanilir.

    Returns:
        (avg_sqm_price, std_sqm_price) — veri yoksa (None, None).
    """
    # Son N kaydi sub-select ile al, sonra istatistik hesapla
    # PredictionLog.input_data['district'] filtresi
    subq = (
        select(
            (
                cast(
                    PredictionLog.output_data["estimated_price"].as_float(),
                    Float,
                )
                / sa_func.greatest(
                    cast(
                        PredictionLog.input_data["net_sqm"].as_float(),
                        Float,
                    ),
                    1.0,
                )
            ).label("sqm_price"),
        )
        .where(
            PredictionLog.input_data["district"].as_string()
            == district,
        )
        .order_by(PredictionLog.created_at.desc())
        .limit(_FALLBACK_LOG_LIMIT)
        .subquery()
    )

    stmt = select(
        sa_func.avg(subq.c.sqm_price).label("avg_sqm"),
        sa_func.stddev_pop(subq.c.sqm_price).label("std_sqm"),
    )

    result = await session.execute(stmt)
    row = result.one_or_none()

    if row is None or row.avg_sqm is None:
        return None, None

    avg_val = float(row.avg_sqm)
    std_val = float(row.std_sqm) if row.std_sqm is not None else None

    # NaN kontrolu (stddev_pop tek kayitta NaN verebilir)
    if std_val is not None and math.isnan(std_val):
        std_val = None

    return avg_val, std_val
