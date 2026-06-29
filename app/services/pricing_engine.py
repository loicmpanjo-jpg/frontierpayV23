"""Intelligent Pricing Engine — Notre marge sur le coût PSP"""
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class PricingTier:
    name: str
    base_markup_percentage: float
    volume_discount_threshold: float
    volume_discount: float
    risk_premium: float


class IntelligentPricingEngine:
    PRICING_TIERS = {
        "kaybic_premium": PricingTier(
            name="Kaybic Premium Partner",
            base_markup_percentage=0.005,
            volume_discount_threshold=100_000_000,
            volume_discount=0.002,
            risk_premium=0.003,
        ),
        "standard": PricingTier(
            name="Standard",
            base_markup_percentage=0.008,
            volume_discount_threshold=50_000_000,
            volume_discount=0.001,
            risk_premium=0.005,
        ),
    }

    SURCHARGES = {
        "speed_premium": 0.002,
        "fallback_payoneer": 0.005,
        "weekend": 0.001,
        "high_amount": -0.001,
    }

    def calculate_price(
        self, psp_cost: float, amount: float,
        merchant_tier: str = "kaybic_premium",
        merchant_monthly_volume: float = 0,
        risk_score: float = 50,
        speed_required_minutes: int = 60,
        fallback_used: bool = False,
        is_weekend: bool = False,
    ) -> Dict[str, Any]:
        tier = self.PRICING_TIERS.get(merchant_tier, self.PRICING_TIERS["standard"])

        markup = amount * tier.base_markup_percentage

        volume_discount = 0
        if merchant_monthly_volume >= tier.volume_discount_threshold:
            volume_discount = amount * tier.volume_discount
            markup -= volume_discount

        risk_premium = 0
        if risk_score > 70:
            risk_premium = amount * tier.risk_premium
            markup += risk_premium

        speed_premium = 0
        if speed_required_minutes < 60:
            speed_premium = amount * self.SURCHARGES["speed_premium"]
            markup += speed_premium

        fallback_surcharge = 0
        if fallback_used:
            fallback_surcharge = amount * self.SURCHARGES["fallback_payoneer"]
            markup += fallback_surcharge

        weekend_surcharge = 0
        if is_weekend:
            weekend_surcharge = amount * self.SURCHARGES["weekend"]
            markup += weekend_surcharge

        high_amount_discount = 0
        if amount > 1_000_000:
            high_amount_discount = amount * self.SURCHARGES["high_amount"]
            markup += high_amount_discount

        total_fee = psp_cost + markup

        return {
            "amount": amount,
            "psp_cost": round(psp_cost, 2),
            "frontierpay_markup": round(markup, 2),
            "total_fee": round(total_fee, 2),
            "net_amount": round(amount - total_fee, 2),
            "fee_percentage": round(total_fee / amount * 100, 2),
            "breakdown": {
                "psp_cost": round(psp_cost, 2),
                "base_markup": round(amount * tier.base_markup_percentage, 2),
                "volume_discount": round(volume_discount, 2),
                "risk_premium": round(risk_premium, 2),
                "speed_premium": round(speed_premium, 2),
                "fallback_surcharge": round(fallback_surcharge, 2),
                "weekend_surcharge": round(weekend_surcharge, 2),
                "high_amount_discount": round(high_amount_discount, 2),
            },
            "merchant_tier": tier.name,
            "effective_markup_percentage": round(markup / amount * 100, 3),
        }
