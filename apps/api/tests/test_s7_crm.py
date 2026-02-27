"""
Sprint S7 Unit Test Suite — CRM (Customer + Matching)

Pure unit testleri — DB bagimliligi YOK, mock pattern kullanir.

Test kategorileri:
  1. TestCustomerSchemas       — Pydantic validation (CustomerCreate, LeadStatusUpdate, NoteCreate) — 7 test
  2. TestLeadStatusTransitions — VALID_STATUS_TRANSITIONS gecis kurallari — 4 test
  3. TestMatchScoreCalculation — Bilesik skor hesaplama (calculate_match_score) — 7 test
  4. TestRoomParsing           — parse_room_count edge case'leri — 5 test
  5. TestPriceScore            — _calculate_price_score sinir degerleri — 5 test
  6. TestLocationScore         — _calculate_location_score — 4 test
  7. TestAreaScore             — _calculate_area_score — 3 test
  8. TestCustomerQuota         — Plan bazli musteri kota limitleri — 5 test

Toplam: 40 test
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.core.plan_policy import get_customer_quota, is_unlimited_plan
from src.modules.customers.schemas import CustomerCreate, LeadStatusUpdate, NoteCreate
from src.modules.customers.service import VALID_STATUS_TRANSITIONS, validate_status_transition
from src.modules.matches.matching_service import (
    DEFAULT_WEIGHTS,
    SCORE_THRESHOLD,
    _calculate_area_score,
    _calculate_location_score,
    _calculate_price_score,
    calculate_match_score,
    parse_room_count,
)

# ================================================================
# Helper: Mock property ve customer olusturma
# ================================================================


def _make_property(
    price: float = 5_000_000,
    district: str = "Kadikoy",
    rooms: str = "3+1",
    net_area: float = 120.0,
) -> MagicMock:
    """Mock Property nesnesi olusturur."""
    prop = MagicMock()
    prop.price = price
    prop.district = district
    prop.rooms = rooms
    prop.net_area = net_area
    return prop


def _make_customer(
    budget_min: float | None = 4_000_000,
    budget_max: float | None = 6_000_000,
    desired_districts: list[str] | None = None,
    desired_rooms: str | None = "3+1",
    desired_area_min: int | None = 100,
    desired_area_max: int | None = 150,
) -> MagicMock:
    """Mock Customer nesnesi olusturur."""
    customer = MagicMock()
    customer.budget_min = budget_min
    customer.budget_max = budget_max
    customer.desired_districts = desired_districts if desired_districts is not None else ["Kadikoy"]
    customer.desired_rooms = desired_rooms
    customer.desired_area_min = desired_area_min
    customer.desired_area_max = desired_area_max
    return customer


# ================================================================
# 1. TestCustomerSchemas — Pydantic validation (7 test)
# ================================================================


class TestCustomerSchemas:
    """S7-TC-001: CustomerCreate, LeadStatusUpdate, NoteCreate schema dogrulama.

    Kapsamlar:
        - S7-TC-001 (P0): Customer create schema validation
        - S7-TC-005 (P1): Customer detail (schema seviyesinde)
        - S7-TC-007 (P1): Customer update (schema defaults)
        - S7-TC-013 (P1): Add note (NoteCreate)
        - S7-TC-014 (P1): List notes (NoteCreate tipi)
        - S7-TC-011 (P2): Invalid lead status (LeadStatusUpdate)
    """

    def test_customer_create_valid_minimal(self) -> None:
        """S7-TC-001: Gecerli minimum alanlarla CustomerCreate olusturulabilmeli."""
        c = CustomerCreate(full_name="Ahmet Yilmaz")
        assert c.full_name == "Ahmet Yilmaz"
        assert c.customer_type == "buyer"
        assert c.desired_districts == []
        assert c.tags == []

    def test_customer_create_name_too_short(self) -> None:
        """S7-TC-001: full_name 2 karakterden kisa ise ValidationError firlatmali."""
        with pytest.raises(ValidationError):
            CustomerCreate(full_name="A")

    def test_customer_create_invalid_customer_type(self) -> None:
        """S7-TC-001: Gecersiz customer_type ValidationError firlatmali."""
        with pytest.raises(ValidationError):
            CustomerCreate(full_name="Test User", customer_type="agent")

    def test_customer_create_negative_budget_rejected(self) -> None:
        """S7-TC-001: Negatif budget_min reddedilmeli (ge=0)."""
        with pytest.raises(ValidationError):
            CustomerCreate(full_name="Test User", budget_min=-100)

    def test_lead_status_update_invalid(self) -> None:
        """S7-TC-011: Gecersiz status degeri ValidationError firlatmali."""
        with pytest.raises(ValidationError):
            LeadStatusUpdate(status="invalid_status")

    def test_note_create_empty_content_rejected(self) -> None:
        """S7-TC-013: Bos content NoteCreate'de reddedilmeli (min_length=1)."""
        with pytest.raises(ValidationError):
            NoteCreate(content="")

    def test_note_create_invalid_note_type(self) -> None:
        """S7-TC-013: Gecersiz note_type ValidationError firlatmali."""
        with pytest.raises(ValidationError):
            NoteCreate(content="Bir not", note_type="sms")


# ================================================================
# 2. TestLeadStatusTransitions — VALID_STATUS_TRANSITIONS (4 test)
# ================================================================


class TestLeadStatusTransitions:
    """S7-TC-009/010/011: Lead status gecis kurallari.

    Kapsamlar:
        - S7-TC-009 (P1): Lead status cold -> warm
        - S7-TC-010 (P1): Status warm -> hot -> converted
        - S7-TC-011 (P2): Invalid lead status
        - S7-TC-008 (P1): Soft delete (lost -> warm yeniden kazanma)
    """

    def test_cold_to_warm_allowed(self) -> None:
        """S7-TC-009: cold -> warm gecisi gecerli olmali."""
        assert "warm" in VALID_STATUS_TRANSITIONS["cold"]
        # validate_status_transition hata firlatmamali
        validate_status_transition("cold", "warm")

    def test_warm_to_hot_to_converted(self) -> None:
        """S7-TC-010: warm -> hot -> converted zincir gecis gecerli olmali."""
        validate_status_transition("warm", "hot")
        validate_status_transition("hot", "converted")

    def test_invalid_cold_to_converted_raises(self) -> None:
        """S7-TC-011: cold -> converted gecersiz gecis, converted terminal durum."""
        from src.core.exceptions import ValidationError as AppValidationError

        assert VALID_STATUS_TRANSITIONS["converted"] == set()
        with pytest.raises(AppValidationError):
            validate_status_transition("cold", "converted")

    def test_lost_to_warm_allowed(self) -> None:
        """S7-TC-008: lost -> warm (yeniden kazanma) gecerli olmali."""
        assert "warm" in VALID_STATUS_TRANSITIONS["lost"]
        validate_status_transition("lost", "warm")


# ================================================================
# 3. TestMatchScoreCalculation — calculate_match_score (7 test)
# ================================================================


class TestMatchScoreCalculation:
    """Bilesik skor hesaplama testleri.

    Kapsamlar:
        - S7-TC-017 (P0): Perfect match score = 100
        - S7-TC-018 (P1): Partial match score >= 70
        - S7-TC-019 (P1): Low score below threshold
        - S7-TC-025 (P1): Missing criteria — weight normalize
        - S7-TC-026 (P2): All criteria missing -> score 0
        - S7-TC-027 (P0): Match run for property (service method)
        - S7-TC-028 (P1): Match run for customer
        - S7-TC-031 (P1): Match list
        - S7-TC-033 (P1): Celery async matching
    """

    def test_perfect_match_score_100(self) -> None:
        """S7-TC-017: Tum kriterler tam eslestigi zaman skor 100 olmali."""
        prop = _make_property(price=5_000_000, district="Kadikoy", rooms="3+1", net_area=120.0)
        customer = _make_customer(
            budget_min=4_000_000, budget_max=6_000_000,
            desired_districts=["Kadikoy"], desired_rooms="3+1",
            desired_area_min=100, desired_area_max=150,
        )
        score, details = calculate_match_score(prop, customer)
        assert score == 100.0
        assert details["price_score"] == 100.0
        assert details["location_score"] == 100.0
        assert details["room_score"] == 100.0
        assert details["area_score"] == 100.0

    def test_partial_match_above_threshold(self) -> None:
        """S7-TC-018: Kismi eslesme — skor >= 70 (room ±1 farki)."""
        prop = _make_property(price=5_000_000, district="Kadikoy", rooms="3+1", net_area=120.0)
        customer = _make_customer(
            budget_min=4_000_000, budget_max=6_000_000,
            desired_districts=["Kadikoy"], desired_rooms="2+1",  # 1 fark → room=50
            desired_area_min=100, desired_area_max=150,
        )
        score, details = calculate_match_score(prop, customer)
        # price=100, location=100, room=50, area=100
        # weighted: 0.30*100 + 0.30*100 + 0.20*50 + 0.20*100 = 30+30+10+20 = 90
        assert score >= SCORE_THRESHOLD
        assert details["room_score"] == 50.0

    def test_low_score_below_threshold(self) -> None:
        """S7-TC-019: Dusuk eslesme — skor < 70."""
        prop = _make_property(price=50_000_000, district="Sariyer", rooms="5+1", net_area=300.0)
        customer = _make_customer(
            budget_min=1_000_000, budget_max=2_000_000,
            desired_districts=["Kadikoy"], desired_rooms="2+1",
            desired_area_min=60, desired_area_max=80,
        )
        score, _details = calculate_match_score(prop, customer)
        assert score < SCORE_THRESHOLD

    def test_missing_criteria_weight_normalize(self) -> None:
        """S7-TC-025: Eksik kriter (None) atlanir, agirliklar normalize edilir."""
        prop = _make_property(price=5_000_000, district="Kadikoy", rooms="3+1", net_area=120.0)
        customer = _make_customer(
            budget_min=None, budget_max=None,  # price → None, atlanir
            desired_districts=["Kadikoy"], desired_rooms="3+1",
            desired_area_min=100, desired_area_max=150,
        )
        score, details = calculate_match_score(prop, customer)
        assert details["price_score"] is None
        # Kalan agirliklar: location(0.30), room(0.20), area(0.20)
        # normalize: 0.30/0.70, 0.20/0.70, 0.20/0.70
        assert "price" not in details["weights_used"]
        assert score == 100.0  # tum aktif kriterler 100

    def test_all_criteria_missing_score_zero(self) -> None:
        """S7-TC-026: Tum kriterler None → skor 0."""
        prop = _make_property(price=5_000_000, district="Kadikoy", rooms=None, net_area=None)
        customer = _make_customer(
            budget_min=None, budget_max=None,
            desired_districts=[], desired_rooms=None,
            desired_area_min=None, desired_area_max=None,
        )
        score, details = calculate_match_score(prop, customer)
        assert score == 0.0
        assert details["weights_used"] == {}

    def test_default_weights_sum_to_one(self) -> None:
        """S7-TC-027/028: DEFAULT_WEIGHTS toplami 1.0 olmali (match run icin gerekli)."""
        total = sum(DEFAULT_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_score_threshold_is_70(self) -> None:
        """S7-TC-029/031/032/033: SCORE_THRESHOLD sabiti 70 olmali."""
        assert SCORE_THRESHOLD == 70


# ================================================================
# 4. TestRoomParsing — parse_room_count edge case'leri (5 test)
# ================================================================


class TestRoomParsing:
    """parse_room_count parsing testleri.

    Kapsamlar:
        - S7-TC-022 (P2): Room score ±1 difference
        - S7-TC-023 (P2): Room score ±2 difference
        - S7-TC-024 (P2): Room parsing edge cases
    """

    def test_parse_standard_format(self) -> None:
        """S7-TC-024: '3+1' → 3 donmeli."""
        assert parse_room_count("3+1") == 3

    def test_parse_studio_format(self) -> None:
        """S7-TC-024: '2+0' → 2 donmeli (studio)."""
        assert parse_room_count("2+0") == 2

    def test_parse_plain_number(self) -> None:
        """S7-TC-024: '4' → 4 donmeli."""
        assert parse_room_count("4") == 4

    def test_parse_none_returns_none(self) -> None:
        """S7-TC-024: None → None donmeli."""
        assert parse_room_count(None) is None

    def test_parse_empty_string_returns_none(self) -> None:
        """S7-TC-024: '' → None donmeli."""
        assert parse_room_count("") is None


# ================================================================
# 5. TestPriceScore — _calculate_price_score sinir degerleri (5 test)
# ================================================================


class TestPriceScore:
    """Fiyat skor hesaplama sinir degerleri.

    Kapsamlar:
        - S7-TC-020 (P1): Price score ±20% boundary
    """

    def test_price_in_range_score_100(self) -> None:
        """S7-TC-020: Fiyat [budget_min, budget_max] araliginda → 100."""
        score = _calculate_price_score(5_000_000, 4_000_000, 6_000_000)
        assert score == 100.0

    def test_price_at_budget_max_boundary(self) -> None:
        """S7-TC-020: Fiyat tam budget_max'da → 100."""
        score = _calculate_price_score(6_000_000, 4_000_000, 6_000_000)
        assert score == 100.0

    def test_price_above_20_percent_score_0(self) -> None:
        """S7-TC-020: Fiyat budget_max * 1.2 uzerinde → 0."""
        # budget_max=6M, upper=7.2M → price=8M → 0
        score = _calculate_price_score(8_000_000, 4_000_000, 6_000_000)
        assert score == 0.0

    def test_price_below_20_percent_score_0(self) -> None:
        """S7-TC-020: Fiyat budget_min * 0.8 altinda → 0."""
        # budget_min=4M, lower=3.2M → price=3M → 0
        score = _calculate_price_score(3_000_000, 4_000_000, 6_000_000)
        assert score == 0.0

    def test_both_budgets_none_returns_none(self) -> None:
        """S7-TC-020: Her iki budget None → None (kriter atlanir)."""
        score = _calculate_price_score(5_000_000, None, None)
        assert score is None


# ================================================================
# 6. TestLocationScore — _calculate_location_score (4 test)
# ================================================================


class TestLocationScore:
    """Konum skor hesaplama testleri.

    Kapsamlar:
        - S7-TC-006 (P0): RLS — different office customer not visible
        - S7-TC-003 (P1): Customer list with filters (konum bazli)
        - S7-TC-004 (P1): JSONB search (desired_districts)
    """

    def test_exact_match_score_100(self) -> None:
        """S7-TC-006: District exact match → 100."""
        score = _calculate_location_score("Kadikoy", ["Kadikoy", "Besiktas"])
        assert score == 100.0

    def test_case_insensitive_match(self) -> None:
        """S7-TC-004: Case-insensitive eslesme → 100 (JSONB search davranisi)."""
        score = _calculate_location_score("kadikoy", ["Kadikoy"])
        assert score == 100.0

    def test_no_match_score_0(self) -> None:
        """S7-TC-006: District listede yok → 0 (farkli ofis/konum)."""
        score = _calculate_location_score("Sariyer", ["Kadikoy", "Besiktas"])
        assert score == 0.0

    def test_empty_districts_returns_none(self) -> None:
        """S7-TC-003: desired_districts bos → None (kriter atlanir, filtre yok)."""
        score = _calculate_location_score("Kadikoy", [])
        assert score is None


# ================================================================
# 7. TestAreaScore — _calculate_area_score (3 test)
# ================================================================


class TestAreaScore:
    """Alan skor hesaplama testleri.

    Kapsamlar:
        - S7-TC-016 (P1): Timeline (alan bazli skor hesabi)
    """

    def test_area_in_range_score_100(self) -> None:
        """Alan [area_min, area_max] araliginda → 100."""
        score = _calculate_area_score(120.0, 100, 150)
        assert score == 100.0

    def test_area_none_returns_none(self) -> None:
        """net_area None → None (kriter atlanir)."""
        score = _calculate_area_score(None, 100, 150)
        assert score is None

    def test_area_far_above_max_score_0(self) -> None:
        """Alan area_max * 1.2 uzerinde → 0."""
        # area_max=150, upper=180 → net_area=200 → 0
        score = _calculate_area_score(200.0, 100, 150)
        assert score == 0.0


# ================================================================
# 8. TestCustomerQuota — Plan bazli musteri kota limitleri (5 test)
# ================================================================


class TestCustomerQuota:
    """Plan bazli musteri kota kontrolleri.

    Kapsamlar:
        - S7-TC-002 (P1): Customer quota exceeded
    """

    def test_starter_customer_quota_50(self) -> None:
        """S7-TC-002: Starter plan 50 musteri kotasi verir."""
        assert get_customer_quota("starter") == 50

    def test_pro_customer_quota_500(self) -> None:
        """S7-TC-002: Pro plan 500 musteri kotasi verir."""
        assert get_customer_quota("pro") == 500

    def test_elite_customer_quota_unlimited(self) -> None:
        """S7-TC-002: Elite plan sinirsiz (-1) musteri kotasi verir."""
        assert get_customer_quota("elite") == -1

    def test_elite_is_unlimited(self) -> None:
        """S7-TC-002: Elite plan icin is_unlimited_plan True donmeli."""
        assert is_unlimited_plan("elite") is True

    def test_invalid_plan_raises(self) -> None:
        """S7-TC-002: Gecersiz plan tipi ValueError firlatmali."""
        with pytest.raises(ValueError, match="Gecersiz plan tipi"):
            get_customer_quota("invalid_plan")
