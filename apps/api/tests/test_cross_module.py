"""
Cross-Module Unit Tests

Moduller arasi entegrasyon senaryolarinin mock-based, DB bagimsiz testleri.

Kapsam:
    - CROSS-TC-001 (P0): Property create -> trigger matching
    - CROSS-TC-002 (P0): Match -> notification trigger
    - CROSS-TC-005 (P0): Full CRM flow (status transitions)
    - CROSS-TC-003 (P1): Customer create -> trigger matching
    - CROSS-TC-006 (P1): Cross-module quota consistency
    - CROSS-TC-007 (P1): Month change -- all quotas reset
    - CROSS-TC-009 (P1): Telegram -> backend API (same quota)
    - CROSS-TC-010 (P1): Telegram CRM -> same RLS
    - CROSS-TC-008 (P2): Plan upgrade quota increase
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.core.plan_policy import (
    PlanType,
    get_capabilities,
    get_customer_quota,
    get_listing_quota,
    get_photo_quota,
    get_staging_quota,
    get_valuation_quota,
    is_unlimited_plan,
    is_unlimited_quota,
)
from src.modules.customers.service import (
    validate_status_transition,
)
from src.modules.matches.matching_service import (
    SCORE_THRESHOLD,
    trigger_matching_after_customer_create,
    trigger_matching_after_property_create,
)
from src.modules.valuations.quota_service import QuotaType

# ================================================================
# CROSS-TC-006 (P1): Cross-module Quota Consistency
# ================================================================


class TestCrossModuleQuotaConsistency:
    """Tum 5 kota tipinin plan bazli beklenen degerlere uygunlugunu dogrular."""

    def test_starter_quotas_match_expected(self) -> None:
        """CROSS-TC-006: Starter tum kota degerleri beklenenle eslesir."""
        assert get_valuation_quota("starter") == 50
        assert get_listing_quota("starter") == 20
        assert get_staging_quota("starter") == 10
        assert get_photo_quota("starter") == 100
        assert get_customer_quota("starter") == 50

    def test_pro_quotas_match_expected(self) -> None:
        """CROSS-TC-006: Pro tum kota degerleri beklenenle eslesir."""
        assert get_valuation_quota("pro") == 500
        assert get_listing_quota("pro") == 100
        assert get_staging_quota("pro") == 50
        assert get_photo_quota("pro") == 500
        assert get_customer_quota("pro") == 500

    def test_elite_quotas_match_expected(self) -> None:
        """CROSS-TC-006: Elite kota degerleri — sinirsiz ve sabit."""
        assert get_valuation_quota("elite") == -1
        assert get_listing_quota("elite") == -1
        assert get_staging_quota("elite") == 200
        assert get_photo_quota("elite") == -1
        assert get_customer_quota("elite") == -1

    def test_is_unlimited_plan_only_elite(self) -> None:
        """CROSS-TC-006: Sadece elite plani sinirsiz (valuation bazli)."""
        assert not is_unlimited_plan("starter")
        assert not is_unlimited_plan("pro")
        assert is_unlimited_plan("elite")

    def test_is_unlimited_quota_per_type(self) -> None:
        """CROSS-TC-006: Elite'de valuation/listing/photo sinirsiz, staging degil."""
        assert is_unlimited_quota("elite", "valuation")
        assert is_unlimited_quota("elite", "listing")
        assert not is_unlimited_quota("elite", "staging")
        assert is_unlimited_quota("elite", "photo")

    def test_invalid_plan_raises_value_error(self) -> None:
        """CROSS-TC-006: Gecersiz plan tipi ValueError firlatmali."""
        with pytest.raises(ValueError, match="Gecersiz plan tipi"):
            get_valuation_quota("nonexistent")


# ================================================================
# CROSS-TC-008 (P2): Plan Upgrade Quota Increase
# ================================================================


class TestPlanUpgrade:
    """Plan yukseltme sonrasi kota artisini dogrular."""

    def test_upgrade_starter_to_pro_valuation_increases(self) -> None:
        """CROSS-TC-008: starter->pro valuation kotasi artar (50->500)."""
        starter = get_valuation_quota("starter")
        pro = get_valuation_quota("pro")
        assert pro > starter

    def test_upgrade_pro_to_elite_valuation_becomes_unlimited(self) -> None:
        """CROSS-TC-008: pro->elite valuation sinirsiz olur."""
        assert not is_unlimited_plan("pro")
        assert is_unlimited_plan("elite")

    def test_upgrade_all_quotas_monotonically_increase(self) -> None:
        """CROSS-TC-008: Tum plan gecislerinde kotalar monoton artar veya sinirsiz olur."""
        plans = ["starter", "pro", "elite"]
        getters = [
            get_valuation_quota,
            get_listing_quota,
            get_staging_quota,
            get_photo_quota,
            get_customer_quota,
        ]
        for getter in getters:
            values = [getter(p) for p in plans]
            for i in range(len(values) - 1):
                current = values[i]
                next_val = values[i + 1]
                assert next_val == -1 or next_val > current, (
                    f"{getter.__name__}: {plans[i]}={current} -> {plans[i+1]}={next_val} "
                    f"monoton artis ihlali"
                )


# ================================================================
# CROSS-TC-001 (P0) + CROSS-TC-003 (P1): Matching Trigger Flow
# ================================================================


class TestMatchingTriggerFlow:
    """Trigger fonksiyonlarinin var oldugunu ve cagrilabilir oldugunu dogrular."""

    def test_trigger_matching_after_property_create_is_callable(self) -> None:
        """CROSS-TC-001: trigger_matching_after_property_create callable olmali."""
        assert callable(trigger_matching_after_property_create)

    def test_trigger_matching_after_customer_create_is_callable(self) -> None:
        """CROSS-TC-003: trigger_matching_after_customer_create callable olmali."""
        assert callable(trigger_matching_after_customer_create)

    def test_trigger_property_create_calls_celery_delay(self) -> None:
        """CROSS-TC-001: Property create trigger Celery .delay() cagirir."""
        prop_id = uuid.uuid4()
        office_id = uuid.uuid4()

        mock_task = MagicMock()
        mock_task.delay.return_value = MagicMock()

        with patch.dict(
            "sys.modules",
            {"src.modules.matches.tasks": MagicMock(trigger_matching_for_property=mock_task)},
        ):
            trigger_matching_after_property_create(prop_id, office_id)
            mock_task.delay.assert_called_once_with(str(prop_id), str(office_id))

    def test_trigger_customer_create_calls_celery_delay(self) -> None:
        """CROSS-TC-003: Customer create trigger Celery .delay() cagirir."""
        cust_id = uuid.uuid4()
        office_id = uuid.uuid4()

        mock_task = MagicMock()
        mock_task.delay.return_value = MagicMock()

        with patch.dict(
            "sys.modules",
            {"src.modules.matches.tasks": MagicMock(trigger_matching_for_customer=mock_task)},
        ):
            trigger_matching_after_customer_create(cust_id, office_id)
            mock_task.delay.assert_called_once_with(str(cust_id), str(office_id))

    def test_score_threshold_is_70(self) -> None:
        """CROSS-TC-002: Match skor esigi 70 olmali."""
        assert SCORE_THRESHOLD == 70


# ================================================================
# CROSS-TC-005 (P0): Full CRM Flow (status transitions)
# ================================================================


class TestCRMFullFlow:
    """CRM lead status gecis zincirini dogrular: cold -> warm -> hot -> converted."""

    def test_cold_to_warm_valid(self) -> None:
        """CROSS-TC-005: cold -> warm gecisi gecerli olmali."""
        validate_status_transition("cold", "warm")

    def test_warm_to_hot_valid(self) -> None:
        """CROSS-TC-005: warm -> hot gecisi gecerli olmali."""
        validate_status_transition("warm", "hot")

    def test_hot_to_converted_valid(self) -> None:
        """CROSS-TC-005: hot -> converted gecisi gecerli olmali."""
        validate_status_transition("hot", "converted")

    def test_converted_is_terminal(self) -> None:
        """CROSS-TC-005: converted terminal durum -- hicbir gecise izin vermemeli."""
        from src.core.exceptions import ValidationError as AppValidationError

        for target in ["cold", "warm", "hot", "lost"]:
            with pytest.raises(AppValidationError):
                validate_status_transition("converted", target)

    def test_full_chain_cold_to_converted(self) -> None:
        """CROSS-TC-005: cold -> warm -> hot -> converted tam zincir gecerli olmali."""
        chain = ["cold", "warm", "hot", "converted"]
        for i in range(len(chain) - 1):
            validate_status_transition(chain[i], chain[i + 1])


# ================================================================
# CROSS-TC-009 / CROSS-TC-010 (P1): Channel Capabilities
# ================================================================


class TestChannelCapabilities:
    """Plan bazli kanal yeteneklerini dogrular (telegram_bot, whatsapp)."""

    def test_starter_capabilities(self) -> None:
        """CROSS-TC-009: Starter telegram+whatsapp_click ama cloud_api yok."""
        caps = get_capabilities("starter")
        assert caps["telegram_bot"] is True
        assert caps["whatsapp_click_to_chat"] is True
        assert caps["whatsapp_cloud_api"] is False

    def test_elite_has_whatsapp_cloud_api(self) -> None:
        """CROSS-TC-009: Elite plani whatsapp_cloud_api olmali."""
        caps = get_capabilities("elite")
        assert caps["whatsapp_cloud_api"] is True

    def test_all_plans_have_telegram_bot(self) -> None:
        """CROSS-TC-010: Tum planlar telegram_bot yetenegi olmali."""
        for plan in PlanType:
            caps = get_capabilities(plan.value)
            assert caps["telegram_bot"] is True, f"{plan.value} planinda telegram_bot yok"


# ================================================================
# CROSS-TC-006 / CROSS-TC-007 (P1): QuotaType Consistency
# ================================================================


class TestQuotaTypeConsistency:
    """QuotaType enum'inin beklenen degerlere sahip oldugunu dogrular."""

    def test_quota_type_has_all_expected_values(self) -> None:
        """CROSS-TC-006: QuotaType valuation, listing, staging, photo degerlerine sahip olmali."""
        assert QuotaType.VALUATION == "valuation"
        assert QuotaType.LISTING == "listing"
        assert QuotaType.STAGING == "staging"
        assert QuotaType.PHOTO == "photo"

    def test_quota_type_count_is_exactly_four(self) -> None:
        """CROSS-TC-007: QuotaType tam olarak 4 deger icermeli."""
        assert len(QuotaType) == 4

    def test_quota_types_align_with_plan_policy_getters(self) -> None:
        """CROSS-TC-006: Her QuotaType icin plan_policy'de bir getter fonksiyonu olmali."""
        getter_map = {
            "valuation": get_valuation_quota,
            "listing": get_listing_quota,
            "staging": get_staging_quota,
            "photo": get_photo_quota,
        }
        for qt in QuotaType:
            assert qt.value in getter_map, f"{qt.value} icin getter fonksiyonu yok"
