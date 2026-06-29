"""Payoneer Connector — Fallback Global"""
import httpx
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.telemetry import traced


class PayoneerConnector:
    BASE_URL = "https://api.payoneer.com/v4"

    SUPPORTED_COUNTRIES = ["GLOBAL"]
    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP"]

    def __init__(self):
        self.client_id = settings.PAYONEER_CLIENT_ID.get_secret_value()
        self.client_secret = settings.PAYONEER_CLIENT_SECRET.get_secret_value()
        self.access_token = None

    async def _get_token(self) -> str:
        if self.access_token:
            return self.access_token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            data = response.json()
            self.access_token = data["access_token"]
            return self.access_token

    @traced(name="payoneer.health_check")
    async def health_check(self) -> Dict[str, Any]:
        try:
            token = await self._get_token()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/ping",
                    headers={"Authorization": f"Bearer {token}"}
                )
                return {"status": "healthy" if response.status_code == 200 else "degraded"}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    @traced(name="payoneer.payout")
    async def payout(
        self, payee_id: str, amount: float,
        currency: str, description: str,
    ) -> Dict[str, Any]:
        token = await self._get_token()
        payload = {
            "payee_id": payee_id,
            "amount": amount,
            "currency": currency,
            "description": description,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/payouts",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            response.raise_for_status()
            return response.json()
