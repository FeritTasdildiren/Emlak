"""
Emlak Teknoloji Platformu - Outbox Worker

Transactional Outbox pattern worker: pending event'leri poll eder,
FOR UPDATE SKIP LOCKED ile kilitler ve isler.

Retry Politikasi (TASK-041):
    - Event tipi bazinda konfigüre edilebilir RetryPolicy
    - Exponential backoff + jitter (thundering herd korunmasi)
    - Error classification: transient (retry) vs permanent (DLQ)
    - max_delay_seconds ust siniri (sonsuz bekleme yok)

Kullanim:
    worker = OutboxWorker(async_session_factory)
    processed = await worker.poll_and_process(batch_size=10)
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.services.retry_policy import (
    RetryPolicy,
    classify_exception,
    get_policy_for_event,
)

logger = logging.getLogger(__name__)


class OutboxWorker:
    """
    Outbox event'lerini poll edip isleyen worker.

    FOR UPDATE SKIP LOCKED kullanarak birden fazla worker
    instance'inin ayni anda calismasina olanak tanir.

    Error Classification (TASK-041):
        - Transient (ConnectionError, TimeoutError, 5xx) -> retry
        - Permanent (ValidationError, 4xx, AuthError) -> direkt DLQ
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._worker_id = f"worker-{uuid.uuid4().hex[:8]}"

    async def poll_and_process(self, batch_size: int = 10) -> int:
        """
        Pending event'leri poll et ve isle.

        Returns:
            Islenen event sayisi.
        """
        async with self._session_factory() as session, session.begin():
            events = await self._acquire_events(session, batch_size)
            if not events:
                return 0

            processed = 0
            for event in events:
                try:
                    await self._process_event(session, event)
                    processed += 1
                except Exception:
                    logger.exception(
                        "Outbox event isleme hatasi: event_id=%s",
                        event.id,
                    )

            return processed

    async def _acquire_events(
        self, session: AsyncSession, batch_size: int
    ) -> list:
        """
        FOR UPDATE SKIP LOCKED ile pending event'leri kilitle.

        Ayni anda calisan birden fazla worker birbirini bloklamaz;
        her worker farkli event'leri alir.

        Subquery pattern: once SELECT ile id'leri sec (SKIP LOCKED),
        sonra UPDATE ile kilitle. Bu pattern buyuk tablolarda
        lock contention'i minimize eder.
        """
        result = await session.execute(
            text(
                "UPDATE outbox_events "
                "SET status = 'processing', "
                "    locked_at = now(), "
                "    locked_by = :worker_id "
                "WHERE id IN ("
                "    SELECT id FROM outbox_events "
                "    WHERE status = 'pending' "
                "      AND (next_retry_at IS NULL OR next_retry_at <= now()) "
                "    ORDER BY created_at "
                "    FOR UPDATE SKIP LOCKED "
                "    LIMIT :batch_size"
                ") "
                "RETURNING *"
            ),
            {"worker_id": self._worker_id, "batch_size": batch_size},
        )
        return result.fetchall()

    async def _process_event(self, session: AsyncSession, event) -> None:
        """
        Tek bir outbox event'ini isle.

        Basarili -> status='sent', processed_at=now()
        Basarisiz ->
            - Transient hata: retry_count artir, exponential backoff ile next_retry_at
            - Permanent hata: direkt dead_letter (retry atlanir)
            - Max retries asildi: dead_letter

        Error Classification (TASK-041):
            1. Exception siniflandirilir (transient/permanent/unknown)
            2. Event tipine gore RetryPolicy secilir
            3. Policy.should_retry() ile karar verilir
            4. Policy.calculate_next_retry() ile delay hesaplanir
        """
        # Event tipine gore retry policy sec
        policy: RetryPolicy = get_policy_for_event(event.event_type)

        try:
            # TODO: Event routing — event_type'a gore handler dispatch
            # Simdilik sadece status guncellemesi yapilir.
            # Gercek implementasyonda burada event publish (Redis, RabbitMQ vb.) yapilir.
            logger.info(
                "Outbox event isleniyor: type=%s aggregate=%s/%s worker=%s",
                event.event_type,
                event.aggregate_type,
                event.aggregate_id,
                self._worker_id,
            )

            await session.execute(
                text(
                    "UPDATE outbox_events "
                    "SET status = 'sent', "
                    "    processed_at = now(), "
                    "    error_message = NULL "
                    "WHERE id = :event_id"
                ),
                {"event_id": event.id},
            )

        except Exception as e:
            new_retry_count = event.retry_count + 1
            error_classification = classify_exception(e)

            # Karar: Retry mi DLQ mi?
            if not policy.should_retry(new_retry_count, e):
                # --- DLQ: Max retries asildi VEYA permanent hata ---
                reason = (
                    "permanent_error"
                    if error_classification == "permanent"
                    else "max_retries_exceeded"
                )

                logger.warning(
                    "Outbox event DLQ'ya gonderiliyor: event_id=%s type=%s "
                    "reason=%s classification=%s retry_count=%d/%d error=%s",
                    event.id,
                    event.event_type,
                    reason,
                    error_classification,
                    new_retry_count,
                    policy.max_retries,
                    str(e)[:200],
                )

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
                        "retry_count": new_retry_count,
                        "error_message": str(e)[:500],
                        "event_id": event.id,
                    },
                )
            else:
                # --- RETRY: Transient hata, tekrar dene ---
                backoff_seconds = policy.calculate_next_retry(new_retry_count)

                logger.info(
                    "Outbox event retry zamanlanacak: event_id=%s type=%s "
                    "classification=%s retry_count=%d/%d backoff=%.1fs",
                    event.id,
                    event.event_type,
                    error_classification,
                    new_retry_count,
                    policy.max_retries,
                    backoff_seconds,
                )

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
                        "error_message": str(e)[:500],
                        "backoff": backoff_seconds,
                        "event_id": event.id,
                    },
                )
            raise
