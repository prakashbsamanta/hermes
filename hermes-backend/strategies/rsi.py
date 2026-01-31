import polars as pl
from engine.strategy import Strategy

class RSIStrategy(Strategy):
    """
    Relative Strength Index (RSI) Strategy.
    
    Logic:
    - Buy when RSI < oversold (default 30) -> Mean Reversion Buy
    - Sell when RSI > overbought (default 70) -> Mean Reversion Sell
    """
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        period = self.params.get("period", 14)
        overbought = self.params.get("overbought", 70)
        oversold = self.params.get("oversold", 30)

        # 1. Calculate Price Changes
        # null_strategy='ignore' is important for first row


        # 2. Separate Gains and Losses
        # We need to replicate:
        # gain = delta.clip(lower=0)
        # loss = -delta.clip(upper=0)
        
        # Native Polars approach for Gain/Loss to avoid external series manips if possible,
        # but creating series is fine.
        
        # Helper to calc RSI using Wilders Smoothing (standard RSI) or Simple Moving Average?
        # Standard RSI uses Wilder's Smoothing.
        # For simplicity and performance in this Alpha, we will use Exponential Weighted Mean (EWM) 
        # which is very close to Wilder's, or exact if alpha=1/period.
        # Polars ewm_mean is available.
        
        # Let's do it inside the dataframe context for speed
        
        df_rsi = df.with_columns([
            pl.col("close").diff().alias("change")
        ]).with_columns([
            pl.when(pl.col("change") > 0).then(pl.col("change")).otherwise(0).alias("gain"),
            pl.when(pl.col("change") < 0).then(-pl.col("change")).otherwise(0).alias("loss")
        ])

        # Wilder's Smoothing via EWM (alpha = 1/period)
        # RSI = 100 - (100 / (1 + RS))
        # RS = AvgGain / AvgLoss
        
        df_indicators = df_rsi.with_columns([
            pl.col("gain").ewm_mean(com=period - 1, min_samples=period).alias("avg_gain"),
            pl.col("loss").ewm_mean(com=period - 1, min_samples=period).alias("avg_loss")
        ]).with_columns([
            (pl.col("avg_gain") / pl.col("avg_loss")).alias("rs")
        ]).with_columns([
            (100 - (100 / (1 + pl.col("rs")))).fill_nan(50).fill_null(50).alias("rsi")
        ])

        # Generate Signals (Triggers)
        # 1 = Buy Trigger (Oversold)
        # -1 = Sell Trigger (Overbought)
        # 0 = Neutral / Hold previous
        
        # We want to LATCH the state:
        # If Buy Trigger -> Position = 1
        # If Sell Trigger -> Position = 0 (Exit)
        # Else -> Maintain previous position
        
        df_triggers = df_indicators.with_columns([
            pl.when(pl.col("rsi") < oversold)
            .then(1)
            .when(pl.col("rsi") > overbought)
            .then(0) # Exit to Cash
            .otherwise(None) # Important: Null allows forward fill
            .alias("signal_trigger")
        ])

        # Forward Fill to create continuous position
        df_signals = df_triggers.with_columns([
            pl.col("signal_trigger").forward_fill().fill_null(0).alias("signal")
        ])

        return df_signals
