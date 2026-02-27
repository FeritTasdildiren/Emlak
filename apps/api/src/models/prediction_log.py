"""
Emlak Teknoloji Platformu - Prediction Log Model

ML model tahmin kayıtları. Her tahmin bir office'e bağlıdır (tenant-scoped).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel, TenantMixin


class PredictionLog(TenantMixin, BaseModel):
    """
    ML model tahmin logu.

    Her tahmin kaydı model adı, versiyonu, girdi/çıktı verileri,
    güven skoru ve gecikme süresini içerir.
    """

    __tablename__ = "prediction_logs"
    __table_args__ = (
        Index("ix_prediction_logs_model_time", "model_name", "model_version", "created_at"),
        Index("ix_prediction_logs_office_id", "office_id"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Model Bilgileri ----------
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    model_version: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )

    # ---------- Tahmin Verileri ----------
    input_data: Mapped[dict] = mapped_column(
        JSON, nullable=False,
    )
    output_data: Mapped[dict] = mapped_column(
        JSON, nullable=False,
    )

    # ---------- Metrikler ----------
    confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True,
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
