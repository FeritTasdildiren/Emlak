"""
Emlak Teknoloji Platformu - Notifications Router

In-app bildirim API endpoint'leri.

Prefix: /api/v1/notifications
Guvenlik: Tum endpoint'ler JWT gerektirir (get_current_active_user).

Endpoint'ler:
    GET    /notifications              → Kullanicinin bildirimlerini listele
    GET    /notifications/unread-count → Okunmamis bildirim sayisi
    PATCH  /notifications/{id}/read   → Tek bildirimi okundu isaretle
    PATCH  /notifications/read-all    → Tum bildirimleri okundu isaretle
    DELETE /notifications/{id}        → Bildirimi soft-delete yap
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Query, status
from sqlalchemy import select

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.notification import Notification
from src.modules.auth.dependencies import ActiveUser
from src.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from src.modules.notifications.service import NotificationService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"],
)


# ---------- GET /notifications ----------


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Bildirimleri listele",
    description="Authenticated kullanicinin bildirimlerini sayfalama ile listeler.",
)
async def list_notifications(
    db: DBSession,
    current_user: ActiveUser,
    unread_only: bool = Query(
        default=False,
        description="True ise sadece okunmamis bildirimler doner",
    ),
    limit: int = Query(
        default=20, ge=1, le=100,
        description="Sayfa basi kayit sayisi (max 100)",
    ),
    offset: int = Query(
        default=0, ge=0,
        description="Atlanacak kayit sayisi (pagination)",
    ),
) -> NotificationListResponse:
    """
    Kullanicinin bildirimlerini listeler.

    - Silinmis bildirimler otomatik filtrelenir
    - Sonuclar en yeniden en eskiye siralanir
    - Pagination: limit + offset
    """
    notifications = await NotificationService.list_for_user(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )

    total = await NotificationService.count_for_user(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
    )

    return NotificationListResponse(
        items=[
            NotificationResponse(
                id=str(n.id),
                type=n.type,
                title=n.title,
                body=n.body,
                is_read=n.is_read,
                data=n.data,
                created_at=n.created_at,
            )
            for n in notifications
        ],
        total=total,
    )


# ---------- GET /notifications/unread-count ----------


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Okunmamis bildirim sayisi",
    description="Kullanicinin okunmamis bildirim sayisini dondurur.",
)
async def get_unread_count(
    db: DBSession,
    current_user: ActiveUser,
) -> UnreadCountResponse:
    """
    Okunmamis bildirim sayisini dondurur.

    Frontend'de badge/counter gostermek icin kullanilir.
    """
    count = await NotificationService.unread_count(
        db=db, user_id=current_user.id
    )

    return UnreadCountResponse(count=count)


# ---------- PATCH /notifications/{id}/read ----------


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Bildirimi okundu isaretle",
    description="Belirtilen bildirimi okundu olarak isaretler.",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> NotificationResponse:
    """
    Tek bildirimi okundu olarak isaretler.

    - Sadece bildirimin sahibi isaretleyebilir
    - Bildirim bulunamazsa veya baska kullaniciya aitse 404
    """
    success = await NotificationService.mark_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if not success:
        raise NotFoundError(resource="Bildirim", resource_id=str(notification_id))

    # Guncellenmis bildirimi getir
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one()

    return NotificationResponse(
        id=str(notification.id),
        type=notification.type,
        title=notification.title,
        body=notification.body,
        is_read=notification.is_read,
        data=notification.data,
        created_at=notification.created_at,
    )


# ---------- PATCH /notifications/read-all ----------


@router.patch(
    "/read-all",
    summary="Tum bildirimleri okundu isaretle",
    description="Kullanicinin tum okunmamis bildirimlerini okundu yapar.",
)
async def mark_all_notifications_read(
    db: DBSession,
    current_user: ActiveUser,
) -> dict:
    """
    Tum okunmamis bildirimleri okundu yapar.

    Returns:
        updated_count: Guncellenen bildirim sayisi.
    """
    updated_count = await NotificationService.mark_all_read(
        db=db, user_id=current_user.id
    )

    return {"updated_count": updated_count}


# ---------- DELETE /notifications/{id} ----------


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Bildirimi sil (soft-delete)",
    description="Belirtilen bildirimi soft-delete yapar. Fiziksel silme yapilmaz.",
)
async def delete_notification(
    notification_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> None:
    """
    Bildirimi soft-delete yapar.

    - deleted_at ve is_deleted alanlari set edilir
    - Sadece bildirimin sahibi silebilir
    - Bildirim bulunamazsa veya baska kullaniciye aitse 404
    """
    success = await NotificationService.delete(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if not success:
        raise NotFoundError(resource="Bildirim", resource_id=str(notification_id))
