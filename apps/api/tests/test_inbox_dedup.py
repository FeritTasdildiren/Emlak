"""
Emlak Teknoloji Platformu - Inbox Deduplication Tests

InboxService.receive_event() idempotency mekanizmasi testleri.

Test Kategorileri:
    A) Temel Dedup — ilk event kabul, duplicate reddedilir
    B) Edge Cases — farkli event_id, farkli source, alan dogrulamasi
    C) Concurrent — eszamanli ayni event_id → sadece biri basarili

Altyapi:
    - Gercek DB UNIQUE constraint test edilir (mock DEGIL)
    - IntegrityError yakalamasi dogrulanir
    - clean_inbox_events fixture ile test sonrasi temizlik

Referanslar:
    - src/services/inbox_service.py — InboxService.receive_event()
    - src/models/inbox_event.py — InboxEvent (event_id UNIQUE)
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from src.models.inbox_event import InboxEvent
from src.services.inbox_service import InboxService
from tests.conftest import OFFICE_A_ID, test_session_factory

# ================================================================
# A) Temel Dedup Testleri
# ================================================================


class TestInboxDeduplication:
    """Inbox event dedup mekanizmasi."""

    async def test_first_event_accepted(
        self, db_session, inbox_service, clean_inbox_events
    ) -> None:
        """
        Ilk event_id → InboxEvent olusturulur, None DEGIL doner.

        receive_event basarili INSERT + flush yapar ve InboxEvent dondurur.
        """
        event_id = f"first-{uuid.uuid4().hex[:8]}"

        result = await inbox_service.receive_event(
            session=db_session,
            event_id=event_id,
            source="test",
            event_type="test.first",
            payload={"number": 1},
        )

        assert result is not None, "Ilk event kabul edilmeli (None DEGIL)"
        assert isinstance(result, InboxEvent)
        assert result.event_id == event_id

    async def test_duplicate_event_rejected(
        self, clean_inbox_events
    ) -> None:
        """
        Ayni event_id → None doner (IntegrityError yakalanir).

        UNIQUE constraint violation:
            1. Session 1: INSERT event_id='X' → basarili (COMMITTED)
            2. Session 2: INSERT event_id='X' → IntegrityError → None

        NOT: Ayri session'lar kullanilir cunku receive_event
        IntegrityError'da session.rollback() cagirir.
        """
        event_id = f"dup-{uuid.uuid4().hex[:8]}"
        inbox_svc = InboxService()

        # 1. Ilk event — commit et
        async with test_session_factory() as session1:
            result1 = await inbox_svc.receive_event(
                session=session1,
                event_id=event_id,
                source="test",
                event_type="test.dup",
                payload={"attempt": 1},
            )
            assert result1 is not None
            await session1.commit()

        # 2. Duplicate event — ayni event_id
        async with test_session_factory() as session2:
            result2 = await inbox_svc.receive_event(
                session=session2,
                event_id=event_id,
                source="test",
                event_type="test.dup",
                payload={"attempt": 2},
            )
            assert result2 is None, "Duplicate event_id icin None donmeli"

    async def test_different_event_ids_both_accepted(
        self, db_session, inbox_service, clean_inbox_events
    ) -> None:
        """
        Farkli event_id'ler → ikisi de kabul edilir.

        event_id UNIQUE constraint farkli key'ler icin catisma uretmez.
        """
        event_id_1 = f"diff-a-{uuid.uuid4().hex[:8]}"
        event_id_2 = f"diff-b-{uuid.uuid4().hex[:8]}"

        result1 = await inbox_service.receive_event(
            session=db_session,
            event_id=event_id_1,
            source="test",
            event_type="test.diff",
            payload={"n": 1},
        )

        result2 = await inbox_service.receive_event(
            session=db_session,
            event_id=event_id_2,
            source="test",
            event_type="test.diff",
            payload={"n": 2},
        )

        assert result1 is not None, "Ilk event kabul edilmeli"
        assert result2 is not None, "Ikinci (farkli) event de kabul edilmeli"
        assert result1.event_id != result2.event_id

    async def test_dedup_across_sources(
        self, clean_inbox_events
    ) -> None:
        """
        Ayni event_id, farkli source → UNIQUE constraint event_id ustunde.

        Mevcut model tasarimi: event_id alani GLOBALLY unique.
        Yani ayni event_id farkli source'lardan gelse bile reddedilir.
        Bu, event_id'nin kaynak sistem tarafindan globally unique
        uretilmesini gerektirir (ki iyzico bunu garanti eder).
        """
        event_id = f"cross-src-{uuid.uuid4().hex[:8]}"
        inbox_svc = InboxService()

        # Source A: iyzico
        async with test_session_factory() as session:
            result_a = await inbox_svc.receive_event(
                session=session,
                event_id=event_id,
                source="iyzico",
                event_type="payment.success",
                payload={"from": "iyzico"},
            )
            await session.commit()

        # Source B: test — ayni event_id
        async with test_session_factory() as session:
            result_b = await inbox_svc.receive_event(
                session=session,
                event_id=event_id,
                source="test",
                event_type="test.event",
                payload={"from": "test"},
            )

        assert result_a is not None, "Ilk source kabul edilmeli"
        assert result_b is None, (
            "Ayni event_id farkli source'tan gelse bile reddedilmeli "
            "(UNIQUE constraint event_id ustunde)"
        )


# ================================================================
# B) Edge Cases & Alan Dogrulamasi
# ================================================================


class TestInboxEventFields:
    """InboxEvent alan dogrulamalari."""

    async def test_inbox_event_fields_populated(
        self, db_session, inbox_service, clean_inbox_events
    ) -> None:
        """
        Olusturulan InboxEvent'te tum alanlar dogru:
        event_id, source, event_type, payload, office_id, status.
        """
        event_id = f"fields-{uuid.uuid4().hex[:8]}"
        test_payload = {"amount": 299.00, "currency": "TRY"}

        result = await inbox_service.receive_event(
            session=db_session,
            event_id=event_id,
            source="iyzico",
            event_type="payment.success",
            payload=test_payload,
            office_id=OFFICE_A_ID,
        )

        assert result is not None

        # Alan dogrulamalari
        assert result.event_id == event_id
        assert result.source == "iyzico"
        assert result.event_type == "payment.success"
        assert result.payload == test_payload
        assert result.office_id == OFFICE_A_ID
        assert result.status == "received", "Varsayilan status 'received' olmali"
        assert result.processed_at is None, "Yeni event'te processed_at None olmali"
        assert result.error_message is None, "Yeni event'te error_message None olmali"

    async def test_inbox_event_without_office_id(
        self, db_session, inbox_service, clean_inbox_events
    ) -> None:
        """
        office_id None → platform-level event olarak kaydedilir.

        InboxEvent.office_id NULLABLE — webhook'lar tenant-agnostic olabilir.
        """
        event_id = f"no-office-{uuid.uuid4().hex[:8]}"

        result = await inbox_service.receive_event(
            session=db_session,
            event_id=event_id,
            source="test",
            event_type="system.event",
            payload={},
            office_id=None,
        )

        assert result is not None
        assert result.office_id is None


# ================================================================
# C) Concurrent Dedup Testi
# ================================================================


class TestConcurrentDedup:
    """Eszamanli duplicate event isleme."""

    async def test_concurrent_duplicate_events(
        self, clean_inbox_events
    ) -> None:
        """
        Eszamanli ayni event_id → sadece biri basarili.

        asyncio.gather ile iki coroutine ayni event_id'yi
        ayni anda eklemeye calisir. PostgreSQL UNIQUE constraint
        sadece birinin basarili olmasini garanti eder.

        Beklenti:
            - 1 coroutine → InboxEvent (basarili)
            - 1 coroutine → None (duplicate IntegrityError)
        """
        event_id = f"concurrent-{uuid.uuid4().hex[:8]}"
        inbox_svc = InboxService()

        async def attempt_insert() -> InboxEvent | None:
            """Tek bir INSERT denemesi — kendi session'i icinde."""
            async with test_session_factory() as session:
                result = await inbox_svc.receive_event(
                    session=session,
                    event_id=event_id,
                    source="test",
                    event_type="test.concurrent",
                    payload={"concurrent": True},
                )
                if result is not None:
                    await session.commit()
                return result

        # Iki coroutine eszamanli calistir
        results = await asyncio.gather(
            attempt_insert(),
            attempt_insert(),
            return_exceptions=True,
        )

        # Sonuclari analiz et
        successes = [
            r for r in results
            if isinstance(r, InboxEvent)
        ]
        nones = [r for r in results if r is None]
        exceptions = [r for r in results if isinstance(r, Exception)]

        assert len(successes) == 1, (
            f"Sadece 1 INSERT basarili olmali — "
            f"{len(successes)} basarili, {len(nones)} None, "
            f"{len(exceptions)} exception"
        )
        assert len(nones) + len(exceptions) >= 1, (
            "Ikinci deneme None veya Exception ile sonuclanmali"
        )

        # DB'de sadece 1 kayit olmali
        async with test_session_factory() as session:
            result = await session.execute(
                select(InboxEvent).where(InboxEvent.event_id == event_id)
            )
            events = result.scalars().all()
            assert len(events) == 1, (
                f"DB'de sadece 1 InboxEvent olmali, {len(events)} bulundu"
            )
