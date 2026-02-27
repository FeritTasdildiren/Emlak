"""property_fts_trigger

Revision ID: 011_property_fts_trigger
Revises: 010_valuation_scraped_listing
Create Date: 2026-02-21

Property FTS trigger + pg_trgm indeksleri:
1. pg_trgm extension (fuzzy matching)
2. properties_search_vector_update() trigger fonksiyonu
3. BEFORE INSERT OR UPDATE trigger binding
4. Trigram GIN indeksler (title, description)
5. Mevcut verilerin search_vector backfill'i

Weight stratejisi:
  A (en yuksek) — title: ilan basligi
  B            — description: ilan aciklamasi
  C            — city, district, neighborhood: konum bilgileri
  D (en dusuk) — address: acik adres

NOT: PostgreSQL'de yerlesik 'turkish' ts_config YOKTUR.
'simple' config kullanilir — tokenize eder ama stemming yapmaz.
Fuzzy matching icin pg_trgm ile desteklenir.
Ileride custom turkish dictionary eklenebilir (Zemberek / Hunspell).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011_property_fts_trigger"
down_revision: Union[str, None] = "010_valuation_scraped_listing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. pg_trgm extension — fuzzy matching (similarity, LIKE '%..%')
    # ================================================================
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # ================================================================
    # 2. Trigger fonksiyonu — search_vector otomatik guncelleme
    #
    #    VOLATILE (default) — trigger fonksiyonlari IMMUTABLE olmamali.
    #    PostgreSQL, IMMUTABLE fonksiyonlarin sonuclarini cache'leyebilir
    #    ve trigger semantigi ile catisir. Ayrica to_tsvector() kendisi
    #    STABLE olarak tanimlidir; onu IMMUTABLE bir fonksiyona koymak
    #    yanlis bir optimizasyon garantisi verir.
    # ================================================================
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION properties_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'B') ||
                setweight(to_tsvector('simple', COALESCE(NEW.city, '')), 'C') ||
                setweight(to_tsvector('simple', COALESCE(NEW.district, '')), 'C') ||
                setweight(to_tsvector('simple', COALESCE(NEW.neighborhood, '')), 'C') ||
                setweight(to_tsvector('simple', COALESCE(NEW.address, '')), 'D');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    # ================================================================
    # 3. Trigger — BEFORE INSERT OR UPDATE (ilgili kolonlar degisince)
    #
    #    OF clause ile sadece FTS'e dahil kolonlar degistiginde tetiklenir.
    #    price, status vb. degisikliklerde trigger CALISMAZ — performans.
    # ================================================================
    op.execute(sa.text("""
        CREATE TRIGGER trg_properties_search_vector_update
            BEFORE INSERT OR UPDATE OF title, description, city, district, neighborhood, address
            ON properties
            FOR EACH ROW
            EXECUTE FUNCTION properties_search_vector_update()
    """))

    # ================================================================
    # 4. Trigram GIN indeksler — LIKE '%ara%' ve similarity() icin
    #
    #    GIN (gin_trgm_ops) secildi, GiST degil:
    #    - GIN: Daha buyuk indeks, daha hizli okuma
    #    - GiST: Daha kucuk indeks, daha yavas okuma
    #    Okuma agirlikli (arama) kullanim icin GIN optimaldir.
    #
    #    Sadece title ve description — city/district icin B-tree
    #    zaten mevcut (ix_properties_city_district).
    # ================================================================
    op.execute(sa.text(
        "CREATE INDEX ix_properties_title_trgm "
        "ON properties USING gin (title gin_trgm_ops)"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_properties_description_trgm "
        "ON properties USING gin (description gin_trgm_ops)"
    ))

    # ================================================================
    # 5. Mevcut verileri backfill
    #
    #    Trigger sadece yeni INSERT/UPDATE'lerde calisir.
    #    Onceden eklenmis kayitlarin search_vector'u NULL olabilir.
    #    Bu UPDATE ile mevcut tum kayitlari dolduruyor.
    #
    #    NOT: Buyuk tablolarda (1M+ satir) batch UPDATE daha guvenli
    #    olur. MVP'de tek UPDATE yeterli — satir sayisi dusuk.
    # ================================================================
    op.execute(sa.text("""
        UPDATE properties SET search_vector =
            setweight(to_tsvector('simple', COALESCE(title, '')), 'A') ||
            setweight(to_tsvector('simple', COALESCE(description, '')), 'B') ||
            setweight(to_tsvector('simple', COALESCE(city, '')), 'C') ||
            setweight(to_tsvector('simple', COALESCE(district, '')), 'C') ||
            setweight(to_tsvector('simple', COALESCE(neighborhood, '')), 'C') ||
            setweight(to_tsvector('simple', COALESCE(address, '')), 'D')
    """))


def downgrade() -> None:
    # Ters sira ile temizlik

    # Trigger kaldir
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS trg_properties_search_vector_update ON properties"
    ))

    # Trigger fonksiyonu kaldir
    op.execute(sa.text(
        "DROP FUNCTION IF EXISTS properties_search_vector_update()"
    ))

    # Trigram indeksler kaldir
    op.execute(sa.text("DROP INDEX IF EXISTS ix_properties_title_trgm"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_properties_description_trgm"))

    # NOT: pg_trgm extension'i DROP ETME — baska migration'lar kullanabilir.
    # NOT: search_vector kolonunu ve GIN indeksini BIRAKMA — 001'de olusturuldu.
    # Backfill'i geri almak icin: UPDATE properties SET search_vector = NULL;
    # Ancak bu genellikle gereksiz — trigger zaten kaldirildi.
