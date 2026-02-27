"""
Emlak Teknoloji Platformu - Messaging Template Engine

Jinja2 tabanli mesaj sablonu motoru.

Sablon dosyalari templates/content/{locale}/ altinda YAML front matter + Jinja2 formatinda tutulur.

Kullanim:
    from src.modules.messaging.templates.engine import MessageTemplateEngine

    engine = MessageTemplateEngine()
    content = engine.render("welcome", locale="tr", name="Ahmet", office_name="ABC Emlak")
"""

from src.modules.messaging.templates.engine import MessageTemplateEngine

__all__ = ["MessageTemplateEngine"]
