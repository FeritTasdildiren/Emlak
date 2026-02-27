"""
Emlak Teknoloji Platformu - OpenAI Service

OpenAI API wrapper: text generation, image analysis, image editing, image generation.
Singleton client, retry logic (exponential backoff), structured logging, no-op guard.

Kullanim:
    from src.services.openai_service import openai_service

    # Text generation
    text = await openai_service.generate_text("Bu mahalleyi analiz et.")

    # Image analysis (vision)
    result = await openai_service.analyze_image(image_bytes, "Gorseli degerlendir")

    # Image generation
    images = await openai_service.generate_image("Modern villa dis cephe gorseli")

    # Image editing
    edited = await openai_service.edit_image(image_bytes, "Bahceyi yesillestir")

No-op Guard:
    OPENAI_API_KEY bos ise mock response dondurur — test ve gelistirme ortaminda
    API cagrisi yapmadan calismaya devam edilebilir.

Mimari Kararlar:
    - Sync OpenAI client + asyncio.to_thread() (WeasyPrint pattern ile tutarli)
    - Lazy import: openai paketi sadece ilk kullanimda import edilir
    - Retry: Kendi retry mekanizmasi (outbox retry_policy'den bagimsiz)
    - Singleton: Modul-seviyesi _client, GIL korumasi altinda thread-safe

Referans: TASK-114 (S8.1)
"""

from __future__ import annotations

import asyncio
import base64
import json
import random
import time
from typing import TYPE_CHECKING

import structlog

from src.config import settings
from src.services.openai_config import (
    DEFAULT_IMAGE_COUNT,
    DEFAULT_IMAGE_QUALITY,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    IMAGE_MODEL,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    RETRY_MULTIPLIER,
    TEXT_MODEL,
)
from src.services.openai_exceptions import (
    OpenAIContentFilterError,
    OpenAIInvalidImageError,
    OpenAIRateLimitError,
    OpenAIServiceError,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from openai import OpenAI
    from openai.types.chat import ChatCompletion
    from openai.types.images_response import ImagesResponse

logger = structlog.get_logger(__name__)


# ---------- Mock Responses (No-op Guard) ----------

_MOCK_TEXT = "[MOCK] OpenAI API key yapilandirilmamis. Bu bir mock yanittir."
_MOCK_ANALYSIS: dict = {
    "mock": True,
    "description": "OpenAI API key yapilandirilmamis. Bu bir mock analiz sonucudur.",
    "objects": [],
    "labels": [],
}
# Minimal 1x1 seffaf PNG — test ortaminda gecerli gorsel verisi
_MOCK_IMAGE = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


# ---------- Client Singleton ----------

_client: OpenAI | None = None
_client_initialized: bool = False


def _get_client() -> OpenAI | None:
    """
    OpenAI client singleton.

    OPENAI_API_KEY bos ise None dondurur (no-op guard aktif).
    Thread-safe: GIL korumasi altinda calisir, cift kontrol ile lazy init.

    Returns:
        OpenAI client instance veya None (API key yoksa).
    """
    global _client, _client_initialized

    if _client_initialized:
        return _client

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        logger.warning(
            "openai_client_skipped",
            reason="OPENAI_API_KEY bos veya tanimlanmamis",
        )
        _client_initialized = True
        return None

    from openai import OpenAI as _OpenAI

    _client = _OpenAI(api_key=api_key)
    _client_initialized = True
    logger.info("openai_client_initialized")
    return _client


def reset_client() -> None:
    """
    Client singleton'i sifirlar — test ve hot-reload icin.

    Production'da kullanilmamali.
    """
    global _client, _client_initialized
    _client = None
    _client_initialized = False
    logger.debug("openai_client_reset")


# ---------- Retry Logic ----------


def _should_retry(exc: Exception, attempt: int) -> bool:
    """
    Exception retry edilebilir mi?

    Retry edilebilir:
        - Rate limit (429)
        - Server error (5xx)
        - Connection / timeout hatalari

    Retry edilmez:
        - Content filter (guvenlik reddi)
        - Invalid request (4xx, 429 haric)
        - Max retry asildi
    """
    if attempt >= MAX_RETRIES:
        return False

    # OpenAI SDK exception'lari — lazy import
    from openai import APIConnectionError, APITimeoutError, RateLimitError

    if isinstance(exc, (RateLimitError, APIConnectionError, APITimeoutError)):
        return True

    # Server error (5xx)
    from openai import APIStatusError

    return isinstance(exc, APIStatusError) and exc.status_code >= 500


def _calculate_delay(attempt: int) -> float:
    """
    Exponential backoff + jitter ile retry gecikmesi hesaplar.

    Formul: base_delay * (multiplier ^ attempt) ± %25 jitter
    Ust sinir: RETRY_MAX_DELAY
    """
    delay = RETRY_BASE_DELAY * (RETRY_MULTIPLIER ** attempt)
    delay = min(delay, RETRY_MAX_DELAY)

    # Jitter — thundering herd korunmasi
    jitter = delay * 0.25
    delay += random.uniform(-jitter, jitter)

    return max(delay, 0.5)


def _classify_and_raise_known(
    exc: Exception,
    operation_name: str,
    **log_context: Any,
) -> None:
    """
    Bilinen OpenAI hatalarini ozel exception siniflarina donusturur.

    Content filter ve gecersiz gorsel hatalari direkt firlatilir
    cunku retry ile cozulemezler.

    Raises:
        OpenAIContentFilterError: Icerik filtresi — prompt/gorsel reddedildi.
        OpenAIInvalidImageError: Gecersiz gorsel formati veya boyutu.
    """
    from openai import BadRequestError

    if not isinstance(exc, BadRequestError):
        return

    error_message = str(exc).lower()

    # Content filter — guvenlik reddi
    if "content_policy" in error_message or "safety" in error_message:
        logger.warning(
            "openai_content_filtered",
            operation=operation_name,
            error=str(exc),
            **log_context,
        )
        raise OpenAIContentFilterError(cause=exc) from exc

    # Invalid image — format/boyut hatasi
    if "image" in error_message and (
        "invalid" in error_message
        or "format" in error_message
        or "size" in error_message
    ):
        logger.warning(
            "openai_invalid_image",
            operation=operation_name,
            error=str(exc),
            **log_context,
        )
        raise OpenAIInvalidImageError(cause=exc) from exc


def _retry_operation(
    operation: Callable[[], Any],
    *,
    operation_name: str,
    **log_context: Any,
) -> Any:
    """
    OpenAI API operasyonunu exponential backoff ile retry eder.

    Args:
        operation: Parametresiz callable (closure olarak context tasir).
        operation_name: Log event'lerinde kullanilacak ad.
        **log_context: Ek structlog konteksti.

    Returns:
        Operasyon sonucu (tip operation'a bagli).

    Raises:
        OpenAIServiceError: Tum retry'lar basarisiz oldugunda.
        OpenAIRateLimitError: Rate limit retry sonrasi da basarisizsa.
        OpenAIContentFilterError: Icerik filtrelendi (retry yapilmaz).
        OpenAIInvalidImageError: Gecersiz gorsel (retry yapilmaz).
    """
    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                logger.info(
                    "openai_retry_attempt",
                    operation=operation_name,
                    attempt=attempt,
                    max_retries=MAX_RETRIES,
                    **log_context,
                )

            result = operation()

            if attempt > 0:
                logger.info(
                    "openai_retry_success",
                    operation=operation_name,
                    succeeded_at_attempt=attempt,
                    **log_context,
                )

            return result

        except (OpenAIContentFilterError, OpenAIInvalidImageError):
            # Bu hatalar retry ile cozulemez — direkt firlatilir
            raise

        except Exception as exc:
            last_exception = exc

            # Bilinen hatalari ozel exception'lara donustur
            _classify_and_raise_known(exc, operation_name, **log_context)

            if not _should_retry(exc, attempt):
                break

            delay = _calculate_delay(attempt)
            logger.warning(
                "openai_retry_scheduled",
                operation=operation_name,
                attempt=attempt,
                delay_seconds=round(delay, 2),
                error=str(exc),
                error_type=type(exc).__name__,
                **log_context,
            )
            time.sleep(delay)

    # Tum denemeler basarisiz
    error_type = type(last_exception).__name__ if last_exception else "Unknown"
    logger.error(
        "openai_operation_failed",
        operation=operation_name,
        total_attempts=MAX_RETRIES + 1,
        error=str(last_exception),
        error_type=error_type,
        **log_context,
    )

    # Rate limit ozel exception
    from openai import RateLimitError

    if isinstance(last_exception, RateLimitError):
        raise OpenAIRateLimitError(cause=last_exception) from last_exception

    raise OpenAIServiceError(
        f"OpenAI {operation_name} basarisiz oldu ({error_type}): {last_exception}",
        cause=last_exception,
    ) from last_exception


# ============================================================
#  Core Operations (Sync)
# ============================================================


def generate_text(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str = TEXT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    """
    OpenAI Chat Completion ile metin uretir.

    Args:
        prompt: Kullanici prompt'u.
        system_prompt: Sistem talimati (opsiyonel, orn. "Sen bir emlak uzmanisin").
        model: Kullanilacak model (varsayilan: gpt-5-mini).
        max_tokens: Maksimum uretilecek token sayisi.
        temperature: Yaraticilik parametresi (0.0 = deterministik, 2.0 = cok yaratici).

    Returns:
        Uretilen metin (stripped).

    Raises:
        OpenAIServiceError: API hatasi (retry sonrasi).
        OpenAIContentFilterError: Icerik filtrelendi.
    """
    client = _get_client()
    if client is None:
        logger.info("openai_mock_text", prompt_length=len(prompt))
        return _MOCK_TEXT

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    def _call() -> str:
        response: ChatCompletion = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    result: str = _retry_operation(
        _call,
        operation_name="generate_text",
        model=model,
        prompt_length=len(prompt),
    )

    logger.info(
        "openai_text_generated",
        model=model,
        prompt_length=len(prompt),
        response_length=len(result),
    )
    return result


def analyze_image(
    image_bytes: bytes,
    prompt: str,
    *,
    model: str = TEXT_MODEL,
    detail: str = "high",
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """
    Gorseli OpenAI Vision ile analiz eder.

    Gorsel base64 encode edilip Chat Completion'a gonderilir.
    Yanit JSON olarak parse edilir; parse basarisizsa raw_response dondurulur.

    Args:
        image_bytes: Gorsel verisi (JPEG, PNG, WebP, GIF).
        prompt: Analiz talimati (orn. "Bu evin durumunu degerlendir").
        model: Vision destekli model (varsayilan: gpt-5-mini).
        detail: Gorsel analiz detay seviyesi ('low', 'high', 'auto').
        max_tokens: Maksimum token sayisi.

    Returns:
        JSON parse edilmis analiz sonucu.
        Parse basarisizsa: {"raw_response": "..."} formatinda ham yanit.

    Raises:
        OpenAIServiceError: API hatasi.
        OpenAIInvalidImageError: Gecersiz gorsel formati veya boyutu.
        OpenAIContentFilterError: Icerik filtrelendi.
    """
    client = _get_client()
    if client is None:
        logger.info("openai_mock_analysis", image_size_bytes=len(image_bytes))
        return _MOCK_ANALYSIS.copy()

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    messages: list[dict] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_image}",
                        "detail": detail,
                    },
                },
            ],
        }
    ]

    def _call() -> dict:
        response: ChatCompletion = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content or "{}"
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError as parse_exc:
            logger.warning(
                "openai_json_parse_failed",
                raw_content=raw_content[:500],
                error=str(parse_exc),
            )
            return {"raw_response": raw_content}

    result: dict = _retry_operation(
        _call,
        operation_name="analyze_image",
        model=model,
        image_size_bytes=len(image_bytes),
        detail=detail,
    )

    logger.info(
        "openai_image_analyzed",
        model=model,
        image_size_bytes=len(image_bytes),
        detail=detail,
        result_keys=list(result.keys()),
    )
    return result


def generate_image(
    prompt: str,
    *,
    model: str = IMAGE_MODEL,
    size: str = DEFAULT_IMAGE_SIZE,
    quality: str = DEFAULT_IMAGE_QUALITY,
    n: int = DEFAULT_IMAGE_COUNT,
) -> list[bytes]:
    """
    OpenAI ile gorsel uretir.

    Args:
        prompt: Gorsel aciklamasi (orn. "Modern minimalist villa dis cephe gorseli").
        model: Kullanilacak model (varsayilan: gpt-image-1.5).
        size: Gorsel boyutu ('1024x1024', '1536x1024', '1024x1536').
        quality: Kalite seviyesi ('low', 'medium', 'high').
        n: Uretilecek gorsel sayisi (1-4).

    Returns:
        PNG formatinda gorsel byte listesi.

    Raises:
        OpenAIServiceError: API hatasi.
        OpenAIContentFilterError: Icerik filtrelendi.
    """
    client = _get_client()
    if client is None:
        logger.info("openai_mock_image_generation", n=n)
        return [_MOCK_IMAGE] * n

    def _call() -> list[bytes]:
        response: ImagesResponse = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,  # type: ignore[arg-type]
            quality=quality,  # type: ignore[arg-type]
            n=n,
            response_format="b64_json",
        )
        return _extract_images(response)

    result: list[bytes] = _retry_operation(
        _call,
        operation_name="generate_image",
        model=model,
        size=size,
        quality=quality,
        n=n,
        prompt_length=len(prompt),
    )

    logger.info(
        "openai_image_generated",
        model=model,
        size=size,
        quality=quality,
        count=len(result),
        total_bytes=sum(len(img) for img in result),
    )
    return result


def edit_image(
    image_bytes: bytes,
    prompt: str,
    *,
    model: str = IMAGE_MODEL,
    size: str = DEFAULT_IMAGE_SIZE,
    quality: str = DEFAULT_IMAGE_QUALITY,
    n: int = DEFAULT_IMAGE_COUNT,
    mask_bytes: bytes | None = None,
) -> list[bytes]:
    """
    Mevcut gorseli OpenAI ile duzenler.

    Args:
        image_bytes: Duzenlenmek istenen gorsel (PNG formati onerilen).
        prompt: Duzenleme talimatlari (orn. "Bahceye havuz ekle").
        model: Kullanilacak model (varsayilan: gpt-image-1.5).
        size: Cikti gorsel boyutu.
        quality: Kalite seviyesi.
        n: Uretilecek varyasyon sayisi (1-4).
        mask_bytes: Maskeleme gorseli (opsiyonel, PNG — seffaf alan duzenlenir).

    Returns:
        PNG formatinda duzenlenmis gorsel byte listesi.

    Raises:
        OpenAIServiceError: API hatasi.
        OpenAIInvalidImageError: Gecersiz gorsel formati veya boyutu.
        OpenAIContentFilterError: Icerik filtrelendi.
    """
    client = _get_client()
    if client is None:
        logger.info("openai_mock_image_edit", image_size_bytes=len(image_bytes))
        return [_MOCK_IMAGE] * n

    def _call() -> list[bytes]:
        kwargs: dict = {
            "model": model,
            "image": image_bytes,
            "prompt": prompt,
            "size": size,
            "quality": quality,  # type: ignore[dict-item]
            "n": n,
            "response_format": "b64_json",
        }
        if mask_bytes is not None:
            kwargs["mask"] = mask_bytes

        response: ImagesResponse = client.images.edit(**kwargs)  # type: ignore[arg-type]
        return _extract_images(response)

    result: list[bytes] = _retry_operation(
        _call,
        operation_name="edit_image",
        model=model,
        image_size_bytes=len(image_bytes),
        has_mask=mask_bytes is not None,
        size=size,
        quality=quality,
        n=n,
    )

    logger.info(
        "openai_image_edited",
        model=model,
        size=size,
        quality=quality,
        count=len(result),
        total_bytes=sum(len(img) for img in result),
    )
    return result


# ---------- Image Response Extraction ----------


def _extract_images(response: ImagesResponse) -> list[bytes]:
    """
    ImagesResponse'dan gorsel byte'larini cikarir.

    Oncelik: b64_json > url. URL fallback'i log'lanir.
    """
    images: list[bytes] = []
    for img_data in response.data:
        if img_data.b64_json:
            images.append(base64.b64decode(img_data.b64_json))
        elif img_data.url:
            logger.warning("openai_image_url_fallback", url=img_data.url[:100])
            images.append(b"")
    return images


# ============================================================
#  Async Wrappers (asyncio.to_thread)
# ============================================================


async def generate_text_async(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str = TEXT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    """generate_text() async wrapper — asyncio.to_thread() ile calisir."""
    return await asyncio.to_thread(
        generate_text,
        prompt,
        system_prompt=system_prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )


async def analyze_image_async(
    image_bytes: bytes,
    prompt: str,
    *,
    model: str = TEXT_MODEL,
    detail: str = "high",
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """analyze_image() async wrapper — asyncio.to_thread() ile calisir."""
    return await asyncio.to_thread(
        analyze_image,
        image_bytes,
        prompt,
        model=model,
        detail=detail,
        max_tokens=max_tokens,
    )


async def generate_image_async(
    prompt: str,
    *,
    model: str = IMAGE_MODEL,
    size: str = DEFAULT_IMAGE_SIZE,
    quality: str = DEFAULT_IMAGE_QUALITY,
    n: int = DEFAULT_IMAGE_COUNT,
) -> list[bytes]:
    """generate_image() async wrapper — asyncio.to_thread() ile calisir."""
    return await asyncio.to_thread(
        generate_image,
        prompt,
        model=model,
        size=size,
        quality=quality,
        n=n,
    )


async def edit_image_async(
    image_bytes: bytes,
    prompt: str,
    *,
    model: str = IMAGE_MODEL,
    size: str = DEFAULT_IMAGE_SIZE,
    quality: str = DEFAULT_IMAGE_QUALITY,
    n: int = DEFAULT_IMAGE_COUNT,
    mask_bytes: bytes | None = None,
) -> list[bytes]:
    """edit_image() async wrapper — asyncio.to_thread() ile calisir."""
    return await asyncio.to_thread(
        edit_image,
        image_bytes,
        prompt,
        model=model,
        size=size,
        quality=quality,
        n=n,
        mask_bytes=mask_bytes,
    )


# ============================================================
#  Service Facade (Dependency Injection)
# ============================================================


class OpenAIService:
    """
    OpenAI servis facade'i — tum operasyonlari tek bir sinif uzerinden saglar.

    Modul-seviyesi fonksiyonlar dogrudan da kullanilabilir.
    Bu sinif dependency injection ve test mock'lamasi icin sunulur.

    Kullanim:
        service = OpenAIService()
        text = await service.generate_text("Merhaba")

        # veya modul-seviyesi singleton:
        from src.services.openai_service import openai_service
        text = await openai_service.generate_text("Merhaba")
    """

    @staticmethod
    async def generate_text(
        prompt: str,
        *,
        system_prompt: str | None = None,
        model: str = TEXT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        """Metin uretir. Detaylar icin generate_text() docstring'ine bakin."""
        return await generate_text_async(
            prompt,
            system_prompt=system_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    @staticmethod
    async def analyze_image(
        image_bytes: bytes,
        prompt: str,
        *,
        model: str = TEXT_MODEL,
        detail: str = "high",
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> dict:
        """Gorsel analiz eder. Detaylar icin analyze_image() docstring'ine bakin."""
        return await analyze_image_async(
            image_bytes,
            prompt,
            model=model,
            detail=detail,
            max_tokens=max_tokens,
        )

    @staticmethod
    async def generate_image(
        prompt: str,
        *,
        model: str = IMAGE_MODEL,
        size: str = DEFAULT_IMAGE_SIZE,
        quality: str = DEFAULT_IMAGE_QUALITY,
        n: int = DEFAULT_IMAGE_COUNT,
    ) -> list[bytes]:
        """Gorsel uretir. Detaylar icin generate_image() docstring'ine bakin."""
        return await generate_image_async(
            prompt,
            model=model,
            size=size,
            quality=quality,
            n=n,
        )

    @staticmethod
    async def edit_image(
        image_bytes: bytes,
        prompt: str,
        *,
        model: str = IMAGE_MODEL,
        size: str = DEFAULT_IMAGE_SIZE,
        quality: str = DEFAULT_IMAGE_QUALITY,
        n: int = DEFAULT_IMAGE_COUNT,
        mask_bytes: bytes | None = None,
    ) -> list[bytes]:
        """Gorsel duzenler. Detaylar icin edit_image() docstring'ine bakin."""
        return await edit_image_async(
            image_bytes,
            prompt,
            model=model,
            size=size,
            quality=quality,
            n=n,
            mask_bytes=mask_bytes,
        )

    @staticmethod
    def is_available() -> bool:
        """OpenAI API key tanimli mi? True ise gercek API cagrisi yapilir."""
        return bool(settings.OPENAI_API_KEY)


# Modul-seviyesi singleton — import sonrasi hemen kullanilabilir
openai_service = OpenAIService()
