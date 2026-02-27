"""
Emlak Teknoloji Platformu - OpenAI Configuration Constants

Model isimleri, kalite seviyeleri, gorsel boyut sabitleri ve retry parametreleri.

Kullanim:
    from src.services.openai_config import TEXT_MODEL, IMAGE_MODEL, SIZE_LANDSCAPE

Referans: TASK-114 (S8.1)
"""

from __future__ import annotations

# ---------- Text Models ----------
TEXT_MODEL: str = "gpt-5-mini"

# ---------- Image Models ----------
IMAGE_MODEL: str = "gpt-image-1.5"
IMAGE_MODEL_MINI: str = "gpt-image-1-mini"

# ---------- Quality Levels ----------
QUALITY_LOW: str = "low"
QUALITY_MEDIUM: str = "medium"
QUALITY_HIGH: str = "high"

# ---------- Image Sizes ----------
SIZE_SQUARE: str = "1024x1024"
SIZE_LANDSCAPE: str = "1536x1024"
SIZE_PORTRAIT: str = "1024x1536"

# ---------- Defaults ----------
DEFAULT_MAX_TOKENS: int = 4096
DEFAULT_TEMPERATURE: float = 0.7
DEFAULT_IMAGE_SIZE: str = SIZE_LANDSCAPE
DEFAULT_IMAGE_QUALITY: str = QUALITY_MEDIUM
DEFAULT_IMAGE_COUNT: int = 1

# ---------- Retry ----------
MAX_RETRIES: int = 3
RETRY_BASE_DELAY: float = 1.0   # saniye
RETRY_MAX_DELAY: float = 30.0   # saniye
RETRY_MULTIPLIER: float = 2.0
