# CLAUDE.md - Emlak Teknoloji Platformu Proje Kayit Dosyasi

> Bu dosya projenin "hafizasi"dir. Orkestrasyon sirasinda ve sonrasinda bagimsiz gelistirme icin kullanilir.

---

## Proje Hafiza Sistemi — ILK OKUNAN BOLUM

**Bu projeye devam eden her LLM ve gelistirici asagidaki 3 dosyayi birlikte kullanmak ZORUNDADIR:**

| Dosya | Konum | Amac | Guncelleme Sikligi |
|-------|-------|------|-------------------|
| **CLAUDE.md** | `Emlak/CLAUDE.md` | Projenin guncel durumu, talimatlar, teknik dokumantasyon | Her yeni ozellik, endpoint, bagimlilik, mimari degisiklikte |
| **reports.md** | `Emlak/reports.md` | Is bazli kronolojik kayit (ne yapildi, ne zaman) | Her ise baslarken, devam ederken ve bitirince |
| **experience.md** | `Emlak/experience.md` | Birikimli tecrube ve ogrenimler (kararlar, hatalar, pattern'ler) | Her gorev tamamlandiginda |

**Baslangic Proseduru (her oturum basinda):**
1. `CLAUDE.md`'yi oku — projeyi, kurallari ve guncel durumu ogren
2. `reports.md`'yi oku — son yapilan isi ve yarim kalan seyleri kontrol et
3. `experience.md`'yi oku — onceki tecrubelerden faydalan, ayni hatalari tekrarlama

**Bu dosyalar olmadan gelistirmeye baslama. Yoksa olustur, varsa oku.**

---

## Proje Bilgileri

| Alan | Deger |
|------|-------|
| **Proje Adi** | Emlak Teknoloji Platformu |
| **Aciklama** | Turkiye emlak sektoru icin yapay zeka destekli web+mobil (Telegram Mini App) platform. AI degerleme, CRM, portfoy vitrin, kredi hesaplayici, deprem risk, bolge analizi, ilan asistani |
| **Olusturma Tarihi** | 2026-02-20 |
| **Teknoloji Stack** | Next.js 15 + FastAPI + PostgreSQL 17 + PostGIS + Redis + Celery + MinIO + LightGBM + OpenAI GPT-5-mini |
| **Proje Durumu** | Alpha — Production deploy tamamlandi (petqas.com) |
| **Son Guncelleme** | 2026-02-28 |
| **GitHub** | https://github.com/FeritTasdildiren/Emlak |
| **Domain** | petqas.com (Cloudflare DNS) |

---

## Teknoloji Kararlari

| Teknoloji | Secim | Gerekce |
|-----------|-------|---------|
| Frontend | Next.js 15.5.12 + React 19 + Tailwind v4 + TypeScript | App Router, SSR/SSG, Turbopack dev build |
| State | Zustand 5 + React Query 5 | Zustand: client state (toast, auth). React Query: server state (cache, invalidation) |
| Form | react-hook-form 7 + Zod 4 | Performansli form yonetimi + tip-guvenli validasyon |
| Harita | MapLibre GL JS 5 | Acik kaynak, ucretsiz, OSM tiles |
| Grafik | Recharts 3 | React-native chart kutuphanesi |
| Backend | FastAPI 0.115+ + Python 3.13 | Async, OpenAPI, Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) + asyncpg | Async ORM, tip guvenligi, lazy='raise' N+1 koruması |
| Veritabani | PostgreSQL 17.7 + PostGIS | RLS multi-tenant izolasyon, GEOGRAPHY, FTS, pg_trgm |
| Migration | Alembic | 21 migration (001→021), otomatik revision chain |
| Cache/Queue | Redis 7 (DB 0=cache, DB 1=broker, DB 2=result) | Celery broker, JWT blacklist, wizard state, cache |
| Task Queue | Celery 5.4 + Beat | 8 periyodik gorev, 3 kuyruk (default, outbox, notifications) |
| Object Storage | MinIO (S3 uyumlu) | Fotograf upload, PDF depolama |
| ML | LightGBM 4.6 + scikit-learn + Optuna | Gayrimenkul degerleme modeli v1 (MAPE %9.35) |
| AI | OpenAI GPT-5-mini | Ilan metni uretimi, virtual staging, oda analizi |
| PDF | WeasyPrint 62 + Jinja2 | Degerleme raporu PDF |
| Telegram | aiogram 3.x + @telegram-apps/sdk-react v3 | Bot komutlari + Mini App |
| Auth | JWT (HS256) + bcrypt | Access (30dk) + Refresh (7 gun) token rotation |
| Rate Limit | slowapi | 3 tier: auth 15/dk, API 100/dk, webhook 5/dk |
| Logging | structlog | Yapisal JSON log, request_id korelasyon |
| Tracing | OpenTelemetry + Grafana Tempo | Dagitik izleme (opsiyonel, .env ile aktif) |
| Deployment | PM2 + Nginx + Cloudflare | Non-Docker production, SSH deploy |

---

## Gelistirme Kurallari

### Gorev Yasam Dongusu Kaydi
Her yapilacak is icin asagidaki adimlar izlenmelidir:

1. **IS ONCESI**: Gorev "Aktif Gorevler" tablosuna `PLANLANMIS` durumunda eklenir
2. **IS BASLANDIGINDA**: Durum `DEVAM EDIYOR` olarak guncellenir
3. **IS TAMAMLANDIGINDA**: Durum `TAMAMLANDI` olarak guncellenir, sonuc yazilir
4. **SORUN CIKTIGINDA**: Durum `BLOKE` olarak guncellenir, sorun aciklamasi eklenir

### Calisma Raporu Sistemi (reports.md) — ZORUNLU

Proje uzerinde yapilan **her derleme, duzenleme, gelistirme, hata duzeltme ve konfigurasyon degisikligi** kayit altina alinmalidir.

**Kayit Formati:**
```markdown
## [RAPOR-XXX] Kisa Baslik
| Alan | Deger |
|------|-------|
| **Durum** | BASLANDI / DEVAM EDIYOR / TAMAMLANDI / BASARISIZ |
| **Baslangic** | YYYY-MM-DD HH:MM |
| **Bitis** | YYYY-MM-DD HH:MM |
| **Etkilenen Dosyalar** | dosya1.ts, dosya2.py, ... |

### Hedef
Aciklama.

### Yapilanlar
- [x] Tamamlanan adim

### Kararlar ve Notlar
- Neden X tercih edildi?

### Sonuc
Son durum.
```

### Tecrube Kayit Sistemi (experience.md) — ZORUNLU

Her gorev tamamlandiginda ogrenimleri bu dosyaya yaz:

```markdown
## [Tarih] - Kisa Baslik
### Gorev: Ne yapildigi
- [KARAR] Karar → Sonuc
- [HATA] Hata → Cozum
- [PATTERN] Yaklasim → Neden ise yaradi
- [UYARI] Dikkat → Neden
```

### Surekli Guncelleme Talimatlari — ZORUNLU

Bu CLAUDE.md dosyasi canli bir dokumandir. Asagidaki degisikliklerde guncellenir:

| Degisiklik Turu | Guncellenecek Bolum |
|-----------------|---------------------|
| Yeni API endpoint | API Dokumantasyonu |
| Yeni ortam degiskeni | Ortam Degiskenleri |
| Yeni bagimlilik | On Gereksinimler |
| DB sema degisikligi | Veritabani Yonetimi |
| Mimari karar | Mimari Kararlar |
| Deployment degisikligi | Deployment |

### Kod Standartlari

**Backend (Python):**
- Linter: ruff (target py312, line-length 99)
- Async everywhere: asyncpg, async SQLAlchemy
- Type hints zorunlu (mypy strict)
- Docstring: Turkce
- Import siralamasi: stdlib → 3rd party → local (ruff isort)

**Frontend (TypeScript):**
- Strict TypeScript
- React Server Components varsayilan, client component icin 'use client'
- Tailwind v4 (JIT, static siniflar — runtime string birlestirme YASAK)
- Form: react-hook-form + Zod
- API state: React Query (gcTime >= staleTime kurali)

### Git & Deployment Guvenlik Kurallari

- Git repo private, tum kaynak dosyalar yuklenebilir
- `.env`, `.env.production` ASLA commit'lenmez
- `CLAUDE.md`, `reports.md`, `experience.md` Git'te tutulur ama sunucuya deploy edilmez

---

## Mimari Kararlar

| # | Karar | Secim | Gerekce |
|---|-------|-------|---------|
| ADR-0001 | Multi-tenant izolasyon | PostgreSQL RLS (Row Level Security) | Tek DB, FORCE RLS + SET LOCAL ile tenant izolasyonu. app_user DB rolu, platform_admin bypass policy |
| ADR-0002 | Migration stratejisi | Alembic (seri, otomatik) | Down migration yok, ileri seri. Rollback icin yeni migration |
| ADR-0003 | Messaging gateway | Protocol + ChannelRegistry | Capability-aware, plan-based routing. Telegram birincil kanal |
| ADR-0004 | Frontend state | Zustand + React Query | Zustand: client state. React Query: server state. Ayristirma |
| ADR-0005 | Search | FTS + pg_trgm + ILIKE | 3 katmanli arama: once FTS, sonra trigram fuzzy, son ILIKE fallback |
| ADR-0006 | ML model | LightGBM + Optuna | GBDT, hizli inference, quantile regression guven araligi |
| ADR-0007 | Kanal yetkinlikleri | ChannelCapabilities v2 | Her kanal icin 10+ yetkinlik flagi (text, photo, inline_keyboard...) |
| ADR-0008 | Outbox pattern | FOR UPDATE SKIP LOCKED | Transactional outbox, inbox dedup, Celery worker poll |
| ADR-0009 | Rate limiting | slowapi (sliding window) | 3 tier: auth, API, webhook. Redis backend |
| ADR-0010 | WebSocket | Stub — graceful degradation | NEXT_PUBLIC_WS_ENABLED=false varsayilan. Aktif edildiginde JWT auth + heartbeat |

---

## Bilinen Sorunlar ve Teknik Borc

| # | Aciklama | Oncelik | Durum |
|---|----------|---------|-------|
| 1 | 3 kirik sidebar link: /dashboard (→ /), /valuation (→ /valuations), /credit (→ /calculator) | ORTA | Acik |
| 2 | test_s5_valuation_functional.py:213 Python 3.14 syntax hatasi (annotations) | DUSUK | Acik |
| 3 | /maps sayfasi 431KB (maplibre-gl chunk ~278KB) | DUSUK | Kabul edildi |
| 4 | Frontend API hook'lari mock data donuyor — gercek API'ye baglanmali | YUKSEK | Acik |
| 5 | Quantile regression guven araligi coverage %57.6 (hedef %80) — model v2'de iyilestirme | ORTA | Gelecek sprint |
| 6 | WeasyPrint Docker disinda kirik olabilir (font bagimliligi) | DUSUK | Sunucuda OK |
| 7 | ruff 82 uyari (N806 ML degisken, TC* type checking) — kritik degil | DUSUK | Kabul edildi |

---

## Deployment Bilgileri

### Sunucu

| Alan | Deger |
|------|-------|
| **Provider** | Hetzner (CloudPanel) |
| **IP** | 157.173.116.230 |
| **SSH** | `ssh root@157.173.116.230` (sifre: `E3Ry8H#bWkMGJc6y`) |
| **CloudPanel** | https://cloud.skystonetech.com (admin / SFj353!*?dd) |
| **Domain** | petqas.com (Cloudflare DNS → A record 157.173.116.230) |
| **SSL** | Cloudflare Full (Strict) — origin cert CloudPanel |
| **Proje Yolu** | `/var/www/petqas/` |
| **PM2 Config** | `/var/www/petqas/ecosystem.config.js` |
| **Logs** | `/var/www/petqas/logs/` |

### Process Manager (PM2)

| Servis | PM2 Adi | Port | Aciklama |
|--------|---------|------|----------|
| FastAPI | petqas-api | 3003 | Uvicorn, 2 worker |
| Next.js | petqas-web | 3004 | SSR production |
| Celery Worker | petqas-celery-worker | — | 3 kuyruk, concurrency=2 |
| Celery Beat | petqas-celery-beat | — | 8 periyodik gorev |

**PM2 komutlari:**
```bash
pm2 status                    # Tum servislerin durumu
pm2 restart all               # Tum servisleri yeniden baslat
pm2 restart petqas-api        # Sadece API
pm2 logs petqas-api --lines 50  # API loglari
pm2 monit                     # Canli monitoring
```

### Nginx Konfigurasyonu

Nginx `/var/www/petqas/` altindaki dosyalari sunuyor:
- `petqas.com/` → Next.js (localhost:3004)
- `petqas.com/api/` → FastAPI (localhost:3003), `/api/` prefix strip edilir
- `petqas.com/health` → FastAPI (localhost:3003)
- `petqas.com/webhooks/` → FastAPI (localhost:3003)
- `petqas.com/ws` → FastAPI WebSocket (localhost:3003)

### Veritabani

| Alan | Deger |
|------|-------|
| **Engine** | PostgreSQL 17.7 + PostGIS |
| **Port** | 5433 (CloudPanel varsayilani) |
| **Superuser** | `postgresql://uniqmys:vSX7BQ3tRF6ybR2WJx4Isat9@localhost:5433/uniqmys_prod` |
| **App User** | `petqas` / `PetQas2026SecureDB` (RLS app_user rolu) |
| **DB Adi** | uniqmys_prod |

### Redis

| Alan | Deger |
|------|-------|
| **URL** | redis://localhost:6379 |
| **DB 0** | Cache (JWT blacklist, wizard state, password reset token) |
| **DB 1** | Celery broker |
| **DB 2** | Celery result backend |

---

## Detayli Teknik Dokumantasyon

### 1. On Gereksinimler (Prerequisites)

| Yazilim | Minimum Versiyon | Kurulum Notu |
|---------|-----------------|--------------|
| Python | 3.12+ | `uv` ile virtual env onerilen |
| Node.js | 20.x+ | Next.js 15 icin gerekli |
| pnpm | 9.x+ | Frontend paket yoneticisi |
| PostgreSQL | 16+ (PostGIS) | Production: 17.7 |
| Redis | 7.x | Cache + Celery broker |
| MinIO | Latest | S3 uyumlu object storage (dev icin Docker) |
| WeasyPrint | 62+ | PDF uretimi — sistem bagimlilik: libpango, libcairo, fonts-noto |
| PM2 | Latest | Production process manager |

### 2. Projeyi Sifirdan Kurma (Fresh Setup)

**Lokal Gelistirme:**
```bash
# 1. Repo klonla
git clone https://github.com/FeritTasdildiren/Emlak.git Emlak && cd Emlak

# 2. Docker servisleri baslat (DB, Redis, MinIO, Tempo, Grafana)
docker compose up -d

# 3. Backend kurulum
cd apps/api
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 4. .env dosyasi olustur
cp .env.example .env  # Degerleri duzenle

# 5. Migration calistir
alembic upgrade head

# 6. Seed verileri yukle (opsiyonel)
python -m src.scripts.seed_pilot_data
python -m src.scripts.seed_demographics

# 7. API'yi baslat
uvicorn src.main:app --reload --port 8000

# 8. Celery worker + beat (ayri terminallerde)
celery -A src.celery_app worker --loglevel=info -Q default,outbox,notifications
celery -A src.celery_app beat --loglevel=info

# 9. Frontend kurulum
cd ../web
pnpm install
pnpm dev  # localhost:3000
```

**Production Deploy (Sunucu):**
```bash
# SSH ile baglan
ssh root@157.173.116.230

# Proje dizini
cd /var/www/petqas

# Backend guncelleme
cd apps/api
source .venv/bin/activate
uv pip install -e .
alembic upgrade head

# Frontend build
cd ../web
pnpm install && pnpm build

# PM2 restart
cd /var/www/petqas
pm2 restart all
pm2 status
```

### 3. Ortam Degiskenleri (Environment Variables)

| Degisken | Aciklama | Ornek | Zorunlu? |
|----------|----------|-------|----------|
| APP_ENV | Ortam adi | production | Evet |
| APP_DEBUG | Debug modu | false | Hayir |
| DB_HOST | PostgreSQL host | localhost | Evet |
| DB_PORT | PostgreSQL port | 5433 | Evet |
| DB_NAME | Veritabani adi | uniqmys_prod | Evet |
| DB_USER | DB kullanici | uniqmys | Evet |
| DB_PASSWORD | DB sifre | (gizli) | Evet |
| APP_DB_USER | RLS app user | petqas | Evet |
| APP_DB_PASSWORD | RLS app user sifre | (gizli) | Evet |
| REDIS_URL | Redis baglanti | redis://localhost:6379/0 | Evet |
| CELERY_BROKER_URL | Celery broker | redis://localhost:6379/1 | Evet |
| CELERY_RESULT_BACKEND | Celery result | redis://localhost:6379/2 | Evet |
| JWT_SECRET_KEY | JWT imza anahtari | (min 32 karakter) | Evet |
| JWT_ALGORITHM | JWT algoritma | HS256 | Hayir |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | Access token omru | 30 | Hayir |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | Refresh token omru | 7 | Hayir |
| PASSWORD_RESET_TOKEN_EXPIRE_MINUTES | Sifre sifirlama TTL | 30 | Hayir |
| FRONTEND_URL | Frontend URL | https://petqas.com | Evet |
| MINIO_ENDPOINT | MinIO endpoint | localhost:9000 | Evet |
| MINIO_ACCESS_KEY | MinIO erisim | (gizli) | Evet |
| MINIO_SECRET_KEY | MinIO sifre | (gizli) | Evet |
| MINIO_BUCKET | MinIO bucket | emlak-media | Hayir |
| TELEGRAM_BOT_TOKEN | Telegram bot | (BotFather'dan) | Hayir |
| TELEGRAM_WEBHOOK_URL | Webhook URL | https://petqas.com/webhooks/telegram | Hayir |
| TELEGRAM_WEBHOOK_SECRET | Webhook secret | (rastgele) | Hayir |
| OPENAI_API_KEY | OpenAI API | sk-... | Hayir (bos=mock) |
| SENTRY_DSN | Sentry hata izleme | (sentry.io'dan) | Hayir (bos=devre disi) |
| OTEL_EXPORTER_OTLP_ENDPOINT | OTel endpoint | http://tempo:4317 | Hayir (bos=devre disi) |
| CORS_ORIGINS | CORS izinli domainler | ["https://petqas.com"] | Evet |

### 4. Veritabani Yonetimi

#### Veritabani Kurulumu
```bash
# PostgreSQL + PostGIS (Docker dev)
docker compose up -d db

# Production (CloudPanel zaten kuruyor):
# DB: uniqmys_prod, Port: 5433
# PostGIS aktif: CREATE EXTENSION IF NOT EXISTS postgis;
# pg_trgm aktif: CREATE EXTENSION IF NOT EXISTS pg_trgm;
# unaccent aktif: CREATE EXTENSION IF NOT EXISTS unaccent;
```

#### RLS (Row Level Security) Yapisi
```sql
-- Her tenant tablosunda:
ALTER TABLE tablename ENABLE ROW LEVEL SECURITY;
ALTER TABLE tablename FORCE ROW LEVEL SECURITY;

-- Tenant izolasyon policy:
CREATE POLICY tenant_isolation_tablename ON tablename
    USING (office_id = current_setting('app.current_office_id', true)::uuid);

-- Platform admin bypass:
CREATE POLICY platform_admin_bypass_tablename ON tablename
    USING (current_setting('app.current_user_role', true) = 'platform_admin');

-- GRANT app_user:
GRANT SELECT, INSERT, UPDATE, DELETE ON tablename TO app_user;
```

**KRITIK RLS NOTU:** `current_setting('app.current_office_id', true)::uuid` bos string dondugunde UUID cast HATA verir. Platform admin bypass islemlerinde MUTLAKA dummy UUID SET LOCAL yapilmali:
```python
await db.execute(text("SET LOCAL app.current_user_role = 'platform_admin'"))
await db.execute(text("SET LOCAL app.current_office_id = '00000000-0000-0000-0000-000000000000'"))
```

#### Migration'lar
```bash
cd apps/api

# Migration olustur
alembic revision --autogenerate -m "aciklama"

# Son migration'a yuksel
alembic upgrade head

# Bir oncekine don
alembic downgrade -1

# Mevcut revision'i goster
alembic current

# Migration gecmisi
alembic history
```

**Migration Zinciri (001 → 021):**
001=initial_schema, 002=rls_policies, 003=app_user_role, 004=payment_table, 005=outbox_inbox, 006=payment_timeline, 007=notifications, 008=telegram_chat_id, 009=area_deprem_price, 010=valuation_scraped, 011=fts_trigger, 012=model_registry, 013=turkish_search, 014=usage_quotas, 015=demographics, 016=customer_match, 017=customer_notes, 018=quota_expand, 019=showcase, 020=performance_indexes, 021=transaction_audit_log

#### Seed Data
```bash
# Istanbul pilot veri (3 ilce: Kadikoy, Uskudar, Atasehir)
python -m src.scripts.seed_pilot_data

# Istanbul demografi (38 ilce)
python -m src.scripts.seed_demographics

# Kredi hesaplayici banka faiz oranlari (6 banka)
# → src/modules/calculator/bank_rates.py icerisinde hardcoded seed
```

### 5. Servisleri Calistirma

#### Gelistirme Ortami
```bash
# Docker servisler (DB, Redis, MinIO, Tempo, Grafana)
docker compose up -d

# Backend API (hot-reload)
cd apps/api && uvicorn src.main:app --reload --port 8000

# Celery Worker
celery -A src.celery_app worker --loglevel=info -Q default,outbox,notifications

# Celery Beat
celery -A src.celery_app beat --loglevel=info

# Frontend (Turbopack)
cd apps/web && pnpm dev
```

#### Production
```bash
# PM2 ile tum servisleri baslat
cd /var/www/petqas
pm2 start ecosystem.config.js
pm2 save

# Sadece API restart
pm2 restart petqas-api

# Frontend rebuild + restart
cd apps/web && pnpm build && pm2 restart petqas-web
```

#### Port Haritasi

| Servis | Dev Port | Prod Port | URL |
|--------|----------|-----------|-----|
| FastAPI | 8000 | 3003 | http://localhost:8000 veya https://petqas.com/api/ |
| Next.js | 3000 | 3004 | http://localhost:3000 veya https://petqas.com/ |
| PostgreSQL | 5432 | 5433 | — |
| Redis | 6379 | 6379 | — |
| MinIO API | 9000 | — | http://localhost:9000 |
| MinIO Console | 9001 | — | http://localhost:9001 |
| Grafana | 3001 | — | http://localhost:3001 |
| Tempo | 4317/3200 | — | gRPC/HTTP |

### 6. API Dokumantasyonu

**Swagger UI:** https://petqas.com/api/docs
**OpenAPI JSON:** https://petqas.com/api/openapi.json

#### Endpoint Ozeti (100 endpoint, 18 modul)

| Modul | Prefix | Endpoint Sayisi | Auth | Aciklama |
|-------|--------|----------------|------|----------|
| auth | /api/v1/auth | 7 | Karma | register, login, refresh, logout, me, forgot-password, reset-password, change-password |
| properties | /api/v1/properties | 5 | JWT | CRUD + listing + sharing toggle |
| search | /api/v1/search | 2 | JWT | Hibrit arama (FTS+trigram+ILIKE) + suggestions |
| valuations | /api/v1/valuations | 5 | JWT | AI degerleme POST + GET list/detail/comparables |
| pdf | /api/v1/valuations | 1 | JWT | GET /{id}/pdf WeasyPrint rapor |
| areas | /api/v1/areas | 5 | JWT | Bolge analizi, trend, karsilastirma, demografi |
| earthquake | /api/v1/earthquake | 2 | JWT | Deprem risk + bina guvenlik skoru |
| maps | /api/v1/maps | 3 | JWT | GeoJSON, heatmap, bbox filtre |
| customers | /api/v1/customers | 9 | JWT | CRM CRUD + notes + timeline + arama |
| matches | /api/v1/matches | 3 | JWT | Eslestirme run + status guncelleme |
| showcases | /api/v1/showcases | 8 | Karma | Vitrin CRUD (JWT) + public slug + WhatsApp |
| calculator | /api/v1/calculator | 3 | JWT | Kredi hesaplama + banka oranlar + karsilastirma |
| notifications | /api/v1/notifications | 5 | JWT | Bildirim CRUD + okundu isaretle |
| listings | /api/v1/listings | 9 | Karma | Ilan metni uretimi + staging + foto + export + tones/portals (public) |
| payments | /api/v1/payments | 2 | JWT | Odeme olustur + webhook |
| telegram | /webhooks/telegram | 2 | Webhook Secret | Bot webhook + mini app auth |
| admin | /api/v1/admin | 8 | JWT+admin | Outbox monitor + DLQ + refresh alerts + drift |
| audit | /api/v1/audit | 3 | JWT+admin | KVKK audit log listele + detay |
| realtime | /ws | 1 | JWT (query) | WebSocket stub (echo+heartbeat) |
| health | /health | 4 | Yok | health, db, pdf, ready |

#### Ornek Istekler

```bash
# Login
curl -X POST https://petqas.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@petqas.com","password":"TestSifre2026!"}'
# → {"access_token":"eyJ...","refresh_token":"eyJ..."}

# Authenticated istek
TOKEN="eyJ..."
curl https://petqas.com/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# AI Degerleme
curl -X POST https://petqas.com/api/v1/valuations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"district":"Kadikoy","net_sqm":120,"room_count":"3+1","building_age":5,"floor_number":4}'

# Arama
curl "https://petqas.com/api/v1/search?q=kadikoy&min_price=1000000&listing_type=sale" \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Proje Klasor Yapisi (Detayli)

```
Emlak/
├── CLAUDE.md                     # Bu dosya (proje hafizasi)
├── PROJE-PLANI.md               # Stratejik proje plani (993 satir)
├── PRODUCT-BACKLOG.md            # 15 Epic, user story'ler
├── Makefile                      # Docker compose kisayollari
├── docker-compose.yml            # Dev ortam (7 servis)
├── ecosystem.config.js           # PM2 production config
├── apps/
│   ├── api/                      # FastAPI Backend
│   │   ├── pyproject.toml        # Python bagimliliklari (uv/hatch)
│   │   ├── alembic.ini           # Alembic config
│   │   ├── migrations/versions/  # 21 migration dosyasi
│   │   ├── src/
│   │   │   ├── main.py           # FastAPI app + lifespan + routers + health
│   │   │   ├── config.py         # Pydantic Settings (tum env vars)
│   │   │   ├── database.py       # SQLAlchemy async engine + session factory
│   │   │   ├── dependencies.py   # FastAPI dependency injection
│   │   │   ├── celery_app.py     # Celery config + 8 beat task
│   │   │   ├── core/             # Exceptions, logging, rate_limit, sentry, telemetry
│   │   │   ├── middleware/       # request_id, tenant (RLS SET LOCAL)
│   │   │   ├── models/           # SQLAlchemy entity models (15+ tablo)
│   │   │   ├── modules/          # 20 is domain modulu
│   │   │   │   ├── auth/         # JWT register/login/refresh/me/password
│   │   │   │   ├── properties/   # Ilan CRUD + search
│   │   │   │   ├── valuations/   # AI degerleme + PDF + drift
│   │   │   │   ├── customers/    # CRM CRUD + notes + timeline
│   │   │   │   ├── matches/      # Eslestirme algoritma + tetikleme
│   │   │   │   ├── showcases/    # Portfoy vitrin CRUD + public
│   │   │   │   ├── calculator/   # Kredi hesaplayici
│   │   │   │   ├── areas/        # Bolge analizi + demografi
│   │   │   │   ├── earthquake/   # Deprem risk + bina skoru
│   │   │   │   ├── maps/         # GeoJSON + heatmap
│   │   │   │   ├── messaging/    # Telegram bot + adapters + templates
│   │   │   │   ├── notifications/# In-app bildirim
│   │   │   │   ├── payments/     # Odeme + transaction + webhook
│   │   │   │   ├── audit/        # KVKK audit log
│   │   │   │   ├── realtime/     # WebSocket stub
│   │   │   │   ├── reporting/    # Gunluk ofis raporu
│   │   │   │   ├── admin/        # DLQ, outbox monitor, refresh alerts
│   │   │   │   └── data_pipeline/# TUiK, TCMB, AFAD, TKGM clients
│   │   │   ├── listings/         # Ilan asistani + staging + photo + export
│   │   │   ├── ml/               # LightGBM model + inference + drift
│   │   │   ├── services/         # Outbox worker, DLQ, messaging, quota
│   │   │   ├── tasks/            # Celery tasks (matching, reporting, refresh)
│   │   │   ├── templates/        # Jinja2 (PDF, email, messaging)
│   │   │   └── data/             # Egitim veri seti, GeoJSON, model artifacts
│   │   └── tests/                # pytest (unit + integration + e2e)
│   │       ├── conftest.py
│   │       ├── unit/             # Telegram bot, auth, calculator testleri
│   │       ├── test_rls.py       # RLS 27 test
│   │       ├── test_s2_*.py      # Sprint 2 testleri
│   │       ├── test_s4_*.py      # Sprint 4 testleri
│   │       ├── test_s5_*.py      # Sprint 5 testleri
│   │       └── test_s6-s10_*.py  # Sprint 6-10 testleri
│   └── web/                      # Next.js Frontend
│       ├── package.json          # pnpm + Next.js 15 + React 19
│       ├── vitest.config.ts      # Vitest test config
│       ├── src/
│       │   ├── app/              # Next.js App Router
│       │   │   ├── layout.tsx    # Root layout + metadata
│       │   │   ├── page.tsx      # Landing page
│       │   │   ├── providers.tsx # QueryClient + WebSocket provider
│       │   │   ├── (auth)/       # Login, Register, Forgot/Reset Password
│       │   │   ├── (dashboard)/  # Ana dashboard route grubu
│       │   │   │   ├── layout.tsx       # Sidebar + TopNav
│       │   │   │   ├── page.tsx         # Dashboard ana sayfa
│       │   │   │   ├── properties/      # Portfoy (liste + form)
│       │   │   │   ├── valuations/      # Degerleme (liste + detay)
│       │   │   │   ├── dashboard/customers/  # CRM (liste + detay + form)
│       │   │   │   ├── listings/        # Ilan Asistani (3 tab)
│       │   │   │   ├── areas/           # Bolge analizi + karsilastirma
│       │   │   │   ├── maps/            # MapLibre harita
│       │   │   │   ├── calculator/      # Kredi hesaplayici
│       │   │   │   ├── network/         # Vitrin yonetimi + paylasim agi
│       │   │   │   ├── messages/        # Mesajlar
│       │   │   │   └── settings/        # Ayarlar
│       │   │   ├── tg/           # Telegram Mini App (3 sayfa)
│       │   │   └── vitrin/[slug] # Public vitrin sayfasi (SSR)
│       │   ├── components/       # 19 UI bilesen (Button, Input, Card, ...)
│       │   ├── hooks/            # 16 React hook (useSearch, useCustomers, ...)
│       │   ├── lib/              # API client, utils, plan-features
│       │   ├── types/            # 7 TypeScript type dosyasi
│       │   └── mock/             # Mock data (gelistirme icin)
│       └── public/               # Statik dosyalar
├── docs/                         # Proje dokumantasyonu
│   ├── TEKNIK-MIMARI.md         # 1748 satir teknik mimari
│   ├── OPERASYONEL-PLAN.md      # 275 gorev, 19 sprint plani
│   ├── UI-UX-TASARIM.md         # Design system + wireframe
│   ├── MIMARI-KARARLAR.md       # 10 ADR
│   ├── KVKK-UYUM.md            # KVKK uyumluluk rehberi
│   ├── RUNBOOK.md               # Migration rollback + ops rehber
│   └── ...                       # Diger dokumanlar
└── infra/                        # Altyapi konfigurasyonu
    ├── db/init.sql              # PostGIS + pg_trgm + unaccent extension
    ├── tempo/tempo.yaml         # Grafana Tempo config
    ├── grafana/provisioning/    # Datasource + dashboard JSON
    └── nginx/                   # Nginx vhost ornegi
```

### 8. Ucuncu Parti Servisler ve Entegrasyonlar

| Servis | Amac | URL/Endpoint | Credential |
|--------|------|--------------|------------|
| PostgreSQL 17 + PostGIS | Ana veritabani | localhost:5433 | .env DB_* |
| Redis 7 | Cache, broker, JWT blacklist | localhost:6379 | .env REDIS_URL |
| MinIO | Fotograf/PDF depolama | localhost:9000 | .env MINIO_* |
| OpenAI GPT-5-mini | Ilan metni, staging, analiz | api.openai.com | .env OPENAI_API_KEY |
| Telegram Bot API | Bot + Mini App | api.telegram.org | .env TELEGRAM_* |
| Cloudflare | DNS + SSL + CDN | dash.cloudflare.com | CloudPanel entegre |
| TUiK API | Nufus, fiyat endeksi | cip.tuik.gov.tr | Public (API key yok) |
| TCMB EVDS | Faiz oranlari | evds2.tcmb.gov.tr | .env TCMB_EVDS_API_KEY |
| AFAD | Deprem verileri | deprem.afad.gov.tr | Public |
| Sentry | Hata izleme | sentry.io | .env SENTRY_DSN |
| Grafana + Tempo | Monitoring + tracing | localhost:3001 | Opsiyonel (dev) |

### 9. Test Stratejisi

#### Test Calistirma
```bash
# Backend testleri (pytest)
cd apps/api
pytest                           # Tum testler
pytest tests/test_rls.py         # Sadece RLS testleri
pytest -k "test_s5"              # Sprint 5 testleri
pytest --tb=short -q             # Kisa cikti

# Frontend testleri (Vitest)
cd apps/web
pnpm test                        # Tum testler
pnpm test:watch                  # Izleme modu

# Linting
cd apps/api && ruff check src/   # Backend lint
cd apps/web && pnpm lint         # Frontend lint
```

#### Test Istatistikleri
- Backend: ~489 test (RLS 27, S1 118, S2 79, S4 134, S5 35, S10 96)
- Frontend: 59 Vitest test (button, input, calculator, search, plan-features)
- Toplam: ~548 test

#### Test Yazma Kurallari
- Pure unit test: DB bagimsiz, mock pattern
- conftest.py: Fixture'lar merkezi
- `pytest-asyncio` + `asyncio_mode = "auto"`
- Her yeni modul icin test dosyasi: `tests/test_[sprint]_[modul].py`

### 10. Deployment (Yayina Alma)

#### CI/CD Pipeline (GitHub Actions)
- `deploy-staging.yml`: SSH + rsync + atomic symlink, main push trigger
- `deploy-prod.yml`: Tag-based, approval gate, DB backup, rollback
- `web-ci.yml`: pnpm build + Vitest

#### Manuel Deployment
```bash
# 1. SSH baglan
ssh root@157.173.116.230

# 2. Kodu guncelle
cd /var/www/petqas
# rsync veya git pull

# 3. Backend
cd apps/api
source .venv/bin/activate
uv pip install -e .
alembic upgrade head

# 4. Frontend
cd ../web
pnpm install --frozen-lockfile
pnpm build

# 5. Servisleri yeniden baslat
cd /var/www/petqas
pm2 restart all && pm2 status

# 6. Dogrulama
curl https://petqas.com/health
curl https://petqas.com/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"test2@petqas.com","password":"TestSifre2026!"}'
```

#### Domain ve DNS
- petqas.com → Cloudflare A record → 157.173.116.230
- SSL: Cloudflare Full (Strict) + CloudPanel origin certificate

### 11. Sik Karsilasilan Sorunlar ve Cozumleri

| Sorun | Olasi Neden | Cozum |
|-------|-------------|-------|
| Login 500 "invalid input syntax for type uuid" | RLS SET LOCAL office_id bos | Platform admin bypass'ta dummy UUID ekle: `SET LOCAL app.current_office_id = '00000000-...'` |
| Pydantic "not fully defined" hatasi | `from __future__ import annotations` + TYPE_CHECKING datetime | `datetime` import'unu TYPE_CHECKING disina tasi |
| asyncpg SET LOCAL parametrize hatasi | asyncpg SET icin $1 desteklemiyor | f-string interpolation kullan (guvenli — deger UUID) |
| Frontend build hatasi "use client" | Server component icinde client hook (useState, useEffect) | Dosya basina `'use client'` ekle |
| WeasyPrint font hatasi | Sistem fontlari eksik | `apt install fonts-noto-core fonts-noto-extra` |
| Celery beat cift calisma | Birden fazla beat instance | PM2'de instances: 1 zorunlu |
| Tailwind class uygulanmiyor | Runtime string birlestirme | Static sinif kullan: `bg-blue-500` (asla `bg-${color}-500` degil) |
| React Query stale data | gcTime < staleTime | gcTime >= staleTime olmali (tum hook'larda kontrol et) |
| PM2 restart loop | Port cakismasi veya .env eksik | `pm2 logs` kontrol, .env.production dogrula |
| Nginx 502 Bad Gateway | Backend ayakta degil | `pm2 status` kontrol, port eslesmesi (3003/3004) |

### 12. Gelistirme Ipuclari ve Kisayollar

```bash
# API docs goruntulemek
open https://petqas.com/api/docs

# PM2 canli monitor
pm2 monit

# Redis CLI (JWT blacklist, wizard state kontrol)
redis-cli -n 0 KEYS "password_reset:*"
redis-cli -n 0 KEYS "jwt_blacklist:*"

# Alembic migration gecmisi
cd apps/api && alembic history --verbose

# ruff auto-fix
ruff check src/ --fix

# Frontend build analizi
cd apps/web && ANALYZE=true pnpm build

# Sunucu log izleme
ssh root@157.173.116.230 "tail -f /var/www/petqas/logs/api-out.log"

# Test hesabi
# Email: test2@petqas.com
# Sifre: TestSifre2026!
# Office ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**RLS Debug:** Eger bir sorgu bos donuyorsa veya 403 aliyorsaniz, SET LOCAL degerlerini kontrol edin:
```sql
-- Mevcut tenant context'i kontrol
SELECT current_setting('app.current_office_id', true);
SELECT current_setting('app.current_user_role', true);
```

**Yeni Modul Ekleme Adimlari:**
1. `src/modules/yeni_modul/` klasoru olustur (`__init__.py`, `router.py`, `service.py`, `schemas.py`)
2. Gerekirse model ekle: `src/models/yeni_model.py` + migration
3. Router'i `main.py`'de include et
4. Eger JWT gerektirmiyorsa `tenant.py` PUBLIC_PATHS'e ekle
5. Test yaz: `tests/test_yeni_modul.py`

---

## Handoff Bilgileri

### Gelistirmeye Devam Etme

**Oncelikli Yapilaciaklar (Alpha → Beta gecisi icin):**

1. **Frontend API Entegrasyonu (YUKSEK):** Hook'lar simdilik mock data donuyor. React Query hook'larini gercek API'ye bagla. Ornek: `useProperties` → `GET /api/v1/properties`, `useCustomers` → `GET /api/v1/customers`
2. **3 Kirik Sidebar Link (ORTA):** `/dashboard` → `/`, `/valuation` → `/valuations`, `/credit` → `/calculator` path duzeltmesi
3. **Quantile Regression Iyilestirme (ORTA):** Coverage %57.6 → %80 hedefi. Model v2'de conformal prediction veya daha genis quantile araligi denenebilir
4. **WhatsApp Cloud API Entegrasyonu (Beta):** Elite plan icin BSP (360dialog) entegrasyonu. Mevcut click-to-chat Starter/Pro icin yeterli
5. **Meilisearch Gecisi (Beta):** FTS+trigram yeterli Alpha icin, Beta'da arama hacmi artarsa Meilisearch'e gecis

### Dikkat Edilmesi Gerekenler

1. **RLS Her Yerde Aktif:** FORCE RLS nedeniyle superuser bile etkilenir. Yeni tablo eklerken mutlaka RLS policy + GRANT app_user ekle
2. **asyncpg SET LOCAL Kisitlamasi:** SET LOCAL icin f-string kullanmak zorunlu (parametrize desteklenmiyor). UUID format dogrulamasi Python tarafinda yapiliyor
3. **TYPE_CHECKING + Pydantic Uyumsuzlugu:** `from __future__ import annotations` aktifken Pydantic `datetime` gibi tipleri runtime'da cozemez. datetime import'unu her zaman TYPE_CHECKING disinda tut
4. **Tenant Middleware Akisi:** `TenantMiddleware` JWT'den office_id/role alip `request.state`'e yazar → `get_db_session()` dependency bu degerleri okuyup `SET LOCAL` uygular → Endpoint'teki tum sorgular RLS filtreli calisir
5. **Celery Sync/Async Koprusu:** Celery task'lari sync calisir. Async servis cagirmak icin `asyncio.run()` kullan. DB icin `psycopg2` (sync driver) kullan
6. **Frontend Server/Client Component Ayrimi:** Next.js 15 App Router'da varsayilan Server Component. `useState`, `useEffect`, event handler kullanan bilesenler icin dosya basina `'use client'` gerekli
7. **PM2 Restart Sonrasi:** `pm2 save` yapmayi unutma, yoksa sunucu reboot'ta servisler kalkmaz

---

## Islem Gecmisi

### 2026-02-28 Proje Teslimi
- **Islem**: Proje handoff dokumani olusturuldu
- **Durum**: COMPLETED
- **Detay**: 168 gorev, 12 sprint (S0-S11 + Audit Fix), 100 API endpoint, 30 frontend route, 21 migration, ~548 test. Production deploy: petqas.com

### 2026-02-27 Deployment + Bug Fix
- RLS dual-session mimari sorunu cozuldu (database.py + tenant.py + auth refactor)
- Pydantic TYPE_CHECKING datetime fix (3 schema dosyasi)
- Tam proje dogrulama: skor 8.8/10

### 2026-02-20 ~ 2026-02-27 Gelistirme
- S0: Altyapi iskeleti (monorepo, Docker, CI, DB, RLS, Auth)
- S1: Messaging Gateway, Outbox Pattern, Payments, Telegram Bot
- S2: Veri Pipeline, API Clients, FTS, Normalizasyon
- S3: ML Model v0, Inference, Drift Monitoring
- S4: PDF Rapor, Turkish Search, Property CRUD
- S5: AI Degerleme v1, Kota, Anomali Tespiti
- S6: Bolge Analizi, MapLibre, Deprem Risk, POI
- S7: CRM, Eslestirme Algoritmasi, Telegram /musteri
- S8: OpenAI, Ilan Asistani, Virtual Staging
- S9: Portfoy Vitrin, Kredi Hesaplayici
- S10: Telegram Mini App, Bot Wizard, Gunluk Rapor
- S11: QA, Guvenlik, Performans, Monitoring, SEO
- Audit Fix: Deploy Pipeline, AuditLog, Sifre Sifirlama, WebSocket Stub, Feature Gating
