"""Abstract base classes for data sinks."""

import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

import polars as pl

Compression = Literal['lz4', 'uncompressed', 'snappy', 'gzip', 'brotli', 'zstd']

logger = logging.getLogger(__name__)




class DataSink(ABC):
    """Abstract base class for data sinks (storage destinations).

    Provides shared utilities for Parquet serialization (with compression),
    data merging/deduplication, and resume logic. Subclasses only need to
    implement the storage-specific read/write/exists/list operations.
    """

    def __init__(self, compression: Compression = "zstd"):
        """Initialize the base sink.

        Args:
            compression: Parquet compression codec. One of:
                'zstd' (default, best balance), 'snappy', 'lz4',
                'gzip', or 'uncompressed'.
        """
        self.compression = compression

    # ------------------------------------------------------------------
    # Parquet helpers — centralized compression
    # ------------------------------------------------------------------

    def _to_parquet_bytes(self, df: pl.DataFrame) -> bytes:
        """Serialize a DataFrame to compressed Parquet bytes.

        Uses the compression codec configured at init time.
        """
        buffer = io.BytesIO()
        df.write_parquet(buffer, compression=self.compression)
        return buffer.getvalue()

    def _from_parquet_bytes(self, data: bytes) -> pl.DataFrame:
        """Deserialize Parquet bytes to a DataFrame.

        Compression is auto-detected — works with any codec.
        """
        return pl.read_parquet(io.BytesIO(data))

    # ------------------------------------------------------------------
    # Data merge helper — deduplicate + sort by timestamp
    # ------------------------------------------------------------------

    def _merge_and_deduplicate(
        self, new_df: pl.DataFrame, existing_df: pl.DataFrame | None
    ) -> pl.DataFrame:
        """Merge new data with existing, deduplicate by timestamp, and sort.

        Args:
            new_df: Newly fetched DataFrame
            existing_df: Previously stored DataFrame, or None

        Returns:
            Merged, deduplicated, sorted DataFrame
        """
        if existing_df is not None:
            new_df = pl.concat([existing_df, new_df])
        return new_df.unique(subset=["timestamp"]).sort("timestamp")

    # ------------------------------------------------------------------
    # Resume helper — get last timestamp for incremental fetching
    # ------------------------------------------------------------------

    def get_last_timestamp(self, symbol: str) -> str | None:
        """Get the last timestamp for a symbol (for resume logic).

        Returns:
            ISO format timestamp string, or None if not found
        """
        df = self.read(symbol)
        if df is None or df.is_empty():
            return None

        last_ts = df.select(pl.col("timestamp").max()).item()
        if last_ts is None:
            return None

        # Handle timezone-aware timestamps
        if hasattr(last_ts, "tzinfo") and last_ts.tzinfo is not None:
            last_ts = last_ts.replace(tzinfo=None)

        return str(last_ts.isoformat())

    # ------------------------------------------------------------------
    # Abstract methods — subclasses implement storage-specific logic
    # ------------------------------------------------------------------

    @abstractmethod
    def write(self, symbol: str, df: pl.DataFrame) -> Path:
        """Write OHLCV data for a symbol.

        Args:
            symbol: Instrument symbol (e.g., "RELIANCE")
            df: DataFrame with OHLCV data

        Returns:
            Path to the written file/resource
        """
        pass

    @abstractmethod
    def read(self, symbol: str) -> pl.DataFrame | None:
        """Read existing data for a symbol (for resume logic).

        Args:
            symbol: Instrument symbol

        Returns:
            DataFrame with existing data, or None if not found
        """
        pass

    @abstractmethod
    def exists(self, symbol: str) -> bool:
        """Check if data exists for a symbol.

        Args:
            symbol: Instrument symbol

        Returns:
            True if data exists
        """
        pass

    @abstractmethod
    def list_symbols(self) -> list[str]:
        """List all available symbols in the sink.

        Returns:
            List of symbol names
        """
        pass
