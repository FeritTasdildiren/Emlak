"""
Emlak Teknoloji Platformu - Property Search Router

Arama endpoint'leri: FTS + trigram + filtre bazli ilan arama.

Prefix: /api/v1/properties/search
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser).
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from src.dependencies import DBSession
from src.modules.auth.dependencies import ActiveUser
from src.modules.properties.search import (
    MAX_LIMIT,
    search_properties,
    search_suggestions,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/properties/search",
    tags=["search"],
)


# ---------- Pydantic Schemas ----------


class PropertySearchItem(BaseModel):
    """Arama sonucu ilan ozeti."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Ilan UUID")
    title: str = Field(description="Ilan basligi")
    description: str | None = Field(default=None, description="Ilan aciklamasi")
    property_type: str = Field(description="Emlak tipi: daire, villa, arsa vb.")
    listing_type: str = Field(description="Ilan tipi: sale, rent")
    price: float = Field(description="Fiyat")
    currency: str = Field(description="Para birimi (ISO 4217)")
    rooms: str | None = Field(default=None, description="Oda sayisi (orn: 3+1)")
    gross_area: float | None = Field(default=None, description="Brut alan (m2)")
    net_area: float | None = Field(default=None, description="Net alan (m2)")
    floor_number: int | None = Field(default=None, description="Bulundugu kat")
    total_floors: int | None = Field(default=None, description="Toplam kat sayisi")
    building_age: int | None = Field(default=None, description="Bina yasi")
    city: str = Field(description="Il")
    district: str = Field(description="Ilce")
    neighborhood: str | None = Field(default=None, description="Mahalle")
    status: str = Field(description="Ilan durumu")
    photos: list = Field(default_factory=list, description="Fotograf URL listesi")
    created_at: datetime = Field(description="Olusturulma tarihi")


class SearchResponse(BaseModel):
    """Sayfalamali arama yaniti."""

    items: list[PropertySearchItem] = Field(description="Arama sonuclari")
    total: int = Field(description="Toplam sonuc sayisi")
    page: int = Field(description="Mevcut sayfa numarasi")
    per_page: int = Field(description="Sayfa basina sonuc sayisi")
    total_pages: int = Field(description="Toplam sayfa sayisi")
    query: str | None = Field(default=None, description="Arama terimi")


class SuggestionResponse(BaseModel):
    """Autocomplete oneri yaniti."""

    suggestions: list[str] = Field(description="Oneri listesi")


# ---------- Endpoints ----------


@router.get(
    "",
    response_model=SearchResponse,
    summary="Ilan arama",
    description=(
        "FTS + trigram + filtre bazli hibrit ilan arama. "
        "q parametresi bossa sadece filtrelerle listeleme yapilir."
    ),
)
async def search(
    db: DBSession,
    user: ActiveUser,
    q: str | None = Query(default=None, description="Arama terimi"),
    city: str | None = Query(default=None, description="Il filtresi"),
    district: str | None = Query(default=None, description="Ilce filtresi"),
    property_type: str | None = Query(
        default=None, description="Emlak tipi: konut, ticari, arsa"
    ),
    listing_type: str | None = Query(
        default=None, description="Ilan tipi: satilik, kiralik"
    ),
    status: str = Query(default="active", description="Ilan durumu: active, sold, rented, draft"),
    min_price: int | None = Query(default=None, ge=0, description="Minimum fiyat"),
    max_price: int | None = Query(default=None, ge=0, description="Maksimum fiyat"),
    min_area: float | None = Query(default=None, ge=0, description="Minimum net alan (m2)"),
    max_area: float | None = Query(default=None, ge=0, description="Maksimum net alan (m2)"),
    sort: str = Query(
        default="relevance",
        description="Siralama: relevance, price_asc, price_desc, newest, area",
    ),
    page: int = Query(default=1, ge=1, description="Sayfa numarasi"),
    per_page: int = Query(default=20, ge=1, le=MAX_LIMIT, description="Sayfa basina sonuc"),
) -> SearchResponse:
    """Hibrit ilan arama endpoint'i."""
    offset = (page - 1) * per_page

    properties, total = await search_properties(
        db,
        q,
        city=city,
        district=district,
        listing_type=listing_type,
        property_type=property_type,
        status=status,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        sort=sort,
        limit=per_page,
        offset=offset,
    )

    total_pages = math.ceil(total / per_page) if total > 0 else 0

    logger.info(
        "property_search",
        query=q,
        total=total,
        page=page,
        per_page=per_page,
        user_id=str(user.id),
    )

    return SearchResponse(
        items=[PropertySearchItem.model_validate(p) for p in properties],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        query=q,
    )


@router.get(
    "/suggestions",
    response_model=SuggestionResponse,
    summary="Arama onerileri",
    description="Autocomplete / typeahead icin ilan basligi onerileri dondurur.",
)
async def suggestions(
    db: DBSession,
    user: ActiveUser,
    q: str = Query(min_length=2, description="Arama terimi (min 2 karakter)"),
    limit: int = Query(default=5, ge=1, le=10, description="Oneri sayisi"),
) -> SuggestionResponse:
    """Autocomplete oneri endpoint'i."""
    results = await search_suggestions(db, q, limit=limit)

    logger.info(
        "search_suggestions",
        query=q,
        count=len(results),
        user_id=str(user.id),
    )

    return SuggestionResponse(suggestions=results)
