"""
Emlak Teknoloji Platformu - WhatsApp Cloud API Adapter (STUB)

WhatsApp Cloud API adaptoru — MessageChannel Protocol implementasyonu.

DURUM: STUB — S12'de tam implementasyon yapilacak.
    - get_capabilities() ve supports() → TAM (ADR-0007)
    - send() ve handle_webhook() → NotImplementedError

Yetenekler (Cloud API v18.0):
    - Delivery + Read receipt (mavi tik)
    - Interactive buttons (max 3)
    - HSM Template mesajlar (24 saat kurali)
    - Location, Contact, Voice, Video, Document
    - 16MB gorsel / 64MB video limiti

Lifecycle (S12'de):
    adapter = WhatsAppAdapter(
        phone_number_id="...",
        access_token="...",
    )
    registry.register("whatsapp", adapter)

NOT: isinstance(adapter, MessageChannel) kontrolu GECMELIDIR (runtime_checkable).

Referans: docs/MIMARI-KARARLAR.md, ADR-0007
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from src.modules.messaging.schemas import (
    ChannelCapabilities,
    DeliveryResult,
    IncomingMessage,
)

if TYPE_CHECKING:
    from src.modules.messaging.schemas import MessageContent

logger = structlog.get_logger(__name__)


class WhatsAppAdapter:
    """
    WhatsApp Cloud API adaptoru — MessageChannel Protocol implementasyonu (STUB).

    S12'de tam implementasyon yapilacak. Su an yalnizca capability modeli aktif.

    Metotlar (MessageChannel Protocol):
        send                → NotImplementedError (STUB)
        handle_webhook      → NotImplementedError (STUB)
        supports_rich_content → True (buton + medya + template destekli)
        get_capabilities    → TAM (ADR-0007 capability modeli)
        supports            → TAM (dinamik capability sorgusu)
    """

    def __init__(
        self,
        phone_number_id: str = "",
        access_token: str = "",
    ) -> None:
        """
        WhatsAppAdapter baslatir.

        STUB: Parametreler S12'de zorunlu olacak.

        Args:
            phone_number_id: WhatsApp Business Phone Number ID.
            access_token: Meta Graph API access token.
        """
        self._phone_number_id = phone_number_id
        self._access_token = access_token
        logger.info(
            "whatsapp_adapter_initialized",
            stub=True,
            phone_number_id=phone_number_id[:8] + "..." if phone_number_id else "(empty)",
        )

    # ================================================================
    # MessageChannel Protocol — send (STUB)
    # ================================================================

    async def send(
        self,
        recipient: str,
        content: MessageContent,
    ) -> DeliveryResult:
        """
        WhatsApp uzerinden mesaj gonderir.

        STUB: S12'de Cloud API entegrasyonu ile implement edilecek.

        Raises:
            NotImplementedError: Her zaman — STUB implementasyon.
        """
        raise NotImplementedError(
            "WhatsAppAdapter.send() henuz implement edilmedi. "
            "S12'de WhatsApp Cloud API entegrasyonu ile aktif olacak."
        )

    # ================================================================
    # MessageChannel Protocol — handle_webhook (STUB)
    # ================================================================

    async def handle_webhook(
        self,
        payload: dict,
    ) -> IncomingMessage:
        """
        WhatsApp Cloud API webhook payload'unu parse eder.

        STUB: S12'de implement edilecek.

        Raises:
            NotImplementedError: Her zaman — STUB implementasyon.
        """
        raise NotImplementedError(
            "WhatsAppAdapter.handle_webhook() henuz implement edilmedi. "
            "S12'de WhatsApp Cloud API entegrasyonu ile aktif olacak."
        )

    # ================================================================
    # MessageChannel Protocol — supports_rich_content
    # ================================================================

    def supports_rich_content(self) -> bool:
        """
        WhatsApp zengin icerik destekler: Interactive buttons, medya, template.

        Returns:
            True — her zaman.
        """
        return True

    # ================================================================
    # MessageChannel Protocol — get_capabilities (ADR-0007)
    # ================================================================

    def get_capabilities(self) -> ChannelCapabilities:
        """
        WhatsApp Cloud API yeteneklerini detayli olarak raporlar (ADR-0007).

        WhatsApp Cloud API v18.0 referans:
            - Delivery receipt: var (tek tik → cift tik)
            - Read receipt: var (mavi tik — kullanici izin verdiyse)
            - Typing indicator: YOK (Cloud API sinirlamasi)
            - Interactive buttons: max 3 buton (reply button)
            - HSM Templates: ZORUNLU (24 saat disinda sadece template gonderilebilir)
            - Medya: 16MB gorsel, 64MB video
            - Reaction API: emoji reaksiyon destegi

        Returns:
            ChannelCapabilities — WhatsApp Cloud API yetenek haritasi.
        """
        return ChannelCapabilities(
            # Temel yetenekler
            supports_delivered=True,          # Delivery receipt (tek tik → cift tik)
            supports_read=True,               # Read receipt (mavi tik)
            supports_typing_indicator=False,  # Cloud API'de typing indicator YOK
            supports_media_upload=True,       # Gorsel, video, ses, belge
            max_message_length=4096,          # WhatsApp karakter limiti

            # Zengin icerik yetenekleri
            supports_reactions=True,           # Reaction API (emoji)
            supports_thread_reply=True,        # Reply context (quoted message)
            supports_inline_buttons=True,      # Interactive reply buttons (max 3)
            supports_location=True,            # Location message
            supports_contact=True,             # Contact card (vCard)
            supports_voice=True,               # Audio message (AAC, OGG)
            supports_video=True,               # Video message (MP4)
            supports_document=True,            # Document message (PDF vb.)
            supports_templates=True,           # HSM templates (24h kurali — ZORUNLU)
            supports_callback_query=False,     # WhatsApp'ta callback query yok

            # Kanal sinirlari
            max_buttons_per_message=3,         # WhatsApp max 3 reply button
            max_media_size_mb=16.0,            # 16MB gorsel, 64MB video (en dusuk limit)
            supported_media_types=[
                "image/jpeg",
                "image/png",
                "video/mp4",
                "audio/ogg",
                "audio/aac",
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ],

            # Metadata
            channel_name="whatsapp",
            channel_version="Cloud API v18.0",
            last_capability_check=datetime.now(UTC).isoformat(),
        )

    # ================================================================
    # MessageChannel Protocol — supports (ADR-0007)
    # ================================================================

    def supports(self, capability: str) -> bool:
        """
        Dinamik capability sorgusu — get_capabilities() uzerinden delege eder.

        Args:
            capability: Yetenek adi ("supports_" prefix'i olmadan).

        Returns:
            True — WhatsApp bu yetenegi destekliyorsa.
        """
        return self.get_capabilities().supports(capability)
