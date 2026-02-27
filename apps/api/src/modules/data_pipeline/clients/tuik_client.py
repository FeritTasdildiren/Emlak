"""
Emlak Teknoloji Platformu - TUIK MEDAS API Client

TUIK (Turkiye Istatistik Kurumu) verilerine erisim:
- Konut satis istatistikleri (il/ilce bazinda)
- Nufus verileri (il/ilce bazinda)
- Konut fiyat endeksi
- Demografik veriler (yas dagilimi, egitim, gelir)

VERI KAYNAKLARI:
1. data.tuik.gov.tr — Veri Portali (web arayuzu, sinirli API)
2. cip.tuik.gov.tr — Cografi Istatistik Portali (JSON API, authentication yok)
3. birdata.tuik.gov.tr — BirData platformu (yeni)

ONEMLI NOTLAR:
- TUIK resmi bir acik REST API sunmuyor; web servisi icin protokol imzalanmasi gerekebilir
- CIP portali JSON endpoint'leri authentication gerektirmiyor ama resmi API degil
- data.tuik.gov.tr web sitesinden veri indirme web scraping gerektirebilir
- CIP degisken kodlari: INS-GK055-O006 (konut satis), ADNKS-GK137473-O29001 (nufus)
- CIP kaynaklari: "medas" (istatistikler) ve "ilGostergeleri" (il gostergeleri)
"""

from __future__ import annotations

from typing import Any

import structlog

from src.modules.data_pipeline.clients.base_client import BaseAPIClient
from src.modules.data_pipeline.schemas.api_responses import (
    DemographicsData,
    HousingPriceIndex,
    HousingSaleData,
    PopulationData,
)

logger = structlog.get_logger("data_pipeline.tuik")


class TUIKClient(BaseAPIClient):
    """
    TUIK (Turkiye Istatistik Kurumu) veri client'i.

    Birincil kaynak olarak CIP (Cografi Istatistik Portali) API'sini kullanir.
    CIP erisilemezse, data.tuik.gov.tr web scraping fallback'i mevcuttur.

    Kullanim:
        async with TUIKClient() as client:
            sales = await client.get_housing_sales("istanbul", 2024, 1)
    """

    SOURCE_NAME = "tuik"

    # ---- CIP API Base URL'leri ----
    CIP_BASE_URL = "https://cip.tuik.gov.tr"
    DATA_PORTAL_BASE_URL = "https://data.tuik.gov.tr"

    # ---- CIP Degisken Kodlari (sideMenu.json'dan) ----
    # Yapi ve Konut
    VAR_HOUSING_SALES_TOTAL = "INS-GK055-O006"  # Konut satis sayilari (toplam)
    VAR_HOUSING_SALES_FIRST = "INS-GK056-O006"  # Ilk satis
    VAR_BUILDING_PERMITS = "INS-GK057-O006"  # Yapi ruhsati — bina sayisi
    VAR_BUILDING_PERMITS_UNITS = "INS-GK058-O006"  # Yapi ruhsati — daire sayisi

    # Nufus ve Demografi
    VAR_TOTAL_POPULATION = "ADNKS-GK137473-O29001"  # Toplam nufus
    VAR_MALE_POPULATION = "ADNKS-GK1003-O29001"  # Erkek nufus
    VAR_FEMALE_POPULATION = "ADNKS-GK1004-O29001"  # Kadin nufus
    VAR_NET_MIGRATION_RATE = "ADNKS-GK140832-O29009"  # Net goc hizi
    VAR_AVG_HOUSEHOLD_SIZE = "NFS-GK069-O005"  # Ortalama hanehalki buyuklugu

    def __init__(
        self,
        base_url: str = "https://cip.tuik.gov.tr",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            headers={
                "Accept": "application/json",
                "Referer": "https://cip.tuik.gov.tr/",
            },
        )

    # ================================================================
    # CIP API (Cografi Istatistik Portali) — Birincil Kaynak
    # ================================================================

    async def _get_cip_map_data(
        self,
        variable_code: str,
        nuts_level: int = 3,
        record_count: int = 5,
        source: str = "medas",
        period: str = "yillik",
    ) -> list[dict[str, Any]]:
        """
        CIP harita verisi sorgula (dogrulanmis endpoint).

        CIP API (cip.tuik.gov.tr) uzerinden il/ilce bazli istatistik verisi cekilir.
        Dogrulanmis endpoint: /Home/GetMapData

        Ornek URL:
            /Home/GetMapData?kaynak=medas&duzey=3&gostergeNo=INS-GK055-O006&kayitSayisi=5&period=yillik

        Args:
            variable_code: CIP degisken kodu (orn: "INS-GK055-O006")
            nuts_level: NUTS seviyesi (2=Bolge, 3=Il, 4=Ilce, 5=Mahalle)
            record_count: Kac donemlik veri alinacak (3, 5, 24)
            source: Veri kaynagi ("medas" veya "ilGostergeleri")
            period: Donem tipi ("yillik" veya "aylik")

        Returns:
            Il/ilce bazli veri listesi
        """
        params = {
            "kaynak": source,
            "duzey": str(nuts_level),
            "gostergeNo": variable_code,
            "kayitSayisi": str(record_count),
            "period": period,
        }

        logger.info(
            "tuik_cip_query",
            variable=variable_code,
            nuts_level=nuts_level,
            source=source,
        )

        try:
            response = await self._get("/Home/GetMapData", params=params)
            return response.json()
        except Exception:
            # Fallback: Statik JSON dosyasi
            logger.warning(
                "tuik_cip_primary_failed",
                variable=variable_code,
            )
            try:
                response = await self._get(f"/assets/data/{variable_code}.json")
                return response.json()
            except Exception:
                logger.error(
                    "tuik_cip_all_endpoints_failed",
                    variable=variable_code,
                )
                raise

    async def get_housing_sales(
        self,
        city: str,
        year: int,
        month: int | None = None,
    ) -> list[HousingSaleData]:
        """
        Il bazinda konut satis istatistikleri.

        Args:
            city: Il adi (orn: "istanbul", "ankara")
            year: Referans yili
            month: Ay (None ise yillik toplam)

        Returns:
            HousingSaleData listesi
        """
        raw_data = await self._get_cip_map_data(
            variable_code=self.VAR_HOUSING_SALES_TOTAL,
            nuts_level=3,  # Il seviyesi
            record_count=5,  # Son 5 yillik veri
        )

        city_lower = city.lower().replace("i", "ı").replace("İ", "i")
        results: list[HousingSaleData] = []

        for item in raw_data:
            item_city = str(item.get("il", item.get("name", ""))).lower()
            if city_lower not in item_city and item_city not in city_lower:
                continue

            value = item.get("value") or item.get("deger") or 0

            results.append(
                HousingSaleData(
                    city=str(item.get("il", item.get("name", city))),
                    year=year,
                    month=month or 0,
                    total_sales=int(float(str(value))),
                )
            )

        if not results:
            logger.warning("tuik_no_housing_data", city=city, year=year)

        return results

    async def get_population(
        self,
        city: str,
        district: str | None = None,
    ) -> PopulationData:
        """
        Il/ilce nufus verileri.

        Args:
            city: Il adi
            district: Ilce adi (None ise il toplami)

        Returns:
            PopulationData
        """
        nuts_level = 4 if district else 3
        raw_data = await self._get_cip_map_data(
            variable_code=self.VAR_TOTAL_POPULATION,
            nuts_level=nuts_level,
            record_count=3,  # Son 3 yillik nufus verisi
        )

        # Il/ilce filtrele
        target = (district or city).lower()
        for item in raw_data:
            item_name = str(item.get("il", item.get("name", ""))).lower()
            if target in item_name or item_name in target:
                value = item.get("value") or item.get("deger") or 0
                return PopulationData(
                    city=city,
                    district=district,
                    year=int(item.get("yil", 2024)),
                    total_population=int(float(str(value))),
                )

        logger.warning("tuik_no_population_data", city=city, district=district)
        return PopulationData(
            city=city,
            district=district,
            year=2024,
            total_population=0,
        )

    async def get_housing_price_index(
        self,
        year: int,
        quarter: int,
    ) -> HousingPriceIndex:
        """
        Konut fiyat endeksi.

        NOT: TUIK konut fiyat endeksini TCMB ile birlikte yayinlar.
        Bu veri TCMB EVDS'den daha guvenilir sekilde alinabilir.
        TUIK'ten cekilemezse TCMBClient kullanilmalidir.

        Args:
            year: Yil
            quarter: Ceyrek (1-4)

        Returns:
            HousingPriceIndex
        """
        # TODO: TUIK'in konut fiyat endeksi verisi TCMB ile paylasimli
        # data.tuik.gov.tr/Kategori/GetKategori?p=insaat-ve-konut endpointi denenecek
        logger.info("tuik_hpi_query", year=year, quarter=quarter)

        try:
            params = {
                "p": "insaat-ve-konut-116",
                "dil": "1",
            }
            response = await self._get("/Kategori/GetKategori", params=params)
            _raw = response.json()

            # TODO: Response parsing — gercek response yapisina gore uyarlanmali
            return HousingPriceIndex(
                year=year,
                quarter=quarter,
                index_value=0.0,  # Placeholder — gercek veri parse edilecek
            )
        except Exception:
            logger.warning(
                "tuik_hpi_fallback",
                year=year,
                quarter=quarter,
                msg="TUIK HPI alinamadi, TCMB EVDS kullanilmali",
            )
            return HousingPriceIndex(
                year=year,
                quarter=quarter,
                index_value=0.0,
            )

    async def get_demographics(
        self,
        city: str,
        district: str | None = None,
    ) -> DemographicsData:
        """
        Demografik veriler: yas dagilimi, egitim seviyesi.

        Args:
            city: Il adi
            district: Ilce adi (opsiyonel)

        Returns:
            DemographicsData
        """
        # TODO: CIP'ten yas dagilimi ve egitim verileri icin ek degisken kodlari
        # bulunmali. Asagidaki kodlar placeholder — CIP sideMenu.json'dan
        # uygun kodlar secilmeli.
        logger.info("tuik_demographics_query", city=city, district=district)

        return DemographicsData(
            city=city,
            district=district,
            year=2024,
            # TODO: Gercek veriler CIP API'den cekilecek
            # CIP sideMenu.json'daki egitim ve yas degiskenleri kullanilmali
        )

    # ================================================================
    # CIP Metadata
    # ================================================================

    async def get_available_variables(self) -> list[dict]:
        """
        CIP'te mevcut tum degisken listesini getir.

        CIP sideMenu.json dosyasi tum degisken kodlarini, isimlerini
        ve parametrelerini icerir.
        """
        # CIP'in degisken katalogu
        response = await self._get("/assets/sideMenu.json", params={"v": "2.000"})
        return response.json()

    # ================================================================
    # data.tuik.gov.tr Fallback (Web Portal)
    # ================================================================

    async def get_data_portal_categories(self) -> list[dict]:
        """
        data.tuik.gov.tr veri portalindan kategori listesi.

        NOT: Bu endpoint web sitesinin dahili API'sidir.
        Degisebilir ve resmi olarak desteklenmez.
        """
        logger.info("tuik_data_portal_categories")

        # data.tuik.gov.tr baska bir domain — yeni client gerekli
        # Bu metod mevcut client'in base_url'ini gecici degistiremez
        # TODO: data.tuik.gov.tr icin ayri bir client veya direct httpx call
        return []
