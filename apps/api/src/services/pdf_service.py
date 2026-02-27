"""
Emlak Teknoloji Platformu - PDF Service

WeasyPrint ile HTML template'lerden PDF uretimi.
Jinja2 template rendering + WeasyPrint PDF donusumu.
"""

from __future__ import annotations

from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader, StrictUndefined

logger = structlog.get_logger()

# Template dizini: src/templates/pdf/
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "pdf"


# ---------- Jinja2 Filters ----------


def _format_currency(value: int | float) -> str:
    """Fiyati Turk Lirasi formatina donusturur: ₺1.234.567"""
    try:
        amount = int(value)
        formatted = f"{amount:,}".replace(",", ".")
        return f"₺{formatted}"
    except (ValueError, TypeError):
        return "₺0"


def _format_number(value: int | float) -> str:
    """Sayiyi Turkce binlik ayiracla formatlar: 1.234.567"""
    try:
        amount = int(value)
        return f"{amount:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"


def _format_decimal(value: float, decimals: int = 1) -> str:
    """Ondalik sayiyi Turkce formata donusturur: 85,3"""
    try:
        formatted = f"{value:.{decimals}f}".replace(".", ",")
        return formatted
    except (ValueError, TypeError):
        return "0"


def _format_percent(value: float) -> str:
    """Yuzdeli format (0-1 arasi giris): %85,3"""
    try:
        return f"%{value * 100:.1f}".replace(".", ",")
    except (ValueError, TypeError):
        return "%0"


# ---------- Jinja2 Environment ----------

_env: Environment | None = None


def _get_env() -> Environment:
    """Jinja2 Environment singleton. Thread-safe (GIL)."""
    global _env
    if _env is None:
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            undefined=StrictUndefined,
        )
        env.filters["currency"] = _format_currency
        env.filters["number"] = _format_number
        env.filters["decimal"] = _format_decimal
        env.filters["percent"] = _format_percent
        _env = env
    return _env


# ---------- PDF Generation ----------


def generate_valuation_pdf(valuation_data: dict) -> bytes:
    """
    Degerleme raporu PDF'i olusturur.

    WeasyPrint sync calisir — endpoint'te asyncio.to_thread() ile cagrilmali.

    Args:
        valuation_data: Template'e gecirilecek veri dict'i.
            Zorunlu: prediction_id, report_date, district, neighborhood,
            property_type, net_sqm, gross_sqm, room_count, living_room_count,
            floor, total_floors, building_age, heating_type, estimated_price,
            min_price, max_price, price_per_sqm, confidence, model_version.
            Opsiyonel:
                comparables (list[dict]) — emsal mulkler.
                area_stats (dict) — bolge istatistikleri.
                office_info (dict|None) — firma bilgisi {name, logo_url, phone, email}.
                user_info (dict|None) — danisman bilgisi {full_name, email, phone}.
                area_trend (list[dict]|None) — bolge fiyat trendi
                    [{period, avg_price_sqm, median_price, listing_count, change_pct}].

    Returns:
        PDF icerik bytelari.
    """
    # Yeni opsiyonel alanlarin template'te hata vermemesi icin default degerler
    valuation_data.setdefault("office_info", None)
    valuation_data.setdefault("user_info", None)
    valuation_data.setdefault("area_trend", None)

    env = _get_env()
    template = env.get_template("valuation_report.html")
    html_content = template.render(**valuation_data)

    from weasyprint import HTML  # noqa: I001 — lazy import: weasyprint agir bagimliligi sadece PDF uretiminde yukle

    pdf_bytes: bytes = HTML(
        string=html_content,
        encoding="utf-8",
        base_url=str(_TEMPLATE_DIR),
    ).write_pdf()

    logger.info(
        "pdf_valuation_report_generated",
        prediction_id=valuation_data.get("prediction_id"),
        pdf_size_bytes=len(pdf_bytes),
    )

    return pdf_bytes
