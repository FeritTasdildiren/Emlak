"""
Emlak Teknoloji Platformu - Building Earthquake Safety Score Service

Bina parametrelerine dayali deprem guvenlik skoru hesaplama algoritmasi.
TBDY 2018 (Turkiye Bina Deprem Yonetmeligi) referansli.

Kullanim:
    from src.modules.earthquake.building_score import BuildingScoreService
    from src.modules.earthquake.schemas import BuildingScoreRequest

    request = BuildingScoreRequest(building_age=10, floors=5, soil_class="ZC")
    result = BuildingScoreService.calculate_score(request)
"""

from __future__ import annotations

import structlog

from src.modules.earthquake.schemas import (
    BuildingScoreRequest,
    BuildingScoreResult,
    ConstructionType,
    RiskLevel,
    SoilClass,
)

logger = structlog.get_logger(__name__)

# =====================================================================
# Sabitler
# =====================================================================

DISCLAIMER = (
    "Bu skor bilgilendirme amaclidir. Resmi degerlendirme icin "
    "lisansli bir yapi muhendisine basvurunuz."
)

# Bina yasi risk faktorleri (TBDY 2018 yonetmelik gecmisi bazli)
# 2018+: Guncel TBDY 2018 uyumlu
# 2000-2017: 1998 deprem yonetmeligi doneminde insa
# 1975-1999: 1975 yonetmeligi doneminde insa
# <1975: Yonetmelik oncesi donem
_AGE_THRESHOLDS: list[tuple[int, float]] = [
    (0, 1.0),     # 2018+ (building_age hesabi: 2026 - yapi_yili)
    (9, 1.2),     # 2000-2017
    (27, 1.8),    # 1975-1999
    (51, 2.5),    # <1975
]

# Kat sayisi risk faktorleri
_FLOOR_THRESHOLDS: list[tuple[int, float]] = [
    (1, 1.0),     # 1-3 kat
    (4, 1.1),     # 4-7 kat
    (8, 1.3),     # 8-15 kat
    (16, 1.5),    # 15+ kat
]

# Zemin sinifi risk faktorleri (TBDY 2018 Tablo 2.1)
_SOIL_FACTORS: dict[SoilClass, float] = {
    SoilClass.ZA: 1.0,
    SoilClass.ZB: 1.1,
    SoilClass.ZC: 1.3,
    SoilClass.ZD: 1.7,
    SoilClass.ZE: 2.2,
}

# Yapi tipi risk faktorleri
_CONSTRUCTION_FACTORS: dict[ConstructionType, float] = {
    ConstructionType.BETONARME: 1.0,
    ConstructionType.CELIK: 0.9,
    ConstructionType.YIGMA: 1.5,
    ConstructionType.AHSAP: 1.8,
}

# Guclendirme risk azaltma katsayisi
_RETROFIT_REDUCTION = 0.30  # %30 risk azaltma

# Risk skoru -> seviye esik degerleri (ust sinir dahil degil)
_RISK_LEVEL_THRESHOLDS: list[tuple[float, RiskLevel, str]] = [
    (70, RiskLevel.LOW, "green"),
    (45, RiskLevel.MEDIUM, "yellow"),
    (25, RiskLevel.HIGH, "orange"),
    (0, RiskLevel.VERY_HIGH, "red"),
]


# =====================================================================
# BuildingScoreService
# =====================================================================


class BuildingScoreService:
    """
    Deprem bina guvenlik skoru hesaplama servisi.

    Tum metodlar statik ve pure — DB bagimliligi yoktur.
    Agirlikli faktor sistemi ile bina parametrelerini
    birlestirip 0-100 arasi guvenlik skoru uretir.
    """

    # ---------- Ana hesaplama ----------

    @staticmethod
    def calculate_score(request: BuildingScoreRequest) -> BuildingScoreResult:
        """
        Bina parametrelerine dayali deprem guvenlik skoru hesapla.

        Algoritma:
            1. Her parametre icin risk faktorunu belirle
            2. Faktorleri carparak toplam risk katsayisi hesapla
            3. Guclendirme varsa %30 azaltma uygula
            4. Risk katsayisini 0-100 guvenlik skoruna donustur
            5. Skor esiklerine gore risk seviyesi ve renk kodu belirle
            6. Risk faktorleri ve onerileri olustur

        Args:
            request: Bina parametreleri.

        Returns:
            Guvenlik skoru, risk seviyesi, oneriler ve yasal uyari.
        """
        # 1) Bireysel faktorleri hesapla
        age_factor = BuildingScoreService._get_age_factor(request.building_age)
        floor_factor = BuildingScoreService._get_floor_factor(request.floors)
        soil_factor = _SOIL_FACTORS[request.soil_class]

        construction_factor = (
            _CONSTRUCTION_FACTORS[request.construction_type]
            if request.construction_type is not None
            else 1.0
        )

        # 2) Toplam risk katsayisi (carpimsal)
        raw_risk = age_factor * floor_factor * soil_factor * construction_factor

        # 3) Guclendirme indirimi
        if request.has_retrofit is True:
            raw_risk *= 1.0 - _RETROFIT_REDUCTION

        # 4) Risk katsayisini 0-100 guvenlik skoruna donustur
        # Minimum risk = 0.9 (celik, 1-3 kat, ZA, yeni) → skor ~100
        # Maksimum risk = 2.5 * 1.5 * 2.2 * 1.8 = 14.85 → skor ~0
        # Lineer interpolasyon: score = max(0, min(100, 100 - (raw_risk - 1) * k))
        # k = 100 / (max_risk - 1) ≈ 7.2 → basitlestirmek icin k=7.0
        safety_score = max(0.0, min(100.0, 100.0 - (raw_risk - 1.0) * 7.0))
        safety_score = round(safety_score, 1)

        # 5) Risk seviyesi ve renk kodu
        risk_level, color_code = BuildingScoreService._classify_risk(safety_score)

        # 6) Risk faktorleri ve oneriler
        risk_factors = BuildingScoreService._build_risk_factors(request, raw_risk)
        recommendations = BuildingScoreService._build_recommendations(
            request, safety_score, risk_level
        )

        logger.info(
            "building_score_calculated",
            building_age=request.building_age,
            floors=request.floors,
            soil_class=request.soil_class.value,
            construction_type=(
                request.construction_type.value
                if request.construction_type
                else None
            ),
            has_retrofit=request.has_retrofit,
            raw_risk=round(raw_risk, 3),
            safety_score=safety_score,
            risk_level=risk_level.value,
        )

        return BuildingScoreResult(
            safety_score=safety_score,
            risk_level=risk_level,
            color_code=color_code,
            risk_factors=risk_factors,
            recommendations=recommendations,
            disclaimer=DISCLAIMER,
        )

    # ---------- Faktor hesaplamalari ----------

    @staticmethod
    def _get_age_factor(building_age: int) -> float:
        """Bina yasina gore risk faktorunu dondur."""
        # Esikler kucukten buyuge siralandi; son eslesen kazanir
        factor = _AGE_THRESHOLDS[-1][1]
        for threshold_age, threshold_factor in _AGE_THRESHOLDS:
            if building_age <= threshold_age:
                factor = threshold_factor
                break
        else:
            # building_age > son esik (51+) → en yuksek risk
            factor = _AGE_THRESHOLDS[-1][1]
        return factor

    @staticmethod
    def _get_floor_factor(floors: int) -> float:
        """Kat sayisina gore risk faktorunu dondur."""
        if floors <= 3:
            return 1.0
        if floors <= 7:
            return 1.1
        if floors <= 15:
            return 1.3
        return 1.5

    # ---------- Risk siniflandirma ----------

    @staticmethod
    def _classify_risk(safety_score: float) -> tuple[RiskLevel, str]:
        """Guvenlik skorunu risk seviyesi ve renk koduna donustur."""
        for threshold, level, color in _RISK_LEVEL_THRESHOLDS:
            if safety_score >= threshold:
                return level, color
        return RiskLevel.VERY_HIGH, "red"

    # ---------- Risk faktorleri ----------

    @staticmethod
    def _build_risk_factors(
        request: BuildingScoreRequest,
        raw_risk: float,
    ) -> list[str]:
        """Tespit edilen risk faktorlerini listele."""
        factors: list[str] = []

        # Bina yasi
        if request.building_age > 50:
            factors.append(
                "Bina 1975 oncesi yonetmeliksiz donemde insa edilmis"
            )
        elif request.building_age > 26:
            factors.append(
                "Bina 1975 yonetmeligi doneminde insa edilmis "
                "(guncel TBDY 2018 standartlarina uygun olmayabilir)"
            )
        elif request.building_age > 8:
            factors.append(
                "Bina 1998/2007 yonetmeligi doneminde insa edilmis"
            )

        # Kat sayisi
        if request.floors > 15:
            factors.append(
                f"{request.floors} katli yuksek bina — depremde salinti etkisi artar"
            )
        elif request.floors > 7:
            factors.append(
                f"{request.floors} katli orta-yuksek bina"
            )

        # Zemin sinifi
        if request.soil_class in (SoilClass.ZD, SoilClass.ZE):
            soil_desc = "yumusak" if request.soil_class == SoilClass.ZE else "zayif"
            factors.append(
                f"Zemin sinifi {request.soil_class.value} — {soil_desc} zemin, "
                "sivrilasma ve oturma riski"
            )
        elif request.soil_class == SoilClass.ZC:
            factors.append(
                f"Zemin sinifi {request.soil_class.value} — orta mukavemetli zemin"
            )

        # Yapi tipi
        if request.construction_type == ConstructionType.YIGMA:
            factors.append("Yigma yapi — depreme karsi dayanimi sinirli")
        elif request.construction_type == ConstructionType.AHSAP:
            factors.append("Ahsap yapi — yangin ve deprem riski bir arada")

        # Guclendirme durumu
        if request.has_retrofit is True:
            factors.append("Guclendirme yapilmis — risk %30 azaltildi")

        # Bilesik risk
        if raw_risk > 5.0:
            factors.append("Birden fazla yuksek risk faktoru bir arada")

        return factors

    # ---------- Oneriler ----------

    @staticmethod
    def _build_recommendations(
        request: BuildingScoreRequest,
        safety_score: float,
        risk_level: RiskLevel,
    ) -> list[str]:
        """Risk seviyesine ve parametrelere gore oneriler olustur."""
        recs: list[str] = []

        # Genel oneriler (risk seviyesine gore)
        if risk_level == RiskLevel.VERY_HIGH:
            recs.append(
                "Acil olarak lisansli bir yapi muhendisinden detayli "
                "degerlendirme yaptirin"
            )
            recs.append("Bina guclendirme veya yeniden yapi seceneklerini arastirin")
        elif risk_level == RiskLevel.HIGH:
            recs.append(
                "Yapi muhendisinden deprem dayanim raporu talep edin"
            )
        elif risk_level == RiskLevel.MEDIUM:
            recs.append(
                "Periyodik yapi kontrolu yaptirmaniz onerilir"
            )

        # Yas bazli oneriler
        if request.building_age > 50 and request.has_retrofit is not True:
            recs.append(
                "1975 oncesi binalarda guclendirme (retrofit) "
                "buyuk olcude risk azaltir"
            )
        elif request.building_age > 26 and request.has_retrofit is not True:
            recs.append(
                "Guncel TBDY 2018 standartlarina uygunluk kontrolu yaptirin"
            )

        # Zemin bazli oneriler
        if request.soil_class in (SoilClass.ZD, SoilClass.ZE):
            recs.append(
                "Zemin etut raporu (jeolojik/jeoteknik) kontrol edin"
            )

        # Yapi tipi bazli oneriler
        if request.construction_type == ConstructionType.YIGMA:
            recs.append(
                "Yigma yapilarda celik karkas guclendirme yontemi etkilidir"
            )
        elif request.construction_type == ConstructionType.AHSAP:
            recs.append(
                "Ahsap yapilarda baglanti noktalari ve temel kontrolu onerilir"
            )

        # Deprem sigortasi (DASK) onerisi
        if safety_score < 70:
            recs.append(
                "Zorunlu deprem sigortasi (DASK) policenizin guncel "
                "oldugundan emin olun"
            )

        return recs
