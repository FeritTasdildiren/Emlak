# Model Degerlendirme Raporu — v0

> Tarih: 2026-02-21T10:20:16.928970+00:00
> Model: LightGBM (GBDT) — `lgbm_konut_fiyat v0`

---

## 1. Genel Bakis

- **Toplam veri:** 3,749 kayit
- **Egitim seti:** 2,999 (%80)
- **Test seti:** 750 (%20)
- **Feature sayisi:** 24
- **Split:** random_state=42

---

## 2. Genel Metrikler

| Metrik | Deger |
|--------|-------|
| **RMSE** | 1,315,032 TL |
| **MAE** | 619,527 TL |
| **Median AE** | 316,702 TL |
| **R²** | 0.9275 |
| **MAPE** | 9.94% |

---

## 3. Ilce Bazli MAPE Analizi

| # | Ilce | MAPE | MAE (TL) | Ort. Fiyat (TL) | Test Sayisi |
|---|------|------|----------|-----------------|-------------|
| 1 | 🟢 Catalca | 14.77% | 266,793 | 1,709,297 | 12 |
| 2 | 🟢 Tuzla | 12.97% | 423,227 | 4,139,965 | 21 |
| 3 | 🟢 Buyukcekmece | 12.74% | 375,598 | 2,751,102 | 14 |
| 4 | 🟢 Beyoglu | 12.14% | 952,996 | 6,441,373 | 25 |
| 5 | 🟢 Eyupsultan | 11.95% | 427,519 | 4,417,480 | 24 |
| 6 | 🟢 Kartal | 11.89% | 677,187 | 5,966,982 | 12 |
| 7 | 🟢 Sariyer | 11.72% | 2,600,453 | 13,582,817 | 15 |
| 8 | 🟢 Atasehir | 11.72% | 877,243 | 6,591,799 | 21 |
| 9 | 🟢 Sultangazi | 11.20% | 190,573 | 2,074,973 | 20 |
| 10 | 🟢 Sancaktepe | 10.98% | 385,820 | 3,720,995 | 23 |
| 11 | 🟢 Uskudar | 10.96% | 1,306,280 | 10,657,109 | 20 |
| 12 | 🟢 Bayrampasa | 10.55% | 461,505 | 4,712,278 | 22 |
| 13 | 🟢 Gaziosmanpasa | 10.50% | 343,352 | 3,178,820 | 16 |
| 14 | 🟢 Besiktas | 10.47% | 1,270,012 | 11,235,959 | 22 |
| 15 | 🟢 Fatih | 10.27% | 743,552 | 6,435,487 | 29 |
| 16 | 🟢 Umraniye | 10.22% | 1,281,204 | 9,145,165 | 19 |
| 17 | 🟢 Kucukcekmece | 10.03% | 356,426 | 3,779,689 | 17 |
| 18 | 🟢 Bahcelievler | 9.88% | 620,211 | 5,654,602 | 20 |
| 19 | 🟢 Adalar | 9.85% | 460,036 | 5,134,936 | 19 |
| 20 | 🟢 Silivri | 9.82% | 192,675 | 2,040,374 | 20 |
| 21 | 🟢 Avcilar | 9.78% | 428,366 | 3,386,787 | 24 |
| 22 | 🟢 Sisli | 9.75% | 950,875 | 9,763,286 | 29 |
| 23 | 🟢 Basaksehir | 9.70% | 931,952 | 7,705,457 | 23 |
| 24 | 🟢 Maltepe | 9.44% | 797,354 | 8,229,218 | 17 |
| 25 | 🟢 Kadikoy | 9.40% | 1,068,324 | 10,182,999 | 24 |
| 26 | 🟢 Beylikduzu | 9.39% | 418,519 | 4,099,012 | 20 |
| 27 | 🟢 Pendik | 9.35% | 609,983 | 5,749,260 | 22 |
| 28 | 🟢 Bagcilar | 9.31% | 330,990 | 3,448,036 | 13 |
| 29 | 🟢 Beykoz | 9.22% | 544,593 | 6,517,068 | 21 |
| 30 | 🟢 Esenler | 8.75% | 297,943 | 3,486,662 | 17 |
| 31 | 🟢 Sile | 8.14% | 234,333 | 2,537,441 | 22 |
| 32 | 🟢 Bakirkoy | 8.07% | 841,401 | 10,026,250 | 16 |
| 33 | 🟢 Sultanbeyli | 7.65% | 202,646 | 2,671,895 | 25 |
| 34 | 🟢 Zeytinburnu | 7.43% | 374,694 | 5,234,620 | 24 |
| 35 | 🟢 Gungoren | 7.38% | 307,673 | 4,289,155 | 21 |
| 36 | 🟢 Esenyurt | 7.17% | 157,123 | 2,436,148 | 10 |
| 37 | 🟢 Cekmekoy | 7.17% | 284,970 | 3,820,351 | 14 |
| 38 | 🟢 Arnavutkoy | 6.64% | 148,042 | 2,097,259 | 17 |

> 🔴 MAPE > 25% — Model zayif &nbsp; 🟡 18-25% — Kabul edilebilir &nbsp; 🟢 < 18% — Iyi

---

## 4. Fiyat Araligi Bazli Performans

| Aralik | Sayi | MAPE | MAE (TL) | RMSE (TL) | Acc (±20%) |
|--------|------|------|----------|-----------|------------|
| 0-1M | 12 | 16.40% | 133,932 | 163,703 | 66.7% |
| 1-3M | 236 | 10.04% | 209,794 | 276,639 | 88.1% |
| 3-5M | 203 | 8.99% | 359,300 | 448,383 | 93.6% |
| 5M+ | 299 | 10.25% | 1,139,093 | 2,034,639 | 89.3% |

---

## 5. Feature Importance (Top 15)

| # | Feature | Importance | Bar |
|---|---------|------------|-----|
| 1 | `net_sqm` | 1057 | ████████████████████ |
| 2 | `lon` | 907 | █████████████████ |
| 3 | `building_age` | 859 | ████████████████ |
| 4 | `gross_sqm` | 756 | ██████████████ |
| 5 | `lat` | 541 | ██████████ |
| 6 | `transport_score` | 487 | █████████ |
| 7 | `district` | 438 | ████████ |
| 8 | `socioeconomic_level` | 397 | ███████ |
| 9 | `sqm_ratio` | 372 | ███████ |
| 10 | `rooms_per_sqm` | 372 | ███████ |
| 11 | `neighborhood` | 365 | ██████ |
| 12 | `floor_ratio` | 291 | █████ |
| 13 | `floor` | 269 | █████ |
| 14 | `total_floors` | 227 | ████ |
| 15 | `parking_type` | 170 | ███ |

---

## 6. Residual Analiz (Tahmin - Gercek)

| Istatistik | Deger (TL) |
|------------|------------|
| Mean | 33,380 |
| Median | -42,655 |
| Std | 1,314,609 |
| Q25 | -360,269 |
| Q75 | 284,082 |
| Min | -6,251,786 |
| Max | 19,710,544 |

### Hata Dagilimi

- **±10% icinde:** 58.7%
- **±20% icinde:** 89.7%
- **±30% icinde:** 98.7%

---

## 7. Sonuc ve Oneriler

Model v0 genel MAPE **9.94%** ile baseline hedefi 
**sagladi** (< 22%).

### Guclu Yanlar
- LightGBM hizli egitim ve tahmin
- Feature engineering pipeline kuruldu
- Train/test ayrimli degerlendirme

### Gelistirme Alanlari
- MAPE > 25% olan ilcelere ozel veri zenginlestirme
- Neighborhood encoding iyilestirme (target encoding vs label encoding)
- Hyperparameter tuning (Optuna ile)
- Temporal feature'lar (ilan tarihi, sezonsellik)
- Ensemble yontemler (stacking)

---

*Rapor otomatik olusturuldu: 2026-02-21T10:20:16.928970+00:00*
