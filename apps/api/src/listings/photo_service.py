"""
Emlak Teknoloji Platformu - Photo Upload Service

Fotoğraf yükleme, validasyon ve thumbnail oluşturma servisi.
MinIO/S3'e async upload yapar, Pillow ile thumbnail oluşturur.

Desteklenen formatlar: JPEG, PNG, WebP
Maksimum dosya boyutu: 50MB
Thumbnail boyutu: 400x300 px, JPEG quality 80
"""

from __future__ import annotations

import io
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog
from aiobotocore.session import get_session
from PIL import Image

from src.config import settings
from src.core.exceptions import ValidationError

if TYPE_CHECKING:
    from fastapi import UploadFile

logger = structlog.get_logger()

# ---------- Sabitler ----------
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
THUMBNAIL_SIZE = (400, 300)
THUMBNAIL_QUALITY = 80
PHOTO_BUCKET = "property-photos"


@dataclass
class PhotoUploadResult:
    """Fotoğraf yükleme sonucu."""

    original_url: str
    thumbnail_url: str
    file_size: int
    dimensions: tuple[int, int]
    content_type: str


def _get_endpoint_url() -> str:
    """MinIO endpoint URL'ini oluşturur."""
    protocol = "https" if settings.MINIO_USE_SSL else "http"
    return f"{protocol}://{settings.MINIO_ENDPOINT}"


def _validate_content_type(content_type: str | None) -> str:
    """
    Dosya MIME tipini doğrular.

    Args:
        content_type: Dosyanın MIME tipi.

    Returns:
        Geçerli dosya uzantısı (jpg, png, webp).

    Raises:
        ValidationError: Desteklenmeyen dosya formatı.
    """
    if content_type is None or content_type not in ALLOWED_CONTENT_TYPES:
        allowed = ", ".join(ALLOWED_CONTENT_TYPES.keys())
        raise ValidationError(
            detail=f"Desteklenmeyen dosya formati. Izin verilen tipler: {allowed}",
        )
    return ALLOWED_CONTENT_TYPES[content_type]


def _validate_file_size(file_size: int) -> None:
    """
    Dosya boyutunu doğrular.

    Args:
        file_size: Dosya boyutu (byte).

    Raises:
        ValidationError: Dosya boyutu 50MB'dan büyükse.
    """
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        raise ValidationError(
            detail=f"Dosya boyutu cok buyuk. Maksimum: {max_mb}MB",
        )


def _validate_magic_bytes(file_data: bytes, content_type: str) -> None:
    """
    Dosyanın ilk byte'larını MIME tipi ile karşılaştırarak doğrular.
    JPEG, PNG ve WebP destekler.

    Raises:
        ValidationError: Magic bytes MIME tipi ile uyuşmuyorsa.
    """
    if len(file_data) < 4:
        raise ValidationError(detail="Gecersiz dosya formatı (dosya cok kucuk).")

    # JPEG: FF D8 FF
    if content_type == "image/jpeg":
        if not (file_data[0] == 0xFF and file_data[1] == 0xD8 and file_data[2] == 0xFF):
            raise ValidationError(detail="Gecersiz JPEG dosyası (magic bytes hatası).")

    # PNG: 89 50 4E 47
    elif content_type == "image/png":
        if not (
            file_data[0] == 0x89
            and file_data[1] == 0x50
            and file_data[2] == 0x4E
            and file_data[3] == 0x47
        ):
            raise ValidationError(detail="Gecersiz PNG dosyası (magic bytes hatası).")

    # WebP: RIFF (first 4) ... WEBP (at offset 8)
    elif content_type == "image/webp" and not (
        file_data.startswith(b"RIFF") and file_data[8:12] == b"WEBP"
    ):
        raise ValidationError(detail="Gecersiz WebP dosyası (magic bytes hatası).")


def _create_thumbnail(image_data: bytes) -> tuple[bytes, tuple[int, int]]:
    """
    Pillow ile thumbnail oluşturur.

    Args:
        image_data: Orijinal fotoğraf binary verisi.

    Returns:
        (thumbnail_bytes, original_dimensions) tuple'ı.
        thumbnail_bytes: JPEG formatında thumbnail verisi.
        original_dimensions: Orijinal fotoğrafın (width, height) boyutları.
    """
    img = Image.open(io.BytesIO(image_data))
    original_dimensions = img.size

    # RGB'ye çevir (PNG alpha kanalı için gerekli)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Thumbnail oluştur — aspect ratio korunur
    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

    # JPEG olarak kaydet
    thumb_buffer = io.BytesIO()
    img.save(thumb_buffer, format="JPEG", quality=THUMBNAIL_QUALITY)
    thumb_buffer.seek(0)

    return thumb_buffer.read(), original_dimensions


async def _upload_to_minio(
    file_data: bytes,
    object_key: str,
    content_type: str,
) -> str:
    """
    Dosyayı MinIO/S3'e yükler.

    Args:
        file_data: Dosya binary verisi.
        object_key: S3 object key (path).
        content_type: MIME tipi.

    Returns:
        Yüklenen dosyanın object key'i.
    """
    session = get_session()

    async with session.create_client(
        "s3",
        endpoint_url=_get_endpoint_url(),
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    ) as client:
        await client.put_object(
            Bucket=PHOTO_BUCKET,
            Key=object_key,
            Body=file_data,
            ContentType=content_type,
        )

    return object_key


async def _get_presigned_url(object_key: str, expires_in: int = 3600) -> str:
    """
    MinIO'dan presigned URL oluşturur.

    Args:
        object_key: S3 object key.
        expires_in: URL geçerlilik süresi (saniye, default 1 saat).

    Returns:
        Presigned URL string.
    """
    session = get_session()

    async with session.create_client(
        "s3",
        endpoint_url=_get_endpoint_url(),
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    ) as client:
        url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": PHOTO_BUCKET, "Key": object_key},
            ExpiresIn=expires_in,
        )
        return url


async def upload_photo(
    file: UploadFile,
    tenant_id: str,
) -> PhotoUploadResult:
    """
    Tek bir fotoğrafı MinIO'ya yükler ve thumbnail oluşturur.

    Akış:
        1. Dosya tipi doğrulama (JPEG/PNG/WebP)
        2. Dosya boyutu doğrulama (maks 50MB)
        3. Orijinal dosyayı MinIO'ya yükle
        4. Pillow ile thumbnail oluştur (400x300, JPEG 80 quality)
        5. Thumbnail'i MinIO'ya yükle
        6. Her iki dosya için presigned URL oluştur

    Args:
        file: FastAPI UploadFile nesnesi.
        tenant_id: Kiracı (ofis) UUID string'i.

    Returns:
        PhotoUploadResult — orijinal ve thumbnail URL'leri, boyut bilgileri.

    Raises:
        ValidationError: Dosya formatı veya boyutu geçersizse.
    """
    # 1. İçerik tipi doğrulama
    ext = _validate_content_type(file.content_type)

    # 2. Dosyayı oku
    file_data = await file.read()
    file_size = len(file_data)

    # 3. Boyut doğrulama
    _validate_file_size(file_size)

    # 4. Magic bytes doğrulama (TASK-150)
    _validate_magic_bytes(file_data, file.content_type or "image/jpeg")

    # 5. Benzersiz ID oluştur
    photo_id = uuid.uuid4().hex

    # 5. Object key'leri belirle
    original_key = f"{tenant_id}/{photo_id}.{ext}"
    thumbnail_key = f"{tenant_id}/thumbs/{photo_id}_thumb.jpg"

    # 6. Thumbnail oluştur
    thumbnail_data, dimensions = _create_thumbnail(file_data)

    # 7. Orijinal ve thumbnail'i MinIO'ya yükle
    await _upload_to_minio(file_data, original_key, file.content_type or "image/jpeg")
    await _upload_to_minio(thumbnail_data, thumbnail_key, "image/jpeg")

    # 8. Presigned URL'ler oluştur
    original_url = await _get_presigned_url(original_key)
    thumbnail_url = await _get_presigned_url(thumbnail_key)

    logger.info(
        "photo_uploaded",
        tenant_id=tenant_id,
        photo_id=photo_id,
        file_size=file_size,
        dimensions=dimensions,
        content_type=file.content_type,
    )

    return PhotoUploadResult(
        original_url=original_url,
        thumbnail_url=thumbnail_url,
        file_size=file_size,
        dimensions=dimensions,
        content_type=file.content_type or "image/jpeg",
    )


async def delete_photo(
    tenant_id: str,
    object_key: str,
) -> bool:
    """
    MinIO'dan fotoğraf ve thumbnail'ini siler.

    Args:
        tenant_id: Kiracı (ofis) UUID string'i.
        object_key: Silinecek fotoğrafın object key'i.

    Returns:
        Başarılı ise True.
    """
    session = get_session()

    # Thumbnail key'ini orijinal key'den türet
    # Örnek: "tenant/abc123.jpg" -> "tenant/thumbs/abc123_thumb.jpg"
    parts = object_key.rsplit("/", 1)
    if len(parts) == 2:
        folder, filename = parts
    else:
        folder = ""
        filename = parts[0]

    name_without_ext = filename.rsplit(".", 1)[0]
    thumbnail_key = f"{folder}/thumbs/{name_without_ext}_thumb.jpg"

    async with session.create_client(
        "s3",
        endpoint_url=_get_endpoint_url(),
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    ) as client:
        # Orijinal dosyayı sil
        await client.delete_object(Bucket=PHOTO_BUCKET, Key=object_key)

        # Thumbnail'i sil
        await client.delete_object(Bucket=PHOTO_BUCKET, Key=thumbnail_key)

    logger.info(
        "photo_deleted",
        tenant_id=tenant_id,
        object_key=object_key,
        thumbnail_key=thumbnail_key,
    )

    return True
