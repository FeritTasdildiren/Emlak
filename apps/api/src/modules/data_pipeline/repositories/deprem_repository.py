"""
Emlak Teknoloji Platformu - DepremRisk UPSERT Repository

Sync session ile calisir (Celery uyumlu).
INSERT ON CONFLICT (city, district, neighborhood) DO UPDATE ile idempotent yazim.
PostGIS ST_GeogFromText ile GEOGRAPHY POINT olusturma.

Kullanim:
    from src.core.sync_database import get_sync_session
    from src.modules.data_pipeline.repositories import upsert_deprem_risk

    with get_sync_session() as session:
        action, risk_id = upsert_deprem_risk(session, data)
        session.commit()
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from sqlalchemy import text

from src.core.provenance import REFRESH_STATUS_FAILED

logger = structlog.get_logger("data_pipeline.repositories.deprem")


def upsert_deprem_risk(
    session: Any,
    data: dict[str, Any],
) -> tuple[str, str | None]:
    """
    INSERT ON CONFLICT (city, district, neighborhood) DO UPDATE.

    Args:
        session: Sync SQLAlchemy Session
        data: normalize_deprem_risk() + build_provenance_fields() ciktisi.
            Zorunlu anahtarlar: city, district, location_wkt, risk_score, pga_value
            Opsiyonel: neighborhood, soil_class, fault_distance_km,
                        data_sources, provenance_version, refresh_status,
                        last_refreshed_at

    Returns:
        (operation, risk_id) -- operation: "inserted" | "updated"
    """
    # -- JSON serialization --
    data_sources = data.get("data_sources", [])
    if isinstance(data_sources, list):
        data_sources_json = json.dumps(data_sources)
    else:
        data_sources_json = json.dumps([])

    upsert_sql = text("""
        INSERT INTO deprem_risks (
            location,
            city, district, neighborhood,
            risk_score,
            pga_value,
            soil_class,
            fault_distance_km,
            data_sources,
            provenance_version,
            refresh_status,
            last_refreshed_at,
            refresh_error,
            created_at,
            updated_at
        ) VALUES (
            ST_GeogFromText(:location_wkt),
            :city, :district, :neighborhood,
            :risk_score,
            :pga_value,
            :soil_class,
            :fault_distance_km,
            :data_sources::jsonb,
            :provenance_version,
            :refresh_status,
            :last_refreshed_at,
            NULL,
            now(),
            now()
        )
        ON CONFLICT ON CONSTRAINT uq_deprem_city_district_neighborhood
        DO UPDATE SET
            location = ST_GeogFromText(:location_wkt),
            risk_score = EXCLUDED.risk_score,
            pga_value = EXCLUDED.pga_value,
            soil_class = EXCLUDED.soil_class,
            fault_distance_km = COALESCE(EXCLUDED.fault_distance_km, deprem_risks.fault_distance_km),
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
            "location_wkt": data["location_wkt"],
            "city": data["city"],
            "district": data["district"],
            "neighborhood": data.get("neighborhood"),
            "risk_score": str(data["risk_score"]),
            "pga_value": str(data["pga_value"]),
            "soil_class": data.get("soil_class"),
            "fault_distance_km": (
                str(data["fault_distance_km"]) if data.get("fault_distance_km") is not None else None
            ),
            "data_sources": data_sources_json,
            "provenance_version": data.get("provenance_version"),
            "refresh_status": data.get("refresh_status", "fresh"),
            "last_refreshed_at": data.get("last_refreshed_at"),
        },
    )

    row = result.fetchone()
    if row:
        operation = "inserted" if row[0] else "updated"
        risk_id = row[1] if len(row) > 1 else None
    else:
        operation = "unknown"
        risk_id = None

    logger.info(
        "deprem_risk_upserted",
        city=data["city"],
        district=data["district"],
        operation=operation,
        pga=str(data.get("pga_value")),
        risk_score=str(data.get("risk_score")),
    )

    return operation, risk_id


def mark_deprem_failed(
    session: Any,
    city: str,
    district: str,
    error_msg: str,
    neighborhood: str | None = None,
) -> None:
    """
    Mevcut deprem_risk kaydinin refresh_status'unu failed olarak isaretle.

    Args:
        session: Sync SQLAlchemy Session
        city: Il adi
        district: Ilce adi
        error_msg: Hata mesaji (500 karaktere truncate edilir)
        neighborhood: Mahalle adi (opsiyonel)
    """
    if neighborhood is None:
        fail_sql = text("""
            UPDATE deprem_risks
            SET refresh_status = :status,
                refresh_error = :error,
                updated_at = now()
            WHERE city = :city
              AND district = :district
              AND neighborhood IS NULL
        """)
    else:
        fail_sql = text("""
            UPDATE deprem_risks
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
