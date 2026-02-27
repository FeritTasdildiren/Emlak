"""
Emlak Teknoloji Platformu - Ilce Merkez Koordinatlari

Turkiye'nin buyuk sehirlerindeki ilcelerin yaklasik merkez koordinatlari.
Celery beat task'lari tarafindan AFAD deprem tehlike sorgusu ve
alan analiz yenilemesi icin kullanilir.

Koordinatlar:
    - WGS84 (SRID 4326) — (latitude, longitude) formati
    - Yaklasik ilce belediye bina/meydan konumlari
    - Google Maps / OSM kaynakli referans noktalar

Not:
    Bu modul statik veri icerir. Guncel/detayli polygon sinirlari icin
    TKGM CBS veya OSM Nominatim API kullanilmalidir.
"""

from __future__ import annotations

# ─── Tip Tanimi ────────────────────────────────────────────────────────
# (latitude, longitude) — WGS84
Coordinate = tuple[float, float]

# ─── Istanbul (39 ilce) — Buyuk ve orta olcekli ilceler ────────────────
_ISTANBUL: dict[str, Coordinate] = {
    "Kadıköy": (40.9927, 29.0230),
    "Beşiktaş": (41.0422, 29.0083),
    "Şişli": (41.0602, 28.9877),
    "Beyoğlu": (41.0370, 28.9770),
    "Fatih": (41.0186, 28.9397),
    "Üsküdar": (41.0240, 29.0154),
    "Bakırköy": (40.9808, 28.8772),
    "Ataşehir": (40.9833, 29.1167),
    "Maltepe": (40.9333, 29.1333),
    "Kartal": (40.8917, 29.1917),
    "Pendik": (40.8752, 29.2333),
    "Tuzla": (40.8167, 29.3000),
    "Ümraniye": (41.0167, 29.1167),
    "Beykoz": (41.1167, 29.1000),
    "Sarıyer": (41.1667, 29.0500),
    "Eyüpsultan": (41.0483, 28.9341),
    "Bayrampaşa": (41.0397, 28.9119),
    "Zeytinburnu": (41.0044, 28.9069),
    "Bahçelievler": (41.0000, 28.8597),
    "Bağcılar": (41.0369, 28.8572),
    "Güngören": (41.0197, 28.8858),
    "Esenler": (41.0425, 28.8767),
    "Başakşehir": (41.0917, 28.8000),
    "Küçükçekmece": (41.0000, 28.7833),
    "Avcılar": (40.9800, 28.7167),
    "Esenyurt": (41.0333, 28.6833),
    "Beylikdüzü": (41.0000, 28.6333),
    "Büyükçekmece": (41.0167, 28.5833),
    "Çatalca": (41.1500, 28.4500),
    "Silivri": (41.0833, 28.2500),
    "Sultangazi": (41.1000, 28.8667),
    "Gaziosmanpaşa": (41.0667, 28.9167),
    "Arnavutköy": (41.2000, 28.7333),
    "Sultanbeyli": (40.9667, 29.2667),
    "Sancaktepe": (41.0000, 29.2333),
    "Çekmeköy": (41.0333, 29.1833),
    "Şile": (41.1833, 29.6167),
    "Adalar": (40.8764, 29.0917),
}

# ─── Ankara (15+ ilce) ────────────────────────────────────────────────
_ANKARA: dict[str, Coordinate] = {
    "Çankaya": (39.9000, 32.8600),
    "Keçiören": (39.9833, 32.8667),
    "Yenimahalle": (39.9667, 32.8000),
    "Mamak": (39.9333, 32.9167),
    "Etimesgut": (39.9500, 32.6833),
    "Sincan": (39.9500, 32.5833),
    "Altındağ": (39.9500, 32.8667),
    "Pursaklar": (40.0333, 32.8833),
    "Gölbaşı": (39.7833, 32.8000),
    "Çubuk": (40.2333, 33.0333),
    "Kahramankazan": (40.2167, 32.6833),
    "Polatlı": (39.5833, 32.1500),
    "Beypazarı": (40.1667, 31.9167),
    "Elmadağ": (39.9167, 33.2333),
}

# ─── Izmir (15+ ilce) ─────────────────────────────────────────────────
_IZMIR: dict[str, Coordinate] = {
    "Konak": (38.4189, 27.1287),
    "Karşıyaka": (38.4561, 27.1114),
    "Bornova": (38.4667, 27.2167),
    "Buca": (38.3833, 27.1667),
    "Bayraklı": (38.4633, 27.1617),
    "Çiğli": (38.5000, 27.0667),
    "Gaziemir": (38.3167, 27.1333),
    "Karabağlar": (38.3833, 27.1167),
    "Narlıdere": (38.3833, 27.0333),
    "Balçova": (38.3833, 27.0500),
    "Menemen": (38.6000, 27.0667),
    "Torbalı": (38.1500, 27.3667),
    "Kemalpaşa": (38.4333, 27.4167),
    "Ödemiş": (38.2333, 27.9667),
    "Bergama": (39.1167, 27.1833),
    "Aliağa": (38.8000, 26.9667),
    "Urla": (38.3333, 26.7667),
    "Çeşme": (38.3167, 26.3000),
    "Seferihisar": (38.2000, 26.8333),
}

# ─── Bursa (8+ ilce) ──────────────────────────────────────────────────
_BURSA: dict[str, Coordinate] = {
    "Osmangazi": (40.1833, 29.0667),
    "Yıldırım": (40.1833, 29.1000),
    "Nilüfer": (40.2167, 28.9833),
    "Gemlik": (40.4333, 29.1500),
    "İnegöl": (40.0833, 29.5167),
    "Mudanya": (40.3833, 28.8833),
    "Gürsu": (40.2333, 29.1667),
    "Kestel": (40.2000, 29.2167),
}

# ─── Antalya (8+ ilce) ────────────────────────────────────────────────
_ANTALYA: dict[str, Coordinate] = {
    "Muratpaşa": (36.8841, 30.7056),
    "Konyaaltı": (36.8667, 30.6333),
    "Kepez": (36.9333, 30.7000),
    "Aksu": (36.9333, 30.8333),
    "Döşemealtı": (37.0667, 30.6000),
    "Alanya": (36.5500, 32.0000),
    "Manavgat": (36.7833, 31.4333),
    "Serik": (36.9167, 31.1000),
    "Kaş": (36.2000, 29.6500),
    "Kemer": (36.5833, 30.5500),
}

# ─── Sehir Haritasi ───────────────────────────────────────────────────
_CITY_REGISTRY: dict[str, dict[str, Coordinate]] = {
    "İstanbul": _ISTANBUL,
    "Ankara": _ANKARA,
    "İzmir": _IZMIR,
    "Bursa": _BURSA,
    "Antalya": _ANTALYA,
}

# Kucuk harfle normalize edilmis lookup tablosu
_NORMALIZED_REGISTRY: dict[str, dict[str, Coordinate]] = {}


def _build_normalized_registry() -> None:
    """Sehir ve ilce isimlerini kucuk harfle normalize ederek lookup hizlandir."""
    for city_name, districts in _CITY_REGISTRY.items():
        city_key = city_name.lower()
        _NORMALIZED_REGISTRY[city_key] = {
            district_name.lower(): coord
            for district_name, coord in districts.items()
        }


_build_normalized_registry()


def get_district_center(city: str, district: str) -> Coordinate | None:
    """
    Ilce merkez koordinatini dondur.

    Args:
        city: Sehir adi (buyuk/kucuk harf duyarsiz, orn: "istanbul", "İstanbul")
        district: Ilce adi (buyuk/kucuk harf duyarsiz, orn: "kadıköy", "Kadıköy")

    Returns:
        (latitude, longitude) tuple veya None (bulunamadiysa)

    Examples:
        >>> get_district_center("İstanbul", "Kadıköy")
        (40.9927, 29.0230)
        >>> get_district_center("istanbul", "kadıköy")
        (40.9927, 29.0230)
        >>> get_district_center("Trabzon", "Ortahisar")  # Desteklenmeyen sehir
        None
    """
    city_key = city.lower()
    district_key = district.lower()

    city_districts = _NORMALIZED_REGISTRY.get(city_key)
    if city_districts is None:
        return None

    return city_districts.get(district_key)


def get_all_districts() -> list[tuple[str, str, float, float]]:
    """
    Kayitli tum ilceleri listele.

    Returns:
        [(city, district, latitude, longitude), ...] listesi.
        Celery beat task'larinda "hangi ilceleri yenileyelim" sorusunun cevabi.

    Examples:
        >>> districts = get_all_districts()
        >>> len(districts) > 50
        True
        >>> districts[0]  # (city, district, lat, lon)
        ('İstanbul', 'Kadıköy', 40.9927, 29.023)
    """
    result: list[tuple[str, str, float, float]] = []
    for city_name, districts in _CITY_REGISTRY.items():
        for district_name, (lat, lon) in districts.items():
            result.append((city_name, district_name, lat, lon))
    return result
