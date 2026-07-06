"""Payment service with Redis-backed idempotency lock. V45+ Production Correction."""

import hashlib
from decimal import Decimal
from datetime import datetime, timezone

import redis.asyncio as redis

from config.config import get_settings
from config.exceptions import PaymentError, ConflictError, CurrencyNotSupportedError
from config.security import verify_webhook_signature
from config.telemetry import payments_processed
from payment_hub.models import Transaction, PaymentStatus, PSPType
from payment_hub.psp_router import psp_router
from event_bus.event_schema import BaseEvent, EventType
from event_bus.redis_producer import event_producer

settings = get_settings()


class PaymentService:
    SUPPORTED_CURRENCIES = {
        "XOF", "XAF", "NGN", "KES", "GHS", "ZAR",
        "USD", "EUR", "GBP", "CAD", "AUD",
    }

    def __init__(self):
        self._redis = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_pool_size,
                decode_responses=True,
            )
        return self._redis

    def _generate_lock_id(self, user_id: str, amount: str, currency: str, timestamp: str) -> str:
        """V45: SHA256 stable lock ID for idempotency."""
        key = f"{user_id}:{amount}:{currency}:{timestamp}"
        return hashlib.sha256(key.encode()).hexdigest()

    async def _acquire_lock(self, lock_id: str, ttl_seconds: int = 300) -> bool:
        """Production Correction: Redis distributed lock instead of in-memory set()."""
        redis_client = await self._get_redis()
        # SET NX EX: set if not exists, with expiry
        acquired = await redis_client.set(f"payment_lock:{lock_id}", "1", nx=True, ex=ttl_seconds)
        return acquired is not None

    async def _release_lock(self, lock_id: str) -> None:
        redis_client = await self._get_redis()
        await redis_client.delete(f"payment_lock:{lock_id}")

    async def process_payment(
        self,
        user_id: str,
        amount: Decimal,
        currency: str,
        method: str = "card",
        region: str = "west_africa",
        metadata: dict | None = None,
    ) -> Transaction:
        if currency not in self.SUPPORTED_CURRENCIES:
            raise CurrencyNotSupportedError(f"Currency {currency} not supported")

        if amount <= 0:
            raise PaymentError("Amount must be greater than 0")

        timestamp = datetime.now(timezone.utc).isoformat()
        idempotency_key = self._generate_lock_id(
            str(user_id),
            str(amount),
            currency,
            timestamp[:10],
        )

        # Production Correction: Redis distributed lock (multi-pod safe)
        lock_acquired = await self._acquire_lock(idempotency_key, ttl_seconds=300)
        if not lock_acquired:
            raise ConflictError("Duplicate payment detected (already processing)")

        try:
            # Production Correction: Use PSP router instead of hardcoded Kora
            selected_psp = psp_router.select_psp(currency, method=method, region=region)

            transaction = Transaction(
                idempotency_key=idempotency_key,
                user_id=user_id,
                psp=selected_psp,
                amount=amount,
                currency=currency,
                status=PaymentStatus.PENDING,
                metadata=metadata or {},
            )

            event = BaseEvent(
                event_type=EventType.PAYMENT_INITIATED,
                payload={
                    "transaction_id": str(transaction.id),
                    "amount": str(amount),
                    "currency": currency,
                    "psp": selected_psp.value,
                    "user_id": str(user_id),
                    "status": "pending",
                },
            )
            await event_producer.publish(event)

            payments_processed.labels(
                psp=selected_psp.value,
                status="pending",
                currency=currency,
            ).inc()

            return transaction

        finally:
            await self._release_lock(idempotency_key)

    async def verify_webhook(self, psp: str, payload: bytes, signature: str) -> bool:
        secrets_map = {
            "kora": settings.kora_webhook_secret,
            "fincra": settings.fincra_webhook_secret,
        }
        secret = secrets_map.get(psp)
        if not secret:
            return False
        return verify_webhook_signature(payload, signature, secret)

    async def close(self):
        if self._redis:
            await self._redis.close()


payment_service = PaymentService()
