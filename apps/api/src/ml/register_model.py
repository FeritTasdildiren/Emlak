"""
Model Registry v0 Kayit Scripti

Egitilmis modelin metriklerini okuyup model_registry_entry.json olusturur.
Bu JSON ileride migration/seed script ile DB'ye yazilacak.

Kullanim:
    cd apps/api && uv run python -m src.ml.register_model
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_JSON = SCRIPT_DIR / "evaluation_results.json"
OUTPUT_JSON = SCRIPT_DIR / "model_registry_entry.json"


def main() -> None:
    print("=" * 60)
    print("Model Registry — v0 Kayit")
    print("=" * 60)

    # Degerlendirme sonuclarini oku
    if not EVAL_JSON.exists():
        print(f"[HATA] Degerlendirme sonuclari bulunamadi: {EVAL_JSON}")
        print("       Once evaluate_model.py calistirin.")
        raise SystemExit(1)

    with open(EVAL_JSON, encoding="utf-8") as f:
        eval_results = json.load(f)

    gm = eval_results["general_metrics"]
    di = eval_results["data_info"]

    # model_registry tablosuna uygun kayit
    entry = {
        "id": str(uuid.uuid4()),
        "model_name": "lgbm_konut_fiyat",
        "version": "v0",
        "artifact_url": "ml/models/v0/",
        "metrics": {
            "rmse": round(gm["rmse"], 2),
            "mae": round(gm["mae"], 2),
            "r2": round(gm["r2"], 4),
            "mape": round(gm["mape"], 4),
            "median_ae": round(gm["median_ae"], 2),
            "test_size": di["test_size"],
            "train_size": di["train_size"],
        },
        "training_data_size": di["total_samples"],
        "feature_count": di["feature_count"],
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

    print("\n[NOT] Bu JSON'i DB'ye yazmak icin migration veya seed script kullanin.")
    print("      SQL ornegi:")
    print("      INSERT INTO model_registry (id, model_name, version, artifact_url,")
    print("        metrics, training_data_size, feature_count, status)")
    print(f"      VALUES ('{entry['id']}', '{entry['model_name']}', '{entry['version']}',")
    print(f"        '{entry['artifact_url']}', '{json.dumps(entry['metrics'])}',")
    print(f"        {entry['training_data_size']}, {entry['feature_count']}, '{entry['status']}');")


if __name__ == "__main__":
    main()
