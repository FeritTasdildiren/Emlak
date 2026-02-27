"""
Emlak Teknoloji Platformu - Message Template Engine

Jinja2 tabanli sablon motoru. Sablon dosyalarini yukler, YAML front matter'i
parse eder ve MessageContent nesnesi uretir.

Sablon dosya formati:
    ---
    buttons:
      - text: 'Buton Metni'
        url: '{{ some_url }}'
    media_url: 'https://...'
    ---
    Merhaba {{ name }},

    Mesaj govdesi burada...

Dosya yapisi:
    templates/content/{locale}/{template_id}.txt

Guvenlik:
    - Jinja2 auto-escape aktif (XSS koruması)
    - Sandbox olmayan sablonlar icin undefined=StrictUndefined
      (eksik degisken kullanimi aninda hata verir)
"""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from src.modules.messaging.schemas import Button, MessageContent

logger = structlog.get_logger(__name__)

# YAML front matter ayirici
_FRONT_MATTER_DELIMITER = "---"


def _parse_template_file(raw: str) -> tuple[dict, str]:
    """
    Sablon dosyasini YAML front matter ve govde olarak ayirir.

    Args:
        raw: Sablon dosyasinin ham icerigi.

    Returns:
        (metadata_dict, body_text) — front matter yoksa bos dict doner.

    Raises:
        ValueError: Front matter YAML parse edilemezse.
    """
    stripped = raw.strip()

    if not stripped.startswith(_FRONT_MATTER_DELIMITER):
        # Front matter yok — tum icerik govde
        return {}, stripped

    # Ilk '---' sonrasinda ikinci '---' yi bul
    after_first = stripped[len(_FRONT_MATTER_DELIMITER) :]
    end_idx = after_first.find(_FRONT_MATTER_DELIMITER)

    if end_idx == -1:
        # Kapatan '---' bulunamadi — tum icerik govde olarak degerlendir
        logger.warning("template_front_matter_unclosed", content_preview=stripped[:80])
        return {}, stripped

    yaml_block = after_first[:end_idx].strip()
    body = after_first[end_idx + len(_FRONT_MATTER_DELIMITER) :].strip()

    if not yaml_block:
        return {}, body

    try:
        metadata = yaml.safe_load(yaml_block)
    except yaml.YAMLError as exc:
        raise ValueError(f"Sablon YAML front matter parse hatasi: {exc}") from exc

    if not isinstance(metadata, dict):
        raise ValueError(
            f"Sablon YAML front matter dict olmali, {type(metadata).__name__} geldi"
        )

    return metadata, body


class MessageTemplateEngine:
    """
    Jinja2 tabanli mesaj sablonu motoru.

    Sorumluluklar:
        - Sablon dosyalarini locale bazli yuklemek
        - YAML front matter parse etmek (buttons, media_url)
        - Jinja2 ile degiskenleri render etmek
        - MessageContent nesnesi dondurmek

    Args:
        templates_dir: Sablon kok dizini. None ise varsayilan konum kullanilir:
                       src/modules/messaging/templates/content/
    """

    def __init__(self, templates_dir: str | None = None) -> None:
        if templates_dir is None:
            # Varsayilan: bu dosyanin bulundugu dizin / content /
            self._base_dir = Path(__file__).resolve().parent / "content"
        else:
            self._base_dir = Path(templates_dir).resolve()

        logger.info("template_engine_initialized", templates_dir=str(self._base_dir))

    def _get_env(self, locale: str) -> Environment:
        """
        Belirtilen locale icin Jinja2 Environment olusturur.

        Her render cagrisi icin taze Environment olusturulur — sablon dosyalari
        runtime'da degisebilir (ornegin hot-reload senaryosu). Jinja2 dosya
        yuklemesi zaten disk-cached oldugu icin performans etkisi minimaldir.

        Args:
            locale: Sablon dili (ornek: "tr", "en").

        Returns:
            Yapilandirilmis Jinja2 Environment.

        Raises:
            FileNotFoundError: Locale dizini bulunamazsa.
        """
        locale_dir = self._base_dir / locale

        if not locale_dir.is_dir():
            raise FileNotFoundError(
                f"Sablon dizini bulunamadi: {locale_dir}. "
                f"Mevcut locale'ler: {self._list_locales()}"
            )

        return Environment(
            loader=FileSystemLoader(str(locale_dir)),
            autoescape=select_autoescape(default_for_string=True, default=True),
            undefined=StrictUndefined,
            keep_trailing_newline=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        template_id: str,
        locale: str = "tr",
        **kwargs: object,
    ) -> MessageContent:
        """
        Sablonu render edip MessageContent nesnesi dondurur.

        Islem akisi:
            1. {locale}/{template_id}.txt dosyasini oku
            2. YAML front matter'i parse et (buttons, media_url)
            3. Front matter icindeki Jinja2 degiskenlerini render et
            4. Govdeyi Jinja2 ile render et
            5. MessageContent nesnesi olustur

        Args:
            template_id: Sablon dosya adi (uzantisiz). Ornek: "welcome"
            locale: Sablon dili. Varsayilan: "tr"
            **kwargs: Sablona aktarilacak degiskenler.

        Returns:
            MessageContent — render edilmis mesaj icerigi.

        Raises:
            FileNotFoundError: Sablon dosyasi bulunamazsa.
            ValueError: YAML front matter parse hatasi.
            jinja2.UndefinedError: Sablonda kullanilan degisken kwargs'da yoksa.
        """
        env = self._get_env(locale)
        filename = f"{template_id}.txt"

        logger.debug(
            "rendering_template",
            template_id=template_id,
            locale=locale,
            variables=list(kwargs.keys()),
        )

        # Ham dosya icerigini oku (Jinja2 render ONCESI — front matter'da da
        # Jinja2 degiskenleri olabilir, ornegin buton URL'leri)
        locale_dir = self._base_dir / locale
        template_path = locale_dir / filename

        if not template_path.is_file():
            available = self._list_templates_for_locale(locale)
            raise FileNotFoundError(
                f"Sablon bulunamadi: '{template_id}' (locale='{locale}'). "
                f"Mevcut sablonlar: {available}"
            )

        raw_content = template_path.read_text(encoding="utf-8")

        # Front matter + govde ayir (render ONCESI ham icerik uzerinde)
        metadata, body_raw = _parse_template_file(raw_content)

        # Govdeyi Jinja2 ile render et
        body_template = env.from_string(body_raw)
        rendered_body = body_template.render(**kwargs)

        # Front matter icindeki Jinja2 degiskenlerini render et
        # (ornegin buton URL'lerinde {{ renewal_url }} gibi)
        buttons: list[Button] | None = None
        if "buttons" in metadata:
            rendered_buttons = []
            for btn_data in metadata["buttons"]:
                btn_text_tpl = env.from_string(str(btn_data.get("text", "")))
                btn_text = btn_text_tpl.render(**kwargs)

                btn_url: str | None = None
                if "url" in btn_data:
                    btn_url_tpl = env.from_string(str(btn_data["url"]))
                    btn_url = btn_url_tpl.render(**kwargs)

                btn_callback: str | None = None
                if "callback_data" in btn_data:
                    btn_cb_tpl = env.from_string(str(btn_data["callback_data"]))
                    btn_callback = btn_cb_tpl.render(**kwargs)

                rendered_buttons.append(
                    Button(text=btn_text, url=btn_url, callback_data=btn_callback)
                )
            buttons = rendered_buttons if rendered_buttons else None

        # media_url render
        media_url: str | None = None
        if "media_url" in metadata:
            media_tpl = env.from_string(str(metadata["media_url"]))
            media_url = media_tpl.render(**kwargs)

        content = MessageContent(
            text=rendered_body,
            media_url=media_url,
            buttons=buttons,
            template_id=template_id,
        )

        logger.info(
            "template_rendered",
            template_id=template_id,
            locale=locale,
            text_length=len(rendered_body),
            has_buttons=buttons is not None,
            has_media=media_url is not None,
        )

        return content

    def list_templates(self) -> list[str]:
        """
        Tum locale'lerdeki mevcut sablon ID'lerini dondurur.

        Returns:
            Benzersiz sablon ID'leri listesi (sirali).
            Ornek: ["new_match", "payment_failed", "payment_success", "welcome"]
        """
        template_ids: set[str] = set()

        if not self._base_dir.is_dir():
            return []

        for locale_dir in self._base_dir.iterdir():
            if not locale_dir.is_dir():
                continue
            for template_file in locale_dir.glob("*.txt"):
                template_ids.add(template_file.stem)

        return sorted(template_ids)

    def _list_locales(self) -> list[str]:
        """Mevcut locale dizinlerini listeler."""
        if not self._base_dir.is_dir():
            return []
        return sorted(d.name for d in self._base_dir.iterdir() if d.is_dir())

    def _list_templates_for_locale(self, locale: str) -> list[str]:
        """Belirtilen locale icin mevcut sablon ID'lerini listeler."""
        locale_dir = self._base_dir / locale
        if not locale_dir.is_dir():
            return []
        return sorted(f.stem for f in locale_dir.glob("*.txt"))
