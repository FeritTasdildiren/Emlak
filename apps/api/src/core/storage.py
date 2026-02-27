"""
Emlak Teknoloji Platformu - Object Storage (MinIO/S3)

MinIO S3 client: dosya yukleme, presigned URL, silme.
aiobotocore ile async islemler.
"""

import uuid
from typing import BinaryIO

import structlog
from aiobotocore.session import get_session

from src.config import settings

logger = structlog.get_logger()


def _get_endpoint_url() -> str:
    """MinIO endpoint URL'ini olusturur."""
    protocol = "https" if settings.MINIO_USE_SSL else "http"
    return f"{protocol}://{settings.MINIO_ENDPOINT}"


def _generate_object_key(folder: str, filename: str) -> str:
    """Benzersiz object key olusturur: folder/uuid_filename"""
    unique_id = uuid.uuid4().hex[:12]
    return f"{folder}/{unique_id}_{filename}"


async def upload_file(
    file_data: BinaryIO,
    filename: str,
    folder: str = "uploads",
    content_type: str = "application/octet-stream",
) -> str:
    """
    Dosyayi MinIO/S3'e yukler.

    Args:
        file_data: Dosya binary verisi
        filename: Orijinal dosya adi
        folder: S3 klasoru (ornegin: listings, avatars)
        content_type: MIME tipi

    Returns:
        Yuklenen dosyanin object key'i
    """
    object_key = _generate_object_key(folder, filename)
    session = get_session()

    async with session.create_client(
        "s3",
        endpoint_url=_get_endpoint_url(),
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    ) as client:
        await client.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=object_key,
            Body=file_data,
            ContentType=content_type,
        )
        logger.info(
            "file_uploaded",
            bucket=settings.MINIO_BUCKET,
            key=object_key,
        )

    return object_key


async def get_presigned_url(
    object_key: str,
    expires_in: int = 3600,
) -> str:
    """
    Dosya icin presigned URL olusturur.

    Args:
        object_key: S3 object key
        expires_in: URL gecerlilik suresi (saniye, default 1 saat)

    Returns:
        Presigned URL string
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
            Params={
                "Bucket": settings.MINIO_BUCKET,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )
        return url


async def delete_file(object_key: str) -> bool:
    """
    Dosyayi MinIO/S3'ten siler.

    Args:
        object_key: Silinecek dosyanin object key'i

    Returns:
        Basarili ise True
    """
    session = get_session()

    async with session.create_client(
        "s3",
        endpoint_url=_get_endpoint_url(),
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    ) as client:
        await client.delete_object(
            Bucket=settings.MINIO_BUCKET,
            Key=object_key,
        )
        logger.info(
            "file_deleted",
            bucket=settings.MINIO_BUCKET,
            key=object_key,
        )
        return True
