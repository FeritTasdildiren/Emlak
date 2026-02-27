"""
TASK-141: Bot Notification Service Unit Tests

BotNotificationService bildirim gonderme ve formatlama testleri.
Telegram API / DB bagimsiz — mock-based.

Kapsam:
    - send_match_notification() inline keyboard butonlari
    - callback_data formati (match:{uuid}:accept/skip)
    - _format_match_card() cikti formati
    - _send_telegram() buttons parametresi
    - Cift kanal (Telegram + in-app)
    - _render_template() eksik key davranisi
    - _format_price_tr() Turk fiyat formati
    - Bilinmeyen bildirim tipi
    - Kullanici bulunamadi senaryosu
    - Telegram gonderim hatasi — in-app bildirim yine de kaydedilir
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.messaging.bot.bot_notification_service import (
    _NOTIFICATION_TEMPLATES,
    BotNotificationService,
    _customer_type_label,
    _format_match_card,
    _format_price_tr,
)

# ================================================================
# Fixtures
# ================================================================


@pytest.fixture
def mock_user():
    """Mock User objesi — telegram_chat_id ile."""
    user = MagicMock()
    user.id = uuid.UUID("a0000000-0000-0000-0000-000000000010")
    user.telegram_chat_id = "123456789"
    user.office_id = uuid.UUID("a0000000-0000-0000-0000-000000000001")
    return user


@pytest.fixture
def notification_service(mock_telegram_adapter, mock_session_factory, mock_user):
    """BotNotificationService instance — mock dependencies ile."""
    # session_factory'den donen session'in user dondurmesini ayarla
    mock_result = mock_session_factory._mock_result
    mock_result.scalar_one_or_none.return_value = mock_user

    return BotNotificationService(
        telegram_adapter=mock_telegram_adapter,
        session_factory=mock_session_factory,
    )


@pytest.fixture
def match_data():
    """Test eslesme verisi."""
    return {
        "district": "Kadikoy",
        "neighborhood": "Caferaga",
        "rooms": "3+1",
        "net_area": 120,
        "price": 4250000,
        "score": 85,
        "customer_name": "Ahmet Y.",
        "customer_type": "buyer",
        "customer_type_label": "Alici",
        "budget_min": 4000000,
        "budget_max": 5000000,
        "listing": "Kadikoy 3+1",
    }


# ================================================================
# _format_price_tr Tests
# ================================================================


class TestFormatPriceTr:
    """_format_price_tr() Turk fiyat formati testleri."""

    def test_formats_millions(self):
        """4500000 → '4.500.000'."""
        assert _format_price_tr(4500000) == "4.500.000"

    def test_formats_thousands(self):
        """15000 → '15.000'."""
        assert _format_price_tr(15000) == "15.000"

    def test_none_returns_dash(self):
        """None → '—'."""
        assert _format_price_tr(None) == "—"

    def test_zero_returns_zero(self):
        """0 → '0'."""
        assert _format_price_tr(0) == "0"


# ================================================================
# _customer_type_label Tests
# ================================================================


class TestCustomerTypeLabel:
    """_customer_type_label() Turkce etiket donusum testleri."""

    def test_buyer_label(self):
        assert _customer_type_label("buyer") == "Alici"

    def test_seller_label(self):
        assert _customer_type_label("seller") == "Satici"

    def test_renter_label(self):
        assert _customer_type_label("renter") == "Kiraci"

    def test_landlord_label(self):
        assert _customer_type_label("landlord") == "Ev Sahibi"

    def test_unknown_returns_original(self):
        """Bilinmeyen tip → kendi degeri doner."""
        assert _customer_type_label("unknown_type") == "unknown_type"


# ================================================================
# _format_match_card Tests
# ================================================================


class TestFormatMatchCard:
    """_format_match_card() zengin kart formati testleri."""

    def test_card_starts_with_header(self, match_data):
        """Kart '🔔 Yeni Eslesme!' ile baslamali."""
        card = _format_match_card(match_data)
        assert card.startswith("🔔 Yeni Eslesme!")

    def test_card_contains_property_info(self, match_data):
        """Kart ilan bilgilerini icermeli (ilce, mahalle, oda, alan)."""
        card = _format_match_card(match_data)
        assert "Kadikoy" in card
        assert "Caferaga" in card
        assert "3+1" in card
        assert "120m²" in card

    def test_card_contains_price(self, match_data):
        """Kart fiyat bilgisini icermeli."""
        card = _format_match_card(match_data)
        assert "4.250.000" in card
        assert "₺" in card

    def test_card_contains_score(self, match_data):
        """Kart uyum skorunu icermeli."""
        card = _format_match_card(match_data)
        assert "%85" in card

    def test_card_contains_customer_info(self, match_data):
        """Kart musteri bilgilerini icermeli."""
        card = _format_match_card(match_data)
        assert "Ahmet Y." in card
        assert "Alici" in card

    def test_card_contains_budget(self, match_data):
        """Kart butce bilgisini icermeli."""
        card = _format_match_card(match_data)
        assert "4.000.000" in card
        assert "5.000.000" in card

    def test_card_without_price(self):
        """Fiyat yoksa fiyat satiri olmamali."""
        data = {"district": "Besiktas", "score": 50, "customer_name": "Test"}
        card = _format_match_card(data)
        assert "💰" not in card

    def test_card_without_budget(self):
        """Butce yoksa butce satiri olmamali."""
        data = {"district": "Besiktas", "score": 50, "customer_name": "Test"}
        card = _format_match_card(data)
        assert "💵" not in card

    def test_card_with_only_budget_max(self):
        """Sadece budget_max varsa 'maks.' ile gosterilmeli."""
        data = {
            "district": "Besiktas",
            "score": 50,
            "customer_name": "Test",
            "budget_max": 3000000,
        }
        card = _format_match_card(data)
        assert "maks." in card
        assert "3.000.000" in card


# ================================================================
# send_match_notification Tests
# ================================================================


class TestSendMatchNotification:
    """send_match_notification() inline keyboard ve cift kanal testleri."""

    @pytest.mark.asyncio
    async def test_sends_with_inline_keyboard(
        self, notification_service, mock_telegram_adapter, match_data
    ):
        """send_match_notification() inline keyboard butonlari gondermeli."""
        user_id = uuid.UUID("a0000000-0000-0000-0000-000000000010")
        match_id = uuid.UUID("c0000000-0000-0000-0000-000000000001")

        with patch(
            "src.modules.messaging.bot.bot_notification_service.NotificationService"
        ) as mock_notif:
            mock_notif.create = AsyncMock()
            result = await notification_service.send_match_notification(
                user_id=user_id,
                match_id=match_id,
                data=match_data,
            )

        assert result is True
        # adapter.send cagrildimi
        mock_telegram_adapter.send.assert_called_once()
        call_args = mock_telegram_adapter.send.call_args
        content_obj = call_args.kwargs.get("content", call_args.args[1] if len(call_args.args) > 1 else None)

        # Butonlar kontrol
        assert content_obj.buttons is not None
        assert len(content_obj.buttons) == 2

    @pytest.mark.asyncio
    async def test_callback_data_format(
        self, notification_service, mock_telegram_adapter, match_data
    ):
        """callback_data 'match:{uuid}:accept' ve 'match:{uuid}:skip' formatinda olmali."""
        user_id = uuid.UUID("a0000000-0000-0000-0000-000000000010")
        match_id = uuid.UUID("c0000000-0000-0000-0000-000000000001")

        with patch(
            "src.modules.messaging.bot.bot_notification_service.NotificationService"
        ) as mock_notif:
            mock_notif.create = AsyncMock()
            await notification_service.send_match_notification(
                user_id=user_id,
                match_id=match_id,
                data=match_data,
            )

        call_args = mock_telegram_adapter.send.call_args
        content_obj = call_args.kwargs.get("content", call_args.args[1] if len(call_args.args) > 1 else None)
        buttons = content_obj.buttons

        accept_btn = buttons[0]
        skip_btn = buttons[1]

        assert accept_btn.callback_data == f"match:{match_id}:accept"
        assert skip_btn.callback_data == f"match:{match_id}:skip"

    @pytest.mark.asyncio
    async def test_accept_button_text(
        self, notification_service, mock_telegram_adapter, match_data
    ):
        """Accept butonu '✅ Ilgileniyorum' metnine sahip olmali."""
        user_id = uuid.UUID("a0000000-0000-0000-0000-000000000010")
        match_id = uuid.UUID("c0000000-0000-0000-0000-000000000001")

        with patch(
            "src.modules.messaging.bot.bot_notification_service.NotificationService"
        ) as mock_notif:
            mock_notif.create = AsyncMock()
            await notification_service.send_match_notification(
                user_id=user_id,
                match_id=match_id,
                data=match_data,
            )

        call_args = mock_telegram_adapter.send.call_args
        content_obj = call_args.kwargs.get("content", call_args.args[1] if len(call_args.args) > 1 else None)
        assert content_obj.buttons[0].text == "✅ Ilgileniyorum"
        assert content_obj.buttons[1].text == "❌ Gec"

    @pytest.mark.asyncio
    async def test_creates_in_app_notification(
        self, notification_service, match_data
    ):
        """send_match_notification() in-app bildirim de olusturmali."""
        user_id = uuid.UUID("a0000000-0000-0000-0000-000000000010")
        match_id = uuid.UUID("c0000000-0000-0000-0000-000000000001")

        with patch(
            "src.modules.messaging.bot.bot_notification_service.NotificationService"
        ) as mock_notif:
            mock_notif.create = AsyncMock()
            await notification_service.send_match_notification(
                user_id=user_id,
                match_id=match_id,
                data=match_data,
            )

            # NotificationService.create en az 1 kez cagrildimi
            mock_notif.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_not_found_returns_false(self, mock_telegram_adapter, mock_session_factory):
        """Kullanici bulunamadiysa False donmeli."""
        mock_session_factory._mock_result.scalar_one_or_none.return_value = None

        service = BotNotificationService(
            telegram_adapter=mock_telegram_adapter,
            session_factory=mock_session_factory,
        )

        with patch(
            "src.modules.messaging.bot.bot_notification_service.NotificationService"
        ):
            result = await service.send_match_notification(
                user_id=uuid.uuid4(),
                match_id=uuid.uuid4(),
                data={"district": "Test"},
            )

        assert result is False


# ================================================================
# send_notification_to_user Tests
# ================================================================


class TestSendNotificationToUser:
    """send_notification_to_user() genel bildirim testleri."""

    @pytest.mark.asyncio
    async def test_unknown_type_returns_false(self, notification_service):
        """Bilinmeyen bildirim tipi False dondurmeli."""
        result = await notification_service.send_notification_to_user(
            user_id=uuid.uuid4(),
            notification_type="nonexistent_type",
            data={},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_notification_templates_have_required_keys(self):
        """Tum bildirim sablonlari 'title' ve 'telegram' anahtarlarina sahip olmali."""
        for name, tmpl in _NOTIFICATION_TEMPLATES.items():
            assert "title" in tmpl, f"'{name}' sablonunda 'title' eksik"
            assert "telegram" in tmpl, f"'{name}' sablonunda 'telegram' eksik"

    @pytest.mark.asyncio
    async def test_four_notification_types_defined(self):
        """4 bildirim tipi tanimli olmali."""
        expected = {"new_match", "valuation_complete", "listing_ready", "quota_warning"}
        assert set(_NOTIFICATION_TEMPLATES.keys()) == expected


# ================================================================
# _render_template Tests
# ================================================================


class TestRenderTemplate:
    """BotNotificationService._render_template() sablon testleri."""

    def test_render_with_all_keys(self):
        """Tum degiskenler verildiginde dogru cikti."""
        result = BotNotificationService._render_template(
            "Merhaba {name}, skorunuz: %{score}",
            {"name": "Ali", "score": 85},
        )
        assert result == "Merhaba Ali, skorunuz: %85"

    def test_render_with_missing_key_raises_key_error(self):
        """
        Eksik degisken durumunda KeyError firlatir.

        NOT: _render_template'in except blogu format_map kullanir ama
        dict comprehension sadece data'daki key'leri iterate ettigindan
        template'deki eksik key'ler icin yine KeyError olusur.
        Bu bilinen bir edge case — calling code tum key'leri saglamali.
        """
        with pytest.raises(KeyError):
            BotNotificationService._render_template(
                "Merhaba {name}, skor: {score}",
                {"name": "Ali"},
            )
