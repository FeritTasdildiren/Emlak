"""
Model Degerlendirme Scripti — v0 LightGBM Konut Fiyat Tahmini

Detayli metrikler, ilce bazli MAPE, fiyat araligi accuracy,
feature importance ve residual analiz.

Kullanim:
    cd apps/api && uv run python -m src.ml.evaluate_model
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

from src.ml.feature_engineering import FeatureEngineer
from src.ml.trainer import ModelTrainer

# Yollar
SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent.parent  # apps/api/
CSV_PATH = API_DIR / "src" / "data" / "training" / "istanbul_training_data.csv"
MODEL_DIR = SCRIPT_DIR / "models" / "v0"
REPORT_PATH = SCRIPT_DIR / "MODEL-EVALUATION-v0.md"
METRICS_JSON_PATH = SCRIPT_DIR / "model_registry_entry.json"


def _mape_safe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Sifir kontrollu MAPE hesapla."""
    mask = y_true != 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


def _price_range_label(price: float) -> str:
    """Fiyat araligi etiketi don."""
    if price < 1_000_000:
        return "0-1M"
    elif price < 3_000_000:
        return "1-3M"
    elif price < 5_000_000:
        return "3-5M"
    else:
        return "5M+"


def evaluate() -> dict:
    """Model degerlendirme pipeline'i calistir."""

    # 1. Model ve feature engineer yukle
    fe = FeatureEngineer()
    trainer = ModelTrainer(fe)
    trainer.load_model(str(MODEL_DIR))

    # 2. CSV oku
    df_raw = pd.read_csv(CSV_PATH, encoding="utf-8")
    print(f"[INFO] Veri yuklendi: {len(df_raw)} kayit")

    # 3. Feature engineering (fit_transform — ayni encoder'lar icin)
    X, y = fe.fit_transform(df_raw)

    # 4. Train/test split (ayni seed=42, %20 test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
    )
    print(f"[INFO] Train: {len(X_train)}, Test: {len(X_test)}")

    # Ayni split ile orijinal DataFrame'deki ilceleri de ayir
    df_test = df_raw.iloc[y_test.index].copy()
    df_test = df_test.reset_index(drop=True)

    # 5. Test seti uzerinde tahmin
    y_pred = trainer.model.predict(X_test)
    y_test_arr = y_test.values
    y_pred_arr = np.array(y_pred)

    # ============================================================
    # 5a. GENEL METRIKLER
    # ============================================================
    rmse = float(np.sqrt(mean_squared_error(y_test_arr, y_pred_arr)))
    mae = float(mean_absolute_error(y_test_arr, y_pred_arr))
    r2 = float(r2_score(y_test_arr, y_pred_arr))
    mape = float(mean_absolute_percentage_error(y_test_arr, y_pred_arr))
    median_ae = float(np.median(np.abs(y_test_arr - y_pred_arr)))

    print("\n[GENEL METRIKLER]")
    print(f"  RMSE:       {rmse:>15,.0f} TL")
    print(f"  MAE:        {mae:>15,.0f} TL")
    print(f"  Median AE:  {median_ae:>15,.0f} TL")
    print(f"  R2:         {r2:>15.4f}")
    print(f"  MAPE:       {mape:>15.2%}")

    # ============================================================
    # 5b. ILCE BAZLI MAPE
    # ============================================================
    districts = df_test["district"].values
    district_results = []
    unique_districts = sorted(set(districts))

    for district in unique_districts:
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

    print("\n[ILCE BAZLI MAPE — En Kotu 10]")
    for d in district_results[:10]:
        print(f"  {d['district']:20s}  MAPE: {d['mape']:.2%}  (n={d['count']})")

    # ============================================================
    # 5c. FIYAT ARALIGI BAZLI ACCURACY
    # ============================================================
    price_ranges = np.array([_price_range_label(p) for p in y_test_arr])
    range_order = ["0-1M", "1-3M", "3-5M", "5M+"]
    price_range_results = []

    for pr in range_order:
        mask = price_ranges == pr
        if mask.sum() == 0:
            continue
        pr_mape = _mape_safe(y_test_arr[mask], y_pred_arr[mask])
        pr_mae = float(np.mean(np.abs(y_test_arr[mask] - y_pred_arr[mask])))
        pr_rmse = float(np.sqrt(np.mean((y_test_arr[mask] - y_pred_arr[mask]) ** 2)))
        pr_count = int(mask.sum())
        # %20 tolerans icinde "dogru" tahmin orani
        within_20 = float(np.mean(
            np.abs(y_test_arr[mask] - y_pred_arr[mask]) / y_test_arr[mask] < 0.20
        ))
        price_range_results.append({
            "range": pr,
            "count": pr_count,
            "mape": pr_mape,
            "mae": pr_mae,
            "rmse": pr_rmse,
            "accuracy_20pct": within_20,
        })

    print("\n[FIYAT ARALIGI BAZLI]")
    for pr in price_range_results:
        print(f"  {pr['range']:6s}  MAPE: {pr['mape']:.2%}  "
              f"Acc(±20%): {pr['accuracy_20pct']:.1%}  (n={pr['count']})")

    # ============================================================
    # 6. FEATURE IMPORTANCE (Top 15)
    # ============================================================
    feature_names = fe.get_feature_names()
    importances = trainer.model.feature_importances_.tolist()
    fi_pairs = sorted(
        zip(feature_names, importances), key=lambda x: x[1], reverse=True,
    )
    top_15 = fi_pairs[:15]

    print("\n[FEATURE IMPORTANCE — Top 15]")
    for name, imp in top_15:
        bar = "█" * int(imp / max(importances) * 30)
        print(f"  {name:25s} {imp:6d}  {bar}")

    # ============================================================
    # 7. RESIDUAL ANALIZ
    # ============================================================
    residuals = y_test_arr - y_pred_arr
    res_mean = float(np.mean(residuals))
    res_std = float(np.std(residuals))
    res_median = float(np.median(residuals))
    res_q25 = float(np.percentile(residuals, 25))
    res_q75 = float(np.percentile(residuals, 75))
    res_min = float(np.min(residuals))
    res_max = float(np.max(residuals))

    # Yuzde bazli residual
    pct_residuals = (residuals / y_test_arr) * 100
    pct_within_10 = float(np.mean(np.abs(pct_residuals) <= 10))
    pct_within_20 = float(np.mean(np.abs(pct_residuals) <= 20))
    pct_within_30 = float(np.mean(np.abs(pct_residuals) <= 30))

    print("\n[RESIDUAL ANALIZ]")
    print(f"  Mean:    {res_mean:>15,.0f} TL")
    print(f"  Median:  {res_median:>15,.0f} TL")
    print(f"  Std:     {res_std:>15,.0f} TL")
    print(f"  Min:     {res_min:>15,.0f} TL")
    print(f"  Max:     {res_max:>15,.0f} TL")
    print(f"\n  ±10% icinde: {pct_within_10:.1%}")
    print(f"  ±20% icinde: {pct_within_20:.1%}")
    print(f"  ±30% icinde: {pct_within_30:.1%}")

    # ============================================================
    # 8. SONUCLARI TOPLA
    # ============================================================
    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "model_version": "v0",
        "general_metrics": {
            "rmse": rmse,
            "mae": mae,
            "median_ae": median_ae,
            "r2": r2,
            "mape": mape,
        },
        "data_info": {
            "total_samples": len(df_raw),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "feature_count": len(feature_names),
            "split_ratio": 0.2,
            "random_state": 42,
        },
        "district_mape": district_results,
        "price_range_metrics": price_range_results,
        "feature_importance_top15": [
            {"feature": name, "importance": imp} for name, imp in top_15
        ],
        "residual_analysis": {
            "mean": res_mean,
            "median": res_median,
            "std": res_std,
            "q25": res_q25,
            "q75": res_q75,
            "min": res_min,
            "max": res_max,
            "pct_within_10": pct_within_10,
            "pct_within_20": pct_within_20,
            "pct_within_30": pct_within_30,
        },
    }

    return results


def write_markdown_report(results: dict) -> None:
    """Sonuclari markdown dosyasina yaz."""
    gm = results["general_metrics"]
    di = results["data_info"]
    ra = results["residual_analysis"]

    lines = [
        "# Model Degerlendirme Raporu — v0",
        "",
        f"> Tarih: {results['timestamp']}",
        "> Model: LightGBM (GBDT) — `lgbm_konut_fiyat v0`",
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
        "## 2. Genel Metrikler",
        "",
        "| Metrik | Deger |",
        "|--------|-------|",
        f"| **RMSE** | {gm['rmse']:,.0f} TL |",
        f"| **MAE** | {gm['mae']:,.0f} TL |",
        f"| **Median AE** | {gm['median_ae']:,.0f} TL |",
        f"| **R²** | {gm['r2']:.4f} |",
        f"| **MAPE** | {gm['mape']:.2%} |",
        "",
        "---",
        "",
        "## 3. Ilce Bazli MAPE Analizi",
        "",
        "| # | Ilce | MAPE | MAE (TL) | Ort. Fiyat (TL) | Test Sayisi |",
        "|---|------|------|----------|-----------------|-------------|",
    ]

    for i, d in enumerate(results["district_mape"], 1):
        emoji = "🔴" if d["mape"] > 0.25 else ("🟡" if d["mape"] > 0.18 else "🟢")
        lines.append(
            f"| {i} | {emoji} {d['district']} | {d['mape']:.2%} | "
            f"{d['mae']:,.0f} | {d['mean_price']:,.0f} | {d['count']} |"
        )

    lines.extend([
        "",
        "> 🔴 MAPE > 25% — Model zayif &nbsp; 🟡 18-25% — Kabul edilebilir &nbsp; 🟢 < 18% — Iyi",
        "",
        "---",
        "",
        "## 4. Fiyat Araligi Bazli Performans",
        "",
        "| Aralik | Sayi | MAPE | MAE (TL) | RMSE (TL) | Acc (±20%) |",
        "|--------|------|------|----------|-----------|------------|",
    ])

    for pr in results["price_range_metrics"]:
        lines.append(
            f"| {pr['range']} | {pr['count']} | {pr['mape']:.2%} | "
            f"{pr['mae']:,.0f} | {pr['rmse']:,.0f} | {pr['accuracy_20pct']:.1%} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Feature Importance (Top 15)",
        "",
        "| # | Feature | Importance | Bar |",
        "|---|---------|------------|-----|",
    ])

    max_imp = results["feature_importance_top15"][0]["importance"] if results["feature_importance_top15"] else 1
    for i, fi in enumerate(results["feature_importance_top15"], 1):
        bar_len = int(fi["importance"] / max_imp * 20)
        bar = "█" * bar_len
        lines.append(f"| {i} | `{fi['feature']}` | {fi['importance']} | {bar} |")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Residual Analiz (Tahmin - Gercek)",
        "",
        "| Istatistik | Deger (TL) |",
        "|------------|------------|",
        f"| Mean | {ra['mean']:,.0f} |",
        f"| Median | {ra['median']:,.0f} |",
        f"| Std | {ra['std']:,.0f} |",
        f"| Q25 | {ra['q25']:,.0f} |",
        f"| Q75 | {ra['q75']:,.0f} |",
        f"| Min | {ra['min']:,.0f} |",
        f"| Max | {ra['max']:,.0f} |",
        "",
        "### Hata Dagilimi",
        "",
        f"- **±10% icinde:** {ra['pct_within_10']:.1%}",
        f"- **±20% icinde:** {ra['pct_within_20']:.1%}",
        f"- **±30% icinde:** {ra['pct_within_30']:.1%}",
        "",
        "---",
        "",
        "## 7. Sonuc ve Oneriler",
        "",
        f"Model v0 genel MAPE **{gm['mape']:.2%}** ile baseline hedefi ",
        f"{'**sagladi** (< 22%).' if gm['mape'] < 0.22 else '**saglayamadi** (>= 22%).'}",
        "",
        "### Guclu Yanlar",
        "- LightGBM hizli egitim ve tahmin",
        "- Feature engineering pipeline kuruldu",
        "- Train/test ayrimli degerlendirme",
        "",
        "### Gelistirme Alanlari",
        "- MAPE > 25% olan ilcelere ozel veri zenginlestirme",
        "- Neighborhood encoding iyilestirme (target encoding vs label encoding)",
        "- Hyperparameter tuning (Optuna ile)",
        "- Temporal feature'lar (ilan tarihi, sezonsellik)",
        "- Ensemble yontemler (stacking)",
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
    print("Model Degerlendirme — v0 LightGBM Konut Fiyat Tahmini")
    print("=" * 60)

    results = evaluate()
    write_markdown_report(results)

    # Metrikleri JSON olarak da kaydet (register_model.py kullanacak)
    json_path = SCRIPT_DIR / "evaluation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[OK] Metrik JSON: {json_path}")


if __name__ == "__main__":
    main()
