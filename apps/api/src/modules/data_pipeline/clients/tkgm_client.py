"""
Emlak Teknoloji Platformu - TKGM WMS/WFS & MEGSiS API Client

TKGM (Tapu ve Kadastro Genel Mudurlugu) verilerine erisim:
- Parsel sorgulama (koordinattan ada/parsel bilgisi)
- Ada/parsel detay bilgileri (GeoJSON Feature response)
- Parsel sinir geometrisi (GeoJSON Polygon)
- Idari yapi sorgusu (il/ilce/mahalle listeleri)

VERI KAYNAKLARI:
1. cbsapi.tkgm.gov.tr/megsiswebapi.v3/api — MEGSiS REST API v3 (birincil)
2. cbsapi.tkgm.gov.tr/megsiswebapi.v3.1 — MEGSiS REST API v3.1 (yeni versiyon)
3. cbsservis.tkgm.gov.tr/megsiswebapi.v3/api — MEGSiS alternatif host
4. cbsservis.tkgm.gov.tr/tkgm.ows/wms — OGC WMS servisi (protokol gerektir)
5. cbsservis.tkgm.gov.tr/tkgm.ows/wfs — OGC WFS servisi (protokol gerektir)
6. megsisapi.tkgm.gov.tr — MEGSiS eski API (yedek)

DOGRULANMIS API ENDPOINT'LERI:
  REST API (auth yok):
    GET /idariYapi/ilListe — Il listesi
    GET /idariYapi/ilceListe/{il_id} — Ilce listesi
    GET /idariYapi/mahalleListe/{ilce_id} — Mahalle listesi
    GET /parsel/{mahalle_id}/{ada_no}/{parsel_no} — Parsel bilgisi + GeoJSON
    GET /parsel/{latitude}/{longitude}/ — Koordinattan parsel sorgusu
    GET /parselbagligeometri/{mahalle_id}/{ada_no}/{parsel_no} — Parsel geometri

  WMS (protokol anlasmasi gerekli):
    URL: cbsservis.tkgm.gov.tr/tkgm.ows/wms
    Katmanlar: TKGM:MEGSIS, TKGM:parseller, TKGM:mahalleler, TKGM:iller

  WFS (protokol anlasmasi gerekli):
    URL: cbsservis.tkgm.gov.tr/tkgm.ows/wfs
    CQL_FILTER destegi: INTERSECTS(geom, POINT(lon lat)), tapumahallead like '...'

GEOJSON RESPONSE ALANLARI (dogrulanmis):
  - ilAd: Il adi
  - ilceAd: Ilce adi
  - mahalleAd: Mahalle adi
  - adaNo: Ada numarasi
  - parselNo: Parsel numarasi
  - pafta: Pafta referansi
  - nitelik: Nitelik (arsa, tarla, bahce ...)
  - alan: Alan (m2, virgullu format: "7,722.87")
  - mevkii: Mevkii
  - zeminKmdurum: Zemin kullanim durumu

ONEMLI NOTLAR:
- REST API authentication gerektirmiyor ancak TKGM resmi olarak "izinsiz erisim" yasaktir diyor
- WMS/WFS servisleri icin TKGM ile protokol anlasmasi gerekli (cbs@tkgm.gov.tr)
- Ticari kullanim yasaktir — sadece bilgilendirme amacli
- Rate limiting uygulanabilir — agresif sorgulamadan kacinilmali
- Koordinat sistemi: WGS84 / EPSG:4326 (ITRF96 dahili)
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from src.modules.data_pipeline.clients.base_client import BaseAPIClient
from src.modules.data_pipeline.schemas.api_responses import (
    ParcelData,
    ParcelDetailData,
)

logger = structlog.get_logger("data_pipeline.tkgm")


class TKGMClient(BaseAPIClient):
    """
    TKGM MEGSiS API client — Parsel ve kadastro sorgulamalari.

    TKGM birden fazla API endpoint'i sunuyor. Bu client once
    birincil endpoint'i dener, basarisiz olursa alternatife gecer.

    Kullanim:
        async with TKGMClient() as client:
            parcel = await client.get_parcel_by_coordinate(41.0082, 28.9784)
            detail = await client.get_parcel_info("istanbul", "besiktas", "levent", "1234", "5")
    """

    SOURCE_NAME = "tkgm"

    # ---- API Base URL'leri (oncelik sirasina gore) ----
    PRIMARY_API_URL = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api"
    SECONDARY_API_URL = "https://cbsservis.tkgm.gov.tr/megsiswebapi.v3/api"
    LEGACY_API_URL = "https://megsisapi.tkgm.gov.tr"

    # ---- WMS/WFS (protokol anlasmasi gerekli) ----
    WMS_URL = "http://cbsservis.tkgm.gov.tr/tkgm.ows/wms"
    WFS_URL = "http://cbsservis.tkgm.gov.tr/tkgm.ows/wfs"

    # ---- WMS Katman Isimleri ----
    LAYER_MEGSIS = "TKGM:MEGSIS"
    LAYER_PARCELS = "TKGM:parseller"
    LAYER_NEIGHBORHOODS = "TKGM:mahalleler"
    LAYER_PROVINCES = "TKGM:iller"

    def __init__(
        self,
        base_url: str = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": "https://parselsorgu.tkgm.gov.tr/",
            },
        )

    # ================================================================
    # Idari Yapi Sorgulari
    # ================================================================

    async def get_provinces(self) -> list[dict[str, Any]]:
        """
        Turkiye il listesi.

        Returns:
            Il listesi. Her il: {"id": int, "text": str, ...}
        """
        logger.info("tkgm_provinces_query")
        response = await self._get("/idariYapi/ilListe")
        return response.json()

    async def get_districts(self, province_id: int) -> list[dict[str, Any]]:
        """
        Belirtilen ilin ilce listesi.

        Args:
            province_id: Il ID'si (get_provinces'tan alinir)

        Returns:
            Ilce listesi
        """
        logger.info("tkgm_districts_query", province_id=province_id)
        response = await self._get(f"/idariYapi/ilceListe/{province_id}")
        return response.json()

    async def get_neighborhoods(self, district_id: int) -> list[dict[str, Any]]:
        """
        Belirtilen ilcenin mahalle/koy listesi.

        Args:
            district_id: Ilce ID'si (get_districts'tan alinir)

        Returns:
            Mahalle listesi
        """
        logger.info("tkgm_neighborhoods_query", district_id=district_id)
        response = await self._get(f"/idariYapi/mahalleListe/{district_id}")
        return response.json()

    # ================================================================
    # Parsel Sorgulari
    # ================================================================

    async def get_parcel_by_coordinate(
        self,
        latitude: float,
        longitude: float,
    ) -> ParcelData:
        """
        Koordinattan ada/parsel bilgisi.

        Verilen enlem/boylam icin TKGM'den parsel bilgisi sorgular.
        Dogrulanmis endpoint: GET /parsel/{latitude}/{longitude}/

        Args:
            latitude: Enlem (WGS84, orn: 39.87431706591352)
            longitude: Boylam (WGS84, orn: 32.859305441379554)

        Returns:
            ParcelData

        Raises:
            APIResponseError: API hata dondururse
            ValueError: Koordinatta parsel bulunamazsa
        """
        logger.info(
            "tkgm_coordinate_query",
            latitude=latitude,
            longitude=longitude,
        )

        # ---- Birincil: /parsel/{lat}/{lng}/ (dogrulanmis endpoint) ----
        try:
            response = await self._get(
                f"/parsel/{latitude}/{longitude}/",
            )
            data = response.json()

            # GeoJSON Feature response
            if data and (data.get("type") == "Feature" or data.get("properties")):
                return self._parse_geojson_parcel(data)

            # Duz JSON response
            if data:
                return self._parse_parcel_response(data)

        except Exception:
            logger.debug(
                "tkgm_coordinate_primary_failed",
                latitude=latitude,
                longitude=longitude,
            )

        # ---- Yedek: WMS GetFeatureInfo ----
        try:
            return await self._get_parcel_via_wms(latitude, longitude)
        except Exception:
            logger.error(
                "tkgm_all_coordinate_methods_failed",
                latitude=latitude,
                longitude=longitude,
            )
            raise

    async def get_parcel_info(
        self,
        city: str,
        district: str,
        neighborhood: str,
        ada: str,
        parsel: str,
    ) -> ParcelDetailData:
        """
        Ada/parsel numarasindan detay bilgi.

        Uc asamali sorgu:
        1. Il → il_id
        2. Ilce → ilce_id → Mahalle → mahalle_id
        3. mahalle_id/ada/parsel → parsel detay (GeoJSON Feature)

        Args:
            city: Il adi
            district: Ilce adi
            neighborhood: Mahalle adi
            ada: Ada numarasi
            parsel: Parsel numarasi

        Returns:
            ParcelDetailData
        """
        logger.info(
            "tkgm_parcel_info_query",
            city=city,
            district=district,
            neighborhood=neighborhood,
            ada=ada,
            parsel=parsel,
        )

        # Adim 1: Il ID'sini bul
        provinces = await self.get_provinces()
        province_id = self._find_id_by_name(provinces, city)
        if province_id is None:
            msg = f"Il bulunamadi: {city}"
            raise ValueError(msg)

        # Adim 2: Ilce ID'sini bul
        districts = await self.get_districts(province_id)
        district_id = self._find_id_by_name(districts, district)
        if district_id is None:
            msg = f"Ilce bulunamadi: {district}"
            raise ValueError(msg)

        # Adim 3: Mahalle ID'sini bul
        neighborhoods = await self.get_neighborhoods(district_id)
        neighborhood_id = self._find_id_by_name(neighborhoods, neighborhood)
        if neighborhood_id is None:
            msg = f"Mahalle bulunamadi: {neighborhood}"
            raise ValueError(msg)

        # Adim 4: Parsel bilgisini cek (GeoJSON Feature response)
        response = await self._get(f"/parsel/{neighborhood_id}/{ada}/{parsel}")
        data = response.json()

        return self._parse_geojson_parcel_detail(data, city, district, neighborhood, ada, parsel)

    async def get_parcel_geometry(
        self,
        neighborhood_id: int,
        ada: str,
        parsel: str,
    ) -> dict:
        """
        Parsel sinir geometrisi (GeoJSON).

        Args:
            neighborhood_id: Mahalle ID'si
            ada: Ada numarasi
            parsel: Parsel numarasi

        Returns:
            GeoJSON Polygon dict
        """
        logger.info(
            "tkgm_parcel_geometry_query",
            neighborhood_id=neighborhood_id,
            ada=ada,
            parsel=parsel,
        )

        response = await self._get(f"/parselbagligeometri/{neighborhood_id}/{ada}/{parsel}")
        data = response.json()

        # GeoJSON Feature response — geometry ust seviyede
        if data.get("type") == "Feature":
            geometry = data.get("geometry")
            if geometry:
                return geometry

        # Duz response — geometry veya geom field'inda
        geometry = (
            data.get("geometry") or data.get("geom") or data.get("properties", {}).get("geometry")
        )

        if geometry is None:
            logger.warning(
                "tkgm_no_geometry",
                neighborhood_id=neighborhood_id,
                ada=ada,
                parsel=parsel,
            )
            return {"type": "Polygon", "coordinates": []}

        return geometry

    # ================================================================
    # WMS Sorgulari (Yedek — Protokol Gerekebilir)
    # ================================================================

    async def _get_parcel_via_wms(
        self,
        latitude: float,
        longitude: float,
    ) -> ParcelData:
        """
        WMS GetFeatureInfo ile koordinattan parsel bilgisi.

        Dogrulanmis WMS URL: cbsservis.tkgm.gov.tr/tkgm.ows/wms
        Katman: TKGM:parseller
        SRS: EPSG:4326

        NOT: WMS/WFS servisleri TKGM ile protokol anlasmasi gerektirir.
        Bu metod yedek olarak kullanilir ve basarisiz olabilir.
        """
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": self.LAYER_PARCELS,
            "QUERY_LAYERS": self.LAYER_PARCELS,
            "INFO_FORMAT": "application/json",
            "SRS": "EPSG:4326",
            "WIDTH": "256",
            "HEIGHT": "256",
            "X": "128",
            "Y": "128",
            "BBOX": self._point_to_bbox(latitude, longitude),
        }

        async with httpx.AsyncClient(timeout=15.0) as wms_client:
            response = await wms_client.get(self.WMS_URL, params=params)
            response.raise_for_status()
            data = response.json()

        features = data.get("features", [])
        if not features:
            msg = f"WMS'te parsel bulunamadi: {latitude}, {longitude}"
            raise ValueError(msg)

        return self._parse_wms_feature(features[0])

    # ================================================================
    # Yardimci Metodlar
    # ================================================================

    @staticmethod
    def _find_id_by_name(
        items: list[dict],
        name: str,
    ) -> int | None:
        """
        Isimden ID bul (buyuk/kucuk harf duyarsiz, Turkce karakter uyumlu).

        MEGSiS API response'larinda il/ilce/mahalle isimleri farkli
        field isimlerinde olabilir: "text", "name", "ad"
        """
        name_lower = name.lower()
        for item in items:
            item_name = str(item.get("text", item.get("name", item.get("ad", "")))).lower()
            if name_lower in item_name or item_name in name_lower:
                return int(item.get("id", item.get("value", 0)))
        return None

    @staticmethod
    def _parse_geojson_parcel(data: dict) -> ParcelData:
        """
        GeoJSON Feature response'unu ParcelData'ya donustur.

        Dogrulanmis GeoJSON properties alanlari:
        - ilAd, ilceAd, mahalleAd, adaNo, parselNo, alan, nitelik, mevkii, pafta
        """
        props = data.get("properties", data)
        geometry = data.get("geometry", {})

        # Merkez koordinatini geometriden hesapla (varsa)
        lat, lon = None, None
        if geometry and geometry.get("coordinates"):
            lat, lon = _centroid_from_polygon(geometry.get("coordinates", []))

        return ParcelData(
            city=str(props.get("ilAd", props.get("IL", props.get("il", "")))),
            district=str(props.get("ilceAd", props.get("ILCE", props.get("ilce", "")))),
            neighborhood=str(
                props.get("mahalleAd", props.get("MAHALLE", props.get("mahalle", "")))
            ),
            block_number=str(props.get("adaNo", props.get("ADA", props.get("ada", "")))),
            parcel_number=str(props.get("parselNo", props.get("PARSEL", props.get("parsel", "")))),
            area_m2=_safe_float(props.get("alan", props.get("ALAN"))),
            latitude=lat,
            longitude=lon,
        )

    @staticmethod
    def _parse_geojson_parcel_detail(
        data: dict,
        city: str,
        district: str,
        neighborhood: str,
        ada: str,
        parsel: str,
    ) -> ParcelDetailData:
        """
        GeoJSON Feature response'unu ParcelDetailData'ya donustur.

        Dogrulanmis ek alanlar: nitelik, mevkii, zeminKmdurum, pafta
        """
        props = data.get("properties", data)

        return ParcelDetailData(
            city=str(props.get("ilAd", city)),
            district=str(props.get("ilceAd", district)),
            neighborhood=str(props.get("mahalleAd", neighborhood)),
            block_number=str(props.get("adaNo", ada)),
            parcel_number=str(props.get("parselNo", parsel)),
            area_m2=_safe_float(props.get("alan", props.get("ALAN"))),
            land_use_type=props.get("nitelik", props.get("NITELIK")),
            zoning_status=props.get("zeminKmdurum", props.get("IMAR")),
            ownership_type=props.get("MULKIYET", props.get("mulkiyet")),
            geometry=data.get("geometry") or data.get("geom"),
        )

    @staticmethod
    def _parse_parcel_response(data: dict) -> ParcelData:
        """Eski format MEGSiS API parsel yanitini ParcelData'ya donustur."""
        props = data.get("properties", data)
        return ParcelData(
            city=str(props.get("IL", props.get("ilAd", props.get("il", "")))),
            district=str(props.get("ILCE", props.get("ilceAd", props.get("ilce", "")))),
            neighborhood=str(
                props.get("MAHALLE", props.get("mahalleAd", props.get("mahalle", "")))
            ),
            block_number=str(props.get("ADA", props.get("adaNo", props.get("ada", "")))),
            parcel_number=str(props.get("PARSEL", props.get("parselNo", props.get("parsel", "")))),
            area_m2=_safe_float(props.get("ALAN", props.get("alan"))),
            latitude=_safe_float(props.get("LAT", props.get("lat"))),
            longitude=_safe_float(props.get("LON", props.get("lon"))),
        )

    @staticmethod
    def _parse_wms_feature(feature: dict) -> ParcelData:
        """WMS GetFeatureInfo yanitini ParcelData'ya donustur."""
        props = feature.get("properties", {})
        return ParcelData(
            city=str(props.get("IL", props.get("ilAd", ""))),
            district=str(props.get("ILCE", props.get("ilceAd", ""))),
            neighborhood=str(props.get("MAHALLE", props.get("mahalleAd", ""))),
            block_number=str(props.get("ADA", props.get("adaNo", ""))),
            parcel_number=str(props.get("PARSEL", props.get("parselNo", ""))),
            area_m2=_safe_float(props.get("ALAN", props.get("alan"))),
        )

    @staticmethod
    def _point_to_bbox(
        latitude: float,
        longitude: float,
        buffer: float = 0.001,
    ) -> str:
        """Nokta koordinatindan WMS BBOX olustur (EPSG:4326 sirasi: lon,lat)."""
        return f"{longitude - buffer},{latitude - buffer},{longitude + buffer},{latitude + buffer}"


# ================================================================
# Module-level Yardimci Fonksiyonlar
# ================================================================


def _safe_float(value: Any) -> float | None:
    """
    Degeri guvenli sekilde float'a cevir.

    TKGM alan degerleri virgullu format kullanabilir: "7,722.87"
    """
    if value is None:
        return None
    try:
        # TKGM "7,722.87" formatinda dondurur — binlik ayirici virgul
        cleaned = str(value).replace(",", "")
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _centroid_from_polygon(coordinates: list) -> tuple[float | None, float | None]:
    """
    GeoJSON Polygon koordinatlarindan yaklasik merkez noktasi hesapla.

    Args:
        coordinates: GeoJSON Polygon coordinates (list of rings)

    Returns:
        (latitude, longitude) tuple veya (None, None)
    """
    if not coordinates or not coordinates[0]:
        return None, None

    try:
        ring = coordinates[0]  # Dis halka
        n = len(ring)
        if n == 0:
            return None, None

        avg_lon = sum(pt[0] for pt in ring) / n
        avg_lat = sum(pt[1] for pt in ring) / n
        return avg_lat, avg_lon
    except (IndexError, TypeError, ZeroDivisionError):
        return None, None
