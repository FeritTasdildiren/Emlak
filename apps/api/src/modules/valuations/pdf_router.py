"""
Emlak Teknoloji Platformu - Valuations PDF Router

Degerleme raporu PDF indirme endpoint'i.

Prefix: /api/v1/valuations
Guvenlik: JWT zorunlu (ActiveUser).
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

import structlog
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.prediction_log import PredictionLog
from src.models.price_history import PriceHistory
from src.modules.auth.dependencies import ActiveUser
from src.modules.valuations.comparable_service import ComparableService
from src.services.pdf_service import generate_valuation_pdf

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/valuations",
    tags=["valuations", "pdf"],
)

# ---------- Yardimci fonksiyonlar ----------

_MONTH_NAMES_TR = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık",
}


def _build_office_info(user: object) -> dict | None:
    """ActiveUser'in bagli ofis bilgilerini dict olarak dondurur."""
    office = getattr(user, "office", None)
    if office is None:
        return None

    return {
        "name": office.name,
        "logo_url": getattr(office, "logo_url", None),
        "phone": getattr(office, "phone", None),
        "email": getattr(office, "email", None),
    }


def _build_user_info(user: object) -> dict | None:
    """ActiveUser'dan danisman bilgisini dict olarak dondurur."""
    full_name = getattr(user, "full_name", None)
    if not full_name:
        return None

    return {
        "full_name": full_name,
        "email": getattr(user, "email", None),
        "phone": getattr(user, "phone", None),
    }


def _format_area_trend(rows: list) -> list[dict]:
    """
    PriceHistory satirlarini template-uyumlu trend listesine donusturur.

    Satirlar tarih ASC sirali gelmeli.
    Her satir icin bir onceki aya gore degisim yuzdesi (change_pct) hesaplanir.
    """
    trend: list[dict] = []
    prev_avg: float | None = None

    for row in rows:
        avg_sqm = float(row.avg_price_sqm) if row.avg_price_sqm else 0
        median = float(row.median_price) if row.median_price else 0
        count = row.listing_count or 0
        period = f"{_MONTH_NAMES_TR.get(row.date.month, '')} {row.date.year}"

        change_pct: float | None = None
        if prev_avg and prev_avg > 0 and avg_sqm > 0:
            change_pct = round(((avg_sqm - prev_avg) / prev_avg) * 100, 1)

        trend.append(
            {
                "period": period,
                "avg_price_sqm": avg_sqm,
                "median_price": median,
                "listing_count": count,
                "change_pct": change_pct,
            }
        )
        prev_avg = avg_sqm if avg_sqm > 0 else prev_avg

    return trend


async def _fetch_area_trend(
    db: object,
    district: str,
    months: int = 6,
) -> list[dict]:
    """
    Ilce bazinda son N ayin fiyat trendini PriceHistory'den ceker.

    Returns:
        Template'e uygun trend dict listesi (kronolojik sira).
        Veri yoksa bos liste.
    """
    cutoff = date.today() - timedelta(days=months * 31)

    stmt = (
        select(PriceHistory)
        .where(
            PriceHistory.area_type == "district",
            PriceHistory.area_name.ilike(district),
            PriceHistory.date >= cutoff,
        )
        .order_by(PriceHistory.date.asc())
        .limit(months)
    )

    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        return []

    return _format_area_trend(rows)


# ---------- Endpoint ----------


@router.get(
    "/{prediction_id}/pdf",
    summary="Degerleme raporu PDF indir",
    description=(
        "Belirtilen prediction_id icin AI degerleme raporu PDF'i olusturur. "
        "Rapor; mulk bilgileri, degerleme sonucu, bolge analizi, bolge fiyat "
        "trendi ve emsal karsilastirma bolumlerini icerir. Firma logosu ve "
        "danisman bilgisi JWT'den otomatik olarak eklenir."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF degerleme raporu",
        },
        404: {"description": "Tahmin kaydı bulunamadi"},
    },
)
async def download_valuation_pdf(
    prediction_id: str,
    db: DBSession,
    user: ActiveUser,
) -> StreamingResponse:
    """
    Degerleme raporu PDF indirme endpoint'i.

    Akis:
        1. PredictionLog'u prediction_id ile bul
        2. Office ve User bilgilerini JWT'den al
        3. Emsal, bolge istatistikleri ve fiyat trendi getir (opsiyonel)
        4. PDF olustur (WeasyPrint, asyncio.to_thread)
        5. StreamingResponse ile dondur
    """
    # 1. PredictionLog'u getir
    stmt = select(PredictionLog).where(PredictionLog.id == prediction_id)
    result = await db.execute(stmt)
    prediction = result.scalar_one_or_none()

    if prediction is None:
        raise NotFoundError(resource="Degerleme kaydi", resource_id=prediction_id)

    # 2. Veri hazirla
    input_data: dict = prediction.input_data
    output_data: dict = prediction.output_data

    report_date = prediction.created_at.strftime("%d.%m.%Y")

    valuation_data: dict = {
        # Rapor meta
        "prediction_id": str(prediction.id),
        "report_date": report_date,
        "model_version": prediction.model_version,
        # Mulk bilgileri (input_data)
        "district": input_data.get("district", "—"),
        "neighborhood": input_data.get("neighborhood", "—"),
        "property_type": input_data.get("property_type", "—"),
        "net_sqm": input_data.get("net_sqm", 0),
        "gross_sqm": input_data.get("gross_sqm", 0),
        "room_count": input_data.get("room_count", 0),
        "living_room_count": input_data.get("living_room_count", 0),
        "floor": input_data.get("floor", 0),
        "total_floors": input_data.get("total_floors", 0),
        "building_age": input_data.get("building_age", 0),
        "heating_type": input_data.get("heating_type", "—"),
        # Degerleme sonucu (output_data)
        "estimated_price": output_data.get("estimated_price", 0),
        "min_price": output_data.get("min_price", 0),
        "max_price": output_data.get("max_price", 0),
        "price_per_sqm": output_data.get("price_per_sqm", 0),
        # Model metrikleri
        "confidence": prediction.confidence or 0.0,
        # Firma ve danisman bilgileri (JWT'den)
        "office_info": _build_office_info(user),
        "user_info": _build_user_info(user),
        # Opsiyonel (asagida doldurulacak)
        "comparables": [],
        "area_stats": None,
        "area_trend": None,
    }

    # 3. Emsal, bolge istatistikleri ve fiyat trendi getir (hata olursa atla)
    district = input_data.get("district", "")
    estimated_price = output_data.get("estimated_price", 0)

    if district:
        try:
            comparable_service = ComparableService(db)

            comparables, area_stats, area_trend = await asyncio.gather(
                comparable_service.find_comparables_enriched(
                    district=district,
                    property_type=input_data.get("property_type", "Daire"),
                    net_sqm=input_data.get("net_sqm", 100),
                    room_count=input_data.get("room_count", 3),
                    building_age=input_data.get("building_age", 5),
                    estimated_price=estimated_price,
                    lat=input_data.get("lat"),
                    lon=input_data.get("lon"),
                ),
                comparable_service.get_area_stats(district=district),
                _fetch_area_trend(db, district=district),
            )

            valuation_data["comparables"] = comparables
            valuation_data["area_stats"] = area_stats
            valuation_data["area_trend"] = area_trend if area_trend else None
        except Exception:
            logger.warning(
                "pdf_supplementary_data_failed",
                prediction_id=prediction_id,
                district=district,
                exc_info=True,
            )

    # 4. PDF olustur (sync WeasyPrint -> asyncio.to_thread)
    pdf_bytes: bytes = await asyncio.to_thread(generate_valuation_pdf, valuation_data)

    logger.info(
        "pdf_download_started",
        prediction_id=prediction_id,
        pdf_size_bytes=len(pdf_bytes),
        user_id=str(user.id),
    )

    # 5. StreamingResponse ile dondur
    filename = f"degerleme-raporu-{prediction_id[:8]}.pdf"

    return StreamingResponse(
        content=iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
