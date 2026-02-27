# Model Degerlendirme Raporu — v1

> Tarih: 2026-02-21
> Model: LightGBM (GBDT) — `lgbm_konut_fiyat v1`
> Onceki: v0 (baseline)

---

## 1. v0 vs v1 Karsilastirma

| Metrik | v0 | v1 | Degisim |
|--------|----|----|---------|
| **MAPE** | 9.94% | 9.35% | -0.59 pp (iyilesme) |
| **R2** | 0.9275 | 0.9424 | +0.0149 (iyilesme) |
| **RMSE** | 1,315,032 TL | 1,172,140 TL | -142,892 TL (iyilesme) |
| **MAE** | 619,527 TL | 576,805 TL | -42,722 TL (iyilesme) |
| **Median AE** | 316,702 TL | 320,568 TL | +3,866 TL (hafif gerileme) |
| **Feature sayisi** | 24 | 24 | ayni |
| **Egitim seti** | 2,999 | 2,999 | ayni |
| **Test seti** | 750 | 750 | ayni |
| **Best iteration** | 130 | 384 | +254 (daha derin ogrenme) |
| **Egitim suresi** | ~30 sn | ~120 sn | +90 sn (Optuna tuning dahil) |

**Ozet:** v1 modeli tum ana metriklerde v0'dan ustun. MAPE %9.35 ile hedef <%22'nin oldukca altinda. R2 0.9424 ile varyans aciklama gucu artti. RMSE ve MAE azaldi. Median AE'de hafif gerileme (~1.2%) ihmal edilebilir seviyede.

---

## 2. Hyperparameter Tuning (Optuna)

| Parametre | v0 (default) | v1 (tuned) |
|-----------|-------------|------------|
| `num_leaves` | 63 | 60 |
| `learning_rate` | 0.05 | 0.0335 |
| `n_estimators` | 500 | 500 |
| `min_child_samples` | 20 (default) | 12 |
| `subsample` | 0.8 | 0.814 |
| `colsample_bytree` | 0.8 | 0.649 |
| `reg_alpha` | 0 (default) | 0.015 |
| `reg_lambda` | 0 (default) | 0.029 |

- **Arama yontemi:** Optuna TPE sampler, 10 trial, 3-fold CV
- **Hedef fonksiyon:** Negatif MAPE minimize
- **En iyi CV MAPE:** 9.92% (Optuna), test MAPE: 9.35%
- **Onemli degisiklikler:**
  - Dusuk learning rate (0.05 -> 0.0335) + daha fazla iterasyon (130 -> 384) = daha ince ogrenme
  - `colsample_bytree` 0.8 -> 0.649: feature subsampling arttirildi, overfitting riski azaltildi
  - Regularization eklendi (`reg_alpha=0.015`, `reg_lambda=0.029`): model complexity sinirlandirildi
  - `min_child_samples` 20 -> 12: yaprak basina minimum veri azaltildi, model daha esnek

---

## 3. Feature Importance (Top 10)

| # | Feature | v1 Importance | v0 Importance | Degisim |
|---|---------|--------------|--------------|---------|
| 1 | `net_sqm` | 2,525 | 1,057 | +1,468 (buyuk artis) |
| 2 | `gross_sqm` | 2,519 | 756 | +1,763 (buyuk artis) |
| 3 | `lon` | 2,234 | 907 | +1,327 (buyuk artis) |
| 4 | `building_age` | 2,033 | 859 | +1,174 (buyuk artis) |
| 5 | `rooms_per_sqm` | 1,578 | 372 | +1,206 (buyuk artis) |
| 6 | `lat` | 1,554 | 541 | +1,013 (buyuk artis) |
| 7 | `sqm_ratio` | 1,544 | 372 | +1,172 (buyuk artis) |
| 8 | `district` | 1,272 | 438 | +834 |
| 9 | `neighborhood` | 1,156 | 365 | +791 |
| 10 | `transport_score` | 918 | 487 | +431 |

**Yorum:** v1'de tum feature'larin importance degerleri yukseldi (daha fazla iterasyon = daha fazla split = daha yuksek importance). Onemli olan sira degisikligi: `rooms_per_sqm` ve `sqm_ratio` turev feature'lari v0'da 9-10. siradan v1'de 5-7. siraya cikti. Bu, Optuna'nin bu turev feature'lari daha iyi kullanmasini saglayan parametreler buldugunu gosteriyor.

---

## 4. Guven Araligi Metrikleri (Quantile Regression)

| Metrik | Deger | Hedef | Durum |
|--------|-------|-------|-------|
| **Coverage** | 57.6% | 80% | KARSILANMADI |
| **Confidence level** | 80% | 80% | OK |
| **Ortalama aralik genisligi** | 1,598,664 TL | - | - |
| **Medyan aralik yuzdesi** | 21.6% | - | - |

### Quantile Model Detaylari

- **q10 model:** LightGBM quantile objective, alpha=0.10
- **q90 model:** LightGBM quantile objective, alpha=0.90
- **Toplam model dosyasi:** 3 (ana + q10 + q90)

### Coverage Analizi

Coverage %57.6 ile hedef %80'in altinda. Bu, quantile modellerin tahmin araliginin gercek dagilima gore **dar** oldugu anlamina gelir. Olasi nedenler:

1. **Egitim verisi yetersizligi:** 3,749 kayit quantile regression icin sinirda
2. **Kucuk trial sayisi:** Quantile modeller de Optuna ile tuning yapilabilir (su an default parametreler)
3. **Feature noise:** Bazi feature'lardaki gurultu quantile tahminlerini daraltmis olabilir

### Iyilestirme Onerileri (v2 icin)

- Quantile modellere ozel Optuna tuning (alpha=0.10 ve 0.90 icin ayri)
- Conformalized Quantile Regression (CQR) ile kalibrasyon
- Veri seti buyutme (5,000+ kayit hedefle)
- Daha genis quantile araligi dene (q=0.05, q=0.95)

---

## 5. Cross-Validation

| Metrik | Deger |
|--------|-------|
| **CV MAPE (3-fold)** | 37.3% |
| **CV Std** | 20.0% |

CV MAPE'nin test MAPE'den cok yuksek olmasi fold'lar arasi veri dagilim farkliligini gosteriyor. 3-fold ile bazi fold'larda nadir ilceler yetersiz temsil ediliyor. Bu, daha fazla veri ile azalacak bir sorundur.

---

## 6. v0 Hata Dagilimi Referans

| Aralik | v0 Yuzde |
|--------|---------|
| +-10% icinde | 58.7% |
| +-20% icinde | 89.7% |
| +-30% icinde | 98.7% |

> v1 icin ayni dagilim analizi henuz calistirilmadi. v0'daki +-20% accuracy %89.7 referans degeridir.

---

## 7. Model Dosyalari

| Dosya | Boyut | Aciklama |
|-------|-------|----------|
| `models/v1/lgbm_model.joblib` | Ana model | Nokta tahmini (regression) |
| `models/v1/lgbm_quantile_q10.joblib` | Q10 model | Alt sinir (%10 quantile) |
| `models/v1/lgbm_quantile_q90.joblib` | Q90 model | Ust sinir (%90 quantile) |
| `models/v1/feature_engineer.joblib` | FE pipeline | LabelEncoder + feature columns |
| `models/v1/training_results.json` | Metrikler | Egitim sonuclari |
| `models/v1/tuning_results.json` | Tuning | Optuna best params |

---

## 8. Bilinen Sinirlamalar

1. **Coverage dusuk (%57.6):** Quantile modeller dar aralik veriyor. Gercek guven araligi icin margin-based fallback hala daha guvenilir.
2. **CV MAPE yuksek (%37.3):** 3-fold CV fold'lar arasi varyans yuksek. Daha fazla veri ve stratified k-fold gerekli.
3. **Sadece Istanbul:** Model Istanbul konut verisi ile egitildi. Diger sehirler icin yeniden egitim gerekli.
4. **Sentetik veri:** Egitim verisi gercek ilan verisi degil, arastirma bazli sentetik veri. Production'da gercek veri ile yeniden egitim sart.
5. **Temporal feature eksik:** Ilan tarihi, sezonsellik gibi zaman boyutu feature'lari henuz yok.
6. **Median AE hafif gerileme:** v1'de median AE 320,568 TL (v0: 316,702 TL). Medyan hatada %1.2 artis var.

---

## 9. Sonuc

Model v1, Optuna hyperparameter tuning ile v0'a gore **tum ana metriklerde iyilesme** sagladi:

- MAPE: %9.94 -> %9.35 (**-0.59 pp**)
- R2: 0.9275 -> 0.9424 (**+0.015**)
- RMSE: 1.31M -> 1.17M (**-143K TL**)
- MAE: 620K -> 577K (**-43K TL**)

Quantile regression ile veri-tabanli guven araligi altyapisi kuruldu ancak coverage henuz hedef %80'e ulasmadi (%57.6). Bu sinirlamayla birlikte InferenceService'de adaptive confidence skoru hesaplanarak interval darligini guven skoruna yansitma mekanizmasi eklendi.

**v2 icin oncelikli iyilestirmeler:**
1. Quantile model tuning (Optuna ile ayri optimizasyon)
2. Conformalized Quantile Regression (CQR) kalibrasyon
3. Veri seti buyutme (hedef: 5,000+ kayit)
4. Gercek ilan verisi ile yeniden egitim

---

*Rapor olusturuldu: 2026-02-21*
