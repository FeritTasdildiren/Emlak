"""
Emlak Teknoloji Platformu - Telegram Adapter

aiogram 3.x tabanli Telegram Bot API adaptoru.
MessageChannel Protocol'unu tam olarak uygular.

Yetenekler:
    - Metin, buton (InlineKeyboard), medya (foto/belge) gonderimi
    - Webhook uzerinden gelen mesajlari parse etme
    - Typing indicator destegi
    - 4096 karakter mesaj limiti

Lifecycle:
    adapter = TelegramAdapter(bot_token="123:ABC...")
    registry.register("telegram", adapter)
    ...
    await adapter.close()  # shutdown'da cagrilmali

NOT: isinstance(adapter, MessageChannel) kontrolu gecmelidir (runtime_checkable).

Referans: docs/MIMARI-KARARLAR.md
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from aiogram import Bot
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from src.modules.messaging.schemas import (
    ChannelCapabilities,
    DeliveryResult,
    IncomingMessage,
)

if TYPE_CHECKING:
    from src.modules.messaging.schemas import MessageContent

logger = structlog.get_logger(__name__)

# ================================================================
# Medya URL uzanti kontrolu
# ================================================================

_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
)


def _is_image_url(url: str) -> bool:
    """
    URL'nin bir gorsel dosyasina isaret edip etmedigini kontrol eder.

    Basit uzanti bazli kontrol — Content-Type header'ina bakmaz.
    Bilinmeyen uzantilar icin False doner (document olarak gonderilir).
    """
    # Query string'i temizle
    path = url.split("?")[0].split("#")[0].lower()
    return any(path.endswith(ext) for ext in _IMAGE_EXTENSIONS)


# ================================================================
# Telegram Adapter
# ================================================================


class TelegramAdapter:
    """
    Telegram Bot API adaptoru — MessageChannel Protocol implementasyonu.

    aiogram 3.x kullanarak Telegram Bot API ile iletisim kurar.

    Metotlar (MessageChannel Protocol):
        send                — mesaj gonder (metin, buton, medya)
        handle_webhook      — gelen Update'i IncomingMessage'e donustur
        supports_rich_content — True (buton + medya destekli)
        get_capabilities    — kanal yetenekleri

    Ek metotlar:
        close               — Bot HTTP session'ini kapat (shutdown'da)
    """

    def __init__(self, bot_token: str) -> None:
        """
        TelegramAdapter baslatir.

        Args:
            bot_token: Telegram BotFather'dan alinan bot token'i.
                       Bos veya gecersiz token runtime'da hata uretir.
        """
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN bos olamaz")
        self._bot = Bot(token=bot_token)
        logger.info("telegram_adapter_initialized")

    # ================================================================
    # MessageChannel Protocol — send
    # ================================================================

    async def send(
        self,
        recipient: str,
        content: MessageContent,
    ) -> DeliveryResult:
        """
        Telegram uzerinden mesaj gonderir.

        Gonderim stratejisi:
            1. content.buttons varsa → InlineKeyboardMarkup olustur
            2. content.media_url varsa → send_photo (gorsel) veya send_document (diger)
            3. Sadece metin → send_message

        Args:
            recipient: Telegram chat_id (kullanici veya grup).
            content: Gonderilecek mesaj icerigi.

        Returns:
            DeliveryResult — basari/hata durumu + Telegram message_id.
        """
        try:
            reply_markup = self._build_inline_keyboard(content.buttons)

            if content.media_url:
                result = await self._send_media(
                    chat_id=recipient,
                    media_url=content.media_url,
                    caption=content.text,
                    reply_markup=reply_markup,
                )
            else:
                result = await self._bot.send_message(
                    chat_id=recipient,
                    text=content.text,
                    reply_markup=reply_markup,
                )

            logger.info(
                "telegram_message_sent",
                chat_id=recipient,
                message_id=result.message_id,
            )

            return DeliveryResult(
                success=True,
                message_id=str(result.message_id),
                channel="telegram",
            )

        except Exception as exc:
            logger.error(
                "telegram_send_failed",
                chat_id=recipient,
                error=str(exc),
                exc_info=True,
            )
            return DeliveryResult(
                success=False,
                message_id=None,
                channel="telegram",
                error=str(exc),
            )

    # ================================================================
    # MessageChannel Protocol — handle_webhook
    # ================================================================

    async def handle_webhook(
        self,
        payload: dict,
    ) -> IncomingMessage:
        """
        Telegram Update payload'unu parse edip IncomingMessage'e donusturur.

        Desteklenen update tipleri:
            - message / edited_message → metin + medya
            - callback_query → buton tiklama verisi

        Args:
            payload: Telegram'dan gelen ham webhook JSON'u.

        Returns:
            IncomingMessage — normalize edilmis gelen mesaj.

        Raises:
            ValueError: Desteklenmeyen veya parse edilemeyen update tipi.
        """
        update = Update.model_validate(payload)

        # --- Mesaj (yeni veya duzenlenmis) ---
        message = update.message or update.edited_message
        if message is not None:
            return self._parse_message(message, payload)

        # --- Callback query (buton tiklama) ---
        if update.callback_query is not None:
            return self._parse_callback_query(update.callback_query, payload)

        # --- Desteklenmeyen update tipi ---
        logger.warning(
            "telegram_unsupported_update_type",
            update_id=update.update_id,
            payload_keys=list(payload.keys()),
        )
        raise ValueError(
            f"Desteklenmeyen Telegram update tipi. "
            f"update_id={update.update_id}, keys={list(payload.keys())}"
        )

    # ================================================================
    # MessageChannel Protocol — supports_rich_content
    # ================================================================

    def supports_rich_content(self) -> bool:
        """
        Telegram zengin icerik destekler: InlineKeyboard butonlari, foto, belge.

        Returns:
            True — her zaman.
        """
        return True

    # ================================================================
    # MessageChannel Protocol — get_capabilities (ADR-0007)
    # ================================================================

    def get_capabilities(self) -> ChannelCapabilities:
        """
        Telegram Bot API yeteneklerini detayli olarak raporlar (ADR-0007).

        Telegram Bot API 7.x referans:
            - Delivery receipt: var (message gonderildi bilgisi)
            - Read receipt: YOK (Bot API sinirlamasi — kullanici gizliligi)
            - Typing indicator: sendChatAction API
            - InlineKeyboard: 100 buton (10x10 grid)
            - Medya: 50MB limit, foto/video/ses/belge
            - Thread reply: reply_to_message_id
            - Location/Contact: sendLocation, sendContact
            - Callback query: InlineKeyboard callback_data

        Returns:
            ChannelCapabilities — Telegram Bot API yetenek haritasi.
        """
        return ChannelCapabilities(
            # Temel yetenekler
            supports_delivered=True,  # Telegram mesaj iletildi bildirimi
            supports_read=False,  # Bot API'de read receipt YOK
            supports_typing_indicator=True,  # sendChatAction("typing")
            supports_media_upload=True,  # Foto, belge, video, ses
            max_message_length=4096,  # Telegram karakter limiti
            # Zengin icerik yetenekleri
            supports_reactions=False,  # Bot API'de sinirli reaksiyon destegi
            supports_thread_reply=True,  # reply_to_message_id
            supports_inline_buttons=True,  # InlineKeyboardMarkup
            supports_location=True,  # sendLocation
            supports_contact=True,  # sendContact
            supports_voice=True,  # sendVoice (OGG/Opus)
            supports_video=True,  # sendVideo (MP4)
            supports_document=True,  # sendDocument
            supports_templates=False,  # Telegram'da HSM template yok
            supports_callback_query=True,  # InlineKeyboard callback_data
            # Kanal sinirlari
            max_buttons_per_message=100,  # 100 inline button (10 satir x 10 sutun)
            max_media_size_mb=50.0,  # Telegram 50MB dosya limiti
            supported_media_types=[
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
                "video/mp4",
                "audio/ogg",
                "application/pdf",
            ],
            # Metadata
            channel_name="telegram",
            channel_version="Bot API 7.x",
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
            True — Telegram bu yetenegi destekliyorsa.
        """
        return self.get_capabilities().supports(capability)

    # ================================================================
    # Lifecycle — close
    # ================================================================

    async def set_webhook(self, url: str) -> None:
        """
        Telegram'a webhook URL'ini bildirir.

        Startup'ta cagrilir. Telegram bu URL'e Update gondermeye baslar.

        Args:
            url: Webhook URL'i (HTTPS olmali, self-signed sertifika kabul edilmez).

        Raises:
            aiogram.exceptions.TelegramAPIError: Telegram API hatasi.
        """
        await self._bot.set_webhook(url=url)
        logger.info("telegram_webhook_configured", webhook_url=url)

    async def close(self) -> None:
        """
        Bot HTTP session'ini kapatir.

        FastAPI lifespan shutdown'da cagrilmalidir.
        Cagrilmazsa aiohttp session leak olusur.
        """
        await self._bot.session.close()
        logger.info("telegram_adapter_closed")

    # ================================================================
    # File Operations
    # ================================================================

    async def download_file(self, file_id: str) -> bytes:
        """
        Telegram sunucusundan dosya indirir.

        Args:
            file_id: Telegram file_id (photo, document vb.).

        Returns:
            Dosya icerigi (bytes).

        Raises:
            aiogram.exceptions.TelegramAPIError: Gecersiz file_id veya API hatasi.
        """
        from io import BytesIO

        file = await self._bot.get_file(file_id)
        buffer = BytesIO()
        await self._bot.download_file(file.file_path, buffer)

        data = buffer.getvalue()
        logger.info(
            "telegram_file_downloaded",
            file_id=file_id,
            size_bytes=len(data),
        )
        return data

    async def send_photo_bytes(
        self,
        chat_id: str,
        photo_bytes: bytes,
        caption: str = "",
    ) -> DeliveryResult:
        """
        Byte verisi olarak foto gonderir (staging sonucu gibi).

        Args:
            chat_id: Telegram chat ID.
            photo_bytes: PNG/JPEG gorsel verisi.
            caption: Foto altina yazilacak metin.

        Returns:
            DeliveryResult — basari/hata durumu.
        """
        try:
            input_file = BufferedInputFile(photo_bytes, filename="staged.png")
            result = await self._bot.send_photo(
                chat_id=chat_id,
                photo=input_file,
                caption=caption,
            )
            logger.info(
                "telegram_photo_bytes_sent",
                chat_id=chat_id,
                message_id=result.message_id,
                photo_size_bytes=len(photo_bytes),
            )
            return DeliveryResult(
                success=True,
                message_id=str(result.message_id),
                channel="telegram",
            )
        except Exception as exc:
            logger.error(
                "telegram_photo_bytes_send_failed",
                chat_id=chat_id,
                error=str(exc),
                exc_info=True,
            )
            return DeliveryResult(
                success=False,
                message_id=None,
                channel="telegram",
                error=str(exc),
            )

    async def send_document(
        self,
        chat_id: str,
        file_bytes: bytes,
        filename: str,
        caption: str = "",
    ) -> DeliveryResult:
        """
        Byte verisi olarak belge gonderir (PDF raporu gibi).

        Args:
            chat_id: Telegram chat ID.
            file_bytes: Belge icerigi (bytes).
            filename: Dosya adi (orn: "degerleme_raporu.pdf").
            caption: Belge altina yazilacak metin.

        Returns:
            DeliveryResult — basari/hata durumu.
        """
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            result = await self._bot.send_document(
                chat_id=chat_id,
                document=input_file,
                caption=caption,
            )
            logger.info(
                "telegram_document_sent",
                chat_id=chat_id,
                message_id=result.message_id,
                filename=filename,
                file_size_bytes=len(file_bytes),
            )
            return DeliveryResult(
                success=True,
                message_id=str(result.message_id),
                channel="telegram",
            )
        except Exception as exc:
            logger.error(
                "telegram_document_send_failed",
                chat_id=chat_id,
                filename=filename,
                error=str(exc),
                exc_info=True,
            )
            return DeliveryResult(
                success=False,
                message_id=None,
                channel="telegram",
                error=str(exc),
            )

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str = "",
    ) -> None:
        """
        Callback query'yi yanitlar (buton uzerindeki loading indicator'u kaldirir).

        Args:
            callback_query_id: Callback query ID (raw_payload'dan alinir).
            text: Kullaniciya gosterilecek kisa bildirim (toast, opsiyonel).
        """
        try:
            await self._bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text,
            )
        except Exception as exc:
            logger.warning(
                "telegram_answer_callback_failed",
                callback_query_id=callback_query_id,
                error=str(exc),
            )

    # ================================================================
    # Private Helpers
    # ================================================================

    @staticmethod
    def _build_inline_keyboard(
        buttons: list | None,
    ) -> InlineKeyboardMarkup | None:
        """
        Button listesinden InlineKeyboardMarkup olusturur.

        Her buton ayri bir satira yerlestirilir (tek sutun layout).
        URL butonu ve callback butonu ayni anda desteklenir.

        Args:
            buttons: MessageContent.buttons listesi (None olabilir).

        Returns:
            InlineKeyboardMarkup veya None (buton yoksa).
        """
        if not buttons:
            return None

        keyboard_rows: list[list[InlineKeyboardButton]] = []

        for btn in buttons:
            if btn.url:
                keyboard_rows.append([InlineKeyboardButton(text=btn.text, url=btn.url)])
            elif btn.callback_data:
                keyboard_rows.append(
                    [InlineKeyboardButton(text=btn.text, callback_data=btn.callback_data)]
                )

        if not keyboard_rows:
            return None

        return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    async def _send_media(
        self,
        chat_id: str,
        media_url: str,
        caption: str,
        reply_markup: InlineKeyboardMarkup | None,
    ):
        """
        Medya tipine gore send_photo veya send_document cagrisini yapar.

        Gorsel uzantilari (.jpg, .png, vb.) → send_photo
        Diger dosyalar → send_document

        Args:
            chat_id: Telegram chat ID.
            media_url: Gonderilecek medya URL'i.
            caption: Medya altina yazilacak metin.
            reply_markup: InlineKeyboard (opsiyonel).

        Returns:
            aiogram Message objesi.
        """
        if _is_image_url(media_url):
            return await self._bot.send_photo(
                chat_id=chat_id,
                photo=media_url,
                caption=caption,
                reply_markup=reply_markup,
            )

        return await self._bot.send_document(
            chat_id=chat_id,
            document=media_url,
            caption=caption,
            reply_markup=reply_markup,
        )

    @staticmethod
    def _parse_message(message, payload: dict) -> IncomingMessage:
        """
        Telegram Message objesinden IncomingMessage olusturur.

        Args:
            message: aiogram Message objesi.
            payload: Orijinal webhook payload'u (raw_payload icin).

        Returns:
            IncomingMessage — normalize edilmis gelen mesaj.

        Raises:
            ValueError: Gonderici bilgisi (from_user) bulunamazsa.
        """
        # from_user None olabilir (kanal postlari gibi)
        if message.from_user is None:
            raise ValueError(
                "Telegram mesajinda gonderici bilgisi (from_user) bulunamadi. "
                "Kanal postlari desteklenmemektedir."
            )

        text = message.text or message.caption or ""

        # Medya cikarma — file_id olarak saklanir
        # NOT: file_id'den download URL almak icin bot.get_file() gerekir,
        # ancak bu islem IncomingMessage scope'u disindadir.
        media_url: str | None = None
        if message.photo:
            # Telegram foto boyut sirali gonderir — son eleman en buyuk
            media_url = message.photo[-1].file_id
        elif message.document:
            media_url = message.document.file_id
        elif message.video:
            media_url = message.video.file_id
        elif message.voice:
            media_url = message.voice.file_id

        return IncomingMessage(
            sender_id=str(message.from_user.id),
            channel="telegram",
            content=text,
            media_url=media_url,
            raw_payload=payload,
        )

    @staticmethod
    def _parse_callback_query(callback_query, payload: dict) -> IncomingMessage:
        """
        Telegram CallbackQuery objesinden IncomingMessage olusturur.

        Buton tiklamalarini isler. callback_data content olarak doner.

        Args:
            callback_query: aiogram CallbackQuery objesi.
            payload: Orijinal webhook payload'u (raw_payload icin).

        Returns:
            IncomingMessage — normalize edilmis callback verisi.
        """
        return IncomingMessage(
            sender_id=str(callback_query.from_user.id),
            channel="telegram",
            content=callback_query.data or "",
            raw_payload=payload,
        )
