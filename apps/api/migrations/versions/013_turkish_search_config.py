"""turkish_search_config

Revision ID: 013_turkish_search_config
Revises: 012_model_registry_prediction_logs
Create Date: 2026-02-21

Turkce arama altyapisi:
1. pg_trgm + unaccent extension garanti (init.sql zaten ekliyor, migration chain'de de olmali)
2. 'turkish' TEXT SEARCH CONFIGURATION (simple'dan kopyalanir)
3. turkish_normalize() fonksiyonu — Turkce karakter → ASCII (IMMUTABLE, index'te kullanilabilir)
4. immutable_unaccent() wrapper — unaccent'in IMMUTABLE versiyonu (index'te kullanilabilir)
5. idx_properties_turkish_search — normalized text uzerinde trigram GIN indeksi

NOT: PostgreSQL'de yerlesik 'turkish' ts_config yoktur.
Custom konfigürasyon 'simple' uzerine kurulur (stemming yok, tokenize + lowercase).
turkish_normalize() ile Turkce ozel karakter donusumu saglanir:
  İ→i, I→ı→i, Ş→s, Ğ→g, Ü→u, Ö→o, Ç→c
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013_turkish_search_config"
down_revision: Union[str, None] = "012_model_registry_prediction_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. Extension'lari garanti et
    #    init.sql zaten ekliyor ama migration chain'de de olmasi lazim.
    #    Ozellikle CI/CD veya farkli ortamlarda init.sql calismamis olabilir.
    # ================================================================
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS unaccent"))

    # ================================================================
    # 2. Turkce TEXT SEARCH CONFIGURATION
    #    'simple' konfigurasyonunu kopyalar.
    #    simple: tokenize + lowercase yapar, stemming YAPMAZ.
    #    Ileride Hunspell/Zemberek dictionary eklenerek genisletilebilir.
    # ================================================================
    op.execute(sa.text(
        "CREATE TEXT SEARCH CONFIGURATION turkish (COPY = simple)"
    ))

    # ================================================================
    # 3. turkish_normalize() — Turkce karakter → ASCII donusumu
    #
    #    IMMUTABLE: Ayni girdi her zaman ayni ciktiyi verir.
    #    Bu sayede expression indekslerde kullanilabilir.
    #
    #    Donusum mantigi:
    #    - Buyuk harfler once kucultulur (Turkce kurallara gore)
    #    - Sonra ASCII karsiliklarina donusturulur
    #    - 'I' → 'ı' → 'i' (Turkce I, noktasiz i'ye donusur, sonra ASCII i)
    #    - 'İ' → 'i' (Turkce İ, dogrudan ASCII i)
    #
    #    plpgsql secildi (SQL yerine): replace() chain'i plpgsql'de
    #    daha okunakli ve debug edilebilir.
    # ================================================================
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION turkish_normalize(input_text TEXT)
        RETURNS TEXT AS $$
        BEGIN
            RETURN lower(
                replace(replace(replace(replace(replace(replace(replace(
                replace(replace(replace(replace(replace(replace(
                    input_text,
                    'İ', 'i'), 'I', 'ı'),
                    'Ş', 'ş'), 'Ğ', 'ğ'),
                    'Ü', 'ü'), 'Ö', 'ö'),
                    'Ç', 'ç'),
                    'ı', 'i'),
                    'ş', 's'), 'ğ', 'g'),
                    'ü', 'u'), 'ö', 'o'),
                    'ç', 'c')
            );
        END;
        $$ LANGUAGE plpgsql IMMUTABLE
    """))

    # ================================================================
    # 4. immutable_unaccent() — unaccent'in IMMUTABLE wrapper'i
    #
    #    PostgreSQL'in built-in unaccent() fonksiyonu STABLE olarak
    #    tanimlidir (dictionary dosyasina bagimli oldugu icin).
    #    Ancak expression indeks olusturmak icin IMMUTABLE fonksiyon gerekir.
    #    Bu wrapper bunu saglar.
    #
    #    PARALLEL SAFE: Paralel query plan'larinda kullanilabilir.
    #    STRICT: NULL girdi → NULL cikti (ekstra NULL check gereksiz).
    # ================================================================
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION immutable_unaccent(TEXT)
        RETURNS TEXT AS $$
            SELECT public.unaccent('public.unaccent', $1)
        $$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
    """))

    # ================================================================
    # 5. Trigram GIN indeks — normalized text uzerinde
    #
    #    011'deki ix_properties_title_trgm ve ix_properties_description_trgm
    #    ham title/description uzerinde calisir.
    #    Bu indeks turkish_normalize() uygulanmis birlesik metin uzerinde
    #    calisir — "kadikoy" aramasinda "Kadıköy" bulunur.
    #
    #    Neden ayri indeks (011'dekileri degistirmek yerine)?
    #    - 011 indeksleri mevcut sorgularda hala kullanilir
    #    - Bu indeks ozellikle normalized arama icin optimize edilmis
    #    - Ileride 011 indeksleri kaldirilabilir (ayri migration ile)
    # ================================================================
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_properties_turkish_search "
        "ON properties USING gin ("
        "(turkish_normalize(title) || ' ' || turkish_normalize(COALESCE(description, ''))) "
        "gin_trgm_ops)"
    ))


def downgrade() -> None:
    # Ters sira ile temizlik (bagimlilik sirasina dikkat)

    # 5. Indeks kaldir (fonksiyona bagimli, once indeks gitmeli)
    op.execute(sa.text("DROP INDEX IF EXISTS idx_properties_turkish_search"))

    # 4. immutable_unaccent kaldir
    op.execute(sa.text("DROP FUNCTION IF EXISTS immutable_unaccent(TEXT)"))

    # 3. turkish_normalize kaldir
    op.execute(sa.text("DROP FUNCTION IF EXISTS turkish_normalize(TEXT)"))

    # 2. Text search config kaldir
    op.execute(sa.text("DROP TEXT SEARCH CONFIGURATION IF EXISTS turkish"))

    # 1. Extension'lari DROP ETME — diger migration'lar kullanabilir (011 pg_trgm)
