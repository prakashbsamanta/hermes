import os
import polars as pl
from typing import List
from api.models import CandlePoint
from engine.loader import DataLoader
import logging

class MarketDataService:
    def __init__(self, data_sources: List[str] | None = None):
        # Setup Data Directory
        # We try to be robust finding the data dir.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir) # hermes-backend
        base_dir = os.path.dirname(parent_dir) # TheForge/hermes/
        
        self.DATA_DIR_CANDIDATES = data_sources or [
            os.path.join(parent_dir, "data", "minute"),
            os.path.join(base_dir, "hermes-backend", "data", "minute"),
            "hermes-backend/data/minute",
            "data/minute"
        ]

    def get_data_dir(self) -> str:
        for d in self.DATA_DIR_CANDIDATES:
            if os.path.exists(d):
                return d
        raise FileNotFoundError("Could not find data/minute directory.")

    def list_instruments(self) -> List[str]:
        try:
            data_dir = self.get_data_dir()
            # List all parquet files
            files = [f for f in os.listdir(data_dir) if f.endswith(".parquet")]
            # Extract symbol names (filename without extension)
            symbols = [os.path.splitext(f)[0] for f in files]
            return sorted(symbols)
        except Exception as e:
            logging.warning(f"Could not list instruments: {str(e)}")
            return []

    def load_and_resample(self, symbol: str, timeframe: str = "1h", start_date: str | None = None, end_date: str | None = None) -> pl.DataFrame:
        data_dir = self.get_data_dir()
        loader = DataLoader(data_dir=data_dir)
        try:
            df = loader.load_data([symbol.upper()], start_date=start_date, end_date=end_date)
            # If start_date is provided but data is missing/empty, loader raises ValueError
        except ValueError as ve:
             # Handle empty data specifically if needed
             raise ve
        except Exception:
            raise FileNotFoundError(f"Data not found for {symbol}")

        return self.resample_data(df, interval=timeframe)

    def get_candles(self, symbol: str, timeframe: str = "1h") -> List[CandlePoint]:
        chart_df = self.load_and_resample(symbol, timeframe)
        
        # Convert to CandlePoint list
        candles = []
        rows = chart_df.rows(named=True)
        for row in rows:
            ts = int(row["timestamp"].timestamp())
            candles.append(CandlePoint(
                time=ts,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"]
            ))
        return candles

    @staticmethod
    def resample_data(df: pl.DataFrame, interval: str = "1h") -> pl.DataFrame:
        """Downsample datasets to specified interval for visualization."""
        
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
        exclude = {"timestamp", "open", "high", "low", "close", "volume", "signal", "position", "strategy_return", "equity", "trade_action"}
        for col in df.columns:
            if col not in exclude and df[col].dtype in [pl.Float64, pl.Float32]:
                agg_dict[col] = pl.col(col).last()

        return (
            df.sort("timestamp")
            .group_by_dynamic("timestamp", every=interval)
            .agg(**agg_dict)
            .drop_nulls()
        )
