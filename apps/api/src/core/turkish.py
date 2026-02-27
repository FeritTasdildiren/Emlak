"""Turkce metin normalizasyon yardimcilari.

Iki farkli normalizasyon stratejisi sunar:

1. normalize_turkish() — Arama icin: Tum Turkce karakterleri ASCII karsiliklarina
   donusturur. "Kadıköy" → "kadikoy". DB'deki turkish_normalize() ile ayni mantik.

2. turkish_lower() — Goruntuleme icin: Turkce-aware lowercase. I→ı, İ→i.
   Python'un str.lower() fonksiyonu Turkce I/İ donusumunu YANLIS yapar.
"""

# Arama normalizasyon tablosu: Turkce → ASCII
# DB'deki turkish_normalize() fonksiyonu ile AYNI donusum mantigi.
# Degisiklik yapilirsa migration'daki fonksiyon da guncellenmelidir.
_TR_NORMALIZE_TABLE = str.maketrans({
    "İ": "i", "I": "i",   # Buyuk I/İ → kucuk i (arama icin ayni)
    "Ş": "s", "ş": "s",
    "Ğ": "g", "ğ": "g",
    "Ü": "u", "ü": "u",
    "Ö": "o", "ö": "o",
    "Ç": "c", "ç": "c",
    "ı": "i",              # Kucuk ı → i
})


def normalize_turkish(text: str) -> str:
    """Turkce metni ASCII-safe kucuk harfe donusturur. Arama icin kullanilir.

    DB'deki turkish_normalize() SQL fonksiyonu ile ayni sonucu uretir.
    Bu eslesme kritiktir — indeks kullanimi icin Python ve SQL tarafinin
    ayni normalizasyonu uygulamasi gerekir.
    """
    return text.translate(_TR_NORMALIZE_TABLE).lower()


def turkish_lower(text: str) -> str:
    """Turkce-aware lowercase: İ→i, I→ı (dogru Turkce kucultme).

    Python'un str.lower() fonksiyonu:
    - 'I'.lower() → 'i' (YANLIS, Turkce'de 'ı' olmali)
    - 'İ'.lower() → 'i̇' (YANLIS, combining dot above ekler)

    Bu fonksiyon dogru Turkce lowercase yapar.
    """
    result = text.replace("İ", "i").replace("I", "ı")
    return result.lower()
