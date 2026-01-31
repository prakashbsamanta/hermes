import polars as pl
from engine.strategy import Strategy
from engine.mtf_utils import resample_data, merge_mtf

class MTFTrendFollowingStrategy(Strategy):
    """
    Multi-Timeframe Strategy.
    1. Resamples data to DAILY.
    2. Calculates Daily Trend (SMA 50 > SMA 200).
    3. Trades Minute RSI Dips ONLY if Daily Trend is Bullish.
    """
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        # 1. Resample to Daily
        daily_df = resample_data(df, interval="1d")
        
        # 2. Calculate Daily Indicators (Trend)
        daily_df = daily_df.with_columns([
            pl.col("close").rolling_mean(window_size=50).alias("sma_50"),
            pl.col("close").rolling_mean(window_size=200).alias("sma_200")
        ]).with_columns([
            (pl.col("sma_50") > pl.col("sma_200")).alias("bullish_trend")
        ])
        
        # 3. Merge Daily Data back to Minute
        # Result columns: bullish_trend_htf
        df_merged = merge_mtf(df, daily_df.select(["timestamp", "bullish_trend"]), suffix="_htf")
        
        # 4. Calculate Minute Indicators (RSI)
        # Reuse logic or efficient calc
        df_indicators = df_merged.with_columns([
             pl.col("close").diff().alias("change")
        ]).with_columns([
            pl.when(pl.col("change") > 0).then(pl.col("change")).otherwise(0).alias("gain"),
            pl.when(pl.col("change") < 0).then(-pl.col("change")).otherwise(0).alias("loss")
        ])
        
        period = 14
        df_indicators = df_indicators.with_columns([
            pl.col("gain").ewm_mean(com=period - 1, min_samples=period).alias("avg_gain"),
            pl.col("loss").ewm_mean(com=period - 1, min_samples=period).alias("avg_loss")
        ]).with_columns([
            (pl.col("avg_gain") / pl.col("avg_loss")).alias("rs")
        ]).with_columns([
            (100 - (100 / (1 + pl.col("rs")))).fill_nan(50).fill_null(50).alias("rsi")
        ])

        # 5. Generate Signals (MTF Logic)
        # Buy if: RSI < 30 AND Daily_Trend is Bullish
        # Sell if: RSI > 70
        
        # Note: 'bullish_trend_htf' comes from the merge. 'bullish_trend' column in daily was renamed?
        # merge_mtf renames specific columns. We passed .select(["timestamp", "bullish_trend"]).
        # So it becomes 'bullish_trend_htf'.
        
        df_triggers = df_indicators.with_columns([
            pl.when( (pl.col("rsi") < 30) & (pl.col("bullish_trend_htf")) )
            .then(1) # Buy
            .when(pl.col("rsi") > 70)
            .then(0) # Sell
            .otherwise(None)
            .alias("signal_trigger")
        ])

        # Latch
        df_signals = df_triggers.with_columns([
            pl.col("signal_trigger").forward_fill().fill_null(0).alias("signal")
        ])

        return df_signals
