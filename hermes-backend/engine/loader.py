import os
import polars as pl
from datetime import datetime
from typing import List, Optional
import logging

class DataLoader:
    """
    Efficiently loads stock data from Parquet files using Polars.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

    def load_data(
        self, 
        symbols: List[str], 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pl.DataFrame:
        """
        Loads data for multiple symbols into a single stacked DataFrame.
        Schema: [timestamp, open, high, low, close, volume, oi, symbol]
        """
        dfs = []
        
        for symbol in symbols:
            file_path = os.path.join(self.data_dir, f"{symbol}.parquet")
            if not os.path.exists(file_path):
                logging.warning(f"Data for {symbol} not found at {file_path}")
                continue
            
            # Lazy Scan for efficiency
            lazy_df = pl.scan_parquet(file_path)
            
            # Filter by Date
            if start_date:
                # Assuming timestamp is datetime in parquet
                # We cast string input to datetime literals for comparison
                s_dt = datetime.strptime(start_date, "%Y-%m-%d")
                lazy_df = lazy_df.filter(pl.col("timestamp") >= s_dt)
            
            if end_date:
                e_dt = datetime.strptime(end_date, "%Y-%m-%d")
                lazy_df = lazy_df.filter(pl.col("timestamp") <= e_dt)
            
            # Add Symbol Column (needed for stacked df)
            lazy_df = lazy_df.with_columns(pl.lit(symbol).alias("symbol"))
            
            dfs.append(lazy_df)
            
        if not dfs:
            raise ValueError("No data loaded for any of the provided symbols.")
            
        # Concat all lazy frames and collect
        # This is very efficient in Polars
        combined_lazy = pl.concat(dfs)
        
        # Sort by timestamp (crucial for backtesting)
        # Note: Depending on strategy, we might sort by (symbol, timestamp) or (timestamp, symbol)
        # For a centralized event loop, (timestamp, symbol) is better.
        combined_lazy = combined_lazy.sort(["timestamp", "symbol"])

        # --- DATA GUARD (Robustness) ---
        # 1. Filter out invalid prices (<= 0)
        # 2. Drop rows with Nulls in critical columns
        # This ensures AUTHENTICITY: we never backtest on fake/zero data.
        
        logging.info("Applying Data Guard: Filtering invalid prices and nulls...")
        combined_lazy = combined_lazy.filter(
            (pl.col("close") > 0) & 
            (pl.col("open") > 0) & 
            (pl.col("high") > 0) & 
            (pl.col("low") > 0)
        ).drop_nulls(subset=["close", "open", "high", "low"])
        
        logging.info(f"Materializing data for {len(symbols)} symbols...")
        final_df = combined_lazy.collect()
        
        logging.info(f"Loaded {len(final_df)} rows.")
        return final_df
