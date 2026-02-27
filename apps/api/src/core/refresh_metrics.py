"""
Emlak Teknoloji Platformu - Veri Yenileme OTel Metrikleri

Area analysis ve deprem risk yenileme islemlerinin metriklerini toplar.
Grafana dashboard'da goruntulenmek uzere OTel'e raporlar.

Tasarim kararlari:
    - get_meter() no-op guard: OTEL_EXPORTER_OTLP_ENDPOINT yoksa tum
      instrument'lar None — sifir overhead.
    - UpDownCounter gauge olarak kullanilir (outbox_monitor pattern).
    - Histogram: yenileme suresi (saniye).
    - Counter: kumulatif basarisiz yenileme sayisi.
    - Modul-level singleton: _metrics ilk import'ta olusturulur.

Metrikler:
    - refresh_status_count       (UpDownCounter) — Her status'taki kayit sayisi
    - refresh_duration_seconds   (Histogram)     — Yenileme suresi
    - refresh_last_success_ts    (UpDownCounter)  — Son basarili yenileme Unix timestamp
    - refresh_failed_total       (Counter)       — Toplam basarisiz yenileme sayisi
    - refresh_stale_records      (UpDownCounter)  — Stale kayit sayisi

Referans: src/services/outbox_monitor.py (OTel pattern), TASK-054
"""

from __future__ import annotations

import time

import structlog

from src.core.telemetry import get_meter

logger = structlog.get_logger(__name__)


class RefreshMetrics:
    """
    Veri yenileme OTel metrikleri.

    get_meter() None donerse tum instrument'lar None olur — no-op.
    Bu sayede metrik cagrilari hicbir kosul kontrolu gerektirmez.

    Usage:
        from src.core.refresh_metrics import refresh_metrics

        refresh_metrics.refresh_started("area_analyses")
        # ... is yap ...
        refresh_metrics.refresh_completed("area_analyses", elapsed=12.5, result="success")
    """

    def __init__(self) -> None:
        self._setup_meters()

    def _setup_meters(self) -> None:
        """OTel meter instrument'larini olusturur."""
        meter = get_meter()

        if meter is None:
            self._status_count = None
            self._duration_histogram = None
            self._last_success_ts = None
            self._failed_counter = None
            self._stale_gauge = None
            logger.debug("refresh_metrics_disabled", reason="otel_not_available")
            return

        self._status_count = meter.create_up_down_counter(
            name="refresh_status_count",
            description="Refresh status bazinda kayit sayisi",
        )
        self._duration_histogram = meter.create_histogram(
            name="refresh_duration_seconds",
            description="Veri yenileme suresi (saniye)",
            unit="s",
        )
        self._last_success_ts = meter.create_up_down_counter(
            name="refresh_last_success_ts",
            description="Son basarili yenileme Unix timestamp",
        )
        self._failed_counter = meter.create_counter(
            name="refresh_failed_total",
            description="Toplam basarisiz yenileme sayisi (kumulatif)",
        )
        self._stale_gauge = meter.create_up_down_counter(
            name="refresh_stale_records",
            description="Stale kayit sayisi",
        )

        logger.debug("refresh_metrics_initialized")

    # ─── Public API ────────────────────────────────────────────────────

    def record_status_counts(
        self,
        table: str,
        fresh: int = 0,
        stale: int = 0,
        refreshing: int = 0,
        failed: int = 0,
    ) -> None:
        """Her status icin kayit sayisini raporla."""
        if self._status_count is not None:
            self._status_count.add(fresh, {"table": table, "status": "fresh"})
            self._status_count.add(stale, {"table": table, "status": "stale"})
            self._status_count.add(refreshing, {"table": table, "status": "refreshing"})
            self._status_count.add(failed, {"table": table, "status": "failed"})

        if self._stale_gauge is not None:
            self._stale_gauge.add(stale, {"table": table})

    def refresh_started(self, table: str) -> None:
        """Yenileme basladiginda cagir — loglama amacli."""
        logger.info("refresh_metric_started", table=table)

    def refresh_completed(
        self,
        table: str,
        duration: float,
        result: str,
    ) -> None:
        """
        Yenileme tamamlandiginda cagir.

        Args:
            table: Tablo adi (area_analyses / deprem_risks)
            duration: Gecen sure (saniye)
            result: "success" veya "failure"
        """
        if self._duration_histogram is not None:
            self._duration_histogram.record(
                duration,
                {"table": table, "result": result},
            )

        if result == "success" and self._last_success_ts is not None:
            self._last_success_ts.add(
                int(time.time()),
                {"table": table},
            )

        if result == "failure" and self._failed_counter is not None:
            self._failed_counter.add(1, {"table": table})

        logger.info(
            "refresh_metric_completed",
            table=table,
            duration=round(duration, 2),
            result=result,
        )

    def record_failed(self, table: str, error_type: str) -> None:
        """Basarisiz yenileme sayacini artir."""
        if self._failed_counter is not None:
            self._failed_counter.add(
                1,
                {"table": table, "error_type": error_type},
            )


# ─── Module-level Singleton ──────────────────────────────────────────
refresh_metrics = RefreshMetrics()
