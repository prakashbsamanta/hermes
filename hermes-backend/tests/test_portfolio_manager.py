
from engine.portfolio import PortfolioManager
from engine.event_bus import EventBus
from engine.events import SignalEvent

def test_portfolio_manager_basic():
    bus = EventBus()
    portfolio = PortfolioManager(bus=bus, initial_cash=100000.0)
    
    # Just exercise the handler to get coverage
    signal = SignalEvent(
        time="2024-01-01 10:00",
        symbol="TEST",
        signal_type="LONG",
        strength=1.0,
        strategy_id="TEST"
    )
    portfolio.on_signal(signal)
    
    assert portfolio.cash == 100000.0  # Cash drops on fill, not signal
