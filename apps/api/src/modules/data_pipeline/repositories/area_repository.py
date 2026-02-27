"""
Emlak Teknoloji Platformu - AreaAnalysis UPSERT Repository

Sync session ile calisir (Celery uyumlu).
INSERT ON CONFLICT (city, district, neighborhood) DO UPDATE ile idempotent yazim.

Kullanim:
    from src.core.sync_database import get_sync_session
    from src.modules.data_pipeline.repositories import upsert_area_analysis

    with get_sync_session() as session:
        action, area_id = upsert_area_analysis(session, data)
        session.commit()
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from sqlalchemy import text

from src.core.provenance import REFRESH_STATUS_FAILED

logger = structlog.get_logger("data_pipeline.repositories.area")


def upsert_area_analysis(
    session: Any,
    data: dict[str, Any],
) -> tuple[str, str | None]:
    """
    INSERT ON CONFLICT (city, district, neighborhood) DO UPDATE.

    Args:
        session: Sync SQLAlchemy Session
        data: normalize_area_analysis() + build_provenance_fields() ciktisi.
            Zorunlu anahtarlar: city, district
            Opsiyonel: neighborhood, population, demographics, avg_price_sqm_sale,
                        price_trend_6m, data_sources, provenance_version,
                        refresh_status, last_refreshed_at, refresh_error

    Returns:
        (operation, area_id) -- operation: "inserted" | "updated"
        area_id: UUID string veya None (RETURNING desteklenmiyorsa)
    """
    # -- JSON serialization --
    data_sources = data.get("data_sources", [])
    if isinstance(data_sources, list):
        data_sources_json = json.dumps(data_sources)
    else:
        data_sources_json = json.dumps([])

    demographics = data.get("demographics", {})
    if isinstance(demographics, dict):
        demographics_json = json.dumps(demographics)
    else:
        demographics_json = json.dumps({})

    upsert_sql = text("""
        INSERT INTO area_analyses (
            city, district, neighborhood,
            population,
            avg_price_sqm_sale,
            price_trend_6m,
            demographics,
            data_sources,
            provenance_version,
            refresh_status,
            last_refreshed_at,
            refresh_error,
            created_at,
            updated_at
        ) VALUES (
            :city, :district, :neighborhood,
            :population,
            :avg_price_sqm_sale,
            :price_trend_6m,
            :demographics::jsonb,
            :data_sources::jsonb,
            :provenance_version,
            :refresh_status,
            :last_refreshed_at,
            NULL,
            now(),
            now()
        )
        ON CONFLICT ON CONSTRAINT uq_area_city_district_neighborhood
        DO UPDATE SET
            population = EXCLUDED.population,
            avg_price_sqm_sale = EXCLUDED.avg_price_sqm_sale,
            price_trend_6m = COALESCE(EXCLUDED.price_trend_6m, area_analyses.price_trend_6m),
            demographics = CASE
                WHEN EXCLUDED.demographics = '{}'::jsonb
                THEN area_analyses.demographics
                ELSE EXCLUDED.demographics
            END,
            data_sources = EXCLUDED.data_sources,
            provenance_version = EXCLUDED.provenance_version,
            refresh_status = EXCLUDED.refresh_status,
            last_refreshed_at = EXCLUDED.last_refreshed_at,
            refresh_error = NULL,
            updated_at = now()
        RETURNING (xmax = 0) AS inserted, id::text
    """)

    result = session.execute(
        upsert_sql,
        {
            "city": data["city"],
            "district": data["district"],
            "neighborhood": data.get("neighborhood"),
            "population": data.get("population", 0),
            "avg_price_sqm_sale": str(data.get("avg_price_sqm_sale", "0.00")),
            "price_trend_6m": (
                str(data["price_trend_6m"]) if data.get("price_trend_6m") is not None else None
            ),
            "demographics": demographics_json,
            "data_sources": data_sources_json,
            "provenance_version": data.get("provenance_version"),
            "refresh_status": data.get("refresh_status", "fresh"),
            "last_refreshed_at": data.get("last_refreshed_at"),
        },
    )

    row = result.fetchone()
    if row:
        operation = "inserted" if row[0] else "updated"
        area_id = row[1] if len(row) > 1 else None
    else:
        operation = "unknown"
        area_id = None

    logger.info(
        "area_analysis_upserted",
        city=data["city"],
        district=data["district"],
        operation=operation,
    )

    return operation, area_id


def mark_area_failed(
    session: Any,
    city: str,
    district: str,
    error_msg: str,
    neighborhood: str | None = None,
) -> None:
    """
    Mevcut area kaydinin refresh_status'unu failed olarak isaretle.

    Args:
        session: Sync SQLAlchemy Session
        city: Il adi
        district: Ilce adi
        error_msg: Hata mesaji (500 karaktere truncate edilir)
        neighborhood: Mahalle adi (opsiyonel)
    """
    if neighborhood is None:
        fail_sql = text("""
            UPDATE area_analyses
            SET refresh_status = :status,
                refresh_error = :error,
                updated_at = now()
            WHERE city = :city
              AND district = :district
              AND neighborhood IS NULL
        """)
    else:
        fail_sql = text("""
            UPDATE area_analyses
            SET refresh_status = :status,
                refresh_error = :error,
                updated_at = now()
            WHERE city = :city
              AND district = :district
              AND neighborhood = :neighborhood
        """)

    params: dict[str, Any] = {
        "status": REFRESH_STATUS_FAILED,
        "error": error_msg[:500],
        "city": city,
        "district": district,
    }
    if neighborhood is not None:
        params["neighborhood"] = neighborhood

    session.execute(fail_sql, params)
