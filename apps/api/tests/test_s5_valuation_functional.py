"""
Sprint S5 Functional Test Suite — AI Valuation (P0 & P1)

Scenarios:
- S5-TC-001: Happy Path (P0)
- S5-TC-002: Quota Exceeded - Starter (P0)
- S5-TC-004: Elite Plan - Unlimited (P0)
- S5-TC-007: Validation - net_sqm = 0 (P1)
- S5-TC-017: Anomaly Detection - Normal (P1)
- S5-TC-018: Anomaly Detection - High (P1)
- S5-TC-024: Comparable Search (P1)
- S5-TC-031: GET Valuation - Not Found (P1)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from src.core.exceptions import QuotaExceededError
from src.modules.valuations.anomaly_service import AnomalyResult

# ================================================================
# Mock Data & Helpers
# ================================================================

VALUATION_PAYLOAD = {
    "district": "Kadikoy",
    "neighborhood": "Caferaga",
    "property_type": "Daire",
    "net_sqm": 120,
    "gross_sqm": 140,
    "room_count": 3,
    "living_room_count": 1,
    "floor": 5,
    "total_floors": 10,
    "building_age": 5,
    "heating_type": "Dogalgaz Kombi",
}

MOCK_JWT = "mock_jwt_token"


@pytest.mark.asyncio
class TestValuationS5Functional:
    """S5 Sprinti P0 ve P1 fonksiyonel test senaryolari."""

    @patch("src.modules.valuations.router._check_and_get_quota")
    @patch("src.modules.valuations.inference_service.InferenceService.get_instance")
    @patch("src.modules.valuations.comparable_service.ComparableService.find_comparables_enriched")
    @patch("src.modules.valuations.router.check_price_anomaly")
    @patch("src.modules.valuations.router._increment_usage")
    async def test_s5_tc_001_happy_path(
        self,
        mock_increment,
        mock_anomaly,
        mock_comparables,
        mock_inference,
        mock_quota,
        client: AsyncClient,
    ) -> None:
        """S5-TC-001: Basarili Değerleme (P0)."""
        # Given: Starter plan, kota musait
        mock_quota.return_value = ("starter", 50, 49)
        
        # Mock Inference
        mock_inference_instance = MagicMock()
        mock_inference_instance.predict = AsyncMock(return_value={
            "estimated_price": 6000000,
            "min_price": 5000000,
            "max_price": 7000000,
            "confidence": 0.85,
            "price_per_sqm": 50000,
            "latency_ms": 120,
            "model_version": "v1",
            "prediction_id": str(uuid.uuid4()),
        })
        mock_inference.return_value = mock_inference_instance

        # Mock Comparables
        mock_comparables.return_value = [
            {
                "property_id": str(uuid.uuid4()),
                "distance_km": 0.5,
                "price_diff_percent": 2.5,
                "similarity_score": 92.0,
                "address": "Moda, Kadikoy",
                "price": 6200000,
                "sqm": 125,
                "rooms": "3+1"
            }
        ]

        # Mock Anomaly
        mock_anomaly.return_value = AnomalyResult(is_anomaly=False, z_score=0.5)

        # When: POST /api/v1/valuations
        response = await client.post(
            "/api/v1/valuations",
            json=VALUATION_PAYLOAD,
            headers={"Authorization": f"Bearer {MOCK_JWT}"}
        )

        # Then: HTTP 200
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["estimated_price"] == 6000000
        assert data["quota_remaining"] == 0
        assert len(data["comparables"]) == 1
        assert data["anomaly_warning"] is None
        
        # Verify calls
        mock_quota.assert_called_once()
        mock_increment.assert_called_once()

    @patch("src.modules.valuations.router._check_and_get_quota")
    async def test_s5_tc_002_quota_exceeded_starter(
        self,
        mock_quota,
        client: AsyncClient,
    ) -> None:
        """S5-TC-002: Kota Asimi — Starter Plan (P0)."""
        # Given: Starter plan, kota 50/50 dolu
        mock_quota.side_effect = QuotaExceededError(limit=50, used=50, plan="starter")

        # When: POST /api/v1/valuations
        response = await client.post(
            "/api/v1/valuations",
            json=VALUATION_PAYLOAD,
            headers={"Authorization": f"Bearer {MOCK_JWT}"}
        )

        # Then: HTTP 429
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert data["type"] == "quota_exceeded"
        assert data["limit"] == 50
        assert data["used"] == 50

    @patch("src.modules.valuations.router._check_and_get_quota")
    @patch("src.modules.valuations.inference_service.InferenceService.get_instance")
    async def test_s5_tc_004_elite_unlimited(
        self,
        mock_inference,
        mock_quota,
        client: AsyncClient,
    ) -> None:
        """S5-TC-004: Elite Plan — Sinirsiz Kota (P0)."""
        # Given: Elite plan
        mock_quota.return_value = ("elite", -1, 1000)
        
        # Mock Inference (minimal)
        mock_inference_instance = MagicMock()
        mock_inference_instance.predict = AsyncMock(return_value={
            "estimated_price": 6000000,
            "prediction_id": str(uuid.uuid4()),
            "latency_ms": 10
        })
        mock_inference.return_value = mock_inference_instance

        # When: POST /api/v1/valuations
        response = await client.post(
            "/api/v1/valuations",
            json=VALUATION_PAYLOAD,
            headers={"Authorization": f"Bearer {MOCK_JWT}"}
        )

        # Then: HTTP 200, quota_remaining = -1
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["quota_remaining"] == -1

    async def test_s5_tc_007_validation_net_sqm_zero(
        self,
        client: AsyncClient,
    ) -> None:
        """S5-TC-007: Validation — net_sqm = 0 (P1)."""
        # Given: net_sqm = 0
        payload = VALUATION_PAYLOAD.copy()
        payload["net_sqm"] = 0

        # When: POST /api/v1/valuations
        response = await client.post(
            "/api/v1/valuations",
            json=payload,
            headers={"Authorization": f"Bearer {MOCK_JWT}"}
        )

        # Then: HTTP 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("src.modules.valuations.anomaly_service.check_price_anomaly")
    async def test_s5_tc_018_anomaly_detected_high(
        self,
        mock_anomaly,
        client: AsyncClient,
    ) -> None:
        """S5-TC-018: Anomali Var — Yuksek Fiyat (P1)."""
        # Import moved inside to avoid circular or missing dependencies during discovery
        from src.modules.valuations.anomaly_service import AnomalyResult
        
        # Given: Anomali sonucu yuksek
        mock_anomaly.return_value = AnomalyResult(
            is_anomaly=True, 
            z_score=2.5, 
            anomaly_reason="yukarida sapma"
        )
        
        # We need to mock other things to reach anomaly check
        with (
            patch("src.modules.valuations.router._check_and_get_quota", return_value=("starter", 50, 0)),
            patch("src.modules.valuations.inference_service.InferenceService.get_instance") as mock_inf,
            patch("src.modules.valuations.comparable_service.ComparableService.find_comparables_enriched", return_value=[]),
            patch("src.modules.valuations.router._increment_usage"),
        ):
            
            mock_inf_inst = MagicMock()
            mock_inf_inst.predict = AsyncMock(return_value={"estimated_price": 9000000, "prediction_id": "123", "latency_ms": 1})
            mock_inf.return_value = mock_inf_inst

            # When: POST /api/v1/valuations
            response = await client.post(
                "/api/v1/valuations",
                json=VALUATION_PAYLOAD,
                headers={"Authorization": f"Bearer {MOCK_JWT}"}
            )

            # Then: Response contains anomaly_warning
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["anomaly_warning"] == "yukarida sapma"

    @patch("src.modules.valuations.comparable_service.ComparableService.find_comparables")
    @patch("src.modules.valuations.comparable_service.ComparableService.get_area_stats")
    async def test_s5_tc_024_comparable_search(
        self,
        mock_stats,
        mock_find,
        client: AsyncClient,
    ) -> None:
        """S5-TC-024: POST /comparables — Basarili Emsal Aramasi (P1)."""
        # Given
        mock_find.return_value = [{"property_id": "1", "similarity_score": 95.0}]
        mock_stats.return_value = {"avg_price": 50000}

        # When: POST /api/v1/valuations/comparables
        response = await client.post(
            "/api/v1/valuations/comparables",
            json={
                "district": "Kadikoy",
                "property_type": "Daire",
                "net_sqm": 120,
                "room_count": 3,
                "building_age": 5,
                "lat": 41.0,
                "lon": 29.0
            },
            headers={"Authorization": f"Bearer {MOCK_JWT}"}
        )

        # Then: HTTP 200
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "comparables" in data
        assert data["total_found"] == 1

    async def test_s5_tc_031_get_valuation_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """S5-TC-031: GET /valuations/{id} — Not Found (P1)."""
        # Given: Random UUID
        val_id = uuid.uuid4()

        # When: GET /api/v1/valuations/{id}
        response = await client.get(
            f"/api/v1/valuations/{val_id}",
            headers={"Authorization": f"Bearer {MOCK_JWT}"}
        )

        # Then: HTTP 404
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"].startswith("Degerleme")
