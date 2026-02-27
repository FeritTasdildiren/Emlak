"""
Emlak Teknoloji Platformu - Portal Export Schemas

Pydantic v2 modeller: portal export istegi/yaniti, portal bilgisi.

Desteklenen portallar:
    - sahibinden.com (baslik maks 50, aciklama maks 2000, emoji YASAK, duz metin)
    - hepsiemlak.com (baslik maks 70, aciklama maks 4000, satir sonu \\n, ozellikler checkbox)

Referans: TASK-120 (S8.8 + S8.16)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ================================================================
# Portal Info
# ================================================================


class PortalInfo(BaseModel):
    """Tek bir portal'in format bilgisi."""

    id: str = Field(
        ...,
        description="Portal ID: sahibinden, hepsiemlak",
        examples=["sahibinden"],
    )
    name: str = Field(..., description="Portal adi")
    max_title_length: int = Field(..., description="Baslik maksimum karakter sayisi")
    max_description_length: int = Field(..., description="Aciklama maksimum karakter sayisi")
    emoji_allowed: bool = Field(..., description="Emoji kullanimi izinli mi?")
    required_fields: list[str] = Field(
        ...,
        description="Portal tarafindan zorunlu tutulan alanlar",
    )
    notes: str = Field(..., description="Portal'a ozel ek bilgi / kurallar")


class PortalListResponse(BaseModel):
    """Tum portal bilgilerinin listesi."""

    portals: list[PortalInfo]
    count: int = Field(..., description="Toplam portal sayisi")


# ================================================================
# Portal Export Request
# ================================================================


class PortalExportRequest(BaseModel):
    """Portal export istegi — ilan metni uretim ciktisini portal formatina cevirir."""

    title: str = Field(
        ...,
        min_length=1,
        description="Ilan basligi (generate-text ciktisi)",
        examples=["3+1 Daire Caferaga Kadikoy - Deniz Manzarali"],
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Ilan aciklamasi (generate-text ciktisi)",
    )
    highlights: list[str] = Field(
        default_factory=list,
        description="One cikan ozellikler listesi (opsiyonel)",
    )
    portal: Literal["sahibinden", "hepsiemlak", "both"] = Field(
        ...,
        description="Hedef portal: sahibinden, hepsiemlak veya both (her ikisi)",
    )


# ================================================================
# Portal Export Result
# ================================================================


class PortalExportResult(BaseModel):
    """Tek bir portal icin formatlanmis ilan ciktisi."""

    portal: str = Field(
        ...,
        description="Portal ID",
        examples=["sahibinden"],
    )
    formatted_title: str = Field(
        ...,
        description="Portal formatina uygun baslik",
    )
    formatted_description: str = Field(
        ...,
        description="Portal formatina uygun aciklama",
    )
    character_counts: dict[str, int] = Field(
        ...,
        description="Karakter sayilari: title_length, description_length",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Uyarilar (orn. 'Baslik kirpildi', 'Emoji kaldirildi')",
    )


class PortalExportResponse(BaseModel):
    """Portal export yaniti — bir veya birden fazla portal ciktisi icerir."""

    exports: list[PortalExportResult]
