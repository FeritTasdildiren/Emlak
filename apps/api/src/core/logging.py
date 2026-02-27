"""
Emlak Teknoloji Platformu - Structured Logging

structlog tabanli yapilandirilmis loglama.
- Development: renkli ConsoleRenderer
- Production: makine-okunabilir JSONRenderer
- contextvars ile request_id otomatik her log satirinda yer alir.
- stdlib logging backend ile filter_by_level uyumlu.
"""

import logging
import logging.config
import time
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.config import settings

# Path'ler loglama disinda tutulabilir (health-check gibi gurultulu endpoint'ler)
_SILENT_PATHS: frozenset[str] = frozenset({"/health"})


def configure_logging() -> None:
    """
    structlog'u uygulamanin basinda bir kez cagrilir.

    stdlib logging'i backend olarak kullanir:
    - filter_by_level: stdlib logger'in seviyesine gore filtreler
    - Development: DEBUG seviye + ConsoleRenderer
    - Production: INFO seviye + JSONRenderer

    Processor zinciri:
        1. merge_contextvars    - request_id gibi context degerlerini birlestir
        2. filter_by_level      - stdlib log seviye filtrelemesi
        3. add_logger_name      - logger adi ekle
        4. add_log_level        - log seviyesi ekle
        5. PositionalArgumentsFormatter - pozisyonel argumanlari formatla
        6. TimeStamper(iso)     - ISO 8601 zaman damgasi
        7. StackInfoRenderer    - stack trace bilgisi
        8. format_exc_info      - exception bilgisi formatla
        9. Renderer             - dev: Console, prod: JSON
    """
    # --- stdlib logging backend ayarlari ---
    log_level = logging.DEBUG if settings.APP_DEBUG else logging.INFO

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                },
            },
            "root": {
                "handlers": ["default"],
                "level": log_level,
            },
            # uvicorn / sqlalchemy gibi gurultulu logger'lari biraz sustur
            "loggers": {
                "uvicorn": {"level": "INFO"},
                "sqlalchemy.engine": {
                    "level": "WARNING" if not settings.APP_DEBUG else "INFO",
                },
            },
        }
    )

    # --- structlog processor zinciri ---
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.APP_DEBUG:
        # Development — renkli, okunabilir cikti
        renderer: Any = structlog.dev.ConsoleRenderer()
    else:
        # Production — JSON cikti (ELK / Datadog / Loki uyumlu)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Her HTTP istegini loglar.

    Log satirlari:
        request_started  — method, path, request_id
        request_finished — method, path, status_code, duration_ms, request_id

    NOT: request_id structlog contextvars'tan otomatik gelir;
         RequestIdMiddleware bundan ONCE calistirilmalidir.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path: str = request.url.path

        # Gurultulu endpoint'leri loglamaya gerek yok
        if path in _SILENT_PATHS:
            return await call_next(request)

        logger = structlog.get_logger("http")
        method: str = request.method

        logger.info("request_started", method=method, path=path)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "request_finished",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response
