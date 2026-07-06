"""Revenue distribution: 35% Ads, 50% Creator, 15% Platform."""

from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

from config.config import get_settings
from config.telemetry import revenue_split


@dataclass
class RevenueSplit:
    ads: Decimal
    creator: Decimal
    platform: Decimal
    total: Decimal


class RevenueEngine:
    def __init__(self):
        settings = get_settings()
        self.ads_rate = Decimal(str(settings.ads_share))
        self.creator_rate = Decimal(str(settings.creator_share))
        self.platform_rate = Decimal(str(settings.platform_share))

    def calculate_split(self, gross_amount: Decimal) -> RevenueSplit:
        quantize = Decimal("0.01")

        ads = (gross_amount * self.ads_rate).quantize(quantize, rounding=ROUND_HALF_UP)
        creator = (gross_amount * self.creator_rate).quantize(quantize, rounding=ROUND_HALF_UP)
        platform = (gross_amount * self.platform_rate).quantize(quantize, rounding=ROUND_HALF_UP)

        total_split = ads + creator + platform
        if total_split != gross_amount:
            diff = gross_amount - total_split
            if creator >= ads and creator >= platform:
                creator += diff
            elif ads >= platform:
                ads += diff
            else:
                platform += diff

        revenue_split.labels(recipient_type="ads").inc(float(ads))
        revenue_split.labels(recipient_type="creator").inc(float(creator))
        revenue_split.labels(recipient_type="platform").inc(float(platform))

        return RevenueSplit(
            ads=ads.quantize(quantize),
            creator=creator.quantize(quantize),
            platform=platform.quantize(quantize),
            total=gross_amount,
        )


revenue_engine = RevenueEngine()
