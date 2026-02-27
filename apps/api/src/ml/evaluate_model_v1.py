"""
Model Degerlendirme Scripti — v1 LightGBM Konut Fiyat Tahmini

v0 vs v1 karsilastirma, ilce bazli MAPE, guven araligi coverage analizi.

Kullanim:
    cd apps/api && uv run python -m src.ml.evaluate_model_v1
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

from src.ml.confidence_interval import ConfidencePredictor
from src.ml.feature_engineering import FeatureEngineer
from src.ml.trainer import ModelTrainer

# Yollar
SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent.parent
CSV_PATH = API_DIR / "src" / "data" / "training" / "istanbul_training_data.csv"
MODEL_DIR_V0 = SCRIPT_DIR / "models" / "v0"
MODEL_DIR_V1 = SCRIPT_DIR / "models" / "v1"
REPORT_PATH = SCRIPT_DIR / "MODEL-EVALUATION-v1.md"

RANDOM_STATE = 42


def _mape_safe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


def _price_range_label(price: float) -> str:
    if price < 1_000_000:
        return "0-1M"
    elif price < 3_000_000:
        return "1-3M"
    elif price < 5_000_000:
        return "3-5M"
    else:
        return "5M+"


def _evaluate_model(
    model: ModelTrainer,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    districts: np.ndarray,
) -> dict:
    """Ortak metrik hesaplama fonksiyonu."""
    y_pred = model.model.predict(X_test)
    y_test_arr = y_test.values
    y_pred_arr = np.array(y_pred)

    rmse = float(np.sqrt(mean_squared_error(y_test_arr, y_pred_arr)))
    mae = float(mean_absolute_error(y_test_arr, y_pred_arr))
    r2 = float(r2_score(y_test_arr, y_pred_arr))
    mape = float(mean_absolute_percentage_error(y_test_arr, y_pred_arr))
    median_ae = float(np.median(np.abs(y_test_arr - y_pred_arr)))

    # Yuzde bazli accuracy
    pct_err = np.abs(y_test_arr - y_pred_arr) / y_test_arr
    within_10 = float(np.mean(pct_err <= 0.10))
    within_20 = float(np.mean(pct_err <= 0.20))
    within_30 = float(np.mean(pct_err <= 0.30))

    # Ilce bazli MAPE
    district_results = []
    for district in sorted(set(districts)):
        mask = districts == district
        if mask.sum() == 0:
            continue
        d_mape = _mape_safe(y_test_arr[mask], y_pred_arr[mask])
        d_mae = float(np.mean(np.abs(y_test_arr[mask] - y_pred_arr[mask])))
        d_count = int(mask.sum())
        d_mean_price = float(np.mean(y_test_arr[mask]))
        district_results.append({
            "district": district,
            "mape": d_mape,
            "mae": d_mae,
            "count": d_count,
            "mean_price": d_mean_price,
        })
    district_results.sort(key=lambda x: x["mape"], reverse=True)

    # Fiyat araligi bazli
    price_ranges = np.array([_price_range_label(p) for p in y_test_arr])
    range_order = ["0-1M", "1-3M", "3-5M", "5M+"]
    price_range_results = []
    for pr in range_order:
        mask = price_ranges == pr
        if mask.sum() == 0:
            continue
        pr_mape = _mape_safe(y_test_arr[mask], y_pred_arr[mask])
        pr_mae = float(np.mean(np.abs(y_test_arr[mask] - y_pred_arr[mask])))
        pr_count = int(mask.sum())
        pr_within_20 = float(np.mean(
            np.abs(y_test_arr[mask] - y_pred_arr[mask]) / y_test_arr[mask] < 0.20
        ))
        price_range_results.append({
            "range": pr,
            "count": pr_count,
            "mape": pr_mape,
            "mae": pr_mae,
            "accuracy_20pct": pr_within_20,
        })

    return {
        "rmse": rmse,
        "mae": mae,
        "median_ae": median_ae,
        "r2": r2,
        "mape": mape,
        "within_10pct": within_10,
        "within_20pct": within_20,
        "within_30pct": within_30,
        "district_mape": district_results,
        "price_range_metrics": price_range_results,
    }


def evaluate() -> dict:
    """v0 vs v1 karsilastirmali degerlendirme."""

    # 1. CSV oku
    df_raw = pd.read_csv(CSV_PATH, encoding="utf-8")
    print(f"[INFO] Veri yuklendi: {len(df_raw)} kayit")

    # 2. v0 model yukle ve feature engineering
    fe_v0 = FeatureEngineer()
    trainer_v0 = ModelTrainer(fe_v0)
    trainer_v0.load_model(str(MODEL_DIR_V0))

    X_v0, y_v0 = fe_v0.fit_transform(df_raw)
    X_train_v0, X_test_v0, y_train_v0, y_test_v0 = train_test_split(
        X_v0, y_v0, test_size=0.2, random_state=RANDOM_STATE,
    )

    # 3. v1 model yukle ve feature engineering
    fe_v1 = FeatureEngineer()
    trainer_v1 = ModelTrainer(fe_v1)
    trainer_v1.load_model(str(MODEL_DIR_V1))

    X_v1, y_v1 = fe_v1.fit_transform(df_raw)
    X_train_v1, X_test_v1, y_train_v1, y_test_v1 = train_test_split(
        X_v1, y_v1, test_size=0.2, random_state=RANDOM_STATE,
    )

    # Ilce bilgisi (ayni split)
    df_test = df_raw.iloc[y_test_v1.index].copy().reset_index(drop=True)
    districts = df_test["district"].values

    print(f"[INFO] Train: {len(X_train_v1)}, Test: {len(X_test_v1)}")

    # 4. Her iki modeli degerlendir
    print("\n[v0 DEGERLENDIRME]")
    metrics_v0 = _evaluate_model(trainer_v0, X_test_v0, y_test_v0, districts)
    print(f"  MAPE: {metrics_v0['mape']:.2%}, R2: {metrics_v0['r2']:.4f}")

    print("\n[v1 DEGERLENDIRME]")
    metrics_v1 = _evaluate_model(trainer_v1, X_test_v1, y_test_v1, districts)
    print(f"  MAPE: {metrics_v1['mape']:.2%}, R2: {metrics_v1['r2']:.4f}")

    # 5. Guven araligi degerlendirmesi (v1 only)
    print("\n[GUVEN ARALIGI DEGERLENDIRMESI]")
    cp = ConfidencePredictor()
    cp.load(str(MODEL_DIR_V1))
    ci_metrics = cp.evaluate_coverage(X_test_v1, y_test_v1)
    print(f"  Coverage:             {ci_metrics['coverage']:.1%} (hedef >= 80%)")
    print(f"  Ort. aralik genisligi: {ci_metrics['avg_interval_width']:,.0f} TL")
    print(f"  Medyan oransal aralik: {ci_metrics['median_relative_width']:.1%}")

    # 6. Feature importance (v1)
    feature_names = fe_v1.get_feature_names()
    importances = trainer_v1.model.feature_importances_.tolist()
    fi_pairs = sorted(
        zip(feature_names, importances), key=lambda x: x[1], reverse=True,
    )
    top_15 = fi_pairs[:15]

    # 7. Iyilesme hesapla
    mape_improvement = (metrics_v0["mape"] - metrics_v1["mape"]) / metrics_v0["mape"] * 100
    r2_improvement = metrics_v1["r2"] - metrics_v0["r2"]
    mae_improvement = (metrics_v0["mae"] - metrics_v1["mae"]) / metrics_v0["mae"] * 100

    print("\n[IYILESME v0 → v1]")
    print(f"  MAPE:  {mape_improvement:+.1f}% {'(daha iyi)' if mape_improvement > 0 else '(gerileme)'}")
    print(f"  R2:    {r2_improvement:+.4f}")
    print(f"  MAE:   {mae_improvement:+.1f}%")

    # Tuning results yukle
    tuning_path = MODEL_DIR_V1 / "tuning_results.json"
    tuning_results = {}
    if tuning_path.exists():
        with open(tuning_path, encoding="utf-8") as f:
            tuning_results = json.load(f)

    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "v0": metrics_v0,
        "v1": metrics_v1,
        "improvement": {
            "mape_pct": mape_improvement,
            "r2_delta": r2_improvement,
            "mae_pct": mae_improvement,
        },
        "confidence_interval": ci_metrics,
        "tuning_results": tuning_results,
        "feature_importance_top15": [
            {"feature": name, "importance": imp} for name, imp in top_15
        ],
        "data_info": {
            "total_samples": len(df_raw),
            "train_size": len(X_train_v1),
            "test_size": len(X_test_v1),
            "feature_count": len(feature_names),
        },
    }

    return results


def write_markdown_report(results: dict) -> None:
    """v0 vs v1 karsilastirma raporu yaz."""
    v0 = results["v0"]
    v1 = results["v1"]
    ci = results["confidence_interval"]
    imp = results["improvement"]
    di = results["data_info"]
    tr = results.get("tuning_results", {})

    def _delta(v0_val: float, v1_val: float, lower_better: bool = True) -> str:
        diff = v1_val - v0_val
        if lower_better:
            symbol = "↓" if diff < 0 else ("↑" if diff > 0 else "→")
        else:
            symbol = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
        return symbol

    lines = [
        "# Model Degerlendirme Raporu — v0 vs v1",
        "",
        f"> Tarih: {results['timestamp']}",
        "> Model: LightGBM (GBDT) — `lgbm_konut_fiyat`",
        "> Yenilik: Optuna hyperparameter tuning + Quantile Regression guven araligi",
        "",
        "---",
        "",
        "## 1. Genel Bakis",
        "",
        f"- **Toplam veri:** {di['total_samples']:,} kayit",
        f"- **Egitim seti:** {di['train_size']:,} (%80)",
        f"- **Test seti:** {di['test_size']:,} (%20)",
        f"- **Feature sayisi:** {di['feature_count']}",
        "- **Split:** random_state=42",
        "",
        "---",
        "",
        "## 2. v0 vs v1 Karsilastirma",
        "",
        "| Metrik | v0 | v1 | Degisim |",
        "|--------|----|----|---------|",
        f"| **MAPE** | {v0['mape']:.2%} | {v1['mape']:.2%} | {_delta(v0['mape'], v1['mape'])} {imp['mape_pct']:+.1f}% |",
        f"| **R²** | {v0['r2']:.4f} | {v1['r2']:.4f} | {_delta(v0['r2'], v1['r2'], False)} {imp['r2_delta']:+.4f} |",
        f"| **RMSE** | {v0['rmse']:,.0f} TL | {v1['rmse']:,.0f} TL | {_delta(v0['rmse'], v1['rmse'])} |",
        f"| **MAE** | {v0['mae']:,.0f} TL | {v1['mae']:,.0f} TL | {_delta(v0['mae'], v1['mae'])} {imp['mae_pct']:+.1f}% |",
        f"| **Median AE** | {v0['median_ae']:,.0f} TL | {v1['median_ae']:,.0f} TL | {_delta(v0['median_ae'], v1['median_ae'])} |",
        f"| **±10% icinde** | {v0['within_10pct']:.1%} | {v1['within_10pct']:.1%} | {_delta(v0['within_10pct'], v1['within_10pct'], False)} |",
        f"| **±20% icinde** | {v0['within_20pct']:.1%} | {v1['within_20pct']:.1%} | {_delta(v0['within_20pct'], v1['within_20pct'], False)} |",
        "",
    ]

    # Optuna tuning sonuclari
    if tr:
        lines.extend([
            "---",
            "",
            "## 3. Optuna Hyperparameter Tuning Sonuclari",
            "",
            f"- **Trial sayisi:** {tr.get('n_trials', 'N/A')}",
            f"- **Fold sayisi:** {tr.get('n_folds', 'N/A')}",
            f"- **En iyi CV MAPE:** {tr.get('best_cv_mape', 0):.4%}",
            f"- **Best iteration:** {tr.get('best_iteration', 'N/A')}",
            "",
            "### En Iyi Parametreler",
            "",
            "| Parametre | Deger |",
            "|-----------|-------|",
        ])
        for k, v in tr.get("best_params", {}).items():
            if isinstance(v, float):
                lines.append(f"| `{k}` | {v:.6f} |")
            else:
                lines.append(f"| `{k}` | {v} |")
        lines.append("")

    # Guven araligi
    lines.extend([
        "---",
        "",
        "## 4. Guven Araligi Analizi (%80 Confidence Interval)",
        "",
        "| Metrik | Deger | Hedef |",
        "|--------|-------|-------|",
        f"| **Coverage** | {ci['coverage']:.1%} | >= 80% {'✅' if ci['coverage_met'] else '❌'} |",
        f"| **Ort. aralik genisligi** | {ci['avg_interval_width']:,.0f} TL | — |",
        f"| **Medyan aralik genisligi** | {ci['median_interval_width']:,.0f} TL | — |",
        f"| **Ort. oransal aralik** | {ci['avg_relative_width']:.1%} | — |",
        f"| **Medyan oransal aralik** | {ci['median_relative_width']:.1%} | — |",
        f"| **Aralik icinde** | {ci['n_in_interval']}/{ci['n_samples']} | — |",
        "",
        "> **Yorum:** Quantile regression (q=0.10, q=0.90) ile her mulk icin",
        "> veriye dayali adaptive guven araligi hesaplaniyor. Sabit margin yerine",
        "> modelin belirsizligine gore daralan/genisleyen araliklar.",
        "",
    ])

    # Ilce bazli karsilastirma
    lines.extend([
        "---",
        "",
        "## 5. Ilce Bazli MAPE Karsilastirma",
        "",
        "| # | Ilce | v0 MAPE | v1 MAPE | Degisim | Test Sayisi |",
        "|---|------|---------|---------|---------|-------------|",
    ])

    # v0 ilce MAPE dict'i
    v0_district_map = {d["district"]: d["mape"] for d in v0["district_mape"]}
    for i, d in enumerate(v1["district_mape"], 1):
        v0_mape = v0_district_map.get(d["district"], 0)
        delta = d["mape"] - v0_mape
        symbol = "↓" if delta < 0 else ("↑" if delta > 0 else "→")
        emoji = "🔴" if d["mape"] > 0.20 else ("🟡" if d["mape"] > 0.12 else "🟢")
        lines.append(
            f"| {i} | {emoji} {d['district']} | {v0_mape:.2%} | {d['mape']:.2%} | "
            f"{symbol} {abs(delta):.2%} | {d['count']} |"
        )

    lines.extend([
        "",
        "> 🔴 MAPE > 20% — Zayif &nbsp; 🟡 12-20% — Kabul edilebilir &nbsp; 🟢 < 12% — Iyi",
        "",
    ])

    # Fiyat araligi
    lines.extend([
        "---",
        "",
        "## 6. Fiyat Araligi Bazli Performans",
        "",
        "| Aralik | v0 MAPE | v1 MAPE | v0 Acc(±20%) | v1 Acc(±20%) | Test |",
        "|--------|---------|---------|-------------|-------------|------|",
    ])

    v0_range_map = {p["range"]: p for p in v0["price_range_metrics"]}
    for pr in v1["price_range_metrics"]:
        v0_pr = v0_range_map.get(pr["range"], {})
        lines.append(
            f"| {pr['range']} | {v0_pr.get('mape', 0):.2%} | {pr['mape']:.2%} | "
            f"{v0_pr.get('accuracy_20pct', 0):.1%} | {pr['accuracy_20pct']:.1%} | {pr['count']} |"
        )

    # Feature importance
    lines.extend([
        "",
        "---",
        "",
        "## 7. Feature Importance (Top 15 — v1)",
        "",
        "| # | Feature | Importance |",
        "|---|---------|------------|",
    ])
    for i, fi in enumerate(results["feature_importance_top15"], 1):
        lines.append(f"| {i} | `{fi['feature']}` | {fi['importance']} |")

    # Sonuc
    lines.extend([
        "",
        "---",
        "",
        "## 8. Sonuc ve Oneriler",
        "",
        "### v0 → v1 Iyilesme Ozeti",
        f"- MAPE: {imp['mape_pct']:+.1f}% iyilesme",
        f"- R²: {imp['r2_delta']:+.4f} artis",
        f"- MAE: {imp['mae_pct']:+.1f}% iyilesme",
        f"- Guven araligi coverage: {ci['coverage']:.1%} (hedef %80)",
        "",
        "### Yeni Ozellikler (v1)",
        "- Optuna ile Bayesian hyperparameter optimization",
        "- Quantile regression ile data-driven guven araligi",
        "- Model version fallback mekanizmasi (v1 → v0)",
        "",
        "### Gelecek Iyilestirmeler (v2 icin)",
        "- Target encoding (neighborhood icin)",
        "- Temporal feature'lar (sezonsellik)",
        "- Ensemble yontemler",
        "- Daha fazla egitim verisi (ozellikle zayif ilceler)",
        "",
        "---",
        "",
        f"*Rapor otomatik olusturuldu: {results['timestamp']}*",
    ])

    report = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n[OK] Rapor yazildi: {REPORT_PATH}")


def main() -> None:
    print("=" * 60)
    print("Model Degerlendirme — v0 vs v1 Karsilastirma")
    print("=" * 60)

    results = evaluate()
    write_markdown_report(results)

    # JSON kaydet
    json_path = SCRIPT_DIR / "evaluation_results_v1.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"[OK] Metrik JSON: {json_path}")


if __name__ == "__main__":
    main()
