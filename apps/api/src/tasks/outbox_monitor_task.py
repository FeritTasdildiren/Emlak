"""
Emlak Teknoloji Platformu - Outbox Monitor Task

Celery Beat tarafindan 60 saniyede bir tetiklenir.
Outbox metriklerini toplar, stuck event'leri tespit eder ve structlog ile loglar.

Tasarim notlari:
    - Beat task'lari request_id tasimaz → None-safe handling (BaseTask halleder).
    - Senkron task — Celery worker'da calisir (sync event loop ile async cagri).
    - OutboxMonitor async metotlari asyncio.run() ile calistirilir.
    - Queue: 'default' (outbox queue sadece poll task'i icindir).

Referans: TASK-040
"""

from __future__ import annotations

import asyncio
from typing import Any

from src.celery_app import celery_app
from src.database import async_session_factory
from src.services.outbox_monitor import OutboxMonitor
from src.tasks.base import BaseTask


@celery_app.task(
    bind=True,
    base=BaseTask,
    queue="default",
    name="src.tasks.outbox_monitor_task.monitor_outbox_health",
    # Bu task monitoring amaçlı — retry yapmasın, bir sonraki beat'te tekrar calisir
    autoretry_for=(),
    max_retries=0,
)
def monitor_outbox_health(self) -> dict[str, Any]:
    """
    Outbox saglik metriklerini toplar ve stuck event'leri raporlar.

    Celery Beat tarafindan 60 saniyede bir cagirilir.
    Metrikleri OTel'e raporlar, stuck event'leri structlog ile loglar.

    Returns:
        dict: Toplanan metrik ozeti.
    """
    self.log.debug("outbox_monitor_started")

    monitor = OutboxMonitor(async_session_factory)

    # --- Metrikleri topla ---
    stats = asyncio.run(monitor.collect_metrics())

    # --- Stuck event tespiti ---
    stuck_events = asyncio.run(monitor.check_stuck_events())

    # --- Structlog ile raporla ---
    self.log.info(
        "outbox_health_report",
        pending_count=stats.pending_count,
        processing_count=stats.processing_count,
        failed_count=stats.failed_count,
        dead_letter_count=stats.dead_letter_count,
        stuck_count=stats.stuck_count,
        processed_total=stats.processed_total,
        avg_lag_seconds=round(stats.avg_lag_seconds, 2),
        max_lag_seconds=round(stats.max_lag_seconds, 2),
        p95_lag_seconds=round(stats.p95_lag_seconds, 2),
    )

    # --- Stuck event'ler icin uyari ---
    if stuck_events:
        for event in stuck_events:
            self.log.warning(
                "outbox_stuck_event_detected",
                event_id=event.id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type,
                locked_by=event.locked_by,
                stuck_duration_seconds=round(event.stuck_duration_seconds, 1),
                retry_count=event.retry_count,
            )

    # --- Kritik esik alarmlari ---
    if stats.pending_count > 1000:
        self.log.error(
            "outbox_pending_threshold_exceeded",
            pending_count=stats.pending_count,
            threshold=1000,
        )

    if stats.avg_lag_seconds > 60:
        self.log.warning(
            "outbox_lag_threshold_exceeded",
            avg_lag_seconds=round(stats.avg_lag_seconds, 2),
            threshold_seconds=60,
        )

    self.log.debug("outbox_monitor_completed")

    return {
        "pending_count": stats.pending_count,
        "processing_count": stats.processing_count,
        "failed_count": stats.failed_count,
        "dead_letter_count": stats.dead_letter_count,
        "stuck_count": stats.stuck_count,
        "processed_total": stats.processed_total,
        "avg_lag_seconds": round(stats.avg_lag_seconds, 2),
        "max_lag_seconds": round(stats.max_lag_seconds, 2),
    }
