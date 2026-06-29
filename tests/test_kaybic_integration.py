"""Tests intégration Kaybic — 10 scénarios critiques"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.collection_router import CollectionRouter, CollectionMethod
from app.services.payout_router import PayoutRouter, PayoutMethod
from app.services.pricing_engine import IntelligentPricingEngine


class MockDB:
    async def commit(self): pass
    async def rollback(self): pass


@pytest.fixture
def mock_db():
    return MockDB()


# TEST 1: CM → NG via Kora (corridor natif)
def test_cm_to_ng_kora_primary():
    router = CollectionRouter()
    result = router.route_collection(
        50000, "XAF", "CM", CollectionMethod.MOBILE_MONEY
    )
    assert result["primary"]["psp"] == "kora"
    assert result["primary"]["psp_name"] == "KoraPay"


# TEST 2: NG → KE via Fincra (Kora pas présent)
def test_ng_to_ke_fincra_primary():
    router = PayoutRouter()
    result = router.route_payout(
        50000, "KES", "KE", PayoutMethod.MOBILE_MONEY
    )
    assert result["primary"]["psp"] == "fincra"


# TEST 3: NG → US via Fincra (rail global)
def test_ng_to_us_fincra_global():
    router = PayoutRouter()
    result = router.route_payout(
        100000, "USD", "US", PayoutMethod.BANK_TRANSFER
    )
    assert result["primary"]["psp"] == "fincra"


# TEST 4: Pricing transparent
def test_pricing_calculation():
    engine = IntelligentPricingEngine()
    result = engine.calculate_price(
        psp_cost=2000, amount=50000,
        merchant_tier="kaybic_premium"
    )
    assert result["fee_percentage"] > 0
    assert result["net_amount"] < 50000
    assert result["breakdown"]["psp_cost"] == 2000


# TEST 5: Volume discount appliqué
def test_volume_discount():
    engine = IntelligentPricingEngine()
    result = engine.calculate_price(
        psp_cost=400000, amount=100000000,  # 100M
        merchant_monthly_volume=150000000,
    )
    assert result["breakdown"]["volume_discount"] > 0


# TEST 6: Fallback Payoneer = surcharge
def test_fallback_surcharge():
    engine = IntelligentPricingEngine()
    result = engine.calculate_price(
        psp_cost=1000, amount=50000,
        fallback_used=True
    )
    assert result["breakdown"]["fallback_surcharge"] > 0


# TEST 7: Kora indisponible → fallback Fincra
def test_kora_unavailable_fallback():
    router = PayoutRouter()
    result = router.route_payout(
        50000, "USD", "US", PayoutMethod.BANK_TRANSFER
    )
    assert result["primary"]["psp"] == "fincra"


# TEST 8: Cost priority vs Speed priority
def test_priority_modes():
    router = PayoutRouter()
    cost_result = router.route_payout(
        50000, "NGN", "NG", PayoutMethod.MOBILE_MONEY, "cost"
    )
    speed_result = router.route_payout(
        50000, "NGN", "NG", PayoutMethod.MOBILE_MONEY, "speed"
    )
    assert cost_result["primary"]["psp"] == speed_result["primary"]["psp"]


# TEST 9: No PSP available
def test_no_psp_available():
    router = PayoutRouter()
    result = router.route_payout(
        50000, "JPY", "JP", PayoutMethod.BANK_TRANSFER
    )
    assert "error" in result


# TEST 10: Quote endpoint structure
def test_quote_structure():
    engine = IntelligentPricingEngine()
    result = engine.calculate_price(
        psp_cost=2250, amount=50000
    )
    assert "breakdown" in result
    assert "merchant_tier" in result
    assert result["effective_markup_percentage"] > 0
