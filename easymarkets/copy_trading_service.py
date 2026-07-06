"""Copy trading with self-follow protection. V45 Correction."""

from decimal import Decimal

from config.config import get_settings
from config.exceptions import SelfFollowError, InvalidAllocationError
from easymarkets.models import CopyTrade, CopyTradeStatus


class CopyTradingService:
    def __init__(self):
        settings = get_settings()
        self.max_allocation = settings.max_copy_allocation_percent

    async def start_copy_trading(
        self,
        follower_id: str,
        leader_id: str,
        allocation_percent: int,
        max_drawdown: Decimal | None = None,
    ) -> CopyTrade:
        # V45 Correction: Prevent self-following
        if follower_id == leader_id:
            raise SelfFollowError()

        # V45 Correction: Allocation must be > 0
        if allocation_percent <= 0:
            raise InvalidAllocationError("Allocation must be greater than 0%")

        if allocation_percent > self.max_allocation:
            raise InvalidAllocationError(f"Allocation cannot exceed {self.max_allocation}%")

        return CopyTrade(
            follower_id=follower_id,
            leader_id=leader_id,
            allocation_percent=allocation_percent,
            max_drawdown=max_drawdown or Decimal("20.0"),
            status=CopyTradeStatus.ACTIVE,
        )


copy_trading_service = CopyTradingService()
