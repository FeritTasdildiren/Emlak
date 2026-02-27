"""
Emlak Teknoloji Platformu - Base API Client

Tum dis API client'larin turetildigi ortak async HTTP client.

Ozellikler:
- httpx.AsyncClient ile async HTTP islemleri
- Exponential backoff ile retry mekanizmasi
- Yapilandirabilir timeout ve max_retries
- structlog ile yapilandirilmis loglama
- Context manager (async with) destegi
- Ortak hata yonetimi (HTTP error, timeout, connection error)
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog

logger = structlog.get_logger("data_pipeline")


class APIClientError(Exception):
    """Dis API client hatalarinin temel sinifi."""

    def __init__(self, message: str, status_code: int | None = None, source: str = "unknown"):
        self.status_code = status_code
        self.source = source
        super().__init__(message)


class APIConnectionError(APIClientError):
    """Baglanti hatasi — sunucuya ulasilamiyor."""


class APITimeoutError(APIClientError):
    """Zaman asimi hatasi."""


class APIResponseError(APIClientError):
    """Sunucu HTTP hata kodu dondurdu (4xx/5xx)."""


class APIRateLimitError(APIClientError):
    """Rate limit asildi (429 Too Many Requests)."""


class BaseAPIClient:
    """
    Ortak async HTTP client base class.

    Kullanim:
        async with TUIKClient() as client:
            data = await client.get_housing_sales("istanbul", 2024, 1)

    Her alt sinif:
    - base_url, timeout, max_retries degerlerini override edebilir
    - _get / _post ile HTTP istekleri yapar
    - _handle_error ile HTTP hatalarini isler
    """

    # Alt siniflar override edebilir
    SOURCE_NAME: str = "base"

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        headers: dict[str, str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._default_headers = headers or {}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> BaseAPIClient:
        """Async context manager — client olustur."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={
                "User-Agent": "EmlakPlatformu/1.0",
                "Accept": "application/json",
                **self._default_headers,
            },
            follow_redirects=True,
        )
        logger.debug("api_client_opened", source=self.SOURCE_NAME, base_url=self.base_url)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager — client kapat."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("api_client_closed", source=self.SOURCE_NAME)

    @property
    def client(self) -> httpx.AsyncClient:
        """Aktif httpx client'i dondurur. Context manager disinda kullanilirsa hata verir."""
        if self._client is None:
            msg = (
                f"{self.__class__.__name__} context manager ile kullanilmalidir: "
                f"async with {self.__class__.__name__}() as client: ..."
            )
            raise RuntimeError(msg)
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        HTTP istegi yap — exponential backoff ile retry.

        Retry yapilacak durumlar:
        - httpx.ConnectError, httpx.ConnectTimeout
        - HTTP 429 (rate limit)
        - HTTP 500, 502, 503, 504 (sunucu hatalari)

        Retry YAPILMAYACAK durumlar:
        - HTTP 400, 401, 403, 404, 422 (client hatalari — tekrar denemek anlamsiz)
        """
        last_exception: Exception | None = None
        retryable_status_codes = {429, 500, 502, 503, 504}

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.request(
                    method,
                    path,
                    params=params,
                    data=data,
                    json=json_body,
                    headers=headers,
                )

                # Basarili veya retry gerektirmeyen hata
                if response.status_code not in retryable_status_codes:
                    self._handle_error(response)
                    return response

                # Retry gerektiren HTTP hata kodu
                if attempt < self.max_retries:
                    wait = self._backoff_delay(attempt, response)
                    logger.warning(
                        "api_request_retry",
                        source=self.SOURCE_NAME,
                        method=method,
                        path=path,
                        status_code=response.status_code,
                        attempt=attempt,
                        wait_seconds=wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                # Son deneme — hatali response'u isle
                self._handle_error(response)
                return response

            except httpx.TimeoutException as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    wait = self._backoff_delay(attempt)
                    logger.warning(
                        "api_timeout_retry",
                        source=self.SOURCE_NAME,
                        method=method,
                        path=path,
                        attempt=attempt,
                        wait_seconds=wait,
                    )
                    await asyncio.sleep(wait)
                    continue

            except httpx.ConnectError as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    wait = self._backoff_delay(attempt)
                    logger.warning(
                        "api_connection_retry",
                        source=self.SOURCE_NAME,
                        method=method,
                        path=path,
                        attempt=attempt,
                        wait_seconds=wait,
                        error=str(exc),
                    )
                    await asyncio.sleep(wait)
                    continue

        # Tum denemeler basarisiz
        if isinstance(last_exception, httpx.TimeoutException):
            logger.error(
                "api_timeout_exhausted",
                source=self.SOURCE_NAME,
                method=method,
                path=path,
                max_retries=self.max_retries,
            )
            raise APITimeoutError(
                f"{self.SOURCE_NAME}: {method} {path} — zaman asimi ({self.max_retries} deneme)",
                source=self.SOURCE_NAME,
            ) from last_exception

        logger.error(
            "api_connection_exhausted",
            source=self.SOURCE_NAME,
            method=method,
            path=path,
            max_retries=self.max_retries,
            error=str(last_exception),
        )
        raise APIConnectionError(
            f"{self.SOURCE_NAME}: {method} {path} — baglanti hatasi ({self.max_retries} deneme)",
            source=self.SOURCE_NAME,
        ) from last_exception

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET istegi — retry + timeout + hata yonetimi."""
        return await self._request("GET", path, params=params, headers=headers)

    async def _post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """POST istegi — retry + timeout + hata yonetimi."""
        return await self._request("POST", path, data=data, json_body=json_body, headers=headers)

    def _handle_error(self, response: httpx.Response) -> None:
        """
        HTTP hata kodlarini isler.

        4xx → APIResponseError (client hatasi)
        429 → APIRateLimitError
        5xx → APIResponseError (sunucu hatasi)
        """
        if response.is_success:
            return

        status = response.status_code
        try:
            body = response.text[:500]
        except Exception:
            body = "<okunamadi>"

        if status == 429:
            logger.warning(
                "api_rate_limited",
                source=self.SOURCE_NAME,
                status_code=status,
                url=str(response.url),
            )
            raise APIRateLimitError(
                f"{self.SOURCE_NAME}: Rate limit asildi (429)",
                status_code=status,
                source=self.SOURCE_NAME,
            )

        logger.error(
            "api_http_error",
            source=self.SOURCE_NAME,
            status_code=status,
            url=str(response.url),
            body_preview=body,
        )
        raise APIResponseError(
            f"{self.SOURCE_NAME}: HTTP {status} — {body}",
            status_code=status,
            source=self.SOURCE_NAME,
        )

    @staticmethod
    def _backoff_delay(attempt: int, response: httpx.Response | None = None) -> float:
        """
        Exponential backoff suresi hesapla.

        attempt=1 → 1s, attempt=2 → 2s, attempt=3 → 4s (max 30s)
        429 hatasi varsa Retry-After header'i kullanilir.
        """
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), 60.0)
                except ValueError:
                    pass

        return min(2 ** (attempt - 1), 30.0)
