"""
LightGBM Model Egitim CLI Scripti

Kullanim:
    cd apps/api && uv run python -m src.ml.train_model
"""

from __future__ import annotations

from pathlib import Path

from src.ml.feature_engineering import FeatureEngineer
from src.ml.trainer import ModelTrainer

# Proje kokundan baslayarak yollar
SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent.parent  # apps/api/
CSV_PATH = API_DIR / "src" / "data" / "training" / "istanbul_training_data.csv"
MODEL_DIR = SCRIPT_DIR / "models" / "v0"


def main() -> None:
    print("=" * 60)
    print("Istanbul Konut Fiyat Tahmini - LightGBM Egitimi")
    print("=" * 60)

    trainer = ModelTrainer(FeatureEngineer())
    results = trainer.train(str(CSV_PATH))

    print("\n" + "=" * 60)
    print("SONUCLAR")
    print("=" * 60)
    print(f"  MAPE:           {results['mape']:.2%}")
    print(f"  CV MAPE:        {results['cv_mape']:.2%}")
    print(f"  R2:             {results['r2']:.4f}")
    print(f"  RMSE:           {results['rmse']:,.0f} TL")
    print(f"  MAE:            {results['mae']:,.0f} TL")
    print(f"  Feature sayisi: {results['feature_count']}")
    print(f"  Best iteration: {results['best_iteration']}")

    # Model kaydet
    trainer.save_model(str(MODEL_DIR))
    print(f"\n[OK] Model v0 kaydedildi: {MODEL_DIR}")

    # Hedef kontrol
    if results["mape"] < 0.22:
        print(f"\n[BASARILI] MAPE hedefi saglandi: {results['mape']:.2%} < 22%")
    else:
        print(f"\n[UYARI] MAPE hedefi saglanamadi: {results['mape']:.2%} >= 22%")


if __name__ == "__main__":
    main()
