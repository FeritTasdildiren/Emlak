"""
Emlak Teknoloji Platformu - Portal Export Service

Ilan metni uretim ciktisini emlak portali formatina donusturur.

Desteklenen portallar:
    - sahibinden.com: baslik maks 50, aciklama maks 2000, emoji YASAK, duz metin
    - hepsiemlak.com: baslik maks 70, aciklama maks 4000, satir sonu \\n, ozellikler checkbox

Referans: TASK-120 (S8.8 + S8.16)
"""

from __future__ import annotations

import re

import structlog

logger = structlog.get_logger(__name__)


# ================================================================
# Portal Format Tanimlari
# ================================================================

PORTAL_FORMATS: dict[str, dict] = {
    "sahibinden": {
        "id": "sahibinden",
        "name": "sahibinden.com",
        "max_title_length": 50,
        "max_description_length": 2000,
        "emoji_allowed": False,
        "required_fields": ["title", "description"],
        "notes": (
            "Baslik maksimum 50 karakter. Aciklama maksimum 2000 karakter. "
            "Emoji kullanilamaz. Duz metin, HTML desteklenmez."
        ),
        "description_separator": "\n",
        "highlights_format": "inline",  # one cikan ozellikler aciklama sonuna eklenir
    },
    "hepsiemlak": {
        "id": "hepsiemlak",
        "name": "hepsiemlak.com",
        "max_title_length": 70,
        "max_description_length": 4000,
        "emoji_allowed": True,
        "required_fields": ["title", "description"],
        "notes": (
            "Baslik maksimum 70 karakter. Aciklama maksimum 4000 karakter. "
            "Satir sonu \\n ile ayrilir. Ozellikler checkbox olarak gosterilir."
        ),
        "description_separator": "\n\n",
        "highlights_format": "checkbox",  # one cikan ozellikler checkbox listesi olarak eklenir
    },
}


# ================================================================
# Emoji Regex (Unicode emoji bloklari)
# ================================================================

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
    "\U00002600-\U000026FF"  # Misc symbols
    "\U0000FE00-\U0000FE0F"  # Variation Selectors
    "\U0000200D"             # Zero Width Joiner
    "]+",
    flags=re.UNICODE,
)


# ================================================================
# Yardimci Fonksiyonlar
# ================================================================


def smart_truncate(text: str, max_len: int) -> str:
    """Metni kelime sinirinda kirpar ve '...' ekler.

    Turkce karakterler (I, S, G, U, O, C) korunur.
    Eger metin zaten sinirin altindaysa aynen doner.
    """
    if len(text) <= max_len:
        return text

    # ... icin 3 karakter ayir
    truncated = text[: max_len - 3]

    # Son kelime sinirini bul
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated.rstrip() + "..."


def _strip_emojis(text: str) -> str:
    """Metindeki tum emoji karakterlerini kaldirir."""
    cleaned = _EMOJI_PATTERN.sub("", text)
    # Birden fazla boslugu teke indir
    cleaned = re.sub(r"  +", " ", cleaned)
    return cleaned.strip()


def _format_highlights_inline(highlights: list[str], separator: str) -> str:
    """One cikan ozellikleri duz metin olarak formatlar."""
    if not highlights:
        return ""
    items = [f"- {h}" for h in highlights]
    return separator + "One Cikan Ozellikler:" + separator + separator.join(items)


def _format_highlights_checkbox(highlights: list[str], separator: str) -> str:
    """One cikan ozellikleri checkbox formatinda formatlar."""
    if not highlights:
        return ""
    items = [f"✓ {h}" for h in highlights]
    return separator + "One Cikan Ozellikler:" + separator + separator.join(items)


# ================================================================
# Ana Fonksiyonlar
# ================================================================


def validate_portal_format(result: dict) -> list[str]:
    """Portal export sonucunu dogrular, uyari listesi dondurur.

    Args:
        result: format_for_portal() ciktisi

    Returns:
        Uyari mesajlari listesi (bos ise sorun yok)
    """
    warnings: list[str] = []
    portal_id = result.get("portal", "")
    fmt = PORTAL_FORMATS.get(portal_id)

    if not fmt:
        warnings.append(f"Bilinmeyen portal: {portal_id}")
        return warnings

    title = result.get("formatted_title", "")
    desc = result.get("formatted_description", "")

    if len(title) > fmt["max_title_length"]:
        warnings.append(
            f"Baslik {len(title)} karakter — {fmt['name']} limiti {fmt['max_title_length']}"
        )

    if len(desc) > fmt["max_description_length"]:
        warnings.append(
            f"Aciklama {len(desc)} karakter — {fmt['name']} limiti {fmt['max_description_length']}"
        )

    if not fmt["emoji_allowed"] and _EMOJI_PATTERN.search(title + desc):
        warnings.append(f"{fmt['name']} emoji kabul etmiyor — emoji tespit edildi")

    return warnings


def format_for_portal(
    text_result: dict,
    portal: str,
) -> dict:
    """Ilan metni uretim ciktisini belirtilen portal formatina cevirir.

    Args:
        text_result: generate-text ciktisi (title, description, highlights)
        portal: Hedef portal ID ('sahibinden' veya 'hepsiemlak')

    Returns:
        Portal formatina uygun dict:
            portal, formatted_title, formatted_description,
            character_counts, warnings
    """
    fmt = PORTAL_FORMATS.get(portal)
    if not fmt:
        raise ValueError(f"Desteklenmeyen portal: {portal}")

    title = text_result.get("title", "")
    description = text_result.get("description", "")
    highlights = text_result.get("highlights", [])

    warnings: list[str] = []
    separator = fmt["description_separator"]

    # --- Emoji temizligi ---
    if not fmt["emoji_allowed"]:
        original_title = title
        original_desc = description

        title = _strip_emojis(title)
        description = _strip_emojis(description)

        if title != original_title or description != original_desc:
            warnings.append("Emoji karakterleri kaldirildi")

    # --- Highlights ekleme ---
    if highlights:
        if fmt["highlights_format"] == "checkbox":
            highlights_text = _format_highlights_checkbox(highlights, separator)
        else:
            highlights_text = _format_highlights_inline(highlights, separator)
        description = description + highlights_text

    # --- Baslik kirpma ---
    if len(title) > fmt["max_title_length"]:
        title = smart_truncate(title, fmt["max_title_length"])
        warnings.append(f"Baslik {fmt['max_title_length']} karaktere kirpildi")

    # --- Aciklama kirpma ---
    if len(description) > fmt["max_description_length"]:
        description = smart_truncate(description, fmt["max_description_length"])
        warnings.append(f"Aciklama {fmt['max_description_length']} karaktere kirpildi")

    result = {
        "portal": portal,
        "formatted_title": title,
        "formatted_description": description,
        "character_counts": {
            "title_length": len(title),
            "description_length": len(description),
        },
        "warnings": warnings,
    }

    # Ek dogrulama
    extra_warnings = validate_portal_format(result)
    if extra_warnings:
        result["warnings"].extend(extra_warnings)

    logger.info(
        "portal_export_formatted",
        portal=portal,
        title_len=len(title),
        desc_len=len(description),
        warnings_count=len(result["warnings"]),
    )

    return result


def export_to_multiple(
    text_result: dict,
    portals: list[str],
) -> list[dict]:
    """Ilan metni ciktisini birden fazla portal formatina cevirir.

    Args:
        text_result: generate-text ciktisi
        portals: Hedef portal ID listesi

    Returns:
        Portal formatina uygun dict listesi
    """
    results: list[dict] = []
    for portal in portals:
        result = format_for_portal(text_result, portal)
        results.append(result)
    return results


def get_portal_info() -> list[dict]:
    """Tum desteklenen portallarin bilgilerini dondurur.

    Returns:
        Portal bilgi dict listesi (id, name, max_title_length, vb.)
    """
    info_list: list[dict] = []
    for _portal_id, fmt in PORTAL_FORMATS.items():
        info_list.append(
            {
                "id": fmt["id"],
                "name": fmt["name"],
                "max_title_length": fmt["max_title_length"],
                "max_description_length": fmt["max_description_length"],
                "emoji_allowed": fmt["emoji_allowed"],
                "required_fields": fmt["required_fields"],
                "notes": fmt["notes"],
            }
        )
    return info_list
