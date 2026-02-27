# TASK-151: Performans Analizi ve Optimizasyon Raporu

**Tarih:** 2026-02-26
**Durum:** Analiz Tamamlandı
**Öncelik:** Yüksek

---

## İçindekiler

1. [N+1 Query Tespitleri](#1-n1-query-tespitleri)
2. [Eksik Veritabanı İndeksleri](#2-eksik-veritabanı-indeksleri)
3. [Lazy Import Kontrolleri](#3-lazy-import-kontrolleri)
4. [Frontend React Query Analizi](#4-frontend-react-query-analizi)
5. [Build Chunk Analizi](#5-build-chunk-analizi)
6. [Aksiyon Planı](#6-aksiyon-planı)

---

## 1. N+1 Query Tespitleri

### Sistemik Sorun: `lazy="selectin"` Kaskad Yükleme

Tüm model relationship'leri `lazy="selectin"` olarak tanımlı. Bu, her entity yüklendiğinde ilişkili tüm nesnelerin otomatik olarak yüklenmesine neden oluyor. En kritik sorun **Office → Users** döngüsel zinciri.

### Bulgu 1: Office ↔ User Döngüsel Eager Load (KRİTİK)

**Dosyalar:** `models/office.py:79-81`, `models/user.py:104-106`

```python
# office.py
users: Mapped[list[User]] = relationship("User", back_populates="office", lazy="selectin")

# user.py
office: Mapped[Office] = relationship("Office", back_populates="users", lazy="selectin")
```

**Etki:** Her authenticated request'te `get_current_user()` → User → Office → TÜM Office kullanıcıları yükleniyor. 50 ajanı olan bir ofis için her istekte 50 User nesnesi gereksiz yere yükleniyor.

**Çözüm:** `Office.users` → `lazy="raise"` veya `lazy="noload"` olarak değiştirilmeli.

### Bulgu 2: Her Entity Office'u Yüklüyor → Office Tüm User'ları Yüklüyor (KRİTİK)

Aşağıdaki modellerin hepsinde `office = relationship("Office", lazy="selectin")` tanımlı:

| Model | Dosya |
|-------|-------|
| Customer | `models/customer.py:121` |
| CustomerNote | `models/customer_note.py:80` |
| PropertyCustomerMatch | `models/match.py:102` |
| Property | `models/property.py:162` |
| Showcase | `models/showcase.py:125` |
| Subscription | `models/subscription.py:92` |
| Notification | `models/notification.py:74` |
| Message | `models/message.py:68, 141` |
| Payment | `models/payment.py:146` |

**Etki:** Tek bir Customer yüklemek bile Office + tüm Office çalışanlarını cascade yüklüyor.

**Çözüm:** `Office.users` ilişkisini `lazy="raise"` yaparak kaskadı kırmak.

### Bulgu 3: `get_timeline()` In-Memory Pagination (YÜKSEK)

**Dosya:** `modules/customers/service.py:494-578`

```python
# Tüm notlar (sınırsız)
notes = list(notes_result.scalars().all())
# Tüm eşleşmeler (sınırsız)
matches = list(matches_result.scalars().all())
# Python'da sort + pagination
timeline_items.sort(key=lambda x: x["timestamp"], reverse=True)
paginated_items = timeline_items[offset : offset + per_page]
```

**Etki:** 500 not + 200 eşleşme = 700 kayıt + tüm relationship'leri belleğe yükleniyor, sonra Python'da sayfalanıyor.

**Çözüm:** SQL `UNION ALL` + `ORDER BY` + `LIMIT/OFFSET` kullanılmalı. Sorguya `.options(noload("*"))` eklenmeli.

### Bulgu 4: MatchingService Tüm ORM Nesnelerini Yüklüyor (YÜKSEK)

**Dosya:** `modules/matches/matching_service.py:392-398, 481-487`

```python
# Tüm müşteriler (full ORM objects + relationships)
customers = list(result.scalars().all())
# Tüm mülkler (full ORM objects + relationships)
properties = list(result.scalars().all())
```

**Etki:** `calculate_match_score()` sadece `price, district, rooms, net_area` gibi scalar alanları kullanıyor ama tüm relationship'ler yükleniyor.

**Çözüm:** `.options(noload("*"))` eklenmeli veya sadece gerekli kolonlar `select()` ile çekilmeli.

### Bulgu 5: CustomerNote Gereksiz İlişki Yükleme (ORTA)

**Dosya:** `models/customer_note.py:78-80`

`list_notes` endpoint'i sadece `id, content, note_type, user_id, created_at` kullanıyor ama her note için Customer, User ve Office yükleniyor.

**Çözüm:** `list_notes` sorgusuna `.options(noload("*"))` eklenmeli.

### Bulgu 6: Match List Gereksiz İlişki Yükleme (ORTA)

**Dosya:** `modules/matches/service.py:85-93`

`_to_response()` sadece scalar alanları kullanıyor ama her match için Property, Customer ve Office yükleniyor.

**Çözüm:** `.options(noload("*"))` eklenmeli.

### Bulgu 7: Showcase `list_by_agent` Gereksiz Yükleme (ORTA)

**Dosya:** `modules/showcases/service.py:199-201`

`_to_list_item()` sadece `id, title, slug, is_active, views_count, created_at` kullanıyor ama Office ve Agent yükleniyor.

**Çözüm:** `.options(noload("*"))` eklenmeli.

### Bulgu 8: Conversation → Messages Sınırsız Eager Load (ORTA)

**Dosya:** `models/message.py:70-73`

```python
messages: Mapped[list[Message]] = relationship(
    "Message", back_populates="conversation", lazy="selectin",
    order_by="Message.created_at",
)
```

**Etki:** Conversation yüklendiğinde TÜM mesajlar yükleniyor (sınırsız).

**Çözüm:** `lazy="raise"` yapılmalı, mesajlar sayfalanmış sorguyla çekilmeli.

### Bulgu 9: Bug - `office.subscription` İlişkisi Yok

**Dosya:** `modules/customers/router.py:108`

```python
plan_type = current_user.office.subscription.plan_type if current_user.office and current_user.office.subscription else "starter"
```

Office modelinde `subscription` ilişkisi tanımlı değil. Bu ya `AttributeError` fırlatıyor ya da her zaman `"starter"` döndürüyor.

**Çözüm:** `SubscriptionService` ile ayrı sorgu yapılmalı (valuations/router.py'deki `_get_plan_type()` pattern'ı gibi).

### Önerilen Sistemik Çözüm

Tüm model-level `lazy="selectin"` tanımlarını `lazy="raise"` olarak değiştirip, her sorguda ihtiyaç duyulan ilişkileri `.options(selectinload(...))` ile açıkça belirtmek (**opt-in eager loading**).

---

## 2. Eksik Veritabanı İndeksleri

### YÜKSEK Öncelik

#### 2.1 Subscription — `(office_id, status, created_at)` Bileşik İndeks

**Mevcut:** Sadece `ix_subscriptions_office_id` (tek kolon)
**Kullanım yeri:** 7+ sorgu noktası — her valuation, credit check, listing, Telegram bot komutu

```python
# 7 farklı dosyada tekrarlanan pattern:
select(Subscription).where(
    Subscription.office_id == ...,
    Subscription.status.in_(["active", "trial"])
).order_by(Subscription.created_at.desc()).limit(1)
```

**Öneri:**
```python
Index("ix_subscriptions_office_status_created", "office_id", "status", "created_at")
```

#### 2.2 PredictionLog — `(office_id, created_at)` Bileşik İndeks

**Mevcut:** Sadece `ix_prediction_logs_office_id` (tek kolon)
**Kullanım yeri:** Valuation history, Telegram bot, anomaly detection

**Öneri:**
```python
Index("ix_prediction_logs_office_created", "office_id", "created_at")
```

#### 2.3 Notification — `(user_id, is_deleted, is_read)` Bileşik İndeks

**Mevcut:** `ix_notifications_user_id_is_read` (user_id, is_read) — `is_deleted` eksik
**Kullanım yeri:** Her notification sorgusu (6 nokta) `is_deleted == False` filtresi kullanıyor

**Öneri:**
```python
Index("ix_notifications_user_active", "user_id", "is_read",
      postgresql_where=text("is_deleted = false"))
```

### ORTA Öncelik

| # | Model.Kolon | Sorun | Öneri |
|---|-------------|-------|-------|
| 2.4 | `AreaAnalysis.lower(district)` | Composite index'te trailing; district-only sorgu 4+ yerde | `Index("ix_area_district_lower", func.lower(district))` |
| 2.5 | `DepremRisk.district` | Composite'te trailing; district-only sorgu | `Index("ix_deprem_district", "district")` |
| 2.6 | `PriceHistory.(area_type, area_name, date)` | Mevcut: sadece (area_type, area_name); date eksik | 3. kolon olarak `date` eklenmeli |
| 2.7 | `Property.agent_id` | FK ama indeks yok | `Index("ix_properties_agent_id", "agent_id")` |
| 2.8 | `Customer.(office_id, created_at)` | `created_at` sıralaması indekssiz | `Index("ix_customers_office_created", "office_id", "created_at")` |
| 2.9 | `InboxEvent.(status, office_id)` | Hiç indeks yok (sadece unique event_id) | OutboxEvent pattern'ı takip edilmeli |

### DÜŞÜK Öncelik

| # | Model.Kolon | Öneri |
|---|-------------|-------|
| 2.10 | `Property.status` (standalone) | Partial index: `status='active'` |
| 2.11 | `Property.property_type` | Tek başına sorgulanıyorsa ekle |
| 2.12 | `Office.is_active` | Ofis sayısı az olduğu sürece gereksiz |
| 2.13 | `PropertyCustomerMatch.(office_id, created_at)` | Daily report hızlanacaksa ekle |

---

## 3. Lazy Import Kontrolleri

### Startup Import Zinciri

```
main.py
  → valuations/router.py
    → inference_service.py          → pandas (EAGER)
      → confidence_interval.py      → joblib, numpy (EAGER)
      → feature_engineering.py      → joblib, numpy, pandas, sklearn (EAGER)
      → trainer.py                  → lightgbm, numpy, pandas, sklearn (EAGER)
  → valuations/pdf_router.py
    → pdf_service.py                → weasyprint (EAGER)
```

**Tahmini startup overhead: ~2.5-7 saniye**

### Detaylı Durum Tablosu

| Kütüphane | Import Süresi | Dosya | Durum | Aksiyon |
|-----------|--------------|-------|-------|---------|
| **WeasyPrint** | ~1-3s | `services/pdf_service.py:14` | ❌ EAGER | Fonksiyon içine taşınmalı |
| **LightGBM** | ~0.5-1.5s | `ml/trainer.py:12` | ❌ EAGER | Lazy yapılmalı |
| **pandas** | ~0.3-0.8s | `inference_service.py:20`, `trainer.py:13`, `feature_engineering.py:13` | ❌ EAGER | Lazy yapılmalı |
| **numpy** | ~0.1-0.3s | `trainer.py:13`, `feature_engineering.py:12`, `confidence_interval.py:22` | ❌ EAGER | Lazy yapılmalı |
| **scikit-learn** | ~0.5-1s | `trainer.py:15-21`, `feature_engineering.py:14` | ❌ EAGER | Lazy yapılmalı |
| **joblib** | ~0.05-0.1s | `trainer.py:11`, `feature_engineering.py:11`, `confidence_interval.py:22` | ❌ EAGER | Lazy yapılmalı |
| **OpenAI SDK** | ~0.2-0.5s | `services/openai_service.py` | ✅ LAZY | Örnek pattern |

### İyi Uygulama Örnekleri (Referans)

**OpenAI Service** — Tam lazy import, dokümante edilmiş:
```python
# openai_service.py:28
# "Lazy import: openai paketi sadece ilk kullanımda import edilir"
```

**confidence_interval.py** — `TYPE_CHECKING` guard:
```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import lightgbm as lgb
```

### Önerilen Düzeltmeler

**1. `pdf_service.py` — WeasyPrint lazy import:**
```python
# ÖNCE (satır 14):
from weasyprint import HTML

# SONRA:
def generate_valuation_pdf(...):
    from weasyprint import HTML
    ...
```

**2. `inference_service.py` — ML kütüphaneleri lazy import:**
```python
# ÖNCE (satır 20, 23, 27-28):
import pandas as pd
from src.ml.confidence_interval import ConfidencePredictor
from src.ml.feature_engineering import FeatureEngineer
from src.ml.trainer import ModelTrainer

# SONRA:
class InferenceService:
    def predict(self, ...):
        import pandas as pd
        from src.ml.feature_engineering import FeatureEngineer
        ...

    def train(self, ...):
        from src.ml.trainer import ModelTrainer
        ...
```

**3. `trainer.py` — Tüm importlar lazy:**
```python
# ÖNCE (satır 11-21):
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import ...
from sklearn.model_selection import ...

# SONRA:
class ModelTrainer:
    def train(self, ...):
        import joblib
        import lightgbm as lgb
        import numpy as np
        import pandas as pd
        from sklearn.metrics import ...
        from sklearn.model_selection import ...
```

---

## 4. Frontend React Query Analizi

### Global Konfigürasyon

**Dosya:** `apps/web/src/app/providers.tsx`

```typescript
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 dakika
      // gcTime: AYARLANMAMIŞ → varsayılan 5 dakika
    },
  },
})
```

### Hook Bazlı Analiz

| Hook | staleTime | gcTime | Sorun | Öneri |
|------|-----------|--------|-------|-------|
| `useDepremRisk` | 30 dk | 5 dk (varsayılan) | ⚠️ gcTime < staleTime | gcTime: 60dk, staleTime: Infinity |
| `useAreaTrends` | 30 dk | 5 dk (varsayılan) | ⚠️ gcTime < staleTime | gcTime: 60dk |
| `useAreaAnalysis` | 5 dk | 5 dk (varsayılan) | Gereksiz override | Global yeterli, kaldır |
| `useProperties` | 5 dk | 5 dk (varsayılan) | Gereksiz override | Global yeterli, kaldır |
| `usePropertySearch` | 5 dk | 5 dk (varsayılan) | Gereksiz override | Global yeterli, kaldır |
| `useAreaCompare` | 5 dk | 5 dk (varsayılan) | Analitik veri için kısa | staleTime: 15dk, gcTime: 30dk |
| `useSearchSuggestions` | 30 sn | 5 dk (varsayılan) | Çok kısa | staleTime: 2-5dk |

### Kritik Sorun: gcTime < staleTime Uyumsuzluğu

`useDepremRisk` ve `useAreaTrends` hook'larında `staleTime` 30 dakika ama `gcTime` varsayılan 5 dakika. Cache, veri stale olmadan 25 dakika önce garbage collect ediliyor. Bu, 30 dakikalık staleTime'ın hiçbir işe yaramaması demek — her component mount'ta yeni fetch yapılıyor.

### Önerilen Global Konfigürasyon

```typescript
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,   // 5 dakika (mevcut)
      gcTime: 10 * 60 * 1000,     // 10 dakika (EKLENMELİ)
      refetchOnWindowFocus: true,  // varsayılan, açık olsun
    },
  },
})
```

### React Query Kullanmayan Hook'lar (Mock → API Migrasyonu İçin Not)

| Hook | Mevcut Pattern | Migrasyon Önerisi |
|------|---------------|-------------------|
| `useCustomers` | `useMemo` + mock | → `useQuery` |
| `useCustomerDetail` | `useMemo` + mock | → `useQuery` |
| `useShowcases` | `useState + useEffect` + mock | → `useQuery` |
| `useSharedShowcases` | `useState + useEffect` + mock | → `useQuery` |
| `useListingAssistant` | `useState` + manual async | → `useMutation` |
| `useVirtualStaging` | `useState` + manual async | → `useMutation` |

---

## 5. Build Chunk Analizi

**Build Tool:** Next.js 15.5.12 (Turbopack)
**Build Süresi:** 9.2s derleme + 265ms disk yazma

### 100KB+ Sayfalar

| Route | Sayfa Boyutu | First Load JS | Durum |
|-------|-------------|---------------|-------|
| `/maps` | **278 kB** | **428 kB** | 🔴 Çok büyük |
| `/areas` | **124 kB** | **274 kB** | 🟡 Büyük |
| `/areas/compare` | **123 kB** | **273 kB** | 🟡 Büyük |
| `/listings` | **89.2 kB** | **239 kB** | 🟡 Sınırda |

### Shared Chunks (Tüm sayfalarda yüklenen)

| Chunk | Boyut |
|-------|-------|
| Shared JS (toplam) | **157 kB** |
| `afdeaa381ce5c402.js` | 59.2 kB |
| `3b80c50f25f7d02d.css` | 19.5 kB |
| `5d4a4b583f222219.js` | 17.2 kB |
| `daad4227609cab0b.js` | 13.2 kB |
| `f554d58504cd6cd8.js` | 10.8 kB |
| Diğer shared chunks | 37.7 kB |

### Analiz ve Öneriler

**🔴 `/maps` — 278 kB (sayfa) + 157 kB (shared) = 428 kB First Load:**
- MapLibre GL JS büyük olasılıkla bu chunk'ın büyük kısmını oluşturuyor
- **Öneri:** `next/dynamic` ile lazy load, harita component'ını `ssr: false` ile yükle
- **Öneri:** MapLibre CSS'i sadece bu sayfada yükle

**🟡 `/areas` ve `/areas/compare` — ~124 kB:**
- Recharts/chart kütüphanesi büyük olasılıkla bu sayfaları şişiriyor
- **Öneri:** Chart component'larını `next/dynamic` ile lazy load et

**🟡 `/listings` — 89.2 kB:**
- Virtual staging, listing assistant ve form component'ları bir arada
- **Öneri:** Tab bazlı lazy loading (her tab'ı dynamic import ile yükle)

**📋 Lint Uyarıları (build sırasında):**
- `virtual-staging-tab.tsx`: 3x `<img>` → `next/image` kullanılmalı (LCP iyileştirmesi)
- `avatar.tsx`: `<img>` → `next/image` kullanılmalı
- `data-freshness-tooltip.tsx`: Kullanılmayan `refreshStatus` değişkeni
- `listings.ts`: Kullanılmayan `GeneratedListing` tipi

---

## 6. Aksiyon Planı

### Faz 1: Kritik (Bu Sprint)

| # | Aksiyon | Etki | Efor |
|---|---------|------|------|
| 1.1 | `Office.users` → `lazy="raise"` | Her isteği etkileyen kaskad yüklemeyi durdurur | S |
| 1.2 | Subscription composite index ekle | 7+ sorgu noktasını hızlandırır | S |
| 1.3 | `useDepremRisk` ve `useAreaTrends` gcTime düzelt | Gereksiz refetch'leri durdurur | XS |
| 1.4 | Global QueryClient'a `gcTime: 10 * 60 * 1000` ekle | Tüm hook'ları etkiler | XS |

### Faz 2: Yüksek Öncelik (Sonraki Sprint)

| # | Aksiyon | Etki | Efor |
|---|---------|------|------|
| 2.1 | WeasyPrint lazy import (`pdf_service.py`) | Startup ~1-3s azalır | XS |
| 2.2 | LightGBM/pandas/sklearn lazy import zinciri | Startup ~2-4s azalır | M |
| 2.3 | `get_timeline()` SQL-level pagination | Büyük timeline'larda N*M sorgu → 2 sorgu | M |
| 2.4 | MatchingService'e `noload("*")` ekle | Eşleşme hesaplaması çok hızlanır | S |
| 2.5 | PredictionLog, Notification composite index'leri | Valuation history + notification sorgularını hızlandırır | S |

### Faz 3: Orta Öncelik

| # | Aksiyon | Etki | Efor |
|---|---------|------|------|
| 3.1 | `/maps` sayfasını dynamic import ile lazy load | First Load 428kB → ~200kB | S |
| 3.2 | `/areas` chart component'larını lazy load | First Load 274kB → ~180kB | S |
| 3.3 | AreaAnalysis, DepremRisk, PriceHistory indeksleri | İlçe bazlı sorgular hızlanır | S |
| 3.4 | Property.agent_id, Customer.(office_id, created_at) indeksleri | FK integrity + listing sorgularını hızlandırır | S |
| 3.5 | `<img>` → `next/image` migrasyonu | LCP skorunu iyileştirir | S |
| 3.6 | Conversation.messages → `lazy="raise"` | Gelecekteki mesajlaşma modülü için hazırlık | XS |

### Faz 4: Sistemik Refactoring

| # | Aksiyon | Etki | Efor |
|---|---------|------|------|
| 4.1 | Tüm `lazy="selectin"` → `lazy="raise"` dönüşümü | Opt-in eager loading pattern'ı | L |
| 4.2 | Her sorguda `.options(selectinload(...))` ile gerekli ilişkileri açıkça belirt | Sorguların veri gereksinimleri görünür olur | L |
| 4.3 | Mock hook'ları React Query'ye migrasyon | Cache, dedup, background refetch avantajları | M |
| 4.4 | `office.subscription` bug fix | customers/router.py:108 sessiz hata | XS |

---

## Özet Metrikler

| Kategori | Bulgu Sayısı | Kritik | Yüksek | Orta | Düşük |
|----------|-------------|--------|--------|------|-------|
| N+1 / Eager Load | 10 | 2 | 2 | 5 | 1 |
| Eksik İndeks | 13 | 3 | 0 | 6 | 4 |
| Lazy Import | 6 dosya | 2 | 2 | 2 | 0 |
| React Query | 7 hook | 2 | 1 | 4 | 0 |
| Build Chunks | 4 sayfa | 1 | 2 | 1 | 0 |
| **TOPLAM** | **40 bulgu** | **10** | **7** | **18** | **5** |
