"""
Emlak Teknoloji Platformu - Data Pipeline Normalizers

API response Pydantic modelleri -> DB entity dict'leri donusumu.
"""

from .area_normalizer import normalize_area_analysis, safe_decimal
from .deprem_normalizer import build_point_wkt, calculate_risk_score, normalize_deprem_risk
from .price_history_normalizer import normalize_price_history
from .provenance_builder import build_provenance_fields

__all__ = [
    "build_point_wkt",
    "build_provenance_fields",
    "calculate_risk_score",
    "normalize_area_analysis",
    "normalize_deprem_risk",
    "normalize_price_history",
    "safe_decimal",
]
