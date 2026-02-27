"""
Emlak Teknoloji Platformu - Channel Registry

Kanal adaptorlerinin merkezi kayit ve erisim noktasi.

Kullanim:
    registry = ChannelRegistry()

    # Adaptor kaydi
    registry.register("telegram", TelegramAdapter())
    registry.register("whatsapp", WhatsAppAdapter())

    # Adaptor erisimi
    adapter = registry.get("telegram")
    await adapter.send(recipient, content)

    # Tum kanallar
    channels = registry.list_channels()  # ["telegram", "whatsapp"]

    # Kanal yetenekleri
    caps = registry.get_capabilities("whatsapp")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.modules.messaging.gateway import MessageChannel

if TYPE_CHECKING:
    from src.modules.messaging.schemas import ChannelCapabilities

logger = structlog.get_logger(__name__)


class ChannelRegistry:
    """
    Kanal adaptorlerinin merkezi registry'si.

    Thread-safe degildir — uygulama baslangicinda (lifespan) kayit yapilir,
    runtime'da sadece okuma yapilir. Bu pattern FastAPI uygulamalarinda guvenlidir.
    """

    def __init__(self) -> None:
        self._channels: dict[str, MessageChannel] = {}

    def register(self, name: str, adapter: MessageChannel) -> None:
        """
        Kanal adaptoru kaydeder.

        Args:
            name: Kanal adi (ornek: "telegram", "whatsapp").
                  Kucuk harf, benzersiz olmali.
            adapter: MessageChannel Protocol'unu saglayan adaptor instance'i.

        Raises:
            TypeError: Adaptor MessageChannel Protocol'unu saglamiyorsa.
            ValueError: Ayni isimde kanal zaten kayitliysa.
        """
        if not isinstance(adapter, MessageChannel):
            raise TypeError(
                f"Adaptor MessageChannel Protocol'unu saglamiyor: {type(adapter).__name__}"
            )

        name_lower = name.lower()

        if name_lower in self._channels:
            raise ValueError(
                f"'{name_lower}' kanali zaten kayitli. "
                f"Mevcut adaptor: {type(self._channels[name_lower]).__name__}"
            )

        self._channels[name_lower] = adapter
        logger.info(
            "channel_registered",
            channel=name_lower,
            adapter=type(adapter).__name__,
            capabilities=adapter.get_capabilities().model_dump(),
        )

    def get(self, name: str) -> MessageChannel:
        """
        Kayitli kanal adaptorunu dondurur.

        Args:
            name: Kanal adi.

        Returns:
            MessageChannel — kayitli adaptor.

        Raises:
            KeyError: Kanal kayitli degilse.
        """
        name_lower = name.lower()
        if name_lower not in self._channels:
            available = ", ".join(self._channels.keys()) or "(bos)"
            raise KeyError(
                f"'{name_lower}' kanali kayitli degil. Mevcut kanallar: {available}"
            )
        return self._channels[name_lower]

    def list_channels(self) -> list[str]:
        """
        Kayitli tum kanal adlarini dondurur.

        Returns:
            Kanal adlari listesi (sirali).
        """
        return sorted(self._channels.keys())

    def get_capabilities(self, name: str) -> ChannelCapabilities:
        """
        Belirtilen kanalin yeteneklerini dondurur.

        Args:
            name: Kanal adi.

        Returns:
            ChannelCapabilities — kanalin yetenek haritasi.

        Raises:
            KeyError: Kanal kayitli degilse.
        """
        adapter = self.get(name)
        return adapter.get_capabilities()

    # ================================================================
    # Capability sorgu API (ADR-0007)
    # ================================================================

    def get_all_capabilities(self) -> dict[str, ChannelCapabilities]:
        """
        Tum kayitli kanallarin yeteneklerini dondurur (ADR-0007).

        Kullanim:
            all_caps = registry.get_all_capabilities()
            for name, caps in all_caps.items():
                print(f"{name}: read={caps.supports('read')}")

        Returns:
            dict — kanal_adi → ChannelCapabilities eslesmesi.
        """
        return {
            name: adapter.get_capabilities()
            for name, adapter in self._channels.items()
        }

    def get_channels_supporting(self, capability: str) -> list[str]:
        """
        Belirli bir yetenegi destekleyen kanallari listeler (ADR-0007).

        Kullanim:
            # Read receipt destekleyen kanallar
            channels = registry.get_channels_supporting("read")
            # → ["whatsapp"]

            # Template destekleyen kanallar
            channels = registry.get_channels_supporting("templates")
            # → ["whatsapp"]

        Args:
            capability: Yetenek adi ("supports_" prefix'i olmadan).
                        Ornek: "read", "inline_buttons", "templates"

        Returns:
            Yetenegi destekleyen kanal adlari listesi (sirali).
        """
        return sorted(
            name
            for name, adapter in self._channels.items()
            if adapter.get_capabilities().supports(capability)
        )

    def __contains__(self, name: str) -> bool:
        """Registry'de kanal var mi kontrolu: 'telegram' in registry"""
        return name.lower() in self._channels

    def __len__(self) -> int:
        """Kayitli kanal sayisi."""
        return len(self._channels)
