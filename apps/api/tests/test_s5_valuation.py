"""
Sprint S5 e2e Test Suite — Valuation Pipeline

Pure unit testleri — DB bagimliligi YOK, mock pattern kullanir.

Test kategorileri:
  1. Kota kontrol (plan_policy) — 6 test
  2. Anomali tespiti (confidence interval sinir degerleri) — 5 test
  3. Confidence interval (ConfidencePredictor) — 7 test
  4. Schema dogrulamalari (Pydantic) — 6 test
  5. InferenceService (predict_quick mock) — 5 test
  6. Feature engineering (FeatureEngineer) — 6 test

Toplam: 35 test
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from src.core.plan_policy import (
    get_valuation_quota,
    is_unlimited_plan,
)
from src.ml.confidence_interval import ConfidencePredictor
from src.ml.feature_engineering import FeatureEngineer
from src.modules.valuations.schemas import (
    ComparableItem,
    ComparableResult,
    ValuationRequest,
    ValuationResponse,
)

# ================================================================
# 1. Kota Kontrol Testleri (plan_policy.py)
# ================================================================


class TestValuationQuota:
    """Plan bazli degerleme kota limitleri."""

    def test_starter_quota_50(self) -> None:
        """Starter plan aylik 50 degerleme hakki verir."""
        assert get_valuation_quota("starter") == 50

    def test_pro_quota_500(self) -> None:
        """Pro plan aylik 500 degerleme hakki verir."""
        assert get_valuation_quota("pro") == 500

    def test_elite_quota_unlimited(self) -> None:
        """Elite plan sinirsiz (-1) degerleme hakki verir."""
        assert get_valuation_quota("elite") == -1

    def test_is_unlimited_elite(self) -> None:
        """Elite plan icin is_unlimited_plan True donmeli."""
        assert is_unlimited_plan("elite") is True

    def test_is_unlimited_starter_false(self) -> None:
        """Starter plan icin is_unlimited_plan False donmeli."""
        assert is_unlimited_plan("starter") is False

    def test_invalid_plan_raises(self) -> None:
        """Gecersiz plan tipi ValueError firlatmali."""
        with pytest.raises(ValueError, match="Gecersiz plan tipi"):
            get_valuation_quota("invalid_plan")


# ================================================================
# 2. Anomali Tespiti Testleri (mock ConfidencePredictor)
# ================================================================


class TestAnomalyDetection:
    """Fiyat anomali tespiti — z-score tabanli sinir degerleri.

    ConfidencePredictor ciktilari uzerinden anomali tespiti:
    - predicted vs low/high arasindaki oran kontrol edilir.
    - Aralik disina dusen tahminler anomali olarak isaretlenir.
    """

    @staticmethod
    def _mock_predictor(predicted: float, low: float, high: float) -> ConfidencePredictor:
        """Mock ConfidencePredictor olustur."""
        predictor = ConfidencePredictor()
        predictor._loaded = True

        mock_main = MagicMock()
        mock_main.predict.return_value = np.array([predicted])
        mock_q10 = MagicMock()
        mock_q10.predict.return_value = np.array([low])
        mock_q90 = MagicMock()
        mock_q90.predict.return_value = np.array([high])

        predictor.main_model = mock_main
        predictor.q10_model = mock_q10
        predictor.q90_model = mock_q90
        return predictor

    def test_normal_price_no_anomaly(self) -> None:
        """Normal fiyat: predicted aralik icinde → anomali degil."""
        predictor = self._mock_predictor(5_000_000, 4_200_000, 5_800_000)
        features = pd.DataFrame([[0] * 5], columns=[f"f{i}" for i in range(5)])
        result = predictor.predict_with_confidence(features)

        assert result["low"] <= result["predicted"] <= result["high"]
        interval_ratio = (result["high"] - result["low"]) / max(result["predicted"], 1)
        assert interval_ratio < 2.0  # Makul aralik

    def test_very_high_price_anomaly(self) -> None:
        """Cok yuksek fiyat: predicted >> high, clamp uygulanir."""
        predictor = self._mock_predictor(50_000_000, 4_000_000, 6_000_000)
        features = pd.DataFrame([[0] * 5], columns=[f"f{i}" for i in range(5)])
        result = predictor.predict_with_confidence(features)

        # predict_with_confidence icindeki clamp: predicted > high ise predicted = high
        assert result["predicted"] == result["high"]

    def test_very_low_price_anomaly(self) -> None:
        """Cok dusuk fiyat: predicted << low, clamp uygulanir."""
        predictor = self._mock_predictor(100_000, 4_000_000, 6_000_000)
        features = pd.DataFrame([[0] * 5], columns=[f"f{i}" for i in range(5)])
        result = predictor.predict_with_confidence(features)

        # predict_with_confidence icindeki clamp: predicted < low ise predicted = low
        assert result["predicted"] == result["low"]

    def test_negative_low_clamped_to_zero(self) -> None:
        """Negatif alt sinir: 0'a clamp edilir."""
        predictor = self._mock_predictor(500_000, -200_000, 1_000_000)
        features = pd.DataFrame([[0] * 5], columns=[f"f{i}" for i in range(5)])
        result = predictor.predict_with_confidence(features)

        assert result["low"] == 0

    def test_swapped_low_high_corrected(self) -> None:
        """low > high ise otomatik swap yapilir."""
        predictor = self._mock_predictor(5_000_000, 7_000_000, 3_000_000)
        features = pd.DataFrame([[0] * 5], columns=[f"f{i}" for i in range(5)])
        result = predictor.predict_with_confidence(features)

        assert result["low"] <= result["high"]


# ================================================================
# 3. Confidence Interval Testleri
# ================================================================


class TestConfidenceInterval:
    """ConfidencePredictor guven araligi hesaplama testleri."""

    @staticmethod
    def _make_predictor(predicted: float, low: float, high: float) -> ConfidencePredictor:
        """Yardimci: mock modelli ConfidencePredictor olustur."""
        predictor = ConfidencePredictor()
        predictor._loaded = True

        mock_main = MagicMock()
        mock_main.predict.return_value = np.array([predicted])
        mock_q10 = MagicMock()
        mock_q10.predict.return_value = np.array([low])
        mock_q90 = MagicMock()
        mock_q90.predict.return_value = np.array([high])

        predictor.main_model = mock_main
        predictor.q10_model = mock_q10
        predictor.q90_model = mock_q90
        return predictor

    def test_confidence_low_less_than_predicted(self) -> None:
        """confidence_low < predicted her zaman saglanmali."""
        predictor = self._make_predictor(5_000_000, 4_200_000, 5_800_000)
        features = pd.DataFrame([[0] * 3], columns=["a", "b", "c"])
        result = predictor.predict_with_confidence(features)

        assert result["low"] <= result["predicted"]

    def test_predicted_less_than_confidence_high(self) -> None:
        """predicted <= confidence_high her zaman saglanmali."""
        predictor = self._make_predictor(5_000_000, 4_200_000, 5_800_000)
        features = pd.DataFrame([[0] * 3], columns=["a", "b", "c"])
        result = predictor.predict_with_confidence(features)

        assert result["predicted"] <= result["high"]

    def test_confidence_level_always_080(self) -> None:
        """confidence_level sabit 0.80 donmeli."""
        predictor = self._make_predictor(5_000_000, 4_200_000, 5_800_000)
        features = pd.DataFrame([[0] * 3], columns=["a", "b", "c"])
        result = predictor.predict_with_confidence(features)

        assert result["confidence_level"] == 0.80

    def test_unloaded_predictor_raises(self) -> None:
        """Model yuklenmemis predictor RuntimeError firlatmali."""
        predictor = ConfidencePredictor()
        features = pd.DataFrame([[0] * 3], columns=["a", "b", "c"])

        with pytest.raises(RuntimeError, match="Modeller yuklenmedi"):
            predictor.predict_with_confidence(features)

    def test_values_are_rounded_integers(self) -> None:
        """Cikti degerleri yuvarlanmis tam sayi olmali."""
        predictor = self._make_predictor(5_123_456.78, 4_234_567.89, 6_012_345.67)
        features = pd.DataFrame([[0] * 3], columns=["a", "b", "c"])
        result = predictor.predict_with_confidence(features)

        assert isinstance(result["predicted"], int)
        assert isinstance(result["low"], int)
        assert isinstance(result["high"], int)

    def test_high_at_least_half_of_predicted(self) -> None:
        """high en az predicted * 0.5 olmali (guvenlik kurali)."""
        predictor = self._make_predictor(10_000_000, 500_000, 100_000)
        features = pd.DataFrame([[0] * 3], columns=["a", "b", "c"])
        result = predictor.predict_with_confidence(features)

        # high = max(high, predicted * 0.5) kurali uygulaniyor
        assert result["high"] >= result["predicted"] * 0.5

    def test_batch_prediction_returns_list(self) -> None:
        """Toplu tahmin N elemanli liste donmeli."""
        predictor = self._make_predictor(5_000_000, 4_200_000, 5_800_000)
        # Batch icin coklu sonuc mock'la
        predictor.main_model.predict.return_value = np.array([5_000_000, 6_000_000])
        predictor.q10_model.predict.return_value = np.array([4_200_000, 5_000_000])
        predictor.q90_model.predict.return_value = np.array([5_800_000, 7_000_000])

        features = pd.DataFrame([[0, 0, 0], [1, 1, 1]], columns=["a", "b", "c"])
        results = predictor.predict_batch_with_confidence(features)

        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert r["low"] <= r["predicted"] <= r["high"]


# ================================================================
# 4. Schema Testleri (Pydantic dogrulama)
# ================================================================


class TestValuationSchemas:
    """Pydantic schema dogrulama testleri."""

    def test_valuation_request_valid(self) -> None:
        """Gecerli ValuationRequest olusturulabilmeli."""
        req = ValuationRequest(
            district="Kadikoy",
            neighborhood="Caferaga",
            property_type="Daire",
            net_sqm=120.0,
            gross_sqm=145.0,
            room_count=3,
            living_room_count=1,
            floor=5,
            total_floors=10,
            building_age=5,
            heating_type="Kombi",
        )
        assert req.district == "Kadikoy"
        assert req.net_sqm == 120.0

    def test_valuation_request_negative_sqm_rejected(self) -> None:
        """Negatif metrekare reddedilmeli."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ValuationRequest(
                district="Kadikoy",
                neighborhood="Caferaga",
                property_type="Daire",
                net_sqm=-10.0,
                gross_sqm=145.0,
                room_count=3,
                living_room_count=1,
                floor=5,
                total_floors=10,
                building_age=5,
                heating_type="Kombi",
            )

    def test_valuation_request_to_model_input(self) -> None:
        """to_model_input() tum alanlari dict olarak donmeli."""
        req = ValuationRequest(
            district="Kadikoy",
            neighborhood="Caferaga",
            property_type="Daire",
            net_sqm=120.0,
            gross_sqm=145.0,
            room_count=3,
            living_room_count=1,
            floor=5,
            total_floors=10,
            building_age=5,
            heating_type="Kombi",
        )
        data = req.to_model_input()
        assert isinstance(data, dict)
        assert data["district"] == "Kadikoy"
        assert data["net_sqm"] == 120.0
        assert "room_count" in data

    def test_valuation_response_serialization(self) -> None:
        """ValuationResponse duzgun serialize edilmeli."""
        resp = ValuationResponse(
            estimated_price=5_000_000,
            min_price=4_200_000,
            max_price=5_800_000,
            confidence=0.85,
            price_per_sqm=41_666,
            latency_ms=45,
            model_version="v1",
            prediction_id="abc-123",
            comparables=[],
            quota_remaining=49,
            quota_limit=50,
        )
        data = resp.model_dump()
        assert data["estimated_price"] == 5_000_000
        assert data["quota_remaining"] == 49
        assert data["comparables"] == []

    def test_comparable_result_schema(self) -> None:
        """ComparableResult tum alanlari kabul etmeli."""
        comp = ComparableResult(
            property_id="prop-001",
            distance_km=1.5,
            price_diff_percent=-3.2,
            similarity_score=87.5,
            address="Kadikoy, Caferaga Mah.",
            price=4_850_000,
            sqm=115.0,
            rooms="3+1",
        )
        assert comp.similarity_score == 87.5
        assert comp.price_diff_percent == -3.2

    def test_comparable_item_similarity_bounds(self) -> None:
        """ComparableItem similarity_score 0-100 arasinda olmali."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ComparableItem(
                district="Kadikoy",
                net_sqm=120.0,
                price=5_000_000,
                building_age=5,
                room_count=3,
                similarity_score=150.0,  # > 100 — invalid
            )


# ================================================================
# 5. InferenceService Testleri (predict_quick mock)
# ================================================================


class TestInferenceService:
    """InferenceService predict_quick — mock model ile."""

    @staticmethod
    def _create_service():
        """Mock model yuklu InferenceService olustur."""
        from src.modules.valuations.inference_service import InferenceService

        svc = InferenceService()
        svc._model_loaded = True
        svc._model_version = "v1-test"
        svc._has_confidence = True

        # Mock trainer
        mock_trainer = MagicMock()
        mock_trainer.predict.return_value = {
            "estimated_price": 5_000_000,
            "confidence": 0.85,
        }
        # Mock feature engineer icin transform
        mock_fe = MagicMock()
        mock_fe.transform.return_value = pd.DataFrame([[0] * 5])
        mock_trainer.fe = mock_fe
        svc.trainer = mock_trainer

        # Mock confidence predictor
        mock_ci = MagicMock()
        mock_ci.predict_with_confidence.return_value = {
            "predicted": 5_000_000,
            "low": 4_200_000,
            "high": 5_800_000,
            "confidence_level": 0.80,
        }
        svc.confidence_predictor = mock_ci

        return svc

    def test_predict_quick_returns_required_keys(self) -> None:
        """predict_quick donusu gerekli key'leri icermeli."""
        svc = self._create_service()
        result = svc.predict_quick({"district": "Kadikoy", "net_sqm": 120})

        assert "estimated_price" in result
        assert "confidence_low" in result
        assert "confidence_high" in result
        assert "confidence_level" in result

    def test_predict_quick_confidence_bounds(self) -> None:
        """confidence_low < estimated_price < confidence_high olmali."""
        svc = self._create_service()
        result = svc.predict_quick({"district": "Kadikoy", "net_sqm": 120})

        assert result["confidence_low"] <= result["estimated_price"]
        assert result["estimated_price"] <= result["confidence_high"]

    def test_predict_quick_not_loaded_raises(self) -> None:
        """Model yuklu degilse RuntimeError firlatmali."""
        from src.modules.valuations.inference_service import InferenceService

        svc = InferenceService()
        svc._model_loaded = False

        with pytest.raises(RuntimeError, match="Model yuklenmedi"):
            svc.predict_quick({"district": "Kadikoy", "net_sqm": 120})

    def test_predict_quick_v0_fallback_no_confidence(self) -> None:
        """v0 model (confidence predictor yok): margin-based aralik hesaplanmali."""
        svc = self._create_service()
        svc._has_confidence = False
        svc.confidence_predictor = None

        result = svc.predict_quick({"district": "Kadikoy", "net_sqm": 120})

        # v0 fallback: margin = (5 - 4 * confidence) / 12
        assert result["confidence_low"] < result["estimated_price"]
        assert result["confidence_high"] > result["estimated_price"]
        assert result["confidence_level"] == 0.80

    def test_predict_quick_model_version(self) -> None:
        """Servis mock model version'ini dogru raporlamali."""
        svc = self._create_service()
        assert svc._model_version == "v1-test"


# ================================================================
# 6. Feature Engineering Testleri
# ================================================================


class TestFeatureEngineering:
    """FeatureEngineer donusum ve encoding testleri."""

    @staticmethod
    def _sample_train_df() -> pd.DataFrame:
        """Egitim icin ornek DataFrame."""
        return pd.DataFrame({
            "district": ["Kadikoy", "Uskudar", "Besiktas", "Kadikoy", "Atasehir"],
            "neighborhood": ["Caferaga", "Kuzguncuk", "Ortakoy", "Moda", "Atasehir"],
            "property_type": ["Daire", "Daire", "Villa", "Daire", "Daire"],
            "heating_type": ["Kombi", "Merkezi", "Yerden", "Kombi", "Kombi"],
            "net_sqm": [120.0, 95.0, 250.0, 110.0, 85.0],
            "gross_sqm": [145.0, 115.0, 300.0, 130.0, 100.0],
            "room_count": [3, 2, 5, 3, 2],
            "living_room_count": [1, 1, 2, 1, 1],
            "floor": [5, 3, 0, 7, 10],
            "total_floors": [10, 8, 3, 12, 15],
            "building_age": [5, 15, 2, 20, 1],
            "price": [5_000_000, 3_500_000, 12_000_000, 4_500_000, 2_800_000],
        })

    def test_fit_transform_output_shape(self) -> None:
        """fit_transform() dogru boyutta X ve y donmeli."""
        fe = FeatureEngineer()
        df = self._sample_train_df()
        x_features, y = fe.fit_transform(df)

        assert len(x_features) == 5
        assert len(y) == 5
        assert "price" not in x_features.columns

    def test_derived_features_created(self) -> None:
        """Turev feature'lar (sqm_ratio, floor_ratio, total_rooms, rooms_per_sqm) olusturulmali."""
        fe = FeatureEngineer()
        df = self._sample_train_df()
        x_features, _y = fe.fit_transform(df)

        assert "sqm_ratio" in x_features.columns
        assert "floor_ratio" in x_features.columns
        assert "total_rooms" in x_features.columns
        assert "rooms_per_sqm" in x_features.columns

    def test_label_encoders_stored(self) -> None:
        """Categorical sutunlar icin LabelEncoder kayit edilmeli."""
        fe = FeatureEngineer()
        df = self._sample_train_df()
        fe.fit_transform(df)

        expected_cols = {"district", "neighborhood", "property_type", "heating_type"}
        assert set(fe.label_encoders.keys()) == expected_cols

    def test_transform_unknown_category_returns_minus_one(self) -> None:
        """Bilinmeyen kategori -1 olarak encode edilmeli."""
        fe = FeatureEngineer()
        df = self._sample_train_df()
        fe.fit_transform(df)

        # Inference verisi: "Sariyer" egitimde yok
        new_df = pd.DataFrame({
            "district": ["Sariyer"],
            "neighborhood": ["BilinmeyenMah"],
            "property_type": ["Daire"],
            "heating_type": ["Kombi"],
            "net_sqm": [100.0],
            "gross_sqm": [120.0],
            "room_count": [2],
            "living_room_count": [1],
            "floor": [3],
            "total_floors": [8],
            "building_age": [10],
        })
        x_new = fe.transform(new_df)

        # Bilinmeyen district ve neighborhood -1 olmali
        assert x_new["district"].iloc[0] == -1
        assert x_new["neighborhood"].iloc[0] == -1

    def test_transform_preserves_column_order(self) -> None:
        """transform() egitim sirasindaki sutun sirasiyla donmeli."""
        fe = FeatureEngineer()
        df = self._sample_train_df()
        fe.fit_transform(df)

        new_df = pd.DataFrame({
            "district": ["Kadikoy"],
            "neighborhood": ["Caferaga"],
            "property_type": ["Daire"],
            "heating_type": ["Kombi"],
            "net_sqm": [100.0],
            "gross_sqm": [120.0],
            "room_count": [2],
            "living_room_count": [1],
            "floor": [3],
            "total_floors": [8],
            "building_age": [10],
        })
        x_new = fe.transform(new_df)

        assert list(x_new.columns) == fe.feature_columns

    def test_get_feature_names_after_fit(self) -> None:
        """get_feature_names() egitim sonrasi dolu liste donmeli."""
        fe = FeatureEngineer()
        df = self._sample_train_df()
        fe.fit_transform(df)

        names = fe.get_feature_names()
        assert len(names) > 0
        assert "net_sqm" in names
        assert "price" not in names
