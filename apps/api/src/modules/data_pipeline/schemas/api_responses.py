"""
Emlak Teknoloji Platformu - Data Pipeline Response Schemas

Dis API client'larindan donen verilerin Pydantic v2 modelleri.
Her model, API'den gelen ham veriyi yapilandirilmis Python nesnesine donusturur.
"""

import datetime

from pydantic import BaseModel, Field

# ============================================================
# TUIK Response Schemas
# ============================================================


class HousingSaleData(BaseModel):
    """TUIK konut satis istatistikleri (il/ilce bazinda)."""

    city: str = Field(description="Il adi")
    district: str | None = Field(default=None, description="Ilce adi")
    year: int = Field(description="Yil")
    month: int = Field(ge=1, le=12, description="Ay")
    total_sales: int = Field(ge=0, description="Toplam konut satisi")
    first_hand_sales: int = Field(default=0, ge=0, description="Ilk el (sifir) konut satisi")
    second_hand_sales: int = Field(default=0, ge=0, description="Ikinci el konut satisi")
    mortgage_sales: int = Field(default=0, ge=0, description="Ipotekli satis")
    foreign_sales: int = Field(default=0, ge=0, description="Yabancilara satis")


class PopulationData(BaseModel):
    """TUIK nufus verileri (il/ilce bazinda)."""

    city: str = Field(description="Il adi")
    district: str | None = Field(default=None, description="Ilce adi")
    year: int = Field(description="Referans yili")
    total_population: int = Field(ge=0, description="Toplam nufus")
    male_population: int = Field(default=0, ge=0, description="Erkek nufus")
    female_population: int = Field(default=0, ge=0, description="Kadin nufus")
    household_count: int = Field(default=0, ge=0, description="Hane sayisi")
    population_density: float = Field(default=0.0, ge=0, description="Nufus yogunlugu (kisi/km2)")


class HousingPriceIndex(BaseModel):
    """TUIK konut fiyat endeksi."""

    year: int = Field(description="Yil")
    quarter: int = Field(ge=1, le=4, description="Ceyrek")
    index_value: float = Field(description="Endeks degeri (2017=100)")
    annual_change_pct: float | None = Field(default=None, description="Yillik degisim yuzdesi")
    quarterly_change_pct: float | None = Field(
        default=None, description="Ceyreklik degisim yuzdesi"
    )
    city: str | None = Field(default=None, description="Il (None ise Turkiye geneli)")


class DemographicsData(BaseModel):
    """TUIK demografik veriler (yas dagilimi, egitim, gelir)."""

    city: str = Field(description="Il adi")
    district: str | None = Field(default=None, description="Ilce adi")
    year: int = Field(description="Referans yili")

    # Yas dagilimi
    age_0_14_pct: float = Field(default=0.0, description="0-14 yas grubu yuzdesi")
    age_15_24_pct: float = Field(default=0.0, description="15-24 yas grubu yuzdesi")
    age_25_44_pct: float = Field(default=0.0, description="25-44 yas grubu yuzdesi")
    age_45_64_pct: float = Field(default=0.0, description="45-64 yas grubu yuzdesi")
    age_65_plus_pct: float = Field(default=0.0, description="65+ yas grubu yuzdesi")

    # Egitim seviyesi
    university_graduate_pct: float = Field(default=0.0, description="Universite mezunu yuzdesi")
    high_school_graduate_pct: float = Field(default=0.0, description="Lise mezunu yuzdesi")

    # Gelir bilgisi
    median_income: float | None = Field(default=None, description="Medyan hanehalki geliri (TRY)")


# ============================================================
# TCMB EVDS Response Schemas
# ============================================================


class HousingPriceIndexData(BaseModel):
    """TCMB konut fiyat endeksi verisi (EVDS TP.HKFE serisi)."""

    date: datetime.date = Field(description="Veri tarihi")
    index_value: float = Field(description="Endeks degeri")
    series_code: str = Field(description="EVDS seri kodu (orn: TP.HKFE01)")
    city: str | None = Field(default=None, description="Il (None ise Turkiye geneli)")
    annual_change_pct: float | None = Field(default=None, description="Yillik degisim yuzdesi")


class MortgageRateData(BaseModel):
    """TCMB konut kredisi faiz oranlari."""

    date: datetime.date = Field(description="Veri tarihi")
    rate_pct: float = Field(description="Faiz orani (%)")
    bank_type: str = Field(
        default="weighted_average",
        description="Banka tipi: weighted_average, public, private",
    )
    maturity_months: int | None = Field(default=None, description="Vade suresi (ay)")


class ExchangeRateData(BaseModel):
    """TCMB doviz kurlari."""

    date: datetime.date = Field(description="Kur tarihi")
    usd_try_buying: float = Field(description="USD/TRY alis kuru")
    usd_try_selling: float = Field(description="USD/TRY satis kuru")
    eur_try_buying: float = Field(description="EUR/TRY alis kuru")
    eur_try_selling: float = Field(description="EUR/TRY satis kuru")


# ============================================================
# AFAD TDTH Response Schemas
# ============================================================


class EarthquakeHazardData(BaseModel):
    """
    AFAD deprem tehlike parametreleri (koordinat bazli).

    Veri kaynaklari:
    - TUCBS WMS (tucbs-public-api.csb.gov.tr): SS, S1, PGA raster degerleri
    - TDTH (tdth.afad.gov.tr): Ss, S1, PGA muhendislik degerleri (e-Devlet gerekli)
    - ArcGIS katmani: Yaklasik PGA degeri (yedek)

    TBDY 2018 tekrarlanma periyotlari:
    - DD-1: 2475 yil (%2 asim olasiligi, 50 yil)
    - DD-2: 475 yil (%10 asim olasiligi, 50 yil) — STANDART TASARIM
    - DD-3: 72 yil (%50 asim olasiligi, 50 yil)
    - DD-4: 43 yil (%68 asim olasiligi, 50 yil)
    """

    latitude: float = Field(description="Enlem")
    longitude: float = Field(description="Boylam")

    # PGA — Peak Ground Acceleration
    pga_475: float = Field(
        description="PGA degeri — 475 yil tekrarlanma periyodu (DD-2, standart)"
    )
    pga_2475: float | None = Field(
        default=None,
        description="PGA degeri — 2475 yil tekrarlanma periyodu (DD-1)",
    )

    # Spectral Acceleration — DD-2 (475 yil, standart tasarim)
    ss: float | None = Field(
        default=None,
        description="Kisa periyot spektral ivme katsayisi Ss (0.2s) — DD-2",
    )
    s1: float | None = Field(
        default=None,
        description="1 saniye periyot spektral ivme katsayisi S1 — DD-2",
    )

    # Spectral Acceleration — DD-1 (2475 yil)
    ss_2475: float | None = Field(
        default=None,
        description="Kisa periyot spektral ivme katsayisi Ss — DD-1 (2475 yil)",
    )
    s1_2475: float | None = Field(
        default=None,
        description="1 saniye periyot spektral ivme katsayisi S1 — DD-1 (2475 yil)",
    )

    # Zemin sinifi
    soil_class: str | None = Field(
        default=None,
        description="Zemin sinifi (ZA, ZB, ZC, ZD, ZE)",
    )

    # Deprem bolgesi (eski sistem referansi)
    earthquake_zone: int | None = Field(
        default=None,
        description="Deprem bolgesi (1-5, eski siniflandirma referansi)",
    )

    # Ek bilgiler
    design_ground_type: str | None = Field(
        default=None,
        description="Tasarim zemin tipi (TBDY 2018)",
    )

    # Veri kaynagi (hangi strateji ile alindi)
    data_source: str | None = Field(
        default=None,
        description="Veri kaynagi: tucbs_wms, tdth, arcgis_fallback, default",
    )


class FaultData(BaseModel):
    """Aktif fay hatti bilgisi."""

    name: str = Field(description="Fay hatti adi")
    distance_km: float = Field(description="Noktaya mesafe (km)")
    fault_type: str | None = Field(
        default=None,
        description="Fay tipi (normal, ters, dogrultu atimli)",
    )
    length_km: float | None = Field(default=None, description="Fay hatti uzunlugu (km)")
    max_magnitude: float | None = Field(default=None, description="Tahmini maksimum buyukluk (Mw)")
    geometry: dict | None = Field(
        default=None, description="Fay hatti geometrisi (GeoJSON LineString)"
    )


# ============================================================
# TKGM WMS/WFS Response Schemas
# ============================================================


class ParcelData(BaseModel):
    """TKGM parsel temel bilgileri (koordinattan sorgulama)."""

    city: str = Field(description="Il adi")
    district: str = Field(description="Ilce adi")
    neighborhood: str = Field(description="Mahalle/koy adi")
    block_number: str = Field(description="Ada numarasi")
    parcel_number: str = Field(description="Parsel numarasi")
    area_m2: float | None = Field(default=None, description="Alan (m2)")
    latitude: float | None = Field(default=None, description="Merkez enlem")
    longitude: float | None = Field(default=None, description="Merkez boylam")


class ParcelDetailData(BaseModel):
    """TKGM parsel detay bilgileri."""

    city: str = Field(description="Il adi")
    district: str = Field(description="Ilce adi")
    neighborhood: str = Field(description="Mahalle/koy adi")
    block_number: str = Field(description="Ada numarasi")
    parcel_number: str = Field(description="Parsel numarasi")
    area_m2: float | None = Field(default=None, description="Alan (m2)")
    land_use_type: str | None = Field(
        default=None, description="Arazi kullanim turu (arsa, tarla, bag, bahce ...)"
    )
    zoning_status: str | None = Field(default=None, description="Imar durumu")
    ownership_type: str | None = Field(
        default=None, description="Mulkiyet tipi (sahsi, tuzel, hazine)"
    )
    geometry: dict | None = Field(
        default=None, description="Parsel sinir geometrisi (GeoJSON Polygon)"
    )
    created_at: datetime.datetime | None = Field(default=None, description="Kayit tarihi")
    updated_at: datetime.datetime | None = Field(default=None, description="Son guncelleme tarihi")
