"""
Emlak Teknoloji Platformu - Rate Limiting Configuration

slowapi kütüphanesi kullanılarak API istek sınırlama (rate limiting) yapılandırması.
Redis backend veya in-memory storage destekler.
"""

from typing import Any

import structlog
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

logger = structlog.get_logger()


def get_user_identifier(request: Request) -> str:
    """
    Rate limit anahtarı oluşturur.
    Önce kullanıcı ID'sine (JWT'den gelirse), yoksa IP adresine bakar.
    """
    # TenantMiddleware veya Auth dependencies tarafından eklenmiş olabilir
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return str(user.id)

    # Fallback: IP adresi
    return get_remote_address(request)


# Limiter instance
# storage_uri: Redis URL (prod) veya None (dev/in-memory)
storage_uri = settings.REDIS_URL if settings.APP_ENV != "test" else None

limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=storage_uri,
    default_limits=["60/minute"],  # Genel limit
    enabled=True,
)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Any:
    """
    Rate limit aşıldığında dönecek hata yanıtı.
    429 Too Many Requests + Retry-After header.
    """
    from fastapi.responses import JSONResponse

    retry_after = getattr(exc, "retry_after", "60")

    logger.warning(
        "rate_limit_exceeded",
        path=request.url.path,
        client_ip=get_remote_address(request),
        retry_after=retry_after,
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "too_many_requests",
                "message": "Çok fazla istek gönderildi. Lütfen bir süre bekleyin.",
                "retry_after_seconds": retry_after,
            }
        },
        headers={"Retry-After": str(retry_after)},
    )
