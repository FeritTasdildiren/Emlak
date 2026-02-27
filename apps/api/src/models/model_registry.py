"""
Emlak Teknoloji Platformu - Model Registry

ML model kayıtları. Platform geneli — tenant-scoped değildir.
"""

from __future__ import annotations

from sqlalchemy import Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel


class ModelRegistry(BaseModel):
    """
    ML model kayıt defteri.

    Her model + versiyon kombinasyonu benzersizdir (uq_model_registry_name_version).
    Durumlar (status): active, archived, deprecated
    """

    __tablename__ = "model_registry"
    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_registry_name_version"),
    )

    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
    )
    version: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    artifact_url: Mapped[str] = mapped_column(
        String(500), nullable=False,
    )
    metrics: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
    )
    training_data_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    feature_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'active'"),
    )
