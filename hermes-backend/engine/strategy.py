from abc import ABC, abstractmethod
import polars as pl

class Strategy(ABC):
    """
    Abstract Base Class for Vectorized Strategies.
    Strategies must work on the entire DataFrame at once (Polars) for maximum speed.
    """
    def __init__(self, params: dict | None = None):
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Core Logic.
        Input: DataFrame with [timestamp, open, high, low, close, volume, symbol]
        Output: DataFrame with an added 'signal' column.
                1 = ENTRY (Buy)
                -1 = EXIT (Sell)
                0 = HOLD / NO ACTION
        
        The result should be the SAME length as the input.
        """
        pass
