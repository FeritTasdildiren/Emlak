"""
İstanbul pilot veri yükleme — Kadıköy, Üsküdar, Ataşehir.

Gerçek verilerle AreaAnalysis, DepremRisk ve PriceHistory seed.
Tüm veriler web araştırmasından derlenmiş, kaynak bilgileri provenance
alanlarında saklanır.

Kaynaklar:
    - TÜİK ADNKS 2024 (nüfus ve demografi) — nufusu.com, gazetekadikoy.com.tr
    - Emlakjet Şubat 2026 (konut fiyat) — emlakjet.com
    - Endeksa 2025 (fiyat trendi) — endeksa.com, istiklal.com.tr
    - AFAD TBDY 2018 / İBB DEZİM (deprem risk) — afad.gov.tr, depremzemin.ibb.istanbul
    - MTA Diri Fay Haritası 2023 (fay mesafesi) — mta.gov.tr
    - metro.istanbul (ulaşım) — metro.istanbul

Kullanım:
    python -m src.scripts.seed_pilot_data

İdempotent: Tekrar çalıştırılabilir (UPSERT ON CONFLICT).
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import structlog
from sqlalchemy import text

from src.core.sync_database import get_sync_session
from src.modules.data_pipeline.normalizers import (
    build_point_wkt,
    calculate_risk_score,
    safe_decimal,
)
from src.modules.data_pipeline.normalizers.provenance_builder import (
    build_provenance_fields,
)
from src.modules.data_pipeline.repositories import (
    batch_insert_price_history,
    upsert_area_analysis,
    upsert_deprem_risk,
)

logger = structlog.get_logger("scripts.seed_pilot_data")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VERİ KAYNAKLARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Kadıköy:
#   Nüfus: 462,189 — TÜİK ADNKS 2024 (nufusu.com)
#   Yaş dağılımı: gazetekadikoy.com.tr (TÜİK 2024 kaynaklı)
#   65+ oranı: 20.6% — kadikoyakademi.org (TÜİK 2024)
#   Üniversite mezunu: 46% — verikaynagi.com (TÜİK ADNKS 2023)
#   Hane sayısı: 193,522 — kadikoyakademi.org (TÜİK 2024)
#   m² satış: 116,222 TL — Emlakjet (Şubat 2026)
#   m² kira: 535 TL — Emlakjet (Şubat 2026)
#   Fiyat trendi: ~%15 (6 ay) — Endeksa/istiklal.com.tr (2025 yıllık %29)
#   PGA: ~0.40g — AFAD TBDY 2018 (haberturk.com raporları)
#   Zemin: ZD baskın — İBB DEZİM (2019)
#   Fay mesafesi: ~15 km — MTA/Kandilli (Kuzey Anadolu Fayı deniz segmenti)
#   Metro/rail: 13 istasyon — metro.istanbul (M4 + Marmaray)
#   Hastane: 43 — gazetekadikoy.com.tr (Kadıköy 2030 Raporu)
#   Okul: 269 — gazetekadikoy.com.tr (Kadıköy 2030 Raporu)
#   AVM: 6 — kadikoy.com
#   Park: 102 — gazetekadikoy.com.tr (Kadıköy 2030 Raporu)
#
# Üsküdar:
#   Nüfus: 512,981 — TÜİK ADNKS 2024 (nufusu.com)
#   65+ oranı: ~14% — nufusubu.com tahmin (TÜİK 2023 kaynaklı)
#   Üniversite mezunu: ~30% — TÜİK ulusal ort. üzeri tahmin (affluent ilçe)
#   Hane sayısı: 180,222 — urbistat.com (TÜİK 2020 kaynaklı)
#   m² satış: 95,000 TL — Emlakjet/Türkiye Gazetesi (Ocak 2026)
#   m² kira: 393 TL — Emlakjet (Şubat 2025)
#   Fiyat trendi: ~%14 (6 ay) — Endeksa İstanbul geneli %29 yıllık
#   PGA: ~0.20g — İBB DEZİM raporu (analizgazetesi.com.tr)
#   Zemin: ZB baskın (%90) — analizgazetesi.com.tr / İBB DEZİM
#   Fay mesafesi: ~12 km — Adalar Fayı segmenti (haberturk.com)
#   Metro/rail: 7 istasyon — metro.istanbul (M5 + Marmaray)
#   Hastane: 9 — uskudar.bel.tr e-rehber
#   AVM: 4 — Wikipedia AVM listesi
#   Park: 244 — Üsküdar Belediyesi 2025-2029 Stratejik Plan
#
# Ataşehir:
#   Nüfus: 414,866 — TÜİK ADNKS 2024 (nufusu.com)
#   Yaş dağılımı: citypopulation.de (TÜİK 2023 kaynaklı)
#   Ort. hane büyüklüğü: 3.01 — Endeksa
#   m² satış: 63,265 TL — Emlakjet (Şubat 2026)
#   m² kira: 354 TL — Emlakjet (Şubat 2026)
#   Fiyat trendi: ~%12 (6 ay) — istiklal.com.tr top 10 ilçe
#   PGA: ~0.35g — İBB DEZİM / AFAD haritası renk kodu tahmini
#   Zemin: ZC baskın — insaatdoktoru.com / İBB DEZİM
#   Fay mesafesi: ~18 km — AFAD fay haritası, coğrafi konum
#   Metro: 6 istasyon — atasehirrehberi.com.tr (M4 + M8)
#   Hastane: 29 sağlık kuruluşu — trhastane.com
#   AVM: 6 — mekanlar.com
#   Park: 235 — atasehir.bel.tr
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


PILOT_DISTRICTS: list[dict[str, Any]] = [
    # ─── Kadıköy ─────────────────────────────────────────────────────
    {
        "city": "İstanbul",
        "district": "Kadıköy",
        "center": (40.9927, 29.0230),  # (lat, lon) — WGS84
        "area": {
            "population": 462189,
            "avg_price_sqm_sale": "116222.00",
            "avg_price_sqm_rent": "535.00",
            "price_trend_6m": "15.00",
            "transport_score": "85.00",
            "amenity_score": "90.00",
            "investment_score": "82.00",
            "amortization_years": "18.1",
            "demographics": {
                "year": 2024,
                "age_0_14_pct": 11.0,
                "age_15_24_pct": 10.0,
                "age_25_44_pct": 29.0,
                "age_45_64_pct": 29.4,
                "age_65_plus_pct": 20.6,
                "university_graduate_pct": 46.0,
                "high_school_graduate_pct": 22.0,
                "household_count": 193522,
                "population_density_km2": 18420,
            },
            "poi_data": {
                "metro_stations": 13,
                "marmaray_stations": 7,
                "hospitals": 43,
                "schools": 269,
                "shopping_malls": 6,
                "parks": 102,
                "cultural_facilities": 128,
            },
            "provenance_sources": [
                ("TUIK", "ADNKS-2024", 1),
                ("Emlakjet", "2026-02", 1),
                ("Endeksa", "2025-11", 1),
            ],
        },
        "deprem": {
            "pga_value": "0.4000",
            "soil_class": "ZD",
            "fault_distance_km": "15.00",
            "provenance_sources": [
                ("AFAD", "TBDY-2018", 1),
                ("IBB_DEZIM", "2019", 1),
                ("MTA", "diri-fay-2023", 1),
            ],
        },
        "price_history": [
            {"date": date(2025, 8, 1), "avg_price_sqm": "101063.00", "transaction_count": 660},
            {"date": date(2025, 9, 1), "avg_price_sqm": "104095.00", "transaction_count": 680},
            {"date": date(2025, 10, 1), "avg_price_sqm": "107127.00", "transaction_count": 700},
            {"date": date(2025, 11, 1), "avg_price_sqm": "110159.00", "transaction_count": 720},
            {"date": date(2025, 12, 1), "avg_price_sqm": "113191.00", "transaction_count": 740},
            {"date": date(2026, 1, 1), "avg_price_sqm": "116222.00", "transaction_count": 766},
        ],
    },
    # ─── Üsküdar ─────────────────────────────────────────────────────
    {
        "city": "İstanbul",
        "district": "Üsküdar",
        "center": (41.0240, 29.0154),
        "area": {
            "population": 512981,
            "avg_price_sqm_sale": "95000.00",
            "avg_price_sqm_rent": "393.00",
            "price_trend_6m": "14.00",
            "transport_score": "70.00",
            "amenity_score": "75.00",
            "investment_score": "72.00",
            "amortization_years": "20.1",
            "demographics": {
                "year": 2024,
                "age_0_14_pct": 14.0,
                "age_15_24_pct": 13.0,
                "age_25_44_pct": 31.0,
                "age_45_64_pct": 27.0,
                "age_65_plus_pct": 15.0,
                "university_graduate_pct": 30.0,
                "high_school_graduate_pct": 24.0,
                "household_count": 180222,
                "population_density_km2": 14732,
            },
            "poi_data": {
                "metro_stations": 6,
                "marmaray_stations": 1,
                "hospitals": 9,
                "schools": 269,
                "shopping_malls": 4,
                "parks": 244,
            },
            "provenance_sources": [
                ("TUIK", "ADNKS-2024", 1),
                ("Emlakjet", "2026-01", 1),
                ("Endeksa", "2025-12", 1),
            ],
        },
        "deprem": {
            "pga_value": "0.2000",
            "soil_class": "ZB",
            "fault_distance_km": "12.00",
            "provenance_sources": [
                ("AFAD", "TBDY-2018", 1),
                ("IBB_DEZIM", "2019", 1),
                ("MTA", "diri-fay-2023", 1),
            ],
        },
        "price_history": [
            {"date": date(2025, 8, 1), "avg_price_sqm": "83333.00", "transaction_count": 465},
            {"date": date(2025, 9, 1), "avg_price_sqm": "85667.00", "transaction_count": 475},
            {"date": date(2025, 10, 1), "avg_price_sqm": "88000.00", "transaction_count": 485},
            {"date": date(2025, 11, 1), "avg_price_sqm": "90333.00", "transaction_count": 490},
            {"date": date(2025, 12, 1), "avg_price_sqm": "92667.00", "transaction_count": 495},
            {"date": date(2026, 1, 1), "avg_price_sqm": "95000.00", "transaction_count": 500},
        ],
    },
    # ─── Ataşehir ────────────────────────────────────────────────────
    {
        "city": "İstanbul",
        "district": "Ataşehir",
        "center": (40.9833, 29.1167),
        "area": {
            "population": 414866,
            "avg_price_sqm_sale": "63265.00",
            "avg_price_sqm_rent": "354.00",
            "price_trend_6m": "12.00",
            "transport_score": "65.00",
            "amenity_score": "78.00",
            "investment_score": "80.00",
            "amortization_years": "14.9",
            "demographics": {
                "year": 2024,
                "age_0_14_pct": 17.4,
                "age_15_24_pct": 12.0,
                "age_25_44_pct": 33.0,
                "age_45_64_pct": 28.5,
                "age_65_plus_pct": 9.1,
                "university_graduate_pct": 32.0,
                "high_school_graduate_pct": 25.0,
                "household_count": 138000,
                "population_density_km2": 16595,
            },
            "poi_data": {
                "metro_stations": 6,
                "marmaray_stations": 0,
                "hospitals": 29,
                "schools": 200,
                "shopping_malls": 6,
                "parks": 235,
            },
            "provenance_sources": [
                ("TUIK", "ADNKS-2024", 1),
                ("Emlakjet", "2026-02", 1),
                ("Endeksa", "2025-12", 1),
            ],
        },
        "deprem": {
            "pga_value": "0.3500",
            "soil_class": "ZC",
            "fault_distance_km": "18.00",
            "provenance_sources": [
                ("AFAD", "TBDY-2018", 1),
                ("IBB_DEZIM", "2019", 1),
                ("MTA", "diri-fay-2023", 1),
            ],
        },
        "price_history": [
            {"date": date(2025, 8, 1), "avg_price_sqm": "56487.00", "transaction_count": 550},
            {"date": date(2025, 9, 1), "avg_price_sqm": "57843.00", "transaction_count": 560},
            {"date": date(2025, 10, 1), "avg_price_sqm": "59199.00", "transaction_count": 570},
            {"date": date(2025, 11, 1), "avg_price_sqm": "60555.00", "transaction_count": 575},
            {"date": date(2025, 12, 1), "avg_price_sqm": "61910.00", "transaction_count": 580},
            {"date": date(2026, 1, 1), "avg_price_sqm": "63265.00", "transaction_count": 590},
        ],
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEED FONKSİYONLARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _update_area_extra_fields(
    session: Any,
    city: str,
    district: str,
    extra: dict[str, Any],
) -> None:
    """
    upsert_area_analysis'in kapsamadığı alanları güncelle.

    avg_price_sqm_rent, transport_score, amenity_score, investment_score,
    poi_data, amortization_years alanları mevcut repository SQL'inde yok.
    """
    update_sql = text("""
        UPDATE area_analyses SET
            avg_price_sqm_rent = :avg_price_sqm_rent,
            transport_score = :transport_score,
            amenity_score = :amenity_score,
            investment_score = :investment_score,
            poi_data = :poi_data::jsonb,
            amortization_years = :amortization_years,
            updated_at = now()
        WHERE city = :city
          AND district = :district
          AND neighborhood IS NULL
    """)
    session.execute(update_sql, {"city": city, "district": district, **extra})


def seed_area_analyses(session: Any) -> int:
    """
    AreaAnalysis seed — 3 ilçe.

    1. upsert_area_analysis() ile temel alanları yaz (idempotent).
    2. Ek alanları (kira, skorlar, POI) supplementary UPDATE ile doldur.

    Returns:
        Seed edilen kayıt sayısı.
    """
    count = 0

    for d in PILOT_DISTRICTS:
        area = d["area"]

        # — Provenance —
        provenance = build_provenance_fields(
            sources=area["provenance_sources"],
        )

        # — Temel alanlar (upsert_area_analysis destekli) —
        data: dict[str, Any] = {
            "city": d["city"],
            "district": d["district"],
            "neighborhood": None,
            "population": area["population"],
            "avg_price_sqm_sale": safe_decimal(area["avg_price_sqm_sale"]),
            "price_trend_6m": safe_decimal(area["price_trend_6m"]),
            "demographics": area["demographics"],
            **provenance,
        }

        operation, area_id = upsert_area_analysis(session, data)

        # — Ek alanlar (repository kapsamı dışında) —
        _update_area_extra_fields(session, d["city"], d["district"], {
            "avg_price_sqm_rent": str(safe_decimal(area["avg_price_sqm_rent"])),
            "transport_score": str(safe_decimal(area["transport_score"])),
            "amenity_score": str(safe_decimal(area["amenity_score"])),
            "investment_score": str(safe_decimal(area["investment_score"])),
            "poi_data": json.dumps(area["poi_data"]),
            "amortization_years": str(safe_decimal(area["amortization_years"])),
        })

        count += 1
        logger.info(
            "area_analysis_seeded",
            district=d["district"],
            operation=operation,
            population=area["population"],
            avg_price_sqm_sale=area["avg_price_sqm_sale"],
        )

    return count


def seed_deprem_risks(session: Any) -> int:
    """
    DepremRisk seed — 3 ilçe.

    PGA → risk_score dönüşümü calculate_risk_score() ile yapılır.
    PostGIS WKT build_point_wkt(lat, lon) ile oluşturulur.

    Returns:
        Seed edilen kayıt sayısı.
    """
    count = 0

    for d in PILOT_DISTRICTS:
        deprem = d["deprem"]
        lat, lon = d["center"]

        # — PGA → Risk skoru —
        pga = safe_decimal(deprem["pga_value"])
        risk_score = calculate_risk_score(pga)

        # — PostGIS WKT: SRID=4326;POINT(lon lat) —
        location_wkt = build_point_wkt(latitude=lat, longitude=lon)

        # — Provenance —
        provenance = build_provenance_fields(
            sources=deprem["provenance_sources"],
        )

        data: dict[str, Any] = {
            "city": d["city"],
            "district": d["district"],
            "neighborhood": None,
            "location_wkt": location_wkt,
            "risk_score": risk_score,
            "pga_value": pga,
            "soil_class": deprem["soil_class"],
            "fault_distance_km": safe_decimal(deprem["fault_distance_km"]),
            **provenance,
        }

        operation, risk_id = upsert_deprem_risk(session, data)
        count += 1

        logger.info(
            "deprem_risk_seeded",
            district=d["district"],
            operation=operation,
            pga=str(pga),
            risk_score=str(risk_score),
            soil_class=deprem["soil_class"],
            location_wkt=location_wkt,
        )

    return count


def seed_price_history(session: Any) -> int:
    """
    PriceHistory seed — 3 ilçe × 6 ay = 18 kayıt.

    Ağustos 2025 - Ocak 2026 arası aylık m² fiyat ve satış adet verileri.
    batch_insert_price_history() ile ON CONFLICT idempotent yazım.

    Returns:
        Seed edilen kayıt sayısı.
    """
    all_records: list[dict[str, Any]] = []

    for d in PILOT_DISTRICTS:
        for entry in d["price_history"]:
            record: dict[str, Any] = {
                "area_type": "district",
                "area_name": d["district"],
                "city": d["city"],
                "district": d["district"],
                "date": entry["date"],
                "avg_price_sqm": safe_decimal(entry["avg_price_sqm"]),
                "median_price": None,
                "listing_count": None,
                "transaction_count": entry["transaction_count"],
                "source": "seed_pilot",
                "provenance_version": f"seed-{entry['date'].strftime('%Y-%m')}",
            }
            all_records.append(record)

    count = batch_insert_price_history(session, all_records)

    logger.info(
        "price_history_seeded",
        total_records=len(all_records),
        upserted=count,
        districts=[d["district"] for d in PILOT_DISTRICTS],
    )

    return count


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main() -> None:
    """Tüm pilot verileri yükle."""
    print("=" * 60)
    print("İstanbul Pilot Veri Yükleme")
    print("İlçeler: Kadıköy, Üsküdar, Ataşehir")
    print("=" * 60)

    with get_sync_session() as session:
        # — AreaAnalysis —
        print("\n[1/3] AreaAnalysis seed başlıyor...")
        area_count = seed_area_analyses(session)
        print(f"  ✓ {area_count} ilçe AreaAnalysis kaydı yüklendi.")

        # — DepremRisk —
        print("\n[2/3] DepremRisk seed başlıyor...")
        deprem_count = seed_deprem_risks(session)
        print(f"  ✓ {deprem_count} ilçe DepremRisk kaydı yüklendi.")

        # — PriceHistory —
        print("\n[3/3] PriceHistory seed başlıyor...")
        price_count = seed_price_history(session)
        print(f"  ✓ {price_count} PriceHistory kaydı yüklendi.")

        # — Commit —
        session.commit()

        print("\n" + "=" * 60)
        print("ÖZET")
        print(f"  AreaAnalysis : {area_count} kayıt")
        print(f"  DepremRisk   : {deprem_count} kayıt")
        print(f"  PriceHistory : {price_count} kayıt")
        print(f"  TOPLAM       : {area_count + deprem_count + price_count} kayıt")
        print("=" * 60)
        print("Tüm pilot veriler başarıyla yüklendi.")

    logger.info(
        "seed_pilot_completed",
        area_count=area_count,
        deprem_count=deprem_count,
        price_count=price_count,
    )


if __name__ == "__main__":
    main()
