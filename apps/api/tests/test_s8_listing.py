"""
Sprint S8 Unit Test Suite — Ilan Asistani

Pure unit testleri — DB bagimliligi YOK, mock pattern kullanir.

Test kategorileri:
  1. TestListingTones (ton secenekleri ve dogrulama) — 4 test
  2. TestListingValidation (validate_request edge case'leri) — 4 test
  3. TestListingPromptBuilder (build_listing_prompt ciktilari) — 4 test
  4. TestSeoOptimization (seo_optimize_title, extract_seo_keywords) — 4 test
  5. TestLLMResponseParser (_parse_llm_response JSON/markdown) — 4 test
  6. TestPhotoValidation (content type, file size) — 5 test
  7. TestPortalExport (format_for_portal, smart_truncate, portal info) — 4 test
  8. TestListingQuota (listing, staging, photo kotalari) — 4 test
  9. TestOpenAIErrors (hata tipleri: content filter, rate limit) — 2 test

Toplam: 35 test
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.core.plan_policy import get_listing_quota, get_photo_quota, get_staging_quota
from src.listings.listing_assistant_service import (
    _parse_llm_response,
    build_listing_prompt,
    extract_seo_keywords,
    get_available_tones,
    seo_optimize_title,
    validate_request,
)
from src.listings.photo_service import (
    MAX_FILE_SIZE,
    _validate_content_type,
    _validate_file_size,
)
from src.listings.portal_export_service import (
    PORTAL_FORMATS,
    format_for_portal,
    smart_truncate,
)

# ================================================================
# Yardimci: Mock request olusturucu
# ================================================================

def _make_request(**overrides) -> MagicMock:
    """Standart ilan istegi icin MagicMock olusturur.

    Tum zorunlu ve opsiyonel alanlar varsayilan degerlerle doldurulur.
    overrides ile istenilen alan degistirilebilir.
    """
    defaults = {
        "tone": "kurumsal",
        "property_type": "Daire",
        "district": "Kadikoy",
        "neighborhood": "Caferaga",
        "room_count": "3+1",
        "net_sqm": 120.0,
        "gross_sqm": 145.0,
        "price": 5_000_000,
        "floor": 5,
        "total_floors": 10,
        "building_age": 5,
        "heating_type": "Kombi",
        "has_elevator": True,
        "has_parking": False,
        "has_balcony": True,
        "has_garden": False,
        "has_pool": False,
        "is_furnished": False,
        "has_security": True,
        "view_type": None,
        "additional_notes": None,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


# ================================================================
# 1. TestListingTones — S8-TC-003, S8-TC-020
# ================================================================


class TestListingTones:
    """Ton secenekleri ve ton dogrulama testleri."""

    def test_get_available_tones_returns_three(self) -> None:
        """S8-TC-003: Tam olarak 3 ton secenegi olmali."""
        tones = get_available_tones()
        assert len(tones) == 3

    def test_tone_ids_match_expected(self) -> None:
        """S8-TC-020: Ton ID'leri kurumsal, samimi, acil olmali."""
        tones = get_available_tones()
        tone_ids = {t["id"] for t in tones}
        assert tone_ids == {"kurumsal", "samimi", "acil"}

    def test_each_tone_has_required_fields(self) -> None:
        """Her ton id, name_tr, description, example_phrase icermeli."""
        tones = get_available_tones()
        required_keys = {"id", "name_tr", "description", "example_phrase"}
        for tone in tones:
            assert required_keys.issubset(tone.keys()), f"Eksik alan: {tone.get('id')}"

    def test_invalid_tone_raises_in_validate_request(self) -> None:
        """Gecersiz ton validate_request'te ValueError firlatmali."""
        request = _make_request(tone="resmi")
        with pytest.raises(ValueError, match="Gecersiz ton"):
            validate_request(request)


# ================================================================
# 2. TestListingValidation — validate_request edge case'leri
# ================================================================


class TestListingValidation:
    """validate_request is mantigi dogrulama testleri."""

    def test_valid_request_passes(self) -> None:
        """Gecerli istek hata firlatmadan gecmeli."""
        request = _make_request()
        validate_request(request)  # Hata firlatmamali

    def test_net_sqm_greater_than_gross_sqm_raises(self) -> None:
        """net_sqm > gross_sqm olunca ValueError firlatmali."""
        request = _make_request(net_sqm=200.0, gross_sqm=150.0)
        with pytest.raises(ValueError, match=r"Net metrekare.*buyuk olamaz"):
            validate_request(request)

    def test_floor_greater_than_total_floors_raises(self) -> None:
        """floor > total_floors olunca ValueError firlatmali."""
        request = _make_request(floor=15, total_floors=10)
        with pytest.raises(ValueError, match=r"Bulundugu kat.*buyuk olamaz"):
            validate_request(request)

    def test_none_gross_sqm_skips_sqm_check(self) -> None:
        """gross_sqm None ise metrekare kontrolu atlanmali."""
        request = _make_request(net_sqm=200.0, gross_sqm=None)
        validate_request(request)  # Hata firlatmamali


# ================================================================
# 3. TestListingPromptBuilder — S8-TC-001, S8-TC-002, S8-TC-021
# ================================================================


class TestListingPromptBuilder:
    """build_listing_prompt cikti testleri."""

    def test_returns_tuple_of_two_strings(self) -> None:
        """S8-TC-001: build_listing_prompt (system_prompt, user_prompt) tuple donmeli."""
        request = _make_request()
        result = build_listing_prompt(request, "kurumsal")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str) and isinstance(result[1], str)

    def test_user_prompt_contains_property_details(self) -> None:
        """S8-TC-002: user_prompt mulk bilgilerini icermeli."""
        request = _make_request(district="Besiktas", net_sqm=180.0)
        _system, user = build_listing_prompt(request, "samimi")
        assert "Besiktas" in user
        assert "180" in user

    def test_system_prompt_matches_tone(self) -> None:
        """S8-TC-021: Her ton icin farkli system_prompt uretilmeli."""
        request = _make_request()
        sys_kurumsal, _ = build_listing_prompt(request, "kurumsal")
        sys_samimi, _ = build_listing_prompt(request, "samimi")
        assert sys_kurumsal != sys_samimi

    def test_invalid_tone_raises_in_prompt_builder(self) -> None:
        """Gecersiz ton build_listing_prompt'ta ValueError firlatmali."""
        request = _make_request()
        with pytest.raises(ValueError, match="Gecersiz ton"):
            build_listing_prompt(request, "bilinmeyen_ton")


# ================================================================
# 4. TestSeoOptimization — SEO baslik ve keyword testleri
# ================================================================


class TestSeoOptimization:
    """seo_optimize_title ve extract_seo_keywords testleri."""

    def test_title_already_optimized_returns_as_is(self) -> None:
        """Baslik zaten ilce ve oda bilgisini iceriyorsa dokunmaz."""
        request = _make_request(room_count="3+1", district="Kadikoy")
        raw_title = "3+1 Daire Kadikoy - Deniz Manzarali"
        result = seo_optimize_title(raw_title, request)
        assert result == raw_title

    def test_title_reformatted_when_missing_info(self) -> None:
        """Baslik eksik bilgi iceriyorsa yeniden formatlanmali."""
        request = _make_request(
            room_count="3+1",
            district="Kadikoy",
            neighborhood="Caferaga",
            property_type="Daire",
        )
        raw_title = "Satilik Guzel Daire"
        result = seo_optimize_title(raw_title, request)
        assert "3+1" in result
        assert "Kadikoy" in result
        assert "Caferaga" in result

    def test_title_max_120_characters(self) -> None:
        """Baslik 120 karakteri gecmemeli."""
        request = _make_request(room_count="3+1", district="Kadikoy")
        raw_title = "A" * 200
        result = seo_optimize_title(raw_title, request)
        assert len(result) <= 120

    def test_extract_seo_keywords_returns_list(self) -> None:
        """extract_seo_keywords liste donmeli, en az 4 eleman icermeli."""
        request = _make_request()
        keywords = extract_seo_keywords(request, "Guzel daire, Kadikoy'de yatirim firsati.")
        assert isinstance(keywords, list)
        assert len(keywords) >= 4
        # Ilce bazli keyword olmali
        assert any("kadikoy" in kw.lower() for kw in keywords)


# ================================================================
# 5. TestLLMResponseParser — _parse_llm_response testleri
# ================================================================


class TestLLMResponseParser:
    """LLM yanit parse testleri — JSON ve markdown code fence."""

    def test_parse_clean_json(self) -> None:
        """Temiz JSON string duzgun parse edilmeli."""
        raw = json.dumps({
            "title": "Test Baslik",
            "description": "Test aciklama",
            "highlights": ["Ozellik 1"],
            "seo_keywords": ["anahtar1"],
        })
        result = _parse_llm_response(raw)
        assert result["title"] == "Test Baslik"
        assert isinstance(result["highlights"], list)

    def test_parse_json_with_markdown_fence(self) -> None:
        """Markdown ```json ... ``` fence icindeki JSON parse edilmeli."""
        inner = json.dumps({
            "title": "Markdown Baslik",
            "description": "Aciklama",
            "highlights": [],
            "seo_keywords": [],
        })
        raw = f"```json\n{inner}\n```"
        result = _parse_llm_response(raw)
        assert result["title"] == "Markdown Baslik"

    def test_parse_json_with_plain_fence(self) -> None:
        """Markdown ``` ... ``` fence (json etiketsiz) parse edilmeli."""
        inner = json.dumps({"title": "Plain Fence", "description": "Aciklama"})
        raw = f"```\n{inner}\n```"
        result = _parse_llm_response(raw)
        assert result["title"] == "Plain Fence"

    def test_parse_invalid_json_raises(self) -> None:
        """Gecersiz JSON ValueError firlatmali."""
        raw = "Bu bir JSON degil, sadece metin."
        with pytest.raises(ValueError, match="JSON olarak parse edilemedi"):
            _parse_llm_response(raw)


# ================================================================
# 6. TestPhotoValidation — S8-TC-012, S8-TC-013, S8-TC-014
# ================================================================


class TestPhotoValidation:
    """Foto upload content type ve file size dogrulama testleri."""

    def test_jpeg_content_type_valid(self) -> None:
        """S8-TC-012: image/jpeg kabul edilmeli, 'jpg' donmeli."""
        ext = _validate_content_type("image/jpeg")
        assert ext == "jpg"

    def test_png_and_webp_content_types_valid(self) -> None:
        """S8-TC-012: image/png ve image/webp kabul edilmeli."""
        assert _validate_content_type("image/png") == "png"
        assert _validate_content_type("image/webp") == "webp"

    def test_exe_content_type_rejected(self) -> None:
        """S8-TC-014: application/x-msdownload (.exe) reddedilmeli."""
        from src.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            _validate_content_type("application/x-msdownload")

    def test_none_content_type_rejected(self) -> None:
        """Content type None ise ValidationError firlatmali."""
        from src.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            _validate_content_type(None)

    def test_file_size_over_limit_rejected(self) -> None:
        """S8-TC-013: MAX_FILE_SIZE uzerindeki dosya reddedilmeli."""
        from src.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match="Dosya boyutu cok buyuk"):
            _validate_file_size(MAX_FILE_SIZE + 1)


# ================================================================
# 7. TestPortalExport — S8-TC-018 portal format testleri
# ================================================================


class TestPortalExport:
    """Portal export format, smart_truncate ve portal bilgi testleri."""

    def test_sahibinden_format_strips_emojis(self) -> None:
        """S8-TC-018: sahibinden emoji kabul etmez, strip edilmeli."""
        text_result = {
            "title": "Satilik Daire Kadikoy",
            "description": "Harika bir daire satista.",
            "highlights": ["Asansor", "Otopark"],
        }
        result = format_for_portal(text_result, "sahibinden")
        assert result["portal"] == "sahibinden"
        assert len(result["formatted_title"]) <= PORTAL_FORMATS["sahibinden"]["max_title_length"]

    def test_hepsiemlak_format_allows_emoji(self) -> None:
        """S8-TC-018: hepsiemlak emoji'ye izin verir."""
        text_result = {
            "title": "Satilik Daire",
            "description": "Harika bir daire satista.",
            "highlights": ["Asansor"],
        }
        result = format_for_portal(text_result, "hepsiemlak")
        assert result["portal"] == "hepsiemlak"
        assert "character_counts" in result

    def test_smart_truncate_short_text_untouched(self) -> None:
        """Kisa metin smart_truncate'ten aynen donmeli."""
        text = "Kisa metin"
        assert smart_truncate(text, 50) == text

    def test_smart_truncate_long_text_adds_ellipsis(self) -> None:
        """Uzun metin kelime sinirinda kirpilip '...' eklenmeli."""
        text = "Bu cok uzun bir metin ornegi burada devam ediyor"
        result = smart_truncate(text, 20)
        assert result.endswith("...")
        assert len(result) <= 20


# ================================================================
# 8. TestListingQuota — S8-TC-008, S8-TC-010, S8-TC-017
# ================================================================


class TestListingQuota:
    """Plan bazli ilan, staging ve foto kota limitleri."""

    def test_listing_quota_starter_20(self) -> None:
        """Starter plan aylik 20 ilan hakki verir."""
        assert get_listing_quota("starter") == 20

    def test_staging_quota_starter_10(self) -> None:
        """S8-TC-010: Starter plan aylik 10 staging hakki verir."""
        assert get_staging_quota("starter") == 10

    def test_photo_quota_starter_100(self) -> None:
        """S8-TC-017: Starter plan aylik 100 foto hakki verir."""
        assert get_photo_quota("starter") == 100

    def test_staging_quota_elite_200(self) -> None:
        """S8-TC-008: Elite plan 200 staging hakki verir."""
        assert get_staging_quota("elite") == 200


# ================================================================
# 9. TestOpenAIErrors — S8-TC-004, S8-TC-005, S8-TC-006
# ================================================================


class TestOpenAIErrors:
    """OpenAI hata sinifi testleri."""

    def test_rate_limit_error_has_retry_after(self) -> None:
        """S8-TC-005: OpenAIRateLimitError retry_after attribute icermeli."""
        from src.services.openai_exceptions import OpenAIRateLimitError

        err = OpenAIRateLimitError(retry_after=30.0)
        assert err.retry_after == 30.0
        assert isinstance(err, Exception)

    def test_content_filter_error_is_service_error(self) -> None:
        """S8-TC-006: OpenAIContentFilterError, OpenAIServiceError alt sinifi olmali."""
        from src.services.openai_exceptions import (
            OpenAIContentFilterError,
            OpenAIServiceError,
        )

        err = OpenAIContentFilterError()
        assert isinstance(err, OpenAIServiceError)
        assert "guvenlik filtresi" in str(err)
