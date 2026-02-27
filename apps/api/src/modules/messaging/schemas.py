"""
Emlak Teknoloji Platformu - Messaging Schemas

Mesajlasma modulu icin Pydantic veri modelleri.
Tum kanal adaptorlerinde ortak kullanilan tipler.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

# ================================================================
# Alt Modeller
# ================================================================


class Button(BaseModel):
    """
    Mesaj icindeki interaktif buton.

    Tip bazli kullanim:
        - url doluysa: link butonu (kullaniciyi URL'e yonlendirir)
        - callback_data doluysa: callback butonu (webhook uzerinden geri donus)
    """

    text: str = Field(..., description="Buton uzerindeki yazi", max_length=256)
    url: str | None = Field(None, description="Link butonu — tiklandiginda acilacak URL")
    callback_data: str | None = Field(
        None,
        description="Callback butonu — tiklandiginda webhook'a gonderilecek veri",
        max_length=512,
    )


# ================================================================
# Mesaj Icerigi
# ================================================================


class MessageContent(BaseModel):
    """
    Kanala gonderilecek mesaj icerigi.

    Adaptorler bu modeli alip kanala ozgu formata donusturur.
    Ornegin:
        - Telegram: text + buttons → InlineKeyboardMarkup
        - WhatsApp: text + template_id → Template Message
    """

    text: str = Field(..., description="Mesaj metni", max_length=4096)
    media_url: str | None = Field(
        None,
        description="Ek medya URL'i (gorsel, belge, vb.)",
    )
    buttons: list[Button] | None = Field(
        None,
        description="Interaktif butonlar (destekleyen kanallarda gosterilir)",
    )
    template_id: str | None = Field(
        None,
        description="Kanal bazli mesaj sablonu ID'si (WhatsApp template, vb.)",
    )


# ================================================================
# Gonderim Sonucu
# ================================================================


class DeliveryResult(BaseModel):
    """
    Mesaj gonderim sonucu.

    Her kanal adaptoru bu modeli dondurmeli.
    Basarisiz gonderim icin success=False + error alani kullanilir.
    """

    success: bool = Field(..., description="Gonderim basarili mi?")
    message_id: str | None = Field(
        None,
        description="Kanalin atadigi mesaj ID'si (tracking icin)",
    )
    channel: str = Field(..., description="Mesajin gonderildigi kanal adi")
    error: str | None = Field(None, description="Hata durumunda aciklama")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Gonderim zamani (UTC)",
    )


# ================================================================
# Gelen Mesaj
# ================================================================


class IncomingMessage(BaseModel):
    """
    Webhook uzerinden gelen mesaj.

    Kanal adaptorlerinin handle_webhook() metodu bu modeli dondurur.
    raw_payload alaninda kanalin orijinal verisi saklanir (debug icin).
    """

    sender_id: str = Field(..., description="Gondericinin kanal bazli benzersiz ID'si")
    channel: str = Field(..., description="Mesajin geldigi kanal adi")
    content: str = Field(..., description="Mesaj metni")
    media_url: str | None = Field(None, description="Gelen medya URL'i (varsa)")
    raw_payload: dict = Field(
        default_factory=dict,
        description="Kanalin orijinal webhook payload'u (debug ve audit icin)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Mesajin alindigi zaman (UTC)",
    )


# ================================================================
# Kanal Yetenekleri
# ================================================================


class ChannelCapabilities(BaseModel):
    """
    Bir kanalin destekledigi ozellikler (ADR-0007).

    Varsayilan degerler en kisitlayici (False / 0) olarak ayarlanmistir.
    Adaptor uygulamalari get_capabilities() metodunda gercek degerleri dondurur.

    Uc katman:
        1. Temel yetenekler  — delivery/read/typing/media (mevcut)
        2. Zengin icerik      — reactions, thread, buttons, location vb.
        3. Kanal sinirlari    — max buton, max dosya boyutu, desteklenen MIME

    Ornek:
        WhatsApp Cloud API:
            supports_delivered=True, supports_read=True,
            supports_media_upload=True, supports_templates=True,
            max_buttons_per_message=3, max_message_length=4096

        Telegram Bot API:
            supports_delivered=True, supports_read=False,
            supports_typing_indicator=True, supports_inline_buttons=True,
            max_buttons_per_message=100, max_message_length=4096

    Kullanim:
        caps = adapter.get_capabilities()
        caps.supports("read")           # → True/False
        caps.to_dict()                  # → JSON-serializable dict
        ChannelCapabilities.from_dict(d)  # → bilinmeyen key'leri yoksayar
    """

    # ------------------------------------------------------------------
    # Temel yetenekler (mevcut)
    # ------------------------------------------------------------------
    supports_delivered: bool = Field(
        default=False,
        description="Mesajin iletildigine dair bildirim destegi",
    )
    supports_read: bool = Field(
        default=False,
        description="Mesajin okunduguna dair bildirim destegi",
    )
    supports_typing_indicator: bool = Field(
        default=False,
        description="Yazma gostergesi destegi",
    )
    supports_media_upload: bool = Field(
        default=False,
        description="Medya dosyasi gonderme destegi",
    )
    max_message_length: int = Field(
        default=4096,
        description="Maksimum mesaj karakter uzunlugu",
        ge=1,
    )

    # ------------------------------------------------------------------
    # Zengin icerik yetenekleri (ADR-0007 genisletme)
    # ------------------------------------------------------------------
    supports_reactions: bool = Field(
        default=False,
        description="Mesaj reaksiyon (emoji) destegi",
    )
    supports_thread_reply: bool = Field(
        default=False,
        description="Mesaj zinciri / yanitlama destegi",
    )
    supports_inline_buttons: bool = Field(
        default=False,
        description="Inline buton (InlineKeyboard / Interactive) destegi",
    )
    supports_location: bool = Field(
        default=False,
        description="Konum mesaji gonderme destegi",
    )
    supports_contact: bool = Field(
        default=False,
        description="Kisi karti gonderme destegi",
    )
    supports_voice: bool = Field(
        default=False,
        description="Sesli mesaj gonderme destegi",
    )
    supports_video: bool = Field(
        default=False,
        description="Video mesaj gonderme destegi",
    )
    supports_document: bool = Field(
        default=False,
        description="Belge dosyasi gonderme destegi",
    )
    supports_templates: bool = Field(
        default=False,
        description="Sablon mesaj destegi (WhatsApp HSM template vb.)",
    )
    supports_callback_query: bool = Field(
        default=False,
        description="Inline buton callback destegi (Telegram callback_query vb.)",
    )

    # ------------------------------------------------------------------
    # Kanal sinirlari
    # ------------------------------------------------------------------
    max_buttons_per_message: int = Field(
        default=0,
        description="Tek mesajda gosterilebilecek maksimum buton sayisi (0 = desteklenmiyor)",
        ge=0,
    )
    max_media_size_mb: float = Field(
        default=0.0,
        description="Maksimum medya dosya boyutu (MB, 0.0 = desteklenmiyor)",
        ge=0.0,
    )
    supported_media_types: list[str] = Field(
        default_factory=list,
        description=(
            "Desteklenen MIME tipleri listesi. "
            'Ornek: ["image/jpeg", "image/png", "application/pdf"]'
        ),
    )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    channel_name: str = Field(
        default="",
        description="Kanal adi (ornek: 'telegram', 'whatsapp')",
    )
    channel_version: str = Field(
        default="",
        description="Kanal API surumu (ornek: 'Bot API 7.x', 'Cloud API v18.0')",
    )
    last_capability_check: str = Field(
        default="",
        description="Son yetenek kontrolu zamani (ISO 8601 timestamp)",
    )

    # ------------------------------------------------------------------
    # Yardimci metotlar
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """JSON-serializable dict dondur. API response'lar icin."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> ChannelCapabilities:
        """
        Dict'ten olustur — bilinmeyen alanlari yoksay (forward compatibility).

        Farkli surumlerdeki capability JSON'lari guvenle parse edilir.
        Yeni eklenen alanlar bilinmiyorsa varsayilan deger kullanilir.
        """
        valid_fields = set(cls.model_fields.keys())
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def supports(self, capability: str) -> bool:
        """
        Dinamik yetenek sorgusu.

        Kullanim:
            caps.supports("read")            # → supports_read
            caps.supports("inline_buttons")  # → supports_inline_buttons
            caps.supports("bilinmeyen")      # → False (guvenli)

        Args:
            capability: Yetenek adi ("supports_" prefix'i olmadan).

        Returns:
            True — yetenek destekleniyor, False — desteklenmiyor veya bilinmiyor.
        """
        attr = f"supports_{capability}"
        value = getattr(self, attr, False)
        return bool(value)
