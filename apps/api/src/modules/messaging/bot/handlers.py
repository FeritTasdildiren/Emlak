"""
Emlak Teknoloji Platformu - Telegram Bot Handler

Webhook uzerinden gelen IncomingMessage'lari analiz eder,
komut ise ilgili handler'a yonlendirir, degilse echo yapar.

Komutlar:
    /start [token]  — Karsilama + opsiyonel deep link baglama
    /help           — Kullanilabilir komutlarin listesi
    /degerleme      — AI konut degerleme (ilce, m2, oda, kat, bina yasi)
    /musteri        — Hizli musteri kaydi (ad, telefon, tip, butce)
    /fotograf       — Sanal mobilyalama (virtual staging)
    /kredi          — Konut kredisi hesaplama (tutar, vade, pesinat)
    /portfoy        — Ofis portfoy listesi (son 5 ilan)
    /rapor          — Son degerleme raporunu PDF olarak gonder
    (diger)         — Echo — gelen mesaji aynen geri gonder

Ozel akislar:
    - Fotograf mesaji (media_url != None): Oda analizi + tarz secimi
    - Callback query (staging:*): Tarz secimi sonrasi sahneleme
    - Callback query (ilan:*): Ilan wizard onay/iptal/yeniden
    - Callback query (match:*): Eslesme ilgileniyorum/gec

Tasarim:
    - TelegramAdapter uzerinden mesaj gonderir (MessageContent kullanir)
    - TelegramAuthBridge uzerinden deep link dogrulama yapar
    - from_user None olabilir (kanal postlari) → IncomingMessage'da sender_id bos olamaz,
      ancak handle() None/bos content icin guard koyar
    - Hata durumunda exception firlatMAZ, loglayip sessizce gecer
      (webhook handler her zaman 200 dondurmeli)

Referans: TASK-039, TASK-110, TASK-121, TASK-135, TASK-138, TASK-139
"""

from __future__ import annotations

import base64
import uuid
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from src.modules.messaging.bot.conversation_state import (
    ConversationState,
    ConversationStateManager,
    WizardStep,
)
from src.modules.messaging.schemas import Button, MessageContent

if TYPE_CHECKING:
    import redis.asyncio as aioredis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from src.modules.messaging.adapters.telegram import TelegramAdapter
    from src.modules.messaging.bot.auth_bridge import TelegramAuthBridge
    from src.modules.messaging.schemas import IncomingMessage

logger = structlog.get_logger(__name__)

# ================================================================
# Sabitler
# ================================================================

_WELCOME_MESSAGE = (
    "Merhaba! 👋 Emlak Teknoloji Platformu botuna hos geldiniz.\n\n"
    "Kullanilabilir komutlar:\n"
    "/start      — Karsilama mesaji\n"
    "/help       — Yardim\n"
    "/degerleme  — AI konut degerleme\n"
    "/musteri    — Hizli musteri kaydi\n"
    "/fotograf   — Sanal mobilyalama\n"
    "/kredi      — Konut kredisi hesaplama\n"
    "/portfoy    — Portfoy listesi\n"
    "/rapor      — Son degerleme raporu (PDF)\n\n"
    "Hesabinizi baglamak icin web panelden 'Telegram Bagla' butonunu kullanin."
)

_HELP_MESSAGE = (
    "📋 Kullanilabilir komutlar:\n\n"
    "/start      — Karsilama mesaji\n"
    "/help       — Bu yardim mesaji\n"
    "/degerleme  — AI konut degerleme\n"
    "/musteri    — Hizli musteri kaydi\n"
    "/fotograf   — Sanal mobilyalama (virtual staging)\n"
    "/kredi      — Konut kredisi hesaplama\n"
    "/ilan       — Ilan olusturma wizard'i\n"
    "/portfoy    — Portfoy listesi (son 5 ilan)\n"
    "/rapor      — Son degerleme raporu (PDF)\n"
    "/iptal      — Aktif ilan wizard'ini iptal et\n\n"
    "Ornek: /degerleme Kadikoy, 120, 3+1, 5, 10\n"
    "Ornek: /musteri Ahmet Yilmaz, 05321234567, a, 1000000, 3000000\n"
    "Ornek: /kredi 2.5m 15y 30\n\n"
    "Diger mesajlariniz echo olarak geri gonderilir.\n"
    "Hesap baglama icin web panelden link olusturun."
)

_LINK_SUCCESS_MESSAGE = (
    "✅ Hesabiniz basariyla baglandi!\n\n"
    "Artik platform bildirimlerini bu sohbet uzerinden alacaksiniz."
)

_LINK_INVALID_MESSAGE = (
    "❌ Baglanti kodu gecersiz veya suresi dolmus.\n\n"
    "Lutfen web panelden yeni bir baglanti linki olusturun."
)

_DEGERLEME_USAGE_MESSAGE = (
    "📊 Degerleme Komutu Kullanimi:\n\n"
    "/degerleme <ilce>, <m2>, <oda>, <kat>, <bina yasi>\n\n"
    "Ornek:\n"
    "/degerleme Kadikoy, 120, 3+1, 5, 10\n\n"
    "Parametreler:\n"
    "• Ilce: Istanbul ilce adi (orn: Kadikoy, Besiktas)\n"
    "• m2: Net metrekare\n"
    "• Oda: Oda sayisi (orn: 3+1, 2+1)\n"
    "• Kat: Bulundugu kat\n"
    "• Bina Yasi: Yil olarak"
)

_DEGERLEME_ERROR_MESSAGE = (
    "❌ Degerleme yapilamadi, lutfen tekrar deneyin.\n\n"
    "Sorun devam ederse parametreleri kontrol edin."
)

_MUSTERI_USAGE_MESSAGE = (
    "📋 Musteri Kayit Komutu Kullanimi:\n\n"
    "/musteri <ad>, <telefon>[, <tip>[, <butce_min>, <butce_max>]]\n\n"
    "Ornekler:\n"
    "/musteri Ahmet Yilmaz, 05321234567\n"
    "/musteri Ahmet Yilmaz, 05321234567, a\n"
    "/musteri Ahmet Yilmaz, 05321234567, a, 1000000, 3000000\n"
    "/musteri Mehmet Kaya, 05559876543, k, 5000, 10000\n\n"
    "Tip kisaltmalari:\n"
    "• a = Alici (buyer) [varsayilan]\n"
    "• s = Satici (seller)\n"
    "• k = Kiraci (renter)\n"
    "• e = Ev Sahibi (landlord)"
)

_MUSTERI_QUOTA_MESSAGE = (
    "⚠️ Musteri kotaniz doldu.\n\n"
    "Mevcut planinizdaki musteri limitine ulastiniz.\n"
    "Daha fazla musteri eklemek icin planinizi yukseltebilirsiniz."
)

_MUSTERI_NOT_LINKED_MESSAGE = (
    "❌ Hesabiniz baglanmamis.\n\n"
    "Bu komutu kullanabilmek icin once Telegram hesabinizi\n"
    "web panelden baglamaniz gerekiyor.\n\n"
    "Web panel → Ayarlar → Telegram Bagla"
)

_MUSTERI_ERROR_MESSAGE = (
    "❌ Musteri kaydi sirasinda bir hata olustu.\n\n"
    "Lutfen tekrar deneyin. Sorun devam ederse destek ile iletisime gecin."
)

# ================================================================
# /portfoy Sabitleri
# ================================================================

_PORTFOY_NOT_LINKED_MESSAGE = (
    "❌ Hesabiniz baglanmamis.\n\n"
    "Bu komutu kullanabilmek icin once Telegram hesabinizi\n"
    "web panelden baglamaniz gerekiyor.\n\n"
    "Web panel → Ayarlar → Telegram Bagla"
)

_PORTFOY_EMPTY_MESSAGE = (
    "📋 Portfoyunuzde henuz ilan bulunmuyor.\n\n"
    "Web panelden yeni ilan ekleyebilirsiniz."
)

_PORTFOY_ERROR_MESSAGE = (
    "❌ Portfoy bilgileri alinirken bir hata olustu.\n\n"
    "Lutfen tekrar deneyin."
)

# ================================================================
# /rapor Sabitleri
# ================================================================

_RAPOR_NOT_LINKED_MESSAGE = (
    "❌ Hesabiniz baglanmamis.\n\n"
    "Bu komutu kullanabilmek icin once Telegram hesabinizi\n"
    "web panelden baglamaniz gerekiyor.\n\n"
    "Web panel → Ayarlar → Telegram Bagla"
)

_RAPOR_NO_VALUATION_MESSAGE = (
    "📊 Henuz bir degerleme yapmadiniz.\n\n"
    "/degerleme komutu ile baslayabilirsiniz.\n"
    "Ornek: /degerleme Kadikoy, 120, 3+1, 5, 10"
)

_RAPOR_ERROR_MESSAGE = (
    "❌ Rapor olusturulurken bir hata olustu.\n\n"
    "Lutfen tekrar deneyin."
)

# ================================================================
# /kredi Sabitleri
# ================================================================

_KREDI_USAGE_MESSAGE = (
    "💰 Kredi Hesaplama Komutu Kullanimi:\n\n"
    "/kredi <tutar> <vade_ay> <pesinat_yuzde>\n\n"
    "Ornekler:\n"
    "/kredi 2500000 180 30\n"
    "/kredi 2.5m 15y 30\n"
    "/kredi 500k 60 20\n\n"
    "Kisaltmalar:\n"
    "• m = milyon (orn: 2.5m = 2.500.000)\n"
    "• k = bin (orn: 500k = 500.000)\n"
    "• y = yil (orn: 15y = 180 ay)\n\n"
    "Limitler:\n"
    "• Tutar: 100.000 - 50.000.000 ₺\n"
    "• Vade: 12 - 360 ay\n"
    "• Pesinat: %10 - %90"
)

_KREDI_ERROR_MESSAGE = (
    "❌ Kredi hesaplama sirasinda bir hata olustu.\n\n"
    "Lutfen tekrar deneyin."
)

# ================================================================
# /fotograf + Virtual Staging Sabitleri
# ================================================================

_FOTOGRAF_WELCOME_MESSAGE = (
    "📸 Sanal Mobilyalama (Virtual Staging)\n\n"
    "Bos oda fotografinizi gonderin, yapay zeka ile\n"
    "mobilyali hale getirelim!\n\n"
    "Lutfen bos bir oda fotografi gonderin."
)

_FOTOGRAF_NOT_EMPTY_MESSAGE = (
    "⚠️ Bu oda bos gorunmuyor.\n\n"
    "Virtual staging yalnizca bos veya mobilyasiz odalar icin calisir.\n"
    "Lutfen bos bir oda fotografi gonderin."
)

_FOTOGRAF_STYLE_PROMPT = (
    "✅ Oda analizi tamamlandi!\n\nOda tipi: {room_type}\n\nLutfen bir mobilya tarzi secin:"
)

_FOTOGRAF_EXPIRED_MESSAGE = (
    "⚠️ Fotograf suresi dolmus (5 dk).\n\nLutfen yeni bir fotograf gonderin."
)

_STAGING_PROCESSING_MESSAGE = (
    "⏳ Fotografiniz isleniyor...\n\n"
    "Yapay zeka {style} tarzinda mobilyalama yapiyor.\n"
    "Bu islem 15-30 saniye surebilir."
)

_STAGING_QUOTA_MESSAGE = (
    "⚠️ Sahneleme kotaniz doldu.\n\n"
    "Mevcut planinizdaki sahneleme limitine ulastiniz.\n"
    "Daha fazla sahneleme icin planinizi yukseltebilirsiniz."
)

_STAGING_NOT_LINKED_MESSAGE = (
    "❌ Hesabiniz baglanmamis.\n\n"
    "Bu ozelligi kullanabilmek icin once Telegram hesabinizi\n"
    "web panelden baglamaniz gerekiyor.\n\n"
    "Web panel → Ayarlar → Telegram Bagla"
)

_STAGING_ERROR_MESSAGE = (
    "❌ Sahneleme sirasinda bir hata olustu.\n\n"
    "Lutfen tekrar deneyin. Sorun devam ederse destek ile iletisime gecin."
)

_STAGING_SUCCESS_MESSAGE = (
    "✅ Sanal mobilyalama tamamlandi!\n\nTarz: {style}\nIslem suresi: {duration} saniye"
)

# Tarz secim butonlari: (style_id, emoji_label)
_STAGING_STYLES: list[tuple[str, str]] = [
    ("modern", "🏢 Modern"),
    ("klasik", "🏛️ Klasik"),
    ("minimalist", "⬜ Minimalist"),
    ("skandinav", "🌿 Skandinav"),
    ("bohem", "🎨 Bohem"),
    ("endustriyel", "🔧 Endustriyel"),
]

_STAGING_STYLE_IDS: frozenset[str] = frozenset(s[0] for s in _STAGING_STYLES)

_STAGING_STYLE_LABELS: dict[str, str] = {s[0]: s[1] for s in _STAGING_STYLES}

# Oda tipi → Turkce etiket
_ROOM_TYPE_LABELS_TR: dict[str, str] = {
    "salon": "Salon",
    "yatak_odasi": "Yatak Odasi",
    "mutfak": "Mutfak",
    "banyo": "Banyo",
    "cocuk_odasi": "Cocuk Odasi",
    "calisma_odasi": "Calisma Odasi",
    "yemek_odasi": "Yemek Odasi",
    "antre": "Antre",
}

# Redis key prefix + TTL
_STAGING_REDIS_PREFIX = "staging:photo:"
_STAGING_REDIS_TTL = 300  # 5 dakika

# ================================================================
# /ilan Wizard Sabitleri
# ================================================================

_ILAN_WELCOME_MESSAGE = (
    "📸 Ilan olusturma wizard'ina hosgeldiniz!\n\n"
    "Adim adim ilan taslagi olusturacagiz.\n"
    "Oncelikle emlak fotografini gonderin.\n\n"
    "Iptal icin: /iptal"
)

_ILAN_PHOTO_RECEIVED_MESSAGE = (
    "✅ Fotograf alindi!\n\n"
    "Simdi emlagin konumunu gonderin 📍\n"
    "(veya ilce adini yazin)"
)

_ILAN_LOCATION_RECEIVED_MESSAGE = (
    "🏠 Emlak bilgilerini girin:\n"
    "Alan (m²), Oda sayisi, Bina yasi, Kat\n\n"
    "Ornek: 120 3+1 5 3\n\n"
    "Iptal icin: /iptal"
)

_ILAN_DETAILS_ERROR_MESSAGE = (
    "❌ Girdi formati hatali.\n\n"
    "Dogru format: <m2> <oda> <bina_yasi> <kat>\n"
    "Ornek: 120 3+1 5 3\n\n"
    "Sinirlar:\n"
    "• Alan: 10-1000 m²\n"
    "• Oda: 1+0 — 10+2 formati\n"
    "• Bina yasi: 0-100\n"
    "• Kat: 0-50"
)

_ILAN_DETAILS_MAX_RETRIES_MESSAGE = (
    "❌ Cok fazla hatali giris.\n\n"
    "Wizard iptal edildi. Tekrar baslatmak icin /ilan yazin."
)

_ILAN_CANCEL_MESSAGE = (
    "🗑️ Ilan olusturma islemi iptal edildi.\n\n"
    "Tekrar baslatmak icin /ilan yazin."
)

_ILAN_NO_ACTIVE_MESSAGE = "ℹ️ Aktif bir ilan olusturma islemi bulunmuyor."

_ILAN_PROCESSING_MESSAGE = (
    "⏳ Ilan metniniz hazirlaniyor...\n\n"
    "Yapay zeka ilan metni uretiyor.\n"
    "Bu islem 10-20 saniye surebilir."
)

_ILAN_QUOTA_MESSAGE = (
    "⚠️ Aylik ilan olusturma limitinize ulastiniz.\n\n"
    "Daha fazla ilan olusturmak icin planinizi yukseltebilirsiniz."
)

_ILAN_NOT_LINKED_MESSAGE = (
    "❌ Hesabiniz baglanmamis.\n\n"
    "Bu ozelligi kullanabilmek icin once Telegram hesabinizi\n"
    "web panelden baglamaniz gerekiyor.\n\n"
    "Web panel → Ayarlar → Telegram Bagla"
)

_ILAN_ERROR_MESSAGE = (
    "❌ Ilan olusturma sirasinda bir hata olustu.\n\n"
    "Lutfen tekrar deneyin. /ilan ile yeniden baslayabilirsiniz."
)

_ILAN_ALREADY_ACTIVE_MESSAGE = (
    "⚠️ Zaten aktif bir ilan olusturma isleminiz var.\n\n"
    "Devam etmek icin mevcut adimi tamamlayin\n"
    "veya /iptal ile iptal edin."
)

_ILAN_PHOTO_UPLOAD_ERROR_MESSAGE = (
    "⚠️ Fotograf yuklenirken hata olustu, ama devam edebilirsiniz.\n\n"
    "Simdi emlagin konumunu gonderin 📍\n"
    "(veya ilce adini yazin)"
)

_ILAN_DISTRICT_NOT_FOUND_MESSAGE = (
    "❌ Ilce adi taninmadi.\n\n"
    "Lutfen Istanbul'daki 39 ilceden birini yazin.\n"
    "Ornek: Kadikoy, Besiktas, Uskudar\n\n"
    "Veya konum pini gonderin 📍"
)

# /ilan wizard icin ilce fuzzy-match esik mesafesi
_ILAN_DISTRICT_MAX_DISTANCE = 3

# ================================================================
# Standart Hata Mesajlari (TASK-139)
# ================================================================

_ERROR_MESSAGES: dict[str, str] = {
    "general": "❌ Bir hata olustu. Lutfen tekrar deneyin.\n\n📋 Referans: {request_id}",
    "quota": (
        "⚠️ Kota limitinize ulastiniz. Plan yukseltmek icin /help yazin."
        "\n\n📋 Referans: {request_id}"
    ),
    "not_found": "🔍 Istenen kayit bulunamadi.\n\n📋 Referans: {request_id}",
    "permission": "🔒 Bu islem icin yetkiniz yok.\n\n📋 Referans: {request_id}",
    "timeout": (
        "⏳ Islem zaman asimina ugradi. Lutfen tekrar deneyin."
        "\n\n📋 Referans: {request_id}"
    ),
    "invalid_input": (
        "📝 Girdi formati hatali. Lutfen dogru formati kullanin."
        "\n\n📋 Referans: {request_id}"
    ),
}

# Conversation state max retries
_ILAN_MAX_RETRIES = 3

# Tip kisaltmalari → tam tip adi
_CUSTOMER_TYPE_MAP: dict[str, str] = {
    "a": "buyer",
    "s": "seller",
    "k": "renter",
    "e": "landlord",
}

# Tip adi → Turkce etiket
_CUSTOMER_TYPE_LABELS: dict[str, str] = {
    "buyer": "Alici",
    "seller": "Satici",
    "renter": "Kiraci",
    "landlord": "Ev Sahibi",
}

# Istanbul ilce merkez koordinatlari (yaklasik)
_DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    "adalar": (40.8765, 29.0923),
    "arnavutkoy": (41.1843, 28.7396),
    "atasehir": (40.9923, 29.1244),
    "avcilar": (40.9796, 28.7217),
    "bagcilar": (41.0368, 28.8567),
    "bahcelievler": (41.0018, 28.8597),
    "bakirkoy": (40.9819, 28.8721),
    "basaksehir": (41.0933, 28.8020),
    "bayrampasa": (41.0440, 28.9120),
    "besiktas": (41.0422, 29.0083),
    "beykoz": (41.1327, 29.0955),
    "beylikduzu": (41.0027, 28.6407),
    "beyoglu": (41.0370, 28.9770),
    "buyukcekmece": (41.0237, 28.5847),
    "catalca": (41.1437, 28.4610),
    "cekmekoy": (41.0573, 29.1793),
    "esenler": (41.0437, 28.8737),
    "esenyurt": (41.0287, 28.6727),
    "eyupsultan": (41.0480, 28.9340),
    "fatih": (41.0190, 28.9490),
    "gaziosmanpasa": (41.0653, 28.9133),
    "gungoren": (41.0160, 28.8820),
    "kadikoy": (40.9927, 29.0277),
    "kagithane": (41.0787, 28.9717),
    "kartal": (40.8893, 29.1917),
    "kucukcekmece": (41.0023, 28.7810),
    "maltepe": (40.9337, 29.1577),
    "pendik": (40.8767, 29.2337),
    "sancaktepe": (41.0010, 29.2340),
    "sariyer": (41.1673, 29.0567),
    "silivri": (41.0737, 28.2467),
    "sultanbeyli": (40.9573, 29.2627),
    "sultangazi": (41.1057, 28.8667),
    "sile": (41.1773, 29.6127),
    "sisli": (41.0607, 28.9873),
    "tuzla": (40.8167, 29.2997),
    "umraniye": (41.0167, 29.1167),
    "uskudar": (41.0247, 29.0157),
    "zeytinburnu": (41.0037, 28.9010),
}


# ================================================================
# TelegramBotHandler
# ================================================================


class TelegramBotHandler:
    """
    Telegram bot komut isleyicisi.

    Webhook'tan gelen IncomingMessage'lari analiz eder ve uygun handler'a
    yonlendirir. Komut disinda kalan mesajlar echo olarak geri doner.

    Args:
        telegram_adapter: Mesaj gondermek icin TelegramAdapter instance'i.
        auth_bridge: Deep link dogrulama icin TelegramAuthBridge instance'i.
        session_factory: SQLAlchemy async_sessionmaker — DB erisimi gerektiren
            komutlar icin (orn: /musteri).
        redis_client: Redis async client — staging fotograf gecici depolama icin.
    """

    def __init__(
        self,
        telegram_adapter: TelegramAdapter,
        auth_bridge: TelegramAuthBridge,
        session_factory: async_sessionmaker[AsyncSession],
        redis_client: aioredis.Redis | None = None,
    ) -> None:
        self._adapter = telegram_adapter
        self._auth_bridge = auth_bridge
        self._session_factory = session_factory
        self._redis = redis_client
        self._conv: ConversationStateManager | None = (
            ConversationStateManager(redis_client) if redis_client else None
        )
        logger.info("telegram_bot_handler_initialized")

    # ================================================================
    # Public — Ana giris noktasi
    # ================================================================

    async def handle(self, incoming: IncomingMessage) -> None:
        """
        Gelen mesaji analiz edip uygun handler'a yonlendirir.

        Akis:
            1. Callback query kontrol et (staging:*, ilan:*, match:* prefix)
            2. Fotograf mesaji kontrol et (media_url != None, komut degil)
            3. content bos mu kontrol et
            4. Komut parse et (/ ile baslayan ilk kelime)
            5. Komut handler'a yonlendir veya echo yap
            6. Hata durumunda loglayip sessizce gec

        Args:
            incoming: Webhook'tan parse edilmis IncomingMessage.

        Not:
            Bu metot ASLA exception firlatmaz.
            Webhook handler her zaman 200 dondurmeli.
        """
        try:
            content = incoming.content.strip()
            sender_id = incoming.sender_id

            # -- Callback query: staging tarz secimi --
            if content.startswith("staging:"):
                await self._handle_staging_callback(incoming)
                return

            # -- Callback query: ilan wizard onay/iptal/yeniden --
            if content.startswith("ilan:"):
                await self._handle_ilan_callback(incoming)
                return

            # -- Callback query: eslesme ilgileniyorum/gec --
            if content.startswith("match:"):
                await self._handle_match_callback(incoming)
                return

            # -- /ilan ve /iptal komutlari once kontrol --
            if content.startswith("/"):
                _cmd_part = content.split()[0]
                _cmd = _cmd_part.split("@")[0].lower()

                if _cmd == "/ilan":
                    await self._handle_ilan(incoming)
                    return
                if _cmd == "/iptal":
                    await self._handle_iptal(incoming)
                    return

            # -- Aktif wizard varsa: mesaji wizard handler'a yonlendir --
            conv_state = await self._get_conv_state(sender_id)
            if conv_state is not None:
                # Fotograf mesaji + PHOTO state
                if incoming.media_url and conv_state.step == WizardStep.PHOTO:
                    await self._handle_wizard_photo(incoming, conv_state)
                    return
                # Konum veya ilce adi + LOCATION state
                if conv_state.step == WizardStep.LOCATION:
                    await self._handle_wizard_location(incoming, conv_state)
                    return
                # Emlak detaylari + DETAILS state (komut degilse)
                if (
                    conv_state.step == WizardStep.DETAILS
                    and not content.startswith("/")
                ):
                    await self._handle_wizard_details(incoming, conv_state)
                    return

            # -- Fotograf mesaji: media_url var ve komut degil --
            #    (conversation state yoksa eski staging akisi)
            if incoming.media_url and not content.startswith("/"):
                await self._handle_photo_message(incoming)
                return

            if not content:
                logger.debug(
                    "telegram_bot_empty_content",
                    sender_id=sender_id,
                )
                return

            # Komut parse — /command veya /command@botname formatini destekle
            if content.startswith("/"):
                command_part = content.split()[0]  # "/start" veya "/start@botname"
                command = command_part.split("@")[0].lower()  # "/start"

                if command == "/start":
                    await self._handle_start(incoming)
                elif command == "/help":
                    await self._handle_help(incoming)
                elif command == "/degerleme":
                    await self._handle_degerleme(incoming)
                elif command == "/musteri":
                    await self._handle_musteri(incoming)
                elif command == "/fotograf":
                    await self._handle_fotograf(incoming)
                elif command == "/kredi":
                    await self._handle_kredi(incoming)
                elif command == "/portfoy":
                    await self._handle_portfoy(incoming)
                elif command == "/rapor":
                    await self._handle_rapor(incoming)
                else:
                    # Bilinmeyen komut — echo olarak geri gonder
                    await self._handle_echo(incoming)
            else:
                await self._handle_echo(incoming)

        except Exception as exc:
            # KRITIK: Webhook handler 200 dondurmeli — exception firlatma
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="handle",
                request_id=request_id,
                user_id=incoming.sender_id,
                chat_id=incoming.sender_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )

    # ================================================================
    # Private — Komut Handler'lar
    # ================================================================

    async def _handle_start(self, incoming: IncomingMessage) -> None:
        """
        /start komutu handler'i.

        Iki senaryo:
            1. /start {token} — Deep link ile hesap baglama
            2. /start — Karsilama mesaji

        Deep link akisi:
            - Token parse edilir
            - TelegramAuthBridge.verify_and_link() cagrilir
            - Basarili → onay mesaji, basarisiz → hata mesaji
        """
        parts = incoming.content.strip().split(maxsplit=1)

        if len(parts) > 1:
            # Deep link token var — hesap baglama denemesi
            token = parts[1].strip()
            await self._handle_deep_link(incoming.sender_id, token)
        else:
            # Basit /start — karsilama mesaji
            await self._send_reply(incoming.sender_id, _WELCOME_MESSAGE)

        logger.info(
            "telegram_bot_start_handled",
            sender_id=incoming.sender_id,
            has_token=len(parts) > 1,
        )

    async def _handle_help(self, incoming: IncomingMessage) -> None:
        """
        /help komutu handler'i — kullanilabilir komutlari listeler.
        """
        await self._send_reply(incoming.sender_id, _HELP_MESSAGE)

        logger.info(
            "telegram_bot_help_handled",
            sender_id=incoming.sender_id,
        )

    async def _handle_echo(self, incoming: IncomingMessage) -> None:
        """
        Echo handler — gelen mesaji aynen geri gonderir.

        Komut olmayan tum mesajlar buraya duser.
        """
        echo_text = f"🔄 {incoming.content}"
        await self._send_reply(incoming.sender_id, echo_text)

        logger.debug(
            "telegram_bot_echo_handled",
            sender_id=incoming.sender_id,
            content_preview=incoming.content[:50],
        )

    async def _handle_degerleme(self, incoming: IncomingMessage) -> None:
        """
        /degerleme komutu handler'i — AI ile konut degerleme.

        Format: /degerleme <ilce>, <m2>, <oda>, <kat>, <bina_yasi>
        Ornek: /degerleme Kadikoy, 120, 3+1, 5, 10

        Akis:
            1. Parametreleri parse et (5 adet, virgul ile ayrılmis)
            2. Oda formatini ayristir (3+1 → room=3, living=1)
            3. Eksik feature'lar icin makul varsayilan deger ata
            4. InferenceService.predict_quick() cagir
            5. Sonucu formatla ve gonder
        """
        content = incoming.content.strip()
        parts = content.split(maxsplit=1)

        if len(parts) < 2:
            await self._send_reply(incoming.sender_id, _DEGERLEME_USAGE_MESSAGE)
            logger.info(
                "telegram_bot_degerleme_no_params",
                sender_id=incoming.sender_id,
            )
            return

        params = [p.strip() for p in parts[1].split(",")]

        if len(params) != 5:
            await self._send_reply(incoming.sender_id, _DEGERLEME_USAGE_MESSAGE)
            logger.info(
                "telegram_bot_degerleme_wrong_param_count",
                sender_id=incoming.sender_id,
                param_count=len(params),
            )
            return

        try:
            district = params[0].strip()
            net_sqm = float(params[1].strip())
            room_str = params[2].strip()
            floor = int(params[3].strip())
            building_age = int(params[4].strip())
        except (ValueError, IndexError):
            await self._send_reply(incoming.sender_id, _DEGERLEME_USAGE_MESSAGE)
            return

        # Oda formatini parse et: "3+1" → (3, 1)
        room_count, living_room_count = _parse_room_format(room_str)

        # Ilce adini model formatina donustur (ASCII)
        district_normalized = _normalize_district(district)

        # Koordinat lookup
        lat, lon = _DISTRICT_COORDS.get(district_normalized.lower(), (41.0, 29.0))

        input_data = {
            "district": district_normalized,
            "neighborhood": "Merkez",
            "property_type": "Daire",
            "gross_sqm": round(net_sqm * 1.2),
            "net_sqm": net_sqm,
            "room_count": room_count,
            "living_room_count": living_room_count,
            "floor": floor,
            "total_floors": max(floor + 3, 5),
            "building_age": building_age,
            "bathroom_count": 1,
            "has_balcony": 1,
            "parking_type": "Yok",
            "has_elevator": 1 if floor > 4 else 0,
            "heating_type": "Dogalgaz Kombi",
            "lat": lat,
            "lon": lon,
            "earthquake_risk_score": 0.5,
            "transport_score": 0.5,
            "socioeconomic_level": 0.5,
        }

        try:
            from src.modules.valuations.inference_service import InferenceService

            service = InferenceService.get_instance()
            result = service.predict_quick(input_data)

            estimated = _format_price(result["estimated_price"])
            low = _format_price(result["confidence_low"])
            high = _format_price(result["confidence_high"])
            confidence_pct = int(result.get("confidence_level", 0.80) * 100)

            response = (
                f"🏠 Degerleme Sonucu\n\n"
                f"Ilce: {district}\n"
                f"Alan: {net_sqm:.0f} m² | Oda: {room_str}\n"
                f"Kat: {floor} | Bina Yasi: {building_age}\n\n"
                f"💰 Tahmini Deger: {low} - {high} TL\n"
                f"📊 Ortalama: {estimated} TL\n"
                f"🎯 Guven: %{confidence_pct}\n\n"
                f"ℹ️ Bu tahmin AI modeline dayali yaklasik bir degerdir."
            )

            await self._send_reply(incoming.sender_id, response)

            logger.info(
                "telegram_bot_degerleme_success",
                sender_id=incoming.sender_id,
                district=district_normalized,
                net_sqm=net_sqm,
                estimated_price=result["estimated_price"],
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="degerleme",
                request_id=request_id,
                user_id=incoming.sender_id,
                chat_id=incoming.sender_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(incoming.sender_id, "general", request_id)

    async def _handle_musteri(self, incoming: IncomingMessage) -> None:
        """
        /musteri komutu handler'i — hizli musteri kaydi.

        Format: /musteri <ad>, <telefon>[, <tip>[, <butce_min>, <butce_max>]]
        Ornekler:
            /musteri Ahmet Yilmaz, 05321234567
            /musteri Ahmet Yilmaz, 05321234567, a
            /musteri Ahmet Yilmaz, 05321234567, a, 1000000, 3000000

        Tip kisaltmalari: a=buyer, s=seller, k=renter, e=landlord

        Akis:
            1. Parametreleri parse et (virgul ile ayrilmis)
            2. Minimum 2 parametre kontrolu (ad + telefon)
            3. Tip varsa normalize et (kisaltma → tam ad)
            4. Linked account kontrolu (chat_id → user)
            5. Kota kontrolu (plan limiti)
            6. CustomerService.create() ile kayit
            7. Basarili → onay mesaji, hata → Turkce hata mesaji
        """
        try:
            content = incoming.content.strip()
            parts = content.split(maxsplit=1)

            # -- 1. Parametre yoksa kullanim rehberi goster --
            if len(parts) < 2:
                await self._send_reply(incoming.sender_id, _MUSTERI_USAGE_MESSAGE)
                logger.info(
                    "telegram_bot_musteri_no_params",
                    sender_id=incoming.sender_id,
                )
                return

            # -- 2. Parametreleri parse et --
            params = [p.strip() for p in parts[1].split(",")]

            if len(params) < 2:
                await self._send_reply(incoming.sender_id, _MUSTERI_USAGE_MESSAGE)
                logger.info(
                    "telegram_bot_musteri_insufficient_params",
                    sender_id=incoming.sender_id,
                    param_count=len(params),
                )
                return

            full_name = params[0].strip()
            phone = params[1].strip()

            if not full_name or not phone:
                await self._send_reply(incoming.sender_id, _MUSTERI_USAGE_MESSAGE)
                return

            # -- 3. Tip normalize et --
            customer_type = "buyer"  # varsayilan
            if len(params) >= 3:
                type_shortcut = params[2].strip().lower()
                if type_shortcut in _CUSTOMER_TYPE_MAP:
                    customer_type = _CUSTOMER_TYPE_MAP[type_shortcut]
                else:
                    await self._send_reply(incoming.sender_id, _MUSTERI_USAGE_MESSAGE)
                    logger.info(
                        "telegram_bot_musteri_invalid_type",
                        sender_id=incoming.sender_id,
                        type_shortcut=type_shortcut,
                    )
                    return

            # -- Butce parse et (opsiyonel) --
            budget_min: float | None = None
            budget_max: float | None = None
            if len(params) >= 5:
                try:
                    budget_min = float(params[3].strip())
                    budget_max = float(params[4].strip())
                except ValueError:
                    await self._send_reply(incoming.sender_id, _MUSTERI_USAGE_MESSAGE)
                    logger.info(
                        "telegram_bot_musteri_invalid_budget",
                        sender_id=incoming.sender_id,
                    )
                    return

            # -- 4. Linked account kontrolu --
            user = await self._auth_bridge.get_user_by_chat_id(incoming.sender_id)
            if user is None:
                await self._send_reply(incoming.sender_id, _MUSTERI_NOT_LINKED_MESSAGE)
                logger.info(
                    "telegram_bot_musteri_not_linked",
                    sender_id=incoming.sender_id,
                )
                return

            office_id = user.office_id

            # -- 5. Kota kontrolu + 6. Musteri olustur (tek transaction) --
            async with self._session_factory() as db:
                # Subscription sorgula → plan_type al
                from src.models.subscription import Subscription

                sub_result = await db.execute(
                    select(Subscription)
                    .where(
                        Subscription.office_id == office_id,
                        Subscription.status.in_(["trial", "active"]),
                    )
                    .order_by(Subscription.created_at.desc())
                    .limit(1)
                )
                subscription = sub_result.scalar_one_or_none()

                plan_type = subscription.plan_type if subscription else "starter"

                # Kota kontrolu
                from src.core.plan_policy import get_customer_quota
                from src.modules.customers.service import CustomerService

                quota = get_customer_quota(plan_type)

                if quota != -1:
                    current_count = await CustomerService.count_for_office(db, office_id)
                    if current_count >= quota:
                        await self._send_reply(incoming.sender_id, _MUSTERI_QUOTA_MESSAGE)
                        logger.info(
                            "telegram_bot_musteri_quota_exceeded",
                            sender_id=incoming.sender_id,
                            office_id=str(office_id),
                            current_count=current_count,
                            quota=quota,
                        )
                        return

                # Musteri olustur
                customer_data: dict[str, str | float | None] = {
                    "full_name": full_name,
                    "phone": phone,
                    "customer_type": customer_type,
                    "source": "telegram",
                }
                if budget_min is not None:
                    customer_data["budget_min"] = budget_min
                if budget_max is not None:
                    customer_data["budget_max"] = budget_max

                customer = await CustomerService.create(db, office_id, customer_data)
                await db.commit()

            # -- 7. Basarili → onay mesaji --
            type_label = _CUSTOMER_TYPE_LABELS.get(customer_type, customer_type)

            budget_text = ""
            if budget_min is not None and budget_max is not None:
                budget_text = (
                    f"\nButce: {_format_price(budget_min)} - {_format_price(budget_max)} TL"
                )

            success_msg = (
                f"✅ Musteri basariyla kaydedildi!\n\n"
                f"Ad: {full_name}\n"
                f"Telefon: {phone}\n"
                f"Tip: {type_label}"
                f"{budget_text}"
            )

            await self._send_reply(incoming.sender_id, success_msg)

            logger.info(
                "telegram_bot_musteri_success",
                sender_id=incoming.sender_id,
                office_id=str(office_id),
                customer_id=str(customer.id),
                customer_type=customer_type,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="musteri",
                request_id=request_id,
                user_id=incoming.sender_id,
                chat_id=incoming.sender_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(incoming.sender_id, "general", request_id)

    # ================================================================
    # Private — /portfoy Handler
    # ================================================================

    async def _handle_portfoy(self, incoming: IncomingMessage) -> None:
        """
        /portfoy komutu handler'i — ofis portfoy listesi.

        Kullanicinin ofisindeki aktif ilanlari listeler (son 5 ilan).

        Akis:
            1. Linked account kontrolu (chat_id → user)
            2. Kullanicinin office_id'si ile aktif ilanlari sorgula
            3. Son 5 ilani formatla ve gonder
            4. Toplam ilan sayisini goster
        """
        try:
            # 1. Linked account kontrolu
            user = await self._auth_bridge.get_user_by_chat_id(incoming.sender_id)
            if user is None:
                await self._send_reply(incoming.sender_id, _PORTFOY_NOT_LINKED_MESSAGE)
                logger.info(
                    "telegram_bot_portfoy_not_linked",
                    sender_id=incoming.sender_id,
                )
                return

            office_id = user.office_id

            # 2. Aktif ilanlari sorgula
            async with self._session_factory() as db:
                from src.models.property import Property

                # Toplam aktif ilan sayisi
                total_result = await db.execute(
                    select(func.count(Property.id)).where(
                        Property.office_id == office_id,
                        Property.status == "active",
                    )
                )
                total_count = total_result.scalar_one()

                if total_count == 0:
                    await self._send_reply(
                        incoming.sender_id, _PORTFOY_EMPTY_MESSAGE
                    )
                    logger.info(
                        "telegram_bot_portfoy_empty",
                        sender_id=incoming.sender_id,
                        office_id=str(office_id),
                    )
                    return

                # Son 5 aktif ilan
                listings_result = await db.execute(
                    select(Property)
                    .where(
                        Property.office_id == office_id,
                        Property.status == "active",
                    )
                    .order_by(Property.created_at.desc())
                    .limit(5)
                )
                listings = list(listings_result.scalars().all())

                # Bugunun goruntulenmesi
                today_views = sum(p.views_count for p in listings)

            # 3. Formatlama
            display_count = len(listings)
            lines = [f"🏠 Portfoyunuz ({display_count}/{total_count} ilan)\n"]

            for i, prop in enumerate(listings, start=1):
                rooms = prop.rooms or ""
                net_area = int(prop.net_area) if prop.net_area else ""
                price_str = _format_price(prop.price)
                area_str = f" {net_area}m²" if net_area else ""
                rooms_str = f" {rooms}" if rooms else ""

                lines.append(
                    f"{i}. {prop.district}{rooms_str}{area_str}"
                    f" — {price_str}₺"
                )

            lines.append(
                f"\n📊 Toplam: {total_count} ilan"
                f" | Bugun: {today_views} goruntullenme"
            )

            response = "\n".join(lines)
            await self._send_reply(incoming.sender_id, response)

            logger.info(
                "telegram_bot_portfoy_success",
                sender_id=incoming.sender_id,
                office_id=str(office_id),
                total_count=total_count,
                displayed=display_count,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="portfoy",
                request_id=request_id,
                user_id=incoming.sender_id,
                chat_id=incoming.sender_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(incoming.sender_id, "general", request_id)

    # ================================================================
    # Private — /rapor Handler
    # ================================================================

    async def _handle_rapor(self, incoming: IncomingMessage) -> None:
        """
        /rapor komutu handler'i — son degerleme raporunu PDF olarak gonder.

        Akis:
            1. Linked account kontrolu (chat_id → user)
            2. Son prediction_log kaydini bul
            3. pdf_service.generate_valuation_pdf() ile PDF olustur
            4. TelegramAdapter.send_document() ile PDF gonder
        """
        try:
            # 1. Linked account kontrolu
            user = await self._auth_bridge.get_user_by_chat_id(incoming.sender_id)
            if user is None:
                await self._send_reply(
                    incoming.sender_id, _RAPOR_NOT_LINKED_MESSAGE
                )
                logger.info(
                    "telegram_bot_rapor_not_linked",
                    sender_id=incoming.sender_id,
                )
                return

            office_id = user.office_id

            # 2. Son prediction_log kaydini bul
            async with self._session_factory() as db:
                from src.models.prediction_log import PredictionLog

                pred_result = await db.execute(
                    select(PredictionLog)
                    .where(PredictionLog.office_id == office_id)
                    .order_by(PredictionLog.created_at.desc())
                    .limit(1)
                )
                prediction = pred_result.scalar_one_or_none()

            if prediction is None:
                await self._send_reply(
                    incoming.sender_id, _RAPOR_NO_VALUATION_MESSAGE
                )
                logger.info(
                    "telegram_bot_rapor_no_prediction",
                    sender_id=incoming.sender_id,
                    office_id=str(office_id),
                )
                return

            # 3. PDF olustur
            import asyncio

            from src.services.pdf_service import generate_valuation_pdf

            input_data = prediction.input_data or {}
            output_data = prediction.output_data or {}

            valuation_data = {
                "prediction_id": str(prediction.id),
                "report_date": prediction.created_at.strftime("%d.%m.%Y"),
                "district": input_data.get("district", ""),
                "neighborhood": input_data.get("neighborhood", ""),
                "property_type": input_data.get(
                    "property_type", "Daire"
                ),
                "net_sqm": input_data.get("net_sqm", 0),
                "gross_sqm": input_data.get("gross_sqm", 0),
                "room_count": input_data.get("room_count", 0),
                "living_room_count": input_data.get(
                    "living_room_count", 0
                ),
                "floor": input_data.get("floor", 0),
                "total_floors": input_data.get("total_floors", 0),
                "building_age": input_data.get("building_age", 0),
                "heating_type": input_data.get("heating_type", ""),
                "estimated_price": output_data.get(
                    "estimated_price", 0
                ),
                "min_price": output_data.get("confidence_low", 0),
                "max_price": output_data.get("confidence_high", 0),
                "price_per_sqm": output_data.get("price_per_sqm", 0),
                "confidence": prediction.confidence or 0.80,
                "model_version": prediction.model_version,
                "user_info": {
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                },
            }

            # WeasyPrint sync calisir — asyncio.to_thread ile cagir
            pdf_bytes = await asyncio.to_thread(
                generate_valuation_pdf, valuation_data
            )

            # 4. PDF gonder
            report_date = prediction.created_at.strftime("%d.%m.%Y")
            caption = f"📄 Degerleme Raporu — {report_date}"
            filename = (
                f"degerleme_raporu_"
                f"{prediction.created_at.strftime('%Y%m%d')}.pdf"
            )

            result = await self._adapter.send_document(
                chat_id=incoming.sender_id,
                file_bytes=pdf_bytes,
                filename=filename,
                caption=caption,
            )

            if not result.success:
                await self._send_reply(
                    incoming.sender_id, _RAPOR_ERROR_MESSAGE
                )
                logger.error(
                    "telegram_bot_rapor_send_failed",
                    sender_id=incoming.sender_id,
                    error=result.error,
                )
                return

            logger.info(
                "telegram_bot_rapor_success",
                sender_id=incoming.sender_id,
                office_id=str(office_id),
                prediction_id=str(prediction.id),
                pdf_size_bytes=len(pdf_bytes),
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="rapor",
                request_id=request_id,
                user_id=incoming.sender_id,
                chat_id=incoming.sender_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(incoming.sender_id, "general", request_id)

    # ================================================================
    # Private — /kredi Handler
    # ================================================================

    async def _handle_kredi(self, incoming: IncomingMessage) -> None:
        """
        /kredi komutu handler'i — konut kredisi hesaplama.

        Format: /kredi <tutar> <vade_ay> <pesinat_yuzde>
        Ornekler:
            /kredi 2500000 180 30
            /kredi 2.5m 15y 30
            /kredi 500k 60 20

        Kisaltmalar: m=milyon, k=bin, y=yil

        Akis:
            1. Parametreleri parse et (3 adet, bosluk ile ayrilmis)
            2. Validasyon (tutar, vade, pesinat araliklari)
            3. Kredi tutari hesapla: tutar * (1 - pesinat/100)
            4. CreditCalculatorService ile aylik taksit hesapla
            5. get_bank_rates() ile en uygun 3 bankayi bul
            6. Sonucu formatla ve gonder

        NOT: Kota kontrolu GEREKMEZ — bedava ozellik.
        """
        try:
            content = incoming.content.strip()
            parts = content.split()

            # -- 1. Parametre yoksa kullanim rehberi goster --
            if len(parts) != 4:
                await self._send_reply(incoming.sender_id, _KREDI_USAGE_MESSAGE)
                logger.info(
                    "telegram_bot_kredi_wrong_params",
                    sender_id=incoming.sender_id,
                    param_count=len(parts) - 1,
                )
                return

            # -- 2. Parametreleri parse et --
            try:
                tutar = _parse_amount(parts[1])
                vade_ay = _parse_term(parts[2])
                pesinat_pct = int(parts[3])
            except (ValueError, InvalidParamError):
                await self._send_reply(incoming.sender_id, _KREDI_USAGE_MESSAGE)
                logger.info(
                    "telegram_bot_kredi_parse_error",
                    sender_id=incoming.sender_id,
                    raw_params=parts[1:],
                )
                return

            # -- 3. Validasyon --
            if tutar < 100_000 or tutar > 50_000_000:
                await self._send_reply(incoming.sender_id, _KREDI_USAGE_MESSAGE)
                return
            if vade_ay < 12 or vade_ay > 360:
                await self._send_reply(incoming.sender_id, _KREDI_USAGE_MESSAGE)
                return
            if pesinat_pct < 10 or pesinat_pct > 90:
                await self._send_reply(incoming.sender_id, _KREDI_USAGE_MESSAGE)
                return

            # -- 4. Kredi tutari hesapla --
            from decimal import Decimal

            from src.modules.calculator.bank_rates import get_bank_rates
            from src.modules.calculator.calculator_service import (
                CreditCalculatorService,
            )

            pesinat_tutari = tutar * pesinat_pct / 100
            kredi_tutari = tutar - pesinat_tutari
            principal = Decimal(str(int(kredi_tutari)))

            # -- 5. En uygun 3 bankayi bul --
            bank_rates = get_bank_rates()

            # Vade ve tutar uygunlugu kontrolu + siralama
            uygun_bankalar: list[dict] = []
            for rate in bank_rates:
                if rate.min_term <= vade_ay <= rate.max_term and (
                    rate.min_amount <= principal <= rate.max_amount
                ):
                    monthly = CreditCalculatorService.calculate_monthly_payment(
                        principal=principal,
                        annual_rate=rate.annual_rate,
                        months=vade_ay,
                    )
                    total = CreditCalculatorService.calculate_total_payment(
                        monthly=monthly,
                        months=vade_ay,
                    )
                    uygun_bankalar.append(
                        {
                            "bank_name": rate.bank_name,
                            "annual_rate": rate.annual_rate,
                            "monthly": monthly,
                            "total": total,
                        }
                    )

            # En dusuk taksit sirasina gore sirala
            uygun_bankalar.sort(key=lambda b: b["monthly"])
            top3 = uygun_bankalar[:3]

            # -- 6. Sonuc mesaji olustur --
            vade_yil = vade_ay // 12
            vade_kalan_ay = vade_ay % 12
            vade_str = f"{vade_ay} ay"
            if vade_kalan_ay == 0 and vade_yil > 0:
                vade_str = f"{vade_ay} ay ({vade_yil} yil)"
            elif vade_yil > 0:
                vade_str = f"{vade_ay} ay ({vade_yil} yil {vade_kalan_ay} ay)"

            lines = [
                "🏠 Kredi Hesaplama Sonucu\n",
                f"Emlak Fiyati: {_format_price(tutar)} ₺",
                f"Pesinat (%{pesinat_pct}): {_format_price(pesinat_tutari)} ₺",
                f"Kredi Tutari: {_format_price(kredi_tutari)} ₺",
                f"Vade: {vade_str}",
            ]

            if top3:
                lines.append("\n💰 En Uygun 3 Banka:\n")
                rank_emojis = ["1️⃣", "2️⃣", "3️⃣"]
                for i, bank in enumerate(top3):
                    lines.append(f"{rank_emojis[i]} {bank['bank_name']}")
                    lines.append(
                        f"   Faiz: %{bank['annual_rate']} | "
                        f"Taksit: {_format_price(bank['monthly'])} ₺"
                    )
                    lines.append(
                        f"   Toplam: {_format_price(bank['total'])} ₺\n"
                    )
            else:
                lines.append(
                    "\n⚠️ Bu kosullara uygun banka bulunamadi.\n"
                    "Vade veya tutar araligini degistirmeyi deneyin."
                )

            lines.append("📊 Detayli hesaplama icin: https://emlak.app/kredi")

            response = "\n".join(lines)
            await self._send_reply(incoming.sender_id, response)

            logger.info(
                "telegram_bot_kredi_success",
                sender_id=incoming.sender_id,
                tutar=tutar,
                vade_ay=vade_ay,
                pesinat_pct=pesinat_pct,
                kredi_tutari=float(kredi_tutari),
                top_bank=top3[0]["bank_name"] if top3 else None,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="kredi",
                request_id=request_id,
                user_id=incoming.sender_id,
                chat_id=incoming.sender_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(incoming.sender_id, "general", request_id)

    # ================================================================
    # Private — /fotograf + Virtual Staging Handler'lar
    # ================================================================

    async def _handle_fotograf(self, incoming: IncomingMessage) -> None:
        """
        /fotograf komutu handler'i — sanal mobilyalama baslatma.

        Kullaniciya bilgilendirme mesaji gonderir ve fotograf gondermesini ister.
        """
        await self._send_reply(incoming.sender_id, _FOTOGRAF_WELCOME_MESSAGE)

        logger.info(
            "telegram_bot_fotograf_handled",
            sender_id=incoming.sender_id,
        )

    async def _handle_photo_message(self, incoming: IncomingMessage) -> None:
        """
        Fotograf mesaj handler'i — oda analizi + tarz secim menusu.

        Akis:
            1. Telegram API'den fotoyu indir (file_id → bytes)
            2. staging_service.analyze_room() ile oda analizi
            3. Bos degilse uyari mesaji
            4. Bossa Redis'e kaydet (base64, 5dk TTL)
            5. 6 tarz secenekli InlineKeyboard gonder

        NOT: Redis client yoksa islem yapilamaz (graceful degrade).
        """
        chat_id = incoming.sender_id

        if self._redis is None:
            logger.warning(
                "telegram_bot_photo_no_redis",
                sender_id=chat_id,
            )
            await self._send_reply(chat_id, _STAGING_ERROR_MESSAGE)
            return

        try:
            # 1. Fotoyu indir
            photo_bytes = await self._adapter.download_file(incoming.media_url)

            logger.info(
                "telegram_bot_photo_downloaded",
                sender_id=chat_id,
                photo_size_bytes=len(photo_bytes),
            )

            # 2. Oda analizi
            from src.listings.staging_service import analyze_room

            analysis = await analyze_room(photo_bytes)

            # 3. Bos degil → uyari
            if not analysis.is_empty:
                await self._send_reply(chat_id, _FOTOGRAF_NOT_EMPTY_MESSAGE)
                logger.info(
                    "telegram_bot_photo_not_empty",
                    sender_id=chat_id,
                    room_type=analysis.room_type,
                )
                return

            # 4. Redis'e kaydet (base64, 5dk TTL)
            encoded = base64.b64encode(photo_bytes).decode("ascii")
            redis_key = f"{_STAGING_REDIS_PREFIX}{chat_id}"
            await self._redis.set(redis_key, encoded, ex=_STAGING_REDIS_TTL)

            # 5. Tarz secim menusu
            room_type_label = _ROOM_TYPE_LABELS_TR.get(analysis.room_type, analysis.room_type)
            text = _FOTOGRAF_STYLE_PROMPT.format(room_type=room_type_label)

            buttons = [
                Button(text=label, callback_data=f"staging:{style_id}")
                for style_id, label in _STAGING_STYLES
            ]
            content = MessageContent(text=text, buttons=buttons)
            await self._adapter.send(recipient=chat_id, content=content)

            logger.info(
                "telegram_bot_photo_analyzed",
                sender_id=chat_id,
                room_type=analysis.room_type,
                is_empty=True,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="photo_message",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)

    async def _handle_staging_callback(self, incoming: IncomingMessage) -> None:
        """
        Staging tarz secimi callback handler'i.

        callback_data formati: "staging:{style_id}"

        Akis:
            1. Callback query'yi yanitla (loading indicator kaldir)
            2. Style ID parse + validasyon
            3. Linked account kontrolu
            4. Redis'ten fotograf al
            5. Kota kontrolu (QuotaType.STAGING)
            6. Isleniyor mesaji gonder
            7. virtual_stage() ile sahneleme
            8. Sonuc fotografini gonder
            9. Kota sayacini artir + Redis temizle
        """
        chat_id = incoming.sender_id

        # 1. Callback query yanitla
        cq_id = incoming.raw_payload.get("callback_query", {}).get("id")
        if cq_id:
            await self._adapter.answer_callback_query(cq_id)

        try:
            # 2. Style ID parse
            style_id = incoming.content.split(":", 1)[1]
            if style_id not in _STAGING_STYLE_IDS:
                await self._send_reply(chat_id, _STAGING_ERROR_MESSAGE)
                return

            # 3. Linked account kontrolu
            user = await self._auth_bridge.get_user_by_chat_id(chat_id)
            if user is None:
                await self._send_reply(chat_id, _STAGING_NOT_LINKED_MESSAGE)
                logger.info(
                    "telegram_bot_staging_not_linked",
                    sender_id=chat_id,
                )
                return

            # 4. Redis'ten fotograf al
            if self._redis is None:
                await self._send_reply(chat_id, _STAGING_ERROR_MESSAGE)
                return

            redis_key = f"{_STAGING_REDIS_PREFIX}{chat_id}"
            encoded = await self._redis.get(redis_key)
            if encoded is None:
                await self._send_reply(chat_id, _FOTOGRAF_EXPIRED_MESSAGE)
                logger.info(
                    "telegram_bot_staging_photo_expired",
                    sender_id=chat_id,
                )
                return

            photo_bytes = base64.b64decode(encoded)

            # 5. Kota kontrolu
            office_id = user.office_id
            async with self._session_factory() as db:
                from src.models.subscription import Subscription
                from src.modules.valuations.quota_service import (
                    QuotaType,
                    check_credit,
                    check_quota,
                    increment_quota,
                    use_credit,
                )

                sub_result = await db.execute(
                    select(Subscription)
                    .where(
                        Subscription.office_id == office_id,
                        Subscription.status.in_(["trial", "active"]),
                    )
                    .order_by(Subscription.created_at.desc())
                    .limit(1)
                )
                subscription = sub_result.scalar_one_or_none()
                plan_type = subscription.plan_type if subscription else "starter"

                is_allowed, _used, _limit = await check_quota(
                    db, office_id, plan_type, QuotaType.STAGING
                )

                if not is_allowed:
                    has_credit = await check_credit(db, office_id, plan_type, QuotaType.STAGING)
                    if not has_credit:
                        await self._send_reply(chat_id, _STAGING_QUOTA_MESSAGE)
                        logger.info(
                            "telegram_bot_staging_quota_exceeded",
                            sender_id=chat_id,
                            office_id=str(office_id),
                        )
                        return
                    await use_credit(db, office_id, plan_type, QuotaType.STAGING)

                # 6. Isleniyor mesaji
                style_label = _STAGING_STYLE_LABELS.get(style_id, style_id)
                await self._send_reply(
                    chat_id,
                    _STAGING_PROCESSING_MESSAGE.format(style=style_label),
                )

                # 7. Virtual staging
                from src.listings.staging_service import virtual_stage

                result = await virtual_stage(photo_bytes, style_id)

                # 8. Sonuc fotografini gonder
                staged_bytes = result.staged_images[0]
                duration_sec = round(result.processing_time_ms / 1000, 1)
                caption = _STAGING_SUCCESS_MESSAGE.format(style=style_label, duration=duration_sec)
                await self._adapter.send_photo_bytes(chat_id, staged_bytes, caption=caption)

                # 9. Kota artir (use_credit zaten artirdi ise tekrar artirma)
                if is_allowed:
                    await increment_quota(db, office_id, plan_type, QuotaType.STAGING)

                await db.commit()

            # Redis temizle
            await self._redis.delete(redis_key)

            logger.info(
                "telegram_bot_staging_success",
                sender_id=chat_id,
                office_id=str(office_id),
                style=style_id,
                processing_time_ms=result.processing_time_ms,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="staging_callback",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)


    # ================================================================
    # Private — /ilan Wizard Handler'lar
    # ================================================================

    async def _get_conv_state(self, user_id: str) -> ConversationState | None:
        """Conversation state'i Redis'ten okur. Conv manager yoksa None."""
        if self._conv is None:
            return None
        return await self._conv.get(user_id)

    async def _handle_ilan(self, incoming: IncomingMessage) -> None:
        """
        /ilan komutu handler'i — wizard baslatma.

        Aktif wizard varsa uyari gosterir.
        Redis yoksa hata mesaji gonderir.
        """
        chat_id = incoming.sender_id

        if self._conv is None:
            logger.warning("telegram_bot_ilan_no_redis", sender_id=chat_id)
            await self._send_reply(chat_id, _ILAN_ERROR_MESSAGE)
            return

        try:
            # Aktif wizard kontrolu
            if await self._conv.is_active(chat_id):
                await self._send_reply(chat_id, _ILAN_ALREADY_ACTIVE_MESSAGE)
                logger.info(
                    "telegram_bot_ilan_already_active",
                    sender_id=chat_id,
                )
                return

            # Yeni wizard baslat — PHOTO adimi
            await self._conv.start(chat_id)
            await self._send_reply(chat_id, _ILAN_WELCOME_MESSAGE)

            logger.info(
                "telegram_bot_ilan_started",
                sender_id=chat_id,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="ilan",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)

    async def _handle_iptal(self, incoming: IncomingMessage) -> None:
        """
        /iptal komutu handler'i — aktif wizard'i iptal eder.
        """
        chat_id = incoming.sender_id

        if self._conv is None:
            return

        try:
            if await self._conv.is_active(chat_id):
                await self._conv.clear(chat_id)
                await self._send_reply(chat_id, _ILAN_CANCEL_MESSAGE)
                logger.info(
                    "telegram_bot_ilan_cancelled",
                    sender_id=chat_id,
                )
            else:
                await self._send_reply(chat_id, _ILAN_NO_ACTIVE_MESSAGE)

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="iptal",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )

    async def _handle_wizard_photo(
        self,
        incoming: IncomingMessage,
        conv_state: ConversationState,
    ) -> None:
        """
        PHOTO adimi — fotograf indir, MinIO'ya yukle, oda analizi (opsiyonel).

        Akis:
            1. Telegram API'den fotoyu indir
            2. MinIO'ya upload (photo_service._upload_to_minio)
            3. Oda analizi (staging_service.analyze_room) — hata durumunda atlanir
            4. State'e photo_url, room_analysis kaydet
            5. LOCATION adimina ilerle
        """
        chat_id = incoming.sender_id

        try:
            # 1. Fotoyu indir
            photo_bytes = await self._adapter.download_file(incoming.media_url)

            logger.info(
                "telegram_bot_wizard_photo_downloaded",
                sender_id=chat_id,
                photo_size_bytes=len(photo_bytes),
            )

            # 2. MinIO'ya upload
            photo_url: str | None = None
            try:
                import uuid as _uuid

                from src.listings.photo_service import (
                    _get_public_url,
                    _upload_to_minio,
                )

                object_key = f"wizard/{chat_id}/{_uuid.uuid4().hex}.jpg"
                await _upload_to_minio(photo_bytes, object_key, "image/jpeg")
                photo_url = _get_public_url(object_key)

                logger.info(
                    "telegram_bot_wizard_photo_uploaded",
                    sender_id=chat_id,
                    object_key=object_key,
                )
            except Exception as upload_exc:
                logger.warning(
                    "telegram_bot_wizard_photo_upload_failed",
                    sender_id=chat_id,
                    error=str(upload_exc),
                )
                # Upload hatasi wizard'i durdurmaz

            # 3. Oda analizi (opsiyonel)
            room_analysis: str | None = None
            try:
                from src.listings.staging_service import analyze_room

                analysis = await analyze_room(photo_bytes)
                room_analysis = analysis.room_type
            except Exception as analysis_exc:
                logger.warning(
                    "telegram_bot_wizard_room_analysis_failed",
                    sender_id=chat_id,
                    error=str(analysis_exc),
                )

            # 4. State guncelle — LOCATION adimina ilerle
            new_data: dict[str, str | None] = {
                "photo_url": photo_url,
                "room_analysis": room_analysis,
            }
            await self._conv.advance(chat_id, WizardStep.LOCATION, new_data)

            # 5. Kullaniciya bilgi mesaji gonder
            await self._send_reply(chat_id, _ILAN_PHOTO_RECEIVED_MESSAGE)

            logger.info(
                "telegram_bot_wizard_photo_step_done",
                sender_id=chat_id,
                has_photo_url=photo_url is not None,
                room_analysis=room_analysis,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="wizard_photo",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)
            if self._conv:
                await self._conv.clear(chat_id)

    async def _handle_wizard_location(
        self,
        incoming: IncomingMessage,
        conv_state: ConversationState,
    ) -> None:
        """
        LOCATION adimi — konum veya ilce adi.

        Secenek A: Konum paylasildi (raw_payload'da location var)
                   -> lat/lon al, reverse geocode ile ilce belirle
        Secenek B: Ilce adi yazildi
                   -> Fuzzy match ile 39 Istanbul ilcesinden eslestir
        """
        chat_id = incoming.sender_id

        try:
            content = incoming.content.strip()
            raw = incoming.raw_payload or {}
            msg_payload = raw.get("message", {})
            location = msg_payload.get("location")

            district: str | None = None
            lat: float | None = None
            lon: float | None = None

            if location:
                # Secenek A: Konum pini
                lat = location.get("latitude")
                lon = location.get("longitude")
                if lat is not None and lon is not None:
                    district = _reverse_geocode_district(lat, lon)
            else:
                # Secenek B: Ilce adi yazildi
                district = _fuzzy_match_district(content)

            if district is None:
                await self._send_reply(chat_id, _ILAN_DISTRICT_NOT_FOUND_MESSAGE)
                logger.info(
                    "telegram_bot_wizard_district_not_found",
                    sender_id=chat_id,
                    raw_input=content[:50],
                )
                return

            # Koordinat yoksa ilce merkezinden al
            if lat is None or lon is None:
                lat, lon = _DISTRICT_COORDS.get(
                    district.lower(), (41.0, 29.0)
                )

            # State guncelle — DETAILS adimina ilerle
            district_title = _normalize_district(district)
            new_data = {
                "district": district_title,
                "lat": lat,
                "lon": lon,
            }
            await self._conv.advance(chat_id, WizardStep.DETAILS, new_data)

            # Konum onay + detay istegi
            msg = f"📍 Ilce: {district_title}\n\n" + _ILAN_LOCATION_RECEIVED_MESSAGE
            await self._send_reply(chat_id, msg)

            logger.info(
                "telegram_bot_wizard_location_step_done",
                sender_id=chat_id,
                district=district_title,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="wizard_location",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)
            if self._conv:
                await self._conv.clear(chat_id)

    async def _handle_wizard_details(
        self,
        incoming: IncomingMessage,
        conv_state: ConversationState,
    ) -> None:
        """
        DETAILS adimi — emlak bilgilerini parse et.

        Format: <m2> <oda> <bina_yasi> <kat>
        Ornek: 120 3+1 5 3

        3 deneme hakki — asildiysa wizard iptal.
        """
        chat_id = incoming.sender_id

        try:
            content = incoming.content.strip()
            parts = content.split()

            # Validation helper — retry mantigi
            valid = True

            if len(parts) != 4:
                valid = False

            area_sqm = 0
            rooms = ""
            building_age = 0
            floor = 0

            if valid:
                try:
                    area_sqm = int(parts[0])
                    rooms = parts[1]
                    building_age = int(parts[2])
                    floor = int(parts[3])
                except ValueError:
                    valid = False

            if valid and not (10 <= area_sqm <= 1000):
                valid = False
            if valid and "+" not in rooms:
                valid = False
            if valid and not (0 <= building_age <= 100):
                valid = False
            if valid and not (0 <= floor <= 50):
                valid = False

            if not valid:
                retries = await self._conv.increment_retries(chat_id)
                if retries >= _ILAN_MAX_RETRIES:
                    await self._send_reply(
                        chat_id, _ILAN_DETAILS_MAX_RETRIES_MESSAGE
                    )
                    await self._conv.clear(chat_id)
                    return
                await self._send_reply(chat_id, _ILAN_DETAILS_ERROR_MESSAGE)
                return

            # State guncelle
            district = conv_state.data.get("district", "Bilinmiyor")
            new_data = {
                "area_sqm": area_sqm,
                "rooms": rooms,
                "building_age": building_age,
                "floor": floor,
            }
            await self._conv.advance(chat_id, WizardStep.CONFIRM, new_data)

            # Ozet goster + onay iste
            summary = (
                f"📋 Ilan Ozeti:\n"
                f"📍 {district}\n"
                f"📐 {area_sqm} m² | {rooms} | "
                f"{building_age} yasinda | {floor}. kat\n\n"
                f"Ilan metni olusturulsun mu?"
            )

            buttons = [
                Button(text="✅ Evet", callback_data="ilan:confirm"),
                Button(text="❌ Iptal", callback_data="ilan:cancel"),
            ]
            msg_content = MessageContent(text=summary, buttons=buttons)
            await self._adapter.send(recipient=chat_id, content=msg_content)

            logger.info(
                "telegram_bot_wizard_details_step_done",
                sender_id=chat_id,
                area_sqm=area_sqm,
                rooms=rooms,
                building_age=building_age,
                floor=floor,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="wizard_details",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)
            if self._conv:
                await self._conv.clear(chat_id)

    async def _handle_ilan_callback(self, incoming: IncomingMessage) -> None:
        """
        Ilan wizard callback handler'i.

        callback_data formatlari:
            - ilan:confirm  -> Ilan metni uret
            - ilan:cancel   -> Wizard iptal
            - ilan:regen    -> Yeniden uret
        """
        chat_id = incoming.sender_id

        # Callback query yanitla
        cq_id = incoming.raw_payload.get("callback_query", {}).get("id")
        if cq_id:
            await self._adapter.answer_callback_query(cq_id)

        try:
            action = incoming.content.split(":", 1)[1]

            if action == "cancel":
                if self._conv:
                    await self._conv.clear(chat_id)
                await self._send_reply(chat_id, _ILAN_CANCEL_MESSAGE)
                logger.info(
                    "telegram_bot_ilan_callback_cancel",
                    sender_id=chat_id,
                )
                return

            if action in ("confirm", "regen"):
                await self._handle_wizard_generate(incoming)
                return

            logger.warning(
                "telegram_bot_ilan_unknown_callback",
                sender_id=chat_id,
                action=action,
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="ilan_callback",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)

    # ================================================================
    # Eslesme Callback Handler
    # ================================================================

    async def _handle_match_callback(self, incoming: IncomingMessage) -> None:
        """
        Eslesme bildirimi callback handler'i.

        callback_data formatlari:
            - match:{match_id}:accept  -> Eslesme kabul (interested)
            - match:{match_id}:skip    -> Eslesme atla (passed)

        Akis:
            1. Callback query'yi yanitla (loading indicator kaldir)
            2. match_id + action parse et
            3. DB'den match sorgula (PropertyCustomerMatch)
            4. Zaten islenmis mi kontrol et (idempotent)
            5. Status guncelle + responded_at kaydet
            6. Accept → musteri iletisim bilgilerini gonder
            7. Skip → mesaji duzenle, keyboard kaldir, "Atlandi" notu ekle
        """
        chat_id = incoming.sender_id

        # 1. Callback query yanitla
        cq_id = incoming.raw_payload.get("callback_query", {}).get("id")
        message_id = (
            incoming.raw_payload.get("callback_query", {})
            .get("message", {})
            .get("message_id")
        )

        try:
            # 2. Parse: match:{uuid}:{accept|skip}
            parts = incoming.content.split(":")
            if len(parts) != 3:
                if cq_id:
                    await self._adapter.answer_callback_query(
                        cq_id, text="Gecersiz islem"
                    )
                return

            match_id_str, action = parts[1], parts[2]
            if action not in ("accept", "skip"):
                if cq_id:
                    await self._adapter.answer_callback_query(
                        cq_id, text="Gecersiz islem"
                    )
                return

            try:
                match_uuid = uuid.UUID(match_id_str)
            except ValueError:
                if cq_id:
                    await self._adapter.answer_callback_query(
                        cq_id, text="Gecersiz eslesme"
                    )
                return

            # 3. DB'den match sorgula
            from src.models.match import PropertyCustomerMatch

            async with self._session_factory() as db:
                result = await db.execute(
                    select(PropertyCustomerMatch).where(
                        PropertyCustomerMatch.id == match_uuid
                    )
                )
                match_obj = result.scalar_one_or_none()

                if match_obj is None:
                    if cq_id:
                        await self._adapter.answer_callback_query(
                            cq_id, text="Eslesme bulunamadi"
                        )
                    return

                # 4. Zaten islenmis mi? (idempotent)
                if match_obj.status != "pending":
                    status_label = (
                        "Zaten kabul edildi ✅"
                        if match_obj.status == "interested"
                        else "Zaten islendi"
                    )
                    if cq_id:
                        await self._adapter.answer_callback_query(
                            cq_id, text=status_label
                        )
                    return

                # 5. Status guncelle
                from datetime import UTC, datetime

                new_status = "interested" if action == "accept" else "passed"
                match_obj.status = new_status
                match_obj.responded_at = datetime.now(UTC)
                await db.commit()

                # relationship'ler uzerinden customer verisini oku
                # (selectin lazy load — commit sonrasi refresh gerekebilir)
                await db.refresh(match_obj, ["customer", "property"])

                if action == "accept":
                    # 6a. Accept → onay mesaji + musteri iletisim bilgileri
                    if cq_id:
                        await self._adapter.answer_callback_query(
                            cq_id, text="Kabul edildi ✅"
                        )

                    customer = match_obj.customer
                    contact_lines = [
                        "✅ Eslesme kabul edildi! Musteri iletisim bilgileri:",
                        "",
                        f"👤 {customer.full_name}",
                    ]
                    if customer.phone:
                        contact_lines.append(f"📞 {customer.phone}")
                    if customer.email:
                        contact_lines.append(f"📧 {customer.email}")
                    if customer.notes:
                        contact_lines.append(f"📝 Not: {customer.notes}")

                    await self._send_reply(chat_id, "\n".join(contact_lines))

                    # Orijinal mesajdaki keyboard'u kaldir, onay notu ekle
                    await self._edit_match_message(
                        chat_id,
                        message_id,
                        incoming,
                        suffix="\n\n✅ Kabul edildi",
                    )

                else:
                    # 6b. Skip → keyboard kaldir, "Atlandi" notu ekle
                    if cq_id:
                        await self._adapter.answer_callback_query(
                            cq_id, text="Atlandi"
                        )

                    await self._edit_match_message(
                        chat_id,
                        message_id,
                        incoming,
                        suffix="\n\n⏭ Atlandi",
                    )

                logger.info(
                    "telegram_bot_match_callback_handled",
                    sender_id=chat_id,
                    match_id=match_id_str,
                    action=action,
                    new_status=new_status,
                )

        except Exception as exc:
            logger.error(
                "telegram_bot_match_callback_error",
                sender_id=chat_id,
                error=str(exc),
                exc_info=True,
            )
            if cq_id:
                await self._adapter.answer_callback_query(
                    cq_id, text="Bir hata olustu"
                )

    async def _edit_match_message(
        self,
        chat_id: str,
        message_id: int | None,
        incoming: IncomingMessage,
        *,
        suffix: str,
    ) -> None:
        """
        Eslesme bildirim mesajini duzenler — keyboard kaldirir, suffix ekler.

        Bot API edit_message_text cagrisini dogrudan kullanir.
        Hata durumunda sessizce loglar (webhook 200 donmeli).

        Args:
            chat_id: Telegram chat ID.
            message_id: Duzenlenecek mesaj ID (None ise atla).
            incoming: Orijinal IncomingMessage (mesaj metnini almak icin).
            suffix: Mesaj sonuna eklenecek durum notu.
        """
        if message_id is None:
            return

        try:
            original_text = (
                incoming.raw_payload.get("callback_query", {})
                .get("message", {})
                .get("text", "")
            )
            new_text = f"{original_text}{suffix}" if original_text else suffix.strip()

            # aiogram Bot instance uzerinden dogrudan edit
            await self._adapter._bot.edit_message_text(
                chat_id=int(chat_id),
                message_id=message_id,
                text=new_text,
            )
        except Exception as exc:
            logger.warning(
                "telegram_bot_match_edit_message_failed",
                chat_id=chat_id,
                message_id=message_id,
                error=str(exc),
            )

    async def _handle_wizard_generate(self, incoming: IncomingMessage) -> None:
        """
        CONFIRM adimi — ilan metni uretimi.

        Akis:
            1. Linked account kontrolu
            2. Kota kontrolu (QuotaType.LISTING)
            3. listing_assistant_service.generate_listing_text() cagir
            4. Sonucu goster + inline keyboard
            5. State: CONFIRM -> DONE
        """
        chat_id = incoming.sender_id

        if self._conv is None:
            await self._send_reply(chat_id, _ILAN_ERROR_MESSAGE)
            return

        try:
            conv_state = await self._conv.get(chat_id)
            if conv_state is None or conv_state.step not in (
                WizardStep.CONFIRM,
                WizardStep.DONE,
            ):
                await self._send_reply(chat_id, _ILAN_NO_ACTIVE_MESSAGE)
                return

            data = conv_state.data

            # 1. Linked account kontrolu
            user = await self._auth_bridge.get_user_by_chat_id(chat_id)
            if user is None:
                await self._send_reply(chat_id, _ILAN_NOT_LINKED_MESSAGE)
                logger.info(
                    "telegram_bot_ilan_not_linked",
                    sender_id=chat_id,
                )
                return

            # Isleniyor mesaji
            await self._send_reply(chat_id, _ILAN_PROCESSING_MESSAGE)

            # 2. Kota kontrolu
            office_id = user.office_id
            async with self._session_factory() as db:
                from src.models.subscription import Subscription
                from src.modules.valuations.quota_service import (
                    QuotaType,
                    check_credit,
                    check_quota,
                    increment_quota,
                    use_credit,
                )

                sub_result = await db.execute(
                    select(Subscription)
                    .where(
                        Subscription.office_id == office_id,
                        Subscription.status.in_(["trial", "active"]),
                    )
                    .order_by(Subscription.created_at.desc())
                    .limit(1)
                )
                subscription = sub_result.scalar_one_or_none()
                plan_type = (
                    subscription.plan_type if subscription else "starter"
                )

                is_allowed, _used, _limit = await check_quota(
                    db, office_id, plan_type, QuotaType.LISTING
                )

                if not is_allowed:
                    has_credit = await check_credit(
                        db, office_id, plan_type, QuotaType.LISTING
                    )
                    if not has_credit:
                        await self._send_reply(chat_id, _ILAN_QUOTA_MESSAGE)
                        logger.info(
                            "telegram_bot_ilan_quota_exceeded",
                            sender_id=chat_id,
                            office_id=str(office_id),
                        )
                        return
                    await use_credit(
                        db, office_id, plan_type, QuotaType.LISTING
                    )

                # 3. Ilan metni uret
                try:
                    from src.listings.listing_assistant_schemas import (
                        ListingTextRequest,
                    )
                    from src.listings.listing_assistant_service import (
                        generate_listing_text,
                    )

                    # Oda parse
                    room_count, living_room_count = _parse_room_format(
                        data.get("rooms", "2+1")
                    )
                    room_str = f"{room_count}+{living_room_count}"

                    request = ListingTextRequest(
                        property_type="daire",
                        district=data.get("district", "Istanbul"),
                        neighborhood="Merkez",
                        net_sqm=data.get("area_sqm", 100),
                        room_count=room_str,
                        price=0,  # Fiyat bilgisi yok — placeholder
                        floor=data.get("floor"),
                        building_age=data.get("building_age"),
                        tone="samimi",
                    )

                    result = await generate_listing_text(request)

                except Exception as gen_exc:
                    logger.error(
                        "telegram_bot_ilan_generate_error",
                        sender_id=chat_id,
                        error=str(gen_exc),
                        exc_info=True,
                    )
                    await self._send_reply(chat_id, _ILAN_ERROR_MESSAGE)
                    return

                # 4. Kota artir
                if is_allowed:
                    await increment_quota(
                        db, office_id, plan_type, QuotaType.LISTING
                    )
                await db.commit()

            # 5. Sonuc mesaji
            title = result.get("title", "Ilan")
            description = result.get("description", "")
            highlights = result.get("highlights", [])

            highlights_text = ""
            if highlights:
                highlights_text = "\n".join(f"• {h}" for h in highlights)
                highlights_text = (
                    f"\n\n✨ One Cikan Ozellikler:\n{highlights_text}"
                )

            response_text = (
                f"✨ Ilan Metniniz Hazir!\n\n"
                f"📌 {title}\n\n"
                f"{description}"
                f"{highlights_text}"
            )

            # Telegram mesaj limiti kontrolu (4096 char)
            if len(response_text) > 4000:
                response_text = response_text[:3997] + "..."

            buttons = [
                Button(
                    text="🔄 Yeniden Uret", callback_data="ilan:regen"
                ),
                Button(text="🗑️ Iptal", callback_data="ilan:cancel"),
            ]
            msg_content = MessageContent(
                text=response_text, buttons=buttons
            )
            await self._adapter.send(
                recipient=chat_id, content=msg_content
            )

            # 6. State -> DONE
            await self._conv.advance(chat_id, WizardStep.DONE)

            logger.info(
                "telegram_bot_ilan_generated",
                sender_id=chat_id,
                office_id=str(office_id),
                district=data.get("district"),
                token_usage=result.get("token_usage", 0),
            )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="wizard_generate",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_error(chat_id, "general", request_id)


    # ================================================================
    # Private — Yardimci Metotlar
    # ================================================================

    async def _handle_deep_link(self, chat_id: str, token: str) -> None:
        """
        Deep link token'i ile hesap baglama islemini yurutur.

        Args:
            chat_id: Telegram chat ID (sender_id olarak gelir).
            token: Deep link token (Redis'te saklanan tek kullanimlik kod).
        """
        try:
            success = await self._auth_bridge.verify_and_link(
                token=token,
                chat_id=chat_id,
            )

            if success:
                await self._send_reply(chat_id, _LINK_SUCCESS_MESSAGE)
                logger.info(
                    "telegram_bot_deep_link_success",
                    chat_id=chat_id,
                )
            else:
                await self._send_reply(chat_id, _LINK_INVALID_MESSAGE)
                logger.warning(
                    "telegram_bot_deep_link_invalid",
                    chat_id=chat_id,
                )

        except Exception as exc:
            request_id = uuid.uuid4().hex[:8]
            logger.error(
                "telegram_handler_error",
                handler="deep_link",
                request_id=request_id,
                user_id=chat_id,
                chat_id=chat_id,
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                exc_info=True,
            )
            await self._send_reply(chat_id, _LINK_INVALID_MESSAGE)

    async def _send_reply(self, chat_id: str, text: str) -> None:
        """
        TelegramAdapter uzerinden mesaj gonderir.

        Gonderim hatasi durumunda exception firlatmaz, loglar.

        Args:
            chat_id: Telegram chat ID.
            text: Gonderilecek mesaj metni.
        """
        content = MessageContent(text=text)
        result = await self._adapter.send(recipient=chat_id, content=content)

        if not result.success:
            logger.error(
                "telegram_bot_reply_failed",
                chat_id=chat_id,
                error=result.error,
            )

    async def _send_error(
        self,
        chat_id: str,
        error_type: str,
        request_id: str,
    ) -> None:
        """
        Standart hata mesaji gonder.

        _ERROR_MESSAGES dict'inden hata tipine gore mesaj secer,
        request_id ile formatlar ve kullaniciya gonderir.

        Args:
            chat_id: Telegram chat ID.
            error_type: Hata tipi (general, quota, not_found, vb.).
            request_id: Kullaniciya gosterilecek takip kodu.
        """
        msg = _ERROR_MESSAGES.get(error_type, _ERROR_MESSAGES["general"])
        await self._send_reply(chat_id, msg.format(request_id=request_id))


# ================================================================
# Module-level Yardimci Fonksiyonlar
# ================================================================

# Turk karakter → ASCII donusum tablosu
_TR_CHAR_MAP = str.maketrans(
    "çğıöşüÇĞİÖŞÜ",
    "cgiosuCGIOSU",
)


def _normalize_district(name: str) -> str:
    """
    Ilce adini model formatina donustur.

    Turk karakterleri ASCII'ye cevirir ve baslik (title) formatina getirir.
    Ornek: "Kadıköy" → "Kadikoy", "BEYOĞLU" → "Beyoglu"
    """
    return name.translate(_TR_CHAR_MAP).strip().title()


def _parse_room_format(room_str: str) -> tuple[int, int]:
    """
    Oda formatini parse et.

    Ornek: "3+1" → (3, 1), "2+0" → (2, 0), "4" → (4, 1)
    """
    if "+" in room_str:
        parts = room_str.split("+", maxsplit=1)
        return int(parts[0]), int(parts[1])
    return int(room_str), 1


def _format_price(price: float | int) -> str:
    """
    Fiyati Turk formatinda goster.

    Ornek: 4500000 → "4.500.000"
    """
    return f"{int(price):,}".replace(",", ".")


# ================================================================
# /kredi Yardimci Fonksiyonlar
# ================================================================


class InvalidParamError(Exception):
    """Gecersiz parametre hatasi — /kredi parse islemi icin."""


def _parse_amount(raw: str) -> float:
    """
    Tutar string'ini float'a donusturur.

    Desteklenen formatlar:
        - 2500000   → 2_500_000.0
        - 2.5m      → 2_500_000.0
        - 2,5m      → 2_500_000.0
        - 500k      → 500_000.0

    Args:
        raw: Kullanicidan gelen tutar string'i.

    Returns:
        Tutar (float).

    Raises:
        InvalidParamError: Gecersiz format.
    """
    text = raw.strip().lower()

    multiplier = 1.0
    if text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]

    # Virgulu noktaya cevir (Turkce format destegi: 2,5m)
    text = text.replace(",", ".")

    try:
        return float(text) * multiplier
    except ValueError as exc:
        raise InvalidParamError(f"Gecersiz tutar: {raw}") from exc


def _parse_term(raw: str) -> int:
    """
    Vade string'ini ay cinsinden int'e donusturur.

    Desteklenen formatlar:
        - 180   → 180 (ay)
        - 15y   → 180 (yil → ay)

    Args:
        raw: Kullanicidan gelen vade string'i.

    Returns:
        Vade (ay, int).

    Raises:
        InvalidParamError: Gecersiz format.
    """
    text = raw.strip().lower()

    if text.endswith("y"):
        text = text[:-1]
        try:
            return int(float(text) * 12)
        except ValueError as exc:
            raise InvalidParamError(f"Gecersiz vade: {raw}") from exc

    try:
        return int(text)
    except ValueError as exc:
        raise InvalidParamError(f"Gecersiz vade: {raw}") from exc


# ================================================================
# /ilan Wizard Yardimci Fonksiyonlar
# ================================================================


def _fuzzy_match_district(text: str) -> str | None:
    """
    Kullanici girdisini 39 Istanbul ilcesiyle eslestir.

    Once exact match (normalize edilmis), sonra Levenshtein benzeri
    basit mesafe kontrolu ile fuzzy match dener.

    Args:
        text: Kullanicinin yazdigi ilce adi.

    Returns:
        Eslesen ilce key'i (lowercase ASCII) veya None.
    """
    if not text:
        return None

    # Normalize et
    normalized = text.translate(_TR_CHAR_MAP).strip().lower()

    # 1. Exact match
    if normalized in _DISTRICT_COORDS:
        return normalized

    # 2. Prefix match (en az 3 karakter)
    if len(normalized) >= 3:
        for district_key in _DISTRICT_COORDS:
            if district_key.startswith(normalized):
                return district_key

    # 3. Contains match
    if len(normalized) >= 4:
        for district_key in _DISTRICT_COORDS:
            if normalized in district_key or district_key in normalized:
                return district_key

    # 4. Basit edit distance (1 karakter tolerans)
    best_match: str | None = None
    best_dist = 999
    for district_key in _DISTRICT_COORDS:
        dist = _simple_edit_distance(normalized, district_key)
        if dist < best_dist:
            best_dist = dist
            best_match = district_key

    if best_dist <= _ILAN_DISTRICT_MAX_DISTANCE:
        return best_match

    return None


def _simple_edit_distance(s1: str, s2: str) -> int:
    """
    Basit karakter farki mesafesi.

    Tam Levenshtein yerine hizli bir yaklasim:
    boyut farki + eslesmyen karakter sayisi.
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    len_diff = len(s2) - len(s1)
    mismatches = sum(1 for a, b in zip(s1, s2, strict=False) if a != b)

    return len_diff + mismatches


def _reverse_geocode_district(lat: float, lon: float) -> str | None:
    """
    Koordinattan en yakin Istanbul ilcesini bul.

    Basit Euclidean mesafe ile en yakin ilce merkezini dondurur.
    Haversine yerine yaklasik mesafe yeterli (ayni sehir ici).

    Args:
        lat: Enlem.
        lon: Boylam.

    Returns:
        En yakin ilce key'i veya None (Istanbul disiysa).
    """
    # Istanbul bounding box kontrolu (yaklasik)
    if not (40.5 <= lat <= 41.7 and 27.5 <= lon <= 30.0):
        return None

    best_key: str | None = None
    best_dist = float("inf")

    for district_key, (d_lat, d_lon) in _DISTRICT_COORDS.items():
        dist = (lat - d_lat) ** 2 + (lon - d_lon) ** 2
        if dist < best_dist:
            best_dist = dist
            best_key = district_key

    return best_key
