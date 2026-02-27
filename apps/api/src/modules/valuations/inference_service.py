"""
Emlak Teknoloji Platformu - Inference Service v1

ML model ile gercek zamanli fiyat tahmini.
Singleton pattern: model uygulama yasam suresi boyunca bir kez yuklenir.

v1 yenilikler:
  - Quantile regression tabanli %80 guven araligi (confidence_low, confidence_high)
  - Model version fallback: v1 → v0 otomatik gecis
  - 3 model dosyasi: main + quantile_q10 + quantile_q90
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.ml.confidence_interval import ConfidencePredictor
from src.models.prediction_log import PredictionLog

logger = structlog.get_logger()

# Model dizinleri (cwd: apps/api/ varsayimi)
MODEL_DIR_V1 = "src/ml/models/v1/"
MODEL_DIR_V0 = "src/ml/models/v0/"
MODEL_NAME = "lgbm_konut_fiyat"


class InferenceService:
    """
    ML model inference servisi.

    Singleton pattern ile model bellekte bir kez yuklenir.
    Thread-safe initialization icin threading.Lock kullanilir.

    v1: Quantile regression ile guven araligi hesaplama.
    v0 fallback: v1 modeli bulunamazsa v0'a duser.
    """

    _instance: InferenceService | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        from src.ml.feature_engineering import FeatureEngineer
        from src.ml.trainer import ModelTrainer

        self.trainer = ModelTrainer(FeatureEngineer())
        self.confidence_predictor: ConfidencePredictor | None = None
        self._model_loaded = False
        self._model_version = "unknown"
        self._has_confidence = False

    @classmethod
    def get_instance(cls) -> InferenceService:
        """Thread-safe singleton erisimi."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = cls()
                    instance._load_model()
                    cls._instance = instance
        return cls._instance

    def _load_model(self) -> None:
        """Model dosyalarini diskten yukle. v1 → v0 fallback."""

        # --- v1 deneme ---
        v1_path = Path(MODEL_DIR_V1)
        if (v1_path / "lgbm_model.joblib").exists():
            try:
                self.trainer.load_model(MODEL_DIR_V1)
                self._model_version = "v1"
                self._model_loaded = True

                # Quantile modelleri yukle
                from src.ml.confidence_interval import ConfidencePredictor

                q10_path = v1_path / "lgbm_quantile_q10.joblib"
                q90_path = v1_path / "lgbm_quantile_q90.joblib"
                if q10_path.exists() and q90_path.exists():
                    self.confidence_predictor = ConfidencePredictor()
                    self.confidence_predictor.load(MODEL_DIR_V1)
                    self._has_confidence = True
                    logger.info(
                        "inference_confidence_models_loaded",
                        model_dir=MODEL_DIR_V1,
                    )

                logger.info(
                    "inference_model_loaded",
                    model_dir=MODEL_DIR_V1,
                    model_name=MODEL_NAME,
                    model_version=self._model_version,
                )
                return

            except Exception as exc:
                logger.warning(
                    "inference_v1_load_failed_fallback_to_v0",
                    error=str(exc),
                    model_dir=MODEL_DIR_V1,
                )

        # --- v0 fallback ---
        try:
            self.trainer.load_model(MODEL_DIR_V0)
            self._model_version = "v0"
            self._model_loaded = True
            self._has_confidence = False
            self.confidence_predictor = None

            logger.info(
                "inference_model_loaded",
                model_dir=MODEL_DIR_V0,
                model_name=MODEL_NAME,
                model_version=self._model_version,
                note="v0 fallback",
            )

        except Exception as exc:
            logger.error(
                "inference_model_load_failed",
                model_dir_v1=MODEL_DIR_V1,
                model_dir_v0=MODEL_DIR_V0,
                error=str(exc),
                exc_info=True,
            )
            raise RuntimeError(
                f"ML model yuklenemedi (v1: {MODEL_DIR_V1}, v0: {MODEL_DIR_V0}): {exc}"
            ) from exc

    def predict_quick(self, input_data: dict) -> dict:
        """
        Hafif fiyat tahmini — DB kaydi gerektirmez.

        Telegram bot gibi session'siz ortamlar icin tasarlanmistir.
        Model tahmini + guven araligi hesaplar, PredictionLog KAYDETMEZ.

        Args:
            input_data: Mulk ozellikleri (district, net_sqm, vb.)

        Returns:
            estimated_price, confidence_low, confidence_high, confidence_level
        """
        if not self._model_loaded:
            raise RuntimeError("Model yuklenmedi. Inference servisi hazir degil.")

        result = self.trainer.predict(input_data)
        estimated_price = result["estimated_price"]

        if self._has_confidence and self.confidence_predictor is not None:
            import pandas as pd

            features_df = self.trainer.fe.transform(pd.DataFrame([input_data]))
            ci_result = self.confidence_predictor.predict_with_confidence(features_df)
            confidence_low = ci_result["low"]
            confidence_high = ci_result["high"]
            confidence_level = ci_result["confidence_level"]
        else:
            confidence = result["confidence"]
            margin = (5 - 4 * confidence) / 12
            confidence_low = round(estimated_price * (1 - margin))
            confidence_high = round(estimated_price * (1 + margin))
            confidence_level = 0.80

        return {
            "estimated_price": estimated_price,
            "confidence_low": confidence_low,
            "confidence_high": confidence_high,
            "confidence_level": confidence_level,
        }

    async def predict(
        self,
        input_data: dict,
        session: AsyncSession,
        office_id: str,
    ) -> dict:
        """
        Fiyat tahmini yap ve PredictionLog'a kaydet.

        Args:
            input_data: Mulk ozellikleri (district, net_sqm, vb.)
            session: Async DB session (ayni transaction icerisinde flush yapilir)
            office_id: Tenant office ID

        Returns:
            Tahmin sonucu: estimated_price, min/max, confidence, latency vb.
            v1'de ek: confidence_low, confidence_high, confidence_level
        """
        if not self._model_loaded:
            raise RuntimeError("Model yuklenmedi. Inference servisi hazir degil.")

        # 1. Zamanlama baslat
        start_time = time.perf_counter()

        # 2. Model tahmini
        result = self.trainer.predict(input_data)
        estimated_price = result["estimated_price"]

        # 3. Guven araligi (v1 quantile, v0 margin-based fallback)
        if self._has_confidence and self.confidence_predictor is not None:
            # v1: Quantile regression ile data-driven guven araligi
            import pandas as pd

            features_df = self.trainer.fe.transform(pd.DataFrame([input_data]))
            ci_result = self.confidence_predictor.predict_with_confidence(features_df)

            confidence_low = ci_result["low"]
            confidence_high = ci_result["high"]
            confidence_level = ci_result["confidence_level"]
            # Adaptive confidence skoru: aralik ne kadar darsa, o kadar guvenliyiz
            interval_ratio = (confidence_high - confidence_low) / max(estimated_price, 1)
            confidence = round(max(0.5, min(0.99, 1.0 - interval_ratio)), 2)
        else:
            # v0 fallback: sabit margin-based aralik
            confidence = result["confidence"]
            margin = (5 - 4 * confidence) / 12
            confidence_low = round(estimated_price * (1 - margin))
            confidence_high = round(estimated_price * (1 + margin))
            confidence_level = 0.80

        # min/max backward compatibility (v0 API uyumu)
        min_price = confidence_low
        max_price = confidence_high

        # 4. m2 birim fiyat
        net_sqm = input_data.get("net_sqm", 1)
        price_per_sqm = int(estimated_price / max(net_sqm, 1))

        # 5. Latency hesapla
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # 6. Cikti verisi
        output_data = {
            "estimated_price": estimated_price,
            "min_price": min_price,
            "max_price": max_price,
            "confidence_low": confidence_low,
            "confidence_high": confidence_high,
            "confidence_level": confidence_level,
            "price_per_sqm": price_per_sqm,
        }

        # 7. PredictionLog'a kaydet (ayni transaction)
        prediction_log = PredictionLog(
            office_id=office_id,
            model_name=MODEL_NAME,
            model_version=self._model_version,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence,
            latency_ms=latency_ms,
        )
        session.add(prediction_log)
        await session.flush()

        logger.info(
            "inference_prediction_completed",
            prediction_id=str(prediction_log.id),
            estimated_price=estimated_price,
            confidence=confidence,
            confidence_low=confidence_low,
            confidence_high=confidence_high,
            latency_ms=latency_ms,
            model_version=self._model_version,
            office_id=office_id,
        )

        # 8. Sonuc don
        return {
            "estimated_price": estimated_price,
            "min_price": min_price,
            "max_price": max_price,
            "confidence_low": confidence_low,
            "confidence_high": confidence_high,
            "confidence_level": confidence_level,
            "confidence": confidence,
            "price_per_sqm": price_per_sqm,
            "latency_ms": latency_ms,
            "model_version": self._model_version,
            "prediction_id": str(prediction_log.id),
        }
