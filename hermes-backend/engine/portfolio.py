"""Decoupled Portfolio Manager for the Event-Driven Backtest Engine.

Subscribes to SignalEvent and FillEvent via the EventBus.
Manages cash, positions, equity tracking, and risk-aware order generation.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from engine.events import FillEvent, OrderEvent, SignalEvent, MarketEvent
from engine.event_bus import EventBus

logger = logging.getLogger(__name__)


@dataclass
class RiskParams:
    """Risk management parameters for position sizing.

    Attributes:
        sizing_method: Position sizing method (fixed, pct_equity, atr_based)
        fixed_quantity: Fixed share count (for sizing_method='fixed')
        pct_equity: Fraction of equity to allocate per trade (0.0 - 1.0)
        atr_multiplier: ATR multiplier for volatility-based sizing
        max_position_pct: Maximum portfolio allocation for a single position (0.0 - 1.0)
        stop_loss_pct: Hard stop-loss as percentage of entry price (0.0 - 1.0)
    """
    sizing_method: str = "fixed"  # "fixed", "pct_equity", "atr_based"
    fixed_quantity: float = 10.0
    pct_equity: float = 0.02  # 2% of equity per trade
    atr_multiplier: float = 1.5
    max_position_pct: float = 0.25  # Max 25% in single position
    stop_loss_pct: float = 0.05  # 5% stop loss


@dataclass
class Position:
    """Tracks an individual position."""
    symbol: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    total_cost: float = 0.0
    realized_pnl: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.quantity != 0.0

    def mark_to_market(self, price: float) -> float:
        """Calculate unrealized P&L at current price."""
        return (price - self.avg_entry_price) * self.quantity


class PortfolioManager:
    """Risk-aware Portfolio Manager for the event-driven engine.

    Responsibilities:
    - Subscribes to SignalEvent: translates signals into sized OrderEvents
    - Subscribes to FillEvent: updates position and cash state
    - Subscribes to MarketEvent: tracks last price for mark-to-market
    - Tracks equity curve (mark-to-market on every bar)
    - Enforces risk limits (max position size, stop-loss)
    """

    def __init__(
        self,
        bus: EventBus,
        initial_cash: float = 100000.0,
        risk_params: Optional[RiskParams] = None,
    ):
        self.bus = bus
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.risk_params = risk_params or RiskParams()

        # Position tracking
        self.positions: Dict[str, Position] = {}
        self.last_prices: Dict[str, float] = {}

        # Metrics tracking
        self.equity_history: List[Dict] = []
        self.fills_log: List[Dict] = []

        # Subscribe to events
        self.bus.subscribe(SignalEvent, self.on_signal)  # type: ignore
        self.bus.subscribe(FillEvent, self.on_fill)  # type: ignore
        self.bus.subscribe(MarketEvent, self.on_bar)  # type: ignore

        logger.info(
            f"PortfolioManager initialized: cash={initial_cash}, "
            f"sizing={self.risk_params.sizing_method}"
        )

    @property
    def equity(self) -> float:
        """Total equity = cash + sum of position market values."""
        total = self.cash
        for sym, pos in self.positions.items():
            price = self.last_prices.get(sym, pos.avg_entry_price)
            total += pos.quantity * price
        return total

    def _get_position(self, symbol: str) -> Position:
        """Get or create a position tracker for a symbol."""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def _calculate_quantity(self, symbol: str, price: float) -> float:
        """Calculate order quantity based on risk parameters."""
        rp = self.risk_params

        if rp.sizing_method == "fixed":
            return rp.fixed_quantity

        elif rp.sizing_method == "pct_equity":
            # Allocate pct_equity fraction of current equity
            allocation = self.equity * rp.pct_equity
            qty = allocation / price if price > 0 else 0
            return max(1.0, round(qty))

        elif rp.sizing_method == "atr_based":
            # ATR-based sizing: risk_amount / (atr * multiplier)
            # For now, use pct_equity as the risk budget
            risk_amount = self.equity * rp.pct_equity
            # In a full implementation, ATR would come from the strategy
            # For now, use stop_loss_pct as a proxy for expected risk
            risk_per_share = price * rp.stop_loss_pct
            qty = risk_amount / risk_per_share if risk_per_share > 0 else 0
            return max(1.0, round(qty))

        return rp.fixed_quantity

    def _check_max_position_limit(self, symbol: str, quantity: float, price: float) -> float:
        """Enforce maximum position size as percentage of equity."""
        max_alloc = self.equity * self.risk_params.max_position_pct
        current_pos = self._get_position(symbol)
        current_value = current_pos.quantity * price
        max_additional = max_alloc - current_value

        if max_additional <= 0:
            logger.warning(
                f"Position limit reached for {symbol}: "
                f"current={current_value:.0f}, max={max_alloc:.0f}"
            )
            return 0.0

        max_qty = max_additional / price if price > 0 else 0
        return min(quantity, max(1.0, round(max_qty)))

    def on_signal(self, event: SignalEvent) -> None:
        """Handle signal events — generate risk-aware orders."""
        position = self._get_position(event.symbol)
        price = self.last_prices.get(event.symbol, 0.0)

        order = None

        if event.signal_type == "LONG" and not position.is_open:
            # Calculate sized quantity
            qty = self._calculate_quantity(event.symbol, price)
            qty = self._check_max_position_limit(event.symbol, qty, price)

            if qty > 0 and price > 0:
                # Verify we have enough cash
                cost = qty * price
                if cost > self.cash:
                    qty = max(1.0, round(self.cash / price) - 1)
                    if qty <= 0:
                        logger.warning(f"Insufficient cash for {event.symbol}")
                        return

                order = OrderEvent(
                    time=event.time,
                    symbol=event.symbol,
                    order_type="MARKET",
                    quantity=qty,
                    direction="BUY",
                )

        elif event.signal_type == "EXIT" and position.is_open and position.quantity > 0:
            order = OrderEvent(
                time=event.time,
                symbol=event.symbol,
                order_type="MARKET",
                quantity=position.quantity,
                direction="SELL",
            )

        elif event.signal_type == "SHORT" and not position.is_open:
            qty = self._calculate_quantity(event.symbol, price)
            if qty > 0 and price > 0:
                order = OrderEvent(
                    time=event.time,
                    symbol=event.symbol,
                    order_type="MARKET",
                    quantity=qty,
                    direction="SELL",
                )

        if order:
            self.bus.publish(order)

    def on_fill(self, event: FillEvent) -> None:
        """Handle fill events — update portfolio state."""
        position = self._get_position(event.symbol)
        fill_price = event.fill_cost or 0.0
        commission = event.commission or 0.0

        if event.direction == "BUY":
            total_cost = event.quantity * fill_price + commission
            self.cash -= total_cost

            # Update average entry
            new_qty = position.quantity + event.quantity
            if new_qty > 0:
                position.avg_entry_price = (
                    (position.avg_entry_price * position.quantity)
                    + (fill_price * event.quantity)
                ) / new_qty
            position.quantity = new_qty
            position.total_cost += total_cost

        elif event.direction == "SELL":
            proceeds = event.quantity * fill_price - commission
            self.cash += proceeds

            # Realize P&L
            pnl = (fill_price - position.avg_entry_price) * event.quantity - commission
            position.realized_pnl += pnl
            position.quantity -= event.quantity

            if position.quantity <= 0:
                position.quantity = 0.0
                position.avg_entry_price = 0.0

        self.fills_log.append({
            "time": event.time,
            "symbol": event.symbol,
            "direction": event.direction,
            "quantity": event.quantity,
            "price": fill_price,
            "commission": commission,
            "cash_after": self.cash,
            "equity_after": self.equity,
        })

    def on_bar(self, event: MarketEvent) -> None:
        """Handle market events — update prices and check stops."""
        self.last_prices[event.symbol] = event.close

        # Check stop-loss
        position = self._get_position(event.symbol)
        if position.is_open and position.quantity > 0:
            loss_pct = (event.close - position.avg_entry_price) / position.avg_entry_price
            if loss_pct < -self.risk_params.stop_loss_pct:
                logger.info(
                    f"Stop-loss triggered for {event.symbol}: "
                    f"loss={loss_pct:.2%}, threshold={-self.risk_params.stop_loss_pct:.2%}"
                )
                stop_order = OrderEvent(
                    time=event.time,
                    symbol=event.symbol,
                    order_type="MARKET",
                    quantity=position.quantity,
                    direction="SELL",
                )
                self.bus.publish(stop_order)

    def snapshot(self, time: int) -> None:
        """Record equity snapshot at a point in time."""
        self.equity_history.append({
            "time": time,
            "equity": self.equity,
            "cash": self.cash,
        })
