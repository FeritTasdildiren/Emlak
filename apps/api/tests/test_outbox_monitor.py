"""
Emlak Teknoloji Platformu - Outbox Monitor Integration Tests (TASK-043)

OutboxMonitor saglik izleme servisi testleri:
    - collect_metrics(): Status bazli sayilar ve lag istatistikleri
    - check_stuck_events(): 5dk+ processing'de kalan event tespiti
    - force_release_stuck(): Stuck event'i pending'e dondurme
    - get_lag_stats(): Admin endpoint icin JSON-serializable istatistikler

Tasarim notu:
    - OutboxMonitor OTel metrikleri test ortaminda no-op (endpoint yok)
    - stuck_threshold_seconds = 1 (test fixture — normalde 300s)
    - COALESCE guard: bos tablo'da PERCENTILE_CONT NULL doner → 0 olmali

asyncio_mode = "auto" (pyproject.toml) — @pytest.mark.asyncio gerekmez
"""

from __future__ import annotations

import asyncio

from src.services.outbox_monitor import LagStats, OutboxMonitor, StuckEvent
from tests.conftest import (
    get_outbox_event_status,
    test_session_factory,
)


# ================================================================
# Test Outbox Monitor
# ================================================================
class TestOutboxMonitor:
    """
    Outbox monitoring servisi integration testleri.

    outbox_monitor fixture: stuck_threshold_seconds=1 (test icin hizli).
    """

    async def test_collect_metrics_empty(self, outbox_monitor):
        """
        Bos outbox'ta tum metrikler 0 (veya yakini).

        NOT: Diger testlerden kalan event'ler olabilir,
        bu yuzden >= 0 kontrolu yapilir.
        COALESCE guard: PERCENTILE_CONT bos tabloda NULL doner → 0.
        """
        stats = await outbox_monitor.collect_metrics()

        assert isinstance(stats, LagStats)
        assert stats.pending_count >= 0
        assert stats.processing_count >= 0
        assert stats.failed_count >= 0
        assert stats.dead_letter_count >= 0
        assert stats.avg_lag_seconds >= 0.0
        assert stats.max_lag_seconds >= 0.0
        assert stats.p95_lag_seconds >= 0.0

    async def test_collect_metrics_with_events(self, outbox_monitor, create_outbox_event):
        """
        Farkli durumlardaki event'lerin dogru sayilmasi.

        3 pending, 1 sent, 1 dead_letter olustur → sayilari dogrula.
        """
        for i in range(3):
            await create_outbox_event(
                event_type=f"monitor.pending.{i}",
                status="pending",
            )
        await create_outbox_event(
            event_type="monitor.sent",
            status="sent",
        )
        await create_outbox_event(
            event_type="monitor.dead",
            status="dead_letter",
        )

        stats = await outbox_monitor.collect_metrics()

        assert stats.pending_count >= 3
        assert stats.processed_total >= 1  # sent event'ler
        assert stats.dead_letter_count >= 1
        assert stats.errors_total >= 1  # failed + dead_letter

    async def test_stuck_event_detection(self, create_outbox_event):
        """
        5dk+ (veya test icin 1s+) processing'de kalan event = stuck.

        Event'i processing status'unda locked_at = gecmis zaman ile olustur.
        outbox_monitor (stuck_threshold=1s) bunu stuck olarak tespit etmeli.
        """
        event_id = await create_outbox_event(
            event_type="monitor.stuck",
            status="processing",
            locked_by="stale-worker-001",
            locked_at="2020-01-01 00:00:00+00",  # Cok eski → kesinlikle stuck
        )

        # stuck_threshold_seconds=1 ile monitor
        monitor = OutboxMonitor(test_session_factory, stuck_threshold_seconds=1)
        stuck_events = await monitor.check_stuck_events()

        assert len(stuck_events) >= 1

        stuck_ids = {se.id for se in stuck_events}
        assert str(event_id) in stuck_ids

        # Stuck event detay kontrolu
        stuck = next(se for se in stuck_events if se.id == str(event_id))
        assert isinstance(stuck, StuckEvent)
        assert stuck.event_type == "monitor.stuck"
        assert stuck.locked_by == "stale-worker-001"
        assert stuck.stuck_duration_seconds > 0

    async def test_no_stuck_events_in_normal_flow(self, outbox_monitor, create_outbox_event):
        """
        Normal akista stuck event yok.

        Sadece pending ve sent event'ler var → stuck_count == 0 (o event'ler icin).
        """
        await create_outbox_event(
            event_type="monitor.normal.pending",
            status="pending",
        )
        await create_outbox_event(
            event_type="monitor.normal.sent",
            status="sent",
        )

        stuck_events = await outbox_monitor.check_stuck_events()
        # Bu testin event'leri stuck olmamali (pending/sent)
        normal_types = {"monitor.normal.pending", "monitor.normal.sent"}
        stuck_types = {se.event_type for se in stuck_events}
        assert not (normal_types & stuck_types), "Normal event'ler stuck olmamali"

    async def test_lag_stats_calculation(self, outbox_monitor, create_outbox_event):
        """
        avg_lag, max_lag, p95_lag dogru hesaplanir.

        Pending event'ler icin lag = now() - created_at.
        En az 1 pending event varken lag > 0 olmali.
        """
        await create_outbox_event(
            event_type="monitor.lag",
            status="pending",
        )

        # Kisa bir bekleme — lag > 0 olmasi icin
        await asyncio.sleep(0.1)

        stats = await outbox_monitor.collect_metrics()

        assert stats.avg_lag_seconds > 0, "Pending event varken avg_lag > 0 olmali"
        assert stats.max_lag_seconds > 0
        assert stats.p95_lag_seconds > 0
        # avg <= max her zaman dogru olmali
        assert stats.avg_lag_seconds <= stats.max_lag_seconds + 0.1

    async def test_force_release_stuck_event(self, create_outbox_event):
        """
        Stuck event serbest birakma: processing → pending, locked_by → None.

        Admin tarafindan manuel mudahale senaryosu.
        """
        event_id = await create_outbox_event(
            event_type="monitor.force.release",
            status="processing",
            locked_by="dead-worker-999",
            locked_at="2020-01-01 00:00:00+00",  # Cok eski → stuck
        )

        monitor = OutboxMonitor(test_session_factory, stuck_threshold_seconds=1)
        result = await monitor.force_release_stuck(str(event_id))
        assert result is True

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "pending"
        assert state["locked_by"] is None
        assert state["locked_at"] is None
        assert "Force released" in (state["error_message"] or "")

    async def test_force_release_non_stuck_event_returns_false(self, create_outbox_event):
        """
        Stuck OLMAYAN event force release edilemez.

        pending status'taki event icin False doner.
        """
        event_id = await create_outbox_event(
            event_type="monitor.not.stuck",
            status="pending",
        )

        monitor = OutboxMonitor(test_session_factory, stuck_threshold_seconds=1)
        result = await monitor.force_release_stuck(str(event_id))
        assert result is False

    async def test_force_release_invalid_uuid_returns_false(self, outbox_monitor):
        """Gecersiz UUID ile force release False doner."""
        result = await outbox_monitor.force_release_stuck("not-a-valid-uuid")
        assert result is False

    async def test_get_lag_stats_returns_dict(self, outbox_monitor, create_outbox_event):
        """
        get_lag_stats() JSON-serializable dict doner.

        Admin endpoint icin kullanilir — tum key'ler mevcut olmali.
        """
        await create_outbox_event(event_type="monitor.lagstats", status="pending")

        lag_dict = await outbox_monitor.get_lag_stats()

        assert isinstance(lag_dict, dict)
        # Beklenen key'ler
        assert "pending_count" in lag_dict
        assert "processing_count" in lag_dict
        assert "failed_count" in lag_dict
        assert "dead_letter_count" in lag_dict
        assert "stuck_count" in lag_dict
        assert "processed_total" in lag_dict
        assert "errors_total" in lag_dict
        assert "lag" in lag_dict
        assert "collected_at" in lag_dict
        assert "stuck_threshold_seconds" in lag_dict

        # Lag sub-dict kontrolu
        lag = lag_dict["lag"]
        assert "avg_seconds" in lag
        assert "max_seconds" in lag
        assert "p95_seconds" in lag
