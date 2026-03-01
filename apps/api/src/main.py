"""
Emlak Teknoloji Platformu - FastAPI Application

Ana uygulama giris noktasi.

Middleware sirasi (en distan en ice):
    1. RequestIdMiddleware       → her istege request_id atar
    2. RequestLoggingMiddleware  → HTTP istek/yanit loglar
    3. TenantMiddleware          → JWT'den office_id + role alir, SET LOCAL ile RLS aktif eder
    4. CORSMiddleware            → CORS baslik yonetimi
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from src.config import settings
from src.core.exceptions import AppException, app_exception_handler
from src.core.logging import RequestLoggingMiddleware, configure_logging
from src.core.rate_limit import limiter, rate_limit_exceeded_handler
from src.core.sentry import init_sentry
from src.core.telemetry import init_telemetry
from src.database import async_session_factory
from src.listings.credit_router import router as credit_router
from src.listings.listing_assistant_router import router as listing_assistant_router
from src.listings.photo_router import router as photo_router
from src.listings.portal_export_router import router as portal_export_router
from src.listings.staging_router import router as staging_router
from src.middleware.request_id import RequestIdMiddleware
from src.middleware.tenant import TenantMiddleware
from src.modules.admin.bank_rates_router import router as admin_bank_rates_router
from src.modules.admin.dlq_router import router as admin_dlq_router
from src.modules.admin.outbox_monitor_router import router as admin_outbox_router
from src.modules.admin.refresh_alerts import router as admin_refresh_router
from src.modules.areas.router import router as areas_router
from src.modules.audit.audit_router import router as audit_router
from src.modules.auth.router import router as auth_router
from src.modules.calculator.calculator_router import router as calculator_router
from src.modules.customers.router import router as customers_router
from src.modules.earthquake.router import router as earthquake_router
from src.modules.maps.router import router as maps_router
from src.modules.matches.router import router as matches_router
from src.modules.messaging.adapters.telegram import TelegramAdapter
from src.modules.messaging.adapters.telegram_router import router as telegram_router
from src.modules.messaging.bot import (
    TelegramAuthBridge,
    TelegramBotHandler,
    telegram_link_router,
)
from src.modules.messaging.registry import ChannelRegistry
from src.modules.notifications.router import router as notifications_router
from src.modules.payments.router import router as payments_router
from src.modules.payments.transaction_router import router as transactions_router
from src.modules.properties.router import router as properties_router
from src.modules.properties.search_router import router as search_router
from src.modules.realtime.router import manager as ws_manager
from src.modules.realtime.router import router as ws_router
from src.modules.showcases.router import router as showcases_router
from src.modules.valuations.drift_router import router as drift_router
from src.modules.valuations.pdf_router import router as pdf_router
from src.modules.valuations.router import router as valuations_router
from src.services.dlq_service import DLQService
from src.services.outbox_monitor import OutboxMonitor

# --- Structured Logging yapilandirmasi (import-time, Sentry'den once) ---
configure_logging()

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    # --- Sentry baslatma ---
    init_sentry()

    # --- OpenTelemetry baslatma ---
    # OTEL_EXPORTER_OTLP_ENDPOINT bos ise sessizce atlanir (dev ortami)
    init_telemetry(app)

    # --- Messaging: ChannelRegistry + Telegram Adapter ---
    channel_registry = ChannelRegistry()
    app.state.channel_registry = channel_registry

    telegram_adapter: TelegramAdapter | None = None
    if settings.TELEGRAM_BOT_TOKEN:
        telegram_adapter = TelegramAdapter(bot_token=settings.TELEGRAM_BOT_TOKEN)
        channel_registry.register("telegram", telegram_adapter)

        # Webhook URL ayarlanmissa Telegram'a bildir
        if settings.TELEGRAM_WEBHOOK_URL:
            try:
                await telegram_adapter.set_webhook(url=settings.TELEGRAM_WEBHOOK_URL)
                logger.info(
                    "telegram_webhook_set",
                    webhook_url=settings.TELEGRAM_WEBHOOK_URL,
                )
            except Exception as exc:
                logger.error(
                    "telegram_webhook_set_failed",
                    error=str(exc),
                    exc_info=True,
                )
    else:
        logger.warning(
            "telegram_adapter_skipped",
            detail="TELEGRAM_BOT_TOKEN bos — Telegram adaptoru devre disi",
        )

    app.state.telegram_adapter = telegram_adapter

    # --- Redis client baslatma (cache DB 0) ---
    import redis.asyncio as aioredis

    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    app.state.redis_client = redis_client
    logger.info("redis_client_initialized", redis_url=settings.REDIS_URL)

    # --- Telegram Bot: AuthBridge + BotHandler ---
    telegram_auth_bridge = TelegramAuthBridge(
        redis_client=redis_client,
        db_session_factory=async_session_factory,
    )
    app.state.telegram_auth_bridge = telegram_auth_bridge

    telegram_bot_handler: TelegramBotHandler | None = None
    if telegram_adapter is not None:
        telegram_bot_handler = TelegramBotHandler(
            telegram_adapter=telegram_adapter,
            auth_bridge=telegram_auth_bridge,
            session_factory=async_session_factory,
            redis_client=redis_client,
        )
    else:
        logger.warning(
            "telegram_bot_handler_skipped",
            detail="TelegramAdapter mevcut degil — bot handler devre disi",
        )

    app.state.telegram_bot_handler = telegram_bot_handler

    # --- Outbox Monitor baslatma ---
    outbox_monitor = OutboxMonitor(async_session_factory)
    app.state.outbox_monitor = outbox_monitor
    logger.info("outbox_monitor_initialized")

    # --- DLQ Service baslatma ---
    dlq_service = DLQService(async_session_factory)
    app.state.dlq_service = dlq_service
    logger.info("dlq_service_initialized")

    # --- WebSocket Manager baslatma (stub — varsayilan aktif, env ile kontrol edilir) ---
    app.state.ws_manager = ws_manager
    logger.info(
        "ws_manager_initialized",
        detail="WebSocket stub altyapisi hazir (echo + heartbeat)",
    )

    logger.info(
        "application_startup",
        env=settings.APP_ENV,
        debug=settings.APP_DEBUG,
        registered_channels=channel_registry.list_channels(),
    )
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection
    yield
    # Shutdown

    # --- Telegram Adapter cleanup ---
    if telegram_adapter is not None:
        await telegram_adapter.close()

    # --- Redis client cleanup ---
    await redis_client.aclose()
    logger.info("redis_client_closed")

    logger.info("application_shutdown")
    # TODO: Close database connection pool


app = FastAPI(
    title="Emlak Teknoloji Platformu API",
    description="Turkiye emlak pazari icin yapay zeka destekli platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.state.limiter = limiter

# ---------- Exception Handlers ----------
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

# AppException → RFC 7807 JSON yaniti (request_id dahil)
app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
# Yakalanmamis Exception'lar RequestIdMiddleware'de RFC 7807 fallback ile handle edilir

# ---------- Middleware (en distan en ice eklenir — son eklenen en disarida calisir) ----------

# 4. CORS — framework level (en icteki middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. TenantMiddleware — RLS policy'ler hazir, tenant isolation aktif
# JWT'den office_id + user_role alinir, SET LOCAL ile PostgreSQL session'a yazilir.
# Public endpoint'ler (health, auth, docs) bypass edilir.
app.add_middleware(TenantMiddleware)

# 2. RequestLoggingMiddleware — request_id context'te, loglama yapabilir
app.add_middleware(RequestLoggingMiddleware)

# 1. RequestIdMiddleware — en dis, her seyden once request_id ata
app.add_middleware(RequestIdMiddleware)


# ---------- Routers ----------
app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(payments_router)
app.include_router(transactions_router)
app.include_router(valuations_router)
app.include_router(areas_router)
app.include_router(earthquake_router)
app.include_router(maps_router)
app.include_router(pdf_router)
app.include_router(telegram_router)
app.include_router(telegram_link_router)

# --- Admin Routers (JWT GEREKTiRiR — PUBLIC_PATHS'e EKLENMEZ) ---
app.include_router(admin_outbox_router)
app.include_router(admin_dlq_router)
app.include_router(admin_refresh_router)
app.include_router(admin_bank_rates_router)
app.include_router(drift_router)

# --- Audit Router (JWT + platform_admin GEREKTiRiR — KVKK denetim kayitlari) ---
app.include_router(audit_router)

# --- CRM Routers (JWT GEREKTiRiR) ---
app.include_router(customers_router)
app.include_router(matches_router)

# --- Calculator Router (JWT GEREKTiRiR — tenant bagimsiz) ---
app.include_router(calculator_router)

# --- Properties & Search Routers (JWT GEREKTiRiR) ---
app.include_router(properties_router)
app.include_router(search_router)

# --- Showcases Router (CRUD: JWT GEREKTiRiR, Public: JWT gereksiz) ---
app.include_router(showcases_router)

# --- WebSocket Router (JWT query param ile dogrulanir) ---
app.include_router(ws_router)

# --- Listings Routers (JWT GEREKTiRiR) ---
app.include_router(photo_router)
app.include_router(credit_router)
app.include_router(staging_router)
app.include_router(listing_assistant_router)
app.include_router(portal_export_router)


# ---------- Health Check ----------


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """
    Liveness probe — uygulama ayakta mi?

    Kubernetes/Docker liveness probe icin kullanilir.
    Hicbir dis bagimliligi kontrol etmez; sadece process'in HTTP yanit
    verebildigini dogrular.
    """
    return {
        "status": "healthy",
        "env": settings.APP_ENV,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/health/db", tags=["system"])
async def health_db() -> JSONResponse:
    """
    Database baglanti kontrolu — SELECT 1 ile basit ping.

    503 donerse DB erisimi yok demektir. Docker healthcheck ve
    monitoring alert'leri bu endpoint'i kullanir.
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", "database": "connected"},
        )
    except Exception as e:
        logger.error("health_db_failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )


@app.get("/health/pdf", tags=["system"])
async def health_pdf() -> JSONResponse:
    """
    WeasyPrint PDF uretim kontrolu.

    WeasyPrint'in calistigini ve Turkce karakter destegini dogrular.
    Basarisizsa 503 doner.
    """
    test_html = """
    <html>
    <head><meta charset="utf-8"></head>
    <body>
        <h1>PDF Sağlık Kontrolü</h1>
        <p>Türkçe karakterler: İ, ı, Ş, ş, Ğ, ğ, Ü, ü, Ö, ö, Ç, ç</p>
    </body>
    </html>
    """
    try:
        from weasyprint import HTML

        pdf_bytes: bytes = await asyncio.to_thread(
            HTML(string=test_html).write_pdf,
        )
        pdf_size = len(pdf_bytes)
        if pdf_size == 0:
            raise ValueError("PDF boyutu 0 byte")

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "pdf_engine": "weasyprint",
                "turkish_chars": True,
                "pdf_size_bytes": pdf_size,
            },
        )
    except Exception as e:
        logger.error("health_pdf_failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "pdf_engine": "weasyprint",
                "error": str(e),
            },
        )


@app.get("/health/ready", tags=["system"])
async def health_ready() -> JSONResponse:
    """
    Readiness probe — tum bagimliliklar hazir mi?

    Kubernetes readiness probe / load-balancer icin kullanilir.
    Tum bagimliliklar (DB, Redis, MinIO) kontrol edilir.
    Herhangi biri basarisiz olursa status=degraded + 503 doner.
    """
    checks: dict[str, dict[str, str]] = {}
    overall_healthy = True

    # --- DB check ---
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # --- Redis check ---
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # --- MinIO check ---
    try:
        import aiobotocore.session as aio_session

        session = aio_session.get_session()
        endpoint_url = (
            f"{'https' if settings.MINIO_USE_SSL else 'http'}://{settings.MINIO_ENDPOINT}"
        )
        async with session.create_client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
        ) as client:
            await client.head_bucket(Bucket=settings.MINIO_BUCKET)
        checks["minio"] = {"status": "healthy"}
    except Exception as e:
        checks["minio"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # --- Outbox health check ---
    outbox_status = "healthy"
    outbox_warnings: list[str] = []
    try:
        monitor: OutboxMonitor = app.state.outbox_monitor
        stats = await monitor.collect_metrics()

        if stats.stuck_count > 0:
            outbox_status = "warning"
            outbox_warnings.append(f"stuck_events={stats.stuck_count}")

        if stats.pending_count > 1000:
            outbox_status = "degraded"
            overall_healthy = False
            outbox_warnings.append(f"pending_count={stats.pending_count}")

        if stats.avg_lag_seconds > 60:
            outbox_status = "degraded"
            overall_healthy = False
            outbox_warnings.append(f"avg_lag={stats.avg_lag_seconds:.1f}s")

        checks["outbox"] = {
            "status": outbox_status,
            "pending_count": stats.pending_count,
            "stuck_count": stats.stuck_count,
            "avg_lag_seconds": round(stats.avg_lag_seconds, 2),
        }
        if outbox_warnings:
            checks["outbox"]["warnings"] = outbox_warnings
    except Exception as e:
        checks["outbox"] = {"status": "unhealthy", "error": str(e)}
        # Outbox monitor hatasi readiness'i bozmasin — degraded olarak raporla
        logger.warning("health_outbox_check_failed", error=str(e))

    # --- PDF (WeasyPrint) check — opsiyonel servis, readiness'i bozmaz ---
    try:
        from weasyprint import HTML

        test_html = "<html><body><p>Türkçe: İışŞğĞüÜöÖçÇ</p></body></html>"
        pdf_bytes: bytes = await asyncio.to_thread(
            HTML(string=test_html).write_pdf,
        )
        if len(pdf_bytes) > 0:
            checks["pdf"] = {"status": "healthy", "pdf_size_bytes": len(pdf_bytes)}
        else:
            checks["pdf"] = {"status": "unhealthy", "error": "PDF boyutu 0 byte"}
            logger.warning("health_pdf_check_failed", error="PDF boyutu 0 byte")
    except Exception as e:
        checks["pdf"] = {"status": "unhealthy", "error": str(e)}
        # PDF opsiyonel — overall_healthy etkilenmez, sadece warning logla
        logger.warning("health_pdf_check_failed", error=str(e))

    status_code = 200 if overall_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": checks,
        },
    )


# ---------- API v1 Root ----------
@app.get("/api/v1", tags=["system"])
async def api_root() -> dict:
    """API v1 root endpoint."""
    return {
        "message": "Emlak Teknoloji Platformu API v1",
        "version": "0.1.0",
        "docs": "/api/docs",
    }
