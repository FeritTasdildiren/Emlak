"""
Emlak Teknoloji Platformu - TCMB EVDS API Client

TCMB Elektronik Veri Dagitim Sistemi (EVDS) uzerinden:
- Konut fiyat endeksi (TP.HKFE serisi)
- Konut kredisi faiz oranlari
- Doviz kurlari (USD/TRY, EUR/TRY)

API Dokumantasyonu: https://evds2.tcmb.gov.tr/index.php?/evds/userDocs
API Key: Ucretsiz kayit — https://evds2.tcmb.gov.tr/ → Kayit Ol

ONEMLI NOTLAR:
- API key header ile gonderilir: headers={'key': api_key} (Nisan 2024 degisikligi)
- Tarih formati: DD-MM-YYYY
- TCMB hafta sonu/resmi tatillerde 404 donebilir → try/except ile atlanmali
- Frequency: 1=Gunluk, 2=Is Gunu, 3=Haftalik, 4=Ayda 2, 5=Aylik, 6=Ceyreklik, 7=6 Aylik, 8=Yillik
"""

from __future__ import annotations

from datetime import date, datetime

import structlog

from src.modules.data_pipeline.clients.base_client import BaseAPIClient
from src.modules.data_pipeline.schemas.api_responses import (
    ExchangeRateData,
    HousingPriceIndexData,
    MortgageRateData,
)

logger = structlog.get_logger("data_pipeline.tcmb")


class TCMBClient(BaseAPIClient):
    """
    TCMB EVDS (Elektronik Veri Dagitim Sistemi) API client.

    Kullanim:
        from src.config import settings

        async with TCMBClient(api_key=settings.TCMB_EVDS_API_KEY) as client:
            data = await client.get_housing_price_index("01-01-2024", "31-12-2024")
    """

    SOURCE_NAME = "tcmb_evds"

    # ---- EVDS Seri Kodlari ----
    # Konut Fiyat Endeksi
    SERIES_HPI_GENERAL = "TP.HKFE01"  # Turkiye geneli
    # TP.HKFE02 - TP.HKFE82: Il bazli endeksler (il plaka kodu + 1)
    # Ornek: Istanbul = TP.HKFE35 (34+1), Ankara = TP.HKFE07 (06+1)

    # Doviz Kurlari (YTL suffixli guncel seri kodlari)
    SERIES_USD_BUYING = "TP.DK.USD.A.YTL"
    SERIES_USD_SELLING = "TP.DK.USD.S.YTL"
    SERIES_EUR_BUYING = "TP.DK.EUR.A.YTL"
    SERIES_EUR_SELLING = "TP.DK.EUR.S.YTL"

    # Konut Kredisi Faiz Oranlari (Agirlikli Ortalama, Haftalik Akim)
    # TODO: Seri kodu dogrulanmali — EVDS portalinden kontrol et
    SERIES_MORTGAGE_RATE = "TP.TRY.K09"

    # ---- EVDS Frequency Kodlari ----
    FREQ_DAILY = 1
    FREQ_BUSINESS_DAY = 2
    FREQ_WEEKLY = 3
    FREQ_BIMONTHLY = 4
    FREQ_MONTHLY = 5
    FREQ_QUARTERLY = 6
    FREQ_SEMIANNUAL = 7
    FREQ_ANNUAL = 8

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://evds2.tcmb.gov.tr/service/evds",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            # Nisan 2024'ten itibaren API key header ile gonderiliyor
            headers={"key": api_key},
        )
        self._api_key = api_key

    async def get_series(
        self,
        series_code: str,
        start_date: str,
        end_date: str,
        frequency: int | None = None,
        aggregation_type: str = "avg",
    ) -> list[dict]:
        """
        Genel EVDS seri sorgusu.

        Args:
            series_code: EVDS seri kodu (orn: "TP.HKFE01")
            start_date: Baslangic tarihi (DD-MM-YYYY)
            end_date: Bitis tarihi (DD-MM-YYYY)
            frequency: Frekans kodu (1-8). None ise serinin dogal frekansi kullanilir.
            aggregation_type: Toplastirma tipi ("avg", "min", "max", "first", "last", "sum")

        Returns:
            EVDS API'den donen items listesi

        Raises:
            APIResponseError: API hata dondururse
            APITimeoutError: Zaman asimi
        """
        params: dict = {
            "series": series_code,
            "startDate": start_date,
            "endDate": end_date,
            "type": "json",
        }
        if frequency is not None:
            params["frequency"] = str(frequency)
            params["aggregationTypes"] = aggregation_type

        logger.info(
            "evds_series_query",
            series=series_code,
            start=start_date,
            end=end_date,
            frequency=frequency,
        )

        response = await self._get("/", params=params)
        data = response.json()

        items = data.get("items", [])
        logger.info("evds_series_result", series=series_code, item_count=len(items))
        return items

    async def get_housing_price_index(
        self,
        start_date: str,
        end_date: str,
        city_plate_code: int | None = None,
    ) -> list[HousingPriceIndexData]:
        """
        TCMB konut fiyat endeksi (TP.HKFE serisi).

        Args:
            start_date: Baslangic tarihi (DD-MM-YYYY)
            end_date: Bitis tarihi (DD-MM-YYYY)
            city_plate_code: Il plaka kodu (None ise Turkiye geneli).
                             Ornek: Istanbul=34, Ankara=6, Izmir=35

        Returns:
            HousingPriceIndexData listesi
        """
        if city_plate_code is not None:
            series_code = f"TP.HKFE{city_plate_code + 1:02d}"
            city_name = f"Plaka {city_plate_code}"
        else:
            series_code = self.SERIES_HPI_GENERAL
            city_name = None

        items = await self.get_series(
            series_code=series_code,
            start_date=start_date,
            end_date=end_date,
            frequency=self.FREQ_MONTHLY,
        )

        results: list[HousingPriceIndexData] = []
        for item in items:
            date_str = item.get("Tarih", "")
            value_key = series_code.replace(".", "_")
            raw_value = item.get(value_key) or item.get(series_code)

            if raw_value is None:
                continue

            try:
                parsed_date = self._parse_evds_date(date_str)
                index_value = float(str(raw_value).replace(",", "."))
            except (ValueError, TypeError):
                logger.warning(
                    "evds_parse_error",
                    series=series_code,
                    date=date_str,
                    value=raw_value,
                )
                continue

            results.append(
                HousingPriceIndexData(
                    date=parsed_date,
                    index_value=index_value,
                    series_code=series_code,
                    city=city_name,
                )
            )

        return results

    async def get_mortgage_rates(
        self,
        start_date: str,
        end_date: str,
    ) -> list[MortgageRateData]:
        """
        Konut kredisi faiz oranlari (agirlikli ortalama).

        Args:
            start_date: Baslangic tarihi (DD-MM-YYYY)
            end_date: Bitis tarihi (DD-MM-YYYY)

        Returns:
            MortgageRateData listesi
        """
        items = await self.get_series(
            series_code=self.SERIES_MORTGAGE_RATE,
            start_date=start_date,
            end_date=end_date,
            frequency=self.FREQ_WEEKLY,
        )

        results: list[MortgageRateData] = []
        for item in items:
            date_str = item.get("Tarih", "")
            value_key = self.SERIES_MORTGAGE_RATE.replace(".", "_")
            raw_value = item.get(value_key) or item.get(self.SERIES_MORTGAGE_RATE)

            if raw_value is None:
                continue

            try:
                parsed_date = self._parse_evds_date(date_str)
                rate = float(str(raw_value).replace(",", "."))
            except (ValueError, TypeError):
                logger.warning("evds_mortgage_parse_error", date=date_str, value=raw_value)
                continue

            results.append(
                MortgageRateData(
                    date=parsed_date,
                    rate_pct=rate,
                    bank_type="weighted_average",
                )
            )

        return results

    async def get_exchange_rates(self, target_date: str) -> ExchangeRateData:
        """
        USD/TRY ve EUR/TRY kurlari.

        Args:
            target_date: Kur tarihi (DD-MM-YYYY)

        Returns:
            ExchangeRateData

        Note:
            TCMB hafta sonu/tatilde 404 donebilir.
            Bu durumda onceki is gununu deneyin.
        """
        series = "-".join(
            [
                self.SERIES_USD_BUYING,
                self.SERIES_USD_SELLING,
                self.SERIES_EUR_BUYING,
                self.SERIES_EUR_SELLING,
            ]
        )

        items = await self.get_series(
            series_code=series,
            start_date=target_date,
            end_date=target_date,
        )

        if not items:
            logger.warning("evds_no_exchange_data", date=target_date)
            msg = f"TCMB doviz kuru verisi bulunamadi: {target_date}"
            raise ValueError(msg)

        item = items[0]
        parsed_date = self._parse_evds_date(item.get("Tarih", target_date))

        return ExchangeRateData(
            date=parsed_date,
            usd_try_buying=self._parse_float(item, self.SERIES_USD_BUYING),
            usd_try_selling=self._parse_float(item, self.SERIES_USD_SELLING),
            eur_try_buying=self._parse_float(item, self.SERIES_EUR_BUYING),
            eur_try_selling=self._parse_float(item, self.SERIES_EUR_SELLING),
        )

    # ---- EVDS Metadata Sorgulari ----

    async def get_categories(self) -> list[dict]:
        """EVDS veri kategorilerini listele."""
        response = await self._get("/categories/", params={"type": "json"})
        return response.json()

    async def get_data_groups(self, category_code: str) -> list[dict]:
        """Bir kategorideki veri gruplarini listele."""
        response = await self._get(
            "/datagroups/",
            params={"mode": "2", "code": category_code, "type": "json"},
        )
        return response.json()

    async def get_series_list(self, group_code: str) -> list[dict]:
        """Bir veri grubundaki serileri listele."""
        response = await self._get(
            "/serieList/",
            params={"type": "json", "code": group_code},
        )
        return response.json()

    # ---- Yardimci Metodlar ----

    @staticmethod
    def _parse_evds_date(date_str: str) -> date:
        """
        EVDS tarih formatini parse et.

        EVDS farkli formatlarda tarih donebilir:
        - "DD-MM-YYYY"
        - "DD.MM.YYYY"
        - "YYYY-MM-DD" (nadir)
        """
        date_str = date_str.strip()
        for fmt in ("%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        msg = f"EVDS tarih formati tanınmadı: {date_str}"
        raise ValueError(msg)

    @staticmethod
    def _parse_float(item: dict, key: str) -> float:
        """EVDS degerini float'a cevir. Nokta/virgul uyumsuzlugunu yonet."""
        # EVDS hem "TP.DK.USD.A" hem "TP_DK_USD_A" key kullanabiliyor
        value = item.get(key) or item.get(key.replace(".", "_"))
        if value is None:
            return 0.0
        return float(str(value).replace(",", "."))
