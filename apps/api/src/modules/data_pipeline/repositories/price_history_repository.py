"""
Emlak Teknoloji Platformu - PriceHistory Batch Insert Repository

Sync session ile calisir (Celery uyumlu).
ON CONFLICT (area_type, area_name, city, date, source) DO UPDATE ile idempotent yazim.

Kullanim:
    from src.core.sync_database import get_sync_session
    from src.modules.data_pipeline.repositories import batch_insert_price_history

    with get_sync_session() as session:
        count = batch_insert_price_history(session, records)
        session.commit()
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text

logger = structlog.get_logger("data_pipeline.repositories.price_history")


def batch_insert_price_history(
    session: Any,
    records: list[dict[str, Any]],
) -> int:
    """
    Batch INSERT PriceHistory kayitlari.
    ON CONFLICT (area_type, area_name, city, date, source) DO UPDATE.

    Args:
        session: Sync SQLAlchemy Session
        records: normalize_price_history() ciktisi.
            Her dict zorunlu anahtarlar: area_type, area_name, city, date, source
            Opsiyonel: district, avg_price_sqm, median_price, listing_count,
                        transaction_count, provenance_version

    Returns:
        Eklenen/guncellenen kayit sayisi.
    """
    if not records:
        return 0

    upsert_sql = text("""
        INSERT INTO price_histories (
            area_type,
            area_name,
            city,
            district,
            date,
            avg_price_sqm,
            median_price,
            listing_count,
            transaction_count,
            source,
            provenance_version,
            created_at
        ) VALUES (
            :area_type,
            :area_name,
            :city,
            :district,
            :date,
            :avg_price_sqm,
            :median_price,
            :listing_count,
            :transaction_count,
            :source,
            :provenance_version,
            now()
        )
        ON CONFLICT ON CONSTRAINT uq_price_area_date_source
        DO UPDATE SET
            avg_price_sqm = COALESCE(EXCLUDED.avg_price_sqm, price_histories.avg_price_sqm),
            median_price = COALESCE(EXCLUDED.median_price, price_histories.median_price),
            listing_count = COALESCE(EXCLUDED.listing_count, price_histories.listing_count),
            transaction_count = COALESCE(EXCLUDED.transaction_count, price_histories.transaction_count),
            provenance_version = EXCLUDED.provenance_version
    """)

    count = 0
    for record in records:
        try:
            session.execute(
                upsert_sql,
                {
                    "area_type": record["area_type"],
                    "area_name": record["area_name"],
                    "city": record["city"],
                    "district": record.get("district"),
                    "date": record["date"],
                    "avg_price_sqm": (
                        str(record["avg_price_sqm"]) if record.get("avg_price_sqm") is not None else None
                    ),
                    "median_price": (
                        str(record["median_price"]) if record.get("median_price") is not None else None
                    ),
                    "listing_count": record.get("listing_count"),
                    "transaction_count": record.get("transaction_count"),
                    "source": record["source"],
                    "provenance_version": record.get("provenance_version"),
                },
            )
            count += 1
        except Exception as exc:
            logger.warning(
                "price_history_insert_failed",
                city=record.get("city"),
                date=str(record.get("date")),
                error=str(exc),
            )

    logger.info(
        "price_history_batch_done",
        total=len(records),
        upserted=count,
    )

    return count
