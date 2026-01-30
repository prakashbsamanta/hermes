import polars as pl
try:
    from engine.strategy import Strategy
except ImportError:
    from hermes_backend.engine.strategy import Strategy

class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Mean Reversion Strategy.
    
    Logic:
    - Buy when Close crosses below Lower Band (Oversold)
    - Sell when Close crosses above Upper Band (Overbought)
    """
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        period = self.params.get("period", 20)
        std_dev_multiplier = self.params.get("std_dev", 2.0)

        # Calculate Rolling Mean and Std Dev
        df_indicators = df.with_columns([
            pl.col("close").rolling_mean(window_size=period).alias("bb_mid"),
            pl.col("close").rolling_std(window_size=period).alias("bb_std")
        ]).with_columns([
            (pl.col("bb_mid") + (pl.col("bb_std") * std_dev_multiplier)).alias("bb_upper"),
            (pl.col("bb_mid") - (pl.col("bb_std") * std_dev_multiplier)).alias("bb_lower")
        ])

        # Generate Triggers
        # Price < Lower -> Buy (1)
        # Price > Upper -> Sell (0)
        # Else -> Hold (Null for fill)
        
        df_triggers = df_indicators.with_columns([
            pl.when(pl.col("close") < pl.col("bb_lower"))
            .then(1)
            .when(pl.col("close") > pl.col("bb_upper"))
            .then(0)
            .otherwise(None)
            .alias("signal_trigger")
        ])
        
        # Latch
        df_signals = df_triggers.with_columns([
            pl.col("signal_trigger").forward_fill().fill_null(0).alias("signal")
        ])

        return df_signals
