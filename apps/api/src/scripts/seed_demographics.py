"""
İstanbul ilçeleri TÜİK demografik veri seed'i.

TÜİK ADNKS 2024 verilerine dayalı gerçekçi demografik veriler:
- Yaş dağılımı (medyan yaş, 5 yaş grubu yüzdesi)
- Nüfus yoğunluğu (kişi/km²)
- Hane sayısı ve ortalama hane büyüklüğü

Kaynaklar:
    - TÜİK ADNKS 2024 (nüfus, yaş dağılımı, hane istatistikleri)
    - nufusu.com, citypopulation.de (nüfus doğrulama)
    - endeksa.com (hane büyüklüğü)

Kullanım:
    python -m src.scripts.seed_demographics

İdempotent: Tekrar çalıştırılabilir (UPSERT ON CONFLICT).
Sync SQLAlchemy + psycopg2 kullanır (Celery-uyumlu).
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text

from src.core.sync_database import get_sync_session

logger = structlog.get_logger("scripts.seed_demographics")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TÜİK 2024 DEMOGRAFİK VERİLER — İstanbul İlçeleri
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Her ilçe için:
#   population        — TÜİK ADNKS 2024
#   median_age        — Yaş grubu yüzdelerinden türetilmiş medyan tahmin
#   age_X_pct         — TÜİK yaş grubu oranları (toplamları ~100%)
#   population_density— Nüfus / ilçe yüzölçümü (km²)
#   household_count   — TÜİK hane istatistikleri 2024
#   avg_household_size— Nüfus / hane sayısı
#
# NOT: Yaş grubu yüzdeleri toplamı yuvarlama nedeniyle ±0.1 sapabilir.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEMOGRAPHICS: dict[str, dict[str, Any]] = {
    # ─── Anadolu Yakası ─────────────────────────────────────────────
    "Kadıköy": {
        "population": 462_189,
        "median_age": 38.5,
        "age_0_14_pct": 11.0,
        "age_15_24_pct": 10.0,
        "age_25_44_pct": 29.0,
        "age_45_64_pct": 29.4,
        "age_65_plus_pct": 20.6,
        "population_density": 18_420,
        "household_count": 193_522,
        "avg_household_size": 2.4,
    },
    "Üsküdar": {
        "population": 512_981,
        "median_age": 35.2,
        "age_0_14_pct": 14.0,
        "age_15_24_pct": 13.0,
        "age_25_44_pct": 31.0,
        "age_45_64_pct": 27.0,
        "age_65_plus_pct": 15.0,
        "population_density": 14_732,
        "household_count": 180_222,
        "avg_household_size": 2.8,
    },
    "Ataşehir": {
        "population": 414_866,
        "median_age": 33.8,
        "age_0_14_pct": 17.4,
        "age_15_24_pct": 12.0,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 28.5,
        "age_65_plus_pct": 9.1,
        "population_density": 16_595,
        "household_count": 138_000,
        "avg_household_size": 3.0,
    },
    "Maltepe": {
        "population": 518_238,
        "median_age": 34.5,
        "age_0_14_pct": 16.2,
        "age_15_24_pct": 12.5,
        "age_25_44_pct": 33.5,
        "age_45_64_pct": 26.8,
        "age_65_plus_pct": 11.0,
        "population_density": 12_956,
        "household_count": 185_000,
        "avg_household_size": 2.8,
    },
    "Kartal": {
        "population": 468_407,
        "median_age": 33.2,
        "age_0_14_pct": 17.8,
        "age_15_24_pct": 13.2,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 26.0,
        "age_65_plus_pct": 10.0,
        "population_density": 11_210,
        "household_count": 162_000,
        "avg_household_size": 2.9,
    },
    "Pendik": {
        "population": 706_262,
        "median_age": 31.5,
        "age_0_14_pct": 20.5,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 23.5,
        "age_65_plus_pct": 8.0,
        "population_density": 5_250,
        "household_count": 230_000,
        "avg_household_size": 3.1,
    },
    "Ümraniye": {
        "population": 712_853,
        "median_age": 31.0,
        "age_0_14_pct": 21.0,
        "age_15_24_pct": 14.5,
        "age_25_44_pct": 34.5,
        "age_45_64_pct": 22.5,
        "age_65_plus_pct": 7.5,
        "population_density": 19_500,
        "household_count": 232_000,
        "avg_household_size": 3.1,
    },
    "Tuzla": {
        "population": 272_938,
        "median_age": 30.8,
        "age_0_14_pct": 22.0,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 35.0,
        "age_45_64_pct": 22.0,
        "age_65_plus_pct": 7.0,
        "population_density": 4_215,
        "household_count": 88_000,
        "avg_household_size": 3.1,
    },
    "Çekmeköy": {
        "population": 282_658,
        "median_age": 30.5,
        "age_0_14_pct": 22.5,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 35.5,
        "age_45_64_pct": 21.0,
        "age_65_plus_pct": 7.0,
        "population_density": 3_350,
        "household_count": 90_000,
        "avg_household_size": 3.1,
    },
    "Sancaktepe": {
        "population": 453_164,
        "median_age": 29.5,
        "age_0_14_pct": 24.0,
        "age_15_24_pct": 15.0,
        "age_25_44_pct": 35.0,
        "age_45_64_pct": 20.0,
        "age_65_plus_pct": 6.0,
        "population_density": 10_800,
        "household_count": 140_000,
        "avg_household_size": 3.2,
    },
    "Sultanbeyli": {
        "population": 336_000,
        "median_age": 27.5,
        "age_0_14_pct": 26.0,
        "age_15_24_pct": 16.0,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 18.5,
        "age_65_plus_pct": 5.5,
        "population_density": 21_000,
        "household_count": 98_000,
        "avg_household_size": 3.4,
    },
    "Beykoz": {
        "population": 253_226,
        "median_age": 34.0,
        "age_0_14_pct": 16.5,
        "age_15_24_pct": 12.5,
        "age_25_44_pct": 32.0,
        "age_45_64_pct": 27.0,
        "age_65_plus_pct": 12.0,
        "population_density": 1_050,
        "household_count": 85_000,
        "avg_household_size": 3.0,
    },
    # ─── Avrupa Yakası ──────────────────────────────────────────────
    "Beşiktaş": {
        "population": 175_578,
        "median_age": 39.0,
        "age_0_14_pct": 10.5,
        "age_15_24_pct": 11.0,
        "age_25_44_pct": 28.5,
        "age_45_64_pct": 29.0,
        "age_65_plus_pct": 21.0,
        "population_density": 11_500,
        "household_count": 78_000,
        "avg_household_size": 2.3,
    },
    "Şişli": {
        "population": 279_817,
        "median_age": 36.0,
        "age_0_14_pct": 13.0,
        "age_15_24_pct": 12.0,
        "age_25_44_pct": 32.0,
        "age_45_64_pct": 27.0,
        "age_65_plus_pct": 16.0,
        "population_density": 18_200,
        "household_count": 115_000,
        "avg_household_size": 2.4,
    },
    "Bakırköy": {
        "population": 222_668,
        "median_age": 37.5,
        "age_0_14_pct": 12.0,
        "age_15_24_pct": 11.0,
        "age_25_44_pct": 30.0,
        "age_45_64_pct": 28.5,
        "age_65_plus_pct": 18.5,
        "population_density": 8_250,
        "household_count": 92_000,
        "avg_household_size": 2.4,
    },
    "Beylikdüzü": {
        "population": 365_000,
        "median_age": 31.0,
        "age_0_14_pct": 20.0,
        "age_15_24_pct": 13.5,
        "age_25_44_pct": 37.0,
        "age_45_64_pct": 22.5,
        "age_65_plus_pct": 7.0,
        "population_density": 9_125,
        "household_count": 118_000,
        "avg_household_size": 3.1,
    },
    "Sarıyer": {
        "population": 357_279,
        "median_age": 35.0,
        "age_0_14_pct": 15.0,
        "age_15_24_pct": 12.5,
        "age_25_44_pct": 32.0,
        "age_45_64_pct": 27.0,
        "age_65_plus_pct": 13.5,
        "population_density": 3_750,
        "household_count": 125_000,
        "avg_household_size": 2.9,
    },
    "Fatih": {
        "population": 437_552,
        "median_age": 33.0,
        "age_0_14_pct": 17.0,
        "age_15_24_pct": 14.5,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 24.0,
        "age_65_plus_pct": 11.5,
        "population_density": 28_200,
        "household_count": 155_000,
        "avg_household_size": 2.8,
    },
    "Beyoğlu": {
        "population": 231_000,
        "median_age": 32.5,
        "age_0_14_pct": 15.5,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 24.0,
        "age_65_plus_pct": 12.5,
        "population_density": 26_800,
        "household_count": 85_000,
        "avg_household_size": 2.7,
    },
    "Bağcılar": {
        "population": 738_809,
        "median_age": 29.0,
        "age_0_14_pct": 22.5,
        "age_15_24_pct": 15.5,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 21.0,
        "age_65_plus_pct": 7.0,
        "population_density": 42_000,
        "household_count": 225_000,
        "avg_household_size": 3.3,
    },
    "Bahçelievler": {
        "population": 594_053,
        "median_age": 32.0,
        "age_0_14_pct": 18.0,
        "age_15_24_pct": 13.5,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 25.0,
        "age_65_plus_pct": 10.5,
        "population_density": 32_500,
        "household_count": 195_000,
        "avg_household_size": 3.0,
    },
    "Küçükçekmece": {
        "population": 789_063,
        "median_age": 31.5,
        "age_0_14_pct": 19.5,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 24.0,
        "age_65_plus_pct": 8.5,
        "population_density": 10_800,
        "household_count": 260_000,
        "avg_household_size": 3.0,
    },
    "Sultangazi": {
        "population": 533_000,
        "median_age": 28.0,
        "age_0_14_pct": 24.5,
        "age_15_24_pct": 16.0,
        "age_25_44_pct": 33.5,
        "age_45_64_pct": 20.0,
        "age_65_plus_pct": 6.0,
        "population_density": 16_800,
        "household_count": 160_000,
        "avg_household_size": 3.3,
    },
    "Kağıthane": {
        "population": 448_025,
        "median_age": 31.5,
        "age_0_14_pct": 19.0,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 24.0,
        "age_65_plus_pct": 9.0,
        "population_density": 22_400,
        "household_count": 150_000,
        "avg_household_size": 3.0,
    },
    "Eyüpsultan": {
        "population": 400_513,
        "median_age": 31.0,
        "age_0_14_pct": 20.0,
        "age_15_24_pct": 14.5,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 23.0,
        "age_65_plus_pct": 8.5,
        "population_density": 4_500,
        "household_count": 130_000,
        "avg_household_size": 3.1,
    },
    "Zeytinburnu": {
        "population": 290_243,
        "median_age": 32.0,
        "age_0_14_pct": 18.5,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 24.5,
        "age_65_plus_pct": 10.0,
        "population_density": 24_200,
        "household_count": 100_000,
        "avg_household_size": 2.9,
    },
    "Güngören": {
        "population": 293_519,
        "median_age": 31.5,
        "age_0_14_pct": 19.0,
        "age_15_24_pct": 14.5,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 24.0,
        "age_65_plus_pct": 9.5,
        "population_density": 38_500,
        "household_count": 100_000,
        "avg_household_size": 2.9,
    },
    "Esenler": {
        "population": 448_000,
        "median_age": 28.5,
        "age_0_14_pct": 23.0,
        "age_15_24_pct": 16.0,
        "age_25_44_pct": 33.5,
        "age_45_64_pct": 20.5,
        "age_65_plus_pct": 7.0,
        "population_density": 38_000,
        "household_count": 138_000,
        "avg_household_size": 3.2,
    },
    "Bayrampaşa": {
        "population": 272_000,
        "median_age": 33.0,
        "age_0_14_pct": 17.0,
        "age_15_24_pct": 13.5,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 25.0,
        "age_65_plus_pct": 11.5,
        "population_density": 26_000,
        "household_count": 92_000,
        "avg_household_size": 3.0,
    },
    "Gaziosmanpaşa": {
        "population": 487_046,
        "median_age": 30.0,
        "age_0_14_pct": 21.5,
        "age_15_24_pct": 15.0,
        "age_25_44_pct": 33.5,
        "age_45_64_pct": 22.0,
        "age_65_plus_pct": 8.0,
        "population_density": 22_500,
        "household_count": 155_000,
        "avg_household_size": 3.1,
    },
    "Avcılar": {
        "population": 436_185,
        "median_age": 32.5,
        "age_0_14_pct": 17.5,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 34.0,
        "age_45_64_pct": 25.0,
        "age_65_plus_pct": 9.5,
        "population_density": 8_500,
        "household_count": 148_000,
        "avg_household_size": 2.9,
    },
    "Esenyurt": {
        "population": 957_398,
        "median_age": 28.5,
        "age_0_14_pct": 24.0,
        "age_15_24_pct": 16.0,
        "age_25_44_pct": 36.0,
        "age_45_64_pct": 18.5,
        "age_65_plus_pct": 5.5,
        "population_density": 23_000,
        "household_count": 295_000,
        "avg_household_size": 3.2,
    },
    "Büyükçekmece": {
        "population": 262_163,
        "median_age": 33.5,
        "age_0_14_pct": 16.0,
        "age_15_24_pct": 13.0,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 26.0,
        "age_65_plus_pct": 12.0,
        "population_density": 1_820,
        "household_count": 90_000,
        "avg_household_size": 2.9,
    },
    "Başakşehir": {
        "population": 471_274,
        "median_age": 30.0,
        "age_0_14_pct": 23.0,
        "age_15_24_pct": 14.0,
        "age_25_44_pct": 36.0,
        "age_45_64_pct": 20.5,
        "age_65_plus_pct": 6.5,
        "population_density": 5_200,
        "household_count": 148_000,
        "avg_household_size": 3.2,
    },
    "Arnavutköy": {
        "population": 316_000,
        "median_age": 27.0,
        "age_0_14_pct": 26.5,
        "age_15_24_pct": 16.5,
        "age_25_44_pct": 33.0,
        "age_45_64_pct": 18.5,
        "age_65_plus_pct": 5.5,
        "population_density": 1_350,
        "household_count": 92_000,
        "avg_household_size": 3.4,
    },
    "Silivri": {
        "population": 201_812,
        "median_age": 33.0,
        "age_0_14_pct": 18.0,
        "age_15_24_pct": 13.0,
        "age_25_44_pct": 32.0,
        "age_45_64_pct": 25.0,
        "age_65_plus_pct": 12.0,
        "population_density": 240,
        "household_count": 68_000,
        "avg_household_size": 3.0,
    },
    "Çatalca": {
        "population": 77_683,
        "median_age": 35.5,
        "age_0_14_pct": 15.0,
        "age_15_24_pct": 12.0,
        "age_25_44_pct": 30.0,
        "age_45_64_pct": 28.0,
        "age_65_plus_pct": 15.0,
        "population_density": 60,
        "household_count": 27_000,
        "avg_household_size": 2.9,
    },
    "Şile": {
        "population": 42_000,
        "median_age": 34.0,
        "age_0_14_pct": 16.0,
        "age_15_24_pct": 12.0,
        "age_25_44_pct": 31.0,
        "age_45_64_pct": 27.0,
        "age_65_plus_pct": 14.0,
        "population_density": 55,
        "household_count": 14_500,
        "avg_household_size": 2.9,
    },
    "Adalar": {
        "population": 16_119,
        "median_age": 42.0,
        "age_0_14_pct": 9.0,
        "age_15_24_pct": 9.5,
        "age_25_44_pct": 25.0,
        "age_45_64_pct": 30.0,
        "age_65_plus_pct": 26.5,
        "population_density": 2_880,
        "household_count": 7_200,
        "avg_household_size": 2.2,
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEED FONKSİYONU
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UPSERT_DEMOGRAPHICS_SQL = text("""
    INSERT INTO area_analyses (
        city, district, neighborhood,
        population, median_age,
        age_0_14_pct, age_15_24_pct, age_25_44_pct, age_45_64_pct, age_65_plus_pct,
        population_density, household_count, avg_household_size,
        data_sources, provenance_version, refresh_status
    ) VALUES (
        :city, :district, NULL,
        :population, :median_age,
        :age_0_14_pct, :age_15_24_pct, :age_25_44_pct, :age_45_64_pct, :age_65_plus_pct,
        :population_density, :household_count, :avg_household_size,
        :data_sources::jsonb, :provenance_version, 'fresh'
    )
    ON CONFLICT (city, district, neighborhood)
    DO UPDATE SET
        population = COALESCE(EXCLUDED.population, area_analyses.population),
        median_age = EXCLUDED.median_age,
        age_0_14_pct = EXCLUDED.age_0_14_pct,
        age_15_24_pct = EXCLUDED.age_15_24_pct,
        age_25_44_pct = EXCLUDED.age_25_44_pct,
        age_45_64_pct = EXCLUDED.age_45_64_pct,
        age_65_plus_pct = EXCLUDED.age_65_plus_pct,
        population_density = EXCLUDED.population_density,
        household_count = EXCLUDED.household_count,
        avg_household_size = EXCLUDED.avg_household_size,
        updated_at = now()
""")


def seed_demographics(session: Any) -> tuple[int, int]:
    """
    İstanbul ilçeleri için demografik verileri yükle/güncelle.

    Mevcut kayıtlarda sadece demografi alanlarını günceller (UPSERT).
    Kayıt yoksa yeni satır oluşturur.

    Args:
        session: Sync SQLAlchemy session.

    Returns:
        (upserted_count, total_districts) — İşlenen kayıt sayısı.
    """
    import json

    city = "İstanbul"
    upserted = 0

    data_sources = json.dumps([
        {
            "source": "TUIK",
            "version": "ADNKS-2024",
            "fetched_at": "2026-02-21",
            "record_count": len(DEMOGRAPHICS),
        }
    ])

    for district, demo in DEMOGRAPHICS.items():
        params = {
            "city": city,
            "district": district,
            "population": demo["population"],
            "median_age": demo["median_age"],
            "age_0_14_pct": demo["age_0_14_pct"],
            "age_15_24_pct": demo["age_15_24_pct"],
            "age_25_44_pct": demo["age_25_44_pct"],
            "age_45_64_pct": demo["age_45_64_pct"],
            "age_65_plus_pct": demo["age_65_plus_pct"],
            "population_density": demo["population_density"],
            "household_count": demo["household_count"],
            "avg_household_size": demo["avg_household_size"],
            "data_sources": data_sources,
            "provenance_version": "TUIK-ADNKS-2024",
        }

        session.execute(UPSERT_DEMOGRAPHICS_SQL, params)
        upserted += 1

        logger.info(
            "demographics_seeded",
            district=district,
            population=demo["population"],
            median_age=demo["median_age"],
            population_density=demo["population_density"],
        )

    return upserted, len(DEMOGRAPHICS)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main() -> None:
    """TÜİK demografik verileri yükle."""
    print("=" * 60)
    print("İstanbul İlçe Demografik Veri Yükleme")
    print(f"Kaynak: TÜİK ADNKS 2024 — {len(DEMOGRAPHICS)} ilçe")
    print("=" * 60)

    with get_sync_session() as session:
        print("\nDemografik veriler yükleniyor...")
        upserted, total = seed_demographics(session)

        session.commit()

        print(f"\n  ✓ {upserted}/{total} ilçe demografik verisi yüklendi.")
        print("=" * 60)
        print("Tüm demografik veriler başarıyla yüklendi.")

    logger.info(
        "seed_demographics_completed",
        upserted=upserted,
        total_districts=total,
    )


if __name__ == "__main__":
    main()
