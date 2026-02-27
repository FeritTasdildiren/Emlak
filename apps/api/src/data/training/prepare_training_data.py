"""
Istanbul Konut Piyasasi - LightGBM Egitim Verisi Hazirlama Scripti

district_centers.py koordinatlari ve istanbul_districts.json ilce verileri
kullanilarak sentetik egitim verisi uretir.

Cikti: istanbul_training_data.csv
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

# ── Sabitler ──────────────────────────────────────────────────────────
SEED = 42
MIN_RECORDS_PER_DISTRICT = 80
MAX_RECORDS_PER_DISTRICT = 120

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_JSON = SCRIPT_DIR / "istanbul_districts.json"
OUTPUT_CSV = SCRIPT_DIR / "istanbul_training_data.csv"

# ── Emlak tipleri ve dagilimlari ──────────────────────────────────────
PROPERTY_TYPES = ["Daire", "Villa", "Mustakil", "IsYeri"]
PROPERTY_WEIGHTS = [0.75, 0.08, 0.07, 0.10]

TYPE_FACTORS: dict[str, float] = {
    "Daire": 1.0,
    "Villa": 1.4,
    "Mustakil": 1.2,
    "IsYeri": 1.1,
}

# Oda dagilimi: (room_count, living_room_count) ve olasilik agirliklari
ROOM_CONFIGS = [
    (1, 1, 0.10),  # 1+1
    (2, 1, 0.25),  # 2+1
    (3, 1, 0.35),  # 3+1
    (4, 1, 0.15),  # 4+1
    (5, 1, 0.05),  # 5+1
    (5, 2, 0.03),  # 5+2
    (6, 2, 0.02),  # 6+2
    (1, 0, 0.05),  # Stüdyo (1+0)
]

# Isitma tipleri
HEATING_TYPES = ["Dogalgaz_Kombi", "Merkezi", "Dogalgaz_Kat", "Soba", "Klima", "Yerden_Isitma"]
HEATING_WEIGHTS = [0.40, 0.20, 0.15, 0.08, 0.07, 0.10]

# Otopark tipleri: 0=yok, 1=acik, 2=kapali
PARKING_TYPES = [0, 1, 2]
PARKING_WEIGHTS = [0.35, 0.30, 0.35]

# Deprem riski -> sayisal skor
EARTHQUAKE_RISK_MAP: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "very_high": 4,
}

# CSV sutun siralamasi
CSV_COLUMNS = [
    "district",
    "neighborhood",
    "property_type",
    "gross_sqm",
    "net_sqm",
    "room_count",
    "living_room_count",
    "floor",
    "total_floors",
    "building_age",
    "bathroom_count",
    "has_balcony",
    "parking_type",
    "has_elevator",
    "heating_type",
    "lat",
    "lon",
    "earthquake_risk_score",
    "transport_score",
    "socioeconomic_level",
    "price",
]


def _weighted_choice(items: list, weights: list) -> any:
    """random.choices ile agirlikli secim (tek eleman)."""
    return random.choices(items, weights=weights, k=1)[0]


def _generate_sqm(property_type: str, room_count: int) -> tuple[int, int]:
    """Emlak tipine ve oda sayisina gore brut/net alan uret."""
    base_map = {
        1: (45, 70),
        2: (65, 100),
        3: (90, 140),
        4: (120, 180),
        5: (150, 220),
        6: (180, 280),
    }
    low, high = base_map.get(room_count, (90, 140))

    if property_type == "Villa":
        low = int(low * 1.5)
        high = int(high * 1.8)
    elif property_type == "Mustakil":
        low = int(low * 1.2)
        high = int(high * 1.4)
    elif property_type == "IsYeri":
        low = max(30, int(low * 0.6))
        high = int(high * 0.8)

    gross_sqm = random.randint(low, high)
    net_ratio = random.uniform(0.78, 0.92)
    net_sqm = int(gross_sqm * net_ratio)
    return gross_sqm, net_sqm


def _generate_building(property_type: str, district_avg_age: int) -> tuple[int, int, int]:
    """Kat, toplam kat, bina yasi uret."""
    if property_type == "Villa":
        total_floors = random.randint(2, 3)
        floor = random.randint(1, total_floors)
        age = max(0, random.randint(0, district_avg_age))
    elif property_type == "Mustakil":
        total_floors = random.randint(1, 3)
        floor = random.randint(1, total_floors)
        age = max(0, random.randint(5, district_avg_age + 10))
    elif property_type == "IsYeri":
        total_floors = random.randint(3, 15)
        floor = random.randint(0, min(3, total_floors))  # genelde alt katlar
        age = max(0, random.randint(0, district_avg_age + 5))
    else:  # Daire
        total_floors = random.randint(4, 20)
        floor = random.randint(1, total_floors)
        age_spread = max(0, district_avg_age + random.randint(-10, 10))
        age = max(0, age_spread)
    return floor, total_floors, age


def _calculate_price(
    district_avg_price: int,
    net_sqm: int,
    building_age: int,
    floor: int,
    has_balcony: int,
    has_elevator: int,
    parking_type: int,
    property_type: str,
) -> int:
    """
    Fiyat hesaplama formulu:
        base_price = district_avg_price_per_sqm * net_sqm
        age_factor = max(0.60, 1.0 - building_age * 0.008)
        floor_factor = 1.0 + max(0, floor - 1) * 0.01
        feature_bonus = 1.0 + has_balcony*0.02 + has_elevator*0.03 + (parking==2)*0.05
        type_factor = {"Daire": 1.0, "Villa": 1.4, "Mustakil": 1.2, "IsYeri": 1.1}
        noise = random.uniform(0.85, 1.15)
        price = int(base * age * floor * feature * type * noise)
    """
    base_price = district_avg_price * net_sqm
    age_factor = max(0.60, 1.0 - building_age * 0.008)
    floor_factor = 1.0 + max(0, floor - 1) * 0.01
    feature_bonus = (
        1.0
        + has_balcony * 0.02
        + has_elevator * 0.03
        + (1 if parking_type == 2 else 0) * 0.05
    )
    type_factor = TYPE_FACTORS.get(property_type, 1.0)
    noise = random.uniform(0.85, 1.15)
    price = int(base_price * age_factor * floor_factor * feature_bonus * type_factor * noise)
    return price


def generate_records(district: dict) -> list[dict]:
    """Tek bir ilce icin sentetik emlak kayitlari uret."""
    records: list[dict] = []
    n = random.randint(MIN_RECORDS_PER_DISTRICT, MAX_RECORDS_PER_DISTRICT)

    name = district["name"]
    avg_price = district["avg_price_per_sqm"]
    lat = district["lat"]
    lon = district["lon"]
    eq_risk = EARTHQUAKE_RISK_MAP.get(district["earthquake_risk"], 2)
    transport = district["transport_score"]
    socio = district["socioeconomic_level"]
    avg_age = district["avg_building_age"]
    neighborhoods = district["neighborhoods"]

    for _ in range(n):
        # Emlak tipi
        property_type = _weighted_choice(PROPERTY_TYPES, PROPERTY_WEIGHTS)

        # Oda konfigurasyonu
        configs = [(r, l) for r, l, _ in ROOM_CONFIGS]
        weights = [w for _, _, w in ROOM_CONFIGS]
        room_count, living_room_count = _weighted_choice(configs, weights)

        # Villa/Mustakil icin minimum 3 oda
        if property_type in ("Villa", "Mustakil") and room_count < 3:
            room_count = random.randint(3, 5)
            living_room_count = 1 if room_count <= 4 else 2

        # Alan
        gross_sqm, net_sqm = _generate_sqm(property_type, room_count)

        # Bina bilgileri
        floor, total_floors, building_age = _generate_building(property_type, avg_age)

        # Banyo sayisi
        if room_count <= 2:
            bathroom_count = 1
        elif room_count <= 4:
            bathroom_count = random.choice([1, 2])
        else:
            bathroom_count = random.choice([2, 3])

        # Ozellikler
        has_balcony = random.choices([0, 1], weights=[0.15, 0.85], k=1)[0]
        parking_type = _weighted_choice(PARKING_TYPES, PARKING_WEIGHTS)

        # Asansor: yuksek binalar ve yeni binalarda daha olasilikli
        if total_floors >= 5:
            has_elevator = random.choices([0, 1], weights=[0.10, 0.90], k=1)[0]
        elif total_floors >= 3:
            has_elevator = random.choices([0, 1], weights=[0.40, 0.60], k=1)[0]
        else:
            has_elevator = 0

        # Isitma
        heating_type = _weighted_choice(HEATING_TYPES, HEATING_WEIGHTS)

        # Mahalle
        neighborhood = random.choice(neighborhoods)

        # Koordinat varyasyonu (ilce icinde kucuk farklar)
        rec_lat = round(lat + random.uniform(-0.015, 0.015), 4)
        rec_lon = round(lon + random.uniform(-0.015, 0.015), 4)

        # Fiyat
        price = _calculate_price(
            avg_price, net_sqm, building_age, floor,
            has_balcony, has_elevator, parking_type, property_type,
        )

        records.append({
            "district": name,
            "neighborhood": neighborhood,
            "property_type": property_type,
            "gross_sqm": gross_sqm,
            "net_sqm": net_sqm,
            "room_count": room_count,
            "living_room_count": living_room_count,
            "floor": floor,
            "total_floors": total_floors,
            "building_age": building_age,
            "bathroom_count": bathroom_count,
            "has_balcony": has_balcony,
            "parking_type": parking_type,
            "has_elevator": has_elevator,
            "heating_type": heating_type,
            "lat": rec_lat,
            "lon": rec_lon,
            "earthquake_risk_score": eq_risk,
            "transport_score": transport,
            "socioeconomic_level": socio,
            "price": price,
        })

    return records


def main() -> None:
    """Ana akis: JSON oku -> kayit uret -> CSV yaz."""
    random.seed(SEED)

    # JSON oku
    with open(INPUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    districts = data["districts"]
    print(f"[INFO] {len(districts)} ilce yuklendi.")

    # Tum kayitlari uret
    all_records: list[dict] = []
    for district in districts:
        records = generate_records(district)
        all_records.extend(records)
        print(f"  {district['name']:20s} -> {len(records):4d} kayit")

    print(f"\n[INFO] Toplam kayit sayisi: {len(all_records)}")

    # CSV yaz
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"[OK] CSV kaydedildi: {OUTPUT_CSV}")

    # Istatistikler
    prices = [r["price"] for r in all_records]
    print("\n[ISTATISTIK]")
    print(f"  Min fiyat:     {min(prices):>15,} TL")
    print(f"  Max fiyat:     {max(prices):>15,} TL")
    print(f"  Ort fiyat:     {sum(prices) // len(prices):>15,} TL")
    print(f"  Ilce sayisi:   {len(districts)}")
    print(f"  Kayit sayisi:  {len(all_records)}")


if __name__ == "__main__":
    main()
