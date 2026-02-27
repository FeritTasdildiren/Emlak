"""
Emlak Teknoloji Platformu - Comparable Service

PostGIS mesafe + benzer ozellik sorgulari ile emsal mulk bulan servis.

Algoritma:
    1. Temel filtreler (ilce, tip, m2, oda, yas)
    2. PostGIS mesafe filtresi (opsiyonel, lat/lon varsa)
    3. Benzerlik skoru hesaplama (0-100)
    4. Skorla siralama, limit kadar donme

Adaptive Radius (v2):
    Konum mevcut ise min_comparables saglanamazsa yaricap genisletilir:
    1km → 3km → 5km → ilce bazli (mesafe filtresi kaldirilir)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from geoalchemy2 import WKTElement
from sqlalchemy import Integer as SAInteger
from sqlalchemy import and_, case, func, literal, select
from sqlalchemy import cast as sa_cast

from src.models.area_analysis import AreaAnalysis
from src.models.property import Property

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Adaptive radius adimlari (km).
# Son adim None = ilce bazli (mesafe filtresi yok).
_ADAPTIVE_RADII: list[float | None] = [1.0, 3.0, 5.0, None]


class ComparableService:
    """Emsal mulk bulma servisi."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public: Temel emsal arama (mevcut endpoint — geriye uyumlu)
    # ------------------------------------------------------------------
    async def find_comparables(
        self,
        district: str,
        property_type: str,
        net_sqm: float,
        room_count: int,
        building_age: int,
        lat: float | None = None,
        lon: float | None = None,
        limit: int = 5,
        max_distance_km: float = 3.0,
    ) -> list[dict]:
        """
        Benzer mulk bulma algoritmasi (geriye uyumlu).

        Filtreler:
            - Ayni ilce, ayni mulk tipi
            - m2: net_sqm * 0.7 ~ net_sqm * 1.3
            - Oda sayisi: room_count +/- 1
            - Bina yasi: building_age +/- 10
            - Mesafe: max_distance_km icinde (konum varsa)

        Benzerlik skoru (0-100):
            sqm_similarity    * 0.3
            age_similarity    * 0.2
            room_similarity   * 0.2
            distance_similarity * 0.3 (konum varsa; yoksa agirliklar yeniden dagitilir)
        """
        rows = await self._execute_comparable_query(
            district=district,
            property_type=property_type,
            net_sqm=net_sqm,
            room_count=room_count,
            building_age=building_age,
            lat=lat,
            lon=lon,
            limit=limit,
            max_distance_km=max_distance_km,
        )

        return [
            {
                "property_id": str(row.property_id),
                "district": row.district,
                "net_sqm": float(row.net_sqm),
                "price": int(row.price),
                "building_age": int(row.building_age),
                "room_count": int(row.room_count),
                "distance_km": (
                    round(float(row.distance_km), 2)
                    if row.distance_km is not None
                    else None
                ),
                "similarity_score": round(float(row.similarity_score), 1),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Public: Zenginlestirilmis emsal arama (valuation endpoint icin)
    # ------------------------------------------------------------------
    async def find_comparables_enriched(
        self,
        district: str,
        property_type: str,
        net_sqm: float,
        room_count: int,
        building_age: int,
        estimated_price: int,
        lat: float | None = None,
        lon: float | None = None,
        limit: int = 5,
        min_comparables: int = 3,
    ) -> list[dict]:
        """
        Adaptive radius ile zenginlestirilmis emsal arama.

        Farklar (find_comparables'a gore):
            - min_comparables: En az bu kadar emsal zorunlu; yetersizse yaricap genisler.
            - estimated_price: Her emsal icin price_diff_percent hesaplanir.
            - address ve rooms alanlari eklenir.

        Adaptive radius mantigi:
            Konum varsa 1km → 3km → 5km → ilce bazli (mesafe filtresi yok).
            Her adimda min_comparables saglanip saglanmadigi kontrol edilir.
            Konum yoksa tek adimda ilce bazli sorgu yapilir.
        """
        has_location = lat is not None and lon is not None
        rows: list = []

        if has_location:
            for radius in _ADAPTIVE_RADII:
                rows = await self._execute_enriched_query(
                    district=district,
                    property_type=property_type,
                    net_sqm=net_sqm,
                    room_count=room_count,
                    building_age=building_age,
                    lat=lat,
                    lon=lon,
                    limit=limit,
                    max_distance_km=radius,
                )

                if len(rows) >= min_comparables:
                    logger.info(
                        "comparables_enriched_found",
                        radius_km=radius,
                        found=len(rows),
                        min_required=min_comparables,
                    )
                    break

                logger.info(
                    "comparables_enriched_expanding",
                    current_radius_km=radius,
                    found=len(rows),
                    min_required=min_comparables,
                )
        else:
            # Konum yok → ilce bazli tek sorgu
            rows = await self._execute_enriched_query(
                district=district,
                property_type=property_type,
                net_sqm=net_sqm,
                room_count=room_count,
                building_age=building_age,
                lat=None,
                lon=None,
                limit=limit,
                max_distance_km=None,
            )

        return self._format_enriched_results(rows, estimated_price)

    # ------------------------------------------------------------------
    # Public: Ilce istatistikleri
    # ------------------------------------------------------------------
    async def get_area_stats(self, district: str) -> dict | None:
        """
        Ilce istatistiklerini AreaAnalysis tablosundan dondurur.

        Returns:
            Ilce bilgileri dict veya None (kayit yoksa).
        """
        stmt = select(AreaAnalysis).where(
            func.lower(AreaAnalysis.district) == district.lower(),
            AreaAnalysis.neighborhood.is_(None),
        )

        result = await self.session.execute(stmt)
        area = result.scalar_one_or_none()

        if area is None:
            return None

        return {
            "district": area.district,
            "city": area.city,
            "avg_price_sqm_sale": float(area.avg_price_sqm_sale) if area.avg_price_sqm_sale else None,
            "avg_price_sqm_rent": float(area.avg_price_sqm_rent) if area.avg_price_sqm_rent else None,
            "price_trend_6m": float(area.price_trend_6m) if area.price_trend_6m else None,
            "population": area.population,
            "listing_count": area.listing_count,
            "transport_score": float(area.transport_score) if area.transport_score else None,
            "amenity_score": float(area.amenity_score) if area.amenity_score else None,
            "investment_score": float(area.investment_score) if area.investment_score else None,
        }

    # ==================================================================
    # Private helpers
    # ==================================================================

    def _build_base_filters(
        self,
        district: str,
        property_type: str,
        net_sqm: float,
        room_count: int,
        building_age: int,
    ) -> tuple[list, ...]:
        """Temel filtre ve benzerlik bilesenleri olusturur."""
        sqm_min = net_sqm * 0.7
        sqm_max = net_sqm * 1.3
        age_min = max(0, building_age - 10)
        age_max = building_age + 10
        room_min = max(1, room_count - 1)
        room_max = room_count + 1

        # rooms alani "3+1" formatinda string — ilk parcayi int'e ceviriyoruz
        room_int = sa_cast(func.split_part(Property.rooms, "+", 1), SAInteger)

        filters = [
            func.lower(Property.district) == district.lower(),
            func.lower(Property.property_type) == property_type.lower(),
            Property.status == "active",
            Property.net_area.isnot(None),
            Property.net_area >= sqm_min,
            Property.net_area <= sqm_max,
            Property.building_age.isnot(None),
            Property.building_age >= age_min,
            Property.building_age <= age_max,
            Property.rooms.isnot(None),
            room_int >= room_min,
            room_int <= room_max,
        ]

        sqm_similarity = 1.0 - func.abs(Property.net_area - net_sqm) / net_sqm
        age_denominator = float(max(building_age, 1))
        age_similarity = 1.0 - func.abs(Property.building_age - building_age) / age_denominator
        room_similarity = case(
            (room_int == room_count, 1.0),
            else_=0.8,
        )

        return filters, sqm_similarity, age_similarity, room_similarity, room_int

    def _build_location_expressions(
        self,
        lat: float | None,
        lon: float | None,
        max_distance_km: float | None,
        sqm_similarity,
        age_similarity,
        room_similarity,
        filters: list,
    ):
        """Konum bazli ifadeler ve toplam benzerlik skoru olusturur."""
        has_location = lat is not None and lon is not None

        if has_location and max_distance_km is not None:
            ref_point = WKTElement(f"POINT({lon} {lat})", srid=4326)
            distance_meters = func.ST_Distance(Property.location, ref_point)
            distance_km_expr = distance_meters / 1000.0

            filters.append(distance_meters < max_distance_km * 1000)

            distance_similarity = 1.0 - (distance_km_expr / max_distance_km)

            total_similarity = (
                sqm_similarity * 0.3
                + age_similarity * 0.2
                + room_similarity * 0.2
                + distance_similarity * 0.3
            ) * 100.0
        elif has_location:
            # Konum var ama mesafe filtresi yok (ilce bazli fallback)
            ref_point = WKTElement(f"POINT({lon} {lat})", srid=4326)
            distance_meters = func.ST_Distance(Property.location, ref_point)
            distance_km_expr = distance_meters / 1000.0

            # Mesafe filtresi yok — agirliklar konum olmayan gibi dagitilir
            total_similarity = (
                sqm_similarity * 0.43
                + age_similarity * 0.28
                + room_similarity * 0.29
            ) * 100.0
        else:
            distance_km_expr = literal(None)

            total_similarity = (
                sqm_similarity * 0.43
                + age_similarity * 0.28
                + room_similarity * 0.29
            ) * 100.0

        return filters, distance_km_expr, total_similarity

    async def _execute_comparable_query(
        self,
        district: str,
        property_type: str,
        net_sqm: float,
        room_count: int,
        building_age: int,
        lat: float | None,
        lon: float | None,
        limit: int,
        max_distance_km: float,
    ) -> list:
        """Temel emsal sorgusu (geriye uyumlu — find_comparables icin)."""
        (
            filters,
            sqm_similarity,
            age_similarity,
            room_similarity,
            room_int,
        ) = self._build_base_filters(district, property_type, net_sqm, room_count, building_age)

        filters, distance_km_expr, total_similarity = self._build_location_expressions(
            lat, lon, max_distance_km, sqm_similarity, age_similarity, room_similarity, filters
        )

        similarity_label = total_similarity.label("similarity_score")
        distance_label = distance_km_expr.label("distance_km")

        stmt = (
            select(
                Property.id.label("property_id"),
                Property.district,
                Property.net_area.label("net_sqm"),
                Property.price,
                Property.building_age,
                room_int.label("room_count"),
                distance_label,
                similarity_label,
            )
            .where(and_(*filters))
            .order_by(similarity_label.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.all()

    async def _execute_enriched_query(
        self,
        district: str,
        property_type: str,
        net_sqm: float,
        room_count: int,
        building_age: int,
        lat: float | None,
        lon: float | None,
        limit: int,
        max_distance_km: float | None,
    ) -> list:
        """
        Zenginlestirilmis emsal sorgusu.

        Ek alanlar: address, rooms (string).
        max_distance_km=None ise mesafe filtresi uygulanmaz (ilce bazli fallback).
        """
        (
            filters,
            sqm_similarity,
            age_similarity,
            room_similarity,
            room_int,
        ) = self._build_base_filters(district, property_type, net_sqm, room_count, building_age)

        filters, distance_km_expr, total_similarity = self._build_location_expressions(
            lat, lon, max_distance_km, sqm_similarity, age_similarity, room_similarity, filters
        )

        similarity_label = total_similarity.label("similarity_score")
        distance_label = distance_km_expr.label("distance_km")

        stmt = (
            select(
                Property.id.label("property_id"),
                Property.net_area.label("net_sqm"),
                Property.price,
                Property.rooms,
                Property.address,
                room_int.label("room_count"),
                distance_label,
                similarity_label,
            )
            .where(and_(*filters))
            .order_by(similarity_label.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.all()

    @staticmethod
    def _format_enriched_results(rows: list, estimated_price: int) -> list[dict]:
        """
        Sorgu satirlarini ComparableResult-uyumlu dict listesine donusturur.

        Her emsal icin:
            - distance_km: PostGIS mesafe / 1000 (metre → km)
            - price_diff_percent: ((emsal_fiyat - tahmin) / tahmin) * 100
        """
        safe_price = max(estimated_price, 1)  # Sifira bolme korumasi

        results: list[dict] = []
        for row in rows:
            emsal_price = int(row.price)
            price_diff_pct = round(((emsal_price - safe_price) / safe_price) * 100, 2)

            results.append(
                {
                    "property_id": str(row.property_id),
                    "distance_km": (
                        round(float(row.distance_km), 2)
                        if row.distance_km is not None
                        else None
                    ),
                    "price_diff_percent": price_diff_pct,
                    "similarity_score": round(float(row.similarity_score), 1),
                    "address": row.address,
                    "price": emsal_price,
                    "sqm": float(row.net_sqm),
                    "rooms": row.rooms,
                }
            )

        return results
