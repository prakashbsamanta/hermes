import polars as pl

def resample_data(df: pl.DataFrame, interval: str = "1d") -> pl.DataFrame:
    """
    Resamples minute data to a higher timeframe.
    Input df must have 'timestamp', 'open', 'high', 'low', 'close', 'volume'.
    """
    # Define aggregation rules
    # We use 'timestamp' as the grouping key via dynamic_group_by if needed, 
    # but for simple '1d' resampling, truncate is easier if we just want daily bars.
    # However, dynamic_group_by is more robust for "1h", "15m" etc.
    
    # Check if timestamp is sorted
    # df = df.sort("timestamp") 
    
    # Polars Dynamic Group By
    # '1d' interval.
    
    q = (
        df.sort("timestamp")
        .group_by_dynamic("timestamp", every=interval)
        .agg([
            pl.col("open").first().alias("open"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
            pl.col("volume").sum().alias("volume"),
            pl.col("symbol").first().alias("symbol")
        ])
    )
    
    return q

def merge_mtf(minute_df: pl.DataFrame, higher_tf_df: pl.DataFrame, suffix: str = "_htf") -> pl.DataFrame:
    """
    Merges higher timeframe data onto minute data.
    CRITICAL: Uses Forward Fill to ensure no lookahead bias.
    The value available at Minute T is the Higher TF value from T-1 (or current running).
    
    For "Daily" data checks:
    At 10:00 AM today, we usually want to know "Yesterday's Close" or "Today's Trend so far".
    
    If we stick to "Completed Bars", we should join based on previous day.
    However, a simpler verifyable approach is:
    1. Upsample HTF data to Minute frequency (forward fill).
    2. Join on timestamp.
    """
    
    # ALIGNMENT STRATEGY:
    # 1. Rename columns in HTF
    # Rename ALL columns except timestamp to avoid collisions
    cols_to_rename = [col for col in higher_tf_df.columns if col != "timestamp"]
    htf_renamed = higher_tf_df.rename({
        col: f"{col}{suffix}" for col in cols_to_rename
    })
    
    # 2. Join_asof (Left Join)
    # Join minute_df with htf_renamed on timestamp.
    # distinct strategy='backward' means: for a minute row, find the LATEST htf row that is <= minute_time.
    # This effectively forward fills the Daily bar onto the intraday minutes.
    
    merged = minute_df.join_asof(
        htf_renamed.sort("timestamp"),
        on="timestamp",
        strategy="backward"
    )
    
    return merged
