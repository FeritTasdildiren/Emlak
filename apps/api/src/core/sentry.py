"""
Emlak Teknoloji Platformu - Sentry Integration

Hata izleme ve performans monitoring.
SENTRY_DSN tanimlanmissa aktif, degilse sessizce atlanir (graceful no-op).
"""

import structlog

from src.config import settings

logger = structlog.get_logger(__name__)


def init_sentry() -> None:
    """
    Sentry SDK'yi baslatir.

    - SENTRY_DSN bos ise hicbir sey yapmaz (development ortami icin guvenli).
    - traces_sample_rate=0.1 → %10 istek performance trace'e dahil edilir.
    - environment ayri ayri production/staging/development olarak isaretlenir.
    """
    if not settings.SENTRY_DSN:
        logger.info("sentry_disabled", reason="SENTRY_DSN not configured")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,
            environment=settings.APP_ENV,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,  # KVKK uyumlulugu — kisisel veri gonderme
        )
        logger.info(
            "sentry_initialized",
            environment=settings.APP_ENV,
            traces_sample_rate=0.1,
        )
    except ImportError:
        logger.warning("sentry_import_error", detail="sentry-sdk yuklu degil, atlanıyor")
