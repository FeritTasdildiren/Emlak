"""
Emlak Teknoloji Platformu - OpenAI Service Exceptions

OpenAI API etkilesimlerinde olusabilecek hata siniflari.
Tum hatalar OpenAIServiceError temel sinifindan turetilir.

Kullanim:
    from src.services.openai_exceptions import OpenAIServiceError, OpenAIRateLimitError

    try:
        result = openai_service.generate_text("...")
    except OpenAIRateLimitError as exc:
        logger.warning("rate_limited", retry_after=exc.retry_after)
    except OpenAIServiceError as exc:
        logger.error("openai_error", cause=str(exc.cause))

Referans: TASK-114 (S8.1)
"""

from __future__ import annotations


class OpenAIServiceError(Exception):
    """
    OpenAI servis katmani temel hata sinifi.

    Tum OpenAI iliskili hatalar bu siniftan turetilir.
    Orijinal exception `cause` attribute'unda saklanir.
    """

    def __init__(
        self,
        message: str = "OpenAI servisi hatasi.",
        *,
        cause: Exception | None = None,
    ):
        self.cause = cause
        super().__init__(message)


class OpenAIRateLimitError(OpenAIServiceError):
    """
    OpenAI API rate limit asimi (HTTP 429).

    Attributes:
        retry_after: API'nin onerdigi bekleme suresi (saniye).
            None ise API header'da belirtilmemis demektir.
    """

    def __init__(
        self,
        message: str = "OpenAI API rate limiti asildi. Lutfen daha sonra tekrar deneyin.",
        *,
        retry_after: float | None = None,
        cause: Exception | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, cause=cause)


class OpenAIContentFilterError(OpenAIServiceError):
    """
    OpenAI icerik filtresi tarafindan reddedildi.

    Prompt veya gorsel icerik, OpenAI guvenlik politikasina aykiri bulundu.
    Bu hata retry ile cozulemez — icerik degistirilmelidir.
    """

    def __init__(
        self,
        message: str = "Icerik OpenAI guvenlik filtresi tarafindan reddedildi.",
        *,
        cause: Exception | None = None,
    ):
        super().__init__(message, cause=cause)


class OpenAIInvalidImageError(OpenAIServiceError):
    """
    Gecersiz gorsel formati veya boyutu.

    Desteklenen formatlar: JPEG, PNG, WebP, GIF.
    Maksimum boyut: 20 MB (model'e gore degisir).
    """

    def __init__(
        self,
        message: str = "Gecersiz gorsel: format veya boyut desteklenmiyor.",
        *,
        cause: Exception | None = None,
    ):
        super().__init__(message, cause=cause)
