"""Seed Database — PSP Providers & Settlement Positions"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, init_db
from app.models import PSPProvider, SettlementPosition


async def seed_psp_providers(db: AsyncSession):
    providers = [
        PSPProvider(
            name="KoraPay",
            psp_code="kora",
            status="active",
            health_score=98,
            success_rate_7d=0.97,
            avg_latency_ms=450,
            circuit_state="closed",
            current_exposure=450000000,
            exposure_limit=1000000000,
            daily_limit=100000000,
            supported_countries=["CM", "NG", "GH", "KE", "CI", "EG", "TZ"],
            supported_currencies=["XAF", "NGN", "GHS", "KES", "XOF", "EGP", "TZS"],
            supported_methods=["mobile_money", "bank_transfer", "card"],
        ),
        PSPProvider(
            name="Fincra",
            psp_code="fincra",
            status="active",
            health_score=94,
            success_rate_7d=0.94,
            avg_latency_ms=800,
            circuit_state="closed",
            current_exposure=280000000,
            exposure_limit=800000000,
            daily_limit=80000000,
            supported_countries=["NG", "GH", "KE", "CI", "ZA", "US", "GB", "IN", "FR"],
            supported_currencies=["NGN", "GHS", "KES", "XOF", "XAF", "ZAR", "USD", "GBP", "EUR", "INR"],
            supported_methods=["mobile_money", "bank_transfer", "card", "cash_pickup"],
        ),
        PSPProvider(
            name="Payoneer",
            psp_code="payoneer",
            status="active",
            health_score=99,
            success_rate_7d=0.99,
            avg_latency_ms=1200,
            circuit_state="closed",
            current_exposure=50000000,
            exposure_limit=500000000,
            daily_limit=50000000,
            supported_countries=["GLOBAL"],
            supported_currencies=["USD", "EUR", "GBP"],
            supported_methods=["wallet", "bank_transfer", "card_push"],
        ),
    ]

    for provider in providers:
        db.add(provider)

    await db.commit()
    print("✅ PSP Providers seeded")


async def seed_settlement_positions(db: AsyncSession):
    positions = [
        SettlementPosition(currency="XAF", available_balance=500000000, pending_incoming=25000000, pending_outgoing=15000000),
        SettlementPosition(currency="NGN", available_balance=200000000, pending_incoming=10000000, pending_outgoing=5000000),
        SettlementPosition(currency="USD", available_balance=500000, pending_incoming=25000, pending_outgoing=10000),
        SettlementPosition(currency="EUR", available_balance=300000, pending_incoming=15000, pending_outgoing=5000),
        SettlementPosition(currency="GHS", available_balance=80000000, pending_incoming=4000000, pending_outgoing=2000000),
    ]

    for pos in positions:
        db.add(pos)

    await db.commit()
    print("✅ Settlement Positions seeded")


async def main():
    await init_db()
    async with async_session() as db:
        await seed_psp_providers(db)
        await seed_settlement_positions(db)
    print("🌱 Database seeded successfully")


if __name__ == "__main__":
    asyncio.run(main())
