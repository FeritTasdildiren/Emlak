"""
Emlak Teknoloji Platformu - OpenTelemetry Instrumentation

Distributed tracing, metrics ve observability altyapisi.

Tasarim kararlari:
    - OTEL_EXPORTER_OTLP_ENDPOINT bos ise tamamen devre disi (no-op).
      Dev ortaminda hicbir performans yuku olmaz.
    - Sampler: ParentBasedTraceIdRatio(1.0) — production'da dusurulabilir.
    - Propagator: W3C TraceContext — upstream service'lerle uyumlu.
    - Instrumentasyonlar: FastAPI, SQLAlchemy, httpx, Redis.
    - MeterProvider: OTLP gRPC ile metrik export. Endpoint yoksa no-op meter.

Referans: docs/MIMARI-KARARLAR.md ADR-0004
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.config import settings

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = structlog.get_logger(__name__)

# ---------- Meter (global reference) ----------
# get_meter() her zaman guvenli: endpoint yoksa no-op meter doner.
_meter = None


def get_meter():
    """
    OTel Meter instance'ini dondurur.

    OTEL_EXPORTER_OTLP_ENDPOINT yapilandirilmamissa no-op meter doner.
    Bu sayede metrik yaratan kodlar hicbir kosul kontrolu yapmak zorunda kalmaz;
    no-op meter uzerindeki tum islemler sifir maliyetlidir.

    Returns:
        opentelemetry.metrics.Meter — aktif veya no-op.
    """
    global _meter
    if _meter is not None:
        return _meter

    # Lazy init: ilk cagrildiginda olustur
    try:
        from opentelemetry import metrics

        _meter = metrics.get_meter("emlak-api")
    except ImportError:
        # opentelemetry paketi yuklu degil — None doner, caller guard etmeli
        _meter = None

    return _meter


def init_telemetry(app: FastAPI) -> None:
    """
    OpenTelemetry SDK'yi baslatir ve FastAPI uygulamasina enstrumante eder.

    OTEL_EXPORTER_OTLP_ENDPOINT bos ise hicbir sey yapmaz (graceful no-op).
    Bu sayede development ortaminda OTel yuku sifirdir.

    Args:
        app: FastAPI uygulama instance'i.
    """
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    service_name = settings.OTEL_SERVICE_NAME

    if not endpoint:
        logger.info(
            "otel_disabled",
            reason="OTEL_EXPORTER_OTLP_ENDPOINT not configured",
        )
        return

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.propagators.textmap import CompositeHTTPPropagator
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
        from opentelemetry.trace.propagation import TraceContextTextMapPropagator
    except ImportError:
        logger.warning(
            "otel_import_error",
            detail="OpenTelemetry paketleri yuklu degil, atlanıyor",
        )
        return

    # --- Resource: service metadata ---
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": app.version or "0.1.0",
            "deployment.environment": settings.APP_ENV,
        }
    )

    # --- Sampler: %100 (production'da dusurulecek) ---
    sampler = ParentBasedTraceIdRatio(rate=1.0)

    # --- TracerProvider ---
    provider = TracerProvider(resource=resource, sampler=sampler)

    # --- OTLP gRPC Exporter ---
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    # --- MeterProvider ---
    global _meter
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=60_000,  # 60sn'de bir export
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    _meter = metrics.get_meter("emlak-api")

    # --- W3C TraceContext Propagator ---
    propagator = CompositeHTTPPropagator([TraceContextTextMapPropagator()])
    set_global_textmap(propagator)

    # --- Instrumentasyonlar ---

    # FastAPI: tum HTTP endpoint'lerini otomatik trace eder
    FastAPIInstrumentor.instrument_app(app)

    # SQLAlchemy: DB sorgularini trace eder
    from src.database import engine

    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    # httpx: dis HTTP cagrilarini trace eder
    HTTPXClientInstrumentor().instrument()

    # Redis: cache operasyonlarini trace eder
    RedisInstrumentor().instrument()

    logger.info(
        "otel_initialized",
        service_name=service_name,
        endpoint=endpoint,
        environment=settings.APP_ENV,
        sampler="ParentBasedTraceIdRatio(1.0)",
        instrumentations=["fastapi", "sqlalchemy", "httpx", "redis"],
        metrics_enabled=True,
        metrics_export_interval_ms=60_000,
    )
