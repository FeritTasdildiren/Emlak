"""
Emlak Teknoloji Platformu - Messaging Gateway Abstract Interface

MessageChannel Protocol: tum kanal adaptorlerinin uygulamasi gereken arayuz.

runtime_checkable dekoratoru sayesinde isinstance() kontrolu yapilabilir:
    if isinstance(adapter, MessageChannel):
        await adapter.send(recipient, content)

Yeni kanal eklemek icin:
    1. Bu Protocol'u uygulayan bir adaptor yazin
    2. ChannelRegistry'ye kaydedin
    3. Adaptorun get_capabilities() metodunu dogru doldurun

Referans: docs/MIMARI-KARARLAR.md, ADR-0007
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.modules.messaging.schemas import (
        ChannelCapabilities,
        DeliveryResult,
        IncomingMessage,
        MessageContent,
    )


@runtime_checkable
class MessageChannel(Protocol):
    """
    Mesajlasma kanal adaptoru icin abstract interface.

    Tum kanal uygulamalari (Telegram, WhatsApp, vb.) bu Protocol'u
    saglamalidir. runtime_checkable sayesinde isinstance() ile
    dogrulama yapilabilir.

    Metotlar:
        send                — mesaj gonder
        handle_webhook      — gelen webhook payload'unu isle
        supports_rich_content — zengin icerik (buton, medya) destegi
        get_capabilities    — kanalin yeteneklerini raporla (ADR-0007)
        supports            — dinamik capability sorgusu (ADR-0007)
    """

    async def send(
        self,
        recipient: str,
        content: MessageContent,
    ) -> DeliveryResult:
        """
        Belirtilen aliciya mesaj gonderir.

        Args:
            recipient: Alicinin kanal bazli benzersiz ID'si
                       (Telegram chat_id, WhatsApp phone_number, vb.)
            content: Gonderilecek mesaj icerigi.

        Returns:
            DeliveryResult — gonderim sonucu (basari/hata).
        """
        ...

    async def handle_webhook(
        self,
        payload: dict,
    ) -> IncomingMessage:
        """
        Kanaldan gelen webhook payload'unu parse edip IncomingMessage'e donusturur.

        Args:
            payload: Kanalin gonderdigi ham webhook verisi.

        Returns:
            IncomingMessage — normalize edilmis gelen mesaj.

        Raises:
            ValueError: Gecersiz veya parse edilemeyen payload.
        """
        ...

    def supports_rich_content(self) -> bool:
        """
        Kanalin zengin icerik (buton, medya, template) destekleyip desteklemedigini dondurur.

        Returns:
            True → butonlar, medya, template'ler gonderilebilir.
            False → sadece duz metin desteklenir.
        """
        ...

    def get_capabilities(self) -> ChannelCapabilities:
        """
        Kanalin destekledigi yetenekleri raporlar (ADR-0007).

        Capability-aware tasarim: servis katmani bu bilgiyi kullanarak
        kanala uygun mesaj formati secebilir. UI bu bilgiyle dinamik
        ozellik gosterimi yapabilir.

        Returns:
            ChannelCapabilities — kanalin yetenek haritasi.
        """
        ...

    def supports(self, capability: str) -> bool:
        """
        Dinamik capability sorgusu (ADR-0007).

        get_capabilities().supports() icin kolaylik metodu.
        Her adaptor bu metodu uygulamalidir.

        Kullanim:
            if adapter.supports("inline_buttons"):
                content.buttons = [...]

        Args:
            capability: Yetenek adi ("supports_" prefix'i olmadan).

        Returns:
            True — yetenek destekleniyor, False — desteklenmiyor.
        """
        ...
