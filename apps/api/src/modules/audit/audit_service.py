"""
Emlak Teknoloji Platformu - Audit Service

KVKK uyumlu audit loglama servisi.
Tum kritik islemleri asenkron olarak kayit altina alir.

Kullanim:
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action=AuditAction.CREATE,
        entity_type="Customer",
        entity_id=str(customer.id),
        new_value={"full_name": "Ali Veli", "phone": "5551234567"},
        request=request,
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.models.audit_log import AuditAction, AuditLog

if TYPE_CHECKING:
    import uuid

    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class AuditService:
    """
    Audit loglama servisi.

    Tum metodlar static — state tutmaz, DB session disaridan alinir.
    Hata durumunda islem BASARISIZ olmaz — audit log yazimi try/except icinde
    yapilir ve basarisizlik sadece loglanir (kritik is mantigi engellenmez).
    """

    @staticmethod
    async def log_action(
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        office_id: uuid.UUID,
        action: AuditAction | str,
        entity_type: str,
        entity_id: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        request: Request | None = None,
    ) -> AuditLog | None:
        """
        Audit log kaydi olusturur.

        Args:
            db: Async database session.
            user_id: Eylemi gerceklestiren kullanici UUID.
            office_id: Tenant (ofis) UUID.
            action: Eylem tipi (AuditAction enum veya string).
            entity_type: Etkilenen varlik tipi (model adi).
            entity_id: Etkilenen varlik UUID (opsiyonel).
            old_value: Degisiklik oncesi degerler (opsiyonel).
            new_value: Degisiklik sonrasi degerler (opsiyonel).
            request: FastAPI Request nesnesi (IP/user agent icin).

        Returns:
            Olusturulan AuditLog kaydi veya hata durumunda None.

        Note:
            Bu metod asla exception firlatmaz — is mantigi engellenmemelidir.
        """
        try:
            # Action enum'a cevir (string geldiyse)
            action_str = action.value if isinstance(action, AuditAction) else str(action)

            # Request bilgilerini cikar
            ip_address: str | None = None
            user_agent: str | None = None
            if request is not None:
                ip_address = _extract_client_ip(request)
                user_agent = request.headers.get("user-agent", "")[:500]

            audit_log = AuditLog(
                office_id=office_id,
                user_id=user_id,
                action=action_str,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(audit_log)
            await db.flush()

            logger.info(
                "audit_log_created",
                audit_id=str(audit_log.id),
                user_id=str(user_id),
                office_id=str(office_id),
                action=action_str,
                entity_type=entity_type,
                entity_id=entity_id,
            )

            return audit_log

        except Exception:
            # Audit log basarisizligi is mantigi engellememelidir
            logger.error(
                "audit_log_failed",
                user_id=str(user_id),
                office_id=str(office_id),
                action=str(action),
                entity_type=entity_type,
                entity_id=entity_id,
                exc_info=True,
            )
            return None


def _extract_client_ip(request: Request) -> str | None:
    """
    Request'ten istemci IP adresini cikarir.

    Proxy arkasindaki gercek IP icin X-Forwarded-For header'ini kontrol eder.
    """
    # Proxy arkasi: X-Forwarded-For header'i (ilk IP gercek istemci)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # X-Real-IP header (nginx reverse proxy)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # Dogrudan baglanti
    if request.client:
        return request.client.host

    return None
