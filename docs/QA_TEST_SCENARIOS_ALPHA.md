# QA Test Senaryoları — Alpha (Sprint S5–S10)

**Proje:** Emlak Teknoloji Platformu
**Tarih:** 2026-02-26
**Hazırlayan:** QA/Test Senaryo Uzmanı
**Versiyon:** 1.0
**Kaynak:** Gerçek backend/frontend kodlarından türetilmiştir.

---

## İçindekiler

1. [Coverage Matrisi](#1-coverage-matrisi)
2. [S5 — AI Değerleme](#2-s5--ai-değerleme)
3. [S6 — Bölge Analizi](#3-s6--bölge-analizi)
4. [S7 — CRM](#4-s7--crm)
5. [S8 — İlan Asistanı](#5-s8--i̇lan-asistanı)
6. [S9 — Vitrin + Kredi Hesaplama](#6-s9--vitrin--kredi-hesaplama)
7. [S10 — Telegram Mini App & Bot](#7-s10--telegram-mini-app--bot)
8. [Çapraz Modül Senaryoları](#8-çapraz-modül-senaryoları)
9. [Multi-Tenant RLS Senaryoları](#9-multi-tenant-rls-senaryoları)
10. [Performans & Güvenlik Senaryoları](#10-performans--güvenlik-senaryoları)
11. [Öncelik Özet Tablosu](#11-öncelik-özet-tablosu)

---

## Öncelik Tanımları

| Seviye | Tanım | Örnek |
|--------|-------|-------|
| **P0** | Blocker — Ürün kullanılamaz | Auth bypass, data leak, crash |
| **P1** | Critical — Ana akış bozuk | Değerleme hatalı, kota çalışmıyor |
| **P2** | Major — Önemli ama workaround var | PDF format bozuk, emsal eksik |
| **P3** | Minor — Kozmetik / UX | Yanlış label, sıralama hatası |

---

## 1. Coverage Matrisi

| Sprint | Modül | API Endpoint Sayısı | Test Senaryosu | P0 | P1 | P2 | P3 |
|--------|-------|---------------------|----------------|----|----|----|----|
| S5 | AI Değerleme | 7 | 42 | 6 | 14 | 14 | 8 |
| S6 | Bölge Analizi | 8 | 35 | 4 | 11 | 13 | 7 |
| S7 | CRM | 14 | 48 | 7 | 16 | 16 | 9 |
| S8 | İlan Asistanı | 9 | 38 | 5 | 12 | 14 | 7 |
| S9 | Vitrin + Kredi | 11 | 36 | 4 | 12 | 13 | 7 |
| S10 | Telegram | 4+ bot cmds | 40 | 6 | 14 | 12 | 8 |
| — | Çapraz Modül | 5 akış | 25 | 5 | 10 | 7 | 3 |
| — | Multi-Tenant RLS | — | 12 | 6 | 4 | 2 | 0 |
| — | Performans/Güvenlik | — | 14 | 4 | 6 | 4 | 0 |
| **TOPLAM** | | | **290** | **47** | **99** | **95** | **49** |

---

## 2. S5 — AI Değerleme

### 2.1 POST /api/v1/valuations — ML Değerleme Oluşturma

**Kaynak Kod:** `modules/valuations/router.py:create_valuation`, `inference_service.py`, `anomaly_service.py`

#### S5-TC-001: Happy Path — Başarılı Değerleme (P0)
```
Given: Starter plan kullanıcı, kota 49/50 kullanılmış, geçerli JWT
When:  POST /api/v1/valuations
       {
         "district": "Kadikoy",
         "neighborhood": "Caferaga",
         "property_type": "Daire",
         "net_sqm": 120,
         "gross_sqm": 140,
         "room_count": 3,
         "living_room_count": 1,
         "floor": 5,
         "total_floors": 10,
         "building_age": 5,
         "heating_type": "Dogalgaz Kombi"
       }
Then:  HTTP 200
       - estimated_price > 0 (int, TL)
       - min_price < estimated_price < max_price
       - confidence ∈ [0, 1]
       - price_per_sqm = estimated_price / net_sqm (yaklaşık)
       - latency_ms > 0
       - model_version = "v0" veya "v1"
       - prediction_id = UUID formatında
       - comparables listesi max 5 eleman
       - quota_remaining = 0
       - quota_limit = 50
       - PredictionLog tablosunda yeni kayıt oluşmuş
```

#### S5-TC-002: Kota Aşımı — Starter Plan (P0)
```
Given: Starter plan kullanıcı, kota 50/50 kullanılmış
When:  POST /api/v1/valuations (geçerli body)
Then:  HTTP 429
       - type = "quota_exceeded"
       - limit = 50, used = 50
       - plan = "starter"
       - upgrade_url = "/pricing"
```

#### S5-TC-003: Kota Aşımı — Pro Plan (P1)
```
Given: Pro plan kullanıcı, kota 500/500 kullanılmış
When:  POST /api/v1/valuations (geçerli body)
Then:  HTTP 429
       - limit = 500, used = 500
       - plan = "pro"
```

#### S5-TC-004: Elite Plan — Sınırsız Kota (P0)
```
Given: Elite plan kullanıcı, 1000+ değerleme yapmış
When:  POST /api/v1/valuations (geçerli body)
Then:  HTTP 200
       - quota_remaining = -1
       - quota_limit = -1
       Açıklama: is_unlimited_plan("elite") → True, kota kontrolü atlanır
```

#### S5-TC-005: Kredi ile Kota Aşımı (P1)
```
Given: Starter plan, kota 50/50 dolu, credit_balance = 5
When:  check_credit(db, office_id, "starter", QuotaType.VALUATION)
Then:  True döner — kredi bakiyesi mevcut
When:  use_credit çağrılır
Then:  credit_balance → 4, valuations_used → 51
```

#### S5-TC-006: Abonelik Yoksa Varsayılan Plan (P1)
```
Given: Kullanıcının ofisi için Subscription kaydı yok
When:  POST /api/v1/valuations
Then:  plan_type "starter" olarak varsayılır (router.py:67-79)
       Kota 50 uygulanır
```

#### S5-TC-007: Validation — net_sqm = 0 (P1)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"net_sqm": 0, ...}
Then:  HTTP 422 — Field gt=0 validation hatası
       Pydantic: "net_sqm must be greater than 0"
```

#### S5-TC-008: Validation — net_sqm > 1000 (P1)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"net_sqm": 1001, ...}
Then:  HTTP 422 — Field le=1000 validation hatası
```

#### S5-TC-009: Validation — floor < -2 (P2)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"floor": -3, ...}
Then:  HTTP 422 — Field ge=-2 validation hatası
       (Bodrum kat: -2 ile 0 arası geçerli)
```

#### S5-TC-010: Validation — building_age > 100 (P2)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"building_age": 101, ...}
Then:  HTTP 422 — Field le=100 validation hatası
```

#### S5-TC-011: Validation — room_count = 0 (P2)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"room_count": 0, ...}
Then:  HTTP 422 — Field ge=1 validation hatası
```

#### S5-TC-012: Validation — Boş district (P1)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"district": "", ...}
Then:  HTTP 422 — Field min_length=1 validation hatası
```

#### S5-TC-013: Boundary — net_sqm = 1 (Minimum) (P2)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"net_sqm": 1, "gross_sqm": 1, ...}
Then:  HTTP 200 — Model tahmin yapabilir
       price_per_sqm = estimated_price (1 m2 için)
```

#### S5-TC-014: Boundary — total_floors = 60, floor = 50 (P2)
```
Given: Geçerli JWT
When:  POST /api/v1/valuations {"total_floors": 60, "floor": 50, ...}
Then:  HTTP 200 — Yüksek kat değeri model tarafından işlenir
```

#### S5-TC-015: JWT Eksik — Unauthenticated (P0)
```
Given: Authorization header yok
When:  POST /api/v1/valuations (geçerli body)
Then:  HTTP 401 — Unauthorized
```

#### S5-TC-016: Geçersiz JWT Token (P0)
```
Given: Authorization: Bearer invalid_token_xyz
When:  POST /api/v1/valuations
Then:  HTTP 401 — Invalid token
```

### 2.2 Anomali Tespiti (Z-Score)

**Kaynak Kod:** `anomaly_service.py` — z_score threshold = 2.0

#### S5-TC-017: Anomali Yok — Normal Fiyat (P1)
```
Given: Kadıköy ortalama m2 = 50.000 TL, std = 10.000 TL
When:  check_price_anomaly(predicted=6.000.000, district="Kadikoy", net_sqm=120)
       predicted_sqm = 50.000 → z_score = |50000-50000|/10000 = 0
Then:  is_anomaly = False
       z_score ≈ 0.0
       anomaly_warning = None
```

#### S5-TC-018: Anomali Var — Yüksek Fiyat (P1)
```
Given: Kadıköy ortalama m2 = 50.000, std = 10.000
When:  check_price_anomaly(predicted=9.000.000, district="Kadikoy", net_sqm=120)
       predicted_sqm = 75.000 → z_score = |75000-50000|/10000 = 2.5
Then:  is_anomaly = True
       z_score = 2.5
       anomaly_reason içerir: "yukarida sapma"
```

#### S5-TC-019: Anomali — Düşük Fiyat (P1)
```
Given: Kadıköy ortalama m2 = 50.000, std = 10.000
When:  predicted_sqm = 25.000 → z_score = 2.5
Then:  is_anomaly = True
       anomaly_reason içerir: "asagida sapma"
```

#### S5-TC-020: AreaAnalysis Verisi Yok — Fallback PredictionLog (P2)
```
Given: AreaAnalysis tablosunda ilçe kaydı yok
       PredictionLog'da ilçe için 10 kayıt var
When:  check_price_anomaly(predicted=..., district="BilinmeyenIlce")
Then:  PredictionLog'dan son 50 kayıt ortalaması ile hesaplama yapılır
       source = "prediction_log"
```

#### S5-TC-021: Hiçbir Veri Yok — Anomali Tespit Edilemez (P2)
```
Given: AreaAnalysis VE PredictionLog'da ilçe kaydı yok
When:  check_price_anomaly(predicted=..., district="YeniIlce")
Then:  is_anomaly = False
       z_score = 0.0
       district_avg_sqm_price = 0.0
```

#### S5-TC-022: Std = 0 — Tek Kayıt Fallback (P2)
```
Given: AreaAnalysis'te tek mahalle kaydı var, stddev_pop = 0
When:  check_price_anomaly(...)
Then:  pct_diff / 50.0 formülü ile z-score hesaplanır
       (%100 sapma ≈ z=2)
```

#### S5-TC-023: net_sqm = 0 Guard — Division By Zero (P0)
```
Given: net_sqm = 0 değeri geçerse
When:  predicted_sqm_price = predicted_price / max(net_sqm, 1.0)
Then:  ZeroDivisionError oluşmaz — max(0, 1.0) = 1.0 kullanılır
```

### 2.3 Emsal Bulma (Comparables)

**Kaynak Kod:** `comparable_service.py`, `router.py:find_comparables`

#### S5-TC-024: POST /comparables — Başarılı Emsal Araması (P1)
```
Given: Geçerli JWT, Kadıköy'de aktif ilanlar mevcut
When:  POST /api/v1/valuations/comparables
       {"district": "Kadikoy", "property_type": "Daire", "net_sqm": 120,
        "room_count": 3, "building_age": 5, "lat": 40.99, "lon": 29.02}
Then:  HTTP 200
       - comparables listesi (similarity_score ∈ [0,100])
       - area_stats dict (veya null)
       - total_found ≥ 0
```

#### S5-TC-025: Emsal Bulunamadı — Seyrek Bölge (P2)
```
Given: Çatalca'da sadece 1 aktif ilan
When:  POST /api/v1/valuations/comparables
       {"district": "Catalca", "property_type": "Villa", ...}
Then:  HTTP 200
       - comparables: [] veya az sayıda
       - total_found ≥ 0 (boş olabilir)
```

#### S5-TC-026: Adaptive Radius — min_comparables=3 (P2)
```
Given: Değerleme sırasında emsal aranıyor, yakın bölgede 2 emsal var
When:  find_comparables_enriched(min_comparables=3)
Then:  Arama yarıçapı otomatik genişletilir
       En az 3 emsal bulunana kadar devam eder
```

### 2.4 GET Endpoints — Değerleme Geçmişi

**Kaynak Kod:** `router.py:list_valuations`, `get_valuation`

#### S5-TC-027: GET /valuations — Sayfalama (P1)
```
Given: Ofiste 25 değerleme kaydı var
When:  GET /api/v1/valuations?limit=10&offset=0
Then:  HTTP 200
       - items.length = 10
       - total = 25
       - limit = 10, offset = 0
```

#### S5-TC-028: GET /valuations — Tarih Filtresi (P2)
```
Given: 2026-01 ve 2026-02'de yapılmış değerlemeler
When:  GET /api/v1/valuations?date_from=2026-02-01T00:00:00&date_to=2026-02-28T23:59:59
Then:  HTTP 200
       - Yalnızca Şubat 2026 değerlemeleri döner
```

#### S5-TC-029: GET /valuations — Boş Liste (P3)
```
Given: Yeni oluşturulmuş ofis, hiç değerleme yok
When:  GET /api/v1/valuations
Then:  HTTP 200 — items: [], total: 0
```

#### S5-TC-030: GET /valuations/{id} — Başarılı Detay (P1)
```
Given: Geçerli valuation_id (UUID), aynı ofis
When:  GET /api/v1/valuations/{valuation_id}
Then:  HTTP 200
       - input_features dict (model girdileri)
       - output_data dict (estimated_price, min_price, max_price)
       - confidence, model_version, latency_ms
```

#### S5-TC-031: GET /valuations/{id} — Not Found (P1)
```
Given: Var olmayan veya başka ofisin valuation_id'si
When:  GET /api/v1/valuations/{random_uuid}
Then:  HTTP 404
       - resource = "Degerleme"
```

#### S5-TC-032: GET /valuations/{id}/comparables (P2)
```
Given: Mevcut bir değerleme kaydı
When:  GET /api/v1/valuations/{id}/comparables
Then:  HTTP 200
       - ComparableResult[] listesi
       - Her eleman: property_id, distance_km, price_diff_percent, similarity_score
```

### 2.5 PDF Rapor

**Kaynak Kod:** `pdf_router.py`, `services/pdf_service.py`

#### S5-TC-033: GET /valuations/{id}/pdf — Başarılı PDF (P1)
```
Given: Mevcut valuation_id
When:  GET /api/v1/valuations/{id}/pdf
Then:  HTTP 200
       - Content-Type: application/pdf
       - Content-Disposition: attachment; filename="degerleme_*.pdf"
       - PDF içeriği: fiyat, emsal tablo, güven aralığı, tarih
```

#### S5-TC-034: PDF — Değerleme Bulunamadı (P2)
```
Given: Geçersiz valuation_id
When:  GET /api/v1/valuations/{invalid_id}/pdf
Then:  HTTP 404
```

### 2.6 Drift Monitor

**Kaynak Kod:** `drift_router.py`

#### S5-TC-035: GET /drift/monitor — Model Drift İstatistikleri (P2)
```
Given: Son 30 günde 100+ değerleme yapılmış
When:  GET /api/v1/valuations/drift/monitor
Then:  HTTP 200
       - Drift metrikleri (MAPE, R2 değişim)
```

#### S5-TC-036: GET /drift/histogram (P3)
```
Given: Yeterli değerleme verisi
When:  GET /api/v1/valuations/drift/histogram
Then:  HTTP 200 — Histogram bucket verileri
```

### 2.7 QuotaService Detay

**Kaynak Kod:** `quota_service.py`

#### S5-TC-037: Yeni Ay — Kota Sıfırlanması (P1)
```
Given: Şubat 2026 dolu, Mart 2026 başladı
When:  get_or_create_quota(db, office_id, "starter")
Then:  Yeni UsageQuota kaydı oluşur
       - valuations_used = 0
       - period_start = 2026-03-01
       - period_end = 2026-03-31
```

#### S5-TC-038: Kota Tipi — Staging (P2)
```
Given: Starter plan, staging_used = 10
When:  check_quota(db, office_id, "starter", QuotaType.STAGING)
Then:  (False, 10, 10) — Staging kota dolu (Starter limit = 10)
```

#### S5-TC-039: Kredi Ekleme — Negatif Miktar (P2)
```
Given: Geçerli ofis
When:  add_credits(db, office_id, "starter", amount=-5)
Then:  ValueError: "Kredi miktari 0'dan buyuk olmalidir."
```

#### S5-TC-040: Kredi Kullanım — Bakiye = 0 (P1)
```
Given: credit_balance = 0
When:  use_credit(db, office_id, "starter", QuotaType.VALUATION)
Then:  ValueError: "Yetersiz kredi bakiyesi."
```

#### S5-TC-041: Frontend — /degerleme Sayfası Yükleme (P1)
```
Given: Kullanıcı login olmuş
When:  /degerleme sayfasına git
Then:  ValuationForm render edilir
       - Tüm alanlar (district, neighborhood, vs.) görünür
       - QuotaInfo bileşeni kalan hakkı gösterir
```

#### S5-TC-042: Frontend — Değerleme Sonuç Gösterimi (P2)
```
Given: Değerleme başarıyla tamamlandı
When:  ValuationResult render edilir
Then:  - estimated_price formatlanmış TL olarak görünür
       - Güven aralığı (min-max) bar chart
       - Emsal listesi (ComparablesList)
       - anomaly_warning varsa sarı uyarı banner
```

---

## 3. S6 — Bölge Analizi

### 3.1 Bölge Listesi ve Detay

**Kaynak Kod:** `modules/areas/router.py`, `earthquake/router.py`, `maps/router.py`

#### S6-TC-001: GET /areas — Bölge Listesi (P1)
```
Given: Geçerli JWT, AreaAnalysis'te 39 İstanbul ilçesi var
When:  GET /api/v1/areas
Then:  HTTP 200
       - items listesi (ilçe bazlı)
       - Her item: district, avg_price_sqm_sale, avg_price_sqm_rent, listing_count
```

#### S6-TC-002: GET /areas/{code} — Bölge Detay (P1)
```
Given: code = "kadikoy"
When:  GET /api/v1/areas/kadikoy
Then:  HTTP 200
       - AreaDetailResponse
       - investment_metrics: kira_verimi, amortisman_yil
       - age_distribution dict (varsa)
```

#### S6-TC-003: GET /areas/{code} — Bilinmeyen Bölge (P1)
```
Given: code = "bilinmeyen"
When:  GET /api/v1/areas/bilinmeyen
Then:  HTTP 404 — NotFoundError
```

#### S6-TC-004: Yatırım Metrikleri — Sıfır Fiyat (P2)
```
Given: avg_sale = 0 veya avg_rent = 0
When:  _calculate_investment_metrics(avg_sale=0, avg_rent=5000)
Then:  InvestmentMetrics() — boş (kira_verimi=None, amortisman_yil=None)
       ZeroDivisionError oluşmaz
```

#### S6-TC-005: Yatırım Metrikleri — Geçerli Hesaplama (P1)
```
Given: avg_sale = 50000 TL/m2, avg_rent = 200 TL/m2
When:  _calculate_investment_metrics(50000, 200)
Then:  kira_verimi = (200*12/50000)*100 = 4.8%
       amortisman_yil = 50000/(200*12) = 20.8 yıl
```

### 3.2 Demografik Veriler

#### S6-TC-006: GET /areas/{code}/demographics (P1)
```
Given: code = "besiktas", demografik veri seed edilmiş
When:  GET /api/v1/areas/besiktas/demographics
Then:  HTTP 200
       - DemographicsResponse: nüfus, yaş dağılımı, eğitim, gelir
```

#### S6-TC-007: Demografik Veri Yok (P2)
```
Given: İlçe için demografik veri girilmemiş
When:  GET /api/v1/areas/esenyurt/demographics
Then:  HTTP 200 veya 404 (veri yoksa uygun yanıt)
```

### 3.3 Fiyat Trendleri

#### S6-TC-008: GET /areas/{code}/price-history (P1)
```
Given: PriceHistory tablosunda Kadıköy için 12 aylık veri
When:  GET /api/v1/areas/kadikoy/price-history
Then:  HTTP 200
       - PriceTrendResponse: trend_items listesi
       - Her item: period, avg_sqm_price, listing_count
```

#### S6-TC-009: Trend Verisi Yetersiz (P3)
```
Given: İlçe için sadece 1 ay veri
When:  GET /api/v1/areas/{code}/price-history
Then:  HTTP 200 — Tek elemanlı trend listesi (trend hesaplanamaz ama veri döner)
```

### 3.4 Bölge Karşılaştırma

#### S6-TC-010: GET /areas/compare — 3 İlçe (P1)
```
Given: Geçerli JWT
When:  GET /api/v1/areas/compare?districts=kadikoy,besiktas,uskudar
Then:  HTTP 200
       - CompareResponse: 3 CompareAreaItem
       - Her item: district, avg_price_sqm, trend, investment_score
```

#### S6-TC-011: Compare — Tek İlçe (P2)
```
Given: Sadece 1 ilçe parametre
When:  GET /api/v1/areas/compare?districts=kadikoy
Then:  HTTP 422 veya 200 tek eleman (validation kuralına bağlı)
```

#### S6-TC-012: Compare — Geçersiz İlçe İsmi (P2)
```
Given: Var olmayan ilçe
When:  GET /api/v1/areas/compare?districts=kadikoy,xyz,besiktas
Then:  HTTP 200 — xyz için null/boş değerler veya HTTP 400
```

### 3.5 Deprem Risk

**Kaynak Kod:** `earthquake/router.py`, `earthquake/service.py`, `building_score.py`

#### S6-TC-013: GET /earthquake/{lat}/{lon} — Başarılı (P0)
```
Given: İstanbul koordinatları (lat=41.0082, lon=28.9784)
When:  GET /api/v1/earthquake/41.0082/28.9784
Then:  HTTP 200
       - EarthquakeRiskResponse
       - risk_level: "dusuk"|"orta"|"yuksek"|"cok_yuksek"
       - pga, pgv değerleri
       - building_score (varsa)
```

#### S6-TC-014: Deprem Risk — İstanbul Dışı Koordinat (P2)
```
Given: Ankara koordinatları (lat=39.93, lon=32.86)
When:  GET /api/v1/earthquake/39.93/32.86
Then:  HTTP 200 veya 404 — Veri yoksa uygun yanıt
```

#### S6-TC-015: Deprem Risk — Geçersiz Koordinat (P1)
```
Given: Geçersiz enlem
When:  GET /api/v1/earthquake/95.0/28.0
Then:  HTTP 422 — lat ge=-90, le=90 validation hatası
```

#### S6-TC-016: Building Score Hesaplama (P2)
```
Given: Bina bilgileri: kat=10, yaş=30, yapı_tipi="betonarme"
When:  calculate_building_score(...)
Then:  Skor 0-100 arasında, yaş ve kat sayısı risk artırıcı
```

### 3.6 Harita

**Kaynak Kod:** `maps/router.py`

#### S6-TC-017: GET /maps/properties — Property Markers (P1)
```
Given: Geçerli JWT, 50 aktif ilan
When:  GET /api/v1/maps/properties
Then:  HTTP 200 — PropertyMapResponse
       - GeoJSON veya marker listesi
       - Her marker: lat, lon, price, property_type
```

#### S6-TC-018: GET /maps/heatmap — Fiyat Isı Haritası (P2)
```
Given: Geçerli JWT
When:  GET /api/v1/maps/heatmap
Then:  HTTP 200 — HeatmapResponse
       - Heatmap grid verileri
```

### 3.7 Frontend — Harita & POI

#### S6-TC-019: MapContainer — MapLibre Yükleme (P1)
```
Given: /maps sayfası açıldı
When:  MapContainer render
Then:  MapLibre GL harita yüklenir
       - İstanbul merkezi görünüm
       - LayerControl bileşeni görünür
```

#### S6-TC-020: POI Layer — Hastane (P2)
```
Given: Harita yüklendi
When:  LayerControl'den "Hastaneler" aktif edilir
Then:  istanbul_hospitals.json verisi haritada pin olarak görünür
       - PoiPopup tıklama ile açılır
```

#### S6-TC-021: POI Layer — Metro (P2)
```
Given: Harita yüklendi
When:  LayerControl'den "Metro" aktif edilir
Then:  istanbul_metro.json verisi haritada görünür
```

#### S6-TC-022: POI Layer — Okullar (P2)
```
Given: Harita yüklendi
When:  "Okullar" katmanı aktif
Then:  istanbul_schools.json verisi görünür
```

### 3.8 Frontend — Dashboard Bileşenleri

#### S6-TC-023: DepremRiskCard (P1)
```
Given: /areas sayfasında ilçe seçildi
When:  deprem-risk-card render
Then:  Risk seviyesi renk kodlu badge (yeşil/sarı/kırmızı)
       PGA/PGV değerleri görünür
```

#### S6-TC-024: PriceTrendChart (P2)
```
Given: 12 aylık trend verisi
When:  price-trend-chart render (Recharts)
Then:  Line chart görünür, tooltip ile değerler
       X: aylar, Y: TL/m2
```

#### S6-TC-025: Bölge Karşılaştırma Sayfası — 3 İlçe Seçimi (P1)
```
Given: /areas/compare sayfası
When:  3 ilçe seçilir (Kadıköy, Beşiktaş, Üsküdar)
Then:  Yanyana karşılaştırma kartları görünür
       m2 fiyat, trend, yatırım skoru karşılaştırılır
```

### 3.9 Data Freshness

#### S6-TC-026: DataFreshnessBadge (P3)
```
Given: Area verisi 24 saat önce güncellendi
When:  data-freshness-badge render
Then:  "Güncel" yeşil badge (< 24h)
```

#### S6-TC-027: DataFreshnessBadge — Eski Veri (P3)
```
Given: Area verisi 7 gün önce güncellendi
When:  data-freshness-badge render
Then:  "Güncelleniyor" sarı badge (> 24h)
```

---

## 4. S7 — CRM

### 4.1 Customer CRUD

**Kaynak Kod:** `modules/customers/router.py`, `service.py`, `schemas.py`

#### S7-TC-001: POST /customers — Başarılı Oluşturma (P0)
```
Given: Geçerli JWT, müşteri kotası müsait
When:  POST /api/v1/customers
       {
         "full_name": "Ahmet Yılmaz",
         "email": "ahmet@example.com",
         "phone": "+905551234567",
         "customer_type": "buyer",
         "budget_min": 2000000,
         "budget_max": 5000000,
         "desired_districts": ["Kadikoy", "Besiktas"],
         "desired_rooms": "3+1",
         "desired_area_min": 100,
         "desired_area_max": 150,
         "notes": "Acil arıyor"
       }
Then:  HTTP 201
       - CustomerResponse: id (UUID), full_name, lead_status = "cold"
       - office_id otomatik JWT'den atanır
```

#### S7-TC-002: POST /customers — Kota Aşımı (P1)
```
Given: Starter plan, 50 müşteri oluşturulmuş (customer quota = 50)
When:  POST /api/v1/customers (geçerli body)
Then:  HTTP 429 — Kota aşıldı
```

#### S7-TC-003: GET /customers — Sayfalama + Filtre (P1)
```
Given: 30 müşteri, 10'u buyer, 20'si seller
When:  GET /api/v1/customers?customer_type=buyer&limit=5&offset=0
Then:  HTTP 200
       - items.length = 5
       - total = 10 (sadece buyer)
```

#### S7-TC-004: GET /customers — Gelişmiş JSONB Arama (P1)
```
Given: desired_districts JSONB alanında ["Kadikoy", "Besiktas"] olan müşteriler
When:  GET /api/v1/customers?search=Kadikoy
Then:  HTTP 200 — JSONB contains veya full-text search ile eşleşenler döner
```

#### S7-TC-005: GET /customers/{id} — Detay (P1)
```
Given: Var olan müşteri UUID
When:  GET /api/v1/customers/{id}
Then:  HTTP 200
       - Tüm alanlar: full_name, email, phone, budget_*, desired_*
       - lead_status, customer_type, created_at
```

#### S7-TC-006: GET /customers/{id} — Başka Ofisin Müşterisi (P0)
```
Given: Müşteri farklı ofise ait (RLS izolasyonu)
When:  GET /api/v1/customers/{other_office_customer_id}
Then:  HTTP 404 — RLS engeller, kayıt görünmez
```

#### S7-TC-007: PATCH /customers/{id} — Güncelleme (P1)
```
Given: Var olan müşteri
When:  PATCH /api/v1/customers/{id}
       {"budget_max": 6000000, "desired_rooms": "4+1"}
Then:  HTTP 200
       - budget_max = 6000000
       - desired_rooms = "4+1"
       - updated_at güncellenir
```

#### S7-TC-008: DELETE /customers/{id} — Soft Delete (P1)
```
Given: Var olan müşteri
When:  DELETE /api/v1/customers/{id}
Then:  HTTP 200/204
       - DB'de is_deleted = True (soft delete)
       - GET /customers listesinde görünmez
```

### 4.2 Lead Status

**Kaynak Kod:** `router.py:update_lead_status` — 5 durum: cold, warm, hot, converted, lost

#### S7-TC-009: PATCH /customers/{id}/status — cold → warm (P1)
```
Given: Müşteri lead_status = "cold"
When:  PATCH /api/v1/customers/{id}/status
       {"status": "warm"}
Then:  HTTP 200 — lead_status = "warm"
```

#### S7-TC-010: Status — warm → hot → converted (P1)
```
Given: Müşteri lead_status = "warm"
When:  PATCH → {"status": "hot"}, sonra PATCH → {"status": "converted"}
Then:  Her adımda başarılı güncelleme
```

#### S7-TC-011: Status — Geçersiz Değer (P2)
```
Given: Geçerli müşteri
When:  PATCH /customers/{id}/status {"status": "super_hot"}
Then:  HTTP 422 — Validation hatası (enum: cold|warm|hot|converted|lost)
```

#### S7-TC-012: Status — lost → warm (Geri Dönüş) (P2)
```
Given: lead_status = "lost"
When:  PATCH → {"status": "warm"}
Then:  HTTP 200 — Geri dönüş izinli (iş kurallarına göre)
```

### 4.3 Notlar

**Kaynak Kod:** `router.py:create_note`, `list_notes` — CustomerNote modeli

#### S7-TC-013: POST /customers/{id}/notes — Not Ekle (P1)
```
Given: Var olan müşteri
When:  POST /api/v1/customers/{id}/notes
       {"content": "Kadıköy 3+1 ilanlara baktık, beğenmedi."}
Then:  HTTP 201
       - NoteResponse: id, content, created_at
       - customer_id = müşteri UUID
```

#### S7-TC-014: GET /customers/{id}/notes (P1)
```
Given: Müşteriye 3 not eklenmiş
When:  GET /api/v1/customers/{id}/notes
Then:  HTTP 200
       - NoteListResponse: 3 not, sıralama created_at DESC
```

#### S7-TC-015: Not — Boş İçerik (P2)
```
Given: Var olan müşteri
When:  POST /customers/{id}/notes {"content": ""}
Then:  HTTP 422 — min_length=1 validation hatası
```

### 4.4 Timeline

#### S7-TC-016: GET /customers/{id}/timeline — Birleşik Akış (P1)
```
Given: Müşteri oluşturuldu, not eklendi, status güncellendi, eşleşme bulundu
When:  GET /api/v1/customers/{id}/timeline
Then:  HTTP 200
       - TimelineResponse: kronolojik olaylar listesi
       - Her olay: type (note|status_change|match), timestamp, data
```

### 4.5 Eşleştirme Algoritması

**Kaynak Kod:** `matches/matching_service.py` — 4 kriter, ağırlıklar, eşik 70

#### S7-TC-017: Tam Uyum — Skor 100 (P0)
```
Given: İlan: Kadıköy, 3.000.000 TL, 3+1, 120 m2
       Müşteri: budget=[2M,4M], districts=["Kadikoy"], rooms="3+1", area=[100,150]
When:  calculate_match_score(property, customer)
Then:  price_score = 100, location_score = 100, room_score = 100, area_score = 100
       final_score = 100.0
       Ağırlıklar: price=0.30, location=0.30, room=0.20, area=0.20
```

#### S7-TC-018: Kısmi Uyum — Skor 70 (Eşik) (P1)
```
Given: İlan: Kadıköy, 3.500.000 TL, 2+1, 90 m2
       Müşteri: budget=[2M,3M], districts=["Kadikoy"], rooms="3+1", area=[100,150]
When:  calculate_match_score(...)
Then:  price_score < 100 (bütçe aşımı ama ±%20 içinde)
       location_score = 100 (Kadıköy eşleşiyor)
       room_score = 50 (1 oda fark)
       area_score < 100 (90 < 100 min)
       final_score ≥ 70 → Eşleşme oluşur
```

#### S7-TC-019: Düşük Skor — Eşik Altı (P1)
```
Given: İlan: Çatalca, 10.000.000 TL, 5+1, 300 m2
       Müşteri: budget=[1M,2M], districts=["Kadikoy"], rooms="2+1", area=[60,80]
When:  calculate_match_score(...)
Then:  price_score ≈ 0 (çok üstünde)
       location_score = 0 (farklı ilçe)
       room_score = 0 (3 oda fark)
       area_score = 0 (çok büyük)
       final_score < 70 → Eşleşme oluşmaz
```

#### S7-TC-020: Fiyat Skoru — Budget ±%20 Sınır (P1)
```
Given: budget_max = 3.000.000
When:  property.price = 3.600.000 (= max * 1.2)
Then:  price_score = 0.0 (üst sınır)

When:  property.price = 3.300.000 (< max * 1.2)
Then:  0 < price_score < 100 (lineer interpolasyon)
```

#### S7-TC-021: Konum Skoru — Case Insensitive (P2)
```
Given: property.district = "Kadıköy"
       customer.desired_districts = ["kadikoy", "BESIKTAS"]
When:  _calculate_location_score(...)
Then:  location_score = 100 (case-insensitive match)
```

#### S7-TC-022: Oda Skoru — ±1 Fark (P2)
```
Given: property.rooms = "3+1", customer.desired_rooms = "2+1"
When:  _calculate_room_score("3+1", "2+1")
Then:  prop_count=3, desired=2, diff=1
       room_score = 50.0
```

#### S7-TC-023: Oda Skoru — ±2 Fark (P2)
```
Given: property.rooms = "4+1", customer.desired_rooms = "2+1"
When:  _calculate_room_score("4+1", "2+1")
Then:  diff=2 → room_score = 20.0
```

#### S7-TC-024: Oda Parsing — Edge Cases (P2)
```
When:  parse_room_count("3+1") → 3
       parse_room_count("2+0") → 2
       parse_room_count("4")   → 4
       parse_room_count(None)  → None
       parse_room_count("")    → None
```

#### S7-TC-025: Eksik Kriter — Ağırlık Normalize (P1)
```
Given: Müşteri sadece budget ve district belirtmiş (rooms=None, area=None)
When:  calculate_match_score(...)
Then:  Aktif kriterler: price, location
       Normalize ağırlıklar: price=0.5, location=0.5
       room_score=None, area_score=None (atlandı)
```

#### S7-TC-026: Tüm Kriterler Eksik — Skor 0 (P2)
```
Given: Müşteri hiçbir tercih belirtmemiş
When:  calculate_match_score(...)
Then:  active_criteria = {}
       final_score = 0.0, weights_used = {}
```

### 4.6 Eşleştirme Endpointleri

**Kaynak Kod:** `matches/router.py`, `matches/tasks.py`

#### S7-TC-027: POST /matches/run/property/{id} — İlan Eşleştir (P0)
```
Given: Aktif ilan, ofiste 10 buyer müşteri
When:  POST /api/v1/matches/run/property/{property_id}
Then:  HTTP 200
       - Eşleştirme çalıştı
       - Skor ≥ 70 olan eşleşmeler PropertyCustomerMatch tablosuna kaydedildi
       - ON CONFLICT → skor güncellendi
```

#### S7-TC-028: POST /matches/run/customer/{id} — Müşteri Eşleştir (P1)
```
Given: buyer müşteri, ofiste 20 aktif ilan
When:  POST /api/v1/matches/run/customer/{customer_id}
Then:  HTTP 200 — Uyumlu ilanlar eşleştirildi
```

#### S7-TC-029: Eşleştirme — İlan Bulunamadı (P1)
```
Given: Geçersiz property_id veya inactive ilan
When:  POST /api/v1/matches/run/property/{invalid_id}
Then:  HTTP 404 — "Aktif ilan bulunamadi"
```

#### S7-TC-030: Eşleştirme — Seller Müşteri (P2)
```
Given: customer_type = "seller" (buyer/renter değil)
When:  POST /api/v1/matches/run/customer/{seller_id}
Then:  HTTP 404 — "Musteri (buyer/renter) bulunamadi"
```

#### S7-TC-031: GET /matches — Eşleşme Listesi (P1)
```
Given: 5 eşleşme kaydı
When:  GET /api/v1/matches
Then:  HTTP 200 — 5 MatchResponse (score, status, property, customer)
```

#### S7-TC-032: PATCH /matches/{id}/status — Durum Güncelleme (P1)
```
Given: Match status = "pending"
When:  PATCH /api/v1/matches/{id}/status {"status": "interested"}
Then:  HTTP 200 — status = "interested"
       (geçerli statüler: pending, interested, passed, contacted, converted)
```

#### S7-TC-033: Celery Task — Async Eşleştirme (P1)
```
Given: İlan oluşturuldu
When:  trigger_matching_for_property.delay(property_id, office_id) çağrılır
Then:  Celery worker eşleştirme çalıştırır
       Sonuç PropertyCustomerMatch tablosuna yazılır
```

### 4.7 Frontend — CRM

#### S7-TC-034: /musteri Sayfası — Müşteri Listesi (P1)
```
Given: /dashboard/customers sayfası
When:  Sayfa yüklenir
Then:  customer-table render edilir
       - Filtreler: customer_type, lead_status
       - Arama çubuğu aktif
       - Sayfalama kontrolleri
```

#### S7-TC-035: Müşteri Detay — Notes Tab (P1)
```
Given: /dashboard/customers/{id} sayfası
When:  "Notlar" sekmesine tıkla
Then:  customer-notes bileşeni
       - Not ekleme formu
       - Mevcut notlar listesi (tarih sıralı)
```

#### S7-TC-036: Pipeline Görünümü (P2)
```
Given: /dashboard/customers sayfası
When:  Pipeline görünümüne geç
Then:  customer-pipeline bileşeni
       - 5 kolon: cold, warm, hot, converted, lost
       - Müşteri kartları sürükle-bırak (varsa)
```

#### S7-TC-037: Quick Add Customer Modal (P2)
```
Given: Herhangi bir dashboard sayfası
When:  "Hızlı Müşteri Ekle" butonuna tıkla
Then:  quick-add-customer modal açılır
       - Minimal form (isim, telefon, tip)
       - Kayıt sonrası liste güncellenir
```

#### S7-TC-038: Match Card Görünümü (P2)
```
Given: /dashboard/customers/{id} detay sayfası
When:  "Eşleşmeler" sekmesine tıkla
Then:  match-list + match-card bileşenleri
       - Skor badge (yeşil ≥80, sarı ≥70)
       - İlan özeti (fiyat, konum, m2)
```

---

## 5. S8 — İlan Asistanı

### 5.1 AI Metin Üretimi

**Kaynak Kod:** `listings/listing_assistant_router.py`, `listing_assistant_service.py`, `openai_service.py`

#### S8-TC-001: POST /assistant/generate-title — Başlık Üretimi (P1)
```
Given: Geçerli JWT, OpenAI API key tanımlı
When:  POST /api/v1/listings/assistant/generate-title
       {"property_type": "Daire", "district": "Kadikoy", "rooms": "3+1",
        "net_sqm": 120, "tone": "professional"}
Then:  HTTP 200
       - AI tarafından üretilmiş başlık (SEO uyumlu)
       - title string, min 10 karakter
```

#### S8-TC-002: POST /assistant/generate-description — Açıklama Üretimi (P1)
```
Given: Geçerli JWT, property bilgileri
When:  POST /api/v1/listings/assistant/generate-description
       {"property_type": "Daire", "district": "Kadikoy", ..., "tone": "friendly"}
Then:  HTTP 200
       - AI üretilmiş ilan açıklaması
       - Ton "friendly" (samimi anlatım)
       - SEO anahtar kelimeler içerir
```

#### S8-TC-003: 3 Ton Seçeneği (P1)
```
Given: Tone parametreleri
When:  tone = "professional" → Resmi, kurumsal
       tone = "friendly"     → Samimi, sıcak
       tone = "luxury"       → Lüks, prestij
Then:  Her ton için farklı metin stili üretilir
```

#### S8-TC-004: OpenAI API Key Yok — Mock Response (P2)
```
Given: OPENAI_API_KEY tanımlı değil
When:  POST /assistant/generate-title
Then:  HTTP 200 — Mock metin döner (geliştirme modu)
       openai_service._get_client() → None, _MOCK_TEXT döner
```

#### S8-TC-005: OpenAI Rate Limit (P1)
```
Given: OpenAI API rate limit aşıldı
When:  POST /assistant/generate-description
Then:  3 retry (exponential backoff), başarısızsa:
       OpenAIRateLimitError fırlatılır
       HTTP 503 veya 429
```

#### S8-TC-006: OpenAI Content Filter (P2)
```
Given: Uygunsuz prompt içeriği
When:  POST /assistant/generate-description
Then:  OpenAIContentFilterError — retry yapılmaz (non-retryable)
       HTTP 400/422 — İçerik reddedildi mesajı
```

#### S8-TC-007: GET /assistant/suggestions (P2)
```
Given: Geçerli JWT
When:  GET /api/v1/listings/assistant/suggestions
Then:  HTTP 200 — İlan iyileştirme önerileri
```

### 5.2 Virtual Staging (Sahneleme)

**Kaynak Kod:** `listings/staging_router.py`, `staging_service.py`

#### S8-TC-008: POST /listings/staging — Sahneleme Uygula (P1)
```
Given: Geçerli JWT, staging kotası müsait, yüklenmiş fotoğraf
When:  POST /api/v1/listings/staging
       {"photo_id": "uuid", "style": "modern_minimalist"}
Then:  HTTP 200
       - OpenAI edit_image ile sahneleme uygulanmış
       - Sonuç MinIO'ya kaydedilmiş
       - URL döner
```

#### S8-TC-009: GET /listings/staging-styles — Public Stiller (P2)
```
Given: Public endpoint (JWT gereksiz)
When:  GET /api/v1/listings/staging-styles
Then:  HTTP 200
       - 6 stil: modern_minimalist, scandinavian, industrial, vb.
       - Her stil: id, name, description, preview_url
```

#### S8-TC-010: Staging Kota — Starter Plan (P1)
```
Given: Starter plan, staging_used = 10 (limit=10)
When:  POST /listings/staging
Then:  HTTP 429 — Staging kotası dolu
       Starter: 10, Pro: 50, Elite: 200
```

#### S8-TC-011: POST /listings/apply-staging — Stili Uygula (P2)
```
Given: Seçilmiş stil ve fotoğraf
When:  POST /api/v1/listings/apply-staging
Then:  HTTP 200 — Sonuç görseli
```

### 5.3 Fotoğraf Yönetimi

**Kaynak Kod:** `listings/photo_router.py`, `photo_service.py`, `core/storage.py`

#### S8-TC-012: POST /listings/photos — Fotoğraf Yükleme (P0)
```
Given: Geçerli JWT, fotoğraf kotası müsait
When:  POST /api/v1/listings/photos (multipart/form-data)
       file: property_photo.jpg (2MB)
Then:  HTTP 201
       - MinIO'ya yüklendi
       - photo_id, url, thumbnail_url döner
```

#### S8-TC-013: Fotoğraf — Boyut Limiti (P1)
```
Given: 15MB fotoğraf
When:  POST /listings/photos
Then:  HTTP 413 veya 422 — Dosya boyutu sınırı aşıldı
```

#### S8-TC-014: Fotoğraf — Geçersiz Format (P2)
```
Given: .exe dosyası upload denemesi
When:  POST /listings/photos
Then:  HTTP 422 — Yalnızca JPEG, PNG, WebP desteklenir
```

#### S8-TC-015: POST /listings/photos/process — Fotoğraf İşleme (P2)
```
Given: Yüklenmiş fotoğraf
When:  POST /api/v1/listings/photos/process
Then:  HTTP 200 — Resize, optimize, thumbnail oluşturma
```

#### S8-TC-016: DELETE /listings/photos/{id} (P2)
```
Given: Var olan fotoğraf
When:  DELETE /api/v1/listings/photos/{photo_id}
Then:  HTTP 200/204 — MinIO'dan ve DB'den silinir
```

#### S8-TC-017: Fotoğraf Kota — Starter Plan (P2)
```
Given: Starter plan, photos_used = 100 (limit=100)
When:  POST /listings/photos
Then:  HTTP 429 — Fotoğraf kotası dolu
       Pro: 500, Elite: sınırsız
```

### 5.4 Portal Export

**Kaynak Kod:** `listings/portal_export_router.py`, `portal_export_service.py`

#### S8-TC-018: POST /listings/export — Portal Export (P1)
```
Given: Geçerli JWT, aktif ilan
When:  POST /api/v1/listings/export
       {"property_id": "uuid", "portal": "sahibinden"}
Then:  HTTP 200 — Export başarılı, dış portal formatında
```

#### S8-TC-019: GET /listings/portals — Portal Listesi (P3)
```
Given: Public endpoint
When:  GET /api/v1/listings/portals
Then:  HTTP 200 — Desteklenen portal listesi
```

### 5.5 Frontend — İlan Asistanı

#### S8-TC-020: /listings Sayfası — 3 Tab Yapısı (P1)
```
Given: /listings sayfası
When:  Sayfa yüklenir
Then:  3 tab görünür:
       1. Metin Oluşturucu (listing-text-form)
       2. Sanal Sahneleme (virtual-staging-tab)
       3. Portal Export (portal-export-tab)
```

#### S8-TC-021: Metin Oluşturucu — Form + Sonuç (P1)
```
Given: "Metin Oluşturucu" sekmesi aktif
When:  Form doldurulur ve "Oluştur" tıklanır
Then:  AI ile metin üretilir
       listing-text-result bileşeni sonucu gösterir
       "Kopyala" butonu ile panoya kopyalanır
```

#### S8-TC-022: Sanal Sahneleme Tab (P2)
```
Given: "Sanal Sahneleme" sekmesi
When:  Fotoğraf seçilir, stil seçilir, "Uygula" tıklanır
Then:  Before/After karşılaştırma görünümü
```

---

## 6. S9 — Vitrin + Kredi Hesaplama

### 6.1 Showcase CRUD

**Kaynak Kod:** `modules/showcases/router.py`, `service.py`, `schemas.py`

#### S9-TC-001: POST /showcases — Vitrin Oluştur (P0)
```
Given: Geçerli JWT
When:  POST /api/v1/showcases
       {"title": "Kadıköy Seçme İlanlar", "description": "...",
        "property_ids": ["uuid1", "uuid2"], "theme": {"primary_color": "#2563EB"}}
Then:  HTTP 201
       - ShowcaseResponse: id, slug (auto-generated), title
       - office_id JWT'den atanır
```

#### S9-TC-002: GET /showcases — Kendi Vitrinleri (P1)
```
Given: Ofiste 3 vitrin var
When:  GET /api/v1/showcases
Then:  HTTP 200 — ShowcaseListResponse: 3 ShowcaseListItem
```

#### S9-TC-003: GET /showcases/{id} — Vitrin Detay (P1)
```
Given: Var olan vitrin
When:  GET /api/v1/showcases/{id}
Then:  HTTP 200
       - ShowcaseResponse: title, description, properties[], theme
       - properties: PropertySummary listesi
```

#### S9-TC-004: PUT /showcases/{id} — Güncelleme (P1)
```
Given: Var olan vitrin
When:  PUT /api/v1/showcases/{id}
       {"title": "Güncellenmiş Başlık", "property_ids": ["uuid1", "uuid3"]}
Then:  HTTP 200 — Başlık ve ilanlar güncellendi
```

#### S9-TC-005: DELETE /showcases/{id} (P2)
```
Given: Var olan vitrin
When:  DELETE /api/v1/showcases/{id}
Then:  HTTP 200/204 — Vitrin silindi
```

### 6.2 Public Showcase

#### S9-TC-006: GET /showcases/public/{slug} — Public SSR (P0)
```
Given: slug = "kadikoy-secme-ilanlar" (public erişim)
When:  GET /api/v1/showcases/public/kadikoy-secme-ilanlar
Then:  HTTP 200 (JWT gerektirmez)
       - ShowcasePublicResponse
       - İlan listesi (fotoğraflar, fiyatlar)
       - Agent bilgileri
```

#### S9-TC-007: Public — Geçersiz Slug (P2)
```
Given: Var olmayan slug
When:  GET /api/v1/showcases/public/invalid-slug
Then:  HTTP 404
```

#### S9-TC-008: POST /showcases/public/{slug}/view — Görüntülenme (P2)
```
Given: Geçerli slug
When:  POST /api/v1/showcases/public/{slug}/view
Then:  HTTP 200 — view_count += 1
       Analytics kaydı oluşur
```

### 6.3 WhatsApp Entegrasyonu

#### S9-TC-009: GET /showcases/public/{slug}/whatsapp — Click-to-Chat (P1)
```
Given: Geçerli slug, agent telefon numarası tanımlı
When:  GET /api/v1/showcases/public/{slug}/whatsapp
Then:  HTTP 200
       - WhatsAppLinkResponse
       - url: "https://wa.me/905551234567?text=..."
       - Önceden hazırlanmış mesaj
```

#### S9-TC-010: WhatsApp — Plan Kontrolü (P2)
```
Given: Starter plan (whatsapp_click_to_chat = true)
When:  WhatsApp link talebi
Then:  Başarılı — Starter'da click-to-chat aktif
       Elite'de ek olarak Cloud API aktif
```

### 6.4 Paylaşım Ağı

#### S9-TC-011: Shared Showcases Listesi (P2)
```
Given: Ofisler arası paylaşılan vitrinler
When:  GET /api/v1/showcases (shared parametre ile)
Then:  HTTP 200 — SharedShowcaseListResponse
```

### 6.5 Kredi Hesaplayıcı

**Kaynak Kod:** `modules/calculator/calculator_router.py`, `calculator_service.py`, `bank_rates.py`

#### S9-TC-012: POST /calculator/calculate — Annuity Hesaplama (P0)
```
Given: Geçerli JWT
When:  POST /api/v1/calculator/calculate
       {"amount": 3000000, "term_months": 120, "interest_rate": 2.5,
        "loan_type": "konut"}
Then:  HTTP 200
       - monthly_payment > 0 (annuity formül)
       - total_payment = monthly_payment * term_months
       - total_interest = total_payment - amount
       - amortization_table: 120 satır (anapara, faiz, kalan)
```

#### S9-TC-013: Annuity Formül Doğrulama (P0)
```
Given: amount=1.000.000, rate=2.0%/ay, term=12 ay
When:  calculate
Then:  monthly = amount * rate / (1 - (1+rate)^(-n))
       Beklenen: ≈ 94.559,61 TL
       total_payment ≈ 1.134.715,32 TL
       total_interest ≈ 134.715,32 TL
```

#### S9-TC-014: GET /calculator/rates — Banka Faiz Oranları (P1)
```
Given: Geçerli JWT
When:  GET /api/v1/calculator/rates
Then:  HTTP 200
       - 6 banka: İş, Garanti, Yapı Kredi, Ziraat, Halkbank, Vakıfbank (örnekler)
       - Her banka: name, interest_rate, max_term, min_amount
```

#### S9-TC-015: POST /calculator/scenarios — Çoklu Senaryo (P1)
```
Given: Geçerli JWT
When:  POST /api/v1/calculator/scenarios
       [{"amount": 3M, "term": 120, "rate": 2.5},
        {"amount": 3M, "term": 180, "rate": 2.5},
        {"amount": 3M, "term": 120, "rate": 3.0}]
Then:  HTTP 200 — 3 ayrı hesaplama sonucu
       Karşılaştırma tablosu oluşturulabilir
```

#### S9-TC-016: Hesaplama — Sıfır Faiz Oranı (P2)
```
Given: interest_rate = 0
When:  POST /calculator/calculate
Then:  monthly_payment = amount / term_months
       total_interest = 0
       (ZeroDivisionError oluşmamalı)
```

#### S9-TC-017: Hesaplama — Negatif Tutar (P2)
```
Given: amount = -1000000
When:  POST /calculator/calculate
Then:  HTTP 422 — Validation hatası (amount > 0 olmalı)
```

#### S9-TC-018: Hesaplama — 0 Ay Vade (P2)
```
Given: term_months = 0
When:  POST /calculator/calculate
Then:  HTTP 422 — term_months > 0 olmalı
```

### 6.6 Frontend — Vitrin & Kredi

#### S9-TC-019: /network Sayfası — Vitrin Listesi (P1)
```
Given: /network sayfası
When:  Sayfa yüklenir
Then:  Showcase listesi kartlarla görünür
       "Yeni Vitrin" butonu mevcut
```

#### S9-TC-020: /network/create — Vitrin Oluşturma Formu (P1)
```
Given: /network/create sayfası
When:  Form doldurulur (başlık, açıklama, ilan seçimi, tema)
Then:  showcase-form bileşeni
       İlan multi-select, renk seçici
```

#### S9-TC-021: /vitrin/[slug] — Public Vitrin Sayfası (P0)
```
Given: Paylaşılmış slug linki
When:  /vitrin/kadikoy-secme-ilanlar adresine git
Then:  SSR ile render
       - Agent bilgileri
       - İlan kartları (fotoğraf, fiyat, detay)
       - WhatsApp iletişim butonu
```

#### S9-TC-022: /calculator Sayfası (P1)
```
Given: /calculator sayfası
When:  Sayfa yüklenir
Then:  use-calculator hook aktif
       - Tutar, vade, faiz input'ları
       - Banka seçimi dropdown
       - Amortisman tablosu (hesaplama sonrası)
```

---

## 7. S10 — Telegram Mini App & Bot

### 7.1 Mini App Auth

**Kaynak Kod:** `messaging/bot/mini_app_auth.py`, `auth_bridge.py`, `bot/router.py`

#### S10-TC-001: GET /telegram/mini-app/auth — HMAC Doğrulama (P0)
```
Given: Telegram Mini App init_data string'i (HMAC-SHA256 imzalı)
When:  GET /api/v1/telegram/mini-app/auth
       headers: X-Telegram-Init-Data: <init_data>
Then:  HTTP 200
       - MiniAppAuthResponse: access_token, user
       - validate_init_data() HMAC doğrulaması başarılı
       - get_or_create_user_from_telegram() ile kullanıcı oluşturulur/bulunur
```

#### S10-TC-002: Auth — Geçersiz HMAC (P0)
```
Given: Manipüle edilmiş init_data (hash uyuşmuyor)
When:  GET /telegram/mini-app/auth
Then:  HTTP 401 — "Invalid Telegram init data"
       HMAC-SHA256 doğrulaması başarısız
```

#### S10-TC-003: Auth — Süresi Dolmuş Init Data (P1)
```
Given: 24 saatten eski init_data (auth_date çok eski)
When:  GET /telegram/mini-app/auth
Then:  HTTP 401 — Expired init data
```

#### S10-TC-004: Auth Bridge — Link Token Oluşturma (P1)
```
Given: Mevcut sistem kullanıcısı
When:  TelegramAuthBridge.generate_link_token(user_id)
Then:  Link token döner (Redis'te saklanır)
       Token bir kez kullanılabilir (one-time)
```

#### S10-TC-005: Auth Bridge — verify_and_link (P1)
```
Given: Geçerli link token + telegram chat_id
When:  verify_and_link(token, chat_id)
Then:  User.telegram_chat_id güncellenir
       Token invalidate edilir
```

### 7.2 Mini App Sayfaları

#### S10-TC-006: /tg — Ana Sayfa (P1)
```
Given: Telegram Mini App açıldı, auth başarılı
When:  /tg sayfası yüklenir
Then:  tg-provider → tg-auth-guard → ana içerik
       - Dashboard özet kartları (use-tg-dashboard hook)
       - tg-bottom-nav (4 tab: Ana, Değerleme, CRM, Ayarlar)
```

#### S10-TC-007: /tg/valuation — Değerleme Sayfası (P1)
```
Given: Mini App içinde
When:  /tg/valuation sayfasına geçiş
Then:  use-tg-valuation hook ile değerleme formu
       Mobil optimize UI
       React Query cache
```

#### S10-TC-008: /tg/crm — CRM Sayfası (P1)
```
Given: Mini App içinde
When:  /tg/crm sayfasına geçiş
Then:  use-tg-customers hook ile müşteri listesi
       Kompakt kart görünümü
```

#### S10-TC-009: Auth Guard — Token Yoksa (P0)
```
Given: tg-auth-guard, geçerli token yok
When:  Mini App sayfası açılır
Then:  Auth akışı yeniden başlatılır
       İçerik gösterilmez, loading/auth ekranı
```

### 7.3 Bot Komutları

**Kaynak Kod:** `messaging/bot/handlers.py`, `bot_commands.py`

#### S10-TC-010: /start Komutu (P1)
```
Given: Yeni Telegram kullanıcısı
When:  /start komutu gönderir
Then:  Karşılama mesajı + inline keyboard
       Komut listesi gösterilir
```

#### S10-TC-011: /degerleme Komutu (P1)
```
Given: Bot kullanıcısı, auth bağlı
When:  /degerleme komutu
Then:  Değerleme özet bilgisi veya Mini App linki
```

#### S10-TC-012: /kredi Komutu — Hesaplama (P1)
```
Given: Bot kullanıcısı
When:  /kredi 2500000 120
Then:  _parse_amount("2500000") → 2.500.000
       _parse_term("120") → 120 ay
       Kredi hesaplama sonucu mesaj olarak döner
```

#### S10-TC-013: /kredi — Kısaltma Formatları (P2)
```
Given: Bot kullanıcısı
When:  /kredi 2.5m 15y
Then:  _parse_amount("2.5m") → 2.500.000
       _parse_term("15y") → 180 ay
       Hesaplama sonucu döner
```

#### S10-TC-014: /kredi — Türkçe Format (P2)
```
Given: Bot kullanıcısı
When:  /kredi 2,5m 180
Then:  _parse_amount("2,5m") → virgül noktaya çevrilir → 2.500.000
       Başarılı hesaplama
```

#### S10-TC-015: /kredi — Geçersiz Tutar (P2)
```
Given: Bot kullanıcısı
When:  /kredi abc 120
Then:  InvalidParamError: "Gecersiz tutar: abc"
       Hata mesajı kullanıcıya iletilir
```

#### S10-TC-016: /ilan Wizard — 6 Adımlı Akış (P0)
```
Given: Bot kullanıcısı, ConversationStateManager aktif
When:  /ilan komutu
Then:  WizardStep enum ile 6 adım:
       1. İlçe → _fuzzy_match_district
       2. Mülk tipi
       3. Oda sayısı
       4. Metrekare
       5. Fiyat
       6. Açıklama
       Her adımda Redis'te state saklanır
       Tamamlandığında ilan taslağı oluşur
```

#### S10-TC-017: /ilan — İlçe Fuzzy Match (P2)
```
Given: Wizard ilçe adımı
When:  Kullanıcı "kadıkoy" (eksik ö) yazar
Then:  _fuzzy_match_district("kadikoy") → exact match bulur
When:  Kullanıcı "kdky" yazar (3 harf altı)
Then:  Prefix match dener, bulamazsa "İlçe bulunamadı" mesajı
```

#### S10-TC-018: /ilan — Reverse Geocode (P2)
```
Given: Wizard ilçe adımı
When:  Kullanıcı konum paylaşır (lat=41.0, lon=29.0)
Then:  _reverse_geocode_district(41.0, 29.0) → En yakın ilçe bulunur
       İstanbul bounding box kontrolü (40.5-41.7, 27.5-30.0)
```

#### S10-TC-019: /ilan — İstanbul Dışı Konum (P2)
```
Given: Wizard ilçe adımı
When:  Kullanıcı Ankara konumu paylaşır (lat=39.93, lon=32.86)
Then:  _reverse_geocode_district → None (İstanbul dışı)
       "İstanbul dışı konum" mesajı
```

### 7.4 Günlük Rapor

**Kaynak Kod:** `tasks/daily_report.py`

#### S10-TC-020: Günlük Rapor — Celery Beat (P1)
```
Given: Celery beat scheduler aktif
When:  Her gün saat 09:00'da send_daily_office_reports çalışır
Then:  Her ofis için:
       - Yeni ilan, yeni müşteri, yeni eşleşme sayıları
       - Kota durumu
       - Rapor Telegram'a gönderilir (bot_notification_service)
```

#### S10-TC-021: Rapor — Telegram Mesaj Formatı (P2)
```
Given: Günlük rapor verileri hazır
When:  BotNotificationService.send_notification_to_user çağrılır
Then:  Markdown formatında mesaj
       - İstatistikler emoji ile
       - Inline keyboard (detay linkler)
```

### 7.5 CRM Keyboard

#### S10-TC-022: CRM Inline Keyboard (P2)
```
Given: Bot'tan müşteri eşleşme bildirimi
When:  _format_match_card helper
Then:  Inline keyboard butonları:
       - "İlgileniyorum" → match status = interested
       - "Geç" → match status = passed
       - "Detay" → Mini App linki
```

### 7.6 Webhook & Error Handling

#### S10-TC-023: POST /telegram/webhook — Valid Update (P0)
```
Given: Telegram webhook konfigüre
When:  POST /api/v1/telegram/webhook (Telegram imzalı)
Then:  HTTP 200 — Update işlendi
       handlers.py'deki uygun handler çağrıldı
```

#### S10-TC-024: Webhook — Geçersiz İmza (P0)
```
Given: Manipüle edilmiş webhook body
When:  POST /telegram/webhook
Then:  HTTP 401 veya 200 (silent drop) — Güvenlik
```

#### S10-TC-025: Bot Error Handling — Service Down (P1)
```
Given: Backend API geçici olarak down
When:  Bot komutu gönderilir
Then:  Kullanıcıya anlamlı hata mesajı
       Retry mekanizması devrede
```

#### S10-TC-026: ConversationState — Redis Timeout (P2)
```
Given: Wizard aktif, 30 dk yanıt yok
When:  Redis TTL sonrası kullanıcı yanıt verir
Then:  State bulunamaz, wizard yeniden başlar
       "Süreniz doldu, lütfen tekrar başlayın" mesajı
```

### 7.7 Frontend — Telegram Bileşenleri

#### S10-TC-027: TgProvider — SDK Init (P1)
```
Given: Telegram WebApp context mevcut
When:  tg-provider render
Then:  @telegram-apps/sdk-react init edilir
       Tema renkleri Telegram'dan alınır
```

#### S10-TC-028: TgBottomNav — 4 Tab (P2)
```
Given: Mini App açık
When:  tg-bottom-nav render
Then:  4 tab: Ana Sayfa, Değerleme, CRM, (4. tab)
       Aktif tab vurgulanır
```

#### S10-TC-029: SegmentedControl — UI (P3)
```
Given: Mini App liste sayfası
When:  segmented-control render
Then:  Segment değiştirme animasyonu
       Seçili segment veri filtreleme
```

---

## 8. Çapraz Modül Senaryoları

### 8.1 İlan → Eşleştirme → Bildirim Akışı

#### CROSS-TC-001: İlan Oluşturma → Otomatik Eşleştirme (P0)
```
Given: Ofiste buyer müşteriler var, uyumlu profiller mevcut
When:  POST /api/v1/properties (yeni ilan oluşturulur)
Then:  trigger_matching_after_property_create() çağrılır
       Celery task: trigger_matching_for_property.delay(property_id, office_id)
       MatchingService.find_matches_for_property çalışır
       Skor ≥ 70 olanlar PropertyCustomerMatch'e kaydedilir
```

#### CROSS-TC-002: Eşleşme → Bildirim → Telegram (P0)
```
Given: Eşleşme oluşturuldu (skor=85)
When:  Match kaydedildikten sonra
Then:  Notification oluşur (notifications tablosu)
       Müşteri agent'ına Telegram bildirim gönderilir
       BotNotificationService.send_match_notification() çağrılır
```

#### CROSS-TC-003: Müşteri Oluşturma → Otomatik Eşleştirme (P1)
```
Given: Ofiste aktif ilanlar var
When:  POST /api/v1/customers (yeni buyer müşteri)
Then:  trigger_matching_after_customer_create() çağrılır
       Celery task: trigger_matching_for_customer.delay(customer_id, office_id)
       Tüm aktif ilanlara karşı skor hesaplanır
```

### 8.2 Değerleme → PDF → Telegram

#### CROSS-TC-004: Değerleme → PDF → Telegram Paylaşım (P1)
```
Given: Kullanıcı değerleme yaptı (prediction_id var)
When:  1. GET /valuations/{id}/pdf → PDF indirildi
       2. Bot üzerinden PDF paylaşımı
Then:  PDF içeriği doğru (fiyat, emsal, güven aralığı)
       Telegram'da dosya olarak paylaşılabilir
```

### 8.3 Müşteri → Match → CRM

#### CROSS-TC-005: Tam CRM Akışı (P0)
```
Given: Yeni müşteri oluşturuldu (cold)
When:  1. Eşleşme bulundu → Bildirim
       2. Agent eşleşmeyi inceler → interested
       3. Agent müşteriye not ekler
       4. Status güncelleme: cold → warm → hot
       5. Match status: contacted → converted
Then:  Timeline'da tüm olaylar kronolojik görünür
       Lead pipeline doğru güncellenir
```

### 8.4 Kota Akışı

#### CROSS-TC-006: Cross-Module Kota Tutarlılığı (P1)
```
Given: Starter plan, tüm kotalar sıfır
When:  1. 50 değerleme → kota dolu (HTTP 429)
       2. 20 ilan → kota dolu (HTTP 429)
       3. 10 staging → kota dolu (HTTP 429)
       4. 100 fotoğraf → kota dolu (HTTP 429)
       5. 50 müşteri → kota dolu (HTTP 429)
Then:  Her modül bağımsız kota kontrolü yapar
       UsageQuota tablosunda doğru sayaçlar
```

#### CROSS-TC-007: Ay Değişimi — Tüm Kotalar Sıfırlanır (P1)
```
Given: Şubat sonu, tüm kotalar dolu
When:  1 Mart'ta yeni işlem
Then:  get_or_create_quota yeni period_start ile kayıt oluşturur
       Tüm *_used alanları 0
```

#### CROSS-TC-008: Plan Upgrade — Kota Artışı (P2)
```
Given: Starter → Pro yükseltme
When:  Sonraki değerleme isteği
Then:  get_valuation_quota("pro") = 500
       Kalan hak güncellenir
```

### 8.5 Telegram → Backend Entegrasyonu

#### CROSS-TC-009: Telegram Değerleme → Backend API (P1)
```
Given: Telegram Mini App'ten değerleme formu
When:  use-tg-valuation hook POST /valuations çağırır
Then:  Aynı kota kontrolü, aynı ML model
       Sonuç Mini App'te gösterilir
```

#### CROSS-TC-010: Telegram CRM → Backend API (P1)
```
Given: Telegram Mini App CRM sayfası
When:  use-tg-customers hook GET /customers çağırır
Then:  RLS izolasyonu korunur
       Aynı müşteri verileri
```

---

## 9. Multi-Tenant RLS Senaryoları

**Kaynak Kod:** `middleware/tenant.py` — TenantMiddleware, SET LOCAL app.current_office_id

#### RLS-TC-001: Tenant İzolasyonu — Müşteri Verisi (P0)
```
Given: Office_A ve Office_B farklı ofisler
       Office_A'da 10 müşteri, Office_B'de 5 müşteri
When:  Office_A kullanıcısı GET /customers
Then:  Sadece 10 müşteri döner (Office_B müşterileri görünmez)
       SET LOCAL app.current_office_id = 'Office_A_UUID'
```

#### RLS-TC-002: Tenant İzolasyonu — Değerleme (P0)
```
Given: Office_A ve Office_B farklı değerlemeler yapmış
When:  Office_A kullanıcısı GET /valuations
Then:  Sadece kendi değerlemeleri döner
```

#### RLS-TC-003: Tenant İzolasyonu — Eşleştirme (P0)
```
Given: Office_A ilanı, Office_B müşterisi
When:  POST /matches/run/property/{office_a_property}
Then:  Sadece Office_A müşterileri eşleştirilir
       Office_B müşterileri dahil edilmez
```

#### RLS-TC-004: Cross-Tenant Erişim Denemesi (P0)
```
Given: Office_A kullanıcısı
When:  GET /customers/{office_b_customer_id}
Then:  HTTP 404 — RLS policy kayıtı görünmez kılar
       Veri sızıntısı YOK
```

#### RLS-TC-005: Public Endpoint — RLS Bypass (P0)
```
Given: Public endpoint (/showcases/public/{slug})
When:  JWT olmadan erişim
Then:  HTTP 200 — Public showcase verileri
       PUBLIC_PATHS frozenset'inde tanımlı
       veya PUBLIC_PREFIXES ile prefix match
```

#### RLS-TC-006: JWT Olmadan Protected Endpoint (P0)
```
Given: JWT header yok
When:  GET /api/v1/customers
Then:  HTTP 401 — TenantMiddleware JWT bulamaz
       DB session açılmaz
```

#### RLS-TC-007: Geçersiz Office_ID JWT'de (P1)
```
Given: JWT'de olmayan/geçersiz office_id
When:  Herhangi bir protected endpoint
Then:  HTTP 401 veya 403
       RLS policy current_setting NULL döner → erişim kapatılır
```

#### RLS-TC-008: Showcase — Paylaşım Ağı (P1)
```
Given: Office_A vitrini paylaşılmış
When:  Office_B kullanıcısı public slug ile erişir
Then:  İlan bilgileri görünür (public)
       Ama Office_A'nın müşteri verileri görünmez
```

#### RLS-TC-009: SQL Injection Denemesi — office_id (P0)
```
Given: JWT manipüle edilmiş, office_id = "'; DROP TABLE customers;--"
When:  TenantMiddleware SET LOCAL çalıştırır
Then:  SQLAlchemy text() parametrize query kullanır
       Injection başarısız
```

#### RLS-TC-010: Concurrent Tenant Sessions (P1)
```
Given: Office_A ve Office_B eşzamanlı istekler
When:  Her iki ofis aynı anda GET /customers çağırır
Then:  SET LOCAL transaction-scoped — izolasyon korunur
       Her session kendi office_id'sini görür
```

#### RLS-TC-011: Webhook Endpoints — Tenant Bypass (P1)
```
Given: /webhooks/payments/iyzico (webhook)
When:  External servis POST gönderir
Then:  PUBLIC_PREFIXES ile match → TenantMiddleware atlanır
       Webhook kendi doğrulama mekanizmasını kullanır
```

#### RLS-TC-012: Platform Admin Bypass (P2)
```
Given: Platform admin rolü
When:  Admin endpoint'lere erişir
Then:  app.current_user_role = "admin" SET LOCAL ile ayarlanır
       RLS policy admin bypass kuralı devrede
```

---

## 10. Performans & Güvenlik Senaryoları

### 10.1 Performans

#### PERF-TC-001: Değerleme Latency — P95 < 500ms (P1)
```
Given: 100 concurrent değerleme isteği
When:  POST /valuations (farklı parametreler)
Then:  P50 latency_ms < 200ms
       P95 latency_ms < 500ms
       P99 latency_ms < 1000ms
```

#### PERF-TC-002: Eşleştirme — 1000 Müşteri (P1)
```
Given: Ofiste 1000 buyer müşteri
When:  POST /matches/run/property/{id}
Then:  elapsed_ms < 5000ms (5 saniye)
       N*M karmaşıklık kabul edilebilir
```

#### PERF-TC-003: Sayfalama — Büyük Veri Setleri (P2)
```
Given: 10.000 müşteri kaydı
When:  GET /customers?limit=20&offset=9980
Then:  Yanıt süresi < 200ms
       Offset + Count query performansı
```

#### PERF-TC-004: PDF Üretimi — Timeout (P2)
```
Given: WeasyPrint PDF oluşturuyor
When:  GET /valuations/{id}/pdf
Then:  PDF 10 saniye içinde oluşur
       Timeout durumunda HTTP 504/408
```

#### PERF-TC-005: OpenAI API — Timeout Handling (P1)
```
Given: OpenAI API yanıt vermiyor
When:  POST /assistant/generate-description
Then:  MAX_RETRIES (3) sonrası timeout
       HTTP 503 — OpenAIServiceError
```

#### PERF-TC-006: DB Connection Pool (P2)
```
Given: 50 concurrent request
When:  Tüm istekler aynı anda
Then:  Connection pool tükenmez
       Kuyrukta bekleyen istekler timeout olmaz (< 30s)
```

### 10.2 Güvenlik

#### SEC-TC-001: JWT Token Expiry (P0)
```
Given: 30 dakikalık access token süresi dolmuş
When:  Protected endpoint'e erişim
Then:  HTTP 401 — Token expired
       Kullanıcı refresh token ile yenileme yapmalı
```

#### SEC-TC-002: Refresh Token Kullanımı (P1)
```
Given: Geçerli refresh token (7 gün)
When:  POST /api/v1/auth/refresh
Then:  Yeni access_token döner
       Eski refresh token invalidate edilir (one-time use)
```

#### SEC-TC-003: CORS Policy (P1)
```
Given: Farklı origin'den API çağrısı
When:  OPTIONS preflight request
Then:  Sadece whitelist'teki origin'ler kabul edilir
       Access-Control-Allow-Origin doğru set
```

#### SEC-TC-004: Rate Limiting — Brute Force Login (P1)
```
Given: 100 ardışık başarısız login denemesi
When:  POST /auth/login (yanlış password)
Then:  Rate limiting devreye girer
       HTTP 429 — Too many requests
```

#### SEC-TC-005: File Upload — Malicious File (P0)
```
Given: .php, .exe, .sh dosyası upload denemesi
When:  POST /listings/photos
Then:  HTTP 422 — Dosya tipi reddedilir
       Yalnızca JPEG, PNG, WebP kabul
```

#### SEC-TC-006: MinIO URL — Signed URL Expiry (P2)
```
Given: MinIO presigned URL oluşturuldu
When:  URL süresi dolduktan sonra erişim
Then:  HTTP 403 — Access Denied
```

#### SEC-TC-007: Telegram HMAC — Replay Attack (P1)
```
Given: Geçerli bir init_data yakalandı
When:  24 saat sonra tekrar gönderilir
Then:  auth_date kontrolü → Expired
       Replay attack önlenir
```

#### SEC-TC-008: Input Sanitization — XSS (P1)
```
Given: Müşteri ismi: "<script>alert('xss')</script>"
When:  POST /customers
Then:  Kayıt oluşur ama frontend'de escape edilir
       React otomatik XSS koruması
```

---

## 11. Öncelik Özet Tablosu

### P0 Senaryolar (Blocker) — 47 adet
| ID | Senaryo | Modül |
|----|---------|-------|
| S5-TC-001 | Happy Path Değerleme | S5 |
| S5-TC-002 | Kota Aşımı Starter | S5 |
| S5-TC-004 | Elite Sınırsız | S5 |
| S5-TC-015 | JWT Eksik | S5 |
| S5-TC-016 | Geçersiz JWT | S5 |
| S5-TC-023 | Division By Zero Guard | S5 |
| S6-TC-013 | Deprem Risk Başarılı | S6 |
| S7-TC-001 | Müşteri Oluşturma | S7 |
| S7-TC-006 | RLS — Başka Ofis Müşterisi | S7 |
| S7-TC-017 | Tam Uyum Skor 100 | S7 |
| S7-TC-027 | İlan Eşleştirme Çalıştır | S7 |
| S8-TC-012 | Fotoğraf Yükleme | S8 |
| S9-TC-001 | Vitrin Oluştur | S9 |
| S9-TC-006 | Public SSR Vitrin | S9 |
| S9-TC-012 | Annuity Hesaplama | S9 |
| S9-TC-021 | Public Vitrin Frontend | S9 |
| S10-TC-001 | HMAC Auth | S10 |
| S10-TC-002 | Geçersiz HMAC | S10 |
| S10-TC-009 | Auth Guard | S10 |
| S10-TC-016 | İlan Wizard | S10 |
| S10-TC-023 | Webhook Valid | S10 |
| S10-TC-024 | Webhook Güvenlik | S10 |
| CROSS-TC-001 | İlan→Eşleştirme | Çapraz |
| CROSS-TC-002 | Eşleşme→Bildirim | Çapraz |
| CROSS-TC-005 | Tam CRM Akışı | Çapraz |
| RLS-TC-001 | Tenant İzolasyonu Müşteri | RLS |
| RLS-TC-002 | Tenant İzolasyonu Değerleme | RLS |
| RLS-TC-003 | Tenant İzolasyonu Eşleştirme | RLS |
| RLS-TC-004 | Cross-Tenant Erişim | RLS |
| RLS-TC-005 | Public Endpoint Bypass | RLS |
| RLS-TC-006 | JWT Olmadan Protected | RLS |
| RLS-TC-009 | SQL Injection Denemesi | RLS |
| SEC-TC-001 | JWT Token Expiry | Güvenlik |
| SEC-TC-005 | Malicious File Upload | Güvenlik |

### Test Çalıştırma Planı

| Faz | Kapsam | Süre | Araç |
|-----|--------|------|------|
| 1. Birim Test | Score hesaplama, parsing, quota | 2 gün | pytest |
| 2. API Entegrasyon | Tüm endpoint'ler (CRUD + auth) | 3 gün | pytest + httpx |
| 3. E2E Çapraz Modül | 5 çapraz akış | 2 gün | pytest + Celery worker |
| 4. RLS/Güvenlik | 12 tenant + 8 güvenlik senaryosu | 2 gün | pytest + SQL |
| 5. Frontend | Component + page render | 2 gün | Vitest + Testing Library |
| 6. Performans | Yük testi (P95 latency) | 1 gün | locust / k6 |
| 7. Telegram | Bot + Mini App | 2 gün | pytest + Telegram test bot |
| **TOPLAM** | **290 senaryo** | **14 gün** | |

---

## Kota Referans Tablosu (plan_policy.py'den)

| Kota Tipi | Starter | Pro | Elite |
|-----------|---------|-----|-------|
| Değerleme | 50/ay | 500/ay | Sınırsız |
| İlan | 20/ay | 100/ay | Sınırsız |
| Staging | 10/ay | 50/ay | 200/ay |
| Fotoğraf | 100/ay | 500/ay | Sınırsız |
| Müşteri | 50 | 500 | Sınırsız |

## Eşleştirme Referans Tablosu (matching_service.py'den)

| Kriter | Ağırlık | Skor Kuralı |
|--------|---------|-------------|
| Fiyat | %30 | Budget aralığında=100, ±%20 dışı=0, arası lineer |
| Konum | %30 | Exact match=100, yoksa=0 |
| Oda | %20 | Aynı=100, ±1=50, ±2=20, fazlası=0 |
| Alan | %20 | Aralıkta=100, ±%20 dışı=0, arası lineer |
| **Eşik** | — | **70** (altı eşleşme oluşmaz) |
