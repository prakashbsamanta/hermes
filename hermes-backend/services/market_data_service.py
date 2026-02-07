"""Market data service providing data access for the API layer.

This service now uses hermes_data.DataService internally while maintaining
backward compatibility with the existing API.
"""

import logging
from typing import List, Optional

import polars as pl

from api.models import CandlePoint

# Import from the new hermes-data package
from hermes_data import DataService


class MarketDataService:
    """Service for accessing market data.
    
    This is a thin wrapper around hermes_data.DataService that maintains
    backward compatibility with the existing API while leveraging the
    new data layer's caching and abstraction.
    """

    def __init__(
        self,
        data_service: Optional[DataService] = None,
        data_sources: Optional[List[str]] = None,  # Kept for backward compat, ignored
    ):
        """Initialize the market data service.
        
        Args:
            data_service: Optional DataService instance. If not provided,
                          creates one using default settings.
            data_sources: DEPRECATED - kept for backward compatibility, ignored.
        """
        if data_sources:
            logging.warning(
                "data_sources parameter is deprecated. "
                "Use HERMES_DATA_DIR environment variable instead."
            )
        
        self._data_service = data_service or DataService()

    @property
    def data_service(self) -> DataService:
        """Access the underlying DataService."""
        return self._data_service

    def get_data_dir(self) -> str:
        """Get the data directory path.
        
        DEPRECATED: For backward compatibility only.
        Use data_service.settings.get_data_path() instead.
        """
        return str(self._data_service.settings.get_data_path())

    def list_instruments(self) -> List[str]:
        """List all available instrument symbols.
        
        Returns:
            Sorted list of symbol names
        """
        try:
            return self._data_service.list_instruments()
        except Exception as e:
            logging.warning(f"Could not list instruments: {str(e)}")
            return []

    def load_and_resample(
        self,
        symbol: str,
        timeframe: str = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pl.DataFrame:
        """Load and resample market data for a symbol.
        
        Args:
            symbol: Instrument symbol
            timeframe: Resample interval (e.g., "1h", "4h", "1d")
            start_date: Optional start date "YYYY-MM-DD"
            end_date: Optional end date "YYYY-MM-DD"
            
        Returns:
            Resampled DataFrame with OHLCV data
        """
        df = self._data_service.get_market_data(
            [symbol.upper()],
            start_date=start_date,
            end_date=end_date,
        )
        return self.resample_data(df, interval=timeframe)

    def get_candles(self, symbol: str, timeframe: str = "1h") -> List[CandlePoint]:
        """Get candles for a symbol in API-ready format.
        
        Args:
            symbol: Instrument symbol
            timeframe: Resample interval
            
        Returns:
            List of CandlePoint objects
        """
        chart_df = self.load_and_resample(symbol, timeframe)

        # Convert to CandlePoint list
        candles = []
        rows = chart_df.rows(named=True)
        for row in rows:
            ts = int(row["timestamp"].timestamp())
            candles.append(
                CandlePoint(
                    time=ts,
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                )
            )
        return candles

    @staticmethod
    def resample_data(df: pl.DataFrame, interval: str = "1h") -> pl.DataFrame:
        """Downsample datasets to specified interval for visualization.
        
        Args:
            df: Input DataFrame with OHLCV data
            interval: Resample interval (e.g., "1h", "4h", "1d")
            
        Returns:
            Resampled DataFrame
        """
        # Define aggregation dict for basic OHLCV
        agg_dict = {
            "open": pl.col("open").first(),
            "high": pl.col("high").max(),
            "low": pl.col("low").min(),
            "close": pl.col("close").last(),
            "volume": pl.col("volume").sum(),
        }

        # If equity/indicators exist, add them
        if "equity" in df.columns:
            agg_dict["equity"] = pl.col("equity").last()

        # Add other float columns as indicators
        exclude = {
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "signal",
            "position",
            "strategy_return",
            "equity",
            "trade_action",
        }
        for col in df.columns:
            if col not in exclude and df[col].dtype in [pl.Float64, pl.Float32]:
                agg_dict[col] = pl.col(col).last()

        return (
            df.sort("timestamp")
            .group_by_dynamic("timestamp", every=interval)
            .agg(**agg_dict)
            .drop_nulls()
        )
