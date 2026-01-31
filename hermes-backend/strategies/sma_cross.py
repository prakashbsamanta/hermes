import polars as pl
# Adjust import based on how we run it. 
# For now, assuming we run as a module or with path set.
from engine.strategy import Strategy


class SMACrossover(Strategy):
    """
    Simple Moving Average Crossover Strategy.
    Long when Fast SMA > Slow SMA.
    Flat otherwise.
    """
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        fast_window = self.params.get("fast_period", 50)
        slow_window = self.params.get("slow_period", 200)

        # Polars Rolling Mean
        # Ensure we have enough data (lazy or eager)
        # Note: 'close' column required.

        # Calculate Indicators
        # We use moving_mean (rolling mean)
        df_with_indicators = df.with_columns([
            pl.col("close").rolling_mean(window_size=fast_window).alias("sma_fast"),
            pl.col("close").rolling_mean(window_size=slow_window).alias("sma_slow")
        ])

        # Generate Signal
        # 1 if Fast > Slow, 0 otherwise
        df_signals = df_with_indicators.with_columns([
            pl.when(pl.col("sma_fast") > pl.col("sma_slow"))
            .then(1)
            .otherwise(0)
            .alias("signal")
        ])
        
        # Cleanup (drop indicators if we don't want them in final output, but usually useful to keep)
        return df_signals
