"""
Emlak Teknoloji Platformu - AFAD TDTH & Deprem API Client

AFAD (Afet ve Acil Durum Yonetimi Baskanligi) verilerine erisim:
- TDTH: Turkiye Deprem Tehlike Haritalari (Ss, S1, PGA parametreleri)
- deprem.afad.gov.tr: Son depremler ve deprem olcum verileri
- TUCBS WMS: Turkiye Ulusal Cografi Bilgi Sistemi (acik WMS servisi)

VERI KAYNAKLARI:
1. tucbs-public-api.csb.gov.tr — TUCBS WMS servisi (ACIK, auth YOK, 99 katman)
   - SS, S1, PGA, PGV verileri tum tekrarlanma periyotlari icin
   - Aktif fay hatlari (layer 82: diri_fay_07052014)
   - GetFeatureInfo ile koordinat bazli sorgu (JSON)
2. deprem.afad.gov.tr/apiv2 — Deprem olay verileri (acik API)
3. tdth.afad.gov.tr — TDTH interaktif uygulama (e-Devlet giris ZORUNLU)
4. cdn.arcgis.com — ArcGIS katmani (yedek, TUCBS WMS ile ayni veriyi kullanir)

TUCBS WMS KATMAN REFERANSI:
  SS (Kisa Periyot Spektral Ivme, 0.2s):
    Layer  9 → TSTH_SS_475   (DD-2, 475 yil)
    Layer 17 → TSTH_SS_2475  (DD-1, 2475 yil)
    Layer 12 → TSTH_SS_43    (DD-4, 43 yil)
    Layer  5 → TSTH_SS_72    (DD-3, 72 yil)
  S1 (1 Saniye Periyot Spektral Ivme):
    Layer 26 → TSTH_S1_475   (DD-2, 475 yil)
    Layer 34 → TSTH_S1_2475  (DD-1, 2475 yil)
  PGA (Peak Ground Acceleration):
    Layer 58 → TSTH_PGA_475  (DD-2, 475 yil)
    Layer 66 → TSTH_PGA_2475 (DD-1, 2475 yil)
  Diger:
    Layer 82 → diri_fay_07052014 (Aktif fay hatlari)

ONEMLI NOTLAR:
- TUCBS WMS GetFeatureInfo raster pixel renk degeri (RGB Red channel, 0-255) donduruyor,
  muhendislik degeri (g cinsinden) DEGIL. Renk-deger donusum tablosu gerekli.
- TDTH (tdth.afad.gov.tr) e-Devlet giris gerektirir — otomatik erisim MUMKUN DEGIL
- TBDY 2018 tekrarlanma periyotlari: DD-1=2475, DD-2=475, DD-3=72, DD-4=43 yil
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from src.modules.data_pipeline.clients.base_client import BaseAPIClient
from src.modules.data_pipeline.schemas.api_responses import (
    EarthquakeHazardData,
    FaultData,
)

logger = structlog.get_logger("data_pipeline.afad")


class AFADClient(BaseAPIClient):
    """
    AFAD deprem veri client'i.

    Uc katmanli erisim:
    1. Deprem tehlike parametreleri → TUCBS WMS (acik, auth yok, BIRINCIL)
    2. Deprem olay verileri → deprem.afad.gov.tr/apiv2 (acik API)
    3. TDTH fallback → tdth.afad.gov.tr (e-Devlet; genellikle basarisiz)

    Kullanim:
        async with AFADClient() as client:
            hazard = await client.get_earthquake_hazard(41.0082, 28.9784)
            recent = await client.get_recent_earthquakes(min_magnitude=4.0)
            faults = await client.get_nearby_faults(41.0082, 28.9784)
    """

    SOURCE_NAME = "afad"

    # deprem.afad.gov.tr — Acik API
    EARTHQUAKE_API_BASE = "https://deprem.afad.gov.tr"

    # TUCBS WMS — BIRINCIL kaynak (acik, auth yok)
    TUCBS_WMS_BASE = "https://tucbs-public-api.csb.gov.tr/trk_afad_tdth_wms"

    # TDTH — e-Devlet gerekli (otomatik erisim sinirli)
    TDTH_BASE = "https://tdth.afad.gov.tr"

    # ArcGIS — AFAD deprem tehlike haritasi katmani (yedek)
    ARCGIS_LAYER_URL = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services"

    # ---- TUCBS WMS Katman ID'leri (dogrulanmis) ----
    # SS — Kisa periyot spektral ivme katsayisi (0.2s)
    LAYER_SS_475 = 9  # DD-2: 475 yil tekrarlanma periyodu (standart)
    LAYER_SS_2475 = 17  # DD-1: 2475 yil
    LAYER_SS_72 = 5  # DD-3: 72 yil
    LAYER_SS_43 = 12  # DD-4: 43 yil

    # S1 — 1 saniye periyot spektral ivme katsayisi
    LAYER_S1_475 = 26  # DD-2: 475 yil
    LAYER_S1_2475 = 34  # DD-1: 2475 yil
    LAYER_S1_72 = 21  # DD-3: 72 yil
    LAYER_S1_43 = 30  # DD-4: 43 yil

    # PGA — Peak Ground Acceleration
    LAYER_PGA_475 = 58  # DD-2: 475 yil (standart tasarim)
    LAYER_PGA_2475 = 66  # DD-1: 2475 yil
    LAYER_PGA_72 = 54  # DD-3: 72 yil
    LAYER_PGA_43 = 62  # DD-4: 43 yil

    # Aktif Fay Hatlari
    LAYER_ACTIVE_FAULTS = 82  # diri_fay_07052014

    def __init__(
        self,
        base_url: str = "https://deprem.afad.gov.tr",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    # ================================================================
    # Deprem Tehlike Parametreleri (TUCBS WMS — Birincil Kaynak)
    # ================================================================

    async def get_earthquake_hazard(
        self,
        latitude: float,
        longitude: float,
    ) -> EarthquakeHazardData:
        """
        Belirtilen koordinat icin deprem tehlike parametreleri.

        Strateji sirasi:
        1. TUCBS WMS GetFeatureInfo (acik, birincil) — SS, S1, PGA
        2. TDTH endpoint deneme (genellikle basarisiz)
        3. ArcGIS katmani (yedek PGA degeri)
        4. Varsayilan degerler (son care)

        Args:
            latitude: Enlem (orn: 41.0082 — Istanbul)
            longitude: Boylam (orn: 28.9784 — Istanbul)

        Returns:
            EarthquakeHazardData (mevcut verilerle doldurulmus)
        """
        logger.info(
            "afad_hazard_query",
            latitude=latitude,
            longitude=longitude,
        )

        # ---- Strateji 1: TUCBS WMS GetFeatureInfo ----
        tucbs_data = await self._get_hazard_from_tucbs_wms(latitude, longitude)

        if tucbs_data:
            logger.info(
                "afad_tucbs_wms_success",
                latitude=latitude,
                longitude=longitude,
                layers_received=list(tucbs_data.keys()),
            )
            return EarthquakeHazardData(
                latitude=latitude,
                longitude=longitude,
                pga_475=tucbs_data.get("pga_475", 0.0),
                pga_2475=tucbs_data.get("pga_2475"),
                ss=tucbs_data.get("ss_475"),
                s1=tucbs_data.get("s1_475"),
                ss_2475=tucbs_data.get("ss_2475"),
                s1_2475=tucbs_data.get("s1_2475"),
                data_source="tucbs_wms",
            )

        # ---- Strateji 2: TDTH endpoint deneme (basarisiz olabilir) ----
        tdth_data = await self._try_tdth_query(latitude, longitude)

        if tdth_data:
            return EarthquakeHazardData(
                latitude=latitude,
                longitude=longitude,
                pga_475=tdth_data.get("pga_475", 0.0),
                pga_2475=tdth_data.get("pga_2475"),
                ss=tdth_data.get("ss"),
                s1=tdth_data.get("s1"),
                soil_class=tdth_data.get("soil_class"),
                design_ground_type=tdth_data.get("design_ground_type"),
                data_source="tdth",
            )

        # ---- Strateji 3: ArcGIS PGA fallback ----
        pga_475 = await self._get_pga_from_arcgis(latitude, longitude)

        return EarthquakeHazardData(
            latitude=latitude,
            longitude=longitude,
            pga_475=pga_475,
            data_source="arcgis_fallback" if pga_475 != 0.4 else "default",
        )

    async def get_pga_value(
        self,
        latitude: float,
        longitude: float,
        return_period: int = 475,
    ) -> float:
        """
        Peak Ground Acceleration (PGA) degeri (g cinsinden).

        Args:
            latitude: Enlem
            longitude: Boylam
            return_period: Tekrarlanma periyodu (475 veya 2475 yil)

        Returns:
            PGA degeri (g cinsinden). Alinamazsa 0.0 doner.
        """
        hazard = await self.get_earthquake_hazard(latitude, longitude)
        if return_period == 2475 and hazard.pga_2475 is not None:
            return hazard.pga_2475
        return hazard.pga_475

    async def get_soil_class(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        """
        Zemin siniflandirmasi (ZA-ZE).

        NOT: Zemin sinifi TDTH'den alinir. TDTH erisilemezse "ZC" (varsayilan)
        dondurulur ve log kaydedilir. TUCBS WMS zemin sinifi icermiyor.

        Args:
            latitude: Enlem
            longitude: Boylam

        Returns:
            Zemin sinifi string (ZA, ZB, ZC, ZD, ZE)
        """
        hazard = await self.get_earthquake_hazard(latitude, longitude)
        if hazard.soil_class:
            return hazard.soil_class

        logger.warning(
            "afad_soil_class_unavailable",
            latitude=latitude,
            longitude=longitude,
            msg="TDTH erisilemedi, varsayilan ZC donduruluyor",
        )
        return "ZC"  # Varsayilan zemin sinifi

    async def get_nearby_faults(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50,
    ) -> list[FaultData]:
        """
        Yakinlardaki aktif fay hatlari.

        TUCBS WMS layer 82 (diri_fay_07052014) uzerinden koordinat yakinindaki
        fay hatlarini sorgular. GetFeatureInfo kullanarak belirtilen bolgedeki
        fay hatti bilgilerini alir.

        Args:
            latitude: Enlem
            longitude: Boylam
            radius_km: Arama yaricapi (km)

        Returns:
            FaultData listesi
        """
        logger.info(
            "afad_nearby_faults_query",
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        return await self._get_faults_from_tucbs_wms(latitude, longitude, radius_km)

    # ================================================================
    # Deprem Olay Verileri (Acik API)
    # ================================================================

    async def get_recent_earthquakes(
        self,
        min_magnitude: float = 0.0,
        limit: int = 100,
    ) -> list[dict]:
        """
        Son depremler (deprem.afad.gov.tr acik API).

        Args:
            min_magnitude: Minimum buyukluk filtresi
            limit: Maksimum sonuc sayisi

        Returns:
            Deprem olay listesi (ham dict)
        """
        response = await self._get(
            "/apiv2/event/filter",
            params={
                "limit": str(limit),
                "orderby": "timedesc",
            },
        )
        data = response.json()

        # Minimum buyukluk filtresi
        events = data if isinstance(data, list) else data.get("result", [])
        if min_magnitude > 0:
            events = [e for e in events if float(e.get("magnitude", 0)) >= min_magnitude]

        return events

    async def get_earthquakes_by_region(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 100,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """
        Belirli bir bolgedeki depremler (koordinat + yaricap).

        Args:
            latitude: Merkez enlem
            longitude: Merkez boylam
            radius_km: Arama yaricapi (km)
            start_date: Baslangic tarihi (YYYY-MM-DDThh:mm:ss)
            end_date: Bitis tarihi (YYYY-MM-DDThh:mm:ss)

        Returns:
            Deprem olay listesi
        """
        params: dict[str, str] = {
            "lat": str(latitude),
            "lon": str(longitude),
            "maxrad": str(radius_km * 1000),  # API metre cinsinden bekliyor
            "orderby": "timedesc",
        }

        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        response = await self._get("/apiv2/event/filter", params=params)
        result = response.json()
        return result if isinstance(result, list) else result.get("result", [])

    # ================================================================
    # TUCBS WMS Sorgu Metodlari (Birincil Kaynak)
    # ================================================================

    async def _get_hazard_from_tucbs_wms(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, float] | None:
        """
        TUCBS WMS GetFeatureInfo ile deprem tehlike parametreleri.

        Birden fazla katmani (SS-475, S1-475, PGA-475, SS-2475, S1-2475, PGA-2475)
        paralel olarak sorgular.

        ONEMLI: TUCBS WMS raster pixel renk degeri (RGB Red channel) donduruyor.
        Bu deger dogrudan muhendislik degeri degildir. Renk-deger donusumu icin
        AFAD'in yayinladigi renk skalasi referans alinmalidir.

        GetFeatureInfo JSON response ornegi:
            {"layers": [{"id": "TSTH_SS_475", "features": [
                {"id": "ELEVATION", "results": [
                    {"key": "ELEVATION", "value": "172.0"},
                    {"key": "UNIT", "value": "RED]"},
                    {"key": "X", "value": "28.9784"},
                    {"key": "Y", "value": "41.0082"}
                ]}
            ]}]}

        Args:
            latitude: Enlem
            longitude: Boylam

        Returns:
            dict[str, float] parametreler veya None (erisilemezse)
        """
        # Koordinat merkezli kucuk BBOX olustur (yaklasik 100m x 100m)
        delta = 0.001  # ~111m
        bbox = f"{longitude - delta},{latitude - delta},{longitude + delta},{latitude + delta}"

        # Sorgulanacak katmanlar ve sonuc isimleri
        layer_mapping: dict[str, int] = {
            "ss_475": self.LAYER_SS_475,
            "s1_475": self.LAYER_S1_475,
            "pga_475": self.LAYER_PGA_475,
            "ss_2475": self.LAYER_SS_2475,
            "s1_2475": self.LAYER_S1_2475,
            "pga_2475": self.LAYER_PGA_2475,
        }

        results: dict[str, float] = {}

        try:
            async with httpx.AsyncClient(timeout=20.0) as wms_client:
                for param_name, layer_id in layer_mapping.items():
                    value = await self._query_tucbs_layer(wms_client, layer_id, bbox)
                    if value is not None:
                        results[param_name] = value

        except Exception as exc:
            logger.warning(
                "afad_tucbs_wms_failed",
                latitude=latitude,
                longitude=longitude,
                error=str(exc),
            )
            return None

        if not results:
            logger.warning(
                "afad_tucbs_wms_no_data",
                latitude=latitude,
                longitude=longitude,
            )
            return None

        return results

    async def _query_tucbs_layer(
        self,
        client: httpx.AsyncClient,
        layer_id: int,
        bbox: str,
    ) -> float | None:
        """
        Tek bir TUCBS WMS katmanini GetFeatureInfo ile sorgula.

        ONEMLI: CRS:84 kullanilmalidir (lon,lat sirasi).
        FORMAT ve STYLES parametreleri GetFeatureInfo icin de zorunludur.

        Args:
            client: httpx.AsyncClient
            layer_id: WMS katman ID'si
            bbox: BBOX string (lon_min,lat_min,lon_max,lat_max)

        Returns:
            float renk degeri (0-255 arasi RGB Red channel) veya None
        """
        params: dict[str, str] = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": str(layer_id),
            "QUERY_LAYERS": str(layer_id),
            "CRS": "CRS:84",
            "BBOX": bbox,
            "WIDTH": "256",
            "HEIGHT": "256",
            "I": "128",  # Merkez piksel
            "J": "128",
            "INFO_FORMAT": "application/json",
            "FORMAT": "image/png",  # GetFeatureInfo icin de zorunlu
            "STYLES": "default",  # GetFeatureInfo icin de zorunlu
        }

        try:
            response = await client.get(self.TUCBS_WMS_BASE, params=params)

            if response.status_code != 200:
                logger.debug(
                    "afad_tucbs_layer_error",
                    layer_id=layer_id,
                    status=response.status_code,
                )
                return None

            data = response.json()
            return self._parse_tucbs_feature_info(data, layer_id)

        except Exception as exc:
            logger.debug(
                "afad_tucbs_layer_query_failed",
                layer_id=layer_id,
                error=str(exc),
            )
            return None

    @staticmethod
    def _parse_tucbs_feature_info(
        data: dict[str, Any],
        layer_id: int,
    ) -> float | None:
        """
        TUCBS WMS GetFeatureInfo JSON response'unu parse et.

        Response yapisi:
            {"layers": [{"id": "TSTH_SS_475", "features": [
                {"id": "ELEVATION", "results": [
                    {"key": "ELEVATION", "value": "172.0"},
                    {"key": "UNIT", "value": "RED]"},
                    ...
                ]}
            ]}]}

        NOT: ELEVATION degeri RGB Red channel renk degeridir (0-255).
        Gercek muhendislik degerine donusum icin renk skalasi tablosu
        kullanilmalidir. Bu deger simdilik ham haliyle dondurulur.

        Args:
            data: GetFeatureInfo JSON response
            layer_id: Sorgulanan katman ID'si

        Returns:
            float pixel degeri veya None
        """
        layers = data.get("layers", [])
        if not layers:
            return None

        for layer in layers:
            features = layer.get("features", [])
            for feature in features:
                results = feature.get("results", [])
                for result in results:
                    if result.get("key") == "ELEVATION":
                        try:
                            return float(result["value"])
                        except (ValueError, KeyError, TypeError):
                            continue

        # staticmethod icinden module-level logger kullanilir
        structlog.get_logger("data_pipeline.afad").debug(
            "afad_tucbs_no_elevation",
            layer_id=layer_id,
        )
        return None

    async def _get_faults_from_tucbs_wms(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50,
    ) -> list[FaultData]:
        """
        TUCBS WMS layer 82 (diri_fay_07052014) uzerinden aktif fay hatlari.

        Belirtilen koordinat merkezli bir BBOX olusturarak fay hatti
        katmanini GetFeatureInfo ile sorgular.

        Args:
            latitude: Enlem
            longitude: Boylam
            radius_km: Arama yaricapi (km)

        Returns:
            FaultData listesi
        """
        # radius_km'yi derece cinsine donustur (yaklasik)
        delta_deg = radius_km / 111.0  # 1 derece ≈ 111 km

        bbox = (
            f"{longitude - delta_deg},{latitude - delta_deg},"
            f"{longitude + delta_deg},{latitude + delta_deg}"
        )

        params: dict[str, str] = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": str(self.LAYER_ACTIVE_FAULTS),
            "QUERY_LAYERS": str(self.LAYER_ACTIVE_FAULTS),
            "CRS": "CRS:84",
            "BBOX": bbox,
            "WIDTH": "256",
            "HEIGHT": "256",
            "I": "128",
            "J": "128",
            "INFO_FORMAT": "application/json",
            "FORMAT": "image/png",
            "STYLES": "default",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as wms_client:
                response = await wms_client.get(self.TUCBS_WMS_BASE, params=params)

                if response.status_code != 200:
                    logger.warning(
                        "afad_tucbs_fault_query_error",
                        status=response.status_code,
                    )
                    return []

                data = response.json()
                return self._parse_fault_features(data, latitude, longitude)

        except Exception as exc:
            logger.warning(
                "afad_tucbs_fault_query_failed",
                latitude=latitude,
                longitude=longitude,
                error=str(exc),
            )
            return []

    @staticmethod
    def _parse_fault_features(
        data: dict[str, Any],
        ref_lat: float,
        ref_lon: float,
    ) -> list[FaultData]:
        """
        TUCBS WMS fay hatti GetFeatureInfo response'unu parse et.

        NOT: WMS GetFeatureInfo fay hatti icin sinirli bilgi dondurebilir.
        Daha detayli fay verisi icin MTA Diri Fay Haritasi WFS servisi
        gerekebilir.

        Args:
            data: GetFeatureInfo JSON response
            ref_lat: Referans enlem (mesafe hesabi icin)
            ref_lon: Referans boylam (mesafe hesabi icin)

        Returns:
            FaultData listesi
        """
        faults: list[FaultData] = []
        layers = data.get("layers", [])

        for layer in layers:
            features = layer.get("features", [])
            for feature in features:
                results = feature.get("results", [])
                attrs: dict[str, str] = {}
                for result in results:
                    key = result.get("key", "")
                    value = result.get("value", "")
                    attrs[key] = value

                # Fay hatti bilgisi varsa FaultData olustur
                fault_name = (
                    attrs.get("ADI")  # Turkce alan adi
                    or attrs.get("NAME")
                    or attrs.get("name")
                    or f"Fay hatti ({ref_lat:.2f}, {ref_lon:.2f})"
                )

                fault_type = attrs.get("TUR") or attrs.get("TYPE") or attrs.get("type")

                # Mesafe bilgisi WMS'den gelmez — 0.0 olarak isaretle
                faults.append(
                    FaultData(
                        name=fault_name,
                        distance_km=0.0,  # WMS'den mesafe hesaplanamaz
                        fault_type=fault_type,
                    )
                )

        if not faults:
            logger.info(
                "afad_no_fault_data_in_region",
                latitude=ref_lat,
                longitude=ref_lon,
                msg="TUCBS WMS'de bu bolge icin fay verisi bulunamadi",
            )

        return faults

    # ================================================================
    # ArcGIS Fallback (Yedek)
    # ================================================================

    async def _get_pga_from_arcgis(
        self,
        latitude: float,
        longitude: float,
    ) -> float:
        """
        ArcGIS katmanindan yaklasik PGA degeri al.

        AFAD'in deprem tehlike haritasi ArcGIS Online'da yayinlaniyor.
        ArcGIS item ID: a5c56050d1c04403aa808e7482d2c378
        Bu katman ayni TUCBS WMS verisini kullaniyor.

        NOT: ArcGIS sorgusu basarisiz olursa varsayilan PGA degeri dondurulur.
        """
        try:
            query_url = (
                f"{self.ARCGIS_LAYER_URL}/a5c56050d1c04403aa808e7482d2c378/FeatureServer/0/query"
            )

            async with httpx.AsyncClient(timeout=15.0) as arcgis_client:
                response = await arcgis_client.get(
                    query_url,
                    params={
                        "geometry": f"{longitude},{latitude}",
                        "geometryType": "esriGeometryPoint",
                        "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "*",
                        "returnGeometry": "false",
                        "f": "json",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    features = data.get("features", [])
                    if features:
                        attrs = features[0].get("attributes", {})
                        pga = (
                            attrs.get("PGA")
                            or attrs.get("pga")
                            or attrs.get("PGA_475")
                            or attrs.get("gridcode")
                        )
                        if pga is not None:
                            return float(pga)

        except Exception as exc:
            logger.warning(
                "afad_arcgis_query_failed",
                latitude=latitude,
                longitude=longitude,
                error=str(exc),
            )

        # Varsayilan PGA degeri (Turkiye ortalamasi)
        logger.info(
            "afad_pga_default",
            latitude=latitude,
            longitude=longitude,
            msg="ArcGIS erisilemedi, varsayilan PGA kullaniliyor",
        )
        return 0.4  # Orta-yuksek tehlike bolgesi varsayimi

    # ================================================================
    # TDTH Fallback (e-Devlet — genellikle basarisiz)
    # ================================================================

    async def _try_tdth_query(
        self,
        latitude: float,
        longitude: float,
    ) -> dict | None:
        """
        TDTH endpoint'ini deneyerek Ss, S1 parametrelerini almaya calis.

        UYARI: TDTH e-Devlet gerektirdiginden bu sorgu genellikle basarisiz olur.
        Basarili olmasi icin:
        - Onceden olusturulmus session cookie
        - e-Devlet OAuth token (client_id: 824612ca-ff05-4cef-b74a-446363af1669)
        - Kurumlararasi API erisim izni
        gereklidir.

        Returns:
            dict eger basarili ise, None eger erisilemezse
        """
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as tdth_client:
                response = await tdth_client.get(f"{self.TDTH_BASE}/TDTH/userLogin.xhtml")
                # 302 yonlendirme → e-Devlet giris sayfasi
                if response.status_code in (302, 301):
                    logger.debug(
                        "afad_tdth_requires_auth",
                        redirect=response.headers.get("Location", ""),
                    )
                    return None

        except Exception as exc:
            logger.debug("afad_tdth_unreachable", error=str(exc))

        return None
