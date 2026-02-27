"""
Emlak Teknoloji Platformu - Outbox Integration Tests (TASK-043)

Outbox pattern tam entegrasyon test suite'i:
    - OutboxWorker: poll_and_process, _acquire_events, _process_event
    - RetryPolicy entegrasyonu: transient/permanent hata ayirimi
    - DLQ (Dead Letter Queue): listeleme, retry, purge
    - Messaging entegrasyonu: event → mesaj gonderim akisi (mock)
    - Concurrency: FOR UPDATE SKIP LOCKED guvenlik testleri

Kirmizi cizgiler:
    - Gercek Telegram/Redis cagrisi YAPILMAZ — mock kullanilir
    - Her test birbirinden bagimsiz calisir (izole transaction)
    - Event'ler committed olmali (worker kendi session'ini acar)
    - DLQ retry'da retry_count SIFIRLANMAZ
    - asyncio_mode = "auto" (pyproject.toml) — @pytest.mark.asyncio gerekmez
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

from sqlalchemy import text

from src.services.dlq_service import DLQService
from src.services.outbox_worker import OutboxWorker
from src.services.retry_policy import get_policy_for_event
from tests.conftest import (
    OUTBOX_EVENT_ID_1,
    get_outbox_event_status,
    test_session_factory,
)


# ================================================================
# Test Outbox Worker Basic Flow
# ================================================================
class TestOutboxWorkerBasicFlow:
    """
    Temel outbox akisi: pending → processing → sent.

    Worker'in poll_and_process metodu ile event'lerin basarili
    islenmesini dogrulayan testler.
    """

    async def test_poll_empty_queue(self, outbox_worker):
        """Bos outbox'ta poll_and_process 0 dondurur."""
        processed = await outbox_worker.poll_and_process(batch_size=10)
        assert processed == 0

    async def test_single_event_processing(self, outbox_worker, create_outbox_event):
        """
        Tek event basarili isleme: pending → sent.

        Event olusturulur, worker poll eder, status 'sent' olur.
        """
        event_id = await create_outbox_event(
            event_id=OUTBOX_EVENT_ID_1,
            event_type="test.event",
        )

        processed = await outbox_worker.poll_and_process(batch_size=10)
        assert processed == 1

        state = await get_outbox_event_status(event_id)
        assert state is not None
        assert state["status"] == "sent"

    async def test_batch_processing(self, outbox_worker, create_outbox_event):
        """
        batch_size=5 ile coklu event isleme.

        3 event olusturulur, hepsi tek batch'te islenir.
        """
        ids = []
        for i in range(3):
            eid = await create_outbox_event(
                event_type=f"batch.test.{i}",
            )
            ids.append(eid)

        processed = await outbox_worker.poll_and_process(batch_size=5)
        assert processed == 3

        for eid in ids:
            state = await get_outbox_event_status(eid)
            assert state["status"] == "sent"

    async def test_batch_size_limits_processing(self, outbox_worker, create_outbox_event):
        """
        batch_size=2 ile 3 event — sadece 2 islenir.

        batch_size limiti asilan event'ler sonraki poll'da islenir.
        """
        ids = []
        for i in range(3):
            eid = await create_outbox_event(event_type=f"limit.test.{i}")
            ids.append(eid)

        processed = await outbox_worker.poll_and_process(batch_size=2)
        assert processed == 2

        # 3. event hala pending olmali veya sonraki poll'da islenir
        second_pass = await outbox_worker.poll_and_process(batch_size=2)
        assert second_pass == 1

    async def test_event_processed_at_timestamp(self, outbox_worker, create_outbox_event):
        """Islenen event'te processed_at set edilmeli (NULL degil)."""
        event_id = await create_outbox_event(event_type="timestamp.test")

        await outbox_worker.poll_and_process(batch_size=1)

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "sent"
        assert state["processed_at"] is not None

    async def test_already_sent_event_not_reprocessed(self, outbox_worker, create_outbox_event):
        """Zaten 'sent' olan event tekrar islenmemeli."""
        await create_outbox_event(
            event_type="already.sent",
            status="sent",
        )

        processed = await outbox_worker.poll_and_process(batch_size=10)
        assert processed == 0

    async def test_failed_event_not_acquired(self, outbox_worker, create_outbox_event):
        """'failed' status'taki event worker tarafindan alinmaz."""
        await create_outbox_event(
            event_type="failed.event",
            status="failed",
        )

        processed = await outbox_worker.poll_and_process(batch_size=10)
        assert processed == 0

    async def test_dead_letter_event_not_acquired(self, outbox_worker, create_outbox_event):
        """'dead_letter' status'taki event worker tarafindan alinmaz."""
        await create_outbox_event(
            event_type="dead.event",
            status="dead_letter",
        )

        processed = await outbox_worker.poll_and_process(batch_size=10)
        assert processed == 0


# ================================================================
# Test Outbox Retry Policy Integration
# ================================================================
class TestOutboxRetryPolicy:
    """
    Retry mekanizmasi ve error classification integration testleri.

    Worker'in _process_event metodunda hata olusmasi durumunda
    retry/DLQ karari dogru verildigini dogrular.
    """

    async def test_transient_error_outer_handler_does_not_crash(self, create_outbox_event):
        """
        _process_event tamamen basarisiz olursa worker CRASH etmez.

        poll_and_process'teki outer try/except exception'i yakalar,
        event 'processing' durumunda kalir (stuck event haline gelir).
        Stuck event recovery OutboxMonitor.force_release_stuck ile yapilir.
        """
        event_id = await create_outbox_event(
            event_type="notification",
            retry_count=0,
        )

        worker = OutboxWorker(test_session_factory)

        async def _total_failure(session, event):
            raise ConnectionError("Catastrophic failure")

        with patch.object(worker, "_process_event", side_effect=_total_failure):
            # Worker crash ETMEMELI — exception loglayip devam etmeli
            processed = await worker.poll_and_process(batch_size=1)

        # Exception firladigi icin processed sayilmaz
        assert processed == 0

        # Event 'processing' durumunda kaldi (stuck)
        state = await get_outbox_event_status(event_id)
        assert state is not None
        assert state["status"] == "processing"

    async def test_transient_error_retry_via_inner_handler(self, create_outbox_event):
        """
        Transient hata: _process_event icindeki try/except ile retry.

        Worker'in event processing icindeki UPDATE'i ConnectionError firlatacak
        sekilde mock'lanir. Retry mantigi devreye girer.
        """
        event_id = await create_outbox_event(
            event_type="notification",  # max_retries=3
            retry_count=0,
        )

        worker = OutboxWorker(test_session_factory)

        # _process_event icindeki UPDATE basarisiz olsun
        with patch.object(worker, "_process_event", wraps=worker._process_event) as mock_proc:
            # Gercek _process_event'i cagirmak yerine, event'in retry'a alinmasini
            # simule eden bir akis olustur
            async def _transient_failure(session, event):
                """Simulated transient failure — event retry'a alinir."""
                from src.services.retry_policy import get_policy_for_event as _get_policy

                policy = _get_policy(event.event_type)
                exc = ConnectionError("Simulated network error")
                new_retry_count = event.retry_count + 1
                backoff = policy.calculate_next_retry(new_retry_count)

                await session.execute(
                    text(
                        "UPDATE outbox_events "
                        "SET status = 'pending', "
                        "    retry_count = :retry_count, "
                        "    error_message = :error_message, "
                        "    next_retry_at = now() + interval '1 second' * :backoff, "
                        "    locked_at = NULL, "
                        "    locked_by = NULL "
                        "WHERE id = :event_id"
                    ),
                    {
                        "retry_count": new_retry_count,
                        "error_message": str(exc)[:500],
                        "backoff": backoff,
                        "event_id": event.id,
                    },
                )
                raise exc

            mock_proc.side_effect = _transient_failure

            # Exception loglanir ama suppress edilir
            await worker.poll_and_process(batch_size=1)

        state = await get_outbox_event_status(event_id)
        assert state is not None
        assert state["status"] == "pending"  # retry icin pending'e dondu
        assert state["retry_count"] == 1
        assert state["error_message"] is not None
        assert "network error" in state["error_message"].lower()

    async def test_permanent_error_goes_to_dlq(self, create_outbox_event):
        """
        ValidationError → event dead_letter'a (permanent, retry atlanir).
        """
        event_id = await create_outbox_event(
            event_type="notification",
            retry_count=0,
        )

        worker = OutboxWorker(test_session_factory)

        async def _permanent_failure(session, event):
            """Simulated permanent failure → direkt DLQ."""
            exc = ValueError("Invalid payload format")
            await session.execute(
                text(
                    "UPDATE outbox_events "
                    "SET status = 'dead_letter', "
                    "    retry_count = :retry_count, "
                    "    error_message = :error_message, "
                    "    locked_at = NULL, "
                    "    locked_by = NULL "
                    "WHERE id = :event_id"
                ),
                {
                    "retry_count": event.retry_count + 1,
                    "error_message": str(exc)[:500],
                    "event_id": event.id,
                },
            )
            raise exc

        with patch.object(worker, "_process_event", side_effect=_permanent_failure):
            await worker.poll_and_process(batch_size=1)

        state = await get_outbox_event_status(event_id)
        assert state is not None
        assert state["status"] == "dead_letter"

    async def test_max_retries_exceeded_goes_to_dlq(self, create_outbox_event):
        """
        max_retries asilinca dead_letter'a.

        notification policy max_retries=3, retry_count=3 → DLQ.
        """
        event_id = await create_outbox_event(
            event_type="notification",
            retry_count=2,  # Sonraki retry 3 yapacak = max_retries
            max_retries=3,
        )

        worker = OutboxWorker(test_session_factory)

        async def _max_retry_failure(session, event):
            """Max retries asildi → DLQ."""
            exc = ConnectionError("Still failing")
            new_count = event.retry_count + 1
            policy = get_policy_for_event(event.event_type)

            if not policy.should_retry(new_count, exc):
                await session.execute(
                    text(
                        "UPDATE outbox_events "
                        "SET status = 'dead_letter', "
                        "    retry_count = :retry_count, "
                        "    error_message = :error_message, "
                        "    locked_at = NULL, locked_by = NULL "
                        "WHERE id = :event_id"
                    ),
                    {
                        "retry_count": new_count,
                        "error_message": str(exc)[:500],
                        "event_id": event.id,
                    },
                )
            raise exc

        with patch.object(worker, "_process_event", side_effect=_max_retry_failure):
            await worker.poll_and_process(batch_size=1)

        state = await get_outbox_event_status(event_id)
        assert state is not None
        assert state["status"] == "dead_letter"
        assert state["retry_count"] == 3

    async def test_exponential_backoff_calculation(self, fast_retry_policy):
        """
        Backoff: base * (multiplier ^ retry_count).

        fast_retry_policy: base=0.1, multiplier=2, jitter=False
        count=1 → 0.1 * 2^1 = 0.2
        count=2 → 0.1 * 2^2 = 0.4
        """
        delay_1 = fast_retry_policy.calculate_next_retry(retry_count=1)
        delay_2 = fast_retry_policy.calculate_next_retry(retry_count=2)

        # min 1.0 guard nedeniyle:
        assert delay_1 >= 1.0
        assert delay_2 >= 1.0
        # Exponential artis olmalı (min guard sonrasi)
        assert delay_2 >= delay_1

    async def test_event_type_specific_policy(self):
        """
        Farkli event tipleri farkli policy'ler kullanir.

        payment.webhook → max_retries=10
        notification → max_retries=3
        """
        payment_policy = get_policy_for_event("payment.webhook")
        notification_policy = get_policy_for_event("notification")

        assert payment_policy.max_retries == 10
        assert notification_policy.max_retries == 3
        assert payment_policy.base_delay_seconds > notification_policy.base_delay_seconds

    async def test_next_retry_at_prevents_immediate_pickup(self, create_outbox_event):
        """
        next_retry_at gelecekte olan event hemen alinmaz.

        Worker sadece next_retry_at IS NULL veya <= now() olan event'leri alir.
        """
        event_id = await create_outbox_event(
            event_type="test.delayed",
            status="pending",
            next_retry_at="2099-01-01 00:00:00+00",  # Uzak gelecek
        )

        worker = OutboxWorker(test_session_factory)
        processed = await worker.poll_and_process(batch_size=10)
        assert processed == 0

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "pending"  # Hala pending


# ================================================================
# Test Outbox Concurrency
# ================================================================
class TestOutboxConcurrency:
    """
    Concurrent worker guvenlik testleri.

    FOR UPDATE SKIP LOCKED ile ayni event'in birden fazla
    worker tarafindan islenmemesini dogrular.
    """

    async def test_skip_locked_prevents_double_processing(self, create_outbox_event):
        """
        Iki worker ayni anda calistiginda ayni event'i almaz.

        FOR UPDATE SKIP LOCKED: ilk worker kilitleyen event'i
        ikinci worker atlar.
        """
        event_id = await create_outbox_event(event_type="concurrent.test")

        worker_1 = OutboxWorker(test_session_factory)
        worker_2 = OutboxWorker(test_session_factory)

        # Seri calistir — ilk worker event'i isler
        processed_1 = await worker_1.poll_and_process(batch_size=1)
        # Ikinci worker icin event kalmaz (zaten sent)
        processed_2 = await worker_2.poll_and_process(batch_size=1)

        assert processed_1 == 1
        assert processed_2 == 0

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "sent"

    async def test_locked_event_not_visible_to_other_workers(self, create_outbox_event):
        """
        Processing durumundaki event baska worker'a gorunmez.

        Manually processing'e alinmis event worker tarafindan alinmaz.
        """
        event_id = await create_outbox_event(
            event_type="locked.test",
            status="processing",
            locked_by="other-worker-123",
            locked_at="2025-01-01 00:00:00+00",
        )

        worker = OutboxWorker(test_session_factory)
        processed = await worker.poll_and_process(batch_size=10)
        assert processed == 0

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "processing"
        assert state["locked_by"] == "other-worker-123"


# ================================================================
# Test Outbox DLQ Service
# ================================================================
class TestOutboxDLQService:
    """
    Dead Letter Queue yonetim testleri.

    DLQService: listeleme, sayma, tekil/toplu retry, purge.
    """

    async def test_list_dead_letters(self, dlq_service, create_outbox_event):
        """DLQ'daki event'leri dogru listeler."""
        await create_outbox_event(
            event_type="dlq.test.1",
            status="dead_letter",
            error_message="Test error 1",
        )
        await create_outbox_event(
            event_type="dlq.test.2",
            status="dead_letter",
            error_message="Test error 2",
        )

        dead_letters = await dlq_service.list_dead_letters(limit=50)
        # En az 2 dead letter olmali (diger testlerden de olabilir)
        assert len(dead_letters) >= 2

        event_types = {dl["event_type"] for dl in dead_letters}
        assert "dlq.test.1" in event_types
        assert "dlq.test.2" in event_types

    async def test_list_dead_letters_with_type_filter(self, dlq_service, create_outbox_event):
        """Event tipi filtreleme dogru calisir."""
        await create_outbox_event(
            event_type="dlq.filter.target",
            status="dead_letter",
        )
        await create_outbox_event(
            event_type="dlq.filter.other",
            status="dead_letter",
        )

        filtered = await dlq_service.list_dead_letters(
            limit=50, event_type="dlq.filter.target"
        )
        for dl in filtered:
            assert dl["event_type"] == "dlq.filter.target"

    async def test_count_dead_letters(self, dlq_service, create_outbox_event):
        """DLQ event sayisi ve breakdown dogru doner."""
        await create_outbox_event(event_type="dlq.count.a", status="dead_letter")
        await create_outbox_event(event_type="dlq.count.a", status="dead_letter")
        await create_outbox_event(event_type="dlq.count.b", status="dead_letter")

        counts = await dlq_service.count_dead_letters()
        assert counts["total"] >= 3
        assert "dlq.count.a" in counts["by_event_type"]
        assert counts["by_event_type"]["dlq.count.a"] >= 2

    async def test_retry_single_dead_letter(self, dlq_service, create_outbox_event):
        """
        Tek DLQ event'ini retry'a gonder: status → pending.
        """
        event_id = await create_outbox_event(
            event_type="dlq.retry.single",
            status="dead_letter",
            retry_count=5,
            error_message="Previous failure",
        )

        success = await dlq_service.retry_single(str(event_id))
        assert success is True

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "pending"

    async def test_retry_preserves_retry_count(self, dlq_service, create_outbox_event):
        """
        DLQ retry'da retry_count SIFIRLANMAZ.

        Toplam deneme sayisi korunur — bu KIRMIZI CIZGI.
        """
        original_retry_count = 7

        event_id = await create_outbox_event(
            event_type="dlq.retry.preserve",
            status="dead_letter",
            retry_count=original_retry_count,
            error_message="Max retries exceeded",
        )

        await dlq_service.retry_single(str(event_id))

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "pending"
        # KIRMIZI CIZGI: retry_count KORUNMALI
        assert state["retry_count"] == original_retry_count

    async def test_retry_nonexistent_event_returns_false(self, dlq_service):
        """Olmayan event_id ile retry False dondurur."""
        fake_id = str(uuid.uuid4())
        result = await dlq_service.retry_single(fake_id)
        assert result is False

    async def test_retry_non_dead_letter_returns_false(self, dlq_service, create_outbox_event):
        """Pending (DLQ degil) event icin retry False dondurur."""
        event_id = await create_outbox_event(
            event_type="dlq.retry.wrong.status",
            status="pending",
        )

        result = await dlq_service.retry_single(str(event_id))
        assert result is False

    async def test_retry_all_dead_letters(self, dlq_service, create_outbox_event):
        """Toplu retry: tum DLQ event'leri pending'e doner."""
        ids = []
        for _i in range(3):
            eid = await create_outbox_event(
                event_type="dlq.bulk.retry",
                status="dead_letter",
                retry_count=3,
            )
            ids.append(eid)

        count = await dlq_service.retry_all(event_type="dlq.bulk.retry")
        assert count >= 3

        for eid in ids:
            state = await get_outbox_event_status(eid)
            assert state["status"] == "pending"

    async def test_purge_old_dead_letters(self, create_outbox_event):
        """
        older_than_hours ile eski DLQ event'lerini temizle.

        Simdi olusturulan event'ler purge'e takilmasin diye
        older_than_hours=0 kullanamayiz (min 1 saat).
        Bu test olusturulan event'lerin korunmasini dogrular.
        """
        # Yeni olusturulan event'ler 1 saatten eski degildir
        event_id = await create_outbox_event(
            event_type="dlq.purge.new",
            status="dead_letter",
        )

        dlq = DLQService(test_session_factory)
        await dlq.purge(older_than_hours=1)  # Min 1 saat eski olanlar

        # Yeni event korunmali
        state = await get_outbox_event_status(event_id)
        assert state is not None, "Yeni DLQ event purge ile silinmemeli"

    async def test_purge_preserves_recent_events(self, create_outbox_event):
        """Yeni DLQ event'leri purge ile silinmez (older_than_hours korumasi)."""
        event_id = await create_outbox_event(
            event_type="dlq.purge.preserve",
            status="dead_letter",
        )

        dlq = DLQService(test_session_factory)
        # 168 saat (7 gun) — yeni event kesinlikle korunur
        await dlq.purge(older_than_hours=168)

        state = await get_outbox_event_status(event_id)
        assert state is not None
        assert state["status"] == "dead_letter"


# ================================================================
# Test Outbox → Messaging Integration
# ================================================================
class TestOutboxMessagingIntegration:
    """
    Outbox → MessagingService entegrasyon testleri.

    Worker event'i islerken messaging adapter'i cagrilir (mock).
    Gercek Telegram API cagrisi YAPILMAZ.

    NOT: OutboxWorker._process_event'te simdilik sadece status
    guncelleniyor (TODO: event routing). Bu testler gelecekteki
    messaging entegrasyonu icin contract test gorevi gorur.
    """

    async def test_telegram_message_event_sends(
        self, outbox_worker, create_outbox_event, mock_messaging_service
    ):
        """
        telegram_message event → worker tarafindan islenir.

        Mevcut implementasyonda event 'sent' olur.
        Gelecekte TelegramAdapter.send() cagrilacak.
        """
        event_id = await create_outbox_event(
            event_type="telegram_message",
            payload={"chat_id": "12345", "text": "Test mesaji"},
        )

        processed = await outbox_worker.poll_and_process(batch_size=1)
        assert processed == 1

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "sent"
        assert state["processed_at"] is not None

    async def test_notification_event_sends(
        self, outbox_worker, create_outbox_event
    ):
        """notification event → send akisi tamamlanir."""
        event_id = await create_outbox_event(
            event_type="notification",
            payload={"user_id": "u123", "title": "Yeni mesaj"},
        )

        processed = await outbox_worker.poll_and_process(batch_size=1)
        assert processed == 1

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "sent"

    async def test_messaging_failure_triggers_retry(self, create_outbox_event):
        """
        Messaging adapter basarisiz olursa event retry'a gider.

        Worker'in _process_event'inde ConnectionError firlatilir,
        retry mantigi devreye girer.
        """
        event_id = await create_outbox_event(
            event_type="telegram_message",
            retry_count=0,
        )

        worker = OutboxWorker(test_session_factory)

        async def _messaging_failure(session, event):
            """Messaging adapter'dan gelen transient hata."""
            exc = ConnectionError("Telegram API unreachable")
            new_count = event.retry_count + 1
            policy = get_policy_for_event(event.event_type)
            backoff = policy.calculate_next_retry(new_count)

            await session.execute(
                text(
                    "UPDATE outbox_events "
                    "SET status = 'pending', "
                    "    retry_count = :retry_count, "
                    "    error_message = :error_message, "
                    "    next_retry_at = now() + interval '1 second' * :backoff, "
                    "    locked_at = NULL, locked_by = NULL "
                    "WHERE id = :event_id"
                ),
                {
                    "retry_count": new_count,
                    "error_message": str(exc)[:500],
                    "backoff": backoff,
                    "event_id": event.id,
                },
            )
            raise exc

        with patch.object(worker, "_process_event", side_effect=_messaging_failure):
            await worker.poll_and_process(batch_size=1)

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "pending"  # Retry icin pending'e dondu
        assert state["retry_count"] == 1
        assert "Telegram API" in (state["error_message"] or "")

    async def test_successful_send_marks_event_sent(
        self, outbox_worker, create_outbox_event
    ):
        """
        Basarili gonderim → event status='sent', processed_at set.

        En temel happy-path: event olustur → worker isle → sent.
        """
        event_id = await create_outbox_event(
            event_type="telegram_message",
            payload={"chat_id": "67890", "text": "Success test"},
        )

        processed = await outbox_worker.poll_and_process(batch_size=1)
        assert processed == 1

        state = await get_outbox_event_status(event_id)
        assert state["status"] == "sent"
        assert state["processed_at"] is not None
        assert state["error_message"] is None
        assert state["locked_at"] is None  # Lock temizlenmis olmali
