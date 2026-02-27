"""
Data Pipeline - API Clients

Kamu veri kaynaklari icin async HTTP client'lar:
- TUIKClient: TUIK MEDAS istatistik verileri
- TCMBClient: TCMB EVDS ekonomik veriler
- AFADClient: AFAD TDTH deprem tehlike verileri
- TKGMClient: TKGM WMS/WFS kadastro verileri
"""

from src.modules.data_pipeline.clients.afad_client import AFADClient
from src.modules.data_pipeline.clients.base_client import BaseAPIClient
from src.modules.data_pipeline.clients.tcmb_client import TCMBClient
from src.modules.data_pipeline.clients.tkgm_client import TKGMClient
from src.modules.data_pipeline.clients.tuik_client import TUIKClient

__all__ = [
    "AFADClient",
    "BaseAPIClient",
    "TCMBClient",
    "TKGMClient",
    "TUIKClient",
]
