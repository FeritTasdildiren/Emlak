"""
Emlak Teknoloji Platformu — Arama Kalitesi Testi (S4.9)

Typo/varyasyon listesiyle precision/recall olcumu.

Pure function unit testleri — DB bagimliligi YOK:
  1. normalize_turkish() — Turkce karakter donusumleri
  2. build_ts_query() — tsquery string uretimi
  3. _sanitize_input() — Girdi temizleme
  4. Arama kalitesi senaryolari — normalize + tsquery birlikte
"""

from __future__ import annotations

import pytest

from src.core.turkish import normalize_turkish
from src.modules.properties.search import _sanitize_input, build_ts_query

# ================================================================
# Test Veri Setleri
# ================================================================

# Kategori 1: Tam esleme normalize
EXACT_NORMALIZE = [
    ("Kadıköy", "kadikoy"),
    ("Ataşehir", "atasehir"),
    ("Üsküdar", "uskudar"),
    ("Şişli", "sisli"),
    ("Çekmeköy", "cekmekoy"),
    ("Güngören", "gungoren"),
    ("İstanbul", "istanbul"),
]

# Kategori 2: Diacritics-siz girdi (zaten ASCII)
DIACRITICLESS_INPUT = [
    ("kadikoy", "kadikoy"),
    ("uskudar", "uskudar"),
    ("sisli", "sisli"),
]

# Kategori 3: build_ts_query cikti dogrulama
#   (query, bos_olmamali)
QUERY_BUILD_CASES = [
    ("Kadıköy daire", True),
    ("kadikoy daire", True),
    ("3+1 daire", True),
    ("", False),
    ("xyz123abc", True),
]

# Kategori 4: Sanitize kontrolu
SANITIZE_CASES = [
    ("kadıköy'de daire", "kadıköy de daire"),
    ("test & deneme", "test deneme"),
    ("  çok   boşluk  ", "çok boşluk"),
    ("normal metin", "normal metin"),
]


# ================================================================
# 1. normalize_turkish() Unit Testleri
# ================================================================


class TestNormalizeTurkish:
    """Turkce karakter donusumleri ve edge case'ler."""

    @pytest.mark.parametrize("turkish,expected", EXACT_NORMALIZE)
    def test_exact_normalize(self, turkish: str, expected: str) -> None:
        """Turkce karakterli yer adi dogru ASCII formuna donusmeli."""
        assert normalize_turkish(turkish) == expected

    @pytest.mark.parametrize("ascii_input,expected", DIACRITICLESS_INPUT)
    def test_diacriticless_passthrough(self, ascii_input: str, expected: str) -> None:
        """Zaten ASCII olan girdi degismeden gecmeli."""
        assert normalize_turkish(ascii_input) == expected

    def test_empty_string(self) -> None:
        """Bos string bos donmeli."""
        assert normalize_turkish("") == ""

    def test_only_turkish_chars(self) -> None:
        """Sadece Turkce karakterlerden olusan string tamamen donusmeli."""
        assert normalize_turkish("ŞğüöçıİÜÖÇĞŞ") == "sguociiuocgs"

    def test_result_is_ascii(self) -> None:
        """Normalize sonucu tamamen ASCII olmali."""
        result = normalize_turkish("İstanbul'da Güneşli Günler Çekmeköy Şişli")
        assert result.isascii()

    def test_mixed_case_lowered(self) -> None:
        """Buyuk harfler kucuge donmeli."""
        assert normalize_turkish("DAIRE") == "daire"

    @pytest.mark.parametrize(
        "char,expected",
        [
            ("İ", "i"),
            ("I", "i"),
            ("ı", "i"),
            ("Ş", "s"),
            ("ş", "s"),
            ("Ğ", "g"),
            ("ğ", "g"),
            ("Ü", "u"),
            ("ü", "u"),
            ("Ö", "o"),
            ("ö", "o"),
            ("Ç", "c"),
            ("ç", "c"),
        ],
    )
    def test_individual_char_mapping(self, char: str, expected: str) -> None:
        """Her Turkce karakter dogru ASCII karsiligina donusmeli."""
        assert normalize_turkish(char) == expected


# ================================================================
# 2. _sanitize_input() Unit Testleri
# ================================================================


class TestSanitizeInput:
    """Girdi temizleme ve guvenlik kontrolleri."""

    @pytest.mark.parametrize("raw,expected", SANITIZE_CASES)
    def test_sanitize_cases(self, raw: str, expected: str) -> None:
        """Veri setindeki sanitize ciktilari beklenen degerle eslesmeli."""
        assert _sanitize_input(raw) == expected

    def test_removes_tsquery_operators(self) -> None:
        """tsquery ozel operatorleri (! & | < >) temizlenmeli."""
        result = _sanitize_input("daire & villa | arsa ! ofis")
        assert "&" not in result
        assert "|" not in result
        assert "!" not in result

    def test_removes_quotes(self) -> None:
        """Tek ve cift tirnak temizlenmeli."""
        result = _sanitize_input("""kadıköy'de "guzel" daire""")
        assert "'" not in result
        assert '"' not in result

    def test_collapses_multiple_spaces(self) -> None:
        """Birden fazla bosluk tek bosluga inmeli."""
        result = _sanitize_input("kadıköy   de    daire")
        assert "  " not in result
        assert result == "kadıköy de daire"

    def test_strips_leading_trailing(self) -> None:
        """Bas ve sondaki bosluklar temizlenmeli."""
        assert _sanitize_input("  daire  ") == "daire"

    def test_preserves_turkish_chars(self) -> None:
        """Turkce harfler korunmali (sanitize sadece operatorleri temizler)."""
        result = _sanitize_input("Şişli Güneşli Çekmeköy")
        assert "Şişli" in result
        assert "Güneşli" in result
        assert "Çekmeköy" in result

    def test_empty_input(self) -> None:
        """Bos girdi bos donmeli."""
        assert _sanitize_input("") == ""

    def test_sql_injection_operators_removed(self) -> None:
        """SQL injection icin kullanilabilecek tsquery operatorleri temizlenmeli."""
        result = _sanitize_input("'; DROP TABLE--")
        assert "'" not in result
        assert "-" not in result


# ================================================================
# 3. build_ts_query() Unit Testleri
# ================================================================


class TestBuildTsQuery:
    """tsquery string uretimi dogrulama."""

    @pytest.mark.parametrize("query,expects_non_empty", QUERY_BUILD_CASES)
    def test_query_build_cases(self, query: str, expects_non_empty: bool) -> None:
        """Veri setindeki sorgular icin bos/dolu beklentisi dogru olmali."""
        result = build_ts_query(query)
        if expects_non_empty:
            assert result, f"build_ts_query({query!r}) bos dondu, dolu bekleniyor"
        else:
            assert result == "", f"build_ts_query({query!r}) bos bekleniyor: {result!r}"

    def test_single_word_prefix_match(self) -> None:
        """Tek kelime prefix match (:*) ile bitmeli."""
        result = build_ts_query("daire")
        assert "daire:*" in result

    def test_multiple_words_and_operator(self) -> None:
        """Birden fazla kelime & operatoru ile birlestirilmeli."""
        result = build_ts_query("kadikoy daire")
        assert "&" in result
        assert "kadikoy:*" in result
        assert "daire:*" in result

    def test_turkish_chars_produce_or_branch(self) -> None:
        """Turkce karakterli sorgu OR (|) ile iki branch icermeli."""
        result = build_ts_query("Kadıköy")
        # Orijinal (kadıköy:*) ve ASCII (kadikoy:*) farkli → OR
        assert "|" in result
        assert "kadikoy:*" in result

    def test_ascii_only_no_or_branch(self) -> None:
        """ASCII-only sorgu OR branch icermemeli (tekrar yok)."""
        result = build_ts_query("kadikoy")
        assert "|" not in result

    def test_empty_returns_empty(self) -> None:
        """Bos string bos donmeli."""
        assert build_ts_query("") == ""

    def test_whitespace_returns_empty(self) -> None:
        """Sadece bosluk iceren sorgu bos donmeli."""
        assert build_ts_query("   ") == ""

    def test_only_operators_returns_empty(self) -> None:
        """Sadece tsquery operatorleri iceren girdi bos donmeli."""
        assert build_ts_query("! & | < >") == ""

    def test_all_words_have_prefix_match(self) -> None:
        """Her kelime :* ile bitmeli."""
        result = build_ts_query("kadikoy daire satilik")
        for word in ["kadikoy", "daire", "satilik"]:
            assert f"{word}:*" in result

    def test_special_chars_removed_from_terms(self) -> None:
        """Ozel karakterler tsquery terimlerinden temizlenmeli."""
        result = build_ts_query("3+1 daire! (kadıköy)")
        assert "!" not in result.replace(":*", "")
        assert "daire:*" in result


# ================================================================
# 4. Arama Kalitesi Senaryolari (normalize + tsquery birlikte)
# ================================================================


class TestSearchQualityScenarios:
    """build_ts_query + normalize_turkish entegrasyon senaryolari."""

    def test_kadikoy_daire_normalize_and_query(self) -> None:
        """'kadikoy daire' normalize + tsquery dogru uretmeli."""
        normalized = normalize_turkish("kadikoy daire")
        assert normalized == "kadikoy daire"
        ts = build_ts_query("kadikoy daire")
        assert "kadikoy:*" in ts
        assert "daire:*" in ts

    def test_uskudar_kiralik_normalize_and_query(self) -> None:
        """'uskudar kiralik' normalize + tsquery dogru uretmeli."""
        normalized = normalize_turkish("uskudar kiralik")
        assert normalized == "uskudar kiralik"
        ts = build_ts_query("uskudar kiralik")
        assert "uskudar:*" in ts
        assert "kiralik:*" in ts

    def test_turkish_kadikoy_daire_both_branches(self) -> None:
        """'Kadıköy daire' Turkce girdide hem orijinal hem ASCII branch olmali."""
        ts = build_ts_query("Kadıköy daire")
        assert ts  # bos olmamali
        assert "kadikoy:*" in ts  # ASCII branch
        assert "|" in ts  # OR branch var

    def test_sisli_satilik_normalize_and_query(self) -> None:
        """'Şişli satılık' normalize + tsquery dogru uretmeli."""
        normalized = normalize_turkish("Şişli satılık")
        assert normalized == "sisli satilik"
        ts = build_ts_query("Şişli satılık")
        assert "sisli:*" in ts
        assert "satilik:*" in ts

    @pytest.mark.parametrize(
        "typo_query",
        [
            "kadıköyde daire",
            "atasheir",
            "besiktas viila",
            "uskudr kiralik",
            "3+1 daier",
        ],
    )
    def test_typo_queries_produce_tsquery(self, typo_query: str) -> None:
        """Typo'lu sorgular tsquery olusturabilmeli (bos donmemeli)."""
        ts = build_ts_query(typo_query)
        assert ts, f"build_ts_query({typo_query!r}) bos dondu"

    @pytest.mark.parametrize(
        "turkish_input,expected_normalized",
        [
            ("Kadıköy'de daire", "kadikoy de daire"),
            ("Üsküdar kiralık", "uskudar kiralik"),
            ("Beşiktaş'ta villa", "besiktas ta villa"),
            ("Çekmeköy arsa", "cekmekoy arsa"),
        ],
    )
    def test_end_to_end_normalize_then_query(
        self, turkish_input: str, expected_normalized: str
    ) -> None:
        """Turkce girdi → sanitize → normalize → tsquery zinciri dogru calismali."""
        sanitized = _sanitize_input(turkish_input)
        normalized = normalize_turkish(sanitized)
        assert normalized == expected_normalized
        ts = build_ts_query(turkish_input)
        assert ts, f"Zincir sonucu tsquery bos: {turkish_input!r}"


# ================================================================
# Trigram Similarity Yardimcisi (Python-side pg_trgm simulasyonu)
# ================================================================


def _trigram_similarity(a: str, b: str) -> float:
    """Python-side trigram similarity (pg_trgm ile ayni mantik)."""

    def _trigrams(s: str) -> set[str]:
        padded = f"  {s} "
        return {padded[i : i + 3] for i in range(len(padded) - 2)}

    trgm_a = _trigrams(a)
    trgm_b = _trigrams(b)
    if not trgm_a or not trgm_b:
        return 0.0
    intersection = trgm_a & trgm_b
    union = trgm_a | trgm_b
    return len(intersection) / len(union) if union else 0.0


class TestTrigramSimulationSanity:
    """Typo toleransi icin trigram similarity esik kontrolu."""

    @pytest.mark.parametrize(
        "typo,correct",
        [
            ("kadıköyde", "kadikoy"),
            ("daier", "daire"),
            ("viila", "villa"),
            ("atasheir", "atasehir"),
            ("uskudr", "uskudar"),
        ],
    )
    def test_typo_similarity_above_threshold(self, typo: str, correct: str) -> None:
        """Typo'lu kelime normalize sonrasi dogru kelimeyle similarity > 0.1."""
        norm_typo = normalize_turkish(typo)
        norm_correct = normalize_turkish(correct)
        sim = _trigram_similarity(norm_typo, norm_correct)
        assert sim > 0.1, (
            f"similarity({norm_typo!r}, {norm_correct!r}) = {sim:.3f} — "
            f"cok dusuk, pg_trgm fallback yakalamayabilir"
        )


# ================================================================
# Kalite Metrik Raporu
# ================================================================


class TestQualityReport:
    """Tum kategorilerin basari oranlarini raporla."""

    def test_overall_quality_report(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Normalize + tsquery kalite metriklerini yazdir ve dogrula."""
        results: dict[str, tuple[int, int, int]] = {}

        # --- Exact normalize ---
        ok = sum(
            1
            for tr, exp in EXACT_NORMALIZE
            if normalize_turkish(tr) == exp
        )
        results["Tam Esleme"] = (ok, len(EXACT_NORMALIZE), 100)

        # --- Diacriticless ---
        ok = sum(
            1
            for inp, exp in DIACRITICLESS_INPUT
            if normalize_turkish(inp) == exp
        )
        results["Diacritics-siz"] = (ok, len(DIACRITICLESS_INPUT), 100)

        # --- Query build ---
        ok = sum(
            1
            for q, expects in QUERY_BUILD_CASES
            if bool(build_ts_query(q)) == expects
        )
        results["tsquery Uretim"] = (ok, len(QUERY_BUILD_CASES), 100)

        # --- Sanitize ---
        ok = sum(
            1
            for raw, exp in SANITIZE_CASES
            if _sanitize_input(raw) == exp
        )
        results["Sanitize"] = (ok, len(SANITIZE_CASES), 100)

        lines = ["\n=== ARAMA KALITESI RAPORU ==="]
        all_pass = True
        for name, (success, total, threshold) in results.items():
            rate = success / total * 100 if total else 100
            status = "PASS" if rate >= threshold else "FAIL"
            lines.append(
                f"  [{status}] {name}: {success}/{total} "
                f"({rate:.0f}%, hedef >={threshold}%)"
            )
            if rate < threshold:
                all_pass = False
        lines.append("=" * 40)

        report = "\n".join(lines)
        print(report)
        assert all_pass, f"Kalite esigi karsilanmayan kategori var:\n{report}"
