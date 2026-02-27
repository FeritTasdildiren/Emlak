"""
Normalizer fonksiyonlarinin unit testleri.

Mock Pydantic response -> Dict donusum dogrulamasi.
Gercek DB baglantisi GEREKMEZ -- saf fonksiyon testleri.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.modules.data_pipeline.normalizers.area_normalizer import (
    normalize_area_analysis,
    safe_decimal,
)
from src.modules.data_pipeline.normalizers.deprem_normalizer import (
    build_point_wkt,
    calculate_risk_score,
    normalize_deprem_risk,
)
from src.modules.data_pipeline.normalizers.price_history_normalizer import (
    normalize_price_history,
)
from src.modules.data_pipeline.schemas.api_responses import (
    DemographicsData,
    EarthquakeHazardData,
    FaultData,
    HousingPriceIndexData,
    HousingSaleData,
    PopulationData,
)

# ================================================================
# Fixtures — Mock Pydantic Modeller
# ================================================================


@pytest.fixture
def population_data() -> PopulationData:
    """Ornek PopulationData (Kadikoy)."""
    return PopulationData(
        city="Istanbul",
        district="Kadikoy",
        year=2024,
        total_population=484957,
        male_population=235000,
        female_population=249957,
        household_count=198000,
        population_density=16832.0,
    )


@pytest.fixture
def demographics_data() -> DemographicsData:
    """Ornek DemographicsData (Kadikoy)."""
    return DemographicsData(
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


@pytest.fixture
def hpi_data() -> HousingPriceIndexData:
    """Ornek TCMB HPI verisi."""
    return HousingPriceIndexData(
        date=date(2024, 12, 1),
        index_value=245.7,
        series_code="TP.HKFE01",
        city="Istanbul",
        annual_change_pct=62.3,
    )


@pytest.fixture
def housing_sales_6m() -> list[HousingSaleData]:
    """Son 6 aylik konut satis verisi."""
    months = [7, 8, 9, 10, 11, 12]
    sales = [1200, 1100, 1050, 1300, 1400, 1500]
    return [
        HousingSaleData(
            city="Istanbul",
            district="Kadikoy",
            year=2024,
            month=m,
            total_sales=s,
            first_hand_sales=s // 3,
            second_hand_sales=s - s // 3,
        )
        for m, s in zip(months, sales, strict=True)
    ]


@pytest.fixture
def hazard_data() -> EarthquakeHazardData:
    """Ornek EarthquakeHazardData (Kadikoy, PGA=0.25g)."""
    return EarthquakeHazardData(
        latitude=40.9927,
        longitude=29.0231,
        pga_475=0.25,
        pga_2475=0.45,
        ss=0.75,
        s1=0.22,
        soil_class="ZC",
        earthquake_zone=1,
        data_source="tucbs_wms",
    )


@pytest.fixture
def fault_data_list() -> list[FaultData]:
    """Ornek FaultData listesi."""
    return [
        FaultData(
            name="Kuzey Anadolu Fayi",
            distance_km=15.3,
            fault_type="dogrultu atimli",
            length_km=1200.0,
            max_magnitude=7.6,
        ),
        FaultData(
            name="Adalar Segment",
            distance_km=8.7,
            fault_type="normal",
            length_km=45.0,
            max_magnitude=6.8,
        ),
        FaultData(
            name="Cinarcik Fayi",
            distance_km=22.1,
            fault_type="normal",
            length_km=60.0,
            max_magnitude=7.0,
        ),
    ]


# ================================================================
# TestAreaNormalizer
# ================================================================


class TestAreaNormalizer:
    """TUIK+TCMB -> AreaAnalysis normalize testleri."""

    def test_normalize_full_data(
        self,
        population_data: PopulationData,
        demographics_data: DemographicsData,
        hpi_data: HousingPriceIndexData,
        housing_sales_6m: list[HousingSaleData],
    ):
        """Tum alanlar dolu -> dict tum key'leri icerir."""
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=population_data,
            demographics_data=demographics_data,
            housing_sales=housing_sales_6m,
            hpi_data=hpi_data,
        )

        assert result["city"] == "Istanbul"
        assert result["district"] == "Kadikoy"
        assert result["neighborhood"] is None
        assert result["population"] == 484957
        assert isinstance(result["demographics"], dict)
        assert result["demographics"]["year"] == 2024
        assert isinstance(result["avg_price_sqm_sale"], Decimal)
        assert result["avg_price_sqm_sale"] == Decimal(str(245.7))
        assert "price_trend_6m" in result

    def test_normalize_partial_data(
        self,
        population_data: PopulationData,
    ):
        """Bazi alanlar None -> NULL olarak donusur."""
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=population_data,
            demographics_data=None,
            housing_sales=None,
            hpi_data=None,
        )

        assert result["population"] == 484957
        assert result["demographics"] == {}
        assert result["avg_price_sqm_sale"] == Decimal("0.00")
        assert "price_trend_6m" not in result

    def test_normalize_missing_population(self):
        """PopulationData None -> population=0 default."""
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=None,
            demographics_data=None,
            housing_sales=None,
            hpi_data=None,
        )

        assert result["population"] == 0

    def test_demographics_jsonb_structure(
        self,
        demographics_data: DemographicsData,
    ):
        """DemographicsData -> JSONB dict format dogrulamasi."""
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=None,
            demographics_data=demographics_data,
            housing_sales=None,
            hpi_data=None,
        )

        demo = result["demographics"]
        assert demo["year"] == 2024
        assert demo["age_0_14_pct"] == 14.2
        assert demo["age_15_24_pct"] == 12.5
        assert demo["age_25_44_pct"] == 33.8
        assert demo["age_45_64_pct"] == 25.1
        assert demo["age_65_plus_pct"] == 14.4
        assert demo["university_graduate_pct"] == 42.5
        assert demo["high_school_graduate_pct"] == 28.3
        assert demo["median_income"] == 38500.0

    def test_demographics_without_median_income(self):
        """median_income None -> demographics dict'te key yok."""
        demo = DemographicsData(
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
            median_income=None,
        )
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=None,
            demographics_data=demo,
            housing_sales=None,
            hpi_data=None,
        )

        assert "median_income" not in result["demographics"]

    def test_neighborhood_included(self, population_data: PopulationData):
        """neighborhood parametresi result'a aktarilir."""
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=population_data,
            demographics_data=None,
            housing_sales=None,
            hpi_data=None,
            neighborhood="Caferaga",
        )

        assert result["neighborhood"] == "Caferaga"

    def test_price_trend_requires_6_months(self):
        """6'dan az satis verisi -> price_trend_6m yok."""
        sales_3m = [
            HousingSaleData(
                city="Istanbul",
                district="Kadikoy",
                year=2024,
                month=m,
                total_sales=1000,
            )
            for m in [10, 11, 12]
        ]
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=None,
            demographics_data=None,
            housing_sales=sales_3m,
            hpi_data=None,
        )

        assert "price_trend_6m" not in result

    def test_price_trend_calculation(self, housing_sales_6m: list[HousingSaleData]):
        """6 aylik veri -> price_trend_6m hesaplanir."""
        result = normalize_area_analysis(
            city="Istanbul",
            district="Kadikoy",
            population_data=None,
            demographics_data=None,
            housing_sales=housing_sales_6m,
            hpi_data=None,
        )

        assert "price_trend_6m" in result
        trend = result["price_trend_6m"]
        assert isinstance(trend, Decimal)
        # Son 3 ay (1300+1400+1500=4200), onceki 3 ay (1200+1100+1050=3350)
        # (4200-3350)/3350 * 100 = 25.37%
        assert trend == Decimal("25.37")


# ================================================================
# TestSafeDecimal
# ================================================================


class TestSafeDecimal:
    """safe_decimal() fonksiyon testleri."""

    def test_float_precision(self):
        """float -> str -> Decimal precision korumasi."""
        result = safe_decimal(0.1)
        assert result == Decimal("0.1")
        assert str(result) == "0.1"

    def test_int_conversion(self):
        """int -> Decimal."""
        result = safe_decimal(42)
        assert result == Decimal("42")

    def test_string_conversion(self):
        """str -> Decimal."""
        result = safe_decimal("123.45")
        assert result == Decimal("123.45")

    def test_none_returns_default(self):
        """None -> Decimal(default)."""
        result = safe_decimal(None)
        assert result == Decimal("0.00")

    def test_none_custom_default(self):
        """None with custom default."""
        result = safe_decimal(None, "99.99")
        assert result == Decimal("99.99")

    def test_invalid_string(self):
        """Gecersiz string -> Decimal(default)."""
        result = safe_decimal("not_a_number")
        assert result == Decimal("0.00")

    def test_empty_string(self):
        """Bos string -> Decimal(default)."""
        result = safe_decimal("")
        assert result == Decimal("0.00")

    def test_negative_value(self):
        """Negatif deger korunur."""
        result = safe_decimal(-15.5)
        assert result == Decimal("-15.5")


# ================================================================
# TestDepremNormalizer
# ================================================================


class TestDepremNormalizer:
    """AFAD -> DepremRisk normalize testleri."""

    def test_normalize_full_hazard(
        self,
        hazard_data: EarthquakeHazardData,
        fault_data_list: list[FaultData],
    ):
        """EarthquakeHazardData + FaultData -> tam dict."""
        result = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=hazard_data,
            fault_data=fault_data_list,
            latitude=40.9927,
            longitude=29.0231,
        )

        assert result["city"] == "Istanbul"
        assert result["district"] == "Kadikoy"
        assert result["neighborhood"] is None
        assert result["pga_value"] == Decimal("0.25")
        assert isinstance(result["risk_score"], Decimal)
        assert result["soil_class"] == "ZC"
        assert "location_wkt" in result
        assert "fault_distance_km" in result
        # En yakin fay 8.7 km (Adalar Segment)
        assert result["fault_distance_km"] == Decimal("8.7")

    def test_normalize_no_hazard(self):
        """hazard_data None -> default degerler."""
        result = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=None,
            latitude=40.9927,
            longitude=29.0231,
        )

        assert result["pga_value"] == Decimal("0.00")
        assert result["risk_score"] == Decimal("0.00")
        assert result["soil_class"] is None
        # Koordinat parametre olarak verildi -> location_wkt olusur
        assert "location_wkt" in result

    def test_normalize_no_faults(self, hazard_data: EarthquakeHazardData):
        """fault_data None -> fault_distance_km yok."""
        result = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=hazard_data,
        )

        assert "fault_distance_km" not in result

    def test_normalize_empty_faults(self, hazard_data: EarthquakeHazardData):
        """Bos fault listesi -> fault_distance_km yok."""
        result = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=hazard_data,
            fault_data=[],
        )

        assert "fault_distance_km" not in result

    def test_coordinates_from_hazard(self, hazard_data: EarthquakeHazardData):
        """Koordinatlar hazard_data'dan alinir (parametre fallback)."""
        result = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=hazard_data,
        )

        assert result["latitude"] == 40.9927
        assert result["longitude"] == 29.0231
        assert "POINT(29.0231 40.9927)" in result["location_wkt"]

    def test_no_coordinates(self):
        """Koordinat yok, hazard_data yok -> location_wkt yok."""
        result = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=None,
        )

        assert "location_wkt" not in result
        assert "latitude" not in result
        assert "longitude" not in result


# ================================================================
# TestCalculateRiskScore
# ================================================================


class TestCalculateRiskScore:
    """calculate_risk_score() PGA -> risk score donusum testleri."""

    def test_zero_pga(self):
        """PGA 0.0 -> risk 0."""
        assert calculate_risk_score(Decimal("0.0")) == Decimal("0.00")

    def test_negative_pga(self):
        """Negatif PGA -> risk 0."""
        assert calculate_risk_score(Decimal("-0.1")) == Decimal("0.00")

    def test_low_risk(self):
        """PGA 0.05 -> risk 10.00 (cok dusuk bant)."""
        result = calculate_risk_score(Decimal("0.05"))
        assert result == Decimal("10.00")

    def test_low_medium_boundary(self):
        """PGA 0.1 -> risk 20.00 (bant siniri)."""
        result = calculate_risk_score(Decimal("0.1"))
        assert result == Decimal("20.00")

    def test_medium_risk(self):
        """PGA 0.25 -> risk 50.00 (orta bant orta noktasi)."""
        result = calculate_risk_score(Decimal("0.25"))
        assert result == Decimal("50.00")

    def test_high_risk(self):
        """PGA 0.35 -> risk 70.00 (yuksek bant)."""
        result = calculate_risk_score(Decimal("0.35"))
        assert result == Decimal("70.00")

    def test_very_high_risk(self):
        """PGA 0.45 -> risk 90.00 (cok yuksek bant)."""
        result = calculate_risk_score(Decimal("0.45"))
        assert result == Decimal("90.00")

    def test_extreme_pga_capped(self):
        """PGA 1.0 -> risk 100 (cap)."""
        result = calculate_risk_score(Decimal("1.0"))
        assert result == Decimal("100.00")

    def test_pga_0_5_cap(self):
        """PGA 0.5 -> risk 100.00."""
        result = calculate_risk_score(Decimal("0.5"))
        assert result == Decimal("100.00")

    def test_pga_0_4_boundary(self):
        """PGA 0.4 -> risk 80.00 (bant siniri)."""
        result = calculate_risk_score(Decimal("0.4"))
        assert result == Decimal("80.00")


# ================================================================
# TestBuildPointWkt
# ================================================================


class TestBuildPointWkt:
    """build_point_wkt() PostGIS WKT olusturma testleri."""

    def test_standard_point(self):
        """lon=29.0231, lat=40.9927 -> 'SRID=4326;POINT(29.0231 40.9927)'."""
        result = build_point_wkt(latitude=40.9927, longitude=29.0231)
        assert result == "SRID=4326;POINT(29.0231 40.9927)"

    def test_zero_coordinates(self):
        """Sifir koordinatlar."""
        result = build_point_wkt(latitude=0.0, longitude=0.0)
        assert result == "SRID=4326;POINT(0.0 0.0)"

    def test_negative_coordinates(self):
        """Negatif koordinatlar (bati/guney yarikure)."""
        result = build_point_wkt(latitude=-33.8688, longitude=151.2093)
        assert result == "SRID=4326;POINT(151.2093 -33.8688)"

    def test_wkt_format_lon_lat_order(self):
        """WKT formatinda longitude (X) latitude (Y) sirasidir."""
        result = build_point_wkt(latitude=41.0, longitude=29.0)
        # POINT(X Y) = POINT(lon lat)
        assert "POINT(29.0 41.0)" in result


# ================================================================
# TestNearestFaultDistance
# ================================================================


class TestNearestFaultDistance:
    """En yakin fay mesafesi secimi testi."""

    def test_nearest_selected(self, fault_data_list: list[FaultData]):
        """En yakin fay mesafesi dogru secilir."""
        result = normalize_deprem_risk(
            city="Istanbul",
            district="Kadikoy",
            hazard_data=None,
            fault_data=fault_data_list,
            latitude=40.9927,
            longitude=29.0231,
        )

        # Adalar Segment 8.7 km -> en yakin
        assert result["fault_distance_km"] == Decimal("8.7")

    def test_single_fault(self):
        """Tek fay hatti."""
        faults = [
            FaultData(name="Test Fayi", distance_km=25.0, fault_type="normal"),
        ]
        result = normalize_deprem_risk(
            city="Ankara",
            district="Cankaya",
            hazard_data=None,
            fault_data=faults,
            latitude=39.9334,
            longitude=32.8597,
        )

        assert result["fault_distance_km"] == Decimal("25.0")


# ================================================================
# TestPriceHistoryNormalizer
# ================================================================


class TestPriceHistoryNormalizer:
    """TUIK HousingSaleData -> PriceHistory normalize testleri."""

    def test_normalize_monthly_records(self, housing_sales_6m: list[HousingSaleData]):
        """6 aylik satis verisi -> 6 PriceHistory dict."""
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=housing_sales_6m,
        )

        assert len(records) == 6
        for rec in records:
            assert rec["city"] == "Istanbul"
            assert rec["district"] == "Kadikoy"
            assert rec["area_type"] == "district"
            assert rec["area_name"] == "Kadikoy"
            assert rec["source"] == "TUIK"
            assert isinstance(rec["date"], date)

    def test_normalize_with_hpi(self, housing_sales_6m: list[HousingSaleData]):
        """HPI endeksi ile m2 fiyat tahmini."""
        hpi_list = [
            HousingPriceIndexData(
                date=date(2024, 12, 1),
                index_value=245.7,
                series_code="TP.HKFE01",
                city="Istanbul",
            ),
        ]
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=housing_sales_6m,
            hpi_data=hpi_list,
        )

        # Aralik 2024 icin HPI match bulunur
        dec_record = next(r for r in records if r["date"].month == 12)
        assert "avg_price_sqm" in dec_record
        assert isinstance(dec_record["avg_price_sqm"], Decimal)
        # base_price (30000) * 245.7 / 100 = 73710.00
        assert dec_record["avg_price_sqm"] == Decimal("73710.00")

    def test_normalize_empty_sales(self):
        """Bos satis listesi -> bos liste."""
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=[],
        )

        assert records == []

    def test_normalize_neighborhood_area_type(self):
        """neighborhood verilirse area_type='neighborhood'."""
        sales = [
            HousingSaleData(
                city="Istanbul",
                district="Kadikoy",
                year=2024,
                month=12,
                total_sales=100,
            ),
        ]
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=sales,
            neighborhood="Caferaga",
        )

        assert len(records) == 1
        assert records[0]["area_type"] == "neighborhood"
        assert records[0]["area_name"] == "Caferaga"

    def test_provenance_version_format(self, housing_sales_6m: list[HousingSaleData]):
        """provenance_version formati: TUIK-YYYY-MM."""
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=housing_sales_6m,
        )

        for rec in records:
            assert rec["provenance_version"].startswith("TUIK-2024-")

    def test_transaction_count_mapped(self, housing_sales_6m: list[HousingSaleData]):
        """total_sales -> transaction_count mapping."""
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=housing_sales_6m,
        )

        # Aralik 2024 -> 1500 satis
        dec_record = next(r for r in records if r["date"].month == 12)
        assert dec_record["transaction_count"] == 1500

    def test_month_zero_skipped(self):
        """month=0 (yillik toplam) atlanir."""
        sales = [
            HousingSaleData(
                city="Istanbul",
                district="Kadikoy",
                year=2024,
                month=0,
                total_sales=15000,
            ),
            HousingSaleData(
                city="Istanbul",
                district="Kadikoy",
                year=2024,
                month=12,
                total_sales=1500,
            ),
        ]
        records = normalize_price_history(
            city="Istanbul",
            district="Kadikoy",
            sales_data=sales,
        )

        # month=0 atlanir, sadece month=12 kalir
        assert len(records) == 1
        assert records[0]["date"].month == 12


# ================================================================
# TestProvenanceBuilder
# ================================================================


class TestProvenanceBuilder:
    """build_provenance_fields() testleri."""

    def test_build_with_sources(self):
        """Kaynak bilgileri ile provenance alanlari olusturulur."""
        from src.modules.data_pipeline.normalizers.provenance_builder import (
            build_provenance_fields,
        )

        result = build_provenance_fields(
            sources=[
                ("TUIK", "2024-Q4", 42),
                ("TCMB_EVDS", "2024-12-30", 5),
            ],
        )

        assert len(result["data_sources"]) == 2
        assert result["data_sources"][0]["source"] == "TUIK"
        assert result["data_sources"][0]["record_count"] == 42
        assert result["data_sources"][1]["source"] == "TCMB_EVDS"
        assert result["provenance_version"] == "2024-Q4"
        assert result["refresh_status"] == "fresh"
        assert result["last_refreshed_at"] is not None
        assert result["refresh_error"] is None

    def test_build_empty_sources(self):
        """Bos kaynak listesi."""
        from src.modules.data_pipeline.normalizers.provenance_builder import (
            build_provenance_fields,
        )

        result = build_provenance_fields(sources=[])

        assert result["data_sources"] == []
        assert result["refresh_status"] == "fresh"
        # Bos kaynak -> haftalik timestamp versiyonu
        assert "-W" in result["provenance_version"]

    def test_build_custom_status(self):
        """Ozel refresh_status."""
        from src.modules.data_pipeline.normalizers.provenance_builder import (
            build_provenance_fields,
        )

        result = build_provenance_fields(
            sources=[("AFAD", "2024", 1)],
            status="stale",
        )

        assert result["refresh_status"] == "stale"

    def test_build_with_extra_kwargs(self):
        """extra_source_kwargs ile ek meta veriler."""
        from src.modules.data_pipeline.normalizers.provenance_builder import (
            build_provenance_fields,
        )

        result = build_provenance_fields(
            sources=[("AFAD", "2024", 1)],
            extra_source_kwargs={
                "AFAD": {"data_source": "tucbs_wms", "pga_475": "0.32"},
            },
        )

        entry = result["data_sources"][0]
        assert entry["data_source"] == "tucbs_wms"
        assert entry["pga_475"] == "0.32"
