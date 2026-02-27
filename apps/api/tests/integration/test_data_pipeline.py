"""
Data pipeline repository integration testleri.

Gercek PostgreSQL (test database) ile UPSERT dogrulamasi.
PostGIS GEOGRAPHY, ON CONFLICT, JSONB islemleri test edilir.
SQLite mock KULLANILAMAZ.

Sync session kullanilir — Celery task uyumu.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from src.modules.data_pipeline.repositories.area_repository import (
    upsert_area_analysis,
)
from src.modules.data_pipeline.repositories.deprem_repository import (
    upsert_deprem_risk,
)
from src.modules.data_pipeline.repositories.price_history_repository import (
    batch_insert_price_history,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ================================================================
# Helpers
# ================================================================


def _area_data(
    city: str = "Istanbul",
    district: str = "Kadikoy",
    neighborhood: str | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """AreaAnalysis UPSERT icin minimum gecerli veri dict'i olusturur."""
    data: dict[str, Any] = {
        "city": city,
        "district": district,
        "neighborhood": neighborhood,
        "population": 484957,
        "avg_price_sqm_sale": Decimal("52300.00"),
        "demographics": {"year": 2024, "age_0_14_pct": 14.2},
        "data_sources": [
            {
                "source": "TUIK",
                "version": "2024-Q4",
                "fetched_at": datetime.now(UTC).isoformat(),
                "record_count": 42,
            }
        ],
        "provenance_version": "2024-Q4",
        "refresh_status": "fresh",
        "last_refreshed_at": datetime.now(UTC),
    }
    data.update(overrides)
    return data


def _deprem_data(
    city: str = "Istanbul",
    district: str = "Kadikoy",
    neighborhood: str | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """DepremRisk UPSERT icin minimum gecerli veri dict'i olusturur."""
    data: dict[str, Any] = {
        "city": city,
        "district": district,
        "neighborhood": neighborhood,
        "location_wkt": "SRID=4326;POINT(29.0231 40.9927)",
        "latitude": 40.9927,
        "longitude": 29.0231,
        "pga_value": Decimal("0.25"),
        "risk_score": Decimal("50.00"),
        "soil_class": "ZC",
        "data_sources": [
            {
                "source": "AFAD",
                "version": "2024",
                "fetched_at": datetime.now(UTC).isoformat(),
                "record_count": 1,
            }
        ],
        "provenance_version": "TBDY-2018",
        "refresh_status": "fresh",
        "last_refreshed_at": datetime.now(UTC),
    }
    data.update(overrides)
    return data


def _price_record(
    year: int = 2024,
    month: int = 12,
    transaction_count: int = 1500,
    **overrides: Any,
) -> dict[str, Any]:
    """PriceHistory INSERT icin minimum gecerli veri dict'i olusturur."""
    data: dict[str, Any] = {
        "area_type": "district",
        "area_name": "Kadikoy",
        "city": "Istanbul",
        "district": "Kadikoy",
        "date": date(year, month, 1),
        "transaction_count": transaction_count,
        "source": "TUIK",
        "provenance_version": f"TUIK-{year}-{month:02d}",
    }
    data.update(overrides)
    return data


def _get_area(session: Session, city: str, district: str) -> Any:
    """DB'den area_analyses kaydini oku."""
    result = session.execute(
        text(
            "SELECT id, city, district, neighborhood, population, "
            "       avg_price_sqm_sale, demographics, data_sources, "
            "       provenance_version, refresh_status, last_refreshed_at "
            "FROM area_analyses "
            "WHERE city = :city AND district = :district "
            "  AND neighborhood IS NULL"
        ),
        {"city": city, "district": district},
    )
    return result.fetchone()


def _get_deprem(session: Session, city: str, district: str) -> Any:
    """DB'den deprem_risks kaydini oku."""
    result = session.execute(
        text(
            "SELECT id, city, district, neighborhood, risk_score, pga_value, "
            "       soil_class, fault_distance_km, "
            "       ST_AsText(location::geometry) as location_text, "
            "       data_sources, provenance_version, refresh_status "
            "FROM deprem_risks "
            "WHERE city = :city AND district = :district "
            "  AND neighborhood IS NULL"
        ),
        {"city": city, "district": district},
    )
    return result.fetchone()


def _count_price_history(session: Session, city: str) -> int:
    """DB'den price_histories kayit sayisini dondur."""
    result = session.execute(
        text("SELECT COUNT(*) FROM price_histories WHERE city = :city"),
        {"city": city},
    )
    return result.scalar()


# ================================================================
# TestAreaRepository
# ================================================================


class TestAreaRepository:
    """AreaAnalysis UPSERT testleri."""

    def test_insert_new_area(self, sync_session: Session):
        """Yeni kayit INSERT edilir."""
        data = _area_data()
        operation, area_id = upsert_area_analysis(sync_session, data)
        sync_session.flush()

        assert operation == "inserted"
        assert area_id is not None

        row = _get_area(sync_session, "Istanbul", "Kadikoy")
        assert row is not None
        assert row.city == "Istanbul"
        assert row.district == "Kadikoy"
        assert row.population == 484957

    def test_update_existing_area(self, sync_session: Session):
        """Mevcut kayit UPDATE edilir (ON CONFLICT)."""
        data = _area_data()
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        # Guncelle
        data["population"] = 500000
        data["avg_price_sqm_sale"] = Decimal("55000.00")
        operation, _area_id = upsert_area_analysis(sync_session, data)
        sync_session.flush()

        assert operation == "updated"
        row = _get_area(sync_session, "Istanbul", "Kadikoy")
        assert row.population == 500000

    def test_upsert_idempotent(self, sync_session: Session):
        """Ayni veri 2 kez UPSERT -> tek kayit, son degerler."""
        data = _area_data()
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        result = sync_session.execute(
            text(
                "SELECT COUNT(*) FROM area_analyses "
                "WHERE city = 'Istanbul' AND district = 'Kadikoy' "
                "  AND neighborhood IS NULL"
            )
        )
        count = result.scalar()
        assert count == 1

    def test_null_neighborhood(self, sync_session: Session):
        """neighborhood=NULL -> UNIQUE constraint calisir."""
        data_no_nh = _area_data(neighborhood=None)
        upsert_area_analysis(sync_session, data_no_nh)
        sync_session.flush()

        # Ayni city+district, farkli neighborhood
        data_with_nh = _area_data(neighborhood="Caferaga")
        upsert_area_analysis(sync_session, data_with_nh)
        sync_session.flush()

        result = sync_session.execute(
            text(
                "SELECT COUNT(*) FROM area_analyses "
                "WHERE city = 'Istanbul' AND district = 'Kadikoy'"
            )
        )
        count = result.scalar()
        assert count == 2  # NULL ve "Caferaga" farkli kayitlar

    def test_provenance_updated(self, sync_session: Session):
        """UPSERT sonrasi data_sources ve last_refreshed_at guncellenir."""
        data = _area_data(provenance_version="2024-Q3")
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        # Yeni provenance ile guncelle
        data["provenance_version"] = "2024-Q4"
        data["data_sources"] = [
            {
                "source": "TUIK",
                "version": "2024-Q4",
                "fetched_at": datetime.now(UTC).isoformat(),
                "record_count": 55,
            }
        ]
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        row = _get_area(sync_session, "Istanbul", "Kadikoy")
        assert row.provenance_version == "2024-Q4"
        sources = json.loads(row.data_sources) if isinstance(row.data_sources, str) else row.data_sources
        assert sources[0]["record_count"] == 55

    def test_demographics_jsonb(self, sync_session: Session):
        """demographics JSONB alani dogru yazilir."""
        demo = {
            "year": 2024,
            "age_0_14_pct": 14.2,
            "university_graduate_pct": 42.5,
        }
        data = _area_data(demographics=demo)
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        row = _get_area(sync_session, "Istanbul", "Kadikoy")
        demographics = json.loads(row.demographics) if isinstance(row.demographics, str) else row.demographics
        assert demographics["year"] == 2024
        assert demographics["university_graduate_pct"] == 42.5

    def test_empty_demographics_preserved(self, sync_session: Session):
        """Bos demographics -> mevcut deger korunur (CASE WHEN)."""
        data = _area_data(demographics={"year": 2024, "age_0_14_pct": 14.2})
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        # Bos demographics ile guncelle -> mevcut korunmali
        data["demographics"] = {}
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        row = _get_area(sync_session, "Istanbul", "Kadikoy")
        demographics = json.loads(row.demographics) if isinstance(row.demographics, str) else row.demographics
        assert demographics.get("year") == 2024

    def test_price_trend_null_preserved(self, sync_session: Session):
        """price_trend_6m COALESCE: NULL guncelleme -> mevcut deger korunur."""
        data = _area_data(price_trend_6m=Decimal("12.50"))
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        # price_trend_6m olmadan guncelle
        data.pop("price_trend_6m", None)
        upsert_area_analysis(sync_session, data)
        sync_session.flush()

        result = sync_session.execute(
            text(
                "SELECT price_trend_6m FROM area_analyses "
                "WHERE city = 'Istanbul' AND district = 'Kadikoy' "
                "  AND neighborhood IS NULL"
            )
        )
        trend = result.scalar()
        assert trend is not None
        assert Decimal(str(trend)) == Decimal("12.50")


# ================================================================
# TestDepremRepository
# ================================================================


class TestDepremRepository:
    """DepremRisk UPSERT testleri."""

    def test_insert_new_risk(self, sync_session: Session):
        """Yeni deprem riski INSERT edilir."""
        data = _deprem_data()
        operation, risk_id = upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        assert operation == "inserted"
        assert risk_id is not None

        row = _get_deprem(sync_session, "Istanbul", "Kadikoy")
        assert row is not None
        assert row.city == "Istanbul"
        assert Decimal(str(row.risk_score)) == Decimal("50.00")
        assert Decimal(str(row.pga_value)) == Decimal("0.2500")

    def test_update_existing_risk(self, sync_session: Session):
        """Mevcut kayit guncellenir."""
        data = _deprem_data()
        upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        data["risk_score"] = Decimal("75.00")
        data["pga_value"] = Decimal("0.38")
        operation, _ = upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        assert operation == "updated"
        row = _get_deprem(sync_session, "Istanbul", "Kadikoy")
        assert Decimal(str(row.risk_score)) == Decimal("75.00")

    def test_postgis_point_stored(self, sync_session: Session):
        """GEOGRAPHY POINT dogru yazilir."""
        data = _deprem_data(
            location_wkt="SRID=4326;POINT(29.0231 40.9927)",
        )
        upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        row = _get_deprem(sync_session, "Istanbul", "Kadikoy")
        # ST_AsText(location::geometry) -> POINT(29.0231 40.9927)
        assert row.location_text is not None
        assert "29.0231" in row.location_text
        assert "40.9927" in row.location_text

    def test_upsert_idempotent(self, sync_session: Session):
        """Ayni veri 2 kez -> tek kayit."""
        data = _deprem_data()
        upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        result = sync_session.execute(
            text(
                "SELECT COUNT(*) FROM deprem_risks "
                "WHERE city = 'Istanbul' AND district = 'Kadikoy' "
                "  AND neighborhood IS NULL"
            )
        )
        assert result.scalar() == 1

    def test_fault_distance_nullable(self, sync_session: Session):
        """fault_distance_km opsiyonel — NULL olabilir."""
        data = _deprem_data()
        data.pop("fault_distance_km", None)  # Yoksa zaten None
        upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        row = _get_deprem(sync_session, "Istanbul", "Kadikoy")
        assert row.fault_distance_km is None

    def test_fault_distance_coalesce(self, sync_session: Session):
        """fault_distance_km COALESCE: NULL guncelleme mevcut degeri korur."""
        data = _deprem_data(fault_distance_km=Decimal("12.30"))
        upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        # fault_distance_km olmadan guncelle -> COALESCE mevcut degeri korur
        data.pop("fault_distance_km", None)
        upsert_deprem_risk(sync_session, data)
        sync_session.flush()

        row = _get_deprem(sync_session, "Istanbul", "Kadikoy")
        assert row.fault_distance_km is not None
        assert Decimal(str(row.fault_distance_km)) == Decimal("12.30")

    def test_different_neighborhoods(self, sync_session: Session):
        """Farkli neighborhood -> farkli kayitlar."""
        data1 = _deprem_data(neighborhood=None)
        data2 = _deprem_data(neighborhood="Caferaga")
        upsert_deprem_risk(sync_session, data1)
        upsert_deprem_risk(sync_session, data2)
        sync_session.flush()

        result = sync_session.execute(
            text(
                "SELECT COUNT(*) FROM deprem_risks "
                "WHERE city = 'Istanbul' AND district = 'Kadikoy'"
            )
        )
        assert result.scalar() == 2


# ================================================================
# TestPriceHistoryRepository
# ================================================================


class TestPriceHistoryRepository:
    """PriceHistory batch INSERT testleri."""

    def test_batch_insert(self, sync_session: Session):
        """Birden fazla kayit tek seferde INSERT."""
        records = [
            _price_record(month=10, transaction_count=1300),
            _price_record(month=11, transaction_count=1400),
            _price_record(month=12, transaction_count=1500),
        ]
        count = batch_insert_price_history(sync_session, records)
        sync_session.flush()

        assert count == 3
        assert _count_price_history(sync_session, "Istanbul") == 3

    def test_batch_upsert_conflict(self, sync_session: Session):
        """Ayni tarih -> ON CONFLICT UPDATE."""
        records = [_price_record(month=12, transaction_count=1500)]
        batch_insert_price_history(sync_session, records)
        sync_session.flush()

        # Ayni tarih, farkli transaction_count
        updated_records = [_price_record(month=12, transaction_count=1600)]
        count = batch_insert_price_history(sync_session, updated_records)
        sync_session.flush()

        assert count == 1
        # Tek kayit olmali
        assert _count_price_history(sync_session, "Istanbul") == 1

        # Guncellenmis deger
        result = sync_session.execute(
            text(
                "SELECT transaction_count FROM price_histories "
                "WHERE city = 'Istanbul' AND date = '2024-12-01' AND source = 'TUIK'"
            )
        )
        assert result.scalar() == 1600

    def test_empty_records(self, sync_session: Session):
        """Bos liste -> 0 kayit."""
        count = batch_insert_price_history(sync_session, [])
        assert count == 0

    def test_avg_price_sqm_stored(self, sync_session: Session):
        """avg_price_sqm deger dogru yazilir."""
        records = [
            _price_record(avg_price_sqm=Decimal("52300.00")),
        ]
        batch_insert_price_history(sync_session, records)
        sync_session.flush()

        result = sync_session.execute(
            text(
                "SELECT avg_price_sqm FROM price_histories "
                "WHERE city = 'Istanbul' AND date = '2024-12-01'"
            )
        )
        val = result.scalar()
        assert val is not None
        assert Decimal(str(val)) == Decimal("52300.00")

    def test_provenance_version_stored(self, sync_session: Session):
        """provenance_version dogru yazilir."""
        records = [_price_record()]
        batch_insert_price_history(sync_session, records)
        sync_session.flush()

        result = sync_session.execute(
            text(
                "SELECT provenance_version FROM price_histories "
                "WHERE city = 'Istanbul' AND date = '2024-12-01'"
            )
        )
        assert result.scalar() == "TUIK-2024-12"

    def test_different_sources_not_conflict(self, sync_session: Session):
        """Farkli source -> farkli kayitlar (UNIQUE constraint source icerir)."""
        rec_tuik = _price_record(source="TUIK")
        rec_scraping = _price_record(source="scraping")
        batch_insert_price_history(sync_session, [rec_tuik])
        batch_insert_price_history(sync_session, [rec_scraping])
        sync_session.flush()

        assert _count_price_history(sync_session, "Istanbul") == 2
