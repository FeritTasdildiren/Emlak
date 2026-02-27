# Sprint S0 Kickoff — "Zemin Sağlam, Ürün Hızlı" Planı

## Amaç (Sprint S0'un tek cümlelik hedefi)

S0 sonunda: **güvenli (multi-tenant), testli, izlenebilir ve deploy edilebilir** bir çekirdek altyapı üzerinde S1–S2'de ürün geliştirmeye risksiz şekilde başlayacağız.

## Kapsam Dışı (S0'da yapmayacağız)

* WhatsApp Cloud API entegrasyonu (Elite / Beta)
* Outbox/Inbox implementasyonu (S1) — sadece tasarım notu/ADR düzeyinde netleştirme
* ML eğitim/servisleme (S3)
* Büyük UI/UX detayları (S2+)

---

# Definition of Done (DoD) — S0 Çıkış Kriterleri

## 1) Repo + CI/CD Temeli

* [ ] PR'da çalışan pipeline: lint/format + unit test + (varsa) integration test
* [ ] Tek komutla local ayağa kalkıyor: `docker compose up` + `migrate` (dokümantasyonu mevcut)
* [ ] Secrets yönetimi: repo'da **secret yok**; `.env.example` var; gerçek secrets CI/CD üzerinden inject
* [ ] Migration'lar otomatik ve geri alınabilir (rollback stratejisi notu)

## 2) DB İskeleti + Multi-tenant RLS (Kırmızı Çizgi)

* [ ] Çekirdek tablolar `office_id` taşıyor (en az: User/Office, Customer, Conversation, Message, Property, Subscription/Payment ile ilişkili olanlar)
* [ ] RLS policy'leri aktif ve "default deny" davranışı var
* [ ] Middleware/DB session akışı: **BEGIN → SET LOCAL → queries → COMMIT/ROLLBACK** (dokümana ve koda yansımış)
* [ ] `current_setting('app.current_office_id', true)` missing-ok kullanımı doğrulanmış
* [ ] Uygulama DB rolü **superuser değil** (ve mümkünse tablo owner'ı değil)

### RLS Testleri (S0'un olmazsa olmazı)

* [ ] Cross-tenant test: Tenant A ile Tenant B verisine erişim **başarısız** olmalı
* [ ] Pool reuse testi: aynı process içinde ardışık farklı tenant request'leri → veri sızıntısı olmamalı
* [ ] Negatif test: tenant context set edilmeden veri erişimi **başarısız** olmalı

## 3) Observability Minimumu (Kırmızı Çizgi)

* [ ] FastAPI middleware `request_id` üretir; response header + log context'e ekler
* [ ] Structured logging standardı var (request_id her log'da görünür)
* [ ] Hata yakalama standardı: beklenmeyen hatalar Sentry/monitoring'e düşer (en azından stub)

> Not: Celery trace propagation implementasyonu S1'de; S0'da sadece request_id'nin backend'de standartlaşması yeter.

## 4) Entitlement / Plan Enablement İskeleti

* [ ] "Plan bazlı kanal enablement" kontrolü backend'de tek bir yerde (policy)
* [ ] Messaging capability modeli dokümana yansımış: UI "capability-aware degrade" çalışır
* [ ] Starter/Pro: click-to-chat; Elite: Cloud API — bu karar repo dokümanlarında tutarlı

## 5) Operasyonel Gate: G0 Checklist

* [ ] Dev environment deploy edilebilir (en azından staging benzeri bir ortam)
* [ ] G0 checklist tek sayfa: "Neyi nasıl doğruladık?" maddeleri (linkli)
* [ ] S0 sonunda 30 dk demo: RLS isolation testleri + request_id log örneği + basic healthcheck

---

# S0 İş Kırılımı (Önerilen)

## P0 (Mutlaka)

1. RLS + SET LOCAL + test suite (cross-tenant + pool reuse)
2. request_id middleware + structured logs
3. CI pipeline + secret hygiene
4. Plan enablement policy iskeleti (kanal on/off)

## P1 (Olursa harika)

5. Healthcheck endpoint'leri (`/health`, `/health/db`)
6. Basic migration rollback notu + runbook başlangıcı
7. Outbox/Inbox concurrency stratejisi için ADR'ye 2 satır not (SKIP LOCKED, polling fallback)

---

# Roller ve Beklenti

* S0 boyunca "hız" değil "zemin" optimize edilecek.
* "Kırmızı çizgi" maddeleri tamamlanmadan S1'e geçilmeyecek.
* Her büyük madde için 1 owner atanacak; günlük standup'ta sadece blokajlar konuşulacak.

Bu notu issue/checklist olarak projeye ekleyebilirsiniz. S0 bitişte hedef: **S1'de özellik geliştirmeyi güvenle hızlandıracak bir temel**.
