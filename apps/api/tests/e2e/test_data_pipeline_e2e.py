"""
Uctan uca veri pipeline testi.

Mock API Response -> Normalize -> Repository -> DB Dogrulama
Tam akis testi: Pydantic model -> normalizer -> UPSERT -> SELECT dogrulama.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import text

from src.modules.data_pipeline.normalizers.area_normalizer import (
    normalize_area_analysis,
)
from src.modules.data_pipeline.normalizers.deprem_normalizer import (
    normalize_deprem_risk,
)
from src.modules.data_pipeline.normalizers.price_history_normalizer import (
    normalize_price_history,
)
from src.modules.data_pipeline.normalizers.provenance_builder import (
    build_provenance_fields,
)
from src.modules.data_pipeline.repositories.area_repository import (
    upsert_area_analysis,
)
from src.modules.data_pipeline.repositories.deprem_repository import (
    upsert_deprem_risk,
)
from src.modules.data_pipeline.repositories.price_history_repository import (
    batch_insert_price_history,
)
from src.modules.data_pipeline.schemas.api_responses import (
    DemographicsData,
    EarthquakeHazardData,
    FaultData,
    HousingPriceIndexData,
    HousingSaleData,
    PopulationData,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ================================================================
# TestAreaPipelineE2E
# ================================================================


class TestAreaPipelineE2E:
    """TUIK+TCMB -> normalize -> upsert -> DB dogrulama."""

    def test_full_pipeline(self, sync_session: Session):
        """
        Tam akis:
        1. Mock PopulationData + DemographicsData + HousingPriceIndexData olustur
        2. normalize_area_analysis() cagir
        3. build_provenance_fields() ile provenance ekle
        4. upsert_area_analysis() cagir
        5. DB'den oku -> Tum alanlar dogru
        """
        # 1. Mock Pydantic modeller
        population = PopulationData(
            city="Istanbul",
            district="Kadikoy",
            year=2024,
            total_population=484957,
            male_population=235000,
            female_population=249957,
            household_count=198000,
            population_density=16832.0,
        )
        demographics = DemographicsData(
            city="Istanbul",
            district="Kadikoy",
            year=2024,
            age_0_14_pct=14.2,
            age_15_24_pct=12.5,
            age_25_44_pct=33.8,
            age_45_64_pct=25.1,
            age_65_plus_pct=14.4,
            university_graduate_pct=42.5,
            high_school_graduate_pct=28.3,
            median_income=38500.0,
        )
        hpi = HousingPriceIndexData(
            date=date(2024, 12, 1),
            index_value=245.7,
            series_code="TP.HKFE01",
            city="Istanbul",
        )
        sales = [
            HousingSaleData(
                city="Istanbul", district="Kadikoy",
                year=2024, month=m, total_sales=s,
            )
            for m, s in [(7, 1200), (8, 1100), (9, 1050), (10, 1300), (11, 1400), (12, 1500)]
        ]

        # 2. Normalize
        normalized = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=population,
            demographics_data=demographics,
            housing_sales=sales,
            hpi_data=hpi,
        )

        # 3. Provenance ekle
        provenance = build_provenance_fields(
            sources=[
                ("TUIK", "2024-Q4", 6),
                ("TCMB_EVDS", "2024-12", 1),
            ],
        )
        normalized.update(provenance)

        # 4. UPSERT
        operation, area_id = upsert_area_analysis(sync_session, normalized)
        sync_session.flush()

        # 5. DB dogrulama
        assert operation == "inserted"
        assert area_id is not None

        row = sync_session.execute(
            text(
                "SELECT city, district, neighborhood, population, "
                "       avg_price_sqm_sale, price_trend_6m, demographics, "
                "       data_sources, provenance_version, refresh_status "
                "FROM area_analyses "
                "WHERE city = 'Istanbul' AND district = 'Kadikoy' "
                "  AND neighborhood IS NULL"
            )
        ).fetchone()

        assert row is not None
        assert row.city == "Istanbul"
        assert row.district == "Kadikoy"
        assert row.population == 484957
        assert Decimal(str(row.avg_price_sqm_sale)) == Decimal("245.7")

        demographics_db = (
            json.loads(row.demographics)
            if isinstance(row.demographics, str)
            else row.demographics
        )
        assert demographics_db["year"] == 2024
        assert demographics_db["age_0_14_pct"] == 14.2
        assert demographics_db["median_income"] == 38500.0

        sources_db = (
            json.loads(row.data_sources)
            if isinstance(row.data_sources, str)
            else row.data_sources
        )
        assert len(sources_db) == 2
        assert sources_db[0]["source"] == "TUIK"
        assert sources_db[1]["source"] == "TCMB_EVDS"
        assert row.provenance_version == "2024-Q4"
        assert row.refresh_status == "fresh"

    def test_pipeline_partial_data(self, sync_session: Session):
        """Bazi API response'lar None -> Graceful handling."""
        # Sadece population, diger kaynaklar yok
        population = PopulationData(
            city="Ankara",
            district="Cankaya",
            year=2024,
            total_population=920000,
        )

        normalized = normalize_area_analysis(
            city="Ankara",
            district="Cankaya",
            population_data=population,
            demographics_data=None,
            housing_sales=None,
            hpi_data=None,
        )

        provenance = build_provenance_fields(
            sources=[("TUIK", "2024-Q4", 1)],
        )
        normalized.update(provenance)

        operation, _area_id = upsert_area_analysis(sync_session, normalized)
        sync_session.flush()

        assert operation == "inserted"

        row = sync_session.execute(
            text(
                "SELECT population, avg_price_sqm_sale, demographics, price_trend_6m "
                "FROM area_analyses "
                "WHERE city = 'Ankara' AND district = 'Cankaya' "
                "  AND neighborhood IS NULL"
            )
        ).fetchone()

        assert row.population == 920000
        assert Decimal(str(row.avg_price_sqm_sale)) == Decimal("0.00")
        demographics_db = (
            json.loads(row.demographics)
            if isinstance(row.demographics, str)
            else row.demographics
        )
        assert demographics_db == {}
        assert row.price_trend_6m is None

    def test_pipeline_provenance_chain(self, sync_session: Session):
        """Ilk insert -> update -> data_sources guncellenir."""
        # Ilk insert
        normalized = normalize_area_analysis(
            city="Izmir",
            district="Karsiyaka",
            population_data=PopulationData(
                city="Izmir", district="Karsiyaka", year=2024,
                total_population=350000,
            ),
            demographics_data=None,
            housing_sales=None,
            hpi_data=None,
        )
        prov1 = build_provenance_fields(sources=[("TUIK", "2024-Q3", 1)])
        normalized.update(prov1)

        upsert_area_analysis(sync_session, normalized)
        sync_session.flush()

        # Update — yeni provenance
        normalized["population"] = 355000
        prov2 = build_provenance_fields(
            sources=[("TUIK", "2024-Q4", 2), ("TCMB_EVDS", "2024-12", 1)],
        )
        normalized.update(prov2)

        upsert_area_analysis(sync_session, normalized)
        sync_session.flush()

        row = sync_session.execute(
            text(
                "SELECT population, provenance_version, data_sources "
                "FROM area_analyses "
                "WHERE city = 'Izmir' AND district = 'Karsiyaka' "
                "  AND neighborhood IS NULL"
            )
        ).fetchone()

        assert row.population == 355000
        assert row.provenance_version == "2024-Q4"
        sources = (
            json.loads(row.data_sources)
            if isinstance(row.data_sources, str)
            else row.data_sources
        )
        # Son UPSERT'in kaynaklari: 2 kaynak
        assert len(sources) == 2
        assert sources[0]["source"] == "TUIK"
        assert sources[1]["source"] == "TCMB_EVDS"


# ================================================================
# TestDepremPipelineE2E
# ================================================================


class TestDepremPipelineE2E:
    """AFAD -> normalize -> upsert -> DB dogrulama."""

    def test_full_pipeline(self, sync_session: Session):
        """Mock EarthquakeHazardData -> normalize -> upsert -> PostGIS POINT dogrula."""
        # 1. Mock Pydantic modeller
        hazard = EarthquakeHazardData(
            latitude=40.9927,
            longitude=29.0231,
            pga_475=0.25,
            pga_2475=0.45,
            ss=0.75,
            s1=0.22,
            soil_class="ZC",
            data_source="tucbs_wms",
        )
        faults = [
            FaultData(name="Kuzey Anadolu Fayi", distance_km=15.3, fault_type="dogrultu atimli"),
            FaultData(name="Adalar Segment", distance_km=8.7, fault_type="normal"),
        ]

        # 2. Normalize
        normalized = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=hazard,
            fault_data=faults,
            latitude=40.9927,
            longitude=29.0231,
        )

        # 3. Provenance ekle
        provenance = build_provenance_fields(
            sources=[("AFAD", "TBDY-2018", 1)],
            extra_source_kwargs={
                "AFAD": {"data_source": "tucbs_wms", "pga_475": "0.25"},
            },
        )
        normalized.update(provenance)

        # 4. UPSERT
        operation, risk_id = upsert_deprem_risk(sync_session, normalized)
        sync_session.flush()

        # 5. DB dogrulama
        assert operation == "inserted"
        assert risk_id is not None

        row = sync_session.execute(
            text(
                "SELECT city, district, risk_score, pga_value, soil_class, "
                "       fault_distance_km, "
                "       ST_AsText(location::geometry) as loc, "
                "       data_sources, provenance_version, refresh_status "
                "FROM deprem_risks "
                "WHERE city = 'Istanbul' AND district = 'Kadikoy' "
                "  AND neighborhood IS NULL"
            )
        ).fetchone()

        assert row is not None
        assert row.city == "Istanbul"
        assert row.district == "Kadikoy"
        assert Decimal(str(row.pga_value)) == Decimal("0.2500")
        assert Decimal(str(row.risk_score)) == Decimal("50.00")
        assert row.soil_class == "ZC"
        assert Decimal(str(row.fault_distance_km)) == Decimal("8.70")
        # PostGIS POINT dogrulama
        assert "29.0231" in row.loc
        assert "40.9927" in row.loc

        sources = (
            json.loads(row.data_sources)
            if isinstance(row.data_sources, str)
            else row.data_sources
        )
        assert sources[0]["source"] == "AFAD"
        assert sources[0]["data_source"] == "tucbs_wms"
        assert row.refresh_status == "fresh"

    def test_pipeline_no_faults(self, sync_session: Session):
        """FaultData yok -> fault_distance_km = None."""
        hazard = EarthquakeHazardData(
            latitude=39.9334,
            longitude=32.8597,
            pga_475=0.12,
            soil_class="ZB",
        )

        normalized = normalize_deprem_risk(
            city="Ankara",
            district="Cankaya",
            hazard_data=hazard,
            fault_data=None,
        )
        provenance = build_provenance_fields(sources=[("AFAD", "2024", 1)])
        normalized.update(provenance)

        upsert_deprem_risk(sync_session, normalized)
        sync_session.flush()

        row = sync_session.execute(
            text(
                "SELECT fault_distance_km, pga_value, soil_class "
                "FROM deprem_risks "
                "WHERE city = 'Ankara' AND district = 'Cankaya' "
                "  AND neighborhood IS NULL"
            )
        ).fetchone()

        assert row.fault_distance_km is None
        assert Decimal(str(row.pga_value)) == Decimal("0.1200")
        assert row.soil_class == "ZB"

    def test_pipeline_update_preserves_fault(self, sync_session: Session):
        """Fault distance mevcut -> NULL guncelleme COALESCE ile korur."""
        hazard = EarthquakeHazardData(
            latitude=40.9927,
            longitude=29.0231,
            pga_475=0.30,
            soil_class="ZC",
        )
        faults = [FaultData(name="Test Fayi", distance_km=10.5)]

        # Ilk insert — fault_distance_km=10.5
        norm1 = normalize_deprem_risk(
            city="Bursa",
            district="Osmangazi",
            hazard_data=hazard,
            fault_data=faults,
            latitude=40.1956,
            longitude=29.0601,
        )
        prov1 = build_provenance_fields(sources=[("AFAD", "2024-Q3", 1)])
        norm1.update(prov1)
        upsert_deprem_risk(sync_session, norm1)
        sync_session.flush()

        # Update — fault yok
        norm2 = normalize_deprem_risk(
            city="Bursa",
            district="Osmangazi",
            hazard_data=hazard,
            fault_data=None,
            latitude=40.1956,
            longitude=29.0601,
        )
        prov2 = build_provenance_fields(sources=[("AFAD", "2024-Q4", 1)])
        norm2.update(prov2)
        upsert_deprem_risk(sync_session, norm2)
        sync_session.flush()

        row = sync_session.execute(
            text(
                "SELECT fault_distance_km FROM deprem_risks "
                "WHERE city = 'Bursa' AND district = 'Osmangazi' "
                "  AND neighborhood IS NULL"
            )
        ).fetchone()

        # COALESCE: NULL update -> mevcut 10.5 korunur
        assert row.fault_distance_km is not None
        assert Decimal(str(row.fault_distance_km)) == Decimal("10.50")


# ================================================================
# TestPriceHistoryPipelineE2E
# ================================================================


class TestPriceHistoryPipelineE2E:
    """TUIK satis -> normalize -> batch insert -> DB dogrulama."""

    def test_full_pipeline(self, sync_session: Session):
        """6 aylik satis -> 6 PriceHistory kaydi."""
        # 1. Mock Pydantic modeller
        sales = [
            HousingSaleData(
                city="Istanbul", district="Kadikoy",
                year=2024, month=m, total_sales=s,
            )
            for m, s in [(7, 1200), (8, 1100), (9, 1050), (10, 1300), (11, 1400), (12, 1500)]
        ]
        hpi_list = [
            HousingPriceIndexData(
                date=date(2024, m, 1),
                index_value=idx,
                series_code="TP.HKFE01",
                city="Istanbul",
            )
            for m, idx in [(7, 230.0), (8, 232.5), (9, 235.0), (10, 238.0), (11, 241.0), (12, 245.7)]
        ]

        # 2. Normalize
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=sales,
            hpi_data=hpi_list,
        )

        assert len(records) == 6

        # 3. Batch insert
        count = batch_insert_price_history(sync_session, records)
        sync_session.flush()

        assert count == 6

        # 4. DB dogrulama
        result = sync_session.execute(
            text(
                "SELECT date, transaction_count, avg_price_sqm, source, provenance_version "
                "FROM price_histories "
                "WHERE city = 'Istanbul' "
                "ORDER BY date"
            )
        )
        rows = result.fetchall()
        assert len(rows) == 6

        # Ilk kayit: Temmuz 2024
        assert rows[0].date == date(2024, 7, 1)
        assert rows[0].transaction_count == 1200
        assert rows[0].source == "TUIK"
        assert rows[0].provenance_version == "TUIK-2024-07"

        # Son kayit: Aralik 2024
        assert rows[5].date == date(2024, 12, 1)
        assert rows[5].transaction_count == 1500
        # HPI 245.7 -> base_price 30000 * 245.7 / 100 = 73710.00
        assert Decimal(str(rows[5].avg_price_sqm)) == Decimal("73710.00")

    def test_pipeline_without_hpi(self, sync_session: Session):
        """HPI verisi olmadan -> avg_price_sqm NULL."""
        sales = [
            HousingSaleData(
                city="Ankara", district="Cankaya",
                year=2024, month=12, total_sales=800,
            ),
        ]

        records = normalize_price_history(
            city="Ankara",
            district="Cankaya",
            sales_data=sales,
            hpi_data=None,
        )

        batch_insert_price_history(sync_session, records)
        sync_session.flush()

        row = sync_session.execute(
            text(
                "SELECT avg_price_sqm, transaction_count "
                "FROM price_histories "
                "WHERE city = 'Ankara' AND date = '2024-12-01'"
            )
        ).fetchone()

        assert row.transaction_count == 800
        assert row.avg_price_sqm is None

    def test_pipeline_upsert_updates_values(self, sync_session: Session):
        """Ayni donem verisi tekrar gelirse guncellenir."""
        sales = [
            HousingSaleData(
                city="Izmir", district="Karsiyaka",
                year=2024, month=12, total_sales=600,
            ),
        ]

        records = normalize_price_history(
            city="Izmir",
            district="Karsiyaka",
            sales_data=sales,
        )
        batch_insert_price_history(sync_session, records)
        sync_session.flush()

        # Guncellenmis veri
        updated_sales = [
            HousingSaleData(
                city="Izmir", district="Karsiyaka",
                year=2024, month=12, total_sales=650,
            ),
        ]
        updated_records = normalize_price_history(
            city="Izmir",
            district="Karsiyaka",
            sales_data=updated_sales,
        )
        batch_insert_price_history(sync_session, updated_records)
        sync_session.flush()

        # Tek kayit, guncellenmis deger
        result = sync_session.execute(
            text(
                "SELECT COUNT(*), MAX(transaction_count) "
                "FROM price_histories "
                "WHERE city = 'Izmir' AND date = '2024-12-01'"
            )
        ).fetchone()

        assert result[0] == 1  # tek kayit
        assert result[1] == 650  # guncellenmis
