"""
Emlak Teknoloji Platformu - Request ID Middleware

Her HTTP istegine benzersiz bir request_id atar.
- X-Request-ID header'dan alir (upstream proxy/gateway varsa)
- Yoksa uuid4 ile uretir
- structlog context'ine baglar (tum loglar request_id icerir)
- Response header'a X-Request-ID ekler
- OTel aktifse aktif span'e app.request_id attribute'u ekler
- Yakalanmamis exception'lar icin RFC 7807 fallback yaniti uretir
"""

from uuid import uuid4

import structlog
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

REQUEST_ID_HEADER = "X-Request-ID"

logger = structlog.get_logger("middleware.request_id")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    En dis middleware olarak calisir.

    Akis:
        1. Gelen request'ten X-Request-ID header'i oku
        2. Yoksa yeni uuid4 uret
        3. request.state.request_id'ye kaydet
        4. structlog contextvars'a bind et (tum loglar otomatik alir)
        5. Sonraki middleware / handler cagir
        6. Response header'a X-Request-ID ekle
        7. Cikista contextvars'i temizle (request izolasyonu)

    ONEMLI:
        En dis middleware oldugu icin yakalanmamis exception'lari da
        burada yakalayip RFC 7807 formatinda yanit uretir.
        Bu sayede HER yanit request_id icerir — hata debug'u icin kritik.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # --- 1. Request ID cozumle ---
        request_id: str = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())

        # --- 2. Request state'e kaydet ---
        request.state.request_id = request_id

        # --- 3. structlog context'ine bind et ---
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # --- 3b. OTel span'e request_id attribute'u ekle ---
        # OTel devre disiysa get_current_span() INVALID_SPAN dondurur,
        # set_attribute() sessizce atlanir — ekstra kontrol gerekmez.
        span = trace.get_current_span()
        span.set_attribute("app.request_id", request_id)

        try:
            # --- 4. Sonraki middleware / handler ---
            response: Response = await call_next(request)
        except Exception:
            # BaseHTTPMiddleware yakalanmamis exception'lari call_next'ten
            # re-raise eder. Burada yakalayip RFC 7807 fallback uretiyoruz.
            logger.exception(
                "unhandled_exception",
                method=request.method,
                path=request.url.path,
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "type": "about:blank",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "Beklenmeyen bir sunucu hatasi olustu.",
                    "instance": str(request.url),
                    "request_id": request_id,
                },
            )

        # --- 5. Response header'a ekle ---
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
