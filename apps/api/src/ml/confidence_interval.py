"""
Guven Araligi Hesaplama Modulu — Quantile Regression

LightGBM quantile objective ile egitilmis q=0.10 ve q=0.90 modelleri
kullanarak %80 guven araligi hesaplar.

Kullanim:
    from src.ml.confidence_interval import ConfidencePredictor

    predictor = ConfidencePredictor()
    predictor.load("src/ml/models/v1/")

    result = predictor.predict_with_confidence(features_df)
    # -> {"predicted": 5_000_000, "low": 4_200_000, "high": 5_800_000, "confidence_level": 0.80}
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import lightgbm as lgb
    import numpy as np
    import pandas as pd


class ConfidencePredictor:
    """Quantile regression tabanli guven araligi hesaplayici.

    3 model kullanir:
      - main_model: Ana regression modeli (nokta tahmini)
      - q10_model:  Alt sinir (q=0.10 quantile modeli)
      - q90_model:  Ust sinir (q=0.90 quantile modeli)

    Bu yaklasim sayesinde her mulk icin spesifik bir guven araligi
    hesaplanir (sabit margin degil, veriye dayali adaptive aralik).
    """

    def __init__(self) -> None:
        self.main_model: lgb.LGBMRegressor | None = None
        self.q10_model: lgb.LGBMRegressor | None = None
        self.q90_model: lgb.LGBMRegressor | None = None
        self._loaded = False

    def load(self, model_dir: str) -> None:
        """Model dosyalarini yukle.

        Args:
            model_dir: v1 model dizini (lgbm_model.joblib, lgbm_quantile_q10/q90.joblib icermeli)
        """
        import joblib

        p = Path(model_dir)

        self.main_model = joblib.load(p / "lgbm_model.joblib")
        self.q10_model = joblib.load(p / "lgbm_quantile_q10.joblib")
        self.q90_model = joblib.load(p / "lgbm_quantile_q90.joblib")
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def predict_with_confidence(
        self,
        features: pd.DataFrame,
    ) -> dict:
        """Tek bir mulk icin fiyat tahmini + guven araligi.

        Args:
            features: Feature engineering sonrasi hazirlanmis DataFrame (1 satir).

        Returns:
            {
                "predicted": float,      # Nokta tahmini (ana model)
                "low": float,            # Alt sinir (%10 quantile)
                "high": float,           # Ust sinir (%90 quantile)
                "confidence_level": 0.80 # Guven duzeyi
            }
        """
        if not self._loaded:
            raise RuntimeError(
                "Modeller yuklenmedi. Once load() cagirin."
            )

        # Nokta tahmini
        predicted = float(self.main_model.predict(features)[0])

        # Quantile tahminleri
        low = float(self.q10_model.predict(features)[0])
        high = float(self.q90_model.predict(features)[0])

        # Guvenlik: alt sinir > ust sinir olmasin
        if low > high:
            low, high = high, low

        # Guvenlik: negatif fiyat olmasin
        low = max(low, 0.0)
        high = max(high, predicted * 0.5)  # En az tahminin yarisi

        # Guvenlik: predicted aralik disinda kalmasin
        if predicted < low:
            predicted = low
        if predicted > high:
            predicted = high

        return {
            "predicted": round(predicted),
            "low": round(low),
            "high": round(high),
            "confidence_level": 0.80,
        }

    def predict_batch_with_confidence(
        self,
        features: pd.DataFrame,
    ) -> list[dict]:
        """Birden fazla mulk icin toplu tahmin + guven araligi.

        Args:
            features: Feature engineering sonrasi DataFrame (N satir).

        Returns:
            N elemanlı list[dict], her biri predict_with_confidence formati.
        """
        if not self._loaded:
            raise RuntimeError("Modeller yuklenmedi. Once load() cagirin.")

        predicted = self.main_model.predict(features)
        low_arr = self.q10_model.predict(features)
        high_arr = self.q90_model.predict(features)

        results = []
        for i in range(len(features)):
            p, lo, hi = float(predicted[i]), float(low_arr[i]), float(high_arr[i])

            # Guvenlik kontrolleri
            if lo > hi:
                lo, hi = hi, lo
            lo = max(lo, 0.0)
            hi = max(hi, p * 0.5)
            if p < lo:
                p = lo
            if p > hi:
                p = hi

            results.append({
                "predicted": round(p),
                "low": round(lo),
                "high": round(hi),
                "confidence_level": 0.80,
            })

        return results

    def evaluate_coverage(
        self,
        features: pd.DataFrame,
        y_true: np.ndarray | pd.Series,
    ) -> dict:
        """Guven araligi kapsam metrikleri hesapla.

        Args:
            features: Feature DataFrame.
            y_true: Gercek fiyatlar.

        Returns:
            Coverage metrikleri dict.
        """
        if not self._loaded:
            raise RuntimeError("Modeller yuklenmedi. Once load() cagirin.")

        import numpy as np

        y_true_arr = np.asarray(y_true)
        predicted = self.main_model.predict(features)
        low_arr = self.q10_model.predict(features)
        high_arr = self.q90_model.predict(features)

        # Swap kontrol
        mask_swap = low_arr > high_arr
        low_arr[mask_swap], high_arr[mask_swap] = high_arr[mask_swap], low_arr[mask_swap]

        # Negatif kontrol
        low_arr = np.maximum(low_arr, 0.0)

        # Coverage: gercek fiyat aralik icinde mi?
        in_interval = (y_true_arr >= low_arr) & (y_true_arr <= high_arr)
        coverage = float(np.mean(in_interval))

        # Aralik genisligi metrikleri
        widths = high_arr - low_arr
        relative_widths = widths / np.maximum(predicted, 1.0)

        return {
            "coverage": coverage,
            "target_coverage": 0.80,
            "coverage_met": coverage >= 0.80,
            "n_samples": len(y_true_arr),
            "n_in_interval": int(np.sum(in_interval)),
            "avg_interval_width": float(np.mean(widths)),
            "median_interval_width": float(np.median(widths)),
            "avg_relative_width": float(np.mean(relative_widths)),
            "median_relative_width": float(np.median(relative_widths)),
        }
