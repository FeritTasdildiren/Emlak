"""
Emlak Teknoloji Platformu - Earthquake Risk Service

Deprem risk hesaplama servisi.
"""

from __future__ import annotations


def calculate_risk_level(pga: float | None) -> str:
    """PGA degerine gore risk seviyesi hesapla.

    Args:
        pga: Peak Ground Acceleration (g cinsinden).

    Returns:
        Risk seviyesi: Dusuk, Orta, Yuksek, Cok Yuksek.
    """
    if pga is None:
        return "Bilinmiyor"
    if pga < 0.1:
        return "Dusuk"
    if pga < 0.2:
        return "Orta"
    if pga < 0.4:
        return "Yuksek"
    return "Cok Yuksek"
