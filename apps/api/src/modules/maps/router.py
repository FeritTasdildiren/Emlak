"""
Emlak Teknoloji Platformu - Maps Router

Harita endpoint'leri: property bounding box sorgusu ve heatmap.

Prefix: /api/v1/maps
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser).
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.sql.expression import cast

from src.core.exceptions import ValidationError
from src.dependencies import DBSession
from src.models.area_analysis import AreaAnalysis
from src.models.property import Property
from src.modules.auth.dependencies import ActiveUser
from src.modules.maps.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONFeatureProperties,
    GeoJSONPoint,
    HeatmapPoint,
    HeatmapResponse,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/maps",
    tags=["maps"],
)

_MAX_PROPERTIES = 500


@router.get(
    "/properties",
    response_model=GeoJSONFeatureCollection,
    summary="Harita property sorgusu (bounding box)",
    description=(
        "Belirtilen bounding box icindeki aktif ilanlari "
        "GeoJSON FeatureCollection formatinda dondurur."
    ),
)
async def get_map_properties(
    db: DBSession,
    user: ActiveUser,
    bbox: str = Query(
        description="Bounding box: minLon,minLat,maxLon,maxLat",
        examples=["28.5,40.8,29.5,41.2"],
    ),
    limit: int = Query(default=200, ge=1, le=_MAX_PROPERTIES),
) -> GeoJSONFeatureCollection:
    """
    Property tablosundan bounding box icindeki aktif ilanlari getirir.

    bbox formati: minLon,minLat,maxLon,maxLat (WGS84)
    Sonuclar GeoJSON FeatureCollection olarak doner.

    Raises:
        ValidationError: bbox formati hatali ise 422.
    """
    parts = bbox.split(",")
    if len(parts) != 4:
        raise ValidationError(
            detail="bbox formati hatali. Beklenen: minLon,minLat,maxLon,maxLat"
        )

    try:
        min_lon, min_lat, max_lon, max_lat = (float(p.strip()) for p in parts)
    except ValueError as err:
        raise ValidationError(
            detail="bbox degerleri sayisal olmali."
        ) from err

    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValidationError(
            detail="bbox degerleri gecersiz: min degerler max degerlerden kucuk olmali."
        )

    # ST_MakeEnvelope(minLon, minLat, maxLon, maxLat, SRID)
    envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    bbox_geog = cast(envelope, Property.location.type)

    stmt = (
        select(
            Property.id,
            Property.title,
            Property.price,
            Property.listing_type,
            Property.property_type,
            Property.rooms,
            Property.net_area,
            Property.district,
            func.ST_Y(func.ST_GeomFromWKB(Property.location.cast(None))).label("lat"),
            func.ST_X(func.ST_GeomFromWKB(Property.location.cast(None))).label("lon"),
        )
        .where(
            Property.status == "active",
            func.ST_Intersects(Property.location, bbox_geog),
        )
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    features: list[GeoJSONFeature] = []
    for row in rows:
        features.append(
            GeoJSONFeature(
                geometry=GeoJSONPoint(coordinates=[row.lon, row.lat]),
                properties=GeoJSONFeatureProperties(
                    id=str(row.id),
                    title=row.title,
                    price=float(row.price),
                    listing_type=row.listing_type,
                    property_type=row.property_type,
                    rooms=row.rooms,
                    net_area=float(row.net_area) if row.net_area else None,
                    district=row.district,
                ),
            )
        )

    logger.info(
        "map_properties_fetched",
        bbox=bbox,
        count=len(features),
        user_id=str(user.id),
    )

    return GeoJSONFeatureCollection(
        features=features,
        metadata={
            "total": len(features),
            "limit": limit,
            "bbox": [min_lon, min_lat, max_lon, max_lat],
        },
    )


@router.get(
    "/heatmap",
    response_model=HeatmapResponse,
    summary="Ilce bazli fiyat heatmap",
    description=(
        "Ilce bazinda ortalama m2 satis fiyatini normalize ederek "
        "heatmap veri noktalari olarak dondurur."
    ),
)
async def get_heatmap(
    db: DBSession,
    user: ActiveUser,
    city: str = Query(default="Istanbul", description="Sehir adi"),
) -> HeatmapResponse:
    """
    AreaAnalysis tablosundan ilce bazli avg_price_sqm_sale verisi cekilir.
    Boundary polygon'un centroid'i kullanilarak [lat, lon, intensity] noktasi uretilir.
    Intensity, min-max normalizasyon ile 0-1 arasina olceklenir.

    Boundary olmayan ilceler icin sabit konum (0,0) kullanilir (filtrelenir).
    """
    stmt = (
        select(
            AreaAnalysis.district,
            AreaAnalysis.avg_price_sqm_sale,
            func.ST_Y(
                func.ST_Centroid(
                    func.ST_GeomFromWKB(AreaAnalysis.boundary.cast(None))
                )
            ).label("lat"),
            func.ST_X(
                func.ST_Centroid(
                    func.ST_GeomFromWKB(AreaAnalysis.boundary.cast(None))
                )
            ).label("lon"),
        )
        .where(
            func.lower(AreaAnalysis.city) == city.lower(),
            AreaAnalysis.neighborhood.is_(None),
            AreaAnalysis.avg_price_sqm_sale.is_not(None),
            AreaAnalysis.boundary.is_not(None),
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return HeatmapResponse(points=[], min_value=None, max_value=None)

    prices = [float(r.avg_price_sqm_sale) for r in rows]
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price

    points: list[HeatmapPoint] = []
    for row in rows:
        price = float(row.avg_price_sqm_sale)
        intensity = (price - min_price) / price_range if price_range > 0 else 0.5
        points.append(
            HeatmapPoint(
                lat=row.lat,
                lon=row.lon,
                intensity=round(intensity, 4),
            )
        )

    logger.info(
        "heatmap_fetched",
        city=city,
        point_count=len(points),
        user_id=str(user.id),
    )

    return HeatmapResponse(
        points=points,
        min_value=round(min_price, 2),
        max_value=round(max_price, 2),
    )
