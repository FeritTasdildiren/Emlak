"""
Data Pipeline - Response Schemas

API client'larindan donen verilerin Pydantic v2 modelleri.
"""

from src.modules.data_pipeline.schemas.api_responses import (
    DemographicsData,
    EarthquakeHazardData,
    ExchangeRateData,
    FaultData,
    HousingPriceIndex,
    HousingPriceIndexData,
    HousingSaleData,
    MortgageRateData,
    ParcelData,
    ParcelDetailData,
    PopulationData,
)

__all__ = [
    "DemographicsData",
    "EarthquakeHazardData",
    "ExchangeRateData",
    "FaultData",
    "HousingPriceIndex",
    "HousingPriceIndexData",
    "HousingSaleData",
    "MortgageRateData",
    "ParcelData",
    "ParcelDetailData",
    "PopulationData",
]
