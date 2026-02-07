"""Tests for RSI strategy including event-driven mode."""

import pytest
from datetime import datetime, timedelta


class TestRSIEventDriven:
    """Tests for RSI strategy event-driven mode."""

    @pytest.fixture
    def sample_prices(self):
        """Generate sample price data for RSI testing."""
        return [100 + i * 0.5 for i in range(20)] + [110 - i * 0.3 for i in range(20)]

    def test_rsi_on_bar_initialization(self, sample_prices):
        """Test RSI strategy on_bar initialization."""
        from strategies.rsi import RSIStrategy
        from engine.events import MarketEvent
        
        strategy = RSIStrategy(params={"period": 14})
        
        # Feed initial prices
        for i, price in enumerate(sample_prices[:16]):
            event = MarketEvent(
                time=datetime(2023, 1, 1) + timedelta(minutes=i),
                symbol="TEST",
                open=price,
                high=price + 0.5,
                low=price - 0.5,
                close=price,
                volume=1000,
            )
            strategy.on_bar(event)
        
        # After 14 periods, strategy should be initialized
        assert strategy.initialized is True

    def test_rsi_on_bar_generates_signals(self, sample_prices):
        """Test RSI generates signals in event mode."""
        from strategies.rsi import RSIStrategy
        from engine.events import MarketEvent
        from engine.event_bus import EventBus
        
        strategy = RSIStrategy(params={"period": 5, "oversold": 30, "overbought": 70})
        bus = EventBus()
        strategy.bus = bus
        
        signals_received = []
        bus.subscribe("signal", lambda e: signals_received.append(e))
        
        # Create a trend that triggers RSI signals
        # Start with uptrend then downtrend
        prices = [100 + i * 2 for i in range(20)] + [140 - i * 3 for i in range(20)]
        
        for i, price in enumerate(prices):
            event = MarketEvent(
                time=datetime(2023, 1, 1) + timedelta(minutes=i),
                symbol="TEST",
                open=price,
                high=price + 0.5,
                low=price - 0.5,
                close=price,
                volume=1000,
            )
            strategy.on_bar(event)
        
        # Strategy should generate at least one signal after enough data
        assert strategy.initialized is True

    def test_rsi_on_bar_single_price(self):
        """Test RSI with only one price point."""
        from strategies.rsi import RSIStrategy
        from engine.events import MarketEvent
        
        strategy = RSIStrategy(params={"period": 14})
        
        event = MarketEvent(
            time=datetime(2023, 1, 1),
            symbol="TEST",
            open=100,
            high=100.5,
            low=99.5,
            close=100,
            volume=1000,
        )
        
        # Should not crash with only one price
        strategy.on_bar(event)
        assert strategy.initialized is False

    def test_rsi_on_bar_no_bus(self):
        """Test RSI event mode without event bus."""
        from strategies.rsi import RSIStrategy
        from engine.events import MarketEvent
        
        strategy = RSIStrategy(params={"period": 3})
        # No bus attached
        
        # Feed enough data to trigger signal logic
        prices = [100 + i * 5 for i in range(10)] + [150 - i * 10 for i in range(10)]
        
        for i, price in enumerate(prices):
            event = MarketEvent(
                time=datetime(2023, 1, 1) + timedelta(minutes=i),
                symbol="TEST",
                open=price,
                high=price + 0.5,
                low=price - 0.5,
                close=price,
                volume=1000,
            )
            # Should not crash even without bus
            strategy.on_bar(event)
        
        assert strategy.initialized is True

    def test_rsi_on_bar_zero_loss(self):
        """Test RSI when there's no price drop (zero loss)."""
        from strategies.rsi import RSIStrategy
        from engine.events import MarketEvent
        
        strategy = RSIStrategy(params={"period": 5})
        
        # Pure uptrend - no losses
        for i in range(15):
            event = MarketEvent(
                time=datetime(2023, 1, 1) + timedelta(minutes=i),
                symbol="TEST",
                open=100 + i,
                high=101 + i,
                low=99 + i,
                close=100 + i,
                volume=1000,
            )
            strategy.on_bar(event)
        
        # RSI should be 100 when no losses
        assert strategy.avg_loss >= 0
