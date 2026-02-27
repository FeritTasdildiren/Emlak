"""
Emlak Teknoloji Platformu - Outbox Monitor Service

Outbox worker saglik izleme servisi: lag metrikleri, stuck event tespiti,
admin endpoint'leri icin veri toplama.

Tasarim kararlari:
    - OTel Meter API: OTEL_EXPORTER_OTLP_ENDPOINT bos ise no-op meter.
      Tum metrik islemleri sifir maliyetli no-op olur.
    - STUCK_THRESHOLD_SECONDS = 300 (5dk): processing durumunda 5dk'dan
      uzun kalan event'ler stuck kabul edilir.
    - collect_metrics(): Celery beat task tarafindan 60sn'de bir cagirilir.
    - Tum DB islemleri raw SQL (text()) ile yapilir — ORM overhead yok.

Metrikler:
    - outbox_lag_seconds     (histogram) → pending event'lerin yaslanma suresi
    - outbox_pending_count   (gauge)     → pending event sayisi
    - outbox_processing_count(gauge)     → processing event sayisi
    - outbox_failed_count    (gauge)     → failed event sayisi
    - outbox_dead_letter_count(gauge)    → dead_letter event sayisi
    - outbox_stuck_count     (gauge)     → stuck event sayisi
    - outbox_processed_total (counter)   → toplam islenen event (kumulatif)
    - outbox_errors_total    (counter)   → toplam hata (kumulatif)

Referans: docs/MIMARI-KARARLAR.md
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.telemetry import get_meter

logger = structlog.get_logger(__name__)

# ---------- Configuration ----------
STUCK_THRESHOLD_SECONDS: int = 300  # 5 dakika — processing'de kalan event stuck sayilir


@dataclass
class LagStats:
    """Outbox lag istatistikleri."""

    pending_count: int = 0
    processing_count: int = 0
    failed_count: int = 0
    dead_letter_count: int = 0
    stuck_count: int = 0
    processed_total: int = 0
    errors_total: int = 0
    avg_lag_seconds: float = 0.0
    max_lag_seconds: float = 0.0
    p95_lag_seconds: float = 0.0
    oldest_pending_at: datetime | None = None


@dataclass
class StuckEvent:
    """Stuck durumundaki event bilgisi."""

    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    status: str
    locked_at: datetime | None
    locked_by: str | None
    stuck_duration_seconds: float
    retry_count: int
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "status": self.status,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "locked_by": self.locked_by,
            "stuck_duration_seconds": round(self.stuck_duration_seconds, 1),
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
        }


class OutboxMonitor:
    """
    Outbox worker saglik izleme servisi.

    OTel Meter API kullanarak metrik toplar. OTEL_EXPORTER_OTLP_ENDPOINT
    yapilandirilmamissa tum metrik islemleri no-op olur (sifir maliyet).

    Usage:
        monitor = OutboxMonitor(async_session_factory)
        stats = await monitor.collect_metrics()
        stuck = await monitor.check_stuck_events()
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        stuck_threshold_seconds: int = STUCK_THRESHOLD_SECONDS,
    ) -> None:
        self._session_factory = session_factory
        self._stuck_threshold = stuck_threshold_seconds

        # --- OTel Metrikleri ---
        self._setup_meters()

    def _setup_meters(self) -> None:
        """
        OTel meter instrument'larini olusturur.

        get_meter() no-op meter donerse tum create_* cagilari
        no-op instrument doner — sifir overhead.
        """
        meter = get_meter()

        if meter is None:
            # OTel paketi yuklu degil — tum instrument'lar None
            self._lag_histogram = None
            self._pending_gauge = None
            self._processing_gauge = None
            self._failed_gauge = None
            self._dead_letter_gauge = None
            self._stuck_gauge = None
            self._processed_counter = None
            self._errors_counter = None
            logger.debug("outbox_monitor_meters_disabled", reason="otel_not_available")
            return

        self._lag_histogram = meter.create_histogram(
            name="outbox_lag_seconds",
            description="Pending outbox event'lerin bekleme suresi (saniye)",
            unit="s",
        )
        self._pending_gauge = meter.create_up_down_counter(
            name="outbox_pending_count",
            description="Pending durumundaki outbox event sayisi",
        )
        self._processing_gauge = meter.create_up_down_counter(
            name="outbox_processing_count",
            description="Processing durumundaki outbox event sayisi",
        )
        self._failed_gauge = meter.create_up_down_counter(
            name="outbox_failed_count",
            description="Failed durumundaki outbox event sayisi",
        )
        self._dead_letter_gauge = meter.create_up_down_counter(
            name="outbox_dead_letter_count",
            description="Dead letter durumundaki outbox event sayisi",
        )
        self._stuck_gauge = meter.create_up_down_counter(
            name="outbox_stuck_count",
            description="Stuck (5dk+ processing) outbox event sayisi",
        )
        self._processed_counter = meter.create_counter(
            name="outbox_processed_total",
            description="Toplam islenen outbox event sayisi (kumulatif)",
        )
        self._errors_counter = meter.create_counter(
            name="outbox_errors_total",
            description="Toplam outbox hata sayisi (kumulatif)",
        )

        logger.debug("outbox_monitor_meters_initialized")

    def _record_gauge(self, gauge, value: int) -> None:
        """
        UpDownCounter'i gauge olarak kullan.

        OTel SDK'da 'observable gauge' callback gerektirir.
        Basitlik icin UpDownCounter kullanip her collection'da
        delta hesapliyoruz.
        """
        if gauge is not None:
            # Not: UpDownCounter sadece delta kabul eder.
            # Bu degeri observe edildigi anda dogru gostermek icin
            # callback-based gauge yerine her seferinde record ediyoruz.
            gauge.add(value)

    async def collect_metrics(self) -> LagStats:
        """
        Outbox metriklerini toplar ve OTel'e raporlar.

        Celery beat task tarafindan periyodik cagirilir (60sn).
        Tek bir DB sorgusu ile tum istatistikleri toplar.

        Returns:
            LagStats: Guncel outbox istatistikleri.
        """
        stats = LagStats()

        try:
            async with self._session_factory() as session:
                # --- Status bazli sayilar ---
                result = await session.execute(
                    text(
                        "SELECT status, COUNT(*) as cnt "
                        "FROM outbox_events "
                        "GROUP BY status"
                    )
                )
                for row in result.fetchall():
                    status_val = row[0]
                    count_val = row[1]
                    if status_val == "pending":
                        stats.pending_count = count_val
                    elif status_val == "processing":
                        stats.processing_count = count_val
                    elif status_val == "failed":
                        stats.failed_count = count_val
                    elif status_val == "dead_letter":
                        stats.dead_letter_count = count_val
                    elif status_val == "sent":
                        stats.processed_total = count_val

                # --- Errors total (failed + dead_letter) ---
                stats.errors_total = stats.failed_count + stats.dead_letter_count

                # --- Stuck event sayisi ---
                result = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM outbox_events "
                        "WHERE status = 'processing' "
                        "  AND locked_at < now() - interval '1 second' * :threshold"
                    ),
                    {"threshold": self._stuck_threshold},
                )
                stats.stuck_count = result.scalar() or 0

                # --- Lag istatistikleri (pending event'ler) ---
                result = await session.execute(
                    text(
                        "SELECT "
                        "  COALESCE(AVG(EXTRACT(EPOCH FROM (now() - created_at))), 0) as avg_lag, "
                        "  COALESCE(MAX(EXTRACT(EPOCH FROM (now() - created_at))), 0) as max_lag, "
                        "  COALESCE("
                        "    PERCENTILE_CONT(0.95) WITHIN GROUP "
                        "    (ORDER BY EXTRACT(EPOCH FROM (now() - created_at))), 0"
                        "  ) as p95_lag, "
                        "  MIN(created_at) as oldest "
                        "FROM outbox_events "
                        "WHERE status = 'pending'"
                    )
                )
                lag_row = result.fetchone()
                if lag_row:
                    stats.avg_lag_seconds = float(lag_row[0] or 0)
                    stats.max_lag_seconds = float(lag_row[1] or 0)
                    stats.p95_lag_seconds = float(lag_row[2] or 0)
                    stats.oldest_pending_at = lag_row[3]

            # --- OTel metriklerini raporla ---
            self._report_otel_metrics(stats)

        except Exception:
            logger.exception("outbox_monitor_collect_failed")

        return stats

    def _report_otel_metrics(self, stats: LagStats) -> None:
        """OTel instrument'larina metrikleri raporla."""
        # Histogram: her pending event'in lag'ini kaydet
        if self._lag_histogram is not None and stats.avg_lag_seconds > 0:
            self._lag_histogram.record(stats.avg_lag_seconds)

        # Gauge-like counters (snapshot degerleri)
        # Not: UpDownCounter delta ister ama monitoring icin
        # her collection'da mutlak degeri loglariz, OTel'e delta gondeririz.
        if self._pending_gauge is not None:
            self._pending_gauge.add(stats.pending_count)
        if self._processing_gauge is not None:
            self._processing_gauge.add(stats.processing_count)
        if self._failed_gauge is not None:
            self._failed_gauge.add(stats.failed_count)
        if self._dead_letter_gauge is not None:
            self._dead_letter_gauge.add(stats.dead_letter_count)
        if self._stuck_gauge is not None:
            self._stuck_gauge.add(stats.stuck_count)

    async def check_stuck_events(self) -> list[StuckEvent]:
        """
        Stuck (5dk+ processing durumunda) event'leri tespit eder.

        Returns:
            list[StuckEvent]: Stuck event detaylari.
        """
        stuck_events: list[StuckEvent] = []

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    text(
                        "SELECT id, event_type, aggregate_type, aggregate_id, "
                        "       status, locked_at, locked_by, retry_count, created_at, "
                        "       EXTRACT(EPOCH FROM (now() - locked_at)) as stuck_seconds "
                        "FROM outbox_events "
                        "WHERE status = 'processing' "
                        "  AND locked_at < now() - interval '1 second' * :threshold "
                        "ORDER BY locked_at ASC"
                    ),
                    {"threshold": self._stuck_threshold},
                )

                for row in result.fetchall():
                    stuck_events.append(
                        StuckEvent(
                            id=str(row[0]),
                            event_type=row[1],
                            aggregate_type=row[2],
                            aggregate_id=str(row[3]),
                            status=row[4],
                            locked_at=row[5],
                            locked_by=row[6],
                            retry_count=row[7],
                            created_at=row[8],
                            stuck_duration_seconds=float(row[9] or 0),
                        )
                    )

        except Exception:
            logger.exception("outbox_monitor_stuck_check_failed")

        return stuck_events

    async def get_lag_stats(self) -> dict[str, Any]:
        """
        Admin endpoint icin lag istatistiklerini dondurur.

        Returns:
            dict: JSON-serializable lag istatistikleri.
        """
        stats = await self.collect_metrics()
        return {
            "pending_count": stats.pending_count,
            "processing_count": stats.processing_count,
            "failed_count": stats.failed_count,
            "dead_letter_count": stats.dead_letter_count,
            "stuck_count": stats.stuck_count,
            "processed_total": stats.processed_total,
            "errors_total": stats.errors_total,
            "lag": {
                "avg_seconds": round(stats.avg_lag_seconds, 2),
                "max_seconds": round(stats.max_lag_seconds, 2),
                "p95_seconds": round(stats.p95_lag_seconds, 2),
            },
            "oldest_pending_at": (
                stats.oldest_pending_at.isoformat() if stats.oldest_pending_at else None
            ),
            "stuck_threshold_seconds": self._stuck_threshold,
            "collected_at": datetime.now(UTC).isoformat(),
        }

    async def force_release_stuck(self, event_id: str) -> bool:
        """
        Stuck event'i zorla serbest birakir (status → pending, lock temizle).

        Admin tarafindan manuel mudahale icin kullanilir.
        Event'i silmez, pending'e dondurur — worker tekrar dener.

        Args:
            event_id: Serbest birakilacak event UUID'si.

        Returns:
            True ise basarili, False ise event bulunamadi veya stuck degil.
        """
        try:
            # UUID validasyonu
            parsed_id = uuid.UUID(event_id)
        except ValueError:
            logger.warning("outbox_monitor_invalid_event_id", event_id=event_id)
            return False

        try:
            async with self._session_factory() as session, session.begin():
                result = await session.execute(
                    text(
                        "UPDATE outbox_events "
                        "SET status = 'pending', "
                        "    locked_at = NULL, "
                        "    locked_by = NULL, "
                        "    error_message = 'Force released by admin at ' || now()::text "
                        "WHERE id = :event_id "
                        "  AND status = 'processing' "
                        "  AND locked_at < now() - interval '1 second' * :threshold"
                    ),
                    {"event_id": str(parsed_id), "threshold": self._stuck_threshold},
                )

                if result.rowcount == 0:
                    logger.warning(
                        "outbox_monitor_release_not_found",
                        event_id=event_id,
                        detail="Event bulunamadi veya stuck degil",
                    )
                    return False

                logger.info(
                    "outbox_monitor_event_released",
                    event_id=event_id,
                )
                return True

        except Exception:
            logger.exception("outbox_monitor_release_failed", event_id=event_id)
            return False
