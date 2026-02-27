"""
Emlak Teknoloji Platformu - Area Refresh Beat Task

Haftalik calisarak area_analyses tablosunu gunceller:
- TUIK CIP API'den nufus verileri
- TCMB EVDS API'den konut fiyat endeksi
- Provenance alanlari (ADR-0006) guncelleme

Beat Schedule:
    Her Pazartesi 03:00 (Europe/Istanbul)

Mimari:
    - Celery worker sync (psycopg2) — async loop YOK
    - Async API client'lar asyncio.run() ile cagirilir
    - Her ilce icin bagimsiz try/except — bir ilce hatasi digerlerini bloklamaz
    - UPSERT (INSERT ON CONFLICT DO UPDATE) ile idempotent guncelleme
    - Normalizasyon ve UPSERT isleri ayri modullere delege edilir:
      - normalizers.normalize_area_analysis() — API response -> dict
      - normalizers.build_provenance_fields() — ADR-0006 provenance
      - repositories.upsert_area_analysis() — DB UPSERT
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, date, datetime
from typing import Any

import structlog

from src.celery_app import celery_app
from src.config import settings
from src.core.sync_database import get_sync_session
from src.modules.data_pipeline.district_centers import get_all_districts
from src.modules.data_pipeline.normalizers import normalize_area_analysis
from src.modules.data_pipeline.normalizers.provenance_builder import build_provenance_fields
from src.modules.data_pipeline.repositories import mark_area_failed, upsert_area_analysis
from src.modules.data_pipeline.schemas.api_responses import (
    HousingPriceIndexData,
    PopulationData,
)
from src.tasks.base import BaseTask

logger = structlog.get_logger("celery.area_refresh")


# ─── Async Wrappers ──────────────────────────────────────────────────


async def _fetch_tuik_population(city: str, district: str) -> dict[str, Any]:
    """
    TUIK CIP API'den nufus verisini cek.

    Returns:
        {"population": int, "record_count": int}
    """
    from src.modules.data_pipeline.clients.tuik_client import TUIKClient

    async with TUIKClient() as client:
        pop_data = await client.get_population(city=city, district=district)
        return {
            "population": pop_data.total_population,
            "record_count": 1 if pop_data.total_population > 0 else 0,
        }


async def _fetch_tcmb_hpi(city_plate_code: int | None = None) -> dict[str, Any]:
    """
    TCMB EVDS API'den konut fiyat endeksini cek.

    Returns:
        {"index_value": float, "date": str, "record_count": int}
    """
    from src.modules.data_pipeline.clients.tcmb_client import TCMBClient

    now = datetime.now(UTC)
    start_date = f"01-01-{now.year}"
    end_date = now.strftime("%d-%m-%Y")

    async with TCMBClient(api_key=settings.TCMB_EVDS_API_KEY) as client:
        hpi_data = await client.get_housing_price_index(
            start_date=start_date,
            end_date=end_date,
            city_plate_code=city_plate_code,
        )

        if hpi_data:
            latest = hpi_data[-1]
            return {
                "index_value": latest.index_value,
                "date": str(latest.date),
                "record_count": len(hpi_data),
            }
        return {"index_value": 0.0, "date": "", "record_count": 0}


# ─── Sehir Plaka Kodu Mapping ─────────────────────────────────────────
_CITY_PLATE_CODES: dict[str, int] = {
    "İstanbul": 34,
    "Ankara": 6,
    "İzmir": 35,
    "Bursa": 16,
    "Antalya": 7,
}


# ─── Celery Task ───────────────────────────────────────────────────────


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="src.tasks.area_refresh.refresh_area_data",
    queue="default",
    max_retries=2,
    soft_time_limit=300,
    time_limit=360,
    autoretry_for=(),  # Manuel retry — her ilce bagimsiz
)
def refresh_area_data(self: BaseTask) -> dict[str, int]:
    """
    Tum kayitli ilceler icin area analysis verisini yenile.

    Beat Schedule: Her Pazartesi 03:00 (Europe/Istanbul)

    Islem akisi:
        1. Tum kayitli ilceleri al (district_centers)
        2. Her sehir icin TCMB HPI cek (sehir basina 1 API call)
        3. Her ilce icin TUIK nufus cek
        4. normalize_area_analysis() ile API verisini normalize et
        5. build_provenance_fields() ile provenance alanlarini olustur
        6. upsert_area_analysis() ile DB'ye yaz

    Returns:
        {"updated": int, "failed": int, "skipped": int}
    """
    from src.core.refresh_metrics import refresh_metrics

    refresh_metrics.refresh_started(table="area_analyses")
    _start_time = time.monotonic()

    self.log.info("area_refresh_started")

    districts = get_all_districts()
    updated = 0
    failed = 0
    skipped = 0

    # ── Sehir bazinda HPI cache (sehir basina 1 API call yeterli) ──
    hpi_cache: dict[str, dict[str, Any]] = {}

    for city, district, _lat, _lon in districts:
        try:
            # ── TCMB HPI (sehir bazinda cache) ──
            if city not in hpi_cache:
                plate_code = _CITY_PLATE_CODES.get(city)
                try:
                    hpi_result = asyncio.run(_fetch_tcmb_hpi(plate_code))
                    hpi_cache[city] = hpi_result
                except Exception as exc:
                    self.log.warning(
                        "area_refresh_hpi_failed",
                        city=city,
                        error=str(exc),
                        error_type=type(exc).__name__,
                    )
                    hpi_cache[city] = {
                        "index_value": 0.0,
                        "date": "",
                        "record_count": 0,
                    }

            hpi_data = hpi_cache[city]

            # ── TUIK Nufus ──
            try:
                pop_result = asyncio.run(_fetch_tuik_population(city, district))
            except Exception as exc:
                self.log.warning(
                    "area_refresh_population_failed",
                    city=city,
                    district=district,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                pop_result = {"population": 0, "record_count": 0}

            # ── Normalize: API response -> dict ──
            pop_model = PopulationData(
                city=city,
                district=district,
                year=datetime.now(UTC).year,
                total_population=pop_result["population"],
            )

            hpi_model = None
            if hpi_data["index_value"] > 0:
                hpi_model = HousingPriceIndexData(
                    date=date.today(),
                    index_value=hpi_data["index_value"],
                    series_code="TP.HKFE01",
                )

            area_data = normalize_area_analysis(
                city=city,
                district=district,
                population_data=pop_model,
                demographics_data=None,
                housing_sales=None,
                hpi_data=hpi_model,
            )

            # ── Provenance (ADR-0006) ──
            now_version = datetime.now(UTC).strftime("%Y-W%W")
            provenance = build_provenance_fields(
                sources=[
                    ("TUIK", now_version, pop_result["record_count"]),
                    ("TCMB_EVDS", hpi_data.get("date", ""), hpi_data["record_count"]),
                ],
            )

            # ── Merge & UPSERT ──
            data = {**area_data, **provenance}

            with get_sync_session() as session:
                action, _ = upsert_area_analysis(session, data)
                session.commit()

            if action == "inserted":
                self.log.info(
                    "area_refresh_inserted",
                    city=city,
                    district=district,
                )
            else:
                self.log.info(
                    "area_refresh_updated",
                    city=city,
                    district=district,
                )

            updated += 1

        except Exception as exc:
            failed += 1
            self.log.error(
                "area_refresh_district_failed",
                city=city,
                district=district,
                error=str(exc),
                error_type=type(exc).__name__,
            )

            # Hatali ilceyi DB'de isaretle
            try:
                with get_sync_session() as session:
                    mark_area_failed(session, city, district, str(exc))
                    session.commit()
            except Exception as mark_exc:
                self.log.error(
                    "area_refresh_mark_failed_error",
                    city=city,
                    district=district,
                    error=str(mark_exc),
                )

    result = {"updated": updated, "failed": failed, "skipped": skipped}

    _elapsed = time.monotonic() - _start_time
    _result_status = "success" if failed == 0 else "failure"
    refresh_metrics.refresh_completed(
        table="area_analyses", duration=_elapsed, result=_result_status,
    )

    self.log.info("area_refresh_completed", **result)
    return result
