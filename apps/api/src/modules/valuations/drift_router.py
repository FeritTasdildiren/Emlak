"""
Emlak Teknoloji Platformu - Drift Monitor Router

ML model drift izleme admin endpoint'leri.

Prefix: /api/v1/valuations/drift
Guvenlik: Tum endpoint'ler JWT + platform_admin rolu gerektirir.

Endpoint'ler:
    GET /api/v1/valuations/drift/report       -> Tam drift raporu
    GET /api/v1/valuations/drift/distribution  -> Giris dagilim analizi
    GET /api/v1/valuations/drift/confidence    -> Confidence trend

Referans: TASK-067
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query

from src.dependencies import DBSession
from src.ml.drift_monitor import DriftMonitor
from src.modules.auth.dependencies import require_role

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/valuations/drift",
    tags=["valuations", "admin", "drift"],
    dependencies=[Depends(require_role("platform_admin"))],
)


# ---------- GET /report ----------


@router.get(
    "/report",
    summary="Tam drift raporu",
    description=(
        "Giris dagilimi, confidence trend ve tahmin istatistiklerini iceren "
        "kapsamli drift raporu. PSI hesaplamasi ve alert seviyeleri dahil."
    ),
)
async def get_drift_report(db: DBSession) -> dict:
    """
    Birlesik drift raporu.

    Icerik:
        - input_distribution: Giris dagilimi + PSI
        - confidence_trend: Gunluk confidence + 7g hareketli ortalama
        - prediction_stats: Toplam tahmin, latency, fiyat istatistikleri
        - overall_status: GREEN | YELLOW | RED
        - alerts: Tespit edilen sorunlar
    """
    monitor = DriftMonitor(db)
    report = await monitor.generate_drift_report()

    logger.info(
        "drift_report_generated",
        overall_status=report["overall_status"],
        alert_count=len(report["alerts"]),
    )

    return report


# ---------- GET /distribution ----------


@router.get(
    "/distribution",
    summary="Giris dagilim analizi",
    description=(
        "Son X gundeki tahmin girislerinin dagilim analizi. "
        "Egitim verisindeki referans dagilimla PSI karsilastirmasi yapar."
    ),
)
async def get_distribution(
    db: DBSession,
    days: int = Query(
        default=7, ge=1, le=90, description="Analiz suresi (gun)"
    ),
) -> dict:
    """
    Giris verisi dagilim analizi.

    Parametreler:
        days: Kac gunluk veri analiz edilsin (varsayilan: 7)
    """
    monitor = DriftMonitor(db)
    return await monitor.check_input_distribution(days=days)


# ---------- GET /confidence ----------


@router.get(
    "/confidence",
    summary="Confidence trend",
    description=(
        "Confidence skorunun zaman icindeki trendi. "
        "Gunluk ortalama ve 7 gunluk hareketli ortalama hesaplar."
    ),
)
async def get_confidence_trend(
    db: DBSession,
    days: int = Query(
        default=30, ge=1, le=180, description="Analiz suresi (gun)"
    ),
) -> dict:
    """
    Confidence trend analizi.

    Parametreler:
        days: Kac gunluk trend gosterilsin (varsayilan: 30)

    Alert seviyeleri:
        - 7g ortalama < 0.7 → WARNING
        - 7g ortalama < 0.5 → ALARM
    """
    monitor = DriftMonitor(db)
    return await monitor.check_confidence_trend(days=days)
