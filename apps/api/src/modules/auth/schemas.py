"""
Emlak Teknoloji Platformu - Auth Schemas

Pydantic v2 modelleri: register, login, token, user response.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ---------- Request Schemas ----------


class RegisterRequest(BaseModel):
    """Yeni kullanici kayit istegi."""

    email: EmailStr = Field(description="E-posta adresi")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Sifre (min 8, max 128 karakter)",
    )
    full_name: str = Field(
        min_length=2,
        max_length=150,
        description="Ad soyad",
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="Telefon numarasi (opsiyonel)",
    )
    office_id: str | None = Field(
        default=None,
        description="Bagli ofis ID (verilmezse yeni ofis olusturulmaz, platform_admin atar)",
    )


class LoginRequest(BaseModel):
    """Giris istegi."""

    email: EmailStr = Field(description="E-posta adresi")
    password: str = Field(description="Sifre")


class RefreshRequest(BaseModel):
    """Token yenileme istegi."""

    refresh_token: str = Field(description="Refresh token")


class LogoutRequest(BaseModel):
    """Cikis istegi — refresh token opsiyonel olarak blacklist'e eklenebilir."""

    refresh_token: str | None = Field(default=None, description="Blacklist'e eklenecek refresh token")


class ForgotPasswordRequest(BaseModel):
    """Sifre sifirlama talebi — email ile reset token olusturur."""

    email: EmailStr = Field(description="Kayitli e-posta adresi")


class ResetPasswordRequest(BaseModel):
    """Sifre sifirlama onay istegi — token + yeni sifre ile sifre gunceller."""

    token: str = Field(description="E-posta ile gonderilen sifirlama tokeni")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Yeni sifre (min 8, max 128 karakter)",
    )


class ChangePasswordRequest(BaseModel):
    """Sifre degistirme istegi — login olmus kullanici icin (JWT zorunlu)."""

    current_password: str = Field(description="Mevcut sifre")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Yeni sifre (min 8, max 128 karakter)",
    )


# ---------- Response Schemas ----------


class TokenResponse(BaseModel):
    """JWT token cifti yaniti."""

    access_token: str = Field(description="Access token (kisa omurlu)")
    refresh_token: str = Field(description="Refresh token (uzun omurlu)")
    token_type: str = Field(default="bearer", description="Token tipi")


class UserResponse(BaseModel):
    """Kullanici bilgileri yaniti."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Kullanici UUID")
    email: str = Field(description="E-posta adresi")
    full_name: str = Field(description="Ad soyad")
    phone: str | None = Field(default=None, description="Telefon numarasi")
    role: str = Field(description="Kullanici rolu")
    office_id: str = Field(description="Bagli ofis UUID")
    avatar_url: str | None = Field(default=None, description="Profil fotografi URL")
    is_active: bool = Field(description="Hesap aktif mi")
    is_verified: bool = Field(description="E-posta dogrulanmis mi")
    preferred_channel: str = Field(description="Tercih edilen iletisim kanali")
