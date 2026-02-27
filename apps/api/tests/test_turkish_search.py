"""
Emlak Teknoloji Platformu — Turkish Lowercasing / Normalization Test Suite

Turkce'nin ozel harflerinin (İ→i, I→ı, Ş→ş, Ğ→ğ, Ü→ü, Ö→ö, Ç→ç)
hem Python hem SQL tarafinda tutarli normalize edildigini dogrulamak icin
kapsamli test seti.

Test Katmanlari:
    1) Python Unit Tests — turkish.py (normalize_turkish, turkish_lower)
    2) SQL Fonksiyon Tests — migration 013 (turkish_normalize, immutable_unaccent)
    3) Python↔SQL Tutarlilik — ayni girdi, ayni cikti
    4) Edge Case / Typo Tests — kullanici arama varyasyonlari

Referanslar:
    - src/core/turkish.py: normalize_turkish(), turkish_lower()
    - Migration 013: turkish_normalize() SQL, immutable_unaccent() SQL
    - S4.6 (TASK-070): Turkce arama altyapisi
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from src.core.turkish import normalize_turkish, turkish_lower

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ================================================================
# Katman 1: Python Unit Tests — normalize_turkish()
# ================================================================
class TestNormalizeTurkish:
    """normalize_turkish(): Turkce → ASCII lowercase donusumu."""

    def test_istanbul_upper(self):
        """İSTANBUL → istanbul (İ→i, buyuk harfler kucultulur)."""
        assert normalize_turkish("İSTANBUL") == "istanbul"

    def test_sisli(self):
        """Şişli → sisli (Ş→s, ş→s, ı→i)."""
        assert normalize_turkish("Şişli") == "sisli"

    def test_guneslibahce(self):
        """GÜNEŞLIBAHÇE → guneslibahce (Ü→u, Ş→s, I→i, Ç→c)."""
        assert normalize_turkish("GÜNEŞLIBAHÇE") == "guneslibahce"

    def test_camlica(self):
        """Çamlıca → camlica (Ç→c, ı→i)."""
        assert normalize_turkish("Çamlıca") == "camlica"

    def test_empty_string(self):
        """Bos string → bos string."""
        assert normalize_turkish("") == ""

    def test_already_ascii(self):
        """Zaten ASCII olan metin degismemeli."""
        assert normalize_turkish("kadikoy") == "kadikoy"

    def test_mixed_turkish_ascii(self):
        """Karisik Turkce ve ASCII karakterler."""
        assert normalize_turkish("Türkiye Cumhuriyeti") == "turkiye cumhuriyeti"

    def test_all_special_chars(self):
        """Tum Turkce ozel karakterlerin donusumu."""
        assert normalize_turkish("İışŞğĞüÜöÖçÇ") == "iissgguuoocc"

    def test_numbers_preserved(self):
        """Rakamlar korunmali."""
        assert normalize_turkish("3+1 Şişli") == "3+1 sisli"


# ================================================================
# Katman 1: Python Unit Tests — turkish_lower()
# ================================================================
class TestTurkishLower:
    """turkish_lower(): Turkce-aware lowercase (goruntuleme icin)."""

    def test_istanbul_dotted_i_upper(self):
        """İSTANBUL → istanbul (İ→i dogru donusum)."""
        assert turkish_lower("İSTANBUL") == "istanbul"

    def test_isparta_dotless_i_upper(self):
        """ISPARTA → ısparta (I→ı dogru Turkce donusum)."""
        assert turkish_lower("ISPARTA") == "ısparta"

    def test_ispartali(self):
        """ISPARTALI → ıspartalı (I→ı, tum buyuk harfler kucultulur)."""
        result = turkish_lower("ISPARTALI")
        assert result == "ıspartalı"

    def test_irak(self):
        """Irak → ırak (I→ı, bastan)."""
        assert turkish_lower("Irak") == "ırak"

    def test_izmir(self):
        """İzmir → izmir (İ→i, bastan)."""
        assert turkish_lower("İzmir") == "izmir"

    def test_mixed_i_variants(self):
        """İSTANBUL ve ISPARTA → istanbul ve ısparta (karisik İ/I)."""
        assert turkish_lower("İSTANBUL ve ISPARTA") == "istanbul ve ısparta"

    def test_lowercase_passthrough(self):
        """Zaten kucuk harf ise degismemeli."""
        assert turkish_lower("istanbul") == "istanbul"

    def test_empty_string(self):
        """Bos string → bos string."""
        assert turkish_lower("") == ""


# ================================================================
# Katman 2: SQL Fonksiyon Tests — turkish_normalize()
# ================================================================
class TestSQLTurkishNormalize:
    """DB'deki turkish_normalize() SQL fonksiyonunu dogrudan test eder."""

    async def test_istanbul(self, db_session: AsyncSession):
        """SQL: turkish_normalize('İSTANBUL') = 'istanbul'."""
        result = await db_session.execute(
            text("SELECT turkish_normalize('İSTANBUL')")
        )
        assert result.scalar() == "istanbul"

    async def test_sisli(self, db_session: AsyncSession):
        """SQL: turkish_normalize('Şişli') = 'sisli'."""
        result = await db_session.execute(
            text("SELECT turkish_normalize('Şişli')")
        )
        assert result.scalar() == "sisli"

    async def test_guneslibahce(self, db_session: AsyncSession):
        """SQL: turkish_normalize('GÜNEŞLIBAHÇE') = 'guneslibahce'."""
        result = await db_session.execute(
            text("SELECT turkish_normalize('GÜNEŞLIBAHÇE')")
        )
        assert result.scalar() == "guneslibahce"

    async def test_camlica(self, db_session: AsyncSession):
        """SQL: turkish_normalize('Çamlıca') = 'camlica'."""
        result = await db_session.execute(
            text("SELECT turkish_normalize('Çamlıca')")
        )
        assert result.scalar() == "camlica"

    async def test_empty_string(self, db_session: AsyncSession):
        """SQL: turkish_normalize('') = ''."""
        result = await db_session.execute(
            text("SELECT turkish_normalize('')")
        )
        assert result.scalar() == ""

    async def test_already_ascii(self, db_session: AsyncSession):
        """SQL: Zaten ASCII olan metin degismemeli."""
        result = await db_session.execute(
            text("SELECT turkish_normalize('kadikoy')")
        )
        assert result.scalar() == "kadikoy"


# ================================================================
# Katman 2: SQL Fonksiyon Tests — immutable_unaccent()
# ================================================================
class TestSQLImmutableUnaccent:
    """DB'deki immutable_unaccent() SQL fonksiyonunu test eder."""

    async def test_kadikoy(self, db_session: AsyncSession):
        """SQL: immutable_unaccent('Kadıköy') = 'Kadikoy'."""
        result = await db_session.execute(
            text("SELECT immutable_unaccent('Kadıköy')")
        )
        assert result.scalar() == "Kadikoy"

    async def test_umraniye(self, db_session: AsyncSession):
        """SQL: immutable_unaccent('Ümraniye') = 'Umraniye'."""
        result = await db_session.execute(
            text("SELECT immutable_unaccent('Ümraniye')")
        )
        assert result.scalar() == "Umraniye"

    async def test_beyoglu(self, db_session: AsyncSession):
        """SQL: immutable_unaccent('Beyoğlu') — ğ kaldirmasi."""
        result = await db_session.execute(
            text("SELECT immutable_unaccent('Beyoğlu')")
        )
        assert result.scalar() == "Beyoglu"

    async def test_atasehir(self, db_session: AsyncSession):
        """SQL: immutable_unaccent('Ataşehir') = 'Atasehir'."""
        result = await db_session.execute(
            text("SELECT immutable_unaccent('Ataşehir')")
        )
        assert result.scalar() == "Atasehir"


# ================================================================
# Katman 3: Python↔SQL Tutarlilik Tests
# ================================================================
# Her ilce icin Python normalize_turkish() ve SQL turkish_normalize()
# ayni ciktiyi vermelidir. Bu kritiktir — expression indeks kullanimi
# icin Python sorgusunun SQL indeksiyle ayni normalizasyonu yapmasi gerekir.

CONSISTENCY_TEST_INPUTS = [
    "İstanbul",
    "Kadıköy",
    "Üsküdar",
    "Şişli",
    "Beyoğlu",
    "Çekmeköy",
    "Güngören",
    "Ataşehir",
    "Bakırköy",
    "Sarıyer",
]


class TestPythonSQLConsistency:
    """Python normalize_turkish() ve SQL turkish_normalize() tutarliligi."""

    @pytest.mark.parametrize("district", CONSISTENCY_TEST_INPUTS)
    async def test_python_sql_match(
        self, db_session: AsyncSession, district: str
    ):
        """Python ve SQL ayni girdi icin ayni ciktiyi uretmeli."""
        python_result = normalize_turkish(district)

        sql_result = await db_session.execute(
            text("SELECT turkish_normalize(:input)"),
            {"input": district},
        )
        sql_value = sql_result.scalar()

        assert python_result == sql_value, (
            f"Tutarsizlik: '{district}' → "
            f"Python='{python_result}', SQL='{sql_value}'"
        )


# ================================================================
# Katman 4: Edge Case / Typo Tests — kullanici arama varyasyonlari
# ================================================================
# Kullanicilar Turkce diacritics'siz veya yarim diacritics ile
# arama yapar. normalize_turkish() her iki taraftaki girdiyi
# ayni ASCII formuna indirerek eslestirme saglar.

SEARCH_MATCH_CASES = [
    # (kullanici_aramasi, veritabani_degeri, aciklama)
    ("kadikoy", "Kadıköy", "diacriticsiz arama"),
    ("istanbul", "İstanbul", "I/İ farksiz arama"),
    ("sisli", "Şişli", "S/Ş ve s/ş farksiz arama"),
    ("cekmeköy", "Çekmeköy", "yarim diacritics — c yerine Ç ama ö korunmus"),
    ("beyoglu", "Beyoğlu", "ğ olmadan arama"),
    ("uskudar", "Üsküdar", "Ü/ü olmadan arama"),
    ("bakirkoy", "Bakırköy", "ı ve ö olmadan arama"),
    ("gungoren", "Güngören", "ü ve ö olmadan arama"),
]


class TestSearchMatchEdgeCases:
    """Kullanici arama varyasyonlari: normalize sonrasi eslesmeli."""

    @pytest.mark.parametrize(
        ("user_query", "db_value", "description"), SEARCH_MATCH_CASES
    )
    def test_normalized_match_python(
        self, user_query: str, db_value: str, description: str
    ):
        """Python: normalize(arama) == normalize(DB degeri) → eslesme."""
        assert normalize_turkish(user_query) == normalize_turkish(db_value), (
            f"Eslesmedi ({description}): "
            f"normalize('{user_query}')='{normalize_turkish(user_query)}', "
            f"normalize('{db_value}')='{normalize_turkish(db_value)}'"
        )

    @pytest.mark.parametrize(
        ("user_query", "db_value", "description"), SEARCH_MATCH_CASES
    )
    async def test_normalized_match_sql(
        self,
        db_session: AsyncSession,
        user_query: str,
        db_value: str,
        description: str,
    ):
        """SQL: turkish_normalize(arama) == turkish_normalize(DB degeri) → eslesme."""
        result = await db_session.execute(
            text(
                "SELECT turkish_normalize(:query) = turkish_normalize(:value)"
            ),
            {"query": user_query, "value": db_value},
        )
        assert result.scalar() is True, (
            f"SQL eslesmedi ({description}): "
            f"turkish_normalize('{user_query}') != "
            f"turkish_normalize('{db_value}')"
        )
