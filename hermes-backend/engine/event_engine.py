from .event_bus import EventBus
from .events import MarketEvent, OrderEvent, FillEvent
from .strategy import Strategy
import logging

class EventEngine:
    """
    Event-Driven Backtest Engine.
    Orchestrates the flow of events between components.
    """
    def __init__(self):
        self.bus = EventBus()
        self.continue_backtest = True

    def register_strategy(self, strategy: Strategy):
        self.bus.subscribe(MarketEvent, strategy.on_bar)
        # In a real system, strategy might also subscribe to FillEvent
        self.bus.subscribe(FillEvent, strategy.on_fill)

    def run(self, data_iterator):
        """
        Run the event loop.
        data_iterator: A generator yielding MarketEvents.
        """
        logging.info("Starting Event Loop")
        
        for event in data_iterator:
            if not self.continue_backtest:
                break
                
            # Publish Market Event
            self.bus.publish(event)
            
            # Process all resulting events (Signals, Orders, Fills)
            self.bus.process_all()
            
        logging.info("Event Loop Finished")

class MockExecutionHandler:
    """
    Simple Execution Handler that fills every order immediately at Close price.
    """
    def __init__(self, bus: EventBus, slippage: float = 0.0, commission: float = 0.0):
        self.bus = bus
        self.slippage = slippage
        self.commission = commission
        self.bus.subscribe(OrderEvent, self.on_order) # type: ignore
        self.bus.subscribe(MarketEvent, self.on_bar) # type: ignore
        self.last_price = 100.0 # Default fallback
        
    def on_bar(self, event: MarketEvent):
        self.last_price = event.close

    def on_order(self, event: OrderEvent):
        # Create Fill Event
        # 1. Determine Base Price
        base_price = event.limit_price if event.limit_price else self.last_price
        
        # 2. Apply Slippage (Penalty on Buy, Penalty on Sell)
        # Buy: Price increases. Sell: Price decreases.
        impact = base_price * self.slippage
        if event.direction == "BUY":
            fill_price = base_price + impact
        else:
            fill_price = base_price - impact
            
        fill = FillEvent(
            time=event.time,
            symbol=event.symbol,
            exchange="MOCK",
            quantity=event.quantity,
            direction=event.direction,
            fill_cost=fill_price, 
            commission=self.commission * event.quantity
        )
        self.bus.publish(fill)
