"""
Emlak Teknoloji Platformu - PDF Smoke Tests (S4.3)

WeasyPrint PDF uretimi smoke testleri.
generate_valuation_pdf() fonksiyonunu ornek veri ile cagirarak:
    - PDF bytes donusu
    - Magic bytes (%PDF-)
    - Boyut araligi (5KB < size < 500KB)
    - Turkce karakter destegi (İ, ş, ğ, ü, ö, ç)
    - Eksik opsiyonel veri (area_stats=None, comparables=None)
    - Sayfa sayisi (1+ sayfa)

WeasyPrint lokalde yoksa veya sistem kutuphaneleri eksikse testler atlanir
(Docker'da mevcut).
"""

from __future__ import annotations

import copy
import io

import pytest

# WeasyPrint, Pango/GLib gibi sistem kutuphanelerine bagimlidir.
# Lokal ortamda bu kutuphaneler olmayabilir — modul atlanir.
weasyprint = pytest.importorskip("weasyprint", reason="WeasyPrint gerekli (Docker'da mevcut)")

# ---------- tinyhtml5 uyumluluk yama ----------
# tinyhtml5 2.0.0, HTMLUnicodeInputStream.__init__'de override_encoding
# kabul etmiyor (WeasyPrint encoding="utf-8" gonderiyor).
# Docker image'inda duzeltilmis surum kullanilir; lokal ortamda
# monkey-patch uyguluyoruz.
try:
    import tinyhtml5.inputstream as _tis

    _orig_init = _tis.HTMLUnicodeInputStream.__init__

    def _patched_init(self, source, **_kwargs):  # type: ignore[no-untyped-def]
        _orig_init(self, source)

    import inspect

    if "kwargs" not in str(inspect.signature(_orig_init)):
        _tis.HTMLUnicodeInputStream.__init__ = _patched_init  # type: ignore[method-assign]
except Exception:
    pass

from src.services.pdf_service import generate_valuation_pdf  # noqa: E402

# Runtime dogrulama: WeasyPrint gercekten PDF uretebiliyor mu?
try:
    from weasyprint import HTML as _HTML

    _HTML(string="<html><body>test</body></html>", encoding="utf-8").write_pdf()
    _WEASYPRINT_FUNCTIONAL = True
except Exception:
    _WEASYPRINT_FUNCTIONAL = False

pytestmark = pytest.mark.skipif(
    not _WEASYPRINT_FUNCTIONAL,
    reason="WeasyPrint runtime uyumsuz (sistem kutuphaneleri eksik) — Docker'da calisir",
)


# ================================================================
# Conftest override: PDF smoke testleri DB gerektirmez
# ================================================================
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Override: PDF smoke testleri PostgreSQL baglantisi gerektirmez."""
    yield


# ================================================================
# Ornek Veri (template'in beklediği flat yapi)
# ================================================================
_SAMPLE_DATA: dict = {
    "prediction_id": "test-prediction-001-abc",
    "report_date": "2026-02-21",
    "model_version": "v0",
    "district": "Kadıköy",
    "neighborhood": "Caferağa",
    "property_type": "konut",
    "net_sqm": 105,
    "gross_sqm": 120,
    "room_count": 3,
    "living_room_count": 1,
    "floor": 3,
    "total_floors": 8,
    "building_age": 5,
    "heating_type": "Doğalgaz (Kombi)",
    "estimated_price": 8500000,
    "min_price": 7650000,
    "max_price": 9350000,
    "price_per_sqm": 70833,
    "confidence": 0.85,
    "area_stats": {
        "avg_price_sqm_sale": 72000,
        "avg_price_sqm_rent": 350,
        "listing_count": 1250,
        "population": 481000,
        "transport_score": 8.5,
        "investment_score": 7.8,
    },
    "comparables": [
        {
            "district": "Kadıköy",
            "net_sqm": 115,
            "price": 8200000,
            "building_age": 3,
            "room_count": "3+1",
            "similarity_score": 92,
        },
        {
            "district": "Kadıköy",
            "net_sqm": 125,
            "price": 8800000,
            "building_age": 7,
            "room_count": "3+1",
            "similarity_score": 87,
        },
    ],
}


def _make_data(**overrides) -> dict:
    """Ornek veriyi kopyalayip override uygular."""
    data = copy.deepcopy(_SAMPLE_DATA)
    data.update(overrides)
    return data


# ================================================================
# PDF Uretim Smoke Testleri
# ================================================================
class TestPdfGeneration:
    """generate_valuation_pdf() temel cikti dogrulamalari."""

    def test_returns_bytes(self):
        """PDF uretimi bytes tipinde sonuc donmeli."""
        result = generate_valuation_pdf(_make_data())
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_magic_bytes(self):
        """PDF dosyasi %PDF- magic bytes ile baslamali."""
        result = generate_valuation_pdf(_make_data())
        assert result[:5] == b"%PDF-", f"Beklenen: %PDF-, Gelen: {result[:10]!r}"

    def test_size_range(self):
        """PDF boyutu 5KB-500KB araliginda olmali."""
        result = generate_valuation_pdf(_make_data())
        size_kb = len(result) / 1024
        assert 5 < size_kb < 500, f"PDF boyutu beklenmedik: {size_kb:.1f} KB"

    def test_has_at_least_one_page(self):
        """PDF en az 1 sayfa icermeli (pypdf ile dogrulama)."""
        from pypdf import PdfReader

        result = generate_valuation_pdf(_make_data())
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) >= 1, f"Sayfa bulunamadi (pages: {len(reader.pages)})"


# ================================================================
# Turkce Karakter Destegi
# ================================================================
class TestTurkishCharacterSupport:
    """Turkce ozel karakterler iceren veri ile PDF olusturma."""

    def test_turkish_chars_in_district(self):
        """İlçe adinda Turkce karakterler (İ, ö, ü) → PDF olusabilmeli."""
        data = _make_data(
            district="Üsküdar",
            neighborhood="Çengelköy",
            heating_type="Doğalgaz (Kombi)",
        )
        result = generate_valuation_pdf(data)
        assert result[:5] == b"%PDF-"

    def test_all_special_turkish_chars(self):
        """Tum Turkce ozel karakterler: İ, ı, Ş, ş, Ğ, ğ, Ü, ü, Ö, ö, Ç, ç."""
        data = _make_data(
            district="Şişli",
            neighborhood="İçerenköy Güneşlibağ",
            property_type="Müstakil Çatılı",
        )
        result = generate_valuation_pdf(data)
        assert isinstance(result, bytes)
        size_kb = len(result) / 1024
        assert size_kb > 5, f"Turkce karakterli PDF cok kucuk: {size_kb:.1f} KB"


# ================================================================
# Opsiyonel Veri Eksikliginde Graceful Degradation
# ================================================================
class TestGracefulDegradation:
    """Opsiyonel alanlar (area_stats, comparables) eksikken PDF olusturma."""

    def test_no_area_stats(self):
        """area_stats=None → Bolge Analizi bolumu atlanmali, PDF olusabilmeli."""
        data = _make_data(area_stats=None)
        result = generate_valuation_pdf(data)
        assert result[:5] == b"%PDF-"
        size_kb = len(result) / 1024
        assert 5 < size_kb < 500

    def test_no_comparables(self):
        """comparables=None → Emsal bolumu atlanmali, PDF olusabilmeli."""
        data = _make_data(comparables=None)
        result = generate_valuation_pdf(data)
        assert result[:5] == b"%PDF-"

    def test_no_optional_fields(self):
        """area_stats=None ve comparables=None → yalnizca zorunlu alanlar ile PDF."""
        data = _make_data(area_stats=None, comparables=None)
        result = generate_valuation_pdf(data)
        assert result[:5] == b"%PDF-"
        size_kb = len(result) / 1024
        assert 5 < size_kb < 500

    def test_empty_comparables_list(self):
        """comparables=[] (bos liste) → Emsal bolumu atlanmali."""
        data = _make_data(comparables=[])
        result = generate_valuation_pdf(data)
        assert result[:5] == b"%PDF-"
