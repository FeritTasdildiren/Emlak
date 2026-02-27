"""
Emlak Teknoloji Platformu - Messaging Channel Adapters

Kanal adaptorlerinin bulundugu paket.

Her adaptor MessageChannel Protocol'unu (gateway.py) tam olarak uygular
ve ChannelRegistry'ye kaydedilerek kullanilir.

Mevcut adaptorler:
    - TelegramAdapter: Telegram Bot API (aiogram 3.x) — TAM
    - WhatsAppAdapter: WhatsApp Cloud API (STUB — S12'de tam implementasyon)
"""

from src.modules.messaging.adapters.telegram import TelegramAdapter
from src.modules.messaging.adapters.whatsapp import WhatsAppAdapter

__all__ = ["TelegramAdapter", "WhatsAppAdapter"]
