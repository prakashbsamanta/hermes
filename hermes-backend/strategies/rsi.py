import polars as pl
from engine.strategy import Strategy
from engine.events import MarketEvent, SignalEvent
import collections

class RSIStrategy(Strategy):
    """
    Relative Strength Index (RSI) Strategy.
    Supports both Vectorized (fast) and Event-Driven (detailed) modes.
    
    Logic:
    - Buy when RSI < oversold (default 30) -> Mean Reversion Buy
    - Sell when RSI > overbought (default 70) -> Mean Reversion Sell
    """
    def __init__(self, params: dict | None = None):
        super().__init__(params)
        self.period = self.params.get("period", 14)
        self.overbought = self.params.get("overbought", 70)
        self.oversold = self.params.get("oversold", 30)
        
        from typing import Deque
        # Event-Driven State
        self.prices: Deque[float] = collections.deque(maxlen=self.period + 10) # Keep enough history
        self.gains: Deque[float] = collections.deque(maxlen=self.period)
        self.losses: Deque[float] = collections.deque(maxlen=self.period)
        self.avg_gain = 0.0
        self.avg_loss = 0.0
        self.initialized = False
        self.position = 0 # 0=Flat, 1=Long

    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        """Vectorized Implementation (unchanged)"""
        period = self.period
        overbought = self.overbought
        oversold = self.oversold

        df_rsi = df.with_columns([
            pl.col("close").diff().alias("change")
        ]).with_columns([
            pl.when(pl.col("change") > 0).then(pl.col("change")).otherwise(0).alias("gain"),
            pl.when(pl.col("change") < 0).then(-pl.col("change")).otherwise(0).alias("loss")
        ])

        df_indicators = df_rsi.with_columns([
            pl.col("gain").ewm_mean(com=period - 1, min_samples=period).alias("avg_gain"),
            pl.col("loss").ewm_mean(com=period - 1, min_samples=period).alias("avg_loss")
        ]).with_columns([
            (pl.col("avg_gain") / pl.col("avg_loss")).alias("rs")
        ]).with_columns([
            (100 - (100 / (1 + pl.col("rs")))).fill_nan(50).fill_null(50).alias("rsi")
        ])

        df_triggers = df_indicators.with_columns([
            pl.when(pl.col("rsi") < oversold)
            .then(1)
            .when(pl.col("rsi") > overbought)
            .then(0) # Exit to Cash
            .otherwise(None) # Important: Null allows forward fill
            .alias("signal_trigger")
        ])

        df_signals = df_triggers.with_columns([
            pl.col("signal_trigger").forward_fill().fill_null(0).alias("signal")
        ])

        return df_signals

    def on_bar(self, event: MarketEvent):
        """
        Event-Driven Implementation.
        Calculates RSI incrementally.
        """
        # 1. Update History
        self.prices.append(event.close)
        
        if len(self.prices) < 2:
            return

        # 2. Calculate Change
        delta = self.prices[-1] - self.prices[-2]
        gain = max(delta, 0)
        loss = max(-delta, 0)
        
        # 3. Calculate Average Gain/Loss (Wilder's Smoothing / EMA)
        if not self.initialized:
            self.gains.append(gain)
            self.losses.append(loss)
            
            if len(self.gains) == self.period:
                # First Average is simple SMA
                self.avg_gain = sum(self.gains) / self.period
                self.avg_loss = sum(self.losses) / self.period
                self.initialized = True
        else:
            # Subsequent steps: Wilder's smoothing
            # AvgGain = ((PrevAvgGain * (period-1)) + CurrGain) / period
            # This is equivalent to Pandas Com=(period-1)
            self.avg_gain = ((self.avg_gain * (self.period - 1)) + gain) / self.period
            self.avg_loss = ((self.avg_loss * (self.period - 1)) + loss) / self.period
            
        if not self.initialized:
            return

        # 4. Calculate RSI
        rs = 0.0
        if self.avg_loss == 0:
            rsi = 100.0
        else:
            rs = self.avg_gain / self.avg_loss
            rsi = 100 - (100 / (1 + rs))
            
        # 5. Generate Signal
        signal_type = None
        
        if rsi < self.oversold and self.position == 0:
            signal_type = "LONG"
            self.position = 1
        elif rsi > self.overbought and self.position == 1:
            signal_type = "EXIT" # Sell to Close
            self.position = 0
            
        if signal_type and self.bus:
            signal = SignalEvent(
                time=event.time,
                symbol=event.symbol,
                signal_type=signal_type,
                strength=1.0,
                strategy_id="RSI"
            )
            self.bus.publish(signal)
