"""
Emlak Teknoloji Platformu — Property Full-Text Search

PostgreSQL FTS + pg_trgm ile Turkce arama destegi.

Strateji (hibrit, 3 katmanli):
  1. FTS (to_tsquery + ts_rank_cd) — tam kelime eslesmesi, weight'li skorlama
  2. pg_trgm (similarity) — fuzzy / bulanik esleme (yazim hatasi toleransi)
  3. ILIKE substring — son care, basit icerir (contains) aramasi

Turkce Normalizasyon (migration 013 ile eklendi):
  - 'turkish' ts_config: simple'dan kopyalanmis custom config
  - turkish_normalize() SQL fonksiyonu: I->i, I->i, S->s, G->g, U->u, O->o, C->c
  - idx_properties_turkish_search: normalized text uzerinde trigram GIN indeksi
  - Python tarafi: src.core.turkish.normalize_turkish() (ayni donusum mantigi)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy import Select, func, literal_column, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.core.turkish import normalize_turkish
from src.models.property import Property

# ---------- Sabitler ----------

#: Minimum pg_trgm similarity esigi.
#: 0.3 = PostgreSQL default. Turkce icin biraz dusuruldu (diacritic farklari).
DEFAULT_SIMILARITY_THRESHOLD: float = 0.2

#: Varsayilan sayfa boyutu
DEFAULT_LIMIT: int = 20

#: Maksimum sayfa boyutu (abuse onleme)
MAX_LIMIT: int = 100

#: FTS minimum sonuc esigi — bunun altinda trgm fallback devreye girer
FTS_MIN_RESULTS_FOR_FALLBACK: int = 3

#: Gecerli siralama secenekleri
VALID_SORT_OPTIONS: set[str] = {"relevance", "price_asc", "price_desc", "newest", "area"}


# ---------- Turkce Normalizasyon ----------
# Merkezi utility: src.core.turkish.normalize_turkish()
# DB fonksiyonu: turkish_normalize() (migration 013)

_normalize_turkish = normalize_turkish  # Geriye donuk uyumluluk (modul ici kullanim)


def _sanitize_input(query: str) -> str:
    """
    Kullanici girdisini temizle ve SQL injection'a karsi koru.

    - Ozel tsquery operatorlerini kaldir (!, &, |, <->)
    - Tek tirnaklari kaldir
    - Fazla bosluklari tek bosluga indirge
    - Strip
    """
    # tsquery ozel karakterleri temizle
    cleaned = re.sub(r"[!&|<>\-():*'\"\\]", " ", query)
    # Birden fazla boslugu teke indir
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


# ---------- tsquery Builder ----------

def build_ts_query(query: str, config: str = "simple") -> str:
    """
    Kullanici arama metnini PostgreSQL plainto_tsquery uyumlu formata cevir.

    Strateji:
      - Her kelimeyi prefix match yaparak ara (kelime:*)
      - Kelimeler arasinda AND (&) operatoru kullan
      - Hem orijinal hem ASCII-normalized versiyonu OR ile birlestir

    Ornek:
      "3+1 daire kadikoy"
      -> "(3:* & 1:* & daire:* & kadikoy:*) | (3:* & 1:* & daire:* & kadikoy:*)"

    NOT: Bu fonksiyon ham string dondurur. Sorguya to_tsquery() ile verilir.
    SQL injection korumasini _sanitize_input() saglar.
    """
    sanitized = _sanitize_input(query)
    if not sanitized:
        return ""

    words = sanitized.lower().split()
    if not words:
        return ""

    # Orijinal kelimelerle tsquery
    original_parts = [f"{w}:*" for w in words]
    original_query = " & ".join(original_parts)

    # ASCII-normalized versiyonu
    ascii_words = _normalize_turkish(sanitized).lower().split()
    ascii_parts = [f"{w}:*" for w in ascii_words]
    ascii_query = " & ".join(ascii_parts)

    # Eger orijinal ve ASCII ayni ise tekrarlamaya gerek yok
    if original_query == ascii_query:
        return original_query

    # OR ile birlestir — iki turlu de eslesmis olsun
    return f"({original_query}) | ({ascii_query})"


# ---------- Ortak Filtre + Siralama ----------

def _apply_filters(
    stmt: Select,
    *,
    city: str | None = None,
    district: str | None = None,
    listing_type: str | None = None,
    property_type: str | None = None,
    status: str = "active",
    min_price: int | None = None,
    max_price: int | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
) -> Select:
    """Ortak filtreleri SELECT ifadesine uygula."""
    stmt = stmt.where(Property.status == status)

    if city is not None:
        stmt = stmt.where(func.lower(Property.city) == city.lower())
    if district is not None:
        stmt = stmt.where(func.lower(Property.district) == district.lower())
    if listing_type is not None:
        stmt = stmt.where(Property.listing_type == listing_type)
    if property_type is not None:
        stmt = stmt.where(Property.property_type == property_type)
    if min_price is not None:
        stmt = stmt.where(Property.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Property.price <= max_price)
    if min_area is not None:
        stmt = stmt.where(Property.net_area >= min_area)
    if max_area is not None:
        stmt = stmt.where(Property.net_area <= max_area)

    return stmt


def _apply_sort(stmt: Select, sort: str, *, has_rank: bool = False) -> Select:
    """Siralama secenegini SELECT ifadesine uygula."""
    if sort == "price_asc":
        return stmt.order_by(Property.price.asc())
    if sort == "price_desc":
        return stmt.order_by(Property.price.desc())
    if sort == "newest":
        return stmt.order_by(Property.created_at.desc())
    if sort == "area":
        return stmt.order_by(Property.net_area.desc().nulls_last())
    # "relevance" — FTS rank varsa zaten uygulanmis, yoksa newest'a dussun
    if not has_rank:
        return stmt.order_by(Property.created_at.desc())
    return stmt


# ---------- FTS Search ----------

async def search_properties(
    session: AsyncSession,
    query: str | None = None,
    *,
    city: str | None = None,
    district: str | None = None,
    listing_type: str | None = None,
    property_type: str | None = None,
    status: str = "active",
    min_price: int | None = None,
    max_price: int | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    sort: str = "relevance",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> tuple[list[Property], int]:
    """
    Hibrit property arama — FTS + trigram + ILIKE fallback.

    query bos/None ise sadece filtreler uygulanir (FTS bypass).

    Hibrit strateji (query varsa):
      1. Once ts_query ile FTS arama (search_vector uzerinde)
      2. Sonuc FTS_MIN_RESULTS_FOR_FALLBACK altindaysa pg_trgm fallback
      3. Trigram da sonuc vermezse ILIKE substring fallback

    Args:
        session: AsyncSession (SQLAlchemy)
        query: Kullanici arama metni (orn: "3+1 daire kadikoy"), None ise FTS bypass
        city: Il filtresi (opsiyonel)
        district: Ilce filtresi (opsiyonel)
        listing_type: Ilan tipi filtresi: sale, rent (opsiyonel)
        property_type: Emlak tipi filtresi: daire, villa, arsa (opsiyonel)
        status: Ilan durumu filtresi (default: "active")
        min_price: Minimum fiyat filtresi (opsiyonel)
        max_price: Maksimum fiyat filtresi (opsiyonel)
        min_area: Minimum net alan filtresi (opsiyonel)
        max_area: Maksimum net alan filtresi (opsiyonel)
        sort: Siralama: relevance, price_asc, price_desc, newest, area
        limit: Sayfa boyutu (max 100)
        offset: Sayfa offseti

    Returns:
        (properties, total_count) tuple
    """
    # Girdi dogrulama
    limit = min(max(1, limit), MAX_LIMIT)
    offset = max(0, offset)
    if sort not in VALID_SORT_OPTIONS:
        sort = "relevance"

    filter_kwargs = {
        "city": city,
        "district": district,
        "listing_type": listing_type,
        "property_type": property_type,
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
        "min_area": min_area,
        "max_area": max_area,
    }

    # --- query yoksa: sadece filtre + siralama ---
    if not query or not query.strip():
        return await _filter_only_search(
            session, sort=sort, limit=limit, offset=offset, **filter_kwargs
        )

    ts_query_str = build_ts_query(query)
    if not ts_query_str:
        return await _filter_only_search(
            session, sort=sort, limit=limit, offset=offset, **filter_kwargs
        )

    # ---- 1. FTS sorgulama ----
    fts_results, fts_count = await _fts_search(
        session, ts_query_str, sort=sort, limit=limit, offset=offset, **filter_kwargs
    )

    if fts_count >= FTS_MIN_RESULTS_FOR_FALLBACK:
        return fts_results, fts_count

    # ---- 2. Trigram fallback ----
    trgm_results, trgm_count = await search_properties_by_similarity(
        session, query, sort=sort, limit=limit, offset=offset, **filter_kwargs
    )

    if trgm_count > fts_count:
        return trgm_results, trgm_count

    # ---- 3. ILIKE fallback (son care) ----
    if fts_count == 0 and trgm_count == 0:
        ilike_results, ilike_count = await _ilike_search(
            session, query, sort=sort, limit=limit, offset=offset, **filter_kwargs
        )
        if ilike_count > 0:
            return ilike_results, ilike_count

    # FTS sonuclari (en az bir sonuc var ama threshold altinda)
    return fts_results, fts_count


async def _filter_only_search(
    session: AsyncSession,
    *,
    sort: str = "relevance",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    **filter_kwargs: str | int | float | None,
) -> tuple[list[Property], int]:
    """Query olmadan sadece filtre + siralama ile listeleme."""
    stmt = select(Property)
    stmt = _apply_filters(stmt, **filter_kwargs)
    stmt = _apply_sort(stmt, sort, has_rank=False)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total_count = total_result.scalar_one()

    paginated = stmt.offset(offset).limit(limit)
    result = await session.execute(paginated)
    properties = list(result.scalars().all())

    return properties, total_count


async def _fts_search(
    session: AsyncSession,
    ts_query_str: str,
    *,
    sort: str = "relevance",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    **filter_kwargs: str | int | float | None,
) -> tuple[list[Property], int]:
    """FTS (full-text search) ile arama."""
    ts_query = func.to_tsquery("simple", literal_column(f"'{ts_query_str}'"))

    rank_expr = func.ts_rank_cd(
        Property.search_vector, ts_query, 32
    ).label("fts_rank")

    stmt = (
        select(Property)
        .where(Property.search_vector.op("@@")(ts_query))
    )
    stmt = _apply_filters(stmt, **filter_kwargs)

    if sort == "relevance":
        stmt = stmt.order_by(rank_expr.desc())
    else:
        stmt = _apply_sort(stmt, sort, has_rank=True)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total_count = total_result.scalar_one()

    paginated = stmt.offset(offset).limit(limit)
    result = await session.execute(paginated)
    properties = list(result.scalars().all())

    return properties, total_count


def _build_fts_query(
    ts_query_str: str,
    *,
    city: str | None = None,
    district: str | None = None,
    listing_type: str | None = None,
    property_type: str | None = None,
    status: str = "active",
) -> Select:
    """
    FTS icin SQLAlchemy SELECT ifadesi olustur (geriye donuk uyumluluk).

    ts_rank_cd kullanir (cover density ranking):
    - Eslesenler arasinda konum yakinligini da dikkate alir
    - ts_rank'ten daha dogru siralama (biraz daha yavas, MVP'de OK)
    """
    ts_query = func.to_tsquery("simple", literal_column(f"'{ts_query_str}'"))

    stmt = (
        select(Property)
        .where(
            Property.search_vector.op("@@")(ts_query),
            Property.status == status,
        )
        .order_by(
            func.ts_rank_cd(
                Property.search_vector,
                ts_query,
                32,  # normalization: rank / (rank + 1) — skor 0-1 arasi
            ).desc()
        )
    )

    # Opsiyonel filtreler
    if city is not None:
        stmt = stmt.where(func.lower(Property.city) == city.lower())
    if district is not None:
        stmt = stmt.where(func.lower(Property.district) == district.lower())
    if listing_type is not None:
        stmt = stmt.where(Property.listing_type == listing_type)
    if property_type is not None:
        stmt = stmt.where(Property.property_type == property_type)

    return stmt


# ---------- Similarity (pg_trgm) Search ----------

async def search_properties_by_similarity(
    session: AsyncSession,
    query: str,
    *,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    city: str | None = None,
    district: str | None = None,
    listing_type: str | None = None,
    property_type: str | None = None,
    status: str = "active",
    min_price: int | None = None,
    max_price: int | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    sort: str = "relevance",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> tuple[list[Property], int]:
    """
    pg_trgm similarity ile fuzzy arama.

    Kullanim alanlari:
      - FTS sonuc vermediginde fallback
      - Yazim hatali aramalarda (orn: "kadikoy" -> "Kadikoy")
      - Kismi kelime eslemesi (orn: "villa" -> "villalari")

    Strateji:
      - similarity(title, query) + similarity(description, query) toplam skor
      - Skor threshold'un uzerindeyse sonuca dahil
      - Title similarity'si 2x agirlikli (daha onemli)

    Args:
        session: AsyncSession
        query: Kullanici arama metni
        threshold: Minimum similarity skoru (0.0 - 1.0)
        city: Il filtresi (opsiyonel)
        district: Ilce filtresi (opsiyonel)
        listing_type: Ilan tipi filtresi (opsiyonel)
        property_type: Emlak tipi filtresi (opsiyonel)
        status: Ilan durumu filtresi (default: "active")
        min_price: Minimum fiyat filtresi (opsiyonel)
        max_price: Maksimum fiyat filtresi (opsiyonel)
        min_area: Minimum net alan filtresi (opsiyonel)
        max_area: Maksimum net alan filtresi (opsiyonel)
        sort: Siralama secenegi
        limit: Maksimum sonuc sayisi
        offset: Sayfa offseti

    Returns:
        (properties, total_count) tuple
    """
    limit = min(max(1, limit), MAX_LIMIT)
    offset = max(0, offset)

    sanitized = _sanitize_input(query)
    if not sanitized:
        return [], 0

    # Normalize: hem Python hem SQL tarafinda ayni donusum
    normalized_query = normalize_turkish(sanitized)

    # turkish_normalize() SQL fonksiyonu ile DB tarafinda da normalize et
    # Bu sayede idx_properties_turkish_search indeksi kullanilir
    normalized_title = func.turkish_normalize(Property.title)
    normalized_desc = func.turkish_normalize(func.coalesce(Property.description, ""))

    # similarity() fonksiyonu — pg_trgm'den gelir
    # Normalized text uzerinde karsilastirma yapilir
    title_sim = func.similarity(normalized_title, normalized_query)
    desc_sim = func.coalesce(
        func.similarity(normalized_desc, normalized_query), 0.0
    )

    # Title 2x agirlikli, description 1x
    combined_score = (title_sim * 2 + desc_sim).label("relevance_score")

    stmt = (
        select(Property)
        .where(
            # En az birinin threshold'u gecmesi gerekir
            (title_sim >= threshold) | (desc_sim >= threshold),
        )
    )

    filter_kwargs = {
        "city": city,
        "district": district,
        "listing_type": listing_type,
        "property_type": property_type,
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
        "min_area": min_area,
        "max_area": max_area,
    }
    stmt = _apply_filters(stmt, **filter_kwargs)

    if sort == "relevance":
        stmt = stmt.order_by(combined_score.desc())
    else:
        stmt = _apply_sort(stmt, sort, has_rank=True)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total_count = total_result.scalar_one()

    # Results (paginated)
    paginated_stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(paginated_stmt)
    properties = list(result.scalars().all())

    return properties, total_count


# ---------- ILIKE Fallback ----------

async def _ilike_search(
    session: AsyncSession,
    query: str,
    *,
    sort: str = "relevance",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    **filter_kwargs: str | int | float | None,
) -> tuple[list[Property], int]:
    """
    ILIKE substring arama — son care fallback.

    FTS ve trigram sonuc vermediginde basit icerir (contains) aramasi yapar.
    turkish_normalize() ile normalize edilmis metin uzerinde calisir.
    """
    sanitized = _sanitize_input(query)
    if not sanitized:
        return [], 0

    normalized_query = normalize_turkish(sanitized)
    pattern = f"%{normalized_query}%"

    normalized_title = func.turkish_normalize(Property.title)
    normalized_desc = func.turkish_normalize(func.coalesce(Property.description, ""))

    stmt = (
        select(Property)
        .where(
            normalized_title.ilike(pattern) | normalized_desc.ilike(pattern),
        )
    )
    stmt = _apply_filters(stmt, **filter_kwargs)
    stmt = _apply_sort(stmt, sort, has_rank=False)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total_count = total_result.scalar_one()

    paginated = stmt.offset(offset).limit(limit)
    result = await session.execute(paginated)
    properties = list(result.scalars().all())

    return properties, total_count


# ---------- Utility ----------

async def search_suggestions(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 5,
) -> list[str]:
    """
    Autocomplete oneriler icin title'lardan aday listesi don.

    Kullanim: Arama kutusundaki onyazi (typeahead) ozelligi.
    pg_trgm LIKE ile calisiyor (trigram indeks kullanir).

    Args:
        session: AsyncSession
        query: Kullanicinin o ana kadar yazdigi metin
        limit: Oneri sayisi (default 5)

    Returns:
        Title listesi (distinct, en fazla `limit` adet)
    """
    sanitized = _sanitize_input(query)
    if not sanitized or len(sanitized) < 2:
        return []

    # Normalize ederek ara — "kadikoy" ile "Kadikoy" eslesir
    normalized_query = normalize_turkish(sanitized)
    pattern = f"%{normalized_query}%"

    # turkish_normalize() ile normalize edilmis title uzerinde LIKE
    normalized_title = func.turkish_normalize(Property.title)

    stmt = (
        select(Property.title)
        .where(
            normalized_title.ilike(pattern),
            Property.status == "active",
        )
        .distinct()
        .order_by(func.similarity(normalized_title, normalized_query).desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    return [row[0] for row in result.fetchall()]
