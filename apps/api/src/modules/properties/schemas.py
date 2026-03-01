"""
Emlak Teknoloji Platformu - Properties Schemas

TASK-189: Property Form Standardizasyon.
Ilan olusturma ve guncelleme icin Pydantic sema tanimlari.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PropertyCreate(BaseModel):
    """Yeni ilan olusturma istegi."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=5, max_length=300, description="Ilan basligi")
    description: str | None = Field(default=None, max_length=5000, description="Ilan aciklamasi")
    property_type: str = Field(description="Emlak tipi: daire, villa, ofis, arsa, dukkan")
    listing_type: str = Field(description="Ilan tipi: sale, rent")
    price: float = Field(gt=0, description="Fiyat")
    currency: str = Field(default="TRY", max_length=3, description="Para birimi (ISO 4217)")

    # Ozellikler
    rooms: str | None = Field(default=None, max_length=20, description="Oda sayisi (orn: 3+1)")
    gross_area: float | None = Field(default=None, gt=0, description="Brut alan (m2)")
    net_area: float | None = Field(default=None, gt=0, description="Net alan (m2)")
    floor_number: int | None = Field(default=None, ge=0, le=100, description="Bulundugu kat")
    total_floors: int | None = Field(default=None, ge=1, le=100, description="Toplam kat sayisi")
    building_age: int | None = Field(default=None, ge=0, le=100, description="Bina yasi")
    heating_type: str | None = Field(default=None, max_length=50, description="Isitma tipi")
    bathroom_count: int | None = Field(default=None, ge=1, le=10, description="Banyo sayisi")
    furniture_status: str | None = Field(
        default=None,
        max_length=20,
        description="Esya durumu: bos, esyali, yari_esyali",
    )
    building_type: str | None = Field(
        default=None,
        max_length=20,
        description="Yapi tipi: betonarme, celik, ahsap, prefabrik, tas, tugla",
    )
    facade: str | None = Field(
        default=None,
        max_length=20,
        description="Cephe yonu: kuzey, guney, dogu, bati vb.",
    )

    # Konum
    city: str = Field(max_length=100, description="Il")
    district: str = Field(max_length=100, description="Ilce")
    neighborhood: str | None = Field(default=None, max_length=100, description="Mahalle")
    address: str | None = Field(default=None, max_length=500, description="Acik adres")
    lat: float = Field(ge=-90, le=90, description="Enlem")
    lon: float = Field(ge=-180, le=180, description="Boylam")

    # Ek veriler
    features: dict | None = Field(default=None, description="Ek ozellikler JSON")
    status: str = Field(default="active", description="Ilan durumu: active, draft")


class PropertyUpdate(BaseModel):
    """Ilan guncelleme istegi — partial update."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=5, max_length=300, description="Ilan basligi")
    description: str | None = Field(default=None, max_length=5000, description="Ilan aciklamasi")
    property_type: str | None = Field(default=None, description="Emlak tipi")
    listing_type: str | None = Field(default=None, description="Ilan tipi")
    price: float | None = Field(default=None, gt=0, description="Fiyat")
    currency: str | None = Field(default=None, max_length=3, description="Para birimi")

    rooms: str | None = Field(default=None, max_length=20, description="Oda sayisi")
    gross_area: float | None = Field(default=None, gt=0, description="Brut alan (m2)")
    net_area: float | None = Field(default=None, gt=0, description="Net alan (m2)")
    floor_number: int | None = Field(default=None, ge=0, le=100, description="Bulundugu kat")
    total_floors: int | None = Field(default=None, ge=1, le=100, description="Toplam kat sayisi")
    building_age: int | None = Field(default=None, ge=0, le=100, description="Bina yasi")
    heating_type: str | None = Field(default=None, max_length=50, description="Isitma tipi")
    bathroom_count: int | None = Field(default=None, ge=1, le=10, description="Banyo sayisi")
    furniture_status: str | None = Field(default=None, max_length=20, description="Esya durumu")
    building_type: str | None = Field(default=None, max_length=20, description="Yapi tipi")
    facade: str | None = Field(default=None, max_length=20, description="Cephe yonu")

    city: str | None = Field(default=None, max_length=100, description="Il")
    district: str | None = Field(default=None, max_length=100, description="Ilce")
    neighborhood: str | None = Field(default=None, max_length=100, description="Mahalle")
    address: str | None = Field(default=None, max_length=500, description="Acik adres")

    features: dict | None = Field(default=None, description="Ek ozellikler JSON")
    status: str | None = Field(default=None, description="Ilan durumu")
