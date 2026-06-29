"""Payout Router — Choisit quel PSP exécute le payout"""
from enum import Enum
from typing import Dict, Any


class PayoutMethod(Enum):
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CASH_PICKUP = "cash_pickup"
    WALLET = "wallet"
    CARD_PUSH = "card_push"


class PayoutRouter:
    PSP_PAYOUT_CAPABILITIES = {
        "kora": {
            "name": "KoraPay",
            "methods": [PayoutMethod.MOBILE_MONEY, PayoutMethod.BANK_TRANSFER],
            "corridors": {
                "CM": {"currencies": ["XAF"], "methods": ["mobile_money", "bank_transfer"]},
                "NG": {"currencies": ["NGN"], "methods": ["mobile_money", "bank_transfer"]},
                "GH": {"currencies": ["GHS"], "methods": ["mobile_money", "bank_transfer"]},
            },
            "fees": {
                "mobile_money": {"percentage": 0.015, "fixed": 0},
                "bank_transfer": {"percentage": 0.010, "fixed": 200},
            },
            "avg_time_minutes": 3,
            "reliability": 0.97,
            "coverage": "africa",
        },
        "fincra": {
            "name": "Fincra",
            "methods": [PayoutMethod.MOBILE_MONEY, PayoutMethod.BANK_TRANSFER, 
                       PayoutMethod.CASH_PICKUP, PayoutMethod.CARD_PUSH],
            "corridors": {
                "NG": {"currencies": ["NGN"], "methods": ["mobile_money", "bank_transfer", "card_push"]},
                "GH": {"currencies": ["GHS"], "methods": ["mobile_money", "bank_transfer"]},
                "KE": {"currencies": ["KES"], "methods": ["mobile_money", "bank_transfer"]},
                "CI": {"currencies": ["XOF"], "methods": ["mobile_money", "bank_transfer"]},
                "ZA": {"currencies": ["ZAR"], "methods": ["bank_transfer"]},
                "US": {"currencies": ["USD"], "methods": ["bank_transfer", "card_push"]},
                "GB": {"currencies": ["GBP"], "methods": ["bank_transfer"]},
                "IN": {"currencies": ["INR"], "methods": ["bank_transfer", "cash_pickup"]},
                "FR": {"currencies": ["EUR"], "methods": ["bank_transfer"]},
            },
            "fees": {
                "mobile_money": {"percentage": 0.020, "fixed": 0},
                "bank_transfer": {"percentage": 0.015, "fixed": 300},
                "cash_pickup": {"percentage": 0.025, "fixed": 500},
                "card_push": {"percentage": 0.018, "fixed": 0},
            },
            "avg_time_minutes": 8,
            "reliability": 0.94,
            "coverage": "global",
        },
        "payoneer": {
            "name": "Payoneer",
            "methods": [PayoutMethod.WALLET, PayoutMethod.BANK_TRANSFER, PayoutMethod.CARD_PUSH],
            "corridors": {"GLOBAL": {"currencies": ["EUR", "USD", "GBP"], "methods": ["wallet", "bank_transfer", "card_push"]}},
            "fees": {
                "wallet": {"percentage": 0.005, "fixed": 0},
                "bank_transfer": {"percentage": 0.010, "fixed": 0},
                "card_push": {"percentage": 0.008, "fixed": 0},
            },
            "avg_time_minutes": 30,
            "reliability": 0.99,
            "coverage": "global",
        }
    }

    def route_payout(
        self, amount: float, currency: str,
        destination_country: str, destination_method: PayoutMethod,
        priority: str = "cost"
    ) -> Dict[str, Any]:
        candidates = []

        for psp_code, config in self.PSP_PAYOUT_CAPABILITIES.items():
            corridor = config["corridors"].get(destination_country)
            if not corridor and "GLOBAL" in config["corridors"]:
                corridor = config["corridors"]["GLOBAL"]
            if not corridor:
                continue
            if currency not in corridor["currencies"]:
                continue
            if destination_method.value not in corridor["methods"]:
                continue

            fee_config = config["fees"].get(destination_method.value, {"percentage": 0.03, "fixed": 0})
            total_fee = (amount * fee_config["percentage"]) + fee_config["fixed"]

            score = self._score_payout_option(psp_code, config, fee_config, amount, destination_country, priority)

            candidates.append({
                "psp": psp_code,
                "psp_name": config["name"],
                "method": destination_method.value,
                "fee_percentage": fee_config["percentage"],
                "fee_fixed": fee_config["fixed"],
                "total_fee": round(total_fee, 2),
                "estimated_time_minutes": config["avg_time_minutes"],
                "reliability": config["reliability"],
                "coverage": config["coverage"],
                "score": score,
            })

        if not candidates:
            return {"error": f"No PSP available for payout to {destination_country} in {currency}"}

        candidates.sort(key=lambda x: x["score"], reverse=True)

        return {
            "primary": candidates[0],
            "fallback": candidates[1] if len(candidates) > 1 else None,
            "all_options": candidates,
        }

    def _score_payout_option(self, psp: str, config: Dict, fee_config: Dict, amount: float, country: str, priority: str) -> float:
        fee_rate = fee_config["percentage"]
        time_score = max(0, 1 - (config["avg_time_minutes"] / 60))
        reliability = config["reliability"]
        cost_score = 1 - min(fee_rate * 10, 1)

        native_bonus = 10 if config["coverage"] == "africa" and country in ["CM", "NG", "GH"] else 0

        weights = {
            "cost": {"cost": 0.5, "speed": 0.2, "reliability": 0.3},
            "speed": {"cost": 0.2, "speed": 0.5, "reliability": 0.3},
            "reliability": {"cost": 0.2, "speed": 0.2, "reliability": 0.6},
        }

        w = weights.get(priority, weights["cost"])
        score = (cost_score * w["cost"] + time_score * w["speed"] + reliability * w["reliability"]) * 100 + native_bonus
        return round(score, 2)
