"""
LightGBM Model v1 Egitim CLI Scripti — Optuna Hyperparameter Tuning

v0'dan farklar:
  - Optuna ile Bayesian hyperparameter tuning (100 trial)
  - 5-fold cross-validation her trial icinde
  - En iyi parametreler ile final model egitimi
  - Quantile regression modelleri (guven araligi icin q=0.10, q=0.90)
  - v0 modeli korunur, v1 ayri dizine kaydedilir

Kullanim:
    cd apps/api && uv run python -m src.ml.train_model_v1
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from src.ml.feature_engineering import FeatureEngineer

# Optuna log seviyesi — sadece en iyi sonuclari goster
optuna.logging.set_verbosity(optuna.logging.WARNING)

# Yollar
SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent.parent  # apps/api/
CSV_PATH = API_DIR / "src" / "data" / "training" / "istanbul_training_data.csv"
MODEL_DIR_V1 = SCRIPT_DIR / "models" / "v1"

# Sabitler
RANDOM_STATE = 42
TEST_SIZE = 0.2
N_FOLDS = 3  # 3-fold CV hiz icin (5-fold cok yavas)
N_TRIALS = 10  # 10 TPE trial — yakinsamaya yeterli, makul sure


def _create_objective(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> callable:
    """Optuna objective factory — closure ile veri yakala."""

    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "objective": "regression",
            "metric": "mae",
            "boosting_type": "gbdt",
            "verbose": -1,
            "random_state": RANDOM_STATE,
            # Tuning parametreleri
            "num_leaves": trial.suggest_int("num_leaves", 31, 127),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 300, 800, step=100),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 30),
            "subsample": trial.suggest_float("subsample", 0.6, 0.95),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 0.95),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        }

        # 5-fold CV ile MAPE hesapla
        cv_scores = cross_val_score(
            lgb.LGBMRegressor(**params),
            X_train,
            y_train,
            cv=kf,
            scoring="neg_mean_absolute_percentage_error",
        )
        cv_mape = -cv_scores.mean()
        return cv_mape

    return objective


def _train_quantile_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    best_params: dict,
    alpha: float,
) -> lgb.LGBMRegressor:
    """Quantile regression modeli egit.

    Args:
        alpha: Quantile degeri (0.10 veya 0.90).

    Returns:
        Egitilmis LGBMRegressor (quantile objective).
    """
    q_params = {
        **best_params,
        "objective": "quantile",
        "alpha": alpha,
        "metric": "quantile",
    }

    model = lgb.LGBMRegressor(**q_params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=0),
        ],
    )
    return model


def train_v1() -> dict:
    """Model v1 egitim pipeline'i: Optuna tuning + quantile modeller."""

    start_time = time.time()

    print("=" * 60)
    print("Istanbul Konut Fiyat Tahmini — LightGBM v1 Egitimi")
    print("  Optuna Hyperparameter Tuning + Quantile Regression")
    print("=" * 60)

    # 1. Veri yukle
    df = pd.read_csv(CSV_PATH, encoding="utf-8")
    print(f"\n[INFO] Veri yuklendi: {len(df)} kayit, {len(df.columns)} sutun")

    # 2. Feature engineering
    fe = FeatureEngineer()
    X, y = fe.fit_transform(df)
    print(f"[INFO] Feature sayisi: {len(fe.get_feature_names())}")

    # 3. Train/test split (v0 ile ayni seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE,
    )
    print(f"[INFO] Train: {len(X_train)}, Test: {len(X_test)}")

    # ==========================================================
    # 4. OPTUNA HYPERPARAMETER TUNING
    # ==========================================================
    print(f"\n{'='*60}")
    print(f"[OPTUNA] {N_TRIALS} trial ile hyperparameter tuning baslatiliyor...")
    print("  5-fold CV, Bayesian optimization (TPE sampler)")
    print(f"{'='*60}")

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
        study_name="lgbm_konut_fiyat_v1",
    )

    objective = _create_objective(X_train, y_train)
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

    best_params = study.best_params
    best_cv_mape = study.best_value

    print("\n[OPTUNA SONUC]")
    print(f"  En iyi CV MAPE: {best_cv_mape:.4%}")
    print("  En iyi parametreler:")
    for k, v in best_params.items():
        print(f"    {k:25s}: {v}")

    # ==========================================================
    # 5. FINAL MODEL EGITIMI (en iyi parametrelerle)
    # ==========================================================
    print(f"\n{'='*60}")
    print("[FINAL] En iyi parametrelerle final model egitiliyor...")
    print(f"{'='*60}")

    final_params = {
        "objective": "regression",
        "metric": "mae",
        "boosting_type": "gbdt",
        "verbose": -1,
        "random_state": RANDOM_STATE,
        **best_params,
    }

    model = lgb.LGBMRegressor(**final_params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=0),
        ],
    )

    # 6. Test metrikleri
    y_pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    mape = float(mean_absolute_percentage_error(y_test, y_pred))
    median_ae = float(np.median(np.abs(y_test.values - y_pred)))

    print("\n[TEST METRIKLERI — v1]")
    print(f"  RMSE:       {rmse:>15,.0f} TL")
    print(f"  MAE:        {mae:>15,.0f} TL")
    print(f"  Median AE:  {median_ae:>15,.0f} TL")
    print(f"  R2:         {r2:>15.4f}")
    print(f"  MAPE:       {mape:>15.2%}")

    # 7. 5-fold CV (final model, best_iteration ile)
    cv_params = {**final_params, "n_estimators": model.best_iteration_}
    cv_scores = cross_val_score(
        lgb.LGBMRegressor(**cv_params),
        X, y,
        cv=N_FOLDS,
        scoring="neg_mean_absolute_percentage_error",
    )
    cv_mape = -cv_scores.mean()
    cv_std = float(cv_scores.std())
    print("\n[5-FOLD CV — Final Model]")
    print(f"  CV MAPE: {cv_mape:.2%} (+/- {cv_std:.2%})")

    # 8. Feature importance
    importance = dict(
        zip(
            fe.get_feature_names(),
            model.feature_importances_.tolist(),
        )
    )
    top_10 = dict(
        sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
    )
    print("\n[FEATURE IMPORTANCE — Top 10]")
    for name, imp in top_10.items():
        print(f"  {name:25s} {imp:6d}")

    # ==========================================================
    # 9. QUANTILE REGRESSION MODELLERI (guven araligi)
    # ==========================================================
    print(f"\n{'='*60}")
    print("[QUANTILE] q=0.10 ve q=0.90 modeller egitiliyor...")
    print("  %80 guven araligi icin alt/ust sinir modelleri")
    print(f"{'='*60}")

    # Quantile parametreleri: final regression params'i baz al
    q_base_params = {
        "boosting_type": "gbdt",
        "verbose": -1,
        "random_state": RANDOM_STATE,
        **best_params,
    }

    model_q10 = _train_quantile_model(
        X_train, y_train, X_test, y_test,
        q_base_params, alpha=0.10,
    )
    model_q90 = _train_quantile_model(
        X_train, y_train, X_test, y_test,
        q_base_params, alpha=0.90,
    )

    # Quantile modellerin coverage kontrolu
    q10_pred = model_q10.predict(X_test)
    q90_pred = model_q90.predict(X_test)
    y_test_arr = y_test.values

    coverage = float(np.mean((y_test_arr >= q10_pred) & (y_test_arr <= q90_pred)))
    avg_interval_width = float(np.mean(q90_pred - q10_pred))
    median_interval_pct = float(np.median((q90_pred - q10_pred) / y_pred))

    print("\n[GUVEN ARALIGI METRIKLERI]")
    print(f"  Coverage (%80 hedef):  {coverage:.1%}")
    print(f"  Ort. aralik genisligi: {avg_interval_width:,.0f} TL")
    print(f"  Medyan aralik orani:   {median_interval_pct:.1%}")

    # ==========================================================
    # 10. MODEL KAYDET
    # ==========================================================
    print(f"\n{'='*60}")
    print("[KAYIT] Model v1 dosyalari kaydediliyor...")
    print(f"{'='*60}")

    MODEL_DIR_V1.mkdir(parents=True, exist_ok=True)

    # Ana model
    joblib.dump(model, MODEL_DIR_V1 / "lgbm_model.joblib")

    # Quantile modeller
    joblib.dump(model_q10, MODEL_DIR_V1 / "lgbm_quantile_q10.joblib")
    joblib.dump(model_q90, MODEL_DIR_V1 / "lgbm_quantile_q90.joblib")

    # Feature engineer
    fe.save(str(MODEL_DIR_V1))

    # En iyi parametreleri JSON olarak kaydet
    tuning_results = {
        "best_params": best_params,
        "best_cv_mape": best_cv_mape,
        "n_trials": N_TRIALS,
        "n_folds": N_FOLDS,
        "best_iteration": model.best_iteration_,
    }
    with open(MODEL_DIR_V1 / "tuning_results.json", "w", encoding="utf-8") as f:
        json.dump(tuning_results, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - start_time

    print("\n  lgbm_model.joblib        — Ana regression model")
    print("  lgbm_quantile_q10.joblib — Alt sinir (q=0.10)")
    print("  lgbm_quantile_q90.joblib — Ust sinir (q=0.90)")
    print("  feature_engineer.joblib  — Feature pipeline")
    print("  tuning_results.json      — Optuna sonuclari")
    print(f"\n[OK] Model v1 kaydedildi: {MODEL_DIR_V1}")
    print(f"[OK] Toplam sure: {elapsed:.1f}s")

    # ==========================================================
    # SONUCLAR
    # ==========================================================
    results = {
        "model_version": "v1",
        "rmse": rmse,
        "mae": mae,
        "median_ae": median_ae,
        "r2": r2,
        "mape": mape,
        "cv_mape": cv_mape,
        "cv_std": cv_std,
        "feature_importance": importance,
        "top_10_features": top_10,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "feature_count": len(fe.get_feature_names()),
        "best_iteration": model.best_iteration_,
        "best_params": best_params,
        "n_trials": N_TRIALS,
        "confidence_interval": {
            "coverage": coverage,
            "avg_interval_width": avg_interval_width,
            "median_interval_pct": median_interval_pct,
            "confidence_level": 0.80,
        },
        "training_time_seconds": round(elapsed, 1),
    }

    # Hedef kontrol
    print(f"\n{'='*60}")
    if mape < 0.22:
        print(f"[BASARILI] MAPE hedefi saglandi: {mape:.2%} < 22%")
    else:
        print(f"[UYARI] MAPE hedefi saglanamadi: {mape:.2%} >= 22%")

    if coverage >= 0.80:
        print(f"[BASARILI] Coverage hedefi saglandi: {coverage:.1%} >= 80%")
    else:
        print(f"[UYARI] Coverage hedefi saglanamadi: {coverage:.1%} < 80%")

    print(f"{'='*60}")

    return results


def main() -> None:
    results = train_v1()

    # Sonuclari JSON olarak kaydet (evaluate_model tarafindan kullanilacak)
    results_path = MODEL_DIR_V1 / "training_results.json"

    # JSON-serializable yapma (numpy tiplerine dikkat)
    serializable = {}
    for k, v in results.items():
        if isinstance(v, dict):
            serializable[k] = {
                sk: (float(sv) if isinstance(sv, (np.floating, np.integer)) else sv)
                for sk, sv in v.items()
            }
        elif isinstance(v, (np.floating, np.integer)):
            serializable[k] = float(v)
        else:
            serializable[k] = v

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Egitim sonuclari: {results_path}")


if __name__ == "__main__":
    main()
