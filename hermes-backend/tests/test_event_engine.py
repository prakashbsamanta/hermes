from engine.event_bus import EventBus
from engine.event_engine import EventEngine
from engine.events import MarketEvent
from engine.strategy import Strategy
from unittest.mock import MagicMock

class MockStrategy(Strategy):
    def generate_signals(self, df):
        return df

    def on_bar(self, event: MarketEvent):
        # Trigger a signal on every bar for testing
        pass

def test_event_bus_publish_subscribe():
    bus = EventBus()
    mock_listener = MagicMock()
    
    bus.subscribe(MarketEvent, mock_listener)
    
    event = MarketEvent(time=100, symbol="TEST", open=10, high=11, low=9, close=10, volume=100)
    bus.publish(event)
    bus.process_next()
    
    mock_listener.assert_called_once_with(event)

def test_event_engine_flow():
    engine = EventEngine()
    strategy = MockStrategy()
    
    # Spy on strategy methods
    strategy.on_bar = MagicMock()
    
    # Register strategy
    engine.register_strategy(strategy)
    
    # Create Data Generator
    def data_gen():
        yield MarketEvent(time=1, symbol="A", open=10, high=11, low=9, close=10, volume=100)
        yield MarketEvent(time=2, symbol="A", open=10, high=11, low=9, close=10, volume=100)
        
    engine.run(data_gen())
    
    assert strategy.on_bar.call_count == 2
