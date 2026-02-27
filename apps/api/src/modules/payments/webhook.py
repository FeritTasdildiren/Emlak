"""
Emlak Teknoloji Platformu - iyzico Webhook Signature Verification

HMAC-SHA256 tabanli webhook imza dogrulamasi.

Guvenlik:
    - hmac.compare_digest() kullanilir (timing-attack korunmasi)
    - Raw body uzerinden imza hesaplanir (JSON parse oncesi)
    - Imza uyusmazligi 403 Forbidden dondurur
"""

from __future__ import annotations

import hashlib
import hmac

import structlog
from fastapi import Request
from starlette.responses import JSONResponse

logger = structlog.get_logger()


async def verify_webhook_signature(
    request: Request,
    secret: str,
) -> tuple[bool, bytes]:
    """
    iyzico webhook imzasini dogrular.

    Args:
        request: FastAPI/Starlette Request nesnesi.
        secret: IYZICO_WEBHOOK_SECRET (HMAC key).

    Returns:
        (is_valid, raw_body) tuple:
            - is_valid: Imza gecerli mi?
            - raw_body: Ham istek govdesi (JSON parse icin tekrar kullanilir).

    Algoritma:
        1. Request body'yi raw bytes olarak oku
        2. HMAC-SHA256(secret, raw_body) hesapla
        3. X-IYZ-Signature header ile hmac.compare_digest() karsilastir
    """
    raw_body: bytes = await request.body()

    # --- Header'dan imza al ---
    received_signature: str | None = request.headers.get("X-IYZ-Signature")
    if not received_signature:
        logger.warning(
            "webhook_signature_missing",
            path=request.url.path,
            remote=request.client.host if request.client else "unknown",
        )
        return False, raw_body

    # --- HMAC-SHA256 hesapla ---
    computed_signature: str = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # --- Timing-safe karsilastirma ---
    is_valid: bool = hmac.compare_digest(computed_signature, received_signature)

    if not is_valid:
        logger.warning(
            "webhook_signature_mismatch",
            path=request.url.path,
            remote=request.client.host if request.client else "unknown",
        )

    return is_valid, raw_body


def signature_error_response(request: Request) -> JSONResponse:
    """Imza dogrulama basarisiz oldugunda dondurulecek 403 yaniti."""
    return JSONResponse(
        status_code=403,
        content={
            "type": "about:blank",
            "title": "Forbidden",
            "status": 403,
            "detail": "Webhook imza dogrulamasi basarisiz.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )
