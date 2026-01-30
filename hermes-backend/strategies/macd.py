import polars as pl
try:
    from engine.strategy import Strategy
except ImportError:
    from hermes_backend.engine.strategy import Strategy

class MACDStrategy(Strategy):
    """
    Moving Average Convergence Divergence (MACD) Strategy.
    
    Logic:
    - MACD Line = Fast EMA (12) - Slow EMA (26)
    - Signal Line = EMA (9) of MACD Line
    - Buy when MACD crosses ABOVE Signal Line
    - Sell when MACD crosses BELOW Signal Line
    """
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        fast_period = self.params.get("fast_period", 12)
        slow_period = self.params.get("slow_period", 26)
        signal_period = self.params.get("signal_period", 9)

        # Calculate EMAs and MACD
        df_indicators = df.with_columns([
            pl.col("close").ewm_mean(span=fast_period, adjust=False).alias("ema_fast"),
            pl.col("close").ewm_mean(span=slow_period, adjust=False).alias("ema_slow")
        ]).with_columns([
            (pl.col("ema_fast") - pl.col("ema_slow")).alias("macd_line")
        ]).with_columns([
            pl.col("macd_line").ewm_mean(span=signal_period, adjust=False).alias("signal_line")
        ])

        # Generate Triggers (Crossover Logic)
        # Buy: MACD > Signal
        # Sell: MACD < Signal
        
        df_triggers = df_indicators.with_columns([
            pl.when(pl.col("macd_line") > pl.col("signal_line"))
            .then(1)
            .when(pl.col("macd_line") < pl.col("signal_line"))
            .then(0) # Exit/Short
            .otherwise(None)
            .alias("signal_trigger")
        ])

        # Latch State
        df_signals = df_triggers.with_columns([
            pl.col("signal_trigger").forward_fill().fill_null(0).alias("signal")
        ])

        return df_signals
