"""
Emlak Teknoloji Platformu - Custom Exceptions & RFC 7807 Error Handling

Uygulama genelinde kullanilan hata siniflari.
RFC 7807 (Problem Details for HTTP APIs) formatinda JSON hata yanitlari uretir.

Response ornegi:
    {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "Ilan (id=42) bulunamadi.",
        "instance": "/api/v1/listings/42",
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse


# ---------- Base Exception ----------
class AppException(Exception):  # noqa: N818 — base exception; subclasses use Error suffix
    """
    Tum uygulama hatalarinin temel sinifi.

    HTTPException yerine Exception kullanilir cunku:
    - RFC 7807 formatini tam kontrol edebiliyoruz
    - request_id gibi ek alanlari ekleyebiliyoruz
    - Tum alt siniflar ayni handler'dan gecer
    """

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Beklenmeyen bir hata olustu.",
        error_type: str = "about:blank",
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_type = error_type
        self.headers = headers
        super().__init__(detail)


# ---------- Concrete Exceptions ----------
class NotFoundError(AppException):
    """Kaynak bulunamadi (404)."""

    def __init__(self, resource: str = "Kaynak", resource_id: str | int | None = None):
        detail = f"{resource} bulunamadi."
        if resource_id is not None:
            detail = f"{resource} (id={resource_id}) bulunamadi."
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class PermissionDenied(AppException):
    """Yetki hatasi (403)."""

    def __init__(self, detail: str = "Bu islemi yapmaya yetkiniz yok."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ValidationError(AppException):
    """Dogrulama hatasi (422)."""

    def __init__(self, detail: str = "Girdi dogrulanamadi."):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class AuthenticationError(AppException):
    """Kimlik dogrulama hatasi (401)."""

    def __init__(self, detail: str = "Kimlik dogrulanamadi."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictError(AppException):
    """Cakisma hatasi (409) - ornegin unique constraint."""

    def __init__(self, detail: str = "Kaynak zaten mevcut."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class QuotaExceededError(AppException):
    """
    Kota asim hatasi (429).

    Kullanicinin plan kotasi dolduğunda firlatilir.
    RFC 7807 body'sine ek olarak limit, used, plan ve upgrade_url alanlari eklenir.
    """

    def __init__(
        self,
        limit: int,
        used: int,
        plan: str,
        detail: str = "Aylik degerleme kotaniz doldu.",
        upgrade_url: str = "/pricing",
    ):
        self.limit = limit
        self.used = used
        self.plan = plan
        self.upgrade_url = upgrade_url
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_type="quota_exceeded",
        )


# ---------- HTTP Status Code → Title Mapping ----------
_STATUS_TITLES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


# ---------- RFC 7807 Exception Handler ----------
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    AppException → RFC 7807 JSON response.

    Her hata yanitinda request_id bulunur (RequestIdMiddleware ile atanir).
    Frontend bu ID ile destek talebi olusturabilir.
    """
    request_id: str | None = getattr(request.state, "request_id", None)

    body: dict = {
        "type": exc.error_type,
        "title": _STATUS_TITLES.get(exc.status_code, "Error"),
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url),
        "request_id": request_id,
    }

    # QuotaExceededError icin ek alanlar
    if isinstance(exc, QuotaExceededError):
        body["limit"] = exc.limit
        body["used"] = exc.used
        body["plan"] = exc.plan
        body["upgrade_url"] = exc.upgrade_url

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=exc.headers,
    )


# ---------- Generic Unhandled Exception Handler ----------
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Yakalanmamis Exception'lar icin fallback handler.

    Production'da detay gostermez, sadece request_id verir.
    Development'ta exc detayini gosterir.
    """
    from src.config import settings

    request_id: str | None = getattr(request.state, "request_id", None)
    detail: str = str(exc) if settings.APP_DEBUG else "Beklenmeyen bir hata olustu."

    body: dict = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "detail": detail,
        "instance": str(request.url),
        "request_id": request_id,
    }

    return JSONResponse(status_code=500, content=body)
