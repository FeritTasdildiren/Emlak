"""
Emlak Teknoloji Platformu - Tenant Context Middleware

JWT token'dan office_id cikartip PostgreSQL session degiskeni olarak ayarlar.
Row-Level Security (RLS) policy'leri bu degiskeni kullanarak veri izolasyonu saglar.

Akis:
    1. Authorization header'dan JWT decode et
    2. Token'dan office_id al
    3. DB session baslat (BEGIN)
    4. SET LOCAL app.current_office_id = '<office_id>'
       (SET LOCAL sadece mevcut transaction scope'unda gecerli — otomatik temizlenir)
    5. Handler'i cagir (tum sorgular RLS ile korunur)
    6. COMMIT veya ROLLBACK

ONEMLI:
    - RLS policy'lerde: current_setting('app.current_office_id', true)::uuid
      missing-ok=true sayesinde setting yoksa NULL doner → erisim kapatilir.
    - Platform admin bypass icin app.current_user_role de SET LOCAL ile ayarlanir.

PUBLIC_PATHS: JWT gerektirmeyen endpoint'ler (health, auth, docs).
"""

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.config import settings

# JWT dogrulamasi gerektirmeyen endpoint'ler
PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/db",
        "/health/pdf",
        "/health/ready",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/listings/staging-styles",
        "/api/v1/listings/tones",
        "/api/v1/listings/portals",
        "/api/docs",
        "/api/openapi.json",
    }
)

# Prefix-based public paths: JWT gerektirmeyen path prefix'leri.
# Webhook endpoint'leri dis servislerden gelir (JWT tasimaz), kendi imza dogrulamasini yapar.
PUBLIC_PATH_PREFIXES: tuple[str, ...] = (
    "/api/docs",
    "/api/redoc",
    "/webhooks/",
    "/api/v1/showcases/public/",
    "/api/v1/telegram/mini-app/",
    "/ws",  # WebSocket — JWT dogrulamasi router icinde yapilir
)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Multi-tenant RLS middleware.

    Middleware sirasi: RequestIdMiddleware → RequestLoggingMiddleware → **TenantMiddleware**

    Her authenticated request icin:
        - JWT'den office_id cikar
        - PostgreSQL SET LOCAL ile transaction-scoped degisken ayarla
        - RLS policy'ler otomatik filtreler
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path: str = request.url.path

        # --- Public endpoint'ler → dogrudan gecir ---
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PATH_PREFIXES):
            return await call_next(request)

        # --- JWT token cozumle ---
        auth_header: str | None = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "type": "about:blank",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Authorization header eksik veya gecersiz.",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        token: str = auth_header.removeprefix("Bearer ").strip()

        try:
            payload: dict = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={
                    "type": "about:blank",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "JWT token gecersiz veya suresi dolmus.",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        office_id: str | None = payload.get("office_id")
        if not office_id:
            return JSONResponse(
                status_code=403,
                content={
                    "type": "about:blank",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": "Token'da office_id bilgisi bulunamadi.",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        # --- Kullanici bilgilerini request state'e kaydet ---
        # get_db_session() dependency bu degerleri okuyarak SET LOCAL uygular.
        # Boylece endpoint'lerin kullandigi DB session'da RLS dogru calisir.
        request.state.user_id = payload.get("sub")
        request.state.office_id = office_id
        request.state.user_role = payload.get("role")

        # NOT: Middleware artik kendi DB session'i ACMIYOR.
        # SET LOCAL islemini get_db_session() dependency hallediyor.
        # Bu dual-session problemini ortadan kaldirir.
        response: Response = await call_next(request)
        return response
