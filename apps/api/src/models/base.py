"""
Emlak Teknoloji Platformu - Base Model & Mixins

Tüm entity modelleri bu base class ve mixin'leri kullanır.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class BaseModel(Base):
    """
    Abstract base model — tüm tablolarda ortak alanlar.

    - id: UUID v4 primary key (auto-increment DEĞİL)
    - created_at: Kayıt oluşturulma zamanı (DB server_default)
    - updated_at: Son güncelleme zamanı (DB server_default + onupdate)
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.now,
    )


class SoftDeleteMixin:
    """
    Soft-delete mixin — silinen kayıtlar fiziksel olarak silinmez.

    - deleted_at: Silinme zamanı (null = silinmemiş)
    - is_deleted: Hızlı filtreleme için boolean flag
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )


class TenantMixin:
    """
    Multi-tenant mixin — office_id FK placeholder.

    Alt sınıflarda office_id ForeignKey olarak tanımlanır.
    RLS (Row-Level Security) D3'te eklenecek.

    NOT: Bu mixin sadece marker/documentation amaçlıdır.
    Gerçek office_id FK alanı her model'de explicit tanımlanır
    çünkü ForeignKey constraint'i model-specific olmalı.
    """

    pass
