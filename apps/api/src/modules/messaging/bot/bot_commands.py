"""
Emlak Teknoloji Platformu - Telegram Bot Komut Menusu

BotFather'a kayitli komut listesini tanimlar ve register eder.
Kullanicilar '/' yazdiklklarinda bu komutlar otomatik acilir menude gorunur.

Referans: TASK-140
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

# ================================================================
# Komut Tanimlari (komut, aciklama) tuple'lari
# ================================================================

BOT_COMMANDS: list[tuple[str, str]] = [
    ("start", "Karsilama mesaji"),
    ("help", "Kullanilabilir komutlarin listesi"),
    ("ilan", "Ilan olusturma wizard'i"),
    ("iptal", "Aktif wizard'i iptal et"),
    ("degerleme", "AI konut degerleme"),
    ("musteri", "Hizli musteri kaydi"),
    ("portfoy", "Portfoy listesi (son 5 ilan)"),
    ("rapor", "Son degerleme raporu (PDF)"),
    ("fotograf", "Sanal mobilyalama (virtual staging)"),
    ("kredi", "Konut kredisi hesaplama"),
]


async def register_commands(bot) -> None:
    """
    Bot komut menusunu BotFather'a kaydeder.

    Telegram Bot API set_my_commands cagrisini yapar.
    Hata durumunda exception firlatmaz, loglayip sessizce gecer
    (bot calismaya devam edebilmeli).

    Args:
        bot: aiogram Bot instance'i
    """
    try:
        from aiogram.types import BotCommand

        commands = [
            BotCommand(command=cmd, description=desc)
            for cmd, desc in BOT_COMMANDS
        ]
        await bot.set_my_commands(commands)
        logger.info(
            "telegram_bot_commands_registered",
            command_count=len(commands),
        )
    except Exception:
        logger.warning(
            "telegram_bot_commands_registration_failed",
            exc_info=True,
        )
