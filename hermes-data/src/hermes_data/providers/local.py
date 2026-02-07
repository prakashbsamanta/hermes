"""Local file system data provider for Parquet files."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import polars as pl

from .base import DataProvider

logger = logging.getLogger(__name__)


class LocalFileProvider(DataProvider):
    """Loads market data from local Parquet files.
    
    This adapter implements the DataProvider interface for local file storage,
    migrating and improving the original DataLoader functionality.
    """

    def __init__(self, data_dir: str | Path):
        """Initialize the local file provider.
        
        Args:
            data_dir: Path to directory containing parquet files
            
        Raises:
            FileNotFoundError: If data directory doesn't exist
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

    def load(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pl.DataFrame:
        """Load OHLCV data for given symbols within date range.
        
        Implements efficient lazy loading with Polars, applying filters 
        at scan time for optimal performance.
        """
        dfs = []

        for symbol in symbols:
            file_path = self.data_dir / f"{symbol}.parquet"
            if not file_path.exists():
                logger.warning(f"Data for {symbol} not found at {file_path}")
                continue

            # Lazy Scan for efficiency
            lazy_df = pl.scan_parquet(file_path)

            # NORMALIZATION: Ensure timestamp is Naive (Wall Clock)
            # This handles UTC-aware parquet files by dropping timezone info
            lazy_df = lazy_df.with_columns(
                pl.col("timestamp").dt.replace_time_zone(None)
            )

            # Filter by Date Range
            if start_date:
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
        combined_lazy = pl.concat(dfs)

        # Sort by timestamp (crucial for backtesting)
        combined_lazy = combined_lazy.sort(["timestamp", "symbol"])

        # --- DATA GUARD (Robustness) ---
        # 1. Filter out invalid prices (<= 0)
        # 2. Drop rows with Nulls in critical columns
        logger.info("Applying Data Guard: Filtering invalid prices and nulls...")
        combined_lazy = combined_lazy.filter(
            (pl.col("close") > 0)
            & (pl.col("open") > 0)
            & (pl.col("high") > 0)
            & (pl.col("low") > 0)
        ).filter(
            # Integrity Checks (High must be highest, Low must be lowest)
            (pl.col("high") >= pl.col("low"))
            & (pl.col("high") >= pl.col("open"))
            & (pl.col("high") >= pl.col("close"))
            & (pl.col("low") <= pl.col("open"))
            & (pl.col("low") <= pl.col("close"))
        ).drop_nulls(subset=["close", "open", "high", "low"])

        logger.info(f"Materializing data for {len(symbols)} symbols...")
        final_df = combined_lazy.collect()

        logger.info(f"Loaded {len(final_df)} rows.")
        return final_df

    def list_symbols(self) -> List[str]:
        """List all available instrument symbols."""
        files = self.data_dir.glob("*.parquet")
        return sorted([f.stem for f in files])

    def get_date_range(self, symbol: str) -> Tuple[str, str]:
        """Get available date range for a symbol."""
        file_path = self.data_dir / f"{symbol}.parquet"
        if not file_path.exists():
            raise FileNotFoundError(f"Data not found for symbol: {symbol}")

        df = (
            pl.scan_parquet(file_path)
            .select(
                pl.col("timestamp").min().alias("start"),
                pl.col("timestamp").max().alias("end"),
            )
            .collect()
        )
        return (
            df["start"][0].strftime("%Y-%m-%d"),
            df["end"][0].strftime("%Y-%m-%d"),
        )

    def health_check(self) -> bool:
        """Verify provider is accessible and has data."""
        return self.data_dir.exists() and any(self.data_dir.glob("*.parquet"))
