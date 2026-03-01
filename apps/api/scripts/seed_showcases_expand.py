"""
Emlak Teknoloji Platformu - Vitrin Seed Genisleme Scripti

Mevcut 2 demo vitrine ek olarak 8 yeni vitrin olusturur.
Farkli temalar ve ilan gruplarini icerir.
Idempotent: ON CONFLICT (slug) DO UPDATE ile tekrar calistirabilirsiniz.

Kullanim:
    cd apps/api
    python3 -m scripts.seed_showcases_expand

Sunucuda:
    cd /var/www/petqas/apps/api
    source .venv/bin/activate
    python3 -m scripts.seed_showcases_expand
"""

from __future__ import annotations

import json
import random
from uuid import uuid4

import psycopg2
from psycopg2.extras import Json

# ──────────────────────────────────────────────
# Baglanti ayarlari (seed_demo.py ile ayni)
# ──────────────────────────────────────────────
DB_URL = "postgresql://petqas:PetQas2026SecureDB@127.0.0.1:5433/petqas_prod"

# ──────────────────────────────────────────────
# Sabit degerler — seed_demo.py'deki demo hesap
# ──────────────────────────────────────────────
OFFICE_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
USER_ID = "1e437f8f-3378-466b-b0f9-1a174fa561e3"  # Demo agent user_id

# Deterministik showcase UUID'leri (idempotent calisma icin)
SHOWCASE_IDS = [
    "bb000001-0000-0000-0000-000000000003",
    "bb000001-0000-0000-0000-000000000004",
    "bb000001-0000-0000-0000-000000000005",
    "bb000001-0000-0000-0000-000000000006",
    "bb000001-0000-0000-0000-000000000007",
    "bb000001-0000-0000-0000-000000000008",
    "bb000001-0000-0000-0000-000000000009",
    "bb000001-0000-0000-0000-000000000010",
]

# seed_demo.py'deki 15 property UUID'si
PROPERTY_IDS = [
    "aa000001-0000-0000-0000-000000000001",
    "aa000001-0000-0000-0000-000000000002",
    "aa000001-0000-0000-0000-000000000003",
    "aa000001-0000-0000-0000-000000000004",
    "aa000001-0000-0000-0000-000000000005",
    "aa000001-0000-0000-0000-000000000006",
    "aa000001-0000-0000-0000-000000000007",
    "aa000001-0000-0000-0000-000000000008",
    "aa000001-0000-0000-0000-000000000009",
    "aa000001-0000-0000-0000-000000000010",
    "aa000001-0000-0000-0000-000000000011",
    "aa000001-0000-0000-0000-000000000012",
    "aa000001-0000-0000-0000-000000000013",
    "aa000001-0000-0000-0000-000000000014",
    "aa000001-0000-0000-0000-000000000015",
]

# ──────────────────────────────────────────────
# 8 yeni vitrin tanimlamasi
# ──────────────────────────────────────────────
SHOWCASES = [
    {
        "id": SHOWCASE_IDS[0],
        "title": "Kadıköy Sahil Lüks Daireler",
        "slug": "kadikoy-sahil-luks-daireler",
        "description": "Kadıköy sahil şeridinde deniz manzaralı premium daireler",
        "theme": "modern",
        "settings": {"display_layout": "grid", "show_price": True, "show_sqm": True},
        # Kadikoy + Atasehir daireleri
        "selected_properties": [PROPERTY_IDS[0], PROPERTY_IDS[1], PROPERTY_IDS[3],
                                 PROPERTY_IDS[4], PROPERTY_IDS[11]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 127,
    },
    {
        "id": SHOWCASE_IDS[1],
        "title": "İstanbul Anadolu Kiralık Portföy",
        "slug": "istanbul-anadolu-kiralik-portfoy",
        "description": "Ataşehir, Maltepe ve Kartal'da uygun fiyatlı kiralık daireler",
        "theme": "classic",
        "settings": {"display_layout": "grid", "show_price": True, "show_sqm": True},
        # Farkli daireler
        "selected_properties": [PROPERTY_IDS[1], PROPERTY_IDS[2], PROPERTY_IDS[3],
                                 PROPERTY_IDS[4], PROPERTY_IDS[9], PROPERTY_IDS[10]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 85,
    },
    {
        "id": SHOWCASE_IDS[2],
        "title": "Ticari Yatırım Fırsatları",
        "slug": "ticari-yatirim-firsatlari",
        "description": "Dükkan, ofis ve işyeri yatırım fırsatları",
        "theme": "minimalist",
        "settings": {"display_layout": "grid", "show_price": True, "show_sqm": True},
        # Ofis + dukkan
        "selected_properties": [PROPERTY_IDS[11], PROPERTY_IDS[12], PROPERTY_IDS[13],
                                 PROPERTY_IDS[14]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 203,
    },
    {
        "id": SHOWCASE_IDS[3],
        "title": "Yeni Mezunlar İçin Başlangıç Evleri",
        "slug": "yeni-mezunlar-icin-baslangic-evleri",
        "description": "Bütçe dostu, ulaşıma yakın 1+1 ve 2+1 daireler",
        "theme": "modern",
        "settings": {"display_layout": "grid", "show_price": True, "show_sqm": True},
        # Kucuk daireler
        "selected_properties": [PROPERTY_IDS[2], PROPERTY_IDS[3], PROPERTY_IDS[4],
                                 PROPERTY_IDS[9], PROPERTY_IDS[10]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 312,
    },
    {
        "id": SHOWCASE_IDS[4],
        "title": "Aile Dostu Geniş Daireler",
        "slug": "aile-dostu-genis-daireler",
        "description": "3+1 ve üzeri, park ve okula yakın aile evleri",
        "theme": "classic",
        "settings": {"display_layout": "grid", "show_price": True, "show_sqm": True},
        # Buyuk daireler + villalar
        "selected_properties": [PROPERTY_IDS[0], PROPERTY_IDS[1], PROPERTY_IDS[5],
                                 PROPERTY_IDS[6], PROPERTY_IDS[7], PROPERTY_IDS[8]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 178,
    },
    {
        "id": SHOWCASE_IDS[5],
        "title": "Deniz Manzaralı Villa Koleksiyonu",
        "slug": "deniz-manzarali-villa-koleksiyonu",
        "description": "Büyükçekmece ve Silivri'de lüks villalar",
        "theme": "modern",
        "settings": {"display_layout": "carousel", "show_price": True, "show_sqm": True},
        # Villalar
        "selected_properties": [PROPERTY_IDS[5], PROPERTY_IDS[6], PROPERTY_IDS[8]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 456,
    },
    {
        "id": SHOWCASE_IDS[6],
        "title": "Kampüse Yakın Öğrenci Evleri",
        "slug": "kampuse-yakin-ogrenci-evleri",
        "description": "Üniversite çevresinde uygun fiyatlı kiralık seçenekler",
        "theme": "minimalist",
        "settings": {"display_layout": "grid", "show_price": True, "show_sqm": False},
        # Kucuk daireler
        "selected_properties": [PROPERTY_IDS[2], PROPERTY_IDS[3], PROPERTY_IDS[9],
                                 PROPERTY_IDS[10], PROPERTY_IDS[13]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 289,
    },
    {
        "id": SHOWCASE_IDS[7],
        "title": "Yatırımcı Paketi — Yüksek Getiri",
        "slug": "yatirimci-paketi-yuksek-getiri",
        "description": "Değer artışı yüksek bölgelerde yatırımlık mülkler",
        "theme": "modern",
        "settings": {"display_layout": "grid", "show_price": True, "show_sqm": True},
        # Karisik yatirimlik
        "selected_properties": [PROPERTY_IDS[0], PROPERTY_IDS[7], PROPERTY_IDS[12],
                                 PROPERTY_IDS[14]],
        "agent_phone": "+90 532 100 0000",
        "agent_email": "demo@petqas.com",
        "views_count": 167,
    },
]


def seed_showcases() -> None:
    """8 yeni vitrini DB'ye ekler. Idempotent: ON CONFLICT (slug) DO UPDATE."""
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # RLS bypass — platform_admin olarak calis
        cur.execute("SET LOCAL app.current_user_role = 'platform_admin'")
        cur.execute(
            "SET LOCAL app.current_office_id = %s", (OFFICE_ID,)
        )

        inserted = 0
        for s in SHOWCASES:
            cur.execute("""
                INSERT INTO showcases (
                    id, office_id, agent_id, title, slug, description,
                    selected_properties, theme, is_active, settings,
                    agent_phone, agent_email, views_count,
                    created_at, updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, true, %s,
                    %s, %s, %s,
                    NOW(), NOW()
                )
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    selected_properties = EXCLUDED.selected_properties,
                    theme = EXCLUDED.theme,
                    settings = EXCLUDED.settings,
                    views_count = EXCLUDED.views_count,
                    updated_at = NOW()
            """, (
                s["id"], OFFICE_ID, USER_ID,
                s["title"], s["slug"], s["description"],
                Json(s["selected_properties"]),
                s["theme"],
                Json(s["settings"]),
                s["agent_phone"], s["agent_email"], s["views_count"],
            ))
            inserted += 1
            print(f"  ✓ Vitrin: {s['title']}")

        conn.commit()
        print(f"\n✅ {inserted} vitrin basariyla seed edildi!")
        print(f"   (Mevcut 2 demo vitrinle birlikte toplam 10 vitrin)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Hata: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Vitrin Seed Genisleme Scripti")
    print("=" * 50)
    seed_showcases()
