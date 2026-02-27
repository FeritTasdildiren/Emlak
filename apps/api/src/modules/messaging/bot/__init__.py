"""
Emlak Teknoloji Platformu - Telegram Bot Module

Telegram bot komut isleme ve hesap baglama (deep link auth bridge) katmani.

Export'lar:
    - TelegramBotHandler: Webhook mesajlarini komutlara yonlendiren handler
    - TelegramAuthBridge: Deep link token yonetimi + hesap baglama
    - router: FastAPI APIRouter (POST/DELETE/GET /telegram/link)
    - LinkResponse, LinkStatusResponse: Pydantic yanit modelleri

Referans: TASK-039
"""

from src.modules.messaging.bot.auth_bridge import TelegramAuthBridge
from src.modules.messaging.bot.handlers import TelegramBotHandler
from src.modules.messaging.bot.router import router as telegram_link_router
from src.modules.messaging.bot.schemas import LinkResponse, LinkStatusResponse

__all__ = [
    "LinkResponse",
    "LinkStatusResponse",
    "TelegramAuthBridge",
    "TelegramBotHandler",
    "telegram_link_router",
]
