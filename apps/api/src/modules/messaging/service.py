"""
Emlak Teknoloji Platformu - Messaging Service

Is mantigi katmani: mesaj gonderme, plan bazli kanal yonlendirme, sablon destegi.

Kanal oncelik sirasi (plan bazli):
    Elite   → whatsapp_cloud_api > telegram_bot > whatsapp_click_to_chat
    Pro     → telegram_bot > whatsapp_click_to_chat
    Starter → telegram_bot > whatsapp_click_to_chat

Kullanim:
    service = MessagingService(registry=registry)

    # Dogrudan gonderim
    result = await service.send_message(
        office_id=uuid, recipient="+905...", channel="telegram", content=content
    )

    # Plan bazli otomatik yonlendirme
    channel = await service.route_message(
        office_id=uuid, recipient="+905...", content=content
    )

    # Sablon bazli gonderim
    result = await service.send_templated_message(
        office_id=uuid, recipient="+905...", channel="telegram",
        template_id="welcome", locale="tr", name="Ahmet", office_name="ABC Emlak"
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.core.plan_policy import PlanType, get_capabilities
from src.modules.messaging.schemas import ChannelCapabilities, MessageContent
from src.modules.messaging.templates.engine import MessageTemplateEngine

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.messaging.registry import ChannelRegistry
    from src.modules.messaging.schemas import DeliveryResult

logger = structlog.get_logger(__name__)

# ================================================================
# Plan bazli kanal oncelik sirasi
# ================================================================
# En yuksek oncelikli kanal basta, en dusuk sonda.
# route_message() bu sirayla ilk mevcut ve kayitli kanali secer.
CHANNEL_PRIORITY: dict[PlanType, list[str]] = {
    PlanType.ELITE: ["whatsapp_cloud_api", "telegram_bot", "whatsapp_click_to_chat"],
    PlanType.PRO: ["telegram_bot", "whatsapp_click_to_chat"],
    PlanType.STARTER: ["telegram_bot", "whatsapp_click_to_chat"],
}


class MessagingService:
    """
    Mesajlasma is mantigi servisi.

    Sorumluluklar:
        - Kanal uzerinden mesaj gonderme (send_message)
        - Plan bazli kanal yonlendirme (route_message)
        - Sablon bazli mesaj gonderme (send_templated_message)
        - Loglama ve hata yonetimi

    NOT: Bu sinif iskelet (skeleton) implementasyondur.
    Office → plan tipi cozumlemesi ileride subscription modulu ile entegre edilecektir.
    """

    def __init__(
        self,
        registry: ChannelRegistry,
        template_engine: MessageTemplateEngine | None = None,
    ) -> None:
        self._registry = registry
        self._template_engine = template_engine or MessageTemplateEngine()

    async def send_message(
        self,
        office_id: UUID,
        recipient: str,
        channel: str,
        content: MessageContent,
    ) -> DeliveryResult:
        """
        Belirtilen kanal uzerinden mesaj gonderir.

        Args:
            office_id: Mesaji gonderen emlak ofisinin UUID'si.
            recipient: Alicinin kanal bazli benzersiz ID'si.
            channel: Kullanilacak kanal adi (ornek: "telegram").
            content: Gonderilecek mesaj icerigi.

        Returns:
            DeliveryResult — gonderim sonucu.

        Raises:
            KeyError: Belirtilen kanal registry'de kayitli degilse.
        """
        logger.info(
            "sending_message",
            office_id=str(office_id),
            channel=channel,
            recipient=recipient,
        )

        adapter = self._registry.get(channel)

        # Zengin icerik desteklenmiyorsa buton/medya'yi temizle
        if not adapter.supports_rich_content():
            content = MessageContent(
                text=content.text,
                media_url=None,
                buttons=None,
                template_id=content.template_id,
            )

        result = await adapter.send(recipient, content)

        if result.success:
            logger.info(
                "message_sent",
                office_id=str(office_id),
                channel=channel,
                message_id=result.message_id,
            )
        else:
            logger.warning(
                "message_send_failed",
                office_id=str(office_id),
                channel=channel,
                error=result.error,
            )

        return result

    async def route_message(
        self,
        office_id: UUID,
        recipient: str,
        content: MessageContent,
        plan_type: str = "starter",
    ) -> str:
        """
        Plan bazli kanal yonlendirme — en uygun kanali secer.

        Algoritma:
            1. Office'in plan tipini al (simdilik parametre olarak)
            2. Plan icin kanal oncelik sirasini belirle
            3. Oncelik sirasina gore ilk mevcut + kayitli kanali sec
            4. Secilen kanal uzerinden mesaj gonder

        Args:
            office_id: Mesaji gonderen emlak ofisinin UUID'si.
            recipient: Alicinin kanal bazli benzersiz ID'si.
            content: Gonderilecek mesaj icerigi.
            plan_type: Office'in abonelik plani ("starter", "pro", "elite").
                       Ileride subscription modulu ile otomatik cozumlenecek.

        Returns:
            Secilen kanal adi (ornek: "telegram_bot").

        Raises:
            ValueError: Plan tipi gecersizse veya uygun kanal bulunamazsa.
        """
        # Plan bazli yetenekleri al
        capabilities = get_capabilities(plan_type)

        # Plan tipi enum'a cevir
        plan = PlanType(plan_type.lower())

        # Plan icin kanal oncelik sirasi
        priority = CHANNEL_PRIORITY.get(plan, CHANNEL_PRIORITY[PlanType.STARTER])

        # Plan yeteneklerine gore filtreleme haritasi
        # ChannelCapability dict key'leri ile kanal adlari eslestirmesi
        capability_map: dict[str, str] = {
            "telegram_bot": "telegram_bot",
            "whatsapp_click_to_chat": "whatsapp_click_to_chat",
            "whatsapp_cloud_api": "whatsapp_cloud_api",
        }

        # Oncelik sirasina gore ilk uygun kanali sec
        selected_channel: str | None = None
        for channel_name in priority:
            # Plan bu kanali destekliyor mu?
            cap_key = capability_map.get(channel_name, channel_name)
            if not capabilities.get(cap_key, False):
                continue

            # Kanal registry'de kayitli mi?
            if channel_name not in self._registry:
                logger.debug(
                    "channel_not_registered",
                    channel=channel_name,
                    office_id=str(office_id),
                )
                continue

            selected_channel = channel_name
            break

        if selected_channel is None:
            available = self._registry.list_channels()
            raise ValueError(
                f"Plan '{plan_type}' icin uygun kanal bulunamadi. "
                f"Kayitli kanallar: {available}"
            )

        logger.info(
            "message_routed",
            office_id=str(office_id),
            plan_type=plan_type,
            selected_channel=selected_channel,
            priority_order=priority,
        )

        # Secilen kanal uzerinden gonder
        await self.send_message(office_id, recipient, selected_channel, content)

        return selected_channel

    # ================================================================
    # Sablon bazli mesaj gonderimi
    # ================================================================

    async def send_templated_message(
        self,
        office_id: UUID,
        recipient: str,
        channel: str,
        template_id: str,
        locale: str = "tr",
        **kwargs: object,
    ) -> DeliveryResult:
        """
        Sablon bazli mesaj gonderir.

        Islem akisi:
            1. MessageTemplateEngine ile sablonu render et → MessageContent
            2. Mevcut send_message() ile kanala gonder
            3. Kanal zengin icerik desteklemiyorsa butonlar otomatik temizlenir
               (send_message icerisindeki capability-aware mantik bunu halleder)

        Args:
            office_id: Mesaji gonderen emlak ofisinin UUID'si.
            recipient: Alicinin kanal bazli benzersiz ID'si.
            channel: Kullanilacak kanal adi (ornek: "telegram").
            template_id: Sablon dosya adi (uzantisiz). Ornek: "welcome"
            locale: Sablon dili. Varsayilan: "tr"
            **kwargs: Sablona aktarilacak degiskenler.
                      Ornek: name="Ahmet", office_name="ABC Emlak"

        Returns:
            DeliveryResult — gonderim sonucu.

        Raises:
            FileNotFoundError: Sablon dosyasi bulunamazsa.
            KeyError: Belirtilen kanal registry'de kayitli degilse.
            jinja2.UndefinedError: Sablonda kullanilan degisken kwargs'da yoksa.
        """
        logger.info(
            "sending_templated_message",
            office_id=str(office_id),
            channel=channel,
            template_id=template_id,
            locale=locale,
        )

        # Sablondan MessageContent olustur
        content = self._template_engine.render(
            template_id=template_id,
            locale=locale,
            **kwargs,
        )

        # Mevcut send_message() akisini kullan
        # (capability-aware rich content temizligi dahil)
        return await self.send_message(office_id, recipient, channel, content)

    # ================================================================
    # Capability sorgu metotlari (ADR-0007)
    # ================================================================

    async def get_channel_capabilities(self, channel: str) -> ChannelCapabilities:
        """
        Belirli bir kanalin yeteneklerini dondurur (ADR-0007).

        Servis katmaninda capability sorgusu — UI ve raporlama bu metodu kullanir.

        Args:
            channel: Kanal adi (ornek: "telegram", "whatsapp").

        Returns:
            ChannelCapabilities — kanalin yetenek haritasi.

        Raises:
            KeyError: Kanal registry'de kayitli degilse.
        """
        return self._registry.get_capabilities(channel)

    async def get_available_channels(
        self,
        capability: str | None = None,
    ) -> list[dict]:
        """
        Tum veya belirli yeteneğe sahip kanallari listeler (ADR-0007).

        Kullanim:
            # Tum kanallar
            channels = await service.get_available_channels()

            # Sadece read receipt destekleyenler
            channels = await service.get_available_channels(capability="read")

        Args:
            capability: Filtreleme icin yetenek adi (opsiyonel).
                        None → tum kanallar dondurulur.
                        "read" → sadece supports_read=True olanlar.

        Returns:
            list[dict] — kanal adi + capability ozeti listesi.
            Her eleman: {"channel": str, "capabilities": dict}
        """
        if capability:
            channel_names = self._registry.get_channels_supporting(capability)
        else:
            channel_names = self._registry.list_channels()

        return [
            {
                "channel": name,
                "capabilities": self._registry.get_capabilities(name).to_dict(),
            }
            for name in channel_names
        ]

    def validate_content_for_channel(
        self,
        channel: str,
        content: MessageContent,
    ) -> list[str]:
        """
        Mesaj iceriginin kanal yetenekleriyle uyumunu kontrol eder (ADR-0007).

        Gonderim oncesinde uyari listesi uretir. Uyarilar gonderimi engellemez
        ancak log'lanir ve API response'ta dondurulur.

        Kontroller:
            1. Mesaj uzunlugu → max_message_length
            2. Medya destegi → supports_media_upload
            3. Buton destegi → supports_inline_buttons + max_buttons_per_message
            4. Template destegi → supports_templates

        Args:
            channel: Kanal adi.
            content: Dogrulanacak mesaj icerigi.

        Returns:
            list[str] — uyari mesajlari listesi (bos liste = sorun yok).

        Raises:
            KeyError: Kanal registry'de kayitli degilse.
        """
        warnings: list[str] = []
        caps = self._registry.get_capabilities(channel)

        # 1. Mesaj uzunlugu kontrolu
        if len(content.text) > caps.max_message_length:
            warnings.append(
                f"Mesaj uzunlugu ({len(content.text)} karakter) "
                f"'{channel}' kanal limitini ({caps.max_message_length}) asiyor"
            )

        # 2. Medya destegi kontrolu
        if content.media_url and not caps.supports_media_upload:
            warnings.append(
                f"'{channel}' kanali medya yuklemeyi desteklemiyor"
            )

        # 3. Buton destegi ve limit kontrolu
        if content.buttons:
            if not caps.supports("inline_buttons"):
                warnings.append(
                    f"'{channel}' kanali inline buton desteklemiyor"
                )
            elif (
                caps.max_buttons_per_message > 0
                and len(content.buttons) > caps.max_buttons_per_message
            ):
                warnings.append(
                    f"Buton sayisi ({len(content.buttons)}) "
                    f"'{channel}' kanal limitini ({caps.max_buttons_per_message}) asiyor"
                )

        # 4. Template destegi kontrolu
        if content.template_id and not caps.supports("templates"):
            warnings.append(
                f"'{channel}' kanali sablon mesajlari desteklemiyor"
            )

        if warnings:
            logger.warning(
                "content_capability_mismatch",
                channel=channel,
                warnings=warnings,
                text_length=len(content.text),
                has_media=content.media_url is not None,
                button_count=len(content.buttons) if content.buttons else 0,
            )

        return warnings
