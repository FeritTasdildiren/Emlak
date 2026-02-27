"""
Emlak Teknoloji Platformu - Matching Celery Tasks

İlan/müşteri eşleştirme tetikleme ve bildirim gönderimi.

Tasks:
    trigger_matching_for_property  — Yeni ilan için eşleştirme + bildirim
    trigger_matching_for_customer  — Yeni müşteri için eşleştirme + bildirim

Mimari Kararlar:
    - asyncio.run() ile async MatchingService çağrılır (Celery prefork → event loop yok)
    - async_session_factory kullanılır (asyncpg)
    - Bildirim hataları matching'i BOZMAZ (ayrı try/except, ayrı transaction)
    - Idempotent: UPSERT sayesinde aynı ID ile tekrar çağrılabilir
    - TelegramAdapter task başına oluşturulur/kapatılır (HTTP session leak yok)

Kuyruğu: default
Retry: max 2, exponential backoff

Referans: TASK-111, S7.7, S7.8
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid as uuid_mod
from typing import TYPE_CHECKING, Any

import structlog

from src.celery_app import celery_app
from src.tasks.base import BaseTask

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


# ================================================================
# Notification Helper (async, internal)
# ================================================================


async def _send_match_notifications(
    db: AsyncSession,
    matches: list[dict],
    office_id: uuid_mod.UUID,
) -> int:
    """
    Eşleşme sonrası bildirim gönderir.

    Her eşleşme için:
        1. In-app bildirim → müşteriyi yöneten danışmana (agent)
        2. Telegram bildirimi → danışmanın telegram_chat_id'si varsa

    Bildirim hataları sessizce loglanır, matching kayıtlarını BOZMAZ.
    Tüm DB sorguları batch olarak yapılır (N+1 yok).

    Args:
        db: Async database session (commit çağrılmaz, çağıran yapar).
        matches: MatchingService'den dönen match record listesi.
        office_id: Tenant UUID.

    Returns:
        Başarıyla gönderilen in-app bildirim sayısı.
    """
    if not matches:
        return 0

    from sqlalchemy import select

    from src.config import settings
    from src.models.customer import Customer
    from src.models.match import PropertyCustomerMatch
    from src.models.property import Property
    from src.models.user import User
    from src.modules.messaging.schemas import MessageContent
    from src.modules.notifications.service import NotificationService

    sent_count = 0
    telegram_adapter = None

    try:
        # --- TelegramAdapter oluştur (bot token varsa) ---
        if settings.TELEGRAM_BOT_TOKEN:
            from src.modules.messaging.adapters.telegram import TelegramAdapter

            telegram_adapter = TelegramAdapter(
                bot_token=settings.TELEGRAM_BOT_TOKEN,
            )

        # --- Batch fetch: customers ---
        customer_ids = list({m["customer_id"] for m in matches})
        result = await db.execute(
            select(Customer).where(Customer.id.in_(customer_ids)),
        )
        customers_map: dict[uuid_mod.UUID, Customer] = {
            c.id: c for c in result.scalars().all()
        }

        # --- Batch fetch: properties ---
        property_ids = list({m["property_id"] for m in matches})
        result = await db.execute(
            select(Property).where(Property.id.in_(property_ids)),
        )
        properties_map: dict[uuid_mod.UUID, Property] = {
            p.id: p for p in result.scalars().all()
        }

        # --- Batch fetch: agents (müşterilerin danışmanları) ---
        agent_ids = list(
            {c.agent_id for c in customers_map.values() if c.agent_id},
        )
        agents_map: dict[uuid_mod.UUID, User] = {}
        if agent_ids:
            result = await db.execute(
                select(User).where(User.id.in_(agent_ids)),
            )
            agents_map = {a.id: a for a in result.scalars().all()}

        # --- Batch fetch: match IDs (notification data için) ---
        match_id_lookup: dict[tuple[uuid_mod.UUID, uuid_mod.UUID], uuid_mod.UUID] = {}
        if property_ids and customer_ids:
            result = await db.execute(
                select(
                    PropertyCustomerMatch.id,
                    PropertyCustomerMatch.property_id,
                    PropertyCustomerMatch.customer_id,
                ).where(
                    PropertyCustomerMatch.office_id == office_id,
                    PropertyCustomerMatch.property_id.in_(property_ids),
                    PropertyCustomerMatch.customer_id.in_(customer_ids),
                ),
            )
            for row in result.all():
                match_id_lookup[(row.property_id, row.customer_id)] = row.id

        # --- Her eşleşme için bildirim gönder ---
        for match_record in matches:
            try:
                customer_id = match_record["customer_id"]
                property_id = match_record["property_id"]
                score = match_record["score"]

                customer = customers_map.get(customer_id)
                prop = properties_map.get(property_id)

                if not customer or not customer.agent_id or not prop:
                    continue

                agent = agents_map.get(customer.agent_id)
                if not agent:
                    continue

                match_id = match_id_lookup.get((property_id, customer_id))
                address = prop.address or prop.title or str(prop.id)
                customer_name = customer.full_name or "Bilinmeyen"

                # ── In-app bildirim ──
                await NotificationService.create(
                    db=db,
                    user_id=agent.id,
                    office_id=office_id,
                    type="new_match",
                    title=f"Yeni Eşleşme: {address}",
                    body=f"{customer_name} ile %{score} uyum",
                    data={
                        "match_id": str(match_id) if match_id else None,
                        "property_id": str(property_id),
                        "customer_id": str(customer_id),
                        "score": score,
                    },
                )
                sent_count += 1

                # ── Telegram bildirim (opsiyonel) ──
                if telegram_adapter and agent.telegram_chat_id:
                    try:
                        telegram_text = (
                            "🔔 Yeni Eşleşme!\n"
                            f"İlan: {address}\n"
                            f"Müşteri: {customer_name}\n"
                            f"Uyum: %{score}"
                        )
                        content = MessageContent(text=telegram_text)
                        await telegram_adapter.send(
                            recipient=agent.telegram_chat_id,
                            content=content,
                        )
                    except Exception:
                        logger.warning(
                            "telegram_match_notification_failed",
                            agent_id=str(agent.id),
                            customer_id=str(customer_id),
                            exc_info=True,
                        )

            except Exception:
                logger.warning(
                    "match_notification_failed",
                    customer_id=str(match_record.get("customer_id")),
                    property_id=str(match_record.get("property_id")),
                    exc_info=True,
                )
                continue

    finally:
        # TelegramAdapter HTTP session cleanup
        if telegram_adapter:
            with contextlib.suppress(Exception):
                await telegram_adapter.close()

    return sent_count


# ================================================================
# Async Runner Functions
# ================================================================


async def _run_matching_for_property(
    property_id: uuid_mod.UUID,
    office_id: uuid_mod.UUID,
) -> dict[str, Any]:
    """
    Property için eşleştirme + bildirim (async worker).

    İki ayrı transaction:
        1. Matching → commit (kalıcı)
        2. Notifications → commit (hata olsa bile matching korunur)
    """
    from src.database import async_session_factory
    from src.modules.matches.matching_service import MatchingService

    async with async_session_factory() as db:
        # ── 1. Matching (ana iş) ──
        matches = await MatchingService.find_matches_for_property(
            db, property_id, office_id,
        )
        await db.commit()

        # ── 2. Bildirimler (ayrı transaction) ──
        notification_count = 0
        if matches:
            try:
                notification_count = await _send_match_notifications(
                    db, matches, office_id,
                )
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception(
                    "match_notification_batch_error",
                    property_id=str(property_id),
                    office_id=str(office_id),
                )

        return {
            "matches_count": len(matches),
            "notification_count": notification_count,
        }


async def _run_matching_for_customer(
    customer_id: uuid_mod.UUID,
    office_id: uuid_mod.UUID,
) -> dict[str, Any]:
    """
    Customer için eşleştirme + bildirim (async worker).

    İki ayrı transaction:
        1. Matching → commit (kalıcı)
        2. Notifications → commit (hata olsa bile matching korunur)
    """
    from src.database import async_session_factory
    from src.modules.matches.matching_service import MatchingService

    async with async_session_factory() as db:
        # ── 1. Matching (ana iş) ──
        matches = await MatchingService.find_matches_for_customer(
            db, customer_id, office_id,
        )
        await db.commit()

        # ── 2. Bildirimler (ayrı transaction) ──
        notification_count = 0
        if matches:
            try:
                notification_count = await _send_match_notifications(
                    db, matches, office_id,
                )
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception(
                    "match_notification_batch_error",
                    customer_id=str(customer_id),
                    office_id=str(office_id),
                )

        return {
            "matches_count": len(matches),
            "notification_count": notification_count,
        }


# ================================================================
# Celery Tasks
# ================================================================


@celery_app.task(
    bind=True,
    base=BaseTask,
    queue="default",
    name="src.modules.matches.tasks.trigger_matching_for_property",
    max_retries=2,
)
def trigger_matching_for_property(
    self: BaseTask,
    property_id: str,
    office_id: str,
) -> dict[str, Any]:
    """
    İlan için eşleştirme Celery task'ı.

    Yeni ilan oluşturulduğunda veya güncellendiğinde çağrılır.
    Tüm uyumlu müşterilerle eşleştirme yapar ve bildirim gönderir.

    Idempotent: Aynı property_id ile tekrar çağrılabilir (UPSERT).

    Args:
        property_id: İlan UUID (string — JSON serialization).
        office_id: Tenant UUID (string — JSON serialization).

    Returns:
        dict: matches_count, notification_count, elapsed_ms
    """
    start_time = time.monotonic()

    self.log.info(
        "matching_task_started",
        property_id=property_id,
        office_id=office_id,
        trigger="property",
    )

    result = asyncio.run(
        _run_matching_for_property(
            uuid_mod.UUID(property_id),
            uuid_mod.UUID(office_id),
        ),
    )

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    self.log.info(
        "matching_task_completed",
        property_id=property_id,
        office_id=office_id,
        matches_count=result["matches_count"],
        notification_count=result["notification_count"],
        elapsed_ms=elapsed_ms,
    )

    return {
        **result,
        "elapsed_ms": elapsed_ms,
        "property_id": property_id,
        "office_id": office_id,
    }


@celery_app.task(
    bind=True,
    base=BaseTask,
    queue="default",
    name="src.modules.matches.tasks.trigger_matching_for_customer",
    max_retries=2,
)
def trigger_matching_for_customer(
    self: BaseTask,
    customer_id: str,
    office_id: str,
) -> dict[str, Any]:
    """
    Müşteri için eşleştirme Celery task'ı.

    Yeni müşteri oluşturulduğunda çağrılır.
    Tüm uyumlu ilanlarla eşleştirme yapar ve bildirim gönderir.

    Idempotent: Aynı customer_id ile tekrar çağrılabilir (UPSERT).

    Args:
        customer_id: Müşteri UUID (string — JSON serialization).
        office_id: Tenant UUID (string — JSON serialization).

    Returns:
        dict: matches_count, notification_count, elapsed_ms
    """
    start_time = time.monotonic()

    self.log.info(
        "matching_task_started",
        customer_id=customer_id,
        office_id=office_id,
        trigger="customer",
    )

    result = asyncio.run(
        _run_matching_for_customer(
            uuid_mod.UUID(customer_id),
            uuid_mod.UUID(office_id),
        ),
    )

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    self.log.info(
        "matching_task_completed",
        customer_id=customer_id,
        office_id=office_id,
        matches_count=result["matches_count"],
        notification_count=result["notification_count"],
        elapsed_ms=elapsed_ms,
    )

    return {
        **result,
        "elapsed_ms": elapsed_ms,
        "customer_id": customer_id,
        "office_id": office_id,
    }
