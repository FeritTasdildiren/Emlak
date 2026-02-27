"""
Model Registry v1 Kayit Scripti

Egitilmis v1 modelin metriklerini okuyup model_registry_entry_v1.json olusturur.

Kullanim:
    cd apps/api && uv run python -m src.ml.register_model_v1
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_JSON = SCRIPT_DIR / "evaluation_results_v1.json"
OUTPUT_JSON = SCRIPT_DIR / "model_registry_entry_v1.json"


def main() -> None:
    print("=" * 60)
    print("Model Registry — v1 Kayit")
    print("=" * 60)

    # Degerlendirme sonuclarini oku
    if not EVAL_JSON.exists():
        print(f"[HATA] Degerlendirme sonuclari bulunamadi: {EVAL_JSON}")
        print("       Once evaluate_model_v1.py calistirin.")
        raise SystemExit(1)

    with open(EVAL_JSON, encoding="utf-8") as f:
        eval_results = json.load(f)

    v1 = eval_results["v1"]
    ci = eval_results["confidence_interval"]
    di = eval_results["data_info"]
    tr = eval_results.get("tuning_results", {})
    imp = eval_results.get("improvement", {})

    # model_registry tablosuna uygun kayit
    entry = {
        "id": str(uuid.uuid4()),
        "model_name": "lgbm_konut_fiyat",
        "version": "v1",
        "artifact_url": "ml/models/v1/",
        "metrics": {
            "rmse": round(v1["rmse"], 2),
            "mae": round(v1["mae"], 2),
            "r2": round(v1["r2"], 4),
            "mape": round(v1["mape"], 4),
            "median_ae": round(v1["median_ae"], 2),
            "within_10pct": round(v1["within_10pct"], 4),
            "within_20pct": round(v1["within_20pct"], 4),
            "test_size": di["test_size"],
            "train_size": di["train_size"],
        },
        "confidence_interval": {
            "coverage": round(ci["coverage"], 4),
            "avg_interval_width": round(ci["avg_interval_width"], 2),
            "median_relative_width": round(ci["median_relative_width"], 4),
            "confidence_level": 0.80,
            "method": "quantile_regression",
            "quantiles": [0.10, 0.90],
        },
        "hyperparameters": tr.get("best_params", {}),
        "tuning": {
            "method": "optuna_tpe",
            "n_trials": tr.get("n_trials", 100),
            "n_folds": tr.get("n_folds", 5),
            "best_cv_mape": tr.get("best_cv_mape"),
        },
        "improvement_over_v0": {
            "mape_pct": round(imp.get("mape_pct", 0), 2),
            "r2_delta": round(imp.get("r2_delta", 0), 4),
            "mae_pct": round(imp.get("mae_pct", 0), 2),
        },
        "training_data_size": di["total_samples"],
        "feature_count": di["feature_count"],
        "artifacts": [
            "lgbm_model.joblib",
            "lgbm_quantile_q10.joblib",
            "lgbm_quantile_q90.joblib",
            "feature_engineer.joblib",
            "tuning_results.json",
        ],
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    # JSON olarak kaydet
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Registry kaydi olusturuldu: {OUTPUT_JSON}")
    print(f"\n  model_name:         {entry['model_name']}")
    print(f"  version:            {entry['version']}")
    print(f"  artifact_url:       {entry['artifact_url']}")
    print(f"  training_data_size: {entry['training_data_size']}")
    print(f"  feature_count:      {entry['feature_count']}")
    print(f"  status:             {entry['status']}")
    print("\n  Metrikler:")
    for k, v in entry["metrics"].items():
        print(f"    {k:15s}: {v}")
    print("\n  Guven Araligi:")
    for k, v in entry["confidence_interval"].items():
        print(f"    {k:25s}: {v}")
    print("\n  v0 → v1 Iyilesme:")
    for k, v in entry["improvement_over_v0"].items():
        print(f"    {k:15s}: {v:+.2f}%")


if __name__ == "__main__":
    main()
