-- ============================================
-- Emlak Teknoloji Platformu - Database Initialization
-- Bu script Docker Compose ile otomatik calisir.
-- ============================================

-- PostGIS eklentisini etkinlestir
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- UUID desteği
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigram similarity (arama icin)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Unaccent (Turkce karakter normalize)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- ============================================
-- app_user rolü oluştur (RLS tabii kullanici)
-- NOT: Bu kullanici superuser DEGILDIR.
-- Sadece gerekli izinlere sahip olacak.
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'app_user_dev_password';
    END IF;
END
$$;

-- Veritabanina baglanma izni
GRANT CONNECT ON DATABASE emlak_dev TO app_user;

-- Schema kullanim izni
GRANT USAGE ON SCHEMA public TO app_user;

-- ============================================
-- NOT: Tablo bazli GRANT ve RLS politikalari
-- migration'lar calistiktan sonra verilecek.
-- Ornek:
--   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
--   ALTER TABLE listings ENABLE ROW LEVEL SECURITY;
--   CREATE POLICY ... ON listings FOR SELECT USING (...);
-- ============================================
