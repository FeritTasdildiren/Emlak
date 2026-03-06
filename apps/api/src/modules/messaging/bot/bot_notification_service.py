"""
Emlak Teknoloji Platformu - Bot Notification Service

Telegram Bot uzerinden kullanicilara bildirim gondermek icin servis katmani.
Cift kanal destegi: Telegram mesaj + in-app bildirim (NotificationService).

Bildirim tipleri:
    - new_match        → Yeni musteri-ilan eslesmesi
    - valuation_complete → Degerleme tamamlandi
    - listing_ready    → Ilan metni hazir
    - quota_warning    → Kota uyarisi

Tasarim:
    - user_id → telegram_chat_id cozumleme (users tablosundan)
    - Telegram gonderim hatasi → logla, exception firlatma
    - In-app bildirim her durumda kaydedilir (Telegram basarisiz olsa bile)
    - Tum metodlar static degil — adapter + session_factory DI ile saglanir

Referans: TASK-135
"""

from __future__ import annotations

import structlog
import uuid
from sqlalchemy import select

from src.models.user import User
from src.modules.messaging.schemas import Button, MessageContent
from src.modules.notifications.service import NotificationService


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if TYPE_CHECKING:
    from src.modules.messaging.adapters.telegram import TelegramAdapter

logger = structlog.get_logger(__name__)

# ================================================================
# Bildirim Sablon Tipleri
# ================================================================

_NOTIFICATION_TEMPLATES: dict[str, dict[str, str]] = {
    "new_match": {
        "title": "Yeni Eslesme",
        "telegram": "🎯 Yeni eslesme! {customer_name} ile {listing} %{score} uyumlu.",
    },
    "valuation_complete": {
        "title": "Degerleme Tamamlandi",
        "telegram": "📊 Degerleme tamamlandi: {district} {sqm}m² → {price}₺",
    },
    "listing_ready": {
        "title": "Ilan Metni Hazir",
        "telegram": "✨ Ilan metniniz hazir: {title}",
    },
    "quota_warning": {
        "title": "Kota Uyarisi",
        "telegram": "⚠️ Kota uyarisi: {remaining}/{limit} kullanim kaldi.",
    },
}


# ================================================================
# BotNotificationService
# ================================================================


class BotNotificationService:
    """
    Bot uzerinden bildirim gonderme servisi.

    Cift kanal: Telegram mesaj + in-app bildirim (NotificationService).
    Hata durumunda exception firlatmaz, sadece loglar.

    Args:
        telegram_adapter: Mesaj gondermek icin TelegramAdapter instance'i.
        session_factory: SQLAlchemy async_sessionmaker — DB erisimi icin.
    """

    def __init__(
        self,
        telegram_adapter: TelegramAdapter,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._adapter = telegram_adapter
        self._session_factory = session_factory

    # ================================================================
    # Public — Ana bildirim fonksiyonu
    # ================================================================

    async def send_notification_to_user(
        self,
        user_id: uuid.UUID,
        notification_type: str,
        data: dict,
    ) -> bool:
        """
        Kullaniciya bildirim gonderir (Telegram + in-app).

        Akis:
            1. user_id → User sorgula (telegram_chat_id + office_id icin)
            2. In-app bildirim olustur (NotificationService.create)
            3. telegram_chat_id varsa Telegram mesaji gonder
            4. Hata durumunda logla, exception firlatma

        Args:
            user_id: Hedef kullanici UUID.
            notification_type: Bildirim tipi (new_match, valuation_complete, vb.).
            data: Sablon degiskenleri (orn: {customer_name, listing, score}).

        Returns:
            True: En az bir kanal basarili. False: Hic bir kanal basarili degil.
        """
        template = _NOTIFICATION_TEMPLATES.get(notification_type)
        if template is None:
            logger.warning(
                "bot_notification_unknown_type",
                user_id=str(user_id),
                notification_type=notification_type,
            )
            return False

        try:
            async with self._session_factory() as db:
                # 1. User sorgula
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if user is None:
                    logger.warning(
                        "bot_notification_user_not_found",
                        user_id=str(user_id),
                    )
                    return False

                # 2. In-app bildirim olustur
                telegram_text = self._render_template(template["telegram"], data)

                await NotificationService.create(
                    db=db,
                    user_id=user_id,
                    office_id=user.office_id,
                    type=notification_type,
                    title=template["title"],
                    body=telegram_text,
                    data=data,
                )
                await db.commit()

                # 3. Telegram mesaji gonder (chat_id varsa)
                telegram_sent = False
                if user.telegram_chat_id:
                    telegram_sent = await self._send_telegram(
                        chat_id=user.telegram_chat_id,
                        text=telegram_text,
                    )

                logger.info(
                    "bot_notification_sent",
                    user_id=str(user_id),
                    notification_type=notification_type,
                    telegram_sent=telegram_sent,
                    has_chat_id=user.telegram_chat_id is not None,
                )

                return True

        except Exception as exc:
            logger.error(
                "bot_notification_error",
                user_id=str(user_id),
                notification_type=notification_type,
                error=str(exc),
                exc_info=True,
            )
            return False

    # ================================================================
    # Public — Eslesme Bildirimi (Inline Keyboard)
    # ================================================================

    async def send_match_notification(
        self,
        user_id: uuid.UUID,
        match_id: uuid.UUID,
        data: dict,
    ) -> bool:
        """
        Eslesme bildirimi gonderir — zengin kart + inline keyboard.

        Telegram mesajinda "Ilgileniyorum" ve "Gec" butonlari yer alir.
        In-app bildirim de olusturulur.

        Args:
            user_id: Hedef kullanici UUID.
            match_id: PropertyCustomerMatch UUID (callback_data icin).
            data: Eslesme detaylari dict'i. Beklenen anahtarlar:
                - district, neighborhood, rooms, net_area (ilan bilgileri)
                - price (ilan fiyati)
                - score (uyum skoru 0-100)
                - customer_name (musteri adi)
                - customer_type_label (musteri tipi Turkce)
                - budget_min, budget_max (musteri butcesi, opsiyonel)

        Returns:
            True: En az bir kanal basarili. False: Hic bir kanal basarili degil.
        """
        template = _NOTIFICATION_TEMPLATES.get("new_match")
        if template is None:
            return False

        try:
            async with self._session_factory() as db:
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if user is None:
                    logger.warning(
                        "bot_match_notification_user_not_found",
                        user_id=str(user_id),
                    )
                    return False

                # In-app bildirim
                short_text = self._render_template(template["telegram"], data)
                await NotificationService.create(
                    db=db,
                    user_id=user_id,
                    office_id=user.office_id,
                    type="new_match",
                    title=template["title"],
                    body=short_text,
                    data=data,
                )
                await db.commit()

                # Telegram — zengin kart mesaji + inline keyboard
                telegram_sent = False
                if user.telegram_chat_id:
                    rich_text = _format_match_card(data)
                    match_id_str = str(match_id)
                    buttons = [
                        Button(
                            text="✅ Ilgileniyorum",
                            callback_data=f"match:{match_id_str}:accept",
                        ),
                        Button(
                            text="❌ Gec",
                            callback_data=f"match:{match_id_str}:skip",
                        ),
                    ]
                    telegram_sent = await self._send_telegram(
                        chat_id=user.telegram_chat_id,
                        text=rich_text,
                        buttons=buttons,
                    )

                logger.info(
                    "bot_match_notification_sent",
                    user_id=str(user_id),
                    match_id=str(match_id),
                    telegram_sent=telegram_sent,
                    has_chat_id=user.telegram_chat_id is not None,
                )

                return True

        except Exception as exc:
            logger.error(
                "bot_match_notification_error",
                user_id=str(user_id),
                match_id=str(match_id),
                error=str(exc),
                exc_info=True,
            )
            return False

    # ================================================================
    # Private — Yardimci Metotlar
    # ================================================================

    async def _send_telegram(
        self,
        chat_id: str,
        text: str,
        buttons: list[Button] | None = None,
    ) -> bool:
        """
        Telegram uzerinden mesaj gonderir.

        Hata durumunda exception firlatmaz, False doner.

        Args:
            chat_id: Telegram chat ID.
            text: Gonderilecek mesaj metni.
            buttons: Opsiyonel inline keyboard butonlari.

        Returns:
            True: Basarili, False: Basarisiz.
        """
        try:
            content = MessageContent(text=text, buttons=buttons)
            result = await self._adapter.send(recipient=chat_id, content=content)
            return result.success

        except Exception as exc:
            logger.error(
                "bot_notification_telegram_send_failed",
                chat_id=chat_id,
                error=str(exc),
                exc_info=True,
            )
            return False

    @staticmethod
    def _render_template(template: str, data: dict) -> str:
        """
        Sablon metnindeki degiskenleri data dict'i ile doldurur.

        Eksik degiskenler {key} olarak kalir (hata firlatmaz).

        Args:
            template: Format string sablonu.
            data: Degisken degerleri.

        Returns:
            Doldurulmus metin.
        """
        try:
            return template.format(**data)
        except KeyError:
            # Eksik key varsa format_map kullan (eksik key'ler oldugu gibi kalir)
            return template.format_map(
                {k: data.get(k, f"{{{k}}}") for k in data}
            )


# ================================================================
# Module-level Yardimci Fonksiyonlar
# ================================================================


def _format_price_tr(price: float | int | None) -> str:
    """Fiyati Turk formatinda goster. Ornek: 4500000 → '4.500.000'."""
    if price is None:
        return "—"
    return f"{int(price):,}".replace(",", ".")


def _customer_type_label(customer_type: str) -> str:
    """Musteri tipini Turkce etikete cevir."""
    labels = {
        "buyer": "Alici",
        "seller": "Satici",
        "renter": "Kiraci",
        "landlord": "Ev Sahibi",
    }
    return labels.get(customer_type, customer_type)


def _format_match_card(data: dict) -> str:
    """
    Eslesme verilerinden zengin bildirim karti olusturur.

    Ornek cikti:
        🔔 Yeni Eslesme!

        🏠 Kadikoy, Caferaga — 3+1, 120m²
        💰 4.250.000 ₺
        📊 Uyum Skoru: %85

        👤 Musteri: Ahmet Y. (Alici)
        💵 Butce: 4.000.000 - 5.000.000 ₺
    """
    # Ilan bilgileri
    district = data.get("district", "—")
    neighborhood = data.get("neighborhood", "")
    rooms = data.get("rooms", "")
    net_area = data.get("net_area")

    location_parts = [district]
    if neighborhood:
        location_parts.append(neighborhood)
    location_str = ", ".join(location_parts)

    detail_parts: list[str] = []
    if rooms:
        detail_parts.append(rooms)
    if net_area:
        detail_parts.append(f"{int(net_area)}m²")
    detail_str = ", ".join(detail_parts)

    property_line = (
        f"🏠 {location_str} — {detail_str}" if detail_str else f"🏠 {location_str}"
    )

    price = data.get("price")
    price_line = f"💰 {_format_price_tr(price)} ₺" if price else ""

    score = data.get("score", 0)
    score_line = f"📊 Uyum Skoru: %{int(score)}"

    # Musteri bilgileri
    customer_name = data.get("customer_name", "—")
    customer_type = data.get("customer_type", "")
    ct_label = data.get("customer_type_label") or _customer_type_label(customer_type)
    customer_line = f"👤 Musteri: {customer_name} ({ct_label})"

    budget_min = data.get("budget_min")
    budget_max = data.get("budget_max")
    if budget_min and budget_max:
        budget_line = (
            f"💵 Butce: {_format_price_tr(budget_min)} - "
            f"{_format_price_tr(budget_max)} ₺"
        )
    elif budget_max:
        budget_line = f"💵 Butce: maks. {_format_price_tr(budget_max)} ₺"
    else:
        budget_line = ""

    # Karti birlesir
    lines = ["🔔 Yeni Eslesme!", "", property_line]
    if price_line:
        lines.append(price_line)
    lines.append(score_line)
    lines.extend(["", customer_line])
    if budget_line:
        lines.append(budget_line)

    return "\n".join(lines)
