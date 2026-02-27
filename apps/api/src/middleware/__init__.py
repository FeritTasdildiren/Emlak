"""
Emlak Teknoloji Platformu - Middleware Module

Aktif middleware'ler:
    - RequestIdMiddleware  : Her istege benzersiz request_id atar
    - RequestLoggingMiddleware : HTTP istek/yanit loglama

Bekleyen (D3'te aktif edilecek):
    - TenantMiddleware     : JWT → RLS tenant izolasyonu
"""

from src.middleware.request_id import RequestIdMiddleware

# TenantMiddleware import'u hazir, main.py'de aktif edilecek
# from src.middleware.tenant import TenantMiddleware

__all__ = [
    "RequestIdMiddleware",
    # "TenantMiddleware",
]
