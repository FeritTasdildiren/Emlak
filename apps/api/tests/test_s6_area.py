"""
Sprint S6 e2e Test Suite — Bolge Analizi (Area Analysis)

Pure unit testleri — DB bagimliligi YOK, mock pattern kullanir.

Test kategorileri:
  1. TestEarthquakeRiskLevel — calculate_risk_level fonksiyon testleri (6 test)
  2. TestBuildingScore — BuildingScoreService.calculate_score testleri (7 test)
  3. TestInvestmentMetrics — _calculate_investment_metrics testleri (7 test)
  4. TestAreaPublicPaths — PUBLIC_PATHS/PREFIXES kontrolu (5 test)

Toplam: 25 test
"""

from __future__ import annotations

from src.middleware.tenant import PUBLIC_PATH_PREFIXES, PUBLIC_PATHS
from src.modules.areas.router import _calculate_investment_metrics
from src.modules.earthquake.building_score import (
    _RETROFIT_REDUCTION,
    BuildingScoreService,
)
from src.modules.earthquake.schemas import (
    BuildingScoreRequest,
    ConstructionType,
    RiskLevel,
    SoilClass,
)
from src.modules.earthquake.service import calculate_risk_level

# ================================================================
# 1. Deprem Risk Seviyesi Testleri (calculate_risk_level)
# ================================================================


class TestEarthquakeRiskLevel:
    """Deprem risk seviyesi hesaplama — calculate_risk_level fonksiyonu."""

    def test_pga_below_01_returns_dusuk(self) -> None:
        """S6-TC-013: Deprem riski — gecerli koordinat → risk level hesaplama (P0)."""
        assert calculate_risk_level(0.05) == "Dusuk"

    def test_pga_exactly_0_returns_dusuk(self) -> None:
        """S6-TC-013: PGA = 0 → en dusuk risk seviyesi (P0)."""
        assert calculate_risk_level(0.0) == "Dusuk"

    def test_pga_01_to_02_returns_orta(self) -> None:
        """S6-TC-013: PGA 0.1-0.2 arasi → Orta risk seviyesi (P0)."""
        assert calculate_risk_level(0.15) == "Orta"

    def test_pga_02_to_04_returns_yuksek(self) -> None:
        """S6-TC-013: PGA 0.2-0.4 arasi → Yuksek risk seviyesi (P0)."""
        assert calculate_risk_level(0.35) == "Yuksek"

    def test_pga_above_04_returns_cok_yuksek(self) -> None:
        """S6-TC-013: PGA >= 0.4 → Cok Yuksek risk seviyesi (P0)."""
        assert calculate_risk_level(0.6) == "Cok Yuksek"

    def test_pga_none_returns_bilinmiyor(self) -> None:
        """S6-TC-015: Gecersiz/eksik koordinat → PGA None ise 'Bilinmiyor' donmeli (P1)."""
        assert calculate_risk_level(None) == "Bilinmiyor"


# ================================================================
# 2. Bina Guvenlik Skoru Testleri (BuildingScoreService)
# ================================================================


class TestBuildingScore:
    """Bina deprem guvenlik skoru — BuildingScoreService.calculate_score."""

    def test_new_building_low_risk(self) -> None:
        """S6-TC-023: DepremRiskCard — yeni bina, iyi zemin → yuksek guvenlik skoru (P1)."""
        request = BuildingScoreRequest(
            building_age=0,
            floors=2,
            soil_class=SoilClass.ZA,
            construction_type=ConstructionType.CELIK,
            has_retrofit=None,
        )
        result = BuildingScoreService.calculate_score(request)

        # Celik (0.9) * age<=0 (1.0) * floors<=3 (1.0) * ZA (1.0) = 0.9
        # safety = min(100, 100 - (0.9 - 1)*7) = 100 + 0.7 = 100.7 → clamped 100
        assert result.safety_score == 100.0
        assert result.risk_level == RiskLevel.LOW
        assert result.color_code == "green"

    def test_old_building_high_risk(self) -> None:
        """S6-TC-023: DepremRiskCard — eski bina, zayif zemin → dusuk guvenlik skoru (P1)."""
        request = BuildingScoreRequest(
            building_age=55,
            floors=10,
            soil_class=SoilClass.ZE,
            construction_type=ConstructionType.YIGMA,
            has_retrofit=None,
        )
        result = BuildingScoreService.calculate_score(request)

        # age>51 (2.5) * floors 8-15 (1.3) * ZE (2.2) * yigma (1.5) = 10.725
        # safety = max(0, 100 - (10.725 - 1)*7) = 100 - 68.075 = 31.925
        assert result.safety_score < 35
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)

    def test_retrofit_reduces_risk(self) -> None:
        """S6-TC-016: Guclendirme (retrofit) yapilmis bina → %30 risk azaltma (P2)."""
        base_request = BuildingScoreRequest(
            building_age=30,
            floors=5,
            soil_class=SoilClass.ZC,
            construction_type=ConstructionType.BETONARME,
            has_retrofit=False,
        )
        retrofit_request = BuildingScoreRequest(
            building_age=30,
            floors=5,
            soil_class=SoilClass.ZC,
            construction_type=ConstructionType.BETONARME,
            has_retrofit=True,
        )

        base_result = BuildingScoreService.calculate_score(base_request)
        retrofit_result = BuildingScoreService.calculate_score(retrofit_request)

        # Guclendirme yapilmis binanin skoru daha yuksek olmali
        assert retrofit_result.safety_score > base_result.safety_score

    def test_retrofit_reduction_constant_is_030(self) -> None:
        """S6-TC-016: Retrofit azaltma katsayisi %30 olmali (P2)."""
        assert _RETROFIT_REDUCTION == 0.30

    def test_result_contains_disclaimer(self) -> None:
        """S6-TC-023: Sonuc yasal uyari (disclaimer) icermeli (P1)."""
        request = BuildingScoreRequest(
            building_age=10,
            floors=5,
            soil_class=SoilClass.ZB,
        )
        result = BuildingScoreService.calculate_score(request)

        assert result.disclaimer is not None
        assert len(result.disclaimer) > 0
        assert "bilgilendirme" in result.disclaimer.lower()

    def test_score_clamped_between_0_and_100(self) -> None:
        """S6-TC-016: Guvenlik skoru 0-100 arasinda clamp edilmeli (P2)."""
        # En kotu senaryo: eski, yuksek, yumusak zemin, ahsap
        worst_request = BuildingScoreRequest(
            building_age=80,
            floors=20,
            soil_class=SoilClass.ZE,
            construction_type=ConstructionType.AHSAP,
            has_retrofit=None,
        )
        result = BuildingScoreService.calculate_score(worst_request)
        assert 0 <= result.safety_score <= 100

        # En iyi senaryo
        best_request = BuildingScoreRequest(
            building_age=1,
            floors=2,
            soil_class=SoilClass.ZA,
            construction_type=ConstructionType.CELIK,
            has_retrofit=True,
        )
        result = BuildingScoreService.calculate_score(best_request)
        assert 0 <= result.safety_score <= 100

    def test_risk_factors_list_populated(self) -> None:
        """S6-TC-023: Yuksek riskli bina icin risk_factors listesi bos olmamali (P1)."""
        request = BuildingScoreRequest(
            building_age=55,
            floors=12,
            soil_class=SoilClass.ZD,
            construction_type=ConstructionType.YIGMA,
            has_retrofit=None,
        )
        result = BuildingScoreService.calculate_score(request)

        assert isinstance(result.risk_factors, list)
        assert len(result.risk_factors) > 0
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0


# ================================================================
# 3. Yatirim Metrikleri Testleri (_calculate_investment_metrics)
# ================================================================


class TestInvestmentMetrics:
    """Yatirim metrikleri hesaplama — _calculate_investment_metrics."""

    def test_valid_kira_verimi_calculation(self) -> None:
        """S6-TC-005: Yatirim metrikleri — gecerli hesaplama, kira_verimi (P1)."""
        # avg_sale=100_000, avg_rent=500
        # kira_verimi = (500*12 / 100_000) * 100 = 6.0%
        result = _calculate_investment_metrics(100_000, 500)
        assert result.kira_verimi == 6.0

    def test_valid_amortisman_calculation(self) -> None:
        """S6-TC-005: Yatirim metrikleri — gecerli hesaplama, amortisman_yil (P1)."""
        # avg_sale=100_000, avg_rent=500
        # amortisman = 100_000 / (500*12) = 16.666... → 16.7
        result = _calculate_investment_metrics(100_000, 500)
        assert result.amortisman_yil == 16.7

    def test_zero_sale_price_returns_empty(self) -> None:
        """S6-TC-004: Satis fiyati sifir → bos metrik donmeli (P2)."""
        result = _calculate_investment_metrics(0, 500)
        assert result.kira_verimi is None
        assert result.amortisman_yil is None

    def test_zero_rent_price_returns_empty(self) -> None:
        """S6-TC-004: Kira fiyati sifir → bos metrik donmeli (P2)."""
        result = _calculate_investment_metrics(100_000, 0)
        assert result.kira_verimi is None
        assert result.amortisman_yil is None

    def test_none_sale_returns_empty(self) -> None:
        """S6-TC-004: Satis fiyati None → bos metrik donmeli (P2)."""
        result = _calculate_investment_metrics(None, 500)
        assert result.kira_verimi is None
        assert result.amortisman_yil is None

    def test_none_rent_returns_empty(self) -> None:
        """S6-TC-004: Kira fiyati None → bos metrik donmeli (P2)."""
        result = _calculate_investment_metrics(100_000, None)
        assert result.kira_verimi is None
        assert result.amortisman_yil is None

    def test_realistic_kadikoy_metrics(self) -> None:
        """S6-TC-005: Gercekci Kadikoy m2 fiyatlariyla yatirim metrikleri (P1)."""
        # Kadikoy: ortalama m2 satis 80_000 TL, m2 kira 300 TL
        result = _calculate_investment_metrics(80_000, 300)

        # kira_verimi = (300*12 / 80_000) * 100 = 4.5%
        assert result.kira_verimi == 4.5
        # amortisman = 80_000 / (300*12) = 22.222... → 22.2
        assert result.amortisman_yil == 22.2


# ================================================================
# 4. Public Paths Testleri (tenant middleware)
# ================================================================


class TestAreaPublicPaths:
    """PUBLIC_PATHS ve PUBLIC_PATH_PREFIXES — area endpoint'lerinin auth gerekliligi."""

    def test_health_in_public_paths(self) -> None:
        """S6-TC-001: /health endpoint'i public olmali (P1)."""
        assert "/health" in PUBLIC_PATHS

    def test_area_endpoints_not_public(self) -> None:
        """S6-TC-002: Bolge detay endpoint'leri public olmamali — JWT gerekli (P1)."""
        # /api/v1/areas/* endpoint'leri public path'lerde olmamali
        area_paths = [p for p in PUBLIC_PATHS if "/areas" in p]
        assert len(area_paths) == 0, "Area endpoint'leri PUBLIC_PATHS'te olmamali"

    def test_area_prefix_not_in_public_prefixes(self) -> None:
        """S6-TC-003: /api/v1/areas prefix'i PUBLIC_PATH_PREFIXES'te olmamali (P1)."""
        for prefix in PUBLIC_PATH_PREFIXES:
            assert not prefix.startswith("/api/v1/areas"), (
                f"Area prefix '{prefix}' public olmamali"
            )

    def test_earthquake_endpoints_not_public(self) -> None:
        """S6-TC-017: Deprem/harita endpoint'leri public olmamali — JWT gerekli (P1)."""
        earthquake_paths = [p for p in PUBLIC_PATHS if "/earthquake" in p]
        assert len(earthquake_paths) == 0, (
            "Earthquake endpoint'leri PUBLIC_PATHS'te olmamali"
        )

    def test_webhook_prefix_is_public(self) -> None:
        """S6-TC-010: Webhook prefix'i public olmali (dis servis erisimi) (P1)."""
        assert any(
            prefix.startswith("/webhooks/") for prefix in PUBLIC_PATH_PREFIXES
        ), "/webhooks/ prefix'i PUBLIC_PATH_PREFIXES'te olmali"
