# G0 Gate Checklist — Sprint S0 Cikis Kontrolu

> **Amac:** S0 sonunda "guvenli, testli, izlenebilir, deploy edilebilir" cekirdek altyapi
> uzerinde S1-S2'de urun gelistirmeye risksiz sekilde baslamak.
>
> **Referans:** [S0-KICKOFF.md](./S0-KICKOFF.md) — Definition of Done kriterleri
>
> **Son Guncelleme:** 2026-02-20

---

## 1) Repo + CI/CD Temeli

| # | Kontrol | Durum | Dogrulama |
|---|---------|-------|-----------|
| 1.1 | `docker compose up` ile tum servisler ayaga kalkiyor (api, db, redis, minio) | ✅ | `docker-compose.yml` — 4 servis tanimli. `make up` komutu ile baslatilir. |
| 1.2 | CI pipeline: lint (ruff) + type-check (mypy) + test (pytest) | ✅ | `.github/workflows/ci.yml` — path-filter ile backend/frontend ayri. |
| 1.3 | Secrets: `.env.example` var, `.env` gitignore'da, repo'da secret YOK | ✅ | `.env.example` tum degiskenleri icerir. `.gitignore` kontrol edildi. |
| 1.4 | Migration'lar otomatik ve geri alinabilir | ✅ | `alembic upgrade head` / `alembic downgrade -1`. 3 migration dosyasi: 001_initial, 002_rls, 003_app_user. Her birinde `downgrade()` tanimli. |

### Ilgili Dosyalar
- `docker-compose.yml` — Servis tanimlari
- `.github/workflows/ci.yml` — CI pipeline
- `.env.example` — Ortam degiskeni sablonu
- `Makefile` — Gelistirici komutlari

---

## 2) DB Iskeleti + Multi-tenant RLS (Kirmizi Cizgi)

| # | Kontrol | Durum | Dogrulama |
|---|---------|-------|-----------|
| 2.1 | Cekirdek tablolar `office_id` tasiyor (8 tablo) | ✅ | `models/`: Office (root), User, Customer, Property, Conversation, Message, Notification, Subscription — hepsi `office_id` FK iceriyor. |
| 2.2 | RLS policy'leri aktif (ENABLE ROW LEVEL SECURITY) | ✅ | `002_rls_policies.py` — 7 tablo: customers, properties, conversations, messages, notifications, subscriptions, users. Offices haric (tenant root). |
| 2.3 | FORCE ROW LEVEL SECURITY aktif | ✅ | `002_rls_policies.py` — 7 tablo. Table owner bile RLS'e tabi. |
| 2.4 | Default deny: `current_setting('app.current_office_id', true)` missing-ok | ✅ | Policy USING clause: `current_setting(..., true)::uuid`. Missing → NULL → hic satir eslesemez. `test_rls.py::TestNegativeScenarios::test_no_tenant_context_returns_empty` ile dogrulanir. |
| 2.5 | Middleware akisi: BEGIN → SET LOCAL → queries → COMMIT/ROLLBACK | ✅ | `middleware/tenant.py::TenantMiddleware` — `session.begin()` context manager icinde SET LOCAL. Transaction commit/rollback ile temizlenir. |
| 2.6 | app_user superuser DEGIL | ✅ | `003_app_user_role.py` — `CREATE ROLE app_user LOGIN PASSWORD ...` (superuser/createdb/createrole flag'leri YOK). |
| 2.7 | app_user table owner DEGIL | ✅ | Tablolar postgres (veya migration calistiran kullanici) tarafindan olusturulur. app_user sadece GRANT ile yetkilendirilir. FORCE RLS sayesinde cift guvenlik. |

### RLS Testleri (Olmazsa Olmaz)

| # | Test Kategorisi | Test Sayisi | Durum | Referans |
|---|----------------|-------------|-------|----------|
| 2.8 | Cross-tenant izolasyon (7 tablo) | 14 test | ✅ | `test_rls.py::TestCrossTenant*` — Her tablo icin A↔B cift yonlu kontrol. |
| 2.9 | Pool reuse guvenlik | 3 test | ✅ | `test_rls.py::TestPoolReuse` — commit sonrasi, rollback sonrasi, ardisik tenant degisimi. |
| 2.10 | Negatif testler (default deny) | 3 test | ✅ | `test_rls.py::TestNegativeScenarios` — context yok, gecersiz UUID, FORCE RLS. |
| 2.11 | Shared properties (cross-office) | 4 test | ✅ | `test_rls.py::TestSharedProperties` — gorunurluk, gizlilik, read-only SELECT, DELETE engeli. |
| 2.12 | Platform admin bypass | 3 test | ✅ | `test_rls.py::TestPlatformAdminBypass` — admin tum user'lari gorur, normal rol kendi ofisi, admin UPDATE. |

**Toplam RLS test: 27 test case** (7 tablo × 2 cross-tenant + 3 pool + 3 negative + 4 shared + 3 admin)

### Ilgili Dosyalar
- `migrations/versions/001_initial_schema.py` — 8 tablo, 17 indeks, TSVECTOR trigger
- `migrations/versions/002_rls_policies.py` — RLS + FORCE + 3 policy tipi
- `migrations/versions/003_app_user_role.py` — app_user role + GRANT
- `src/middleware/tenant.py` — TenantMiddleware (SET LOCAL)
- `tests/test_rls.py` — RLS integration test suite
- `tests/conftest.py` — RLS test altyapisi (app_user engine, seed data)

---

## 3) Observability Minimumu (Kirmizi Cizgi)

| # | Kontrol | Durum | Dogrulama |
|---|---------|-------|-----------|
| 3.1 | `request_id` middleware calisiyor | ✅ | `middleware/request_id.py::RequestIdMiddleware` — UUID v4 uretir, response header + request.state'e ekler. |
| 3.2 | Structured logging standardi var | ✅ | `core/logging.py` — structlog + `RequestLoggingMiddleware`. request_id her log'da gorunur. JSON cikti formati. |
| 3.3 | Sentry stub var | ✅ | `core/sentry.py::init_sentry()` — SENTRY_DSN bos ise no-op. Lifespan'da baslatirilir. |
| 3.4 | Hata yakalama standardi: RFC 7807 | ✅ | `core/exceptions.py::AppException` + `app_exception_handler`. Problem JSON formati. Yakalanmamis hatalar RequestIdMiddleware'de fallback handler. |

### Ilgili Dosyalar
- `src/middleware/request_id.py` — Request ID uretimi
- `src/core/logging.py` — structlog yapilandirmasi + log middleware
- `src/core/sentry.py` — Sentry baslangic
- `src/core/exceptions.py` — RFC 7807 hata formati

---

## 4) Entitlement / Plan Enablement Iskeleti

| # | Kontrol | Durum | Dogrulama |
|---|---------|-------|-----------|
| 4.1 | Plan bazli kanal enablement tek bir yerde (policy pattern) | ✅ | `core/plan_policy.py` — `get_capabilities(plan_type)` fonksiyonu. `PLAN_CAPABILITIES` dict'i. |
| 4.2 | Starter/Pro = click-to-chat, Elite = Cloud API | ✅ | `PlanType.STARTER/PRO: whatsapp_cloud_api=False`, `PlanType.ELITE: whatsapp_cloud_api=True`. |
| 4.3 | Capability-aware degrade dokumana yansiyor | ✅ | TEKNIK-MIMARI.md + UI-UX-TASARIM.md'de capability-aware degrade tarifi mevcut. |

### Ilgili Dosyalar
- `src/core/plan_policy.py` — Plan yetenek motoru
- `docs/TEKNIK-MIMARI.md` — Kanal enablement mimarisi

---

## 5) Auth Sistemi

| # | Kontrol | Durum | Dogrulama |
|---|---------|-------|-----------|
| 5.1 | Register endpoint (/api/v1/auth/register) | ✅ | `modules/auth/router.py` — POST, email uniqueness, bcrypt hash. |
| 5.2 | Login endpoint (/api/v1/auth/login) | ✅ | `modules/auth/router.py` — POST, JWT access + refresh token. |
| 5.3 | Refresh token endpoint (/api/v1/auth/refresh) | ✅ | `modules/auth/router.py` — POST, token rotation. |
| 5.4 | Me endpoint (/api/v1/auth/me) | ✅ | `modules/auth/router.py` — GET, JWT'den kullanici bilgileri. |
| 5.5 | JWT token type field (access/refresh strict) | ✅ | Token payload'da `type: "access"` veya `type: "refresh"` alani. Yanlis tip ile erisim engellenir. |
| 5.6 | Role-based access control (require_role) | ✅ | `modules/auth/dependencies.py::require_role()` factory fonksiyonu. Dekorator olarak kullanilir. |
| 5.7 | Timing attack korumasi | ✅ | Login'de kullanici bulunamasa bile dummy bcrypt hash kontrolu yapilir — timing farki aciga cikmaz. |

### Ilgili Dosyalar
- `src/modules/auth/router.py` — Auth endpoint'leri
- `src/modules/auth/service.py` — Auth is mantigi
- `src/modules/auth/dependencies.py` — JWT dogrulama + role check
- `src/modules/auth/schemas.py` — Pydantic request/response sema'lari

---

## 6) P1 Maddeleri (Olursa Harika)

| # | Kontrol | Durum | Dogrulama |
|---|---------|-------|-----------|
| 6.1 | Healthcheck endpoint'leri (`/health`) | 🔄 | Temel `/health` mevcut. `/health/db` ve `/health/redis` henuz eklenmedi. |
| 6.2 | Migration rollback notu | 🔄 | Her migration'da `downgrade()` tanimli. Runbook'a prosedur eklenmeli. |
| 6.3 | Outbox/Inbox ADR notu | ⏳ | MIMARI-KARARLAR.md'de ADR placeholder. SKIP LOCKED + polling fallback notu eklenmeli. |

---

## Ozet Skor Tablosu

| Kategori | Toplam Kontrol | Gecen | Durum |
|----------|---------------|-------|-------|
| 1. Repo + CI/CD | 4 | 4 | ✅ TAMAM |
| 2. DB + RLS | 12 | 12 | ✅ TAMAM |
| 3. Observability | 4 | 4 | ✅ TAMAM |
| 4. Plan Enablement | 3 | 3 | ✅ TAMAM |
| 5. Auth | 7 | 7 | ✅ TAMAM |
| 6. P1 (Bonus) | 3 | 0 | 🔄 Devam |
| **TOPLAM** | **33** | **30** | **P0: 30/30 ✅** |

---

## G0 Gate Karari

> **P0 maddeleri: 30/30 ✅ — Gate GECILDI.**
>
> S0'in "kirmizi cizgi" maddeleri (RLS, Observability, Auth, Plan Enablement)
> tamami tamamlandi. P1 maddeleri S0 sonrasi D4 dalga'da veya S1 basinda tamamlanabilir.
>
> **Siradaki:** S1 Sprint planlama — Feature gelistirmeye gecis.

---

## Demo Plani (S0 Sonu — 30 dk)

1. **RLS Izolasyon Demo (10 dk)**
   - `pytest tests/test_rls.py -v` calistir, tum testler yesil
   - Cross-tenant: A verisi B'ye gorunmuyor
   - Shared property: network ilani diger ofise gorunuyor
   - Default deny: context yokken 0 satir

2. **Auth Akisi Demo (10 dk)**
   - Register → Login → JWT token al
   - Me endpoint ile kullanici bilgilerini gor
   - Refresh token rotation
   - Role-based erisiln kontrolu

3. **Observability Demo (5 dk)**
   - request_id header'da gorunuyor
   - structlog JSON ciktisi request_id iceriyor
   - Hata durumunda RFC 7807 formati

4. **Plan Enablement Demo (5 dk)**
   - `get_capabilities("starter")` → whatsapp_cloud_api=False
   - `get_capabilities("elite")` → whatsapp_cloud_api=True
