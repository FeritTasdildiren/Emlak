"""
Emlak Teknoloji Platformu - Photo Upload Router

Fotoğraf yükleme endpoint'leri.

Prefix: /api/v1/listings/photos
Güvenlik: Tüm endpoint'ler JWT gerektirir (ActiveUser).
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, UploadFile, status

from src.core.exceptions import ValidationError
from src.listings.photo_service import PhotoUploadResult, upload_photo
from src.modules.auth.dependencies import ActiveUser  # noqa: TC001 — FastAPI runtime

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/listings/photos",
    tags=["photos"],
)

# ---------- Schemas ----------
# Basit dict response kullaniyoruz, ayri schema dosyasina gerek yok.


def _photo_result_to_dict(result: PhotoUploadResult) -> dict:
    """PhotoUploadResult'i JSON serializable dict'e cevirir."""
    return {
        "original_url": result.original_url,
        "thumbnail_url": result.thumbnail_url,
        "file_size": result.file_size,
        "dimensions": list(result.dimensions),
        "content_type": result.content_type,
    }


# ---------- Endpoints ----------


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Tek fotograf yukle",
    description=(
        "Bir adet fotograf yukler. "
        "Desteklenen formatlar: JPEG, PNG, WebP. Maksimum boyut: 50MB. "
        "Otomatik thumbnail olusturulur (400x300, JPEG)."
    ),
)
async def upload_single_photo(
    file: UploadFile,
    user: ActiveUser,
) -> dict:
    """
    Tek fotograf yukleme endpoint'i.

    Akis:
        1. JWT'den tenant_id al
        2. photo_service.upload_photo() ile MinIO'ya yukle
        3. PhotoUploadResult dondur
    """
    tenant_id = str(user.office_id)

    result = await upload_photo(file=file, tenant_id=tenant_id)

    logger.info(
        "photo_upload_single",
        user_id=str(user.id),
        tenant_id=tenant_id,
        file_size=result.file_size,
    )

    return _photo_result_to_dict(result)


@router.post(
    "/batch",
    status_code=status.HTTP_201_CREATED,
    summary="Toplu fotograf yukle (maks 10)",
    description=(
        "Birden fazla fotograf yukler (maksimum 10 adet). "
        "Her fotograf icin ayri thumbnail olusturulur."
    ),
)
async def upload_batch_photos(
    files: list[UploadFile],
    user: ActiveUser,
) -> dict:
    """
    Toplu fotograf yukleme endpoint'i (maks 10 dosya).

    Akis:
        1. Dosya sayisi kontrolu (maks 10)
        2. Her dosya icin photo_service.upload_photo() cagir
        3. Basarili ve basarisiz sonuclari ayri listele
    """
    # Dosya sayisi kontrolu
    max_batch = 10
    if len(files) > max_batch:
        raise ValidationError(
            detail=f"Toplu yuklemede maksimum {max_batch} dosya gonderilebilir.",
        )

    if len(files) == 0:
        raise ValidationError(detail="En az 1 dosya gonderilmelidir.")

    tenant_id = str(user.office_id)
    results: list[dict] = []
    errors: list[dict] = []

    for idx, file in enumerate(files):
        try:
            result = await upload_photo(file=file, tenant_id=tenant_id)
            results.append(_photo_result_to_dict(result))
        except Exception as exc:
            logger.warning(
                "photo_upload_batch_item_failed",
                index=idx,
                filename=file.filename,
                error=str(exc),
            )
            errors.append(
                {
                    "index": idx,
                    "filename": file.filename,
                    "error": str(exc),
                }
            )

    logger.info(
        "photo_upload_batch",
        user_id=str(user.id),
        tenant_id=tenant_id,
        total=len(files),
        success=len(results),
        failed=len(errors),
    )

    return {
        "uploaded": results,
        "errors": errors,
        "total": len(files),
        "success_count": len(results),
        "error_count": len(errors),
    }


@router.delete(
    "/{photo_id}",
    status_code=status.HTTP_200_OK,
    summary="Fotograf sil",
    description="Belirtilen fotoğrafi ve thumbnail'ini MinIO'dan siler.",
)
async def delete_photo_endpoint(
    photo_id: str,
    user: ActiveUser,
) -> dict:
    """
    Fotograf silme endpoint'i.

    Args:
        photo_id: Silinecek fotografin object key'i (tenant_id/uuid.ext formati).

    Akis:
        1. JWT'den tenant_id al
        2. Object key'in bu tenant'a ait olduğunu dogrula
        3. photo_service.delete_photo() ile MinIO'dan sil
    """
    from src.listings.photo_service import delete_photo

    tenant_id = str(user.office_id)

    # Guvenlik: photo_id'nin bu tenant'a ait oldugunu dogrula
    # photo_id formati: "tenant_id/uuid.ext" veya sadece "uuid.ext"
    # Tam key'i olustur
    object_key = photo_id if photo_id.startswith(tenant_id) else f"{tenant_id}/{photo_id}"

    await delete_photo(tenant_id=tenant_id, object_key=object_key)

    logger.info(
        "photo_deleted_endpoint",
        user_id=str(user.id),
        tenant_id=tenant_id,
        photo_id=photo_id,
    )

    return {"deleted": True, "photo_id": photo_id}
