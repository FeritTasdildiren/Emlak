# Emlak Teknoloji Platformu - SLA Tanimlari

> Son guncelleme: 2026-02-26
> Versiyon: 1.0

## 1. Genel Bakis

Bu dokuman, Emlak Teknoloji Platformu icin taahhut edilen servis seviye
anlasmalarini (SLA) tanimlar. Tum metrikler Grafana uzerinden izlenir
ve esik asildiginda otomatik alert tetiklenir.

**Monitoring Dashboard**: http://localhost:3001/d/sla-overview
**Alert Folder**: Grafana → Emlak Alerts

---

## 2. Uptime SLA

| Metrik | Hedef | Olcum Periyodu | Alert Esigi |
|--------|-------|----------------|-------------|
| Platform Uptime | >= %99.5 | 7 gunluk hareketli ortalama | < %99.5 → HIGH |

### Hesaplama
```
Uptime % = (Toplam Dakika - Downtime Dakika) / Toplam Dakika * 100
```

### Downtime Tanimlari
- **Planli bakim**: Onceden duyurulan, SLA'dan haric (max ayda 4 saat)
- **Plansiz kesinti**: SLA'dan dusulen gercek downtime
- **Kismi kesinti**: Sadece belirli endpoint'ler etkileniyorsa %50 oranla sayilir

### Izin Verilen Downtime (Aylik)
| SLA | Aylik Izin | Haftalik Izin |
|-----|-----------|---------------|
| %99.5 | ~3.6 saat | ~50 dakika |
| %99.9 (hedef) | ~43 dakika | ~10 dakika |

---

## 3. API Performans SLA

| Metrik | Hedef | Olcum | Alert |
|--------|-------|-------|-------|
| API p95 Latency | < 500ms | Tum server span'leri | > 500ms 15dk → WARNING |
| API p99 Latency | < 2000ms | Tum server span'leri | > 2000ms 15dk → WARNING |
| Degerleme Suresi | < 3s | /valuation endpoint p95 | > 3s 5dk → WARNING |
| PDF Uretim Suresi | < 10s | /report/pdf endpoint p95 | > 10s 5dk → WARNING |

### Endpoint Bazli Hedefler
| Endpoint Grubu | p95 Hedef | p99 Hedef |
|----------------|----------|----------|
| Health (/health/*) | < 50ms | < 100ms |
| CRUD (GET/POST/PUT) | < 300ms | < 1000ms |
| Arama & Filtreleme | < 500ms | < 1500ms |
| Degerleme (ML) | < 3000ms | < 5000ms |
| PDF Rapor | < 10000ms | < 15000ms |
| Toplu Islemler | < 30000ms | < 60000ms |

---

## 4. Error Rate SLA

| Metrik | Hedef | Olcum | Alert |
|--------|-------|-------|-------|
| 5xx Error Rate | < %1 | Toplam istek icindeki 5xx orani | > %1 10dk → HIGH |
| 4xx Error Rate | < %10 | Bilgilendirme, SLA disi | > %15 → WARNING |

### Haric Tutulan Hatalar
- Rate limiting (429) → SLA disinda
- Authentication (401) → SLA disinda
- Validation (422) → SLA disinda, ancak izlenir

---

## 5. Async Islem SLA

| Metrik | Hedef | Olcum | Alert |
|--------|-------|-------|-------|
| Celery Task p95 | < 30s | Tum Celery task sureleri | > 30s 10dk → WARNING |
| Outbox Lag | < 100 bekleyen | Pending event sayisi | > 100 5dk → WARNING |
| DLQ Boyutu | < 10 event | Dead letter kuyrugu | > 10 → WARNING |

### Task Oncelik Siralari
| Kuyruk | Max Bekleme | Aciklama |
|--------|------------|----------|
| default | 30s | Genel gorevler |
| outbox | 10s | Event isleme (yuksek oncelik) |
| notifications | 60s | Bildirim gonderimi |

---

## 6. ML Model SLA

| Metrik | Hedef | Olcum | Alert |
|--------|-------|-------|-------|
| ML Drift (PSI) | < 0.2 | Population Stability Index | > 0.2 10dk → WARNING |
| Degerleme MAPE | < %22 | Model dogruluk metrigi | Haftalik kontrol |
| Model Yuklenme | < 5s | Cold start suresi | > 5s → WARNING |

### PSI Esikleri
| PSI Degeri | Yorum | Aksiyon |
|-----------|-------|---------|
| < 0.1 | Stabil | Normal operasyon |
| 0.1 - 0.2 | Hafif kayma | Izle, haftalik rapor |
| > 0.2 | Onemli kayma | Alert, yeniden egitim plani |
| > 0.3 | Kritik kayma | Acil yeniden egitim |

---

## 7. Altyapi SLA

| Metrik | Hedef | Alert |
|--------|-------|-------|
| Disk Kullanimi | < %85 | > %85 → WARNING + Telegram |
| Memory Kullanimi | < %90 | > %90 → HIGH + Telegram |
| DB Baglanti | Surekli erisim | 3dk kesinti → CRITICAL |
| Redis Baglanti | Surekli erisim | 3dk kesinti → CRITICAL |

---

## 8. Guvenlik SLA

| Metrik | Hedef | Alert |
|--------|-------|-------|
| RLS Violation | 0 (sifir tolerans) | Herhangi bir ihlal → CRITICAL + Telegram |
| Auth Failure Spike | < 50/dk | > 50/dk → WARNING |

---

## 9. Alert Yanitlanma Sureleri

| Severity | Bildirim | Ilk Yanit | Cozum Hedefi |
|----------|----------|-----------|-------------|
| CRITICAL | Aninda Telegram | 5 dakika | 30 dakika |
| HIGH | Aninda Telegram | 15 dakika | 2 saat |
| WARNING | 4 saatte bir | Is saatleri | 24 saat |

---

## 10. Eskalasyon Matrisi

```
Dakika 0-5:   Alert tetiklendi → On-call muhendis bilgilendirildi
Dakika 5-15:  Ilk mudahale yapildi / yapilmadiysa → Eskalasyon 1 (Tech Lead)
Dakika 15-30: Cozum bulunamazsa → Eskalasyon 2 (CTO)
Dakika 30+:   Devam eden kesinti → Incident post-mortem hazirlik
```

---

## 11. Raporlama

| Rapor | Periyot | Icerik |
|-------|---------|--------|
| SLA Haftalik | Her Pazartesi | Uptime, latency, error trendleri |
| SLA Aylik | Her ayin 1'i | Aylik SLA uyum ozeti |
| Incident Raporu | Her kesinti sonrasi | Root cause, timeline, action items |

---

## 12. Revizyon Gecmisi

| Tarih | Versiyon | Degisiklik |
|-------|----------|-----------|
| 2026-02-26 | 1.0 | Ilk SLA tanimlari olusturuldu |
