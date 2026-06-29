"""Collection Router — Choisit quel PSP collecte les fonds"""
from enum import Enum
from typing import Dict, Any, Optional, List


class CollectionMethod(Enum):
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    WALLET = "wallet"


class CollectionRouter:
    PSP_COLLECTION_CAPABILITIES = {
        "kora": {
            "name": "KoraPay",
            "methods": [CollectionMethod.MOBILE_MONEY, CollectionMethod.BANK_TRANSFER],
            "countries": ["CM", "NG", "GH"],
            "currencies": ["XAF", "NGN", "GHS"],
            "fees": {
                "mobile_money": {"percentage": 0.025, "fixed": 0},
                "bank_transfer": {"percentage": 0.020, "fixed": 500},
            },
            "avg_time_minutes": 2,
            "reliability": 0.97,
        },
        "fincra": {
            "name": "Fincra",
            "methods": [CollectionMethod.MOBILE_MONEY, CollectionMethod.BANK_TRANSFER, CollectionMethod.CARD],
            "countries": ["NG", "GH", "KE", "CI", "ZA", "US", "GB", "IN"],
            "currencies": ["NGN", "GHS", "KES", "XOF", "XAF", "ZAR", "USD", "GBP", "EUR", "INR"],
            "fees": {
                "mobile_money": {"percentage": 0.030, "fixed": 0},
                "bank_transfer": {"percentage": 0.025, "fixed": 300},
                "card": {"percentage": 0.035, "fixed": 0},
            },
            "avg_time_minutes": 5,
            "reliability": 0.94,
        },
        "payoneer": {
            "name": "Payoneer",
            "methods": [CollectionMethod.WALLET, CollectionMethod.BANK_TRANSFER, CollectionMethod.CARD],
            "countries": ["GLOBAL"],
            "currencies": ["EUR", "USD", "GBP"],
            "fees": {
                "wallet": {"percentage": 0.010, "fixed": 0},
                "bank_transfer": {"percentage": 0.015, "fixed": 0},
                "card": {"percentage": 0.029, "fixed": 0},
            },
            "avg_time_minutes": 10,
            "reliability": 0.99,
        }
    }

    def route_collection(
        self, amount: float, currency: str,
        source_country: str, source_method: CollectionMethod,
        priority: str = "cost"
    ) -> Dict[str, Any]:
        candidates = []

        for psp_code, config in self.PSP_COLLECTION_CAPABILITIES.items():
            if source_country not in config["countries"] and "GLOBAL" not in config["countries"]:
                continue
            if currency not in config["currencies"]:
                continue
            if source_method not in config["methods"]:
                continue

            fee_config = config["fees"].get(source_method.value, {"percentage": 0.05, "fixed": 0})
            total_fee = (amount * fee_config["percentage"]) + fee_config["fixed"]

            score = self._score_option(psp_code, config, fee_config, amount, priority)

            candidates.append({
                "psp": psp_code,
                "psp_name": config["name"],
                "method": source_method.value,
                "fee_percentage": fee_config["percentage"],
                "fee_fixed": fee_config["fixed"],
                "total_fee": round(total_fee, 2),
                "estimated_time_minutes": config["avg_time_minutes"],
                "reliability": config["reliability"],
                "score": score,
            })

        if not candidates:
            return {"error": "No PSP available for this corridor"}

        candidates.sort(key=lambda x: x["score"], reverse=True)

        return {
            "primary": candidates[0],
            "fallback": candidates[1] if len(candidates) > 1 else None,
            "all_options": candidates,
        }

    def _score_option(self, psp: str, config: Dict, fee_config: Dict, amount: float, priority: str) -> float:
        fee_rate = fee_config["percentage"]
        time_score = max(0, 1 - (config["avg_time_minutes"] / 60))
        reliability = config["reliability"]
        cost_score = 1 - min(fee_rate * 10, 1)

        weights = {
            "cost": {"cost": 0.5, "speed": 0.2, "reliability": 0.3},
            "speed": {"cost": 0.2, "speed": 0.5, "reliability": 0.3},
            "reliability": {"cost": 0.2, "speed": 0.2, "reliability": 0.6},
        }

        w = weights.get(priority, weights["cost"])
        score = (cost_score * w["cost"] + time_score * w["speed"] + reliability * w["reliability"]) * 100

        if psp == "kora" and config["avg_time_minutes"] <= 5:
            score += 5

        return round(score, 2)
