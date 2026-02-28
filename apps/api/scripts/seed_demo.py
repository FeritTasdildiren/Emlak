"""
Emlak Teknoloji Platformu - Demo Hesap Seed Script

Demo ofis, kullanıcı, abonelik, müşteriler, ilanlar, vitrinler ve kota oluşturur.
İdempotent: ON CONFLICT DO NOTHING / DO UPDATE ile tekrar çalıştırılabilir.

Kullanım:
    cd apps/api
    python3 -m scripts.seed_demo

Sunucuda:
    cd /var/www/petqas/apps/api
    source .venv/bin/activate
    python3 -m scripts.seed_demo
"""

import uuid
from datetime import date, datetime, timezone

import bcrypt
import psycopg2
from psycopg2.extras import execute_values, Json

# ──────────────────────────────────────────────
# Bağlantı ayarları
# Sunucu DB: petqas kullanıcısı (RLS app_user)
# ──────────────────────────────────────────────
DB_URL = "postgresql://petqas:PetQas2026SecureDB@127.0.0.1:5433/petqas_prod"

# ──────────────────────────────────────────────
# Sabit UUID'ler (deterministik, tekrar çalıştırmaya uygun)
# ──────────────────────────────────────────────
OFFICE_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
USER_ID = "1e437f8f-3378-466b-b0f9-1a174fa561e3"  # Actual demo user ID from DB
SUBSCRIPTION_ID = "e1f2a3b4-c5d6-7890-abcd-ef1234567892"
QUOTA_ID = "f1a2b3c4-d5e6-7890-abcd-ef1234567893"

# Müşteri UUID'leri (10 adet)
CUSTOMER_IDS = [
    "c0000001-0000-0000-0000-000000000001",
    "c0000001-0000-0000-0000-000000000002",
    "c0000001-0000-0000-0000-000000000003",
    "c0000001-0000-0000-0000-000000000004",
    "c0000001-0000-0000-0000-000000000005",
    "c0000001-0000-0000-0000-000000000006",
    "c0000001-0000-0000-0000-000000000007",
    "c0000001-0000-0000-0000-000000000008",
    "c0000001-0000-0000-0000-000000000009",
    "c0000001-0000-0000-0000-000000000010",
]

# Property UUID'leri (15 adet)
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

# Showcase UUID'leri (2 adet)
SHOWCASE_IDS = [
    "bb000001-0000-0000-0000-000000000001",
    "bb000001-0000-0000-0000-000000000002",
]

# ──────────────────────────────────────────────
# Bcrypt şifre hash'i: Demo2026!
# ──────────────────────────────────────────────
PASSWORD_HASH = bcrypt.hashpw(b"Demo2026!", bcrypt.gensalt()).decode()

NOW = datetime.now(timezone.utc)


def seed_office(cur):
    """A. Demo ofis oluştur."""
    print("  → Ofis oluşturuluyor...")
    cur.execute("""
        INSERT INTO offices (id, name, slug, phone, email, city, district, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            phone = EXCLUDED.phone,
            email = EXCLUDED.email,
            updated_at = NOW()
    """, (
        OFFICE_ID,
        "PetQas Demo Emlak",
        "petqas-demo",
        "+90 216 555 0100",
        "info@petqas-demo.com",
        "İstanbul",
        "Kadıköy",
    ))
    print("  ✓ Ofis OK")


def seed_user(cur):
    """B. Demo kullanıcı oluştur."""
    print("  → Kullanıcı oluşturuluyor...")
    cur.execute("""
        INSERT INTO users (id, email, password_hash, full_name, role, office_id, is_active, is_verified, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, true, true, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            full_name = EXCLUDED.full_name,
            role = EXCLUDED.role,
            office_id = EXCLUDED.office_id,
            updated_at = NOW()
    """, (
        USER_ID,
        "demo@petqas.com",
        PASSWORD_HASH,
        "Demo Kullanıcı",
        "office_admin",
        OFFICE_ID,
    ))
    print("  ✓ Kullanıcı OK (demo@petqas.com / Demo2026!)")


def seed_subscription(cur):
    """C. Elite abonelik oluştur."""
    print("  → Elite abonelik oluşturuluyor...")
    cur.execute("""
        INSERT INTO subscriptions (
            id, office_id, plan_type, status, start_date, end_date,
            monthly_price, features, payment_failed_count, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            plan_type = EXCLUDED.plan_type,
            status = EXCLUDED.status,
            end_date = EXCLUDED.end_date,
            features = EXCLUDED.features,
            updated_at = NOW()
    """, (
        SUBSCRIPTION_ID,
        OFFICE_ID,
        "elite",
        "active",
        NOW,
        datetime(2027, 12, 31, tzinfo=timezone.utc),
        2999.00,
        Json({
            "max_users": 50,
            "max_properties": 10000,
            "max_valuations_per_month": 9999,
            "max_listings_per_month": 9999,
            "max_staging_per_month": 9999,
            "max_photos_per_month": 9999,
            "whatsapp_enabled": True,
            "api_access": True,
            "priority_support": True,
        }),
    ))
    print("  ✓ Elite abonelik OK")


def seed_customers(cur):
    """D. 10 müşteri oluştur — gerçekçi Türk isimleri ve İstanbul ilçeleri."""
    print("  → 10 müşteri oluşturuluyor...")

    customers = [
        {
            "id": CUSTOMER_IDS[0],
            "full_name": "Ahmet Yılmaz",
            "phone": "+90 532 100 0001",
            "email": "ahmet.yilmaz@example.com",
            "customer_type": "buyer",
            "lead_status": "hot",
            "budget_min": 3000000,
            "budget_max": 5000000,
            "preferred_type": "daire",
            "desired_rooms": "3+1",
            "desired_districts": ["Kadıköy", "Ataşehir"],
            "source": "internet",
            "notes": "Yatırım amaçlı daire arıyor. Acil.",
            "tags": ["yatırımcı", "acil"],
        },
        {
            "id": CUSTOMER_IDS[1],
            "full_name": "Elif Kaya",
            "phone": "+90 533 200 0002",
            "email": "elif.kaya@example.com",
            "customer_type": "buyer",
            "lead_status": "warm",
            "budget_min": 5000000,
            "budget_max": 8000000,
            "preferred_type": "villa",
            "desired_rooms": "4+1",
            "desired_districts": ["Beykoz", "Çekmeköy"],
            "source": "referans",
            "notes": "Bahçeli müstakil arıyor. Ailesiyle birlikte yaşayacak.",
            "tags": ["aile", "bahçeli"],
        },
        {
            "id": CUSTOMER_IDS[2],
            "full_name": "Mehmet Demir",
            "phone": "+90 534 300 0003",
            "email": "mehmet.demir@example.com",
            "customer_type": "seller",
            "lead_status": "hot",
            "budget_min": None,
            "budget_max": None,
            "preferred_type": "daire",
            "desired_rooms": None,
            "desired_districts": [],
            "source": "ilan",
            "notes": "Kadıköy Moda'da 2+1 dairesi var, acil satmak istiyor.",
            "tags": ["acil-satış"],
        },
        {
            "id": CUSTOMER_IDS[3],
            "full_name": "Zeynep Öztürk",
            "phone": "+90 535 400 0004",
            "email": "zeynep.ozturk@example.com",
            "customer_type": "renter",
            "lead_status": "warm",
            "budget_min": 15000,
            "budget_max": 25000,
            "preferred_type": "daire",
            "desired_rooms": "2+1",
            "desired_districts": ["Beşiktaş", "Şişli"],
            "source": "internet",
            "notes": "Üniversite hocası, merkeze yakın kiralık arıyor.",
            "tags": ["kiralık", "merkez"],
        },
        {
            "id": CUSTOMER_IDS[4],
            "full_name": "Fatih Arslan",
            "phone": "+90 536 500 0005",
            "email": "fatih.arslan@example.com",
            "customer_type": "buyer",
            "lead_status": "cold",
            "budget_min": 10000000,
            "budget_max": 20000000,
            "preferred_type": "arsa",
            "desired_rooms": None,
            "desired_districts": ["Tuzla", "Pendik"],
            "source": "referans",
            "notes": "İnşaat firması sahibi, arsa arıyor.",
            "tags": ["müteahhit", "arsa"],
        },
        {
            "id": CUSTOMER_IDS[5],
            "full_name": "Ayşe Çelik",
            "phone": "+90 537 600 0006",
            "email": "ayse.celik@example.com",
            "customer_type": "landlord",
            "lead_status": "warm",
            "budget_min": None,
            "budget_max": None,
            "preferred_type": None,
            "desired_rooms": None,
            "desired_districts": [],
            "source": "ilan",
            "notes": "3 dairesi var, kiracı arıyor. Ataşehir ve Kadıköy.",
            "tags": ["ev-sahibi", "çoklu-mülk"],
        },
        {
            "id": CUSTOMER_IDS[6],
            "full_name": "Can Şahin",
            "phone": "+90 538 700 0007",
            "email": "can.sahin@example.com",
            "customer_type": "buyer",
            "lead_status": "hot",
            "budget_min": 2000000,
            "budget_max": 3500000,
            "preferred_type": "daire",
            "desired_rooms": "2+1",
            "desired_districts": ["Üsküdar", "Kadıköy"],
            "source": "telegram",
            "notes": "Yeni evli çift, ilk evlerini arıyor.",
            "tags": ["ilk-ev", "genç-çift"],
        },
        {
            "id": CUSTOMER_IDS[7],
            "full_name": "Deniz Aydın",
            "phone": "+90 539 800 0008",
            "email": "deniz.aydin@example.com",
            "customer_type": "buyer",
            "lead_status": "warm",
            "budget_min": 1500000,
            "budget_max": 3000000,
            "preferred_type": "ofis",
            "desired_rooms": None,
            "desired_districts": ["Levent", "Maslak"],
            "source": "internet",
            "notes": "Startup ofisi arıyor, 80-120m² arası.",
            "tags": ["ticari", "startup"],
        },
        {
            "id": CUSTOMER_IDS[8],
            "full_name": "Selin Koç",
            "phone": "+90 541 900 0009",
            "email": "selin.koc@example.com",
            "customer_type": "renter",
            "lead_status": "converted",
            "budget_min": 20000,
            "budget_max": 35000,
            "preferred_type": "daire",
            "desired_rooms": "3+1",
            "desired_districts": ["Kadıköy", "Maltepe"],
            "source": "referans",
            "notes": "Kiralık bulundu, sözleşme imzalandı.",
            "tags": ["tamamlandı"],
        },
        {
            "id": CUSTOMER_IDS[9],
            "full_name": "Burak Erdoğan",
            "phone": "+90 542 000 0010",
            "email": "burak.erdogan@example.com",
            "customer_type": "seller",
            "lead_status": "warm",
            "budget_min": None,
            "budget_max": None,
            "preferred_type": "dükkan",
            "desired_rooms": None,
            "desired_districts": [],
            "source": "yürüyüş",
            "notes": "Üsküdar'da 85m² dükkan satmak istiyor.",
            "tags": ["ticari", "dükkan"],
        },
    ]

    for c in customers:
        cur.execute("""
            INSERT INTO customers (
                id, office_id, agent_id, full_name, phone, email, notes,
                customer_type, lead_status, budget_min, budget_max,
                preferred_type, desired_rooms, desired_districts,
                tags, source, created_at, updated_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, NOW(), NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                phone = EXCLUDED.phone,
                email = EXCLUDED.email,
                notes = EXCLUDED.notes,
                customer_type = EXCLUDED.customer_type,
                lead_status = EXCLUDED.lead_status,
                budget_min = EXCLUDED.budget_min,
                budget_max = EXCLUDED.budget_max,
                updated_at = NOW()
        """, (
            c["id"], OFFICE_ID, USER_ID,
            c["full_name"], c["phone"], c["email"], c["notes"],
            c["customer_type"], c["lead_status"],
            c["budget_min"], c["budget_max"],
            c["preferred_type"], c["desired_rooms"],
            Json(c["desired_districts"]),
            Json(c["tags"]), c["source"],
        ))

    print(f"  ✓ {len(customers)} müşteri OK")


def seed_properties(cur):
    """E. 15 property oluştur — 5 daire + 4 villa + 3 ofis + 2 arsa + 1 dükkan."""
    print("  → 15 ilan oluşturuluyor...")

    # (id, title, property_type, listing_type, price, rooms, gross_area, net_area,
    #  floor_number, total_floors, building_age, heating_type,
    #  city, district, neighborhood, lat, lon, features, status)
    properties = [
        # ── 5 Daire ──
        (PROPERTY_IDS[0],
         "Kadıköy Moda Deniz Manzaralı 3+1 Daire", "daire", "sale", 6500000,
         "3+1", 140, 120, 5, 8, 3, "doğalgaz kombi",
         "İstanbul", "Kadıköy", "Caferağa", 40.9862, 29.0262,
         {"balkon": True, "otopark": True, "asansör": True, "güvenlik": True},
         "active"),

        (PROPERTY_IDS[1],
         "Ataşehir Ağaoğlu My Home 2+1 Residence", "daire", "sale", 4200000,
         "2+1", 105, 90, 12, 25, 5, "merkezi",
         "İstanbul", "Ataşehir", "Atatürk", 40.9923, 29.1187,
         {"havuz": True, "spor-salonu": True, "otopark": True, "güvenlik": True},
         "active"),

        (PROPERTY_IDS[2],
         "Üsküdar Çengelköy Boğaz Manzaralı 4+1", "daire", "sale", 12000000,
         "4+1", 200, 175, 3, 6, 8, "doğalgaz kombi",
         "İstanbul", "Üsküdar", "Çengelköy", 41.0466, 29.0565,
         {"balkon": True, "deniz-manzarası": True, "otopark": True},
         "active"),

        (PROPERTY_IDS[3],
         "Beşiktaş Levent Kiralık 1+1 Stüdyo", "daire", "rent", 22000,
         "1+1", 55, 45, 8, 15, 2, "merkezi",
         "İstanbul", "Beşiktaş", "Levent", 41.0812, 29.0129,
         {"eşyalı": True, "asansör": True, "güvenlik": True},
         "active"),

        (PROPERTY_IDS[4],
         "Maltepe Sahil Yolu 3+1 Sıfır Daire", "daire", "sale", 5800000,
         "3+1", 135, 115, 7, 12, 0, "yerden ısıtma",
         "İstanbul", "Maltepe", "Cevizli", 40.9333, 29.1500,
         {"balkon": True, "otopark": True, "asansör": True, "akıllı-ev": True},
         "active"),

        # ── 4 Villa ──
        (PROPERTY_IDS[5],
         "Beykoz Anadoluhisarı Müstakil Villa", "villa", "sale", 18500000,
         "5+2", 400, 350, None, 3, 10, "doğalgaz kombi",
         "İstanbul", "Beykoz", "Anadoluhisarı", 41.0827, 29.0686,
         {"bahçe": True, "havuz": True, "otopark": True, "garaj": True},
         "active"),

        (PROPERTY_IDS[6],
         "Çekmeköy Orman Kenarı Triplex Villa", "villa", "sale", 14000000,
         "4+2", 320, 280, None, 3, 4, "doğalgaz kombi",
         "İstanbul", "Çekmeköy", "Merkez", 41.0428, 29.1846,
         {"bahçe": True, "barbekü": True, "otopark": True, "güvenlik": True},
         "active"),

        (PROPERTY_IDS[7],
         "Sarıyer Tarabya Kiralık Villa", "villa", "rent", 85000,
         "4+1", 280, 240, None, 2, 15, "doğalgaz kombi",
         "İstanbul", "Sarıyer", "Tarabya", 41.1209, 29.0472,
         {"bahçe": True, "deniz-manzarası": True, "otopark": True},
         "active"),

        (PROPERTY_IDS[8],
         "Büyükçekmece Göl Manzaralı Modern Villa", "villa", "sale", 9500000,
         "3+1", 250, 210, None, 2, 2, "yerden ısıtma",
         "İstanbul", "Büyükçekmece", "Bahçelievler", 41.0214, 28.5819,
         {"bahçe": True, "havuz": True, "akıllı-ev": True, "güneş-paneli": True},
         "active"),

        # ── 3 Ofis ──
        (PROPERTY_IDS[9],
         "Levent Plaza'da 200m² Ofis", "ofis", "sale", 7800000,
         None, 220, 200, 10, 20, 6, "merkezi klima",
         "İstanbul", "Beşiktaş", "Levent", 41.0787, 29.0119,
         {"toplantı-odası": True, "otopark": True, "resepsiyon": True},
         "active"),

        (PROPERTY_IDS[10],
         "Maslak Atatürk Oto Sanayi Ofis Katı", "ofis", "rent", 45000,
         None, 150, 130, 5, 12, 8, "merkezi klima",
         "İstanbul", "Sarıyer", "Maslak", 41.1112, 29.0205,
         {"açık-ofis": True, "otopark": True, "asansör": True},
         "active"),

        (PROPERTY_IDS[11],
         "Kadıköy Moda Kiralık Home Office", "ofis", "rent", 18000,
         None, 80, 70, 2, 5, 12, "doğalgaz kombi",
         "İstanbul", "Kadıköy", "Moda", 40.9840, 29.0240,
         {"balkon": True, "eşyalı": True},
         "active"),

        # ── 2 Arsa ──
        (PROPERTY_IDS[12],
         "Tuzla Orhanlı İmarlı 500m² Arsa", "arsa", "sale", 4500000,
         None, 500, None, None, None, None, None,
         "İstanbul", "Tuzla", "Orhanlı", 40.8730, 29.2890,
         {"imar-durumu": "konut", "yol-cephesi": True, "altyapı": True},
         "active"),

        (PROPERTY_IDS[13],
         "Pendik Kurtköy Ticari İmarlı 1200m² Arsa", "arsa", "sale", 15000000,
         None, 1200, None, None, None, None, None,
         "İstanbul", "Pendik", "Kurtköy", 40.8996, 29.3097,
         {"imar-durumu": "ticari", "yol-cephesi": True, "havalimanı-yakın": True},
         "active"),

        # ── 1 Dükkan ──
        (PROPERTY_IDS[14],
         "Üsküdar Bağlarbaşı Cadde Üzeri Dükkan", "dükkan", "sale", 3200000,
         None, 90, 85, 0, 4, 20, None,
         "İstanbul", "Üsküdar", "Bağlarbaşı", 41.0150, 29.0350,
         {"cadde-cephe": True, "wc": True, "depo": True},
         "active"),
    ]

    for p in properties:
        (pid, title, ptype, ltype, price,
         rooms, gross, net, floor, total_floors, age, heating,
         city, district, neighborhood, lat, lon, features, status) = p

        # PostGIS POINT: ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        location_wkt = f"SRID=4326;POINT({lon} {lat})"

        cur.execute("""
            INSERT INTO properties (
                id, office_id, agent_id, title, property_type, listing_type, price, currency,
                rooms, gross_area, net_area, floor_number, total_floors, building_age, heating_type,
                city, district, neighborhood, location, features, photos, status,
                is_shared, share_visibility, views_count, created_at, updated_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, 'TRY',
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, ST_GeogFromText(%s), %s, '[]'::jsonb, %s,
                false, 'private', 0, NOW(), NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                price = EXCLUDED.price,
                status = EXCLUDED.status,
                features = EXCLUDED.features,
                updated_at = NOW()
        """, (
            pid, OFFICE_ID, USER_ID, title, ptype, ltype, price,
            rooms, gross, net, floor, total_floors, age, heating,
            city, district, neighborhood, location_wkt,
            Json(features), status,
        ))

    print(f"  ✓ {len(properties)} ilan OK")


def seed_showcases(cur):
    """F. 2 vitrin oluştur — her biri 3-5 property ile."""
    print("  → 2 vitrin oluşturuluyor...")

    showcases = [
        {
            "id": SHOWCASE_IDS[0],
            "title": "Kadıköy & Çevresi Seçkin Portföy",
            "slug": "demo-kadikoy-seckin",
            "description": "Kadıköy, Ataşehir ve Maltepe bölgesindeki en iyi fırsatlar. Deniz manzaralı daireler ve modern residanslar.",
            "selected_properties": [
                PROPERTY_IDS[0],   # Kadıköy Moda daire
                PROPERTY_IDS[1],   # Ataşehir residence
                PROPERTY_IDS[4],   # Maltepe sıfır daire
                PROPERTY_IDS[11],  # Kadıköy Moda home office
                PROPERTY_IDS[14],  # Üsküdar dükkan
            ],
            "theme": "modern",
            "agent_phone": "+90 532 100 0000",
            "agent_email": "demo@petqas.com",
        },
        {
            "id": SHOWCASE_IDS[1],
            "title": "İstanbul Villa & Arsa Koleksiyonu",
            "slug": "demo-villa-arsa",
            "description": "İstanbul'un en prestijli bölgelerinde villa ve yatırımlık arsa fırsatları.",
            "selected_properties": [
                PROPERTY_IDS[5],   # Beykoz villa
                PROPERTY_IDS[6],   # Çekmeköy villa
                PROPERTY_IDS[8],   # Büyükçekmece villa
            ],
            "theme": "classic",
            "agent_phone": "+90 532 100 0000",
            "agent_email": "demo@petqas.com",
        },
    ]

    for s in showcases:
        cur.execute("""
            INSERT INTO showcases (
                id, office_id, agent_id, title, slug, description,
                selected_properties, theme, is_active, settings,
                agent_phone, agent_email, views_count,
                created_at, updated_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, true, '{}'::jsonb,
                %s, %s, 0,
                NOW(), NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                selected_properties = EXCLUDED.selected_properties,
                theme = EXCLUDED.theme,
                updated_at = NOW()
        """, (
            s["id"], OFFICE_ID, USER_ID, s["title"], s["slug"], s["description"],
            Json(s["selected_properties"]),
            s["theme"], s["agent_phone"], s["agent_email"],
        ))

    print(f"  ✓ {len(showcases)} vitrin OK")


def seed_usage_quota(cur):
    """G. Demo ofis için aylık kota kaydı."""
    print("  → Kullanım kotası oluşturuluyor...")

    today = date.today()
    period_start = today.replace(day=1)
    # Ay sonu hesapla
    if today.month == 12:
        period_end = today.replace(year=today.year + 1, month=1, day=1)
    else:
        period_end = today.replace(month=today.month + 1, day=1)
    # period_end ayın son günü olmalı (bir sonraki ayın 1'inden 1 gün çıkar)
    from datetime import timedelta
    period_end = period_end - timedelta(days=1)

    cur.execute("""
        INSERT INTO usage_quotas (
            id, office_id, period_start, period_end,
            valuations_used, valuations_limit,
            listings_used, staging_used, photos_used, credit_balance,
            created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, 0, 9999, 0, 0, 0, 100, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            period_end = EXCLUDED.period_end,
            valuations_limit = 9999,
            credit_balance = 100,
            updated_at = NOW()
    """, (
        QUOTA_ID, OFFICE_ID, period_start, period_end,
    ))
    print("  ✓ Kullanım kotası OK (Elite: 9999 değerleme/ay)")


def main():
    """Ana fonksiyon — tüm seed adımlarını sırayla çalıştırır."""
    print("=" * 60)
    print("  Emlak Demo Seed Script")
    print("=" * 60)
    print()

    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()

        # RLS ayarları — petqas kullanıcısı RLS'e tabi
        # platform_admin olarak SET LOCAL yapmamız lazım
        cur.execute("SET LOCAL app.current_user_role = 'platform_admin'")
        cur.execute(f"SET LOCAL app.current_office_id = '{OFFICE_ID}'")

        print("[1/7] Ofis")
        seed_office(cur)

        print("[2/7] Kullanıcı (SKIP — already updated)")
        # seed_user(cur)  # Already updated via direct SQL

        print("[3/7] Abonelik (SKIP — already elite)")
        # seed_subscription(cur)  # Already updated to elite

        print("[4/7] Müşteriler")
        seed_customers(cur)

        print("[5/7] İlanlar")
        seed_properties(cur)

        print("[6/7] Vitrinler")
        seed_showcases(cur)

        print("[7/7] Kullanım Kotası")
        seed_usage_quota(cur)

        conn.commit()
        print()
        print("=" * 60)
        print("  ✅ Tüm seed verileri başarıyla eklendi!")
        print("=" * 60)
        print()
        print("  Giriş Bilgileri:")
        print("  ─────────────────────────────────")
        print("  Email    : demo@petqas.com")
        print("  Şifre    : Demo2026!")
        print("  Plan     : Elite")
        print("  Ofis     : PetQas Demo Emlak")
        print("  ─────────────────────────────────")
        print(f"  Müşteri  : 10 adet")
        print(f"  İlan     : 15 adet")
        print(f"  Vitrin   : 2 adet")
        print()

    except Exception as e:
        print(f"\n  ❌ HATA: {e}")
        if 'conn' in dir():
            conn.rollback()
        raise
    finally:
        if 'cur' in dir():
            cur.close()
        if 'conn' in dir():
            conn.close()


if __name__ == "__main__":
    main()
