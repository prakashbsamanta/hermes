from abc import ABC, abstractmethod
import polars as pl
from .events import MarketEvent, FillEvent

class Strategy(ABC):
    """
    Abstract Base Class for Strategies.
    Supports both Vectorized (Polars) and Event-Driven execution.
    """
    def __init__(self, params: dict | None = None):
        self.params = params or {}
        self.bus = None

    def set_bus(self, bus):
        self.bus = bus

    @abstractmethod
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Vectorized Logic.
        Input: DataFrame with [timestamp, open, high, low, close, volume, symbol]
        Output: DataFrame with an added 'signal' column.
                1 = ENTRY (Buy)
                -1 = EXIT (Sell)
                0 = HOLD / NO ACTION
        
        The result should be the SAME length as the input.
        """
        pass

    def on_bar(self, event: MarketEvent):
        """
        Event-Driven Logic.
        Callback for new market data.
        """
        pass

    def on_fill(self, event: FillEvent):
        """
        Event-Driven Logic.
        Callback for order fills.
        """
        pass
