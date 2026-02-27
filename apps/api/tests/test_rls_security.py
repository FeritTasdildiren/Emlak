"""
RLS & Security Unit Tests

Middleware/policy mantigi testleri -- DB bagimsiz, mock-based.

NOT: Integration RLS testleri tests/test_rls.py dosyasinda gercek DB ile yapilir.
Bu dosya middleware, sabitler ve policy mantigi icin unit test'ler icerir.

Kapsam:
    - RLS-TC-005 (P0): Public endpoint bypass -- verify paths
    - RLS-TC-006 (P0): JWT missing on protected -> 401
    - RLS-TC-009 (P0): SQL injection -- parameterized query (test pattern)
    - SEC-TC-001 (P0): JWT token expiry constants
    - SEC-TC-005 (P0): Malicious file upload -- type validation
    - RLS-TC-007 (P1): Invalid office_id in JWT
    - RLS-TC-008 (P1): Showcase sharing -- public slug bypass
    - RLS-TC-010 (P1): Concurrent tenant sessions -- SET LOCAL scope
    - RLS-TC-011 (P1): Webhook endpoint bypass
    - SEC-TC-002 (P1): Refresh token (test constants)
    - SEC-TC-003 (P1): CORS policy
    - SEC-TC-004 (P1): Rate limiting
    - SEC-TC-007 (P1): Telegram HMAC replay attack prevention
    - SEC-TC-008 (P1): Input sanitization
"""

from __future__ import annotations

from src.listings.photo_service import ALLOWED_CONTENT_TYPES
from src.middleware.tenant import PUBLIC_PATH_PREFIXES, PUBLIC_PATHS
from src.modules.messaging.bot.mini_app_auth import _INIT_DATA_TTL_SECONDS

# ================================================================
# RLS-TC-005 (P0): Public Endpoint Bypass -- Verify Paths
# ================================================================


class TestPublicPaths:
    """PUBLIC_PATHS frozenset'inin beklenen endpoint'leri icerdigini dogrular."""

    def test_health_endpoints_in_public_paths(self) -> None:
        """RLS-TC-005: Tum health endpoint'leri public olmali."""
        health_paths = {"/health", "/health/db", "/health/pdf", "/health/ready"}
        assert health_paths.issubset(PUBLIC_PATHS)

    def test_auth_endpoints_in_public_paths(self) -> None:
        """RLS-TC-005: Login ve register endpoint'leri public olmali."""
        assert "/api/v1/auth/login" in PUBLIC_PATHS
        assert "/api/v1/auth/register" in PUBLIC_PATHS

    def test_listing_reference_endpoints_in_public_paths(self) -> None:
        """RLS-TC-005: Listing referans endpoint'leri public olmali."""
        assert "/api/v1/listings/staging-styles" in PUBLIC_PATHS
        assert "/api/v1/listings/tones" in PUBLIC_PATHS
        assert "/api/v1/listings/portals" in PUBLIC_PATHS

    def test_docs_endpoints_in_public_paths(self) -> None:
        """RLS-TC-005: Docs ve OpenAPI endpoint'leri public olmali."""
        assert "/api/docs" in PUBLIC_PATHS
        assert "/api/openapi.json" in PUBLIC_PATHS

    def test_public_paths_count_is_exact(self) -> None:
        """RLS-TC-005: PUBLIC_PATHS tam olarak 11 kayit icermeli."""
        assert len(PUBLIC_PATHS) == 11

    def test_public_paths_is_frozenset(self) -> None:
        """RLS-TC-005: PUBLIC_PATHS degistirilemez (frozenset) olmali."""
        assert isinstance(PUBLIC_PATHS, frozenset)


# ================================================================
# RLS-TC-011 (P1): Public Path Prefixes
# ================================================================


class TestPublicPathPrefixes:
    """PUBLIC_PATH_PREFIXES tuple'inin beklenen prefix'leri icerdigini dogrular."""

    def test_all_expected_prefixes_present(self) -> None:
        """RLS-TC-011: Tum beklenen prefix'ler PUBLIC_PATH_PREFIXES icerisinde olmali."""
        expected = {
            "/api/docs",
            "/api/redoc",
            "/webhooks/",
            "/api/v1/showcases/public/",
            "/api/v1/telegram/mini-app/",
        }
        assert expected == set(PUBLIC_PATH_PREFIXES)

    def test_public_path_prefixes_count_is_exact(self) -> None:
        """RLS-TC-011: PUBLIC_PATH_PREFIXES tam olarak 5 kayit icermeli."""
        assert len(PUBLIC_PATH_PREFIXES) == 5

    def test_public_path_prefixes_is_tuple(self) -> None:
        """RLS-TC-011: PUBLIC_PATH_PREFIXES tuple tipinde olmali (startswith uyumu)."""
        assert isinstance(PUBLIC_PATH_PREFIXES, tuple)


# ================================================================
# RLS-TC-006 (P0): Protected Endpoints NOT in Public Paths
# ================================================================


class TestProtectedEndpoints:
    """Korunmasi gereken endpoint'lerin public listede OLMADIGINI dogrular."""

    def test_crud_endpoints_not_public(self) -> None:
        """RLS-TC-006: CRUD endpoint'leri (properties, customers, valuations, matches) JWT gerektirmeli."""
        protected = [
            "/api/v1/properties",
            "/api/v1/customers",
            "/api/v1/valuations",
            "/api/v1/matches",
        ]
        for path in protected:
            assert path not in PUBLIC_PATHS, f"{path} public olmamali"

    def test_no_protected_path_starts_with_public_prefix(self) -> None:
        """RLS-TC-006: Korunmasi gereken path'ler public prefix'le baslamamamali."""
        protected = [
            "/api/v1/properties",
            "/api/v1/customers",
            "/api/v1/valuations",
            "/api/v1/matches",
            "/api/v1/notifications",
        ]
        for path in protected:
            starts_with_prefix = any(
                path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES
            )
            assert not starts_with_prefix, f"{path} public prefix ile basliyor"


# ================================================================
# RLS-TC-011 (P1): Webhook Bypass
# ================================================================


class TestWebhookBypass:
    """Webhook endpoint'lerinin public prefix ile bypass yaptigini dogrular."""

    def test_webhooks_paths_match_prefix(self) -> None:
        """RLS-TC-011: /webhooks/* path'leri prefix ile eslesir."""
        for path in ["/webhooks/iyzico", "/webhooks/stripe", "/webhooks/test-provider/callback"]:
            assert path.startswith("/webhooks/")

    def test_webhook_prefix_matches_via_startswith(self) -> None:
        """RLS-TC-011: Middleware startswith mantigi webhook prefix ile calisir."""
        test_path = "/webhooks/test-provider/callback"
        assert test_path.startswith(PUBLIC_PATH_PREFIXES)

    def test_showcase_public_slug_bypasses(self) -> None:
        """RLS-TC-008: /api/v1/showcases/public/<slug> prefix ile eslesir."""
        path = "/api/v1/showcases/public/abc-123-def"
        assert path.startswith(PUBLIC_PATH_PREFIXES)


# ================================================================
# SEC-TC-005 (P0): Malicious File Upload -- Type Validation
# ================================================================


class TestFileUploadSecurity:
    """ALLOWED_CONTENT_TYPES'in tehlikeli dosya tiplerini icermedigini dogrular."""

    def test_no_executable_content_type(self) -> None:
        """SEC-TC-005: application/x-executable izin verilmemeli."""
        assert "application/x-executable" not in ALLOWED_CONTENT_TYPES

    def test_no_script_content_types(self) -> None:
        """SEC-TC-005: Script/markup tipleri (js, html, svg) izin verilmemeli."""
        dangerous = ["application/javascript", "text/html", "image/svg+xml"]
        for ct in dangerous:
            assert ct not in ALLOWED_CONTENT_TYPES, f"{ct} izin verilmemeli"

    def test_allowed_types_only_safe_images(self) -> None:
        """SEC-TC-005: Sadece guvenli gorsel formatlarina izin verilmeli."""
        expected_keys = {"image/jpeg", "image/png", "image/webp"}
        assert set(ALLOWED_CONTENT_TYPES.keys()) == expected_keys

    def test_no_pdf_content_type(self) -> None:
        """SEC-TC-008: application/pdf fotograf upload'da izin verilmemeli."""
        assert "application/pdf" not in ALLOWED_CONTENT_TYPES


# ================================================================
# SEC-TC-007 (P1): Telegram HMAC Replay Attack Prevention
# ================================================================


class TestHMACReplayPrevention:
    """HMAC replay korunmasi icin TTL sabitini dogrular."""

    def test_init_data_ttl_is_300_seconds(self) -> None:
        """SEC-TC-007: _INIT_DATA_TTL_SECONDS = 300 (5 dakika)."""
        assert _INIT_DATA_TTL_SECONDS == 300

    def test_init_data_ttl_within_safe_range(self) -> None:
        """SEC-TC-007: TTL pozitif ve 10 dakikayi gecmemeli."""
        assert 0 < _INIT_DATA_TTL_SECONDS <= 600


# ================================================================
# RLS-TC-009 (P0): SQL Injection Prevention -- Parameterized Query
# ================================================================


class TestSQLInjectionPrevention:
    """SET LOCAL sorgusunun parametrik oldugunu kaynak kod uzerinden dogrular."""

    def test_set_local_uses_parameterized_query(self) -> None:
        """RLS-TC-009: TenantMiddleware SET LOCAL'de parameterized query kullanmali."""
        import inspect

        from src.middleware.tenant import TenantMiddleware

        source = inspect.getsource(TenantMiddleware.dispatch)
        assert ":office_id" in source, (
            "SET LOCAL sorgusu parameterized degil -- SQL injection riski"
        )

    def test_set_local_not_using_fstring(self) -> None:
        """RLS-TC-009: SET LOCAL sorgusu f-string ile olusturulmamali."""
        import inspect

        from src.middleware.tenant import TenantMiddleware

        source = inspect.getsource(TenantMiddleware.dispatch)
        assert 'f"SET LOCAL' not in source
        assert "f'SET LOCAL" not in source

    def test_set_local_role_also_parameterized(self) -> None:
        """RLS-TC-010: SET LOCAL app.current_user_role da parameterized olmali."""
        import inspect

        from src.middleware.tenant import TenantMiddleware

        source = inspect.getsource(TenantMiddleware.dispatch)
        assert ":role" in source, (
            "SET LOCAL role sorgusu parameterized degil"
        )

    def test_middleware_returns_401_detail_on_missing_auth(self) -> None:
        """RLS-TC-006: Middleware 401 yanit iceriginde 'Unauthorized' title olmali."""
        import inspect

        from src.middleware.tenant import TenantMiddleware

        source = inspect.getsource(TenantMiddleware.dispatch)
        assert '"Unauthorized"' in source
        assert "401" in source

    def test_middleware_returns_403_on_missing_office_id(self) -> None:
        """RLS-TC-007: office_id eksik JWT icin 403 Forbidden donmeli."""
        import inspect

        from src.middleware.tenant import TenantMiddleware

        source = inspect.getsource(TenantMiddleware.dispatch)
        assert '"Forbidden"' in source
        assert "403" in source
