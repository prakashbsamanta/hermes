"""Volume-Aware Execution Handler for the Event-Driven Backtest Engine.

Replaces MockExecutionHandler with realistic order matching that considers:
- Bar volume for partial fills
- Slippage modeling based on order size vs available volume
- Per-unit commission calculation
"""

import logging

from engine.event_bus import EventBus
from engine.events import FillEvent, MarketEvent, OrderEvent

logger = logging.getLogger(__name__)


class VolumeAwareExecutionHandler:
    """Execution handler that models realistic order matching.

    Features:
    - Volume participation rate: limits order fill to a fraction of bar volume
    - Impact-aware slippage: larger orders relative to volume incur more slippage
    - Partial fills: orders exceeding available volume are partially filled
    - Commission: per-unit or percentage commission modeling
    """

    def __init__(
        self,
        bus: EventBus,
        slippage: float = 0.001,
        commission: float = 0.0,
        max_participation_rate: float = 0.10,
    ):
        """Initialize the execution handler.

        Args:
            bus: EventBus for subscribing/publishing events
            slippage: Base slippage as a fraction (0.001 = 0.1%)
            commission: Commission per unit (e.g., 0.01 per share)
            max_participation_rate: Maximum fraction of bar volume
                                    that an order can consume (0.0-1.0)
        """
        self.bus = bus
        self.slippage = slippage
        self.commission = commission
        self.max_participation_rate = max_participation_rate

        # Track latest bar data
        self.last_price: float = 0.0
        self.last_volume: float = 0.0
        self.last_high: float = 0.0
        self.last_low: float = 0.0

        # Subscribe to events
        self.bus.subscribe(OrderEvent, self.on_order)  # type: ignore
        self.bus.subscribe(MarketEvent, self.on_bar)  # type: ignore

        # Statistics
        self.total_orders = 0
        self.total_fills = 0
        self.total_partial_fills = 0
        self.total_rejected = 0

    def on_bar(self, event: MarketEvent) -> None:
        """Update latest market data for order matching."""
        self.last_price = event.close
        self.last_volume = event.volume
        self.last_high = event.high
        self.last_low = event.low

    def _calculate_fill_quantity(self, requested_qty: float) -> float:
        """Calculate fillable quantity based on volume constraints.

        Returns:
            Actual quantity that can be filled (may be less than requested)
        """
        if self.last_volume <= 0:
            # No volume data — fill full quantity (fallback)
            return requested_qty

        max_fill = self.last_volume * self.max_participation_rate
        return min(requested_qty, max(1.0, max_fill))

    def _calculate_slippage(
        self,
        base_price: float,
        fill_qty: float,
        direction: str,
    ) -> float:
        """Calculate price impact based on order size vs volume.

        Larger orders relative to bar volume experience greater slippage.
        Uses a square-root market impact model.

        Returns:
            Fill price after slippage
        """
        # Calculate participation rate for impact
        if self.last_volume > 0:
            participation = fill_qty / self.last_volume
        else:
            participation = 0.0

        # Square-root impact model: impact = slippage * sqrt(participation)
        impact_factor = self.slippage * (participation ** 0.5) if participation > 0 else self.slippage

        if direction == "BUY":
            fill_price = base_price * (1 + impact_factor)
            # Cap at bar high (can't fill above the high)
            if self.last_high > 0:
                fill_price = min(fill_price, self.last_high)
        else:
            fill_price = base_price * (1 - impact_factor)
            # Floor at bar low (can't fill below the low)
            if self.last_low > 0:
                fill_price = max(fill_price, self.last_low)

        return fill_price

    def on_order(self, event: OrderEvent) -> None:
        """Process an order event with volume-aware matching."""
        self.total_orders += 1

        # Determine base price
        if event.order_type == "LIMIT" and event.limit_price:
            # Check if limit price is executable
            if event.direction == "BUY" and event.limit_price < self.last_low:
                logger.debug(
                    f"Limit BUY order rejected: limit={event.limit_price} < low={self.last_low}"
                )
                self.total_rejected += 1
                return
            if event.direction == "SELL" and event.limit_price > self.last_high:
                logger.debug(
                    f"Limit SELL order rejected: limit={event.limit_price} > high={self.last_high}"
                )
                self.total_rejected += 1
                return
            base_price = event.limit_price
        else:
            base_price = self.last_price

        if base_price <= 0:
            logger.warning(f"Cannot fill order: no valid price for {event.symbol}")
            self.total_rejected += 1
            return

        # Calculate executable quantity
        fill_qty = self._calculate_fill_quantity(event.quantity)
        is_partial = fill_qty < event.quantity

        if is_partial:
            self.total_partial_fills += 1
            logger.debug(
                f"Partial fill for {event.symbol}: "
                f"requested={event.quantity}, filled={fill_qty} "
                f"(vol={self.last_volume}, rate={self.max_participation_rate})"
            )

        # Calculate slippage-adjusted price
        fill_price = self._calculate_slippage(base_price, fill_qty, event.direction)

        # Calculate commission
        total_commission = self.commission * fill_qty

        # Publish fill
        fill = FillEvent(
            time=event.time,
            symbol=event.symbol,
            exchange="BACKTEST",
            quantity=fill_qty,
            direction=event.direction,
            fill_cost=fill_price,
            commission=total_commission,
        )
        self.bus.publish(fill)
        self.total_fills += 1

    def stats(self) -> dict:
        """Get execution statistics."""
        return {
            "total_orders": self.total_orders,
            "total_fills": self.total_fills,
            "total_partial_fills": self.total_partial_fills,
            "total_rejected": self.total_rejected,
            "fill_rate": (
                f"{self.total_fills / self.total_orders * 100:.1f}%"
                if self.total_orders > 0
                else "N/A"
            ),
        }
