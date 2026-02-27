"""
Emlak Teknoloji Platformu - Deprem Risk Refresh Beat Task

Aylik calisarak deprem_risks tablosunu gunceller:
- AFAD TUCBS WMS / ArcGIS / TDTH API'den PGA degerleri
- PGA -> risk_score donusumu (0-100 skalasi)
- PostGIS GEOGRAPHY(POINT) ile konum kaydi
- Provenance alanlari (ADR-0006) guncelleme

Beat Schedule:
    Her ayin 1'i 04:00 (Europe/Istanbul)

Mimari:
    - Celery worker sync (psycopg2) — async loop YOK
    - Async AFAD client asyncio.run() ile cagirilir
    - Her ilce icin bagimsiz try/except — bir ilce hatasi digerlerini bloklamaz
    - Normalizasyon ve UPSERT isleri ayri modullere delege edilir:
      - normalizers.normalize_deprem_risk() — API response -> dict
      - normalizers.build_provenance_fields() — ADR-0006 provenance
      - repositories.upsert_deprem_risk() — DB UPSERT

PGA -> Risk Skoru Donusum Tablosu:
    PGA (g)     Risk Skoru
    0.0 - 0.1   0  - 20   (Cok dusuk)
    0.1 - 0.2   20 - 40   (Dusuk)
    0.2 - 0.3   40 - 60   (Orta)
    0.3 - 0.4   60 - 80   (Yuksek)
    0.4+        80 - 100  (Cok yuksek)
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from src.celery_app import celery_app
from src.core.sync_database import get_sync_session
from src.modules.data_pipeline.district_centers import get_all_districts
from src.modules.data_pipeline.normalizers import normalize_deprem_risk
from src.modules.data_pipeline.normalizers.area_normalizer import safe_decimal
from src.modules.data_pipeline.normalizers.provenance_builder import build_provenance_fields
from src.modules.data_pipeline.repositories import mark_deprem_failed, upsert_deprem_risk
from src.tasks.base import BaseTask

if TYPE_CHECKING:
    from src.modules.data_pipeline.schemas.api_responses import EarthquakeHazardData

logger = structlog.get_logger("celery.deprem_risk_refresh")


# ─── Async Wrapper ─────────────────────────────────────────────────────


async def _fetch_earthquake_hazard(
    latitude: float,
    longitude: float,
) -> EarthquakeHazardData:
    """
    AFAD API'den deprem tehlike parametrelerini cek.

    Returns:
        EarthquakeHazardData Pydantic modeli
    """
    from src.modules.data_pipeline.clients.afad_client import AFADClient

    async with AFADClient() as client:
        return await client.get_earthquake_hazard(latitude, longitude)


# ─── Celery Task ───────────────────────────────────────────────────────


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="src.tasks.deprem_risk_refresh.refresh_deprem_risk",
    queue="default",
    max_retries=2,
    soft_time_limit=300,
    time_limit=360,
    autoretry_for=(),  # Manuel retry — her ilce bagimsiz
)
def refresh_deprem_risk(self: BaseTask) -> dict[str, int]:
    """
    Tum kayitli ilceler icin deprem risk verisini yenile.

    Beat Schedule: Her ayin 1'i 04:00 (Europe/Istanbul)

    Islem akisi:
        1. Tum kayitli ilceleri al (district_centers)
        2. Her ilce icin AFAD API'den EarthquakeHazardData cek
        3. normalize_deprem_risk() ile PGA -> risk_score, WKT, vs. normalize et
        4. build_provenance_fields() ile provenance alanlarini olustur
        5. upsert_deprem_risk() ile DB'ye yaz

    Returns:
        {"updated": int, "failed": int, "skipped": int}
    """
    from src.core.refresh_metrics import refresh_metrics

    refresh_metrics.refresh_started(table="deprem_risks")
    _start_time = time.monotonic()

    self.log.info("deprem_risk_refresh_started")

    districts = get_all_districts()
    updated = 0
    failed = 0
    skipped = 0

    for city, district, lat, lon in districts:
        try:
            # ── AFAD API'den deprem tehlike verisi ──
            try:
                hazard_data = asyncio.run(
                    _fetch_earthquake_hazard(lat, lon)
                )
            except Exception as exc:
                self.log.warning(
                    "deprem_risk_afad_failed",
                    city=city,
                    district=district,
                    latitude=lat,
                    longitude=lon,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                # AFAD basarisiz -> skip (sonraki periyotta tekrar denenir)
                failed += 1

                try:
                    with get_sync_session() as session:
                        mark_deprem_failed(session, city, district, str(exc))
                        session.commit()
                except Exception:
                    pass  # Mark failed hatasi sessizce atlanir

                continue

            # ── Normalize: API response -> dict ──
            risk_data = normalize_deprem_risk(
                city=city,
                district=district,
                hazard_data=hazard_data,
                latitude=lat,
                longitude=lon,
            )

            # ── Provenance (ADR-0006) ──
            pga_decimal = safe_decimal(hazard_data.pga_475)
            pga_2475_str = str(safe_decimal(hazard_data.pga_2475))

            provenance = build_provenance_fields(
                sources=[
                    ("AFAD", datetime.now(UTC).strftime("TBDY-2018-%Y%m"), 1),
                ],
                extra_source_kwargs={
                    "AFAD": {
                        "data_source": hazard_data.data_source or "unknown",
                        "pga_475": str(pga_decimal),
                        "pga_2475": pga_2475_str,
                    },
                },
            )

            # ── Merge & UPSERT ──
            data = {**risk_data, **provenance}

            with get_sync_session() as session:
                action, _ = upsert_deprem_risk(session, data)
                session.commit()

            self.log.info(
                "deprem_risk_district_done",
                city=city,
                district=district,
                action=action,
                pga=str(risk_data.get("pga_value")),
                risk_score=str(risk_data.get("risk_score")),
                data_source=hazard_data.data_source,
            )
            updated += 1

        except Exception as exc:
            failed += 1
            self.log.error(
                "deprem_risk_district_failed",
                city=city,
                district=district,
                error=str(exc),
                error_type=type(exc).__name__,
            )

            try:
                with get_sync_session() as session:
                    mark_deprem_failed(session, city, district, str(exc))
                    session.commit()
            except Exception as mark_exc:
                self.log.error(
                    "deprem_risk_mark_failed_error",
                    city=city,
                    district=district,
                    error=str(mark_exc),
                )

    result = {"updated": updated, "failed": failed, "skipped": skipped}

    _elapsed = time.monotonic() - _start_time
    _result_status = "success" if failed == 0 else "failure"
    refresh_metrics.refresh_completed(
        table="deprem_risks", duration=_elapsed, result=_result_status,
    )

    self.log.info("deprem_risk_refresh_completed", **result)
    return result
