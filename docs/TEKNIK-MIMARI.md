# Emlak Teknoloji Platformu — Teknik Mimari Dokümanı

**Tarih:** 2026-02-20
**Versiyon:** 1.0
**Hazırlayan:** claude-teknik-lider
**Durum:** Taslak — Orkestra Şefi onayı bekleniyor
**Kaynak:** PROJE-PLANI.md (20 bölüm, 993 satır) + PRODUCT-BACKLOG.md (15 Epic, 310 satır)

---

## 1. Tech Stack Kesinleştirme

### 1.1 Özet Tablo

| Katman | Seçilen Teknoloji | Versiyon | Lisans |
|--------|-------------------|----------|--------|
| **Frontend (Web)** | Next.js (React) | 15.x (React 19) | MIT |
| **Frontend (Mobil)** | Telegram Mini App + PWA | — | — |
| **Backend API** | FastAPI | 0.115+ (Python 3.12) | MIT |
| **ORM** | SQLAlchemy | 2.0+ (async) | MIT |
| **Migration** | Alembic | 1.13+ | MIT |
| **Veritabanı** | PostgreSQL + PostGIS | 16 + 3.4 | PostgreSQL / GPLv2 |
| **Arama** | PostgreSQL FTS + pg_trgm (MVP), Meilisearch (Faz 2) | — / 1.x | — / MIT |
| **Önbellek** | Redis | 7.2+ | BSD |
| **Görev Kuyruğu** | Celery + Redis broker | 5.4+ | BSD |
| **Telegram Bot** | aiogram | 3.x | MIT |
| **ML Framework** | LightGBM + scikit-learn | 4.x + 1.5+ | MIT |
| **LLM** | OpenAI API (GPT-5-mini) + Anthropic API (Claude) | — | Proprietary |
| **Harita** | MapLibre GL JS + OpenStreetMap | 5.x | BSD |
| **Dosya Depolama** | MinIO (S3-uyumlu) | RELEASE.2024+ | AGPLv3 |
| **CI/CD** | GitHub Actions + Docker Compose | — | — |
| **Monitoring** | Sentry + Prometheus + Grafana | — | BSL / Apache 2 |
| **Reverse Proxy** | Nginx (CloudPanel) | 1.25+ | BSD |

### 1.2 Kritik Karar #1: Frontend — Next.js 15 mi, Başka Bir Framework mü?

| Alternatif | SSR/SEO | Telegram Mini App | Interaktivite | Ekosistem | Karar |
|-----------|---------|-------------------|---------------|-----------|-------|
| **Next.js 15** | ✅ App Router + ISR + RSC | ✅ `/tg` route grubu | ✅ React 19 | ✅ Devasa | **SEÇİLDİ** |
| Astro + React | ✅ Mükemmel statik | ⚠️ Islands mimarisi sınırlı | ⚠️ Dashboard için zayıf | ⚠️ Orta | Elendi |
| Remix | ✅ Nested routes | ⚠️ Daha az yaygın | ✅ İyi | ⚠️ Küçük | Elendi |
| SvelteKit | ✅ İyi | ⚠️ React ekosistemi kaybı | ✅ Çok hızlı | ⚠️ Küçük | Elendi |

**Gerekçe:** Proje hem SEO-kritik sayfalar (ilan detay, bölge analiz) hem de interaktif dashboard (CRM, eşleştirme, harita) içeriyor. Astro iyisiniye projesinde 5000+ statik sayfa için mükemmel çalıştı ama bu proje SaaS dashboard ağırlıklı — React Server Components + Client Components birlikte kullanılmalı. Next.js 15 App Router bu dengeyi en iyi kuruyor.

**Telegram Mini App stratejisi:** Telegram Mini App, Next.js uygulamasının `/tg/*` route grubu olarak yaşayacak. Telegram-spesifik layout (üst bar yok, alt navigasyon) ve `@tma.js/sdk` ile Telegram WebView entegrasyonu sağlanacak. Bu sayede bileşen paylaşımı maksimize edilir.

**Trade-off:** Next.js self-hosted Node.js sunucusu gerektirir (Vercel kullanılmayacak — maliyet ve kontrol). `standalone` output modu + Docker ile deploy edilecek.

### 1.3 Kritik Karar #2: Monorepo mu, Ayrı Repo mu?

| Alternatif | Avantaj | Dezavantaj | Karar |
|-----------|---------|------------|-------|
| **Monorepo (tek repo)** | Atomik değişiklikler, birleşik CI/CD, kolay cross-reference | Repo büyüklüğü, farklı dil tooling karmaşıklığı | **SEÇİLDİ** |
| Ayrı repolar (frontend + backend) | Bağımsız deploy, basit CI | Senkronizasyon zorluğu, API kontrat kopması | Elendi |

**Gerekçe (UniqMys tecrübesi):** UniqMys'te Turborepo monorepo + modüler monolitik NestJS kullanıldı ve iyi çalıştı. Bu projede polyglot (TypeScript + Python) olduğu için Turborepo sadece JS/TS paketlerini yönetecek, Python tarafı kendi tooling'iyle (uv/poetry) yönetilecek. Docker Compose her şeyi birleştirecek.

### 1.4 Kritik Karar #3: Modüler Monolitik mi, Microservice mi?

| Alternatif | MVP Uygunluğu | Karmaşıklık | Deploy | Ölçeklenme | Karar |
|-----------|---------------|-------------|--------|------------|-------|
| **Modüler Monolitik** | ✅ Hızlı geliştirme | Düşük | Basit | Yeterli (MVP) | **SEÇİLDİ** |
| Microservice | ❌ Overengineering | Yüksek | Karmaşık | Çok iyi | Elendi (Faz 2+) |
| Monolitik (düz) | ✅ En basit | En düşük | En basit | Kötü | Elendi |

**Gerekçe (UniqMys tecrübesi):** "Microservice MVP'de overengineering" — bu ders doğrudan uygulanıyor. FastAPI uygulaması modüler yapıda olacak: her domain (auth, valuation, crm, messaging, property, area, eids) kendi router, service ve repository katmanına sahip olacak ama tek process'te çalışacak.

**Faz 2 geçiş planı:** Messaging Gateway ve ML Pipeline en olası ayrılma adayları. Interface/soyutlama katmanı sayesinde (UniqMys pattern) modülü ayırmak minimal refactoring gerektirecek.

### 1.5 Kritik Karar #4: Elasticsearch mi, Meilisearch mi?

| Alternatif | Full-text | Geo | Faceted | RAM | Kurulum | Karar |
|-----------|-----------|-----|---------|-----|---------|-------|
| **PostgreSQL FTS + pg_trgm** (MVP) | ✅ Yeterli | ✅ PostGIS | ✅ SQL | Düşük | Sıfır | **SEÇİLDİ (MVP)** |
| Meilisearch | ✅ Mükemmel typo tolerance | ⚠️ Sınırlı | ✅ İyi | Orta | Kolay | Faz 2 adayı |
| Elasticsearch | ✅ En güçlü | ✅ Tam | ✅ Tam | Yüksek | Zor | Elendi (MVP) |

**Gerekçe (iyisiniye tecrübesi):** iyisiniye'de PostgreSQL FTS + pg_trgm 5000 kayıtta Elasticsearch yerine kullanıldı ve mükemmel çalıştı. Bu projede MVP'de ~5.000-10.000 ilan bekleniyor — PostgreSQL FTS fazlasıyla yeterli. PostGIS zaten geo-distance sorguları çözüyor. Meilisearch, ilan sayısı 50.000+'yı geçtiğinde veya kullanıcılar typo tolerance talep ettiğinde eklenecek.

**Migrasyon planı:** Search işlemleri bir `SearchService` interface'i arkasında soyutlanacak. MVP'de `PostgresSearchService`, Faz 2'de `MeilisearchService` olarak swap edilecek (UniqMys pattern: interface/soyutlama katmanı).

### 1.6 Kritik Karar #5: MinIO mu, AWS S3 mi?

| Alternatif | Maliyet | Kontrol | Performans | Migrasyon | Karar |
|-----------|---------|---------|------------|-----------|-------|
| **MinIO (self-hosted)** | Düşük (sunucu maliyeti) | Tam | LAN hızı | S3 API uyumlu | **SEÇİLDİ (MVP)** |
| AWS S3 | Yüksek (transfer + depolama) | Sınırlı | CDN ile iyi | Vendor lock-in riski | Faz 2 adayı |
| Cloudflare R2 | Orta | Orta | İyi | S3 uyumlu | Yedek plan |

**Gerekçe:** Proje zaten dedicated sunucu (157.173.116.230) üzerinde çalışıyor. MVP'de fotoğraf depolama hacmi ~500GB olacak — sunucu diski yeterli. MinIO S3-uyumlu API sunduğu için `boto3` veya `aiobotocore` ile yazılan kod, AWS S3'e sıfır değişiklikle taşınabilir.

### 1.7 Ek Kararlar

| Karar | Seçim | Gerekçe |
|-------|-------|---------|
| **Python ORM** | SQLAlchemy 2.0 (async) + Alembic | Endüstri standardı, tam async desteği, güçlü query builder |
| **Telegram Bot** | aiogram 3.x (Python, FastAPI'ye entegre) | Backend ile aynı dil, doğrudan DB erişimi, webhook FastAPI route olarak |
| **WhatsApp BSP (Elite)** | 360dialog (birincil) / Twilio (yedek) | Elite plan: Cloud API. Starter/Pro: click-to-chat (BSP gerektirmez). 360dialog: düşük maliyet, Türkiye desteği |
| **PDF Oluşturucu** | WeasyPrint | Python-native, HTML→PDF, raporlar için ideal |
| **OCR (EİDS)** | Tesseract + OpenCV (MVP), Google Cloud Vision (Faz 2) | Self-hosted = sıfır maliyet MVP'de |
| **State Management (FE)** | Zustand (client) + TanStack Query (server) | Hafif, TypeScript-dostu, boilerplate az |
| **Form Validation (FE)** | Zod + React Hook Form | Runtime type safety, Pydantic ile uyumlu şema |
| **TimescaleDB** | EKLENECEK AMA MVP'DE DEĞİL | PostgreSQL extension olarak sonradan eklenebilir, MVP volume'ü gerektirmiyor |

---

## 2. Sistem Mimarisi

### 2.1 High-Level Mimari Diyagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              KULLANICILAR                                        │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ Web App  │  │ Telegram Bot │  │ Telegram     │  │ WhatsApp               │   │
│  │ (Browser)│  │ (Chat)       │  │ Mini App     │  │ c2c(Alpha)/API(Elite)  │   │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘  └────────────┬───────────┘   │
└───────┼────────────────┼────────────────┼───────────────────────┼────────────────┘
        │                │                │                       │
        ▼                ▼                ▼                       ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                            NGINX REVERSE PROXY (CloudPanel)                       │
│  ┌─────────────────────┐  ┌────────────────────────────────────────────────────┐  │
│  │  SSL Termination    │  │  Rate Limiting (limit_req_zone)                    │  │
│  │  Gzip Compression   │  │  /api/* → FastAPI :8000                            │  │
│  │  Static Cache       │  │  /* → Next.js :3000                                │  │
│  └─────────────────────┘  │  /ws/* → FastAPI WebSocket :8000                   │  │
│                           │  /minio/* → MinIO :9000                            │  │
│                           └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────┘
        │                                    │
        ▼                                    ▼
┌──────────────────────┐      ┌──────────────────────────────────────────────────┐
│  NEXT.JS 15 (SSR)    │      │  FASTAPI (MODÜLER MONOLİTİK)                    │
│  ┌────────────────┐  │      │  ┌───────────────────────────────────────────┐   │
│  │ App Router     │  │      │  │  MODÜLLER                                 │   │
│  │ Server Comp.   │  │      │  │  ┌───────┐ ┌─────┐ ┌──────┐ ┌─────────┐ │   │
│  │ ISR Pages      │  │      │  │  │ Auth  │ │ CRM │ │ Prop │ │ Valuat. │ │   │
│  │ /tg/* (Mini)   │◄─┼──────┼──│  ├───────┤ ├─────┤ ├──────┤ ├─────────┤ │   │
│  │ React 19       │  │ API  │  │  │ Area  │ │ Map │ │ EIDS │ │ Listing │ │   │
│  └────────────────┘  │ Call │  │  ├───────┤ ├─────┤ ├──────┤ ├─────────┤ │   │
│  Port: 3000          │      │  │  │ Match │ │ Sub │ │ Pay  │ │ Report  │ │   │
└──────────────────────┘      │  │  └───────┘ └─────┘ └──────┘ └─────────┘ │   │
                              │  └───────────────────────────────────────────┘   │
                              │  ┌───────────────────────────────────────────┐   │
                              │  │  UNIFIED MESSAGING GATEWAY                │   │
                              │  │  ┌──────────┐┌──────────┐┌─────────────┐ │   │
                              │  │  │ Telegram ││ WhatsApp ││ SMS / Email │ │   │
                              │  │  │ Adapter  ││ Adapter  ││ Adapter     │ │   │
                              │  │  └──────────┘└──────────┘└─────────────┘ │   │
                              │  └───────────────────────────────────────────┘   │
                              │  ┌───────────────────────────────────────────┐   │
                              │  │  TELEGRAM BOT (aiogram 3.x)              │   │
                              │  │  Webhook: /api/v1/telegram/webhook       │   │
                              │  └───────────────────────────────────────────┘   │
                              │  Port: 8000                                      │
                              └──────────────┬───────────────────────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
        ┌───────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
        │  PostgreSQL 16    │  │  Redis 7              │  │  MinIO              │
        │  + PostGIS 3.4    │  │  ┌──────────────────┐ │  │  (S3-uyumlu)       │
        │  ┌──────────────┐ │  │  │ Cache (DB 0)     │ │  │  ┌───────────────┐ │
        │  │ Ana Veri      │ │  │  │ Session (DB 1)   │ │  │  │ Fotoğraflar   │ │
        │  │ PostGIS Geo   │ │  │  │ Celery (DB 2)    │ │  │  │ PDF Raporlar  │ │
        │  │ FTS İndeks    │ │  │  │ Rate Limit (DB 3)│ │  │  │ Dokümanlar    │ │
        │  │ pg_trgm       │ │  │  └──────────────────┘ │  │  └───────────────┘ │
        │  └──────────────┘ │  │  Port: 6379            │  │  Port: 9000        │
        │  Port: 5432       │  └──────────────────────┘  └─────────────────────┘
        └───────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────────────┐
        │  CELERY WORKERS                                    │
        │  ┌────────────┐ ┌────────────┐ ┌───────────────┐  │
        │  │ ML Worker  │ │ Scraping   │ │ Notification  │  │
        │  │ (Değerleme │ │ Worker     │ │ Worker        │  │
        │  │  Eğitim)   │ │ (Veri Top.)│ │ (Bildirim)    │  │
        │  └────────────┘ └────────────┘ └───────────────┘  │
        │  ┌────────────┐ ┌────────────┐                    │
        │  │ PDF Worker │ │ Photo      │                    │
        │  │ (Rapor)    │ │ Worker     │                    │
        │  └────────────┘ └────────────┘                    │
        └───────────────────────────────────────────────────┘
```

### 2.2 Unified Messaging Gateway — Detaylı Mimari

```
┌──────────────────────────────────────────────────────────────────┐
│                    UYGULAMA KATMANI                               │
│  CRM Servisi, Bildirim Servisi, Eşleştirme Servisi, vb.         │
│                                                                   │
│  messaging.send(                                                  │
│    recipient=user,                                                │
│    template="match_found",                                        │
│    data={property: ..., score: 0.85},                            │
│    channel=None  # auto-select                                    │
│  )                                                                │
└───────────────────────┬──────────────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│              MESSAGING SERVICE (Kanal-Agnostik)                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  1. Şablon Motoru (Jinja2)                                 │  │
│  │     template_name + data → rendered_content                │  │
│  │  2. Kanal Yönlendirici (Channel Router)                    │  │
│  │     user.preferred_channel → fallback zinciri              │  │
│  │  3. Kota Kontrolü (Plan + Kanal Enablement)                 │  │
│  │     Elite + BSP aktif → kota kontrol; değilse → click-to-chat│ │
│  │  4. Maliyet Optimizasyonu                                  │  │
│  │     Telegram (0 TL) > SMS (0.15 TL) > WhatsApp (0.25 TL) │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│              KANAL ADAPTÖR KATMANI (Strategy Pattern)             │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐│
│  │  TELEGRAM     │  │  WHATSAPP    │  │  SMS     │  │  EMAIL   ││
│  │  Adapter      │  │  Adapter     │  │  Adapter │  │  Adapter ││
│  │              │  │              │  │          │  │          ││
│  │  aiogram 3.x │  │  360dialog   │  │  Netgsm  │  │  SMTP    ││
│  │  Bot API     │  │  Cloud API   │  │  API     │  │  (Mailcow││
│  │  ─────────── │  │  ─────────── │  │          │  │   local) ││
│  │  Maliyet: 0  │  │  ~0.05-0.15  │  │  ~0.15   │  │  ~0      ││
│  │  Rate: 30/sn │  │  Template    │  │  TL/msg  │  │  TL/msg  ││
│  │  Mini App ✅  │  │  zorunlu     │  │          │  │          ││
│  └──────────────┘  └──────────────┘  └──────────┘  └──────────┘│
└──────────────────────────────────────────────────────────────────┘
│                                                                   │
│  FALLBACK ZİNCİRİ:                                                │
│  Telegram → WhatsApp → SMS (acil) → Email (raporlama)            │
│                                                                   │
│  DELIVERY TRACKING:                                               │
│  Her mesaj → Message tablosuna log → status: kanal capability'sine│
│  göre sent/delivered/read (desteklenmeyen statü atlanır)          │
└──────────────────────────────────────────────────────────────────┘
```

**Mesajlaşma Interface'i (Python pseudo-code):**
```python
class MessageChannel(Protocol):
    async def send(self, recipient: str, content: MessageContent) -> DeliveryResult: ...
    async def handle_webhook(self, payload: dict) -> IncomingMessage: ...
    def supports_rich_content(self) -> bool: ...
    def get_capabilities(self) -> dict: ...

# Her adapter bu interface'i implemente eder.
# Yeni kanal eklemek = yeni adapter yazmak (açık/kapalı prensibi).

# get_capabilities() örnek çıktısı (bkz. ADR-0007):
# {
#   "supports_delivered": true,
#   "supports_read": false,
#   "supports_typing_indicator": false,
#   "supports_media_upload": true,
#   "max_message_length": 4096
# }
# UI ve raporlama bu capability'ye göre davranır:
# - capability varsa göster, yoksa graceful degrade et
# - "read rate" KPI sadece supports_read=true kanallarda hesaplanır
```

**Kota Kontrolü — Plan + Kanal Enablement:**
- Plan WhatsApp Cloud API içeriyorsa (Elite) **VE** BSP aktifse → kota kontrolü uygulanır (aylık mesaj limiti)
- Plan WhatsApp API içermiyorsa (Starter/Pro) → WhatsApp Cloud API kanalına route edilmez; click-to-chat (native link) kullanılır, fallback Telegram/SMS/Email
- Starter/Pro planlarında WhatsApp satırı maliyetsizdir (click-to-chat = BSP gerektirmez)

**Mesaj Statü Doğruluğu:**
`sent → delivered → read` statü zinciri **kanal bazlı capability'ye** bağlıdır. Her kanal tüm statüleri desteklemez:
- **Telegram Bot API:** `sent` ✅ | `delivered` ❌ (API sunmaz) | `read` ❌
- **WhatsApp Cloud API (Elite):** `sent` ✅ | `delivered` ✅ | `read` ✅ (webhook callback)
- **SMS:** `sent` ✅ | `delivered` ✅ (DLR) | `read` ❌
- **Email:** `sent` ✅ | `delivered` ❌ (güvenilir değil) | `read` ⚠️ (pixel tracking, güvenilir değil)

UI'da `delivered/read` sadece ilgili kanalın capability'si destekliyorsa gösterilir. Desteklenmiyorsa alan gizlenir, KPI hesaplanmaz.

### 2.3 Authentication / Authorization Mimarisi

```
┌────────────────────────────────────────────────────────────────┐
│                     AUTH AKIŞI                                  │
│                                                                 │
│  WEB:  Email+Password → JWT Access (15dk) + Refresh (30 gün)  │
│  TG:   initData verify → JWT Access (1 saat) + Refresh        │
│  WA:   Webhook verify → Internal service token                 │
│                                                                 │
│  JWT Payload:                                                   │
│  {                                                              │
│    sub: user_id,                                                │
│    office_id: uuid,                                             │
│    role: "agent" | "office_admin" | "office_owner" | "admin",  │
│    plan: "starter" | "pro" | "elite",                          │
│    exp: timestamp                                               │
│  }                                                              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                     RBAC MATRİSİ                               │
│                                                                 │
│  Rol              │ Kendi │ Ofis  │ Ağ    │ Platform           │
│  ─────────────────┼───────┼───────┼───────┼──────────          │
│  Agent            │ CRUD  │ Read  │ Read* │ —                  │
│  Office Admin     │ CRUD  │ CRUD  │ Read* │ —                  │
│  Office Owner     │ CRUD  │ CRUD  │ CRUD* │ —                  │
│  Platform Admin   │ CRUD  │ CRUD  │ CRUD  │ CRUD               │
│                                                                 │
│  * Ağ erişimi: Sadece paylaşıma açık portföyler görünür        │
│  * Multi-tenant: Tüm sorgulara office_id filtresi otomatik     │
│    eklenir (PostgreSQL RLS politikaları ile)                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Veri Modeli

### 3.1 ER Diyagram (Basitleştirilmiş)

```
                                    ┌──────────────┐
                                    │ Subscription │
                                    │──────────────│
                                    │ plan         │
                                    │ status       │
                                    │ limits       │
                                    └──────┬───────┘
                                           │ 1
                                           │
                                    ┌──────▼───────┐         ┌──────────────┐
                            ┌───────│    Office    │────────►│   Payment    │
                            │       │──────────────│    1:N  │──────────────│
                            │       │ name, city   │         │ amount       │
                            │       │ district     │         │ status       │
                            │       │ location     │         └──────────────┘
                            │       └──────┬───────┘
                            │              │ 1
                            │              │
                     1:N    │       ┌──────▼───────┐
                            │       │     User     │
                            │       │──────────────│
                            │       │ role         │
                            │       │ telegram_id  │
                            │       │ pref_channel │
                            │       └──┬───┬───┬───┘
                            │          │   │   │
                   ┌────────┘    ┌─────┘   │   └─────────┐
                   │             │         │              │
            ┌──────▼──────┐  ┌──▼─────┐   │    ┌────────▼────────┐
            │  Property   │  │Customer│   │    │  Conversation   │
            │─────────────│  │────────│   │    │─────────────────│
            │ type, price │  │ budget │   │    │ channel         │
            │ rooms, area │  │ desire │   │    │ external_id     │
            │ location    │  │ status │   │    └────────┬────────┘
            │ status      │  └───┬────┘   │             │ 1
            │ is_shared   │      │        │             │
            └──┬──┬──┬────┘      │        │      ┌──────▼───────┐
               │  │  │           │        │      │   Message    │
               │  │  │     ┌─────▼────┐   │      │──────────────│
               │  │  │     │  Match   │   │      │ content      │
               │  │  │     │─────────│   │      │ channel      │
               │  │  │     │ score   │   │      │ status       │
               │  │  │     │ status  │   │      └──────────────┘
               │  │  │     └─────────┘
               │  │  │
     ┌─────────┘  │  └──────────┐
     │            │             │
┌────▼─────┐ ┌───▼────────┐ ┌──▼──────────┐
│Valuation │ │EIDSRecord  │ │Transaction  │
│──────────│ │────────────│ │─────────────│
│ price_min│ │ eids_num   │ │ amount      │
│ price_max│ │ ocr_result │ │ commission  │
│ confid.  │ │ verified   │ │ status      │
│ model_v  │ └────────────┘ └─────────────┘
└──────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ AreaAnalysis │  │  DepremRisk  │  │ PriceHistory │
│──────────────│  │──────────────│  │──────────────│
│ neighborhood │  │ risk_score   │  │ date         │
│ avg_price    │  │ pga_value    │  │ avg_price    │
│ demographics │  │ soil_class   │  │ listing_cnt  │
│ poi_data     │  │ sources      │  │ source       │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 3.2 Entity Detayları

#### 3.2.1 User (Kullanıcı)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Birincil anahtar |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Giriş e-postası |
| phone | VARCHAR(20) | | Telefon numarası (+90...) |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| full_name | VARCHAR(150) | NOT NULL | Ad soyad |
| avatar_url | VARCHAR(500) | | Profil fotoğrafı (MinIO) |
| role | VARCHAR(20) | NOT NULL | agent, office_admin, office_owner, platform_admin |
| office_id | UUID | FK → Office | Bağlı olduğu ofis |
| telegram_id | BIGINT | UNIQUE, nullable | Telegram user ID |
| whatsapp_phone | VARCHAR(20) | nullable | WhatsApp numarası |
| preferred_channel | VARCHAR(20) | DEFAULT 'telegram' | telegram, whatsapp, sms, email |
| is_active | BOOLEAN | DEFAULT true | Aktif mi |
| is_verified | BOOLEAN | DEFAULT false | E-posta doğrulandı mı |
| last_login_at | TIMESTAMPTZ | nullable | Son giriş zamanı |
| created_at | TIMESTAMPTZ | DEFAULT now() | Oluşturulma |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Güncelleme |

**İndeksler:** `idx_user_email` (UNIQUE), `idx_user_office` (office_id), `idx_user_telegram` (UNIQUE, telegram_id), `idx_user_phone` (phone)

#### 3.2.2 Office (Emlak Ofisi)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | Ofis adı |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-dostu isim |
| logo_url | VARCHAR(500) | | Logo (MinIO) |
| phone | VARCHAR(20) | | İletişim telefonu |
| email | VARCHAR(255) | | İletişim e-postası |
| address | TEXT | | Tam adres |
| location | GEOGRAPHY(POINT, 4326) | | Konum (PostGIS) |
| city | VARCHAR(100) | NOT NULL | Şehir |
| district | VARCHAR(100) | NOT NULL | İlçe |
| tax_number | VARCHAR(20) | | Vergi numarası |
| subscription_id | UUID | FK → Subscription | Aktif abonelik |
| is_active | BOOLEAN | DEFAULT true | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| updated_at | TIMESTAMPTZ | DEFAULT now() | |

**İndeksler:** `idx_office_slug` (UNIQUE), `idx_office_city_district`, `idx_office_location` (GiST)

#### 3.2.3 Property (Mülk / İlan)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| office_id | UUID | FK → Office, NOT NULL | Multi-tenant anahtar |
| agent_id | UUID | FK → User, NOT NULL | Sorumlu danışman |
| title | VARCHAR(300) | NOT NULL | İlan başlığı |
| description | TEXT | | İlan açıklaması |
| property_type | VARCHAR(30) | NOT NULL | apartment, villa, land, commercial, office |
| listing_type | VARCHAR(10) | NOT NULL | sale, rent |
| price | NUMERIC(15,2) | NOT NULL | Fiyat (TRY) |
| currency | VARCHAR(3) | DEFAULT 'TRY' | Para birimi |
| rooms | VARCHAR(20) | | "2+1", "3+1", vb. |
| gross_area | NUMERIC(8,2) | | Brüt m² |
| net_area | NUMERIC(8,2) | | Net m² |
| floor_number | INTEGER | | Bulunduğu kat |
| total_floors | INTEGER | | Toplam kat |
| building_age | INTEGER | | Bina yaşı |
| heating_type | VARCHAR(50) | | Isıtma tipi |
| address | TEXT | | Tam adres |
| location | GEOGRAPHY(POINT, 4326) | NOT NULL | Konum (PostGIS) |
| city | VARCHAR(100) | NOT NULL | Şehir |
| district | VARCHAR(100) | NOT NULL | İlçe |
| neighborhood | VARCHAR(100) | | Mahalle |
| parcel_id | VARCHAR(50) | | Ada/Parsel numarası |
| features | JSONB | DEFAULT '{}' | Esnek özellikler (balkon, garaj, vb.) |
| photos | JSONB | DEFAULT '[]' | Fotoğraf URL dizisi |
| status | VARCHAR(20) | DEFAULT 'active' | active, pending, sold, rented, withdrawn |
| is_shared | BOOLEAN | DEFAULT false | Paylaşım ağında mı |
| share_visibility | VARCHAR(20) | DEFAULT 'private' | private, office, network |
| eids_status | VARCHAR(20) | DEFAULT 'none' | none, pending, verified |
| eids_record_id | UUID | FK → EIDSRecord, nullable | EİDS kaydı |
| views_count | INTEGER | DEFAULT 0 | Görüntülenme |
| search_vector | TSVECTOR | | Full-text search vektörü |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| updated_at | TIMESTAMPTZ | DEFAULT now() | |

**İndeksler:**
- `idx_prop_office` (office_id) — Multi-tenant filtre
- `idx_prop_agent` (agent_id)
- `idx_prop_location` (GiST, location) — Geo sorgular
- `idx_prop_search` (GIN, search_vector) — Full-text arama
- `idx_prop_type_status` (property_type, listing_type, status) — Filtreleme
- `idx_prop_price` (price) — Fiyat aralığı sorguları
- `idx_prop_city_district` (city, district, neighborhood) — Bölge filtresi
- `idx_prop_features` (GIN, features) — JSONB özellik sorguları
- `idx_prop_shared` (is_shared) WHERE is_shared = true — Paylaşım ağı

**FTS Trigger:**
```sql
CREATE FUNCTION property_search_trigger() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('turkish', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('turkish', coalesce(NEW.description, '')), 'B') ||
    setweight(to_tsvector('turkish', coalesce(NEW.neighborhood, '')), 'A') ||
    setweight(to_tsvector('turkish', coalesce(NEW.district, '')), 'A');
  RETURN NEW;
END $$ LANGUAGE plpgsql;
```

#### 3.2.4 PropertyValuation (Değerleme)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| property_id | UUID | FK → Property, nullable | Bağlı mülk (opsiyonel) |
| user_id | UUID | FK → User, NOT NULL | İsteyen kullanıcı |
| office_id | UUID | FK → Office, NOT NULL | Multi-tenant |
| address | TEXT | NOT NULL | Değerlenen adres |
| location | GEOGRAPHY(POINT, 4326) | NOT NULL | Konum |
| input_params | JSONB | NOT NULL | m², oda, kat, yaş, vb. |
| estimated_price_min | NUMERIC(15,2) | NOT NULL | Alt sınır |
| estimated_price_max | NUMERIC(15,2) | NOT NULL | Üst sınır |
| estimated_price_avg | NUMERIC(15,2) | NOT NULL | Ortalama tahmin |
| confidence_score | NUMERIC(5,4) | NOT NULL | 0.0 — 1.0 güven |
| model_version | VARCHAR(50) | NOT NULL | Kullanılan model versiyonu |
| comparables | JSONB | DEFAULT '[]' | Emsal mülkler listesi |
| price_per_sqm | NUMERIC(10,2) | | Tahmini m² fiyatı |
| area_avg_price_per_sqm | NUMERIC(10,2) | | Bölge ort. m² fiyatı |
| report_url | VARCHAR(500) | nullable | Oluşturulan PDF rapor |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.5 Customer (Müşteri)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| office_id | UUID | FK → Office, NOT NULL | Multi-tenant |
| agent_id | UUID | FK → User, NOT NULL | Sorumlu danışman |
| full_name | VARCHAR(150) | NOT NULL | Ad soyad |
| phone | VARCHAR(20) | | Telefon |
| email | VARCHAR(255) | | E-posta |
| customer_type | VARCHAR(20) | NOT NULL | buyer, seller, renter, landlord |
| budget_min | NUMERIC(15,2) | | Minimum bütçe |
| budget_max | NUMERIC(15,2) | | Maksimum bütçe |
| desired_rooms | VARCHAR(50) | | "2+1", "3+1" vb. |
| desired_area_min | INTEGER | | Min m² |
| desired_area_max | INTEGER | | Max m² |
| desired_districts | JSONB | DEFAULT '[]' | ["Kadıköy", "Üsküdar"] |
| notes | TEXT | | Serbest notlar |
| tags | JSONB | DEFAULT '[]' | Etiketler |
| lead_status | VARCHAR(20) | DEFAULT 'warm' | cold, warm, hot, converted, lost |
| source | VARCHAR(20) | | manual, telegram, whatsapp, web, referral |
| last_contact_at | TIMESTAMPTZ | | Son iletişim |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| updated_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.6 Match (Eşleştirme)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| customer_id | UUID | FK → Customer, NOT NULL | Eşleşen müşteri |
| property_id | UUID | FK → Property, NOT NULL | Eşleşen mülk |
| match_score | NUMERIC(5,4) | NOT NULL | 0.0 — 1.0 uyum skoru |
| match_reasons | JSONB | DEFAULT '[]' | Eşleşme gerekçeleri |
| status | VARCHAR(20) | DEFAULT 'new' | new, notified, viewed, interested, rejected |
| notified_at | TIMESTAMPTZ | nullable | Bildirim zamanı |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**UNIQUE constraint:** (customer_id, property_id) — Aynı çift tekrarlanmaz.

#### 3.2.7 Conversation & Message (Mesajlaşma)

**Conversation:**

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| office_id | UUID | FK → Office | Multi-tenant |
| agent_id | UUID | FK → User | Danışman |
| customer_id | UUID | FK → Customer, nullable | Müşteri (biliniyorsa) |
| channel | VARCHAR(20) | NOT NULL | telegram, whatsapp, sms, email |
| external_chat_id | VARCHAR(255) | | Kanal chat ID'si |
| status | VARCHAR(20) | DEFAULT 'active' | active, archived, closed |
| last_message_at | TIMESTAMPTZ | | Son mesaj zamanı |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**Message:**

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| conversation_id | UUID | FK → Conversation, NOT NULL | Bağlı konuşma |
| sender_type | VARCHAR(20) | NOT NULL | agent, customer, system |
| sender_id | UUID | | Gönderenin ID'si |
| channel | VARCHAR(20) | NOT NULL | telegram, whatsapp, sms, email |
| content_type | VARCHAR(20) | DEFAULT 'text' | text, image, document, location, template |
| content | TEXT | NOT NULL | Mesaj içeriği |
| metadata | JSONB | DEFAULT '{}' | Kanal-spesifik veri |
| status | VARCHAR(20) | DEFAULT 'sent' | sent, delivered, read, failed |
| external_id | VARCHAR(255) | | Kanalın mesaj ID'si |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.8 Notification (Bildirim)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| user_id | UUID | FK → User, NOT NULL | Hedef kullanıcı |
| type | VARCHAR(100) | NOT NULL | match_found, price_change, report_ready, vb. |
| title | VARCHAR(300) | NOT NULL | Bildirim başlığı |
| body | TEXT | | Bildirim içeriği |
| data | JSONB | DEFAULT '{}' | Ek veri (entity_id, vb.) |
| channel | VARCHAR(20) | DEFAULT 'in_app' | in_app, telegram, whatsapp, sms, email |
| status | VARCHAR(20) | DEFAULT 'pending' | pending, sent, delivered, read, failed |
| sent_at | TIMESTAMPTZ | nullable | Gönderim zamanı |
| read_at | TIMESTAMPTZ | nullable | Okunma zamanı |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.9 EIDSRecord (EİDS Doğrulama)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| property_id | UUID | FK → Property, NOT NULL | İlgili mülk |
| office_id | UUID | FK → Office, NOT NULL | Multi-tenant |
| eids_number | VARCHAR(50) | NOT NULL | EİDS belge numarası |
| document_url | VARCHAR(500) | nullable | Yüklenen belge (MinIO) |
| ocr_result | JSONB | nullable | OCR çıktısı |
| verification_status | VARCHAR(20) | DEFAULT 'pending' | pending, verified, rejected |
| verified_by | UUID | FK → User, nullable | Doğrulayan (admin) |
| verified_at | TIMESTAMPTZ | nullable | Doğrulama zamanı |
| rejection_reason | TEXT | nullable | Ret gerekçesi |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.10 DepremRisk (Deprem Riski)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| location | GEOGRAPHY(POINT, 4326) | NOT NULL | Konum |
| city | VARCHAR(100) | NOT NULL | Şehir |
| district | VARCHAR(100) | NOT NULL | İlçe |
| neighborhood | VARCHAR(100) | | Mahalle |
| risk_score | NUMERIC(5,2) | NOT NULL | 0-100 arası risk skoru |
| pga_value | NUMERIC(6,4) | | Peak Ground Acceleration (g) |
| soil_class | VARCHAR(10) | | ZA, ZB, ZC, ZD, ZE |
| building_code_era | VARCHAR(50) | | pre_1999, 1999_2018, post_2018 |
| data_sources | JSONB | DEFAULT '[]' | Veri kaynakları listesi |
| last_updated | TIMESTAMPTZ | DEFAULT now() | Son güncelleme |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.11 AreaAnalysis (Bölge Analizi)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| city | VARCHAR(100) | NOT NULL | Şehir |
| district | VARCHAR(100) | NOT NULL | İlçe |
| neighborhood | VARCHAR(100) | | Mahalle |
| boundary | GEOGRAPHY(POLYGON, 4326) | | Bölge sınırı |
| avg_price_sqm_sale | NUMERIC(10,2) | | Ort. satılık m² fiyatı |
| avg_price_sqm_rent | NUMERIC(10,2) | | Ort. kiralık m² fiyatı |
| price_trend_6m | NUMERIC(5,2) | | 6 aylık fiyat değişimi % |
| supply_demand_ratio | NUMERIC(5,2) | | Arz/talep oranı |
| population | INTEGER | | Nüfus |
| demographics | JSONB | DEFAULT '{}' | Yaş dağılımı, eğitim, gelir |
| poi_data | JSONB | DEFAULT '{}' | Okul, hastane, metro, market sayıları |
| transport_score | NUMERIC(5,2) | | Ulaşım skoru (0-100) |
| amenity_score | NUMERIC(5,2) | | Yaşam kalitesi skoru |
| investment_score | NUMERIC(5,2) | | Yatırım skoru |
| amortization_years | NUMERIC(5,1) | | Amortisman süresi (yıl) |
| last_updated | TIMESTAMPTZ | DEFAULT now() | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**UNIQUE constraint:** (city, district, neighborhood)

#### 3.2.12 Subscription (Abonelik)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| office_id | UUID | FK → Office, UNIQUE, NOT NULL | Tek abonelik/ofis |
| plan | VARCHAR(20) | NOT NULL | starter, pro, elite |
| status | VARCHAR(20) | DEFAULT 'trial' | active, trial, past_due, cancelled |
| price_monthly | NUMERIC(10,2) | NOT NULL | Aylık ücret (TRY) |
| max_agents | INTEGER | NOT NULL | Maks danışman sayısı |
| max_properties | INTEGER | NOT NULL | Maks portföy sayısı |
| max_customers | INTEGER | NOT NULL | Maks müşteri sayısı |
| max_valuations_monthly | INTEGER | NOT NULL | Aylık değerleme limiti |
| features | JSONB | DEFAULT '{}' | Ek özellik bayrakları |
| trial_ends_at | TIMESTAMPTZ | nullable | Deneme bitişi |
| current_period_start | TIMESTAMPTZ | NOT NULL | Dönem başlangıcı |
| current_period_end | TIMESTAMPTZ | NOT NULL | Dönem bitişi |
| cancelled_at | TIMESTAMPTZ | nullable | İptal zamanı |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**Plan limitleri (varsayılan):**

| Limit | Starter (399₺) | Pro (799₺) | Elite (1.499₺) |
|-------|:-:|:-:|:-:|
| max_agents | 1 | 3 | 10 |
| max_properties | 20 | 100 | ∞ (999999) |
| max_customers | 50 | 500 | ∞ |
| max_valuations_monthly | 10 | 100 | ∞ |

#### 3.2.13 Payment (Ödeme)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| office_id | UUID | FK → Office, NOT NULL | |
| subscription_id | UUID | FK → Subscription, NOT NULL | |
| amount | NUMERIC(10,2) | NOT NULL | Ödeme tutarı |
| currency | VARCHAR(3) | DEFAULT 'TRY' | |
| status | VARCHAR(20) | DEFAULT 'pending' | pending, completed, failed, refunded |
| payment_method | VARCHAR(50) | | credit_card, bank_transfer |
| external_payment_id | VARCHAR(255) | | Ödeme gateway ID |
| invoice_url | VARCHAR(500) | | Fatura PDF |
| paid_at | TIMESTAMPTZ | nullable | Ödeme zamanı |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.14 Transaction (Satış/Kira İşlemi)

| Alan | Tip | Constraint | Açıklama |
|------|-----|-----------|----------|
| id | UUID | PK | |
| property_id | UUID | FK → Property, NOT NULL | |
| customer_id | UUID | FK → Customer, NOT NULL | |
| agent_id | UUID | FK → User, NOT NULL | |
| office_id | UUID | FK → Office, NOT NULL | Multi-tenant |
| transaction_type | VARCHAR(10) | NOT NULL | sale, rent |
| amount | NUMERIC(15,2) | NOT NULL | İşlem tutarı |
| commission_amount | NUMERIC(15,2) | | Komisyon tutarı |
| commission_rate | NUMERIC(5,4) | | Komisyon oranı |
| status | VARCHAR(20) | DEFAULT 'pending' | pending, completed, cancelled |
| notes | TEXT | | İşlem notları |
| closed_at | TIMESTAMPTZ | nullable | Kapanış zamanı |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

#### 3.2.15 Yardımcı Tablolar

**PriceHistory (Fiyat Geçmişi):**

| Alan | Tip | Açıklama |
|------|-----|----------|
| id | BIGSERIAL | PK (UUID değil, yüksek hacim) |
| area_type | VARCHAR(20) | neighborhood, district, city |
| area_name | VARCHAR(100) | Bölge adı |
| city | VARCHAR(100) | Şehir |
| date | DATE | Tarih |
| avg_price_sqm | NUMERIC(10,2) | Ortalama m² fiyatı |
| median_price | NUMERIC(15,2) | Medyan fiyat |
| listing_count | INTEGER | İlan sayısı |
| source | VARCHAR(50) | Veri kaynağı |
| created_at | TIMESTAMPTZ | |

**ScrapedListing (Toplanan İlan Verisi):**

| Alan | Tip | Açıklama |
|------|-----|----------|
| id | BIGSERIAL | PK |
| source | VARCHAR(50) | sahibinden, hepsiemlak, vb. |
| external_id | VARCHAR(100) | Kaynak sitedeki ID |
| title | VARCHAR(500) | İlan başlığı |
| price | NUMERIC(15,2) | Fiyat |
| rooms | VARCHAR(20) | Oda sayısı |
| area_sqm | NUMERIC(8,2) | m² |
| location | GEOGRAPHY(POINT) | Konum |
| city | VARCHAR(100) | |
| district | VARCHAR(100) | |
| neighborhood | VARCHAR(100) | |
| raw_data | JSONB | Ham veri |
| scraped_at | TIMESTAMPTZ | Çekilme zamanı |
| UNIQUE(source, external_id) | | Tekrar engeli |

**AuditLog (Denetim İzi):**

| Alan | Tip | Açıklama |
|------|-----|----------|
| id | BIGSERIAL | PK |
| user_id | UUID | İşlemi yapan |
| office_id | UUID | Multi-tenant |
| action | VARCHAR(100) | create, update, delete, login, export, vb. |
| entity_type | VARCHAR(100) | property, customer, valuation, vb. |
| entity_id | UUID | İlgili kayıt |
| changes | JSONB | {old: {...}, new: {...}} |
| ip_address | INET | IP adresi |
| user_agent | TEXT | Tarayıcı bilgisi |
| created_at | TIMESTAMPTZ | |

**UsageQuota (Kullanım Kotası):**

| Alan | Tip | Açıklama |
|------|-----|----------|
| id | UUID | PK |
| office_id | UUID | FK → Office |
| period_start | DATE | Dönem başı |
| period_end | DATE | Dönem sonu |
| valuations_used | INTEGER | Kullanılan değerleme |
| listings_used | INTEGER | Kullanılan ilan oluşturma |
| photos_used | INTEGER | Kullanılan fotoğraf işleme |
| wa_messages_used | INTEGER | Kullanılan WhatsApp mesajı |

### 3.3 Multi-Tenant Strateji

**Yaklaşım:** Row-Level Security (RLS) ile satır bazlı izolasyon.

```sql
-- RLS politikası örneği (Property tablosu)
ALTER TABLE property ENABLE ROW LEVEL SECURITY;
ALTER TABLE property FORCE ROW LEVEL SECURITY;  -- owner bypass koruması (ADR-0001)

CREATE POLICY office_isolation ON property
  USING (office_id = current_setting('app.current_office_id', true)::uuid);
  -- missing-ok=true: setting yoksa NULL döner → policy erişimi kapatır (güvenli varsayılan)

-- Portföy paylaşım ağı istisnası
CREATE POLICY shared_properties ON property
  FOR SELECT
  USING (is_shared = true AND share_visibility = 'network');
```

**FastAPI middleware'de (SET LOCAL + transaction scope):**

> **Neden `SET LOCAL`?** Connection pool reuse ortamında (async/uvicorn + SQLAlchemy) session-level `SET` kalıntısı tenant sızıntısına yol açabilir. `SET LOCAL` transaction scope'una kapalıdır ve COMMIT/ROLLBACK ile otomatik temizlenir. (bkz. ADR-0001)

```python
@app.middleware("http")
async def set_tenant_context(request, call_next):
    if request.user:
        async with db.begin() as transaction:
            # SET LOCAL: transaction scope — pool reuse'da sızıntı riski yok
            await transaction.execute(
                text("SET LOCAL app.current_office_id = :office_id"),
                {"office_id": str(request.user.office_id)}
            )
            response = await call_next(request)
            # COMMIT/ROLLBACK ile SET LOCAL otomatik temizlenir
        return response
    return await call_next(request)
```

**Cross-Tenant Erişim Testleri:**
- **Tenant izolasyon testi:** Tenant A ile giriş → Tenant B verisine erişim denemesi → başarısız olmalı (integration + unit)
- **Pool reuse senaryosu:** Aynı process içinde ardışık farklı tenant request'leri → önceki tenant verisi sızmamalı
- **Owner bypass testi:** `app_user` rolüyle `FORCE RLS` aktifken direkt SQL ile cross-tenant erişim denemesi → başarısız olmalı

### 3.4 İndeks Stratejisi Özeti

| Tablo | İndeks Tipi | Sütun(lar) | Amaç |
|-------|-------------|-----------|-------|
| Property | GiST | location | Geo-distance sorguları |
| Property | GIN | search_vector | Full-text arama |
| Property | GIN | features | JSONB özellik filtre |
| Property | B-tree | (office_id, status, listing_type) | En sık sorgu paterni |
| Property | B-tree | price | Fiyat aralığı filtre |
| AreaAnalysis | GiST | boundary | Spatial contains sorguları |
| PriceHistory | B-tree | (city, district, date) | Trend sorguları |
| Message | B-tree | (conversation_id, created_at) | Mesaj sıralama |
| Match | B-tree | (customer_id, status) | Eşleştirme listesi |
| AuditLog | B-tree | (entity_type, entity_id, created_at) | Denetim izleme |

---

## 4. API Tasarımı

### 4.1 Genel Prensipler

| Prensip | Detay |
|---------|-------|
| **Stil** | RESTful (kaynak tabanlı URL, HTTP method semantiği) |
| **Versiyon** | URL tabanlı: `/api/v1/...` |
| **Kimlik doğrulama** | Bearer JWT token (Authorization header) |
| **Format** | JSON (request + response) |
| **Sayfalama** | Cursor-based (performans) + offset-based (basit sorgular) |
| **Filtreleme** | Query params: `?status=active&city=İstanbul&min_price=500000` |
| **Sıralama** | `?sort=-created_at` (- prefix = DESC) |
| **Hata formatı** | RFC 7807 (Problem Details for HTTP APIs) |

### 4.2 Hata Formatı Standardı

```json
{
  "type": "https://emlak.api/errors/validation",
  "title": "Doğrulama Hatası",
  "status": 422,
  "detail": "Fiyat alanı pozitif bir sayı olmalıdır.",
  "instance": "/api/v1/properties",
  "errors": [
    {
      "field": "price",
      "message": "Pozitif bir sayı giriniz.",
      "code": "positive_number"
    }
  ],
  "request_id": "req_abc123"
}
```

### 4.3 Endpoint Listesi

#### Auth (Kimlik Doğrulama)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| POST | `/api/v1/auth/register` | Yeni kullanıcı/ofis kaydı | ❌ |
| POST | `/api/v1/auth/login` | E-posta + şifre ile giriş | ❌ |
| POST | `/api/v1/auth/refresh` | Access token yenileme | 🔄 Refresh |
| POST | `/api/v1/auth/forgot-password` | Şifre sıfırlama e-postası | ❌ |
| POST | `/api/v1/auth/reset-password` | Şifre sıfırlama (token ile) | ❌ |
| POST | `/api/v1/auth/telegram` | Telegram initData ile giriş | ❌ |
| GET | `/api/v1/auth/me` | Mevcut kullanıcı bilgisi | ✅ |
| POST | `/api/v1/auth/logout` | Oturumu kapat (refresh token invalidate) | ✅ |

#### Properties (Mülk / İlan)

| Method | Endpoint | Açıklama | Auth | Rol |
|--------|----------|----------|:----:|-----|
| POST | `/api/v1/properties` | Yeni mülk ekle | ✅ | Agent+ |
| GET | `/api/v1/properties` | Mülk listesi (filtreli, sayfalı) | ✅ | Agent+ |
| GET | `/api/v1/properties/:id` | Mülk detayı | ✅ | Agent+ |
| PATCH | `/api/v1/properties/:id` | Mülk güncelle | ✅ | Owner |
| DELETE | `/api/v1/properties/:id` | Mülk sil (soft delete) | ✅ | Owner |
| GET | `/api/v1/properties/search` | Full-text + geo arama | ✅ | Agent+ |
| POST | `/api/v1/properties/:id/share` | Paylaşım ağına aç/kapat | ✅ | Owner (Pro+) |
| GET | `/api/v1/properties/network` | Paylaşım ağı ilanları | ✅ | Pro+ |
| POST | `/api/v1/properties/:id/photos` | Fotoğraf yükle (multipart) | ✅ | Owner |

#### Valuations (AI Değerleme)

| Method | Endpoint | Açıklama | Auth | Kota |
|--------|----------|----------|:----:|------|
| POST | `/api/v1/valuations` | Yeni değerleme iste | ✅ | Plan limiti |
| GET | `/api/v1/valuations/:id` | Değerleme detayı | ✅ | |
| GET | `/api/v1/valuations/:id/pdf` | PDF rapor indir | ✅ | |
| GET | `/api/v1/valuations` | Değerleme geçmişi | ✅ | |
| GET | `/api/v1/valuations/:id/comparables` | Emsal mülkler | ✅ | |

#### Customers (Müşteri - CRM)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| POST | `/api/v1/customers` | Yeni müşteri ekle | ✅ |
| GET | `/api/v1/customers` | Müşteri listesi | ✅ |
| GET | `/api/v1/customers/:id` | Müşteri detayı | ✅ |
| PATCH | `/api/v1/customers/:id` | Müşteri güncelle | ✅ |
| DELETE | `/api/v1/customers/:id` | Müşteri sil | ✅ |
| GET | `/api/v1/customers/:id/matches` | Müşterinin eşleşmeleri | ✅ |
| POST | `/api/v1/customers/:id/notes` | Not ekle | ✅ |
| GET | `/api/v1/customers/:id/timeline` | İletişim geçmişi | ✅ |

#### Matches (Eşleştirme)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| GET | `/api/v1/matches` | Eşleştirme listesi | ✅ |
| PATCH | `/api/v1/matches/:id` | Durum güncelle (interested/rejected) | ✅ |
| POST | `/api/v1/matches/run` | Manuel eşleştirme çalıştır | ✅ |

#### Areas (Bölge Analiz)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| GET | `/api/v1/areas/:city/:district` | İlçe analiz kartı | ✅ |
| GET | `/api/v1/areas/:city/:district/:neighborhood` | Mahalle analiz kartı | ✅ |
| GET | `/api/v1/areas/compare?areas=X,Y` | Bölge karşılaştırma | ✅ (Pro+) |
| GET | `/api/v1/areas/:city/:district/trends` | Fiyat trendi | ✅ |

#### Earthquake (Deprem Risk)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| GET | `/api/v1/earthquake/risk?lat=X&lng=Y` | Konum bazlı risk skoru | ✅ |
| GET | `/api/v1/earthquake/building?year=X&floors=Y&lat=X&lng=Y` | Bina güvenlik skoru | ✅ |

#### Listings (AI İlan Asistanı)

| Method | Endpoint | Açıklama | Auth | Kota |
|--------|----------|----------|:----:|------|
| POST | `/api/v1/listings/generate-text` | AI ile ilan metni üret | ✅ | Pro+ |
| POST | `/api/v1/listings/enhance-photo` | Fotoğraf iyileştirme | ✅ | Pro+ |
| POST | `/api/v1/listings/virtual-staging` | Virtual staging (Beta) | ✅ | Elite |
| POST | `/api/v1/listings/export` | Çoklu portal format export | ✅ | Pro+ |

#### Messaging (Mesajlaşma)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| POST | `/api/v1/messages/send` | Mesaj gönder (kanal-agnostik) | ✅ |
| GET | `/api/v1/conversations` | Konuşma listesi | ✅ |
| GET | `/api/v1/conversations/:id/messages` | Konuşma mesajları | ✅ |
| POST | `/api/v1/telegram/webhook` | Telegram webhook (internal) | 🔑 Secret |
| POST | `/api/v1/whatsapp/webhook` | WhatsApp webhook (internal) | 🔑 Secret |

#### EIDS (Doğrulama)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| POST | `/api/v1/eids/verify` | Manuel numara doğrulama | ✅ (Pro+) |
| POST | `/api/v1/eids/upload-document` | Belge yükle + OCR | ✅ (Pro+) |
| GET | `/api/v1/eids/:id` | Doğrulama durumu | ✅ |

#### Calculator (Kredi Hesaplayıcı)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| POST | `/api/v1/calculator/credit` | Kredi hesapla | ✅ |
| GET | `/api/v1/calculator/rates` | Güncel faiz oranları | ✅ |

#### Subscriptions & Payments

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| GET | `/api/v1/subscriptions/plans` | Mevcut planlar | ❌ |
| POST | `/api/v1/subscriptions` | Abone ol | ✅ (Owner) |
| GET | `/api/v1/subscriptions/current` | Mevcut abonelik | ✅ |
| PATCH | `/api/v1/subscriptions/current` | Plan değiştir | ✅ (Owner) |
| POST | `/api/v1/subscriptions/current/cancel` | İptal et | ✅ (Owner) |
| GET | `/api/v1/payments` | Ödeme geçmişi | ✅ (Owner) |

#### Reports (Raporlama — Elite)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| GET | `/api/v1/reports/office-summary` | Ofis özet raporu | ✅ (Elite) |
| GET | `/api/v1/reports/agent-performance` | Danışman performans KPI | ✅ (Elite) |
| GET | `/api/v1/reports/market-trends` | Pazar trend raporu | ✅ (Pro+) |

#### Notifications

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| GET | `/api/v1/notifications` | Bildirim listesi | ✅ |
| PATCH | `/api/v1/notifications/:id/read` | Okundu işaretle | ✅ |
| PATCH | `/api/v1/notifications/read-all` | Tümünü okundu yap | ✅ |
| PUT | `/api/v1/notifications/preferences` | Bildirim tercihleri | ✅ |

#### Maps (Harita)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|----------|:----:|
| GET | `/api/v1/maps/properties?bbox=...` | Harita sınırları içi mülkler (GeoJSON) | ✅ |
| GET | `/api/v1/maps/heatmap?type=price` | Isı haritası verisi | ✅ |
| GET | `/api/v1/maps/poi?lat=X&lng=Y&radius=1000` | Çevre POI'ler | ✅ |

### 4.4 WebSocket Kullanım Alanları

| Endpoint | Amaç | Veri Akışı |
|----------|-------|-----------|
| `ws://host/ws?token=JWT` | Unified WebSocket (tum event tipleri) | Bidirectional |

**Planlanan Event Tipleri:**

| EventType | Amaç | Tetikleyici |
|-----------|-------|-------------|
| `notification` | Gercek zamanli bildirimler | NotificationService.create() |
| `match_update` | Yeni eslesme alertleri | MatchingService (gelecek) |
| `valuation_complete` | Degerleme tamamlandi | ValuationService (gelecek) |
| `system` | Sistem duyurulari, bakim | Manuel broadcast |

**Mevcut Durum: STUB (v0)**

Temel altyapi kuruldu, varsayilan **KAPALI** (`NEXT_PUBLIC_WS_ENABLED=false`):

- **Backend:** `apps/api/src/modules/realtime/`
  - `ConnectionManager` — in-memory baglanti yonetimi (user_id -> [WebSocket])
  - `WebSocket Router` — JWT auth, heartbeat ping-pong, echo
  - `EventType` enum + `WebSocketEvent` dataclass
  - `emit_event()` — fire-and-forget event emitter (graceful degradation)
  - `NotificationService` entegrasyonu — bildirim olusturulunca WS event emit

- **Frontend:** `apps/web/src/`
  - `hooks/use-websocket.ts` — auto-reconnect (exponential backoff), heartbeat, connection state
  - `providers/websocket-provider.tsx` — React Context, env flag ile kontrol
  - `types/websocket.ts` — backend ile senkron tip tanimlari

- **Guvenlik:** JWT query param dogrulama, TenantMiddleware bypass (`/ws` prefix)
- **Graceful Degradation:** WS hatasi uygulama akisini kesmez, bildirimler yine DB'ye yazilir

**Gelecek Plan (v1):**

| Ozellik | Sprint | Oncelik |
|---------|--------|---------|
| Redis PubSub (coklu worker sync) | S3-S4 | Yuksek |
| Canli mesajlasma (bidirectional) | S4-S5 | Orta |
| Connection monitoring (Prometheus) | S3 | Dusuk |
| Token blacklist kontrolu (WS) | S3 | Orta |
| Rate limiting (WS mesaj) | S4 | Dusuk |
| Event persistence (offline kuyruk) | S5+ | Dusuk |

**Implementasyon Hedefi:** FastAPI WebSocket + Redis PubSub (coklu worker senkronizasyonu)

### 4.5 Rate Limiting Stratejisi

| Endpoint Grubu | Limit | Pencere | Aşıldığında |
|----------------|:-----:|:-------:|-------------|
| Auth (login, register) | 10 | 1 dakika | 429 + 60sn bekleme |
| AI endpoints (valuation, listing) | Plan kotası | 1 ay | 429 + kota bilgisi |
| Genel API | 100 | 1 dakika | 429 + Retry-After header |
| Webhook (Telegram, WhatsApp) | 1000 | 1 dakika | Log + silent drop |

**Implementasyon:** Redis sliding window counter (FastAPI middleware).

### 4.6 API Versiyonlama

- **v1:** MVP-Alpha ve Beta boyunca sabit.
- **v2:** Breaking change gerektiğinde (tahminen Faz 2+). v1 en az 6 ay desteklenir.
- Header-based versiyonlama KULLANILMAYACAK (basitlik prensibi). URL-based yeterli.

---

## 5. Monorepo / Klasör Yapısı

### 5.1 Proje Klasör Ağacı

```
emlak-platform/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint + test + type-check
│       ├── deploy-staging.yml        # Staging deploy
│       └── deploy-production.yml     # Production deploy
│
├── apps/
│   ├── web/                          # Next.js 15 Web Uygulaması
│   │   ├── src/
│   │   │   ├── app/                  # App Router
│   │   │   │   ├── (auth)/           # Auth sayfaları (login, register)
│   │   │   │   ├── (dashboard)/      # Ana dashboard layout
│   │   │   │   │   ├── properties/   # Mülk yönetimi
│   │   │   │   │   ├── customers/    # CRM
│   │   │   │   │   ├── valuations/   # Değerleme
│   │   │   │   │   ├── maps/         # Harita görünümü
│   │   │   │   │   ├── areas/        # Bölge analiz
│   │   │   │   │   ├── network/      # Portföy paylaşım ağı
│   │   │   │   │   ├── listings/     # AI ilan asistanı
│   │   │   │   │   ├── messages/     # Mesajlaşma
│   │   │   │   │   ├── reports/      # Raporlar (Elite)
│   │   │   │   │   ├── settings/     # Ayarlar
│   │   │   │   │   └── layout.tsx    # Dashboard shell
│   │   │   │   ├── tg/              # Telegram Mini App route grubu
│   │   │   │   │   ├── layout.tsx    # TG-spesifik layout (no header)
│   │   │   │   │   ├── page.tsx      # Mini App dashboard
│   │   │   │   │   ├── valuation/    # Değerleme (Mini App)
│   │   │   │   │   └── crm/          # CRM (Mini App)
│   │   │   │   ├── api/              # BFF API routes (opsiyonel)
│   │   │   │   ├── layout.tsx        # Root layout
│   │   │   │   └── page.tsx          # Landing page
│   │   │   ├── components/           # Shared React bileşenleri
│   │   │   │   ├── ui/               # Temel UI (Button, Input, Card, vb.)
│   │   │   │   ├── forms/            # Form bileşenleri
│   │   │   │   ├── maps/             # Harita bileşenleri
│   │   │   │   ├── charts/           # Grafik bileşenleri
│   │   │   │   └── layout/           # Layout bileşenleri
│   │   │   ├── lib/                  # Utility fonksiyonlar
│   │   │   │   ├── api-client.ts     # FastAPI client (fetch wrapper)
│   │   │   │   ├── auth.ts           # Auth helpers
│   │   │   │   ├── telegram.ts       # TG Mini App SDK helpers
│   │   │   │   └── utils.ts          # Genel utility
│   │   │   ├── hooks/                # Custom React hooks
│   │   │   ├── stores/               # Zustand stores
│   │   │   ├── types/                # TypeScript type tanımları
│   │   │   └── styles/               # Global CSS, Tailwind config
│   │   ├── public/                   # Statik dosyalar
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── api/                          # FastAPI Backend
│       ├── src/
│       │   ├── main.py               # FastAPI app entry point
│       │   ├── config.py             # Pydantic Settings
│       │   ├── database.py           # SQLAlchemy async engine + session
│       │   ├── dependencies.py       # FastAPI Depends (auth, db, tenant)
│       │   ├── middleware/
│       │   │   ├── auth.py           # JWT middleware
│       │   │   ├── tenant.py         # Multi-tenant context
│       │   │   ├── rate_limit.py     # Rate limiting
│       │   │   └── logging.py        # Request logging
│       │   ├── modules/              # Domain modülleri
│       │   │   ├── auth/
│       │   │   │   ├── router.py     # Auth endpoints
│       │   │   │   ├── service.py    # Auth business logic
│       │   │   │   ├── schemas.py    # Pydantic models
│       │   │   │   └── utils.py      # JWT, password hashing
│       │   │   ├── property/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py
│       │   │   │   ├── repository.py # Data access layer
│       │   │   │   ├── schemas.py
│       │   │   │   └── search.py     # FTS + geo search
│       │   │   ├── valuation/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py
│       │   │   │   ├── ml_engine.py  # LightGBM inference
│       │   │   │   ├── pdf_report.py # WeasyPrint PDF
│       │   │   │   └── schemas.py
│       │   │   ├── customer/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py
│       │   │   │   ├── repository.py
│       │   │   │   └── schemas.py
│       │   │   ├── match/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py    # Eşleştirme algoritması
│       │   │   │   └── schemas.py
│       │   │   ├── messaging/
│       │   │   │   ├── router.py     # Webhook endpoints
│       │   │   │   ├── gateway.py    # Unified Messaging Gateway
│       │   │   │   ├── adapters/
│       │   │   │   │   ├── base.py   # Abstract adapter
│       │   │   │   │   ├── telegram.py
│       │   │   │   │   ├── whatsapp.py
│       │   │   │   │   ├── sms.py
│       │   │   │   │   └── email.py
│       │   │   │   ├── templates/    # Mesaj şablonları (Jinja2)
│       │   │   │   └── schemas.py
│       │   │   ├── telegram_bot/
│       │   │   │   ├── bot.py        # aiogram Bot instance
│       │   │   │   ├── handlers/     # Command & callback handlers
│       │   │   │   ├── keyboards.py  # Inline keyboards
│       │   │   │   └── middleware.py  # Bot middleware
│       │   │   ├── area/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py
│       │   │   │   └── schemas.py
│       │   │   ├── earthquake/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py    # Risk hesaplama
│       │   │   │   └── schemas.py
│       │   │   ├── eids/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py
│       │   │   │   ├── ocr.py        # Tesseract OCR
│       │   │   │   └── schemas.py
│       │   │   ├── listing/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py    # LLM ilan metni üretimi
│       │   │   │   └── schemas.py
│       │   │   ├── subscription/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py
│       │   │   │   └── schemas.py
│       │   │   ├── map/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py    # PostGIS sorgular
│       │   │   │   └── schemas.py
│       │   │   ├── report/
│       │   │   │   ├── router.py
│       │   │   │   ├── service.py
│       │   │   │   └── schemas.py
│       │   │   └── notification/
│       │   │       ├── router.py
│       │   │       ├── service.py
│       │   │       └── schemas.py
│       │   ├── models/               # SQLAlchemy ORM modelleri
│       │   │   ├── base.py           # Base model (id, timestamps)
│       │   │   ├── user.py
│       │   │   ├── office.py
│       │   │   ├── property.py
│       │   │   ├── customer.py
│       │   │   ├── valuation.py
│       │   │   ├── match.py
│       │   │   ├── message.py
│       │   │   ├── notification.py
│       │   │   ├── subscription.py
│       │   │   └── ...
│       │   ├── tasks/                # Celery tasks
│       │   │   ├── ml_tasks.py       # Model eğitim, batch değerleme
│       │   │   ├── scraping_tasks.py # Veri toplama
│       │   │   ├── notification_tasks.py
│       │   │   ├── pdf_tasks.py      # PDF rapor üretimi
│       │   │   └── photo_tasks.py    # Fotoğraf işleme
│       │   └── core/                 # Paylaşılan altyapı
│       │       ├── exceptions.py     # Custom exception'lar
│       │       ├── pagination.py     # Cursor + offset pagination
│       │       ├── cache.py          # Redis cache helpers
│       │       └── storage.py        # MinIO S3 client
│       ├── migrations/               # Alembic migrations
│       │   ├── alembic.ini
│       │   ├── env.py
│       │   └── versions/
│       ├── ml/                       # ML model dosyaları
│       │   ├── models/               # Eğitilmiş modeller (.joblib)
│       │   ├── training/             # Eğitim scriptleri
│       │   │   ├── valuation_model.py
│       │   │   ├── matching_model.py
│       │   │   └── price_anomaly.py
│       │   ├── data/                 # Eğitim verisi (gitignore)
│       │   └── notebooks/            # Jupyter notebooks (deneyler)
│       ├── tests/
│       │   ├── conftest.py           # Pytest fixtures
│       │   ├── test_auth/
│       │   ├── test_property/
│       │   ├── test_valuation/
│       │   └── ...
│       ├── pyproject.toml            # Python proje konfigürasyonu (uv)
│       └── Dockerfile
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.api            # FastAPI production
│   │   ├── Dockerfile.web            # Next.js standalone
│   │   ├── Dockerfile.worker         # Celery worker
│   │   └── Dockerfile.bot            # (API ile birleşik — ayrı gerekmez)
│   ├── nginx/
│   │   ├── nginx.conf                # Ana Nginx konfigürasyonu
│   │   └── conf.d/
│   │       └── emlak.conf            # Site-specific config
│   └── monitoring/
│       ├── prometheus.yml
│       ├── grafana/
│       │   └── dashboards/
│       └── alertmanager.yml
│
├── docker-compose.yml                # Geliştirme ortamı
├── docker-compose.prod.yml           # Production ortamı
├── Makefile                          # Kısayol komutlar
├── .env.example                      # Örnek ortam değişkenleri
├── .gitignore
└── README.md
```

### 5.2 Shared Kod Yönetimi

| Paylaşım Alanı | Yaklaşım |
|-----------------|----------|
| API Types (TS) | OpenAPI spec → `openapi-typescript-codegen` ile otomatik üretim |
| Validation Schemas | Pydantic (backend) → Zod (frontend) — manuel sync, aynı yapı |
| Config | `.env` dosyaları — Docker Compose ile inject |
| UI Components | `apps/web/src/components/` altında, Mini App ile paylaşılır |

**OpenAPI → TypeScript codegen komutu:**
```bash
# Makefile'da:
generate-types:
    cd apps/api && python -c "from main import app; import json; print(json.dumps(app.openapi()))" > openapi.json
    cd apps/web && npx openapi-typescript-codegen --input ../api/openapi.json --output src/types/api
```

---

## 6. Coding Standartları

### 6.1 Backend (Python)

| Kural | Araç | Detay |
|-------|------|-------|
| **Stil** | Ruff (formatter + linter) | PEP 8, line length 120, import sorting |
| **Type Hints** | mypy (strict mode) | Tüm fonksiyon parametreleri ve dönüş tipleri zorunlu |
| **Docstring** | Google style | Public fonksiyon ve class'larda zorunlu |
| **Validation** | Pydantic v2 | Tüm input/output schema'ları Pydantic model |
| **Async** | asyncio + async/await | Tüm I/O işlemleri async (DB, HTTP, Redis) |
| **Error Handling** | Custom exception hierarchy | `AppException` → `NotFoundError`, `ValidationError`, vb. |
| **Testing** | pytest + pytest-asyncio | Minimum %80 coverage hedefi (MVP'de %60 kabul edilir) |

**Katmanlı Mimari Kuralı (ZORUNLU):**
```
Router (endpoint) → Service (iş mantığı) → Repository (veri erişimi)
                                          → External (3. parti API)
```
- Router: HTTP concern'leri (status code, response model)
- Service: İş kuralları, validasyon, orchestration
- Repository: SQLAlchemy sorgular, DB transaction'lar
- **Service katmanı asla doğrudan DB'ye erişmez** (Repository üzerinden)
- **Router katmanı asla iş mantığı içermez** (Service üzerinden)

### 6.2 Frontend (TypeScript / React)

| Kural | Araç | Detay |
|-------|------|-------|
| **Stil** | ESLint + Prettier | Airbnb config + custom rules |
| **TypeScript** | Strict mode | noImplicitAny, strictNullChecks |
| **Components** | Functional + Server Components öncelikli | Class component YASAK |
| **State (server)** | TanStack Query v5 | Tüm API çağrıları TanStack Query ile |
| **State (client)** | Zustand | Minimal client state (tema, sidebar, vb.) |
| **Forms** | React Hook Form + Zod | Validation schema frontend'de de zorunlu |
| **CSS** | Tailwind CSS 4.x | Utility-first, custom component class'ları minimal |
| **Testing** | Vitest + Testing Library | Kritik bileşenler test edilir |

**Dosya Adlandırma:**
```
components/PropertyCard.tsx       # PascalCase (bileşenler)
hooks/useValuation.ts             # camelCase (hook'lar)
lib/api-client.ts                 # kebab-case (utility'ler)
stores/auth-store.ts              # kebab-case (store'lar)
types/property.ts                 # kebab-case (type dosyaları)
```

### 6.3 Git Branching Stratejisi

```
main ──────────────────────────────────────────────►
  │                                    ▲
  └── develop ─────────────────────────┤────────────►
        │         ▲        ▲           │
        ├── feature/EPIC-01-valuation ─┘
        ├── feature/EPIC-05-crm ───────┘
        ├── bugfix/fix-login-redirect
        └── release/v0.1.0-alpha
```

| Branch | Amaç | Merge Hedefi |
|--------|-------|-------------|
| `main` | Production-ready kod | — |
| `develop` | Aktif geliştirme | → main (release) |
| `feature/EPIC-XX-desc` | Yeni özellik | → develop (PR) |
| `bugfix/desc` | Bug fix | → develop (PR) |
| `release/vX.Y.Z` | Release hazırlık | → main + develop |
| `hotfix/desc` | Acil production fix | → main + develop |

### 6.4 Commit Mesaj Formatı (Conventional Commits)

```
<type>(<scope>): <açıklama>

[opsiyonel gövde]

[opsiyonel footer]
```

| Type | Kullanım |
|------|----------|
| `feat` | Yeni özellik |
| `fix` | Bug fix |
| `refactor` | Kod yapısı değişikliği (davranış değişmez) |
| `docs` | Dokümantasyon |
| `test` | Test ekleme/düzeltme |
| `chore` | Build, CI, dependency güncelleme |
| `perf` | Performans iyileştirme |

**Örnekler:**
```
feat(valuation): LightGBM değerleme motoru v1 eklendi
fix(crm): müşteri arama sorgusu boş sonuç döndürmesi düzeltildi
refactor(messaging): WhatsApp adapter Strategy pattern'e çevrildi
```

### 6.5 PR Review Kuralları

| Kural | Detay |
|-------|-------|
| **Minimum 1 onay** | Her PR en az 1 reviewer onayı gerektirir |
| **CI geçmeli** | Lint + test + type-check geçmeden merge edilemez |
| **Kapsam sınırı** | Tek PR max ~500 satır değişiklik (büyük özellikler bölünür) |
| **Açıklama zorunlu** | PR açıklamasında: ne yapıldı, neden, nasıl test edilir |
| **Self-review** | PR sahibi önce kendi kodunu review eder |

---

## 7. DevOps ve Altyapı

### 7.1 Docker Compose Yapısı (Production)

```yaml
# docker-compose.prod.yml — servis listesi
services:
  # === UYGULAMA ===
  api:                    # FastAPI backend
    build: infra/docker/Dockerfile.api
    ports: ["8000:8000"]
    depends_on: [postgres, redis, minio]
    deploy:
      replicas: 2         # 2 instance (gunicorn + uvicorn workers)

  web:                    # Next.js frontend
    build: infra/docker/Dockerfile.web
    ports: ["3000:3000"]
    depends_on: [api]

  worker-default:         # Celery default queue
    build: infra/docker/Dockerfile.worker
    command: celery -A src.tasks worker -Q default -c 4

  worker-ml:              # Celery ML queue (CPU yoğun)
    build: infra/docker/Dockerfile.worker
    command: celery -A src.tasks worker -Q ml -c 2

  worker-scraping:        # Celery scraping queue
    build: infra/docker/Dockerfile.worker
    command: celery -A src.tasks worker -Q scraping -c 2

  celery-beat:            # Celery scheduler
    build: infra/docker/Dockerfile.worker
    command: celery -A src.tasks beat --scheduler redbeat.RedBeatScheduler

  # === VERİTABANI ===
  postgres:               # PostgreSQL 16 + PostGIS
    image: postgis/postgis:16-3.4
    ports: ["5432:5432"]
    volumes: ["pg_data:/var/lib/postgresql/data"]

  redis:                  # Redis 7
    image: redis:7.2-alpine
    ports: ["6379:6379"]
    volumes: ["redis_data:/data"]

  minio:                  # MinIO Object Storage
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    command: server /data --console-address ":9001"
    volumes: ["minio_data:/data"]

  # === MONİTORİNG ===
  prometheus:             # Metrik toplama
    image: prom/prometheus:latest
    ports: ["9090:9090"]

  grafana:                # Dashboard
    image: grafana/grafana:latest
    ports: ["3001:3000"]

  # === REVERSE PROXY ===
  # Nginx → CloudPanel tarafından yönetiliyor (Docker dışında)

volumes:
  pg_data:
  redis_data:
  minio_data:
```

**Toplam servis sayısı:** 10 (api x2, web, 3 worker, beat, postgres, redis, minio, prometheus, grafana)

### 7.2 CI/CD Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                     GitHub Actions Pipeline                    │
│                                                                │
│  PR Açıldığında (ci.yml):                                     │
│  ┌────────┐  ┌────────┐  ┌─────────┐  ┌──────────┐          │
│  │ Lint   │  │ Type   │  │ Unit    │  │ Build    │          │
│  │ (ruff  │  │ Check  │  │ Test    │  │ Check    │          │
│  │ +eslint│  │ (mypy  │  │ (pytest │  │ (docker  │          │
│  │  )     │  │ +tsc)  │  │ +vitest)│  │  build)  │          │
│  └────────┘  └────────┘  └─────────┘  └──────────┘          │
│       │           │            │             │                │
│       └───────────┴────────────┴─────────────┘                │
│                         │                                      │
│                   Tümü geçti mi?                              │
│                    ✅ → PR merge edilebilir                    │
│                    ❌ → PR bloke                               │
│                                                                │
│  develop'a merge sonrası (deploy-staging.yml):                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐      │
│  │ Docker      │  │ Push to      │  │ Deploy to      │      │
│  │ Build       │→ │ Registry     │→ │ Staging        │      │
│  │ (multi-stg) │  │ (GHCR)       │  │ (docker pull)  │      │
│  └─────────────┘  └──────────────┘  └────────────────┘      │
│                                                                │
│  main'e merge sonrası (deploy-production.yml):                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐      │
│  │ Docker      │  │ Push to      │  │ Deploy to      │      │
│  │ Build       │→ │ Registry     │→ │ Production     │      │
│  │ (tagged)    │  │ (GHCR)       │  │ (rolling)      │      │
│  └─────────────┘  └──────────────┘  └────────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

**Deploy mekanizması (MVP):**
```bash
# Sunucuda (SSH ile):
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --no-deps api web worker-default
# Rolling update: API ve Web aynı anda, worker'lar sırayla
```

### 7.3 Staging vs Production Farkları

| Alan | Staging | Production |
|------|---------|------------|
| **Domain** | staging.emlak.skystonetech.com | emlak.skystonetech.com |
| **API replicas** | 1 | 2 |
| **Worker replicas** | 1 (tümü tek worker) | 3 (default, ml, scraping ayrı) |
| **DB** | Aynı PostgreSQL, ayrı schema | Ana schema |
| **Redis** | DB 10-15 | DB 0-5 |
| **MinIO** | staging/ bucket | production/ bucket |
| **Sentry** | staging environment | production environment |
| **Log level** | DEBUG | WARNING |
| **Rate limiting** | Gevşek (test kolaylığı) | Sıkı |

### 7.4 Monitoring ve Alerting

| Araç | İzlenen | Alert Koşulu |
|------|---------|-------------|
| **Sentry** | Uygulama hataları, exception'lar | Her unhandled exception → Telegram bildirimi |
| **Prometheus** | HTTP latency, CPU, RAM, DB bağlantıları | p95 latency > 2sn → alert |
| **Grafana** | Dashboard: request/sn, hata oranı, aktif kullanıcı | Hata oranı > %5 → alert |
| **PostgreSQL** | Slow queries, bağlantı sayısı, disk kullanımı | Slow query > 5sn → log |
| **Redis** | Memory kullanımı, hit ratio | Memory > %80 → alert |
| **Celery** | Kuyruk uzunluğu, failed task'lar | Failed > 10/saat → alert |
| **MinIO** | Disk kullanımı | Disk > %80 → alert |

**Alert kanalı:** Telegram Bot (operasyonel kanal) + E-posta (kritik)

### 7.5 Yedekleme Stratejisi

| Veri | Yöntem | Sıklık | Saklama |
|------|--------|--------|---------|
| PostgreSQL | `pg_dump` → compressed → MinIO | Günlük 03:00 | 30 gün |
| MinIO (fotoğraflar) | `mc mirror` → backup bucket | Haftalık | 90 gün |
| Redis | RDB snapshot | Saatlik | 7 gün |
| .env dosyaları | Git (encrypted) | Her değişiklikte | ∞ |

---

## 8. Güvenlik Mimarisi

### 8.1 KVKK Uyumlu Veri Saklama

```
┌──────────────────────────────────────────────────────────────┐
│                     VERİ SINIFLANDIRMA                        │
│                                                                │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │   PII (Kişisel)      │  │   Anonim / İstatistiksel     │  │
│  │   ─────────────      │  │   ──────────────────────     │  │
│  │   • Ad, soyad        │  │   • Bölge ort. m² fiyatı    │  │
│  │   • Telefon          │  │   • İlan sayısı (aggregate)  │  │
│  │   • E-posta          │  │   • Fiyat trendi             │  │
│  │   • Adres            │  │   • Demografik istatistik    │  │
│  │   • TC Kimlik (yok)  │  │   • Deprem risk skoru        │  │
│  │   • EİDS belge       │  │   • POI verisi               │  │
│  │                      │  │                               │  │
│  │   DEPOLAMA:          │  │   DEPOLAMA:                   │  │
│  │   → AES-256 at-rest  │  │   → Şifrelenmemiş (hız)     │  │
│  │   → Ayrı tablo alanı │  │   → Cache'lenebilir          │  │
│  │   → Audit log zorunlu│  │   → Public API ile sunulabilir│  │
│  │   → 30 gün silme SLA │  │                               │  │
│  └──────────────────────┘  └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 Şifreleme Stratejisi

| Katman | Yöntem | Detay |
|--------|--------|-------|
| **In-Transit** | TLS 1.3 | Nginx SSL termination, Let's Encrypt |
| **At-Rest (DB)** | PostgreSQL pgcrypto + uygulama katmanı | PII alanları (telefon, email) AES-256 ile şifrelenir |
| **At-Rest (Dosya)** | MinIO server-side encryption (SSE-S3) | Tüm yüklenen dosyalar |
| **Şifre** | bcrypt (cost=12) | Password hashing |
| **JWT** | RS256 (RSA key pair) | Asimetrik imza (public key ile verify) |
| **API Keys** | SHA-256 hash | Webhook secret'lar DB'de hash olarak saklanır |

### 8.3 PII vs Anonim Veri Ayrımı (Uygulama Detayı)

```python
# PII alanları şifreleme dekoratörü
from cryptography.fernet import Fernet

class EncryptedField:
    """SQLAlchemy custom type — PII alanları için otomatik şifreleme."""
    def process_bind_param(self, value, dialect):
        if value:
            return fernet.encrypt(value.encode()).decode()
        return value

    def process_result_value(self, value, dialect):
        if value:
            return fernet.decrypt(value.encode()).decode()
        return value

# Kullanım:
class Customer(Base):
    full_name = Column(EncryptedString(150))  # Şifreli
    phone = Column(EncryptedString(20))        # Şifreli
    email = Column(EncryptedString(255))        # Şifreli
    lead_status = Column(String(20))           # Şifresiz (PII değil)
```

### 8.4 RBAC (Role-Based Access Control) Detayı

| Kaynak | Agent | Office Admin | Office Owner | Platform Admin |
|--------|:-----:|:------:|:------:|:------:|
| **Kendi mülkleri** | CRUD | CRUD | CRUD | CRUD |
| **Ofis mülkleri (başka agent)** | Read | CRUD | CRUD | CRUD |
| **Paylaşım ağı mülkleri** | Read | Read | Read + Share | CRUD |
| **Kendi müşterileri** | CRUD | CRUD | CRUD | CRUD |
| **Ofis müşterileri** | — | Read | CRUD | CRUD |
| **Değerleme** | Create + Read own | Read all | Read all | CRUD |
| **Raporlar** | — | — | Read (Elite) | CRUD |
| **Kullanıcı yönetimi** | — | Invite/Remove | Invite/Remove + Roles | CRUD |
| **Abonelik** | — | — | CRUD | CRUD |
| **Ayarlar** | Own profile | Office settings | All settings | All |
| **Audit log** | — | — | Read | CRUD |

### 8.5 Güvenlik Kontrol Listesi (Sprint S0'da Tamamlanacak)

- [ ] HTTPS zorunlu (HTTP → 301 redirect)
- [ ] CORS policy: sadece bilinen domainler
- [ ] Helmet headers (CSP, X-Frame-Options, HSTS)
- [ ] SQL injection koruması (SQLAlchemy parametrik sorgu)
- [ ] XSS koruması (React default escaping + CSP)
- [ ] CSRF token (form submit'lerde)
- [ ] Rate limiting (Redis sliding window)
- [ ] JWT blacklist (logout sonrası)
- [ ] Dosya yükleme validasyonu (tip, boyut, magic bytes)
- [ ] Dependency audit (pip-audit, npm audit)
- [ ] Secret management (.env, asla git'e commit edilmez)
- [ ] PostgreSQL RLS aktif (multi-tenant izolasyon)
- [ ] Audit log middleware (tüm write işlemleri loglanır)
- [ ] KVKK aydınlatma metni ve rıza formu
- [ ] VERBİS kaydı hazırlığı
- [ ] Penetrasyon testi (Beta öncesi — S18'de)

### 8.6 Veri Silme Prosedürü (KVKK Md. 7)

```
Kullanıcı "Hesabımı Sil" talebi
    │
    ▼
1. Soft delete: is_active = false, deleted_at = now()
2. Kişisel veriler anonimleştirilir (ad → "Silinmiş Kullanıcı #XXX")
3. 30 gün bekleme süresi (geri alma imkanı)
4. 30 gün sonra Celery task: hard delete
   - PII alanları NULL yapılır
   - Fotoğraflar MinIO'dan silinir
   - İlişkili kayıtlar (message, vb.) anonimleştirilir
5. Audit log'a "KVKK silme tamamlandı" kaydı düşülür
```

---

## Ekler

### Ek A: Ortam Değişkenleri (.env.example)

```env
# === UYGULAMA ===
APP_NAME=emlak-platform
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=<random-64-char>
APP_URL=https://emlak.skystonetech.com
API_URL=https://emlak.skystonetech.com/api

# === VERİTABANI ===
DATABASE_URL=postgresql+asyncpg://emlak:password@postgres:5432/emlak_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# === REDİS ===
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/2

# === JWT ===
JWT_PRIVATE_KEY_PATH=/app/keys/private.pem
JWT_PUBLIC_KEY_PATH=/app/keys/public.pem
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_WEBHOOK_URL=https://emlak.skystonetech.com/api/v1/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=<random-32-char>
TELEGRAM_MINI_APP_URL=https://emlak.skystonetech.com/tg

# === WHATSAPP (Beta) ===
WHATSAPP_BSP=360dialog
WHATSAPP_API_KEY=<api-key>
WHATSAPP_WEBHOOK_SECRET=<secret>
WHATSAPP_PHONE_NUMBER_ID=<number-id>

# === AI / LLM ===
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
LLM_DEFAULT_PROVIDER=openai
LLM_DEFAULT_MODEL=gpt-5-mini

# === MİNİO ===
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<access-key>
MINIO_SECRET_KEY=<secret-key>
MINIO_BUCKET=emlak-production
MINIO_PUBLIC_URL=https://emlak.skystonetech.com/files

# === ŞİFRELEME ===
ENCRYPTION_KEY=<fernet-key>

# === MONİTORİNG ===
SENTRY_DSN=<sentry-dsn>
SENTRY_ENVIRONMENT=production

# === SCRAPING (Koşullu) ===
SCRAPING_ENABLED=false
PROXY_POOL_URL=<proxy-service-url>
```

### Ek B: Makefile Kısayolları

```makefile
# Geliştirme
dev:              docker compose up -d && cd apps/web && npm run dev
dev-api:          cd apps/api && uvicorn src.main:app --reload --port 8000
dev-web:          cd apps/web && npm run dev
dev-worker:       cd apps/api && celery -A src.tasks worker -l DEBUG

# Veritabanı
db-migrate:       cd apps/api && alembic upgrade head
db-rollback:      cd apps/api && alembic downgrade -1
db-seed:          cd apps/api && python -m src.scripts.seed

# Test
test:             cd apps/api && pytest && cd ../web && npm test
test-api:         cd apps/api && pytest -v
test-web:         cd apps/web && npm test
lint:             cd apps/api && ruff check . && cd ../web && npm run lint

# Type check
types:            cd apps/api && mypy src/ && cd ../web && npx tsc --noEmit

# OpenAPI → TypeScript
gen-types:        cd apps/api && python scripts/export_openapi.py && cd ../web && npx openapi-ts

# Deploy
deploy-staging:   ssh root@157.173.116.230 "cd /var/www/emlak && ./deploy.sh staging"
deploy-prod:      ssh root@157.173.116.230 "cd /var/www/emlak && ./deploy.sh production"
```

---

*Bu doküman, Emlak Teknoloji Platformu'nun teknik temelini tanımlar. Her karar gerekçelendirilmiş, alternatifler değerlendirilmiş, ve önceki proje tecrübeleri (iyisiniye, UniqMys, Yakıt Analizi) dikkate alınmıştır. Doküman yaşayan bir belgedir — sprint'ler ilerledikçe güncellenecektir.*

*Son güncelleme: 2026-02-20*

> 📎 Mimari karar kayıtları (ADR) ve sprint eşleştirmeleri için bkz. [MIMARI-KARARLAR.md](./MIMARI-KARARLAR.md)

