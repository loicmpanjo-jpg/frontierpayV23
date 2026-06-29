"""Fincra Connector — Collection + Payout Global
Basé sur documentation officielle: docs.fincra.com
Fincra = Afrique + Amérique + Asie + Europe
"""
import httpx
import hmac
import hashlib
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.telemetry import traced


class FincraConnector:
    BASE_URL = "https://api.fincra.com"
    SANDBOX_URL = "https://sandboxapi.fincra.com"

    SUPPORTED_COUNTRIES = [
        "NG", "GH", "KE", "CI", "ZA", "UG", "TZ", "ZM",
        "US", "GB", "CA", "IN",
    ]
    SUPPORTED_CURRENCIES = [
        "NGN", "GHS", "KES", "XOF", "XAF", "ZAR", "UGX", "TZS", "ZMW", "EGP",
        "USD", "EUR", "GBP", "CAD",
        "USDT", "USDC", "CNGN",
    ]

    FEE_STRUCTURE = {
        "mobile_money": {"payin": 0.030, "payout": 0.020},
        "bank_transfer": {"payin": 0.025, "payout": 0.015},
        "card": {"payin": 0.035, "payout": None},
        "crypto": {"payin": 0.010, "payout": 0.005},
    }

    def __init__(self):
        self.api_key = settings.FINCRA_API_KEY.get_secret_value()
        self.secret_key = settings.FINCRA_SECRET_KEY.get_secret_value()
        self.headers = {
            "api-key": self.api_key,
            "secret-key": self.secret_key,
            "Content-Type": "application/json",
        }

    @traced(name="fincra.health_check", attributes={"psp": "fincra"})
    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/profile/business",
                    headers=self.headers
                )
                if response.status_code == 200:
                    return {"status": "healthy", "latency_ms": response.elapsed.total_seconds() * 1000}
                return {"status": "degraded", "code": response.status_code}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    @traced(name="fincra.get_balances")
    async def get_balances(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/wallets/balances",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @traced(name="fincra.initialize_checkout")
    async def initialize_checkout(
        self, amount: float, currency: str,
        customer_name: str, customer_email: str,
        reference: str, redirect_url: Optional[str] = None,
        channels: Optional[list] = None,
    ) -> Dict[str, Any]:
        payload = {
            "amount": amount, "currency": currency,
            "customer": {"name": customer_name, "email": customer_email},
            "reference": reference,
        }
        if redirect_url: payload["redirectUrl"] = redirect_url
        if channels: payload["paymentMethods"] = channels

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/checkout/payments",
                headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()

    @traced(name="fincra.generate_quote")
    async def generate_quote(
        self, source_currency: str,
        destination_currency: str, amount: float,
    ) -> Dict[str, Any]:
        payload = {
            "sourceCurrency": source_currency,
            "destinationCurrency": destination_currency,
            "amount": amount,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/quotes",
                headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()

    @traced(name="fincra.initiate_payout")
    async def initiate_payout(
        self, reference: str, amount: float,
        currency: str, destination_currency: str,
        payment_destination: str,
        beneficiary: Dict[str, Any],
        quote_reference: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "reference": reference, "amount": amount,
            "currency": currency,
            "destinationCurrency": destination_currency,
            "paymentDestination": payment_destination,
            "beneficiary": beneficiary,
        }
        if quote_reference: payload["quoteReference"] = quote_reference
        if description: payload["description"] = description

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/payouts",
                headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()

    @traced(name="fincra.query_payout")
    async def query_payout(self, reference: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/payouts/{reference}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(
            self.secret_key.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": payload.get("event", ""),
            "reference": payload.get("data", {}).get("reference"),
            "status": payload.get("data", {}).get("status"),
            "amount": payload.get("data", {}).get("amount"),
            "currency": payload.get("data", {}).get("currency"),
            "raw": payload,
        }
