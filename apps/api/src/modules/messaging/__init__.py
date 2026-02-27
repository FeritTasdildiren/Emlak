"""
Emlak Teknoloji Platformu - Messaging Module

Coklu kanal mesajlasma altyapisi (Telegram, WhatsApp, vb.).

Mimari:
    - MessageChannel Protocol: kanal adaptorlerinin uyguladigi arayuz
    - ChannelRegistry: kanal adaptor kayit ve erisimi
    - MessagingService: is mantigi — mesaj gonderme, kanal yonlendirme
    - MessageTemplateEngine: Jinja2 tabanli sablon motoru
    - Plan bazli kanal secimi: Elite > Pro > Starter

Kullanim:
    from src.modules.messaging.gateway import MessageChannel
    from src.modules.messaging.schemas import MessageContent, DeliveryResult
    from src.modules.messaging.registry import ChannelRegistry
    from src.modules.messaging.service import MessagingService
    from src.modules.messaging.templates import MessageTemplateEngine
"""
