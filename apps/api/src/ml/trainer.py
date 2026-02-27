"""
LightGBM Model Trainer - Istanbul Konut Fiyat Tahmini

Egitim, degerlendirme, kaydetme ve tahmin islemleri.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import lightgbm as lgb

from src.ml.feature_engineering import FeatureEngineer  # noqa: TC001 — runtime


class ModelTrainer:
    """LightGBM regresyon modeli egitim ve tahmin sinifi."""

    def __init__(self, feature_engineer: FeatureEngineer) -> None:
        self.fe = feature_engineer
        self.model: lgb.LGBMRegressor | None = None

    def train(self, csv_path: str) -> dict:
        """CSV verisinden model egit ve metrikleri don.

        Args:
            csv_path: Egitim CSV dosyasinin yolu.

        Returns:
            Egitim metrikleri ve feature importance iceren dict.
        """
        import lightgbm as lgb
        import numpy as np
        import pandas as pd
        from sklearn.metrics import (
            mean_absolute_error,
            mean_absolute_percentage_error,
            mean_squared_error,
            r2_score,
        )
        from sklearn.model_selection import cross_val_score, train_test_split

        # 1. CSV oku
        df = pd.read_csv(csv_path, encoding="utf-8")
        print(f"[INFO] Veri yuklendi: {len(df)} kayit, {len(df.columns)} sutun")

        # 2. Feature engineering
        X, y = self.fe.fit_transform(df)
        print(f"[INFO] Feature sayisi: {len(self.fe.get_feature_names())}")

        # 3. Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42,
        )
        print(f"[INFO] Train: {len(X_train)}, Test: {len(X_test)}")

        # 4. LightGBM parametreleri
        params = {
            "objective": "regression",
            "metric": "mae",
            "boosting_type": "gbdt",
            "num_leaves": 63,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "n_estimators": 500,
            "random_state": 42,
        }

        # 5. Model egitimi
        self.model = lgb.LGBMRegressor(**params)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=0),
            ],
        )

        # 6. Tahmin ve metrikler
        y_pred = self.model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))
        mape = float(mean_absolute_percentage_error(y_test, y_pred))

        print("\n[TEST METRIKLERI]")
        print(f"  RMSE:  {rmse:>15,.0f} TL")
        print(f"  MAE:   {mae:>15,.0f} TL")
        print(f"  R2:    {r2:>15.4f}")
        print(f"  MAPE:  {mape:>15.2%}")

        # 7. Cross-validation (5-fold) — best_iteration kullan (overfitting onleme)
        cv_params = {**params, "n_estimators": self.model.best_iteration_}
        cv_scores = cross_val_score(
            lgb.LGBMRegressor(**cv_params),
            X, y,
            cv=5,
            scoring="neg_mean_absolute_percentage_error",
        )
        cv_mape = -cv_scores.mean()
        cv_std = cv_scores.std()
        print("\n[5-FOLD CV]")
        print(f"  CV MAPE: {cv_mape:.2%} (+/- {cv_std:.2%})")

        # 8. Feature importance (top 10)
        importance = dict(
            zip(
                self.fe.get_feature_names(),
                self.model.feature_importances_.tolist(),
            )
        )
        top_10 = dict(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        print("\n[FEATURE IMPORTANCE - Top 10]")
        for name, imp in top_10.items():
            print(f"  {name:25s} {imp:6d}")

        return {
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "mape": mape,
            "cv_mape": cv_mape,
            "cv_std": float(cv_std),
            "feature_importance": importance,
            "top_10_features": top_10,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "feature_count": len(self.fe.get_feature_names()),
            "best_iteration": self.model.best_iteration_,
        }

    def predict(self, input_data: dict) -> dict:
        """Tek bir mulk icin fiyat tahmini.

        Args:
            input_data: Mulk ozellikleri (dict).

        Returns:
            Tahmini fiyat ve guven skoru.
        """
        import pandas as pd

        if self.model is None:
            raise RuntimeError("Model yuklenmedi. Once train() veya load_model() cagirin.")

        df = pd.DataFrame([input_data])
        X = self.fe.transform(df)
        prediction = self.model.predict(X)[0]

        return {
            "estimated_price": round(float(prediction)),
            "confidence": 0.85,  # Basit sabit guven skoru (ileride gelistirilebilir)
        }

    def save_model(self, path: str) -> None:
        """Model ve feature engineer'i kaydet."""
        import joblib

        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)

        # Feature engineer ayri kaydet
        self.fe.save(path)

        # LightGBM modeli kaydet
        joblib.dump(self.model, p / "lgbm_model.joblib")
        print(f"[OK] Model kaydedildi: {p}")

    def load_model(self, path: str) -> None:
        """Model ve feature engineer'i yukle."""
        import joblib

        p = Path(path)
        self.fe.load(path)
        self.model = joblib.load(p / "lgbm_model.joblib")
        print(f"[OK] Model yuklendi: {p}")
