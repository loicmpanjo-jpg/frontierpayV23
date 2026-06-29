"""KoraPay Connector — PSP Principal Afrique
Documentation: https://docs.korapay.com
Kora = Cameroun, Nigeria, Ghana, Kenya, Côte d'Ivoire, Egypte, Tanzanie
"""
import httpx
import hmac
import hashlib
import json
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.telemetry import traced


class KoraConnector:
    BASE_URL = "https://api.korapay.com"
    SANDBOX_URL = "https://sandbox.api.korapay.com"

    SUPPORTED_COUNTRIES = ["CM", "NG", "GH", "KE", "CI", "EG", "TZ"]
    SUPPORTED_CURRENCIES = ["XAF", "NGN", "GHS", "KES", "XOF", "EGP", "TZS"]

    FEE_STRUCTURE = {
        "mobile_money": {"payin": 0.025, "payout": 0.015},
        "bank_transfer": {"payin": 0.020, "payout": 0.010},
        "card": {"payin": 0.035, "payout": None},
    }

    def __init__(self):
        self.public_key = settings.KORA_PUBLIC_KEY.get_secret_value()
        self.secret_key = settings.KORA_SECRET_KEY.get_secret_value()
        self.headers = {
            "Authorization": f"Bearer {self.public_key}",
            "Content-Type": "application/json",
        }

    @traced(name="kora.health_check", attributes={"psp": "kora"})
    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/merchant/api/v1/misc/banks/NG",
                    headers=self.headers
                )
                if response.status_code == 200:
                    return {"status": "healthy", "latency_ms": response.elapsed.total_seconds() * 1000}
                return {"status": "degraded", "code": response.status_code}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    @traced(name="kora.get_balances")
    async def get_balances(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/merchant/api/v1/balances",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @traced(name="kora.initialize_charge")
    async def initialize_charge(
        self, amount: float, currency: str,
        customer_email: str, customer_name: str,
        reference: str, redirect_url: Optional[str] = None,
        payment_type: str = "mobile_money",
        phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "customer": {
                "name": customer_name,
                "email": customer_email,
            },
            "payment_type": payment_type,
        }
        if redirect_url:
            payload["redirect_url"] = redirect_url
        if phone:
            payload["customer"]["phone"] = phone

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/merchant/api/v1/charges/initialize",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    @traced(name="kora.verify_charge")
    async def verify_charge(self, reference: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/merchant/api/v1/charges/{reference}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @traced(name="kora.initiate_payout")
    async def initiate_payout(
        self, reference: str, amount: float,
        currency: str, beneficiary: Dict[str, Any],
        narration: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "reference": reference,
            "amount": amount,
            "currency": currency,
            "beneficiary": beneficiary,
        }
        if narration:
            payload["narration"] = narration

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/merchant/api/v1/transactions/disburse",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    @traced(name="kora.query_payout")
    async def query_payout(self, reference: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/merchant/api/v1/transactions/{reference}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @traced(name="kora.get_banks")
    async def get_banks(self, country_code: str = "NG") -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/merchant/api/v1/misc/banks/{country_code}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(
            self.secret_key.encode(), payload, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = payload.get("event", "")
        data = payload.get("data", {})
        return {
            "event": event,
            "reference": data.get("reference"),
            "status": data.get("status"),
            "amount": data.get("amount"),
            "currency": data.get("currency"),
            "payment_reference": data.get("payment_reference"),
            "raw": payload,
        }
