"""
Emlak Teknoloji Platformu - Inbox Service

Inbox pattern: Gelen event'lerin idempotent işlenmesini sağlar.
UNIQUE constraint violation durumunda None döner (duplicate event).
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.inbox_event import InboxEvent

logger = logging.getLogger(__name__)


class InboxService:
    """
    Inbox event kayıt servisi.

    event_id UNIQUE constraint sayesinde aynı event birden fazla
    kez işlenmez (idempotency).
    """

    async def receive_event(
        self,
        session: AsyncSession,
        event_id: str,
        source: str,
        event_type: str,
        payload: dict,
        office_id: uuid.UUID | None = None,
    ) -> InboxEvent | None:
        """
        Yeni bir inbox event kaydet.

        Args:
            session: Aktif veritabanı session'ı.
            event_id: Kaynak sistemdeki benzersiz event ID.
            source: Event kaynağı.
            event_type: Event tipi.
            payload: Event payload (dict).
            office_id: Bağlı ofis ID (opsiyonel).

        Returns:
            InboxEvent: Başarılı kayıt.
            None: Duplicate event (zaten mevcut).
        """
        inbox_event = InboxEvent(
            event_id=event_id,
            source=source,
            event_type=event_type,
            payload=payload,
            office_id=office_id,
        )

        try:
            session.add(inbox_event)
            await session.flush()
            logger.info(
                "Inbox event kaydedildi: event_id=%s source=%s type=%s",
                event_id,
                source,
                event_type,
            )
            return inbox_event
        except IntegrityError:
            await session.rollback()
            logger.warning(
                "Duplicate inbox event atlandı: event_id=%s source=%s",
                event_id,
                source,
            )
            return None
