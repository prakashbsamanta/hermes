"""Abstract base classes for data sinks."""

from abc import ABC, abstractmethod
from pathlib import Path

import polars as pl


class DataSink(ABC):
    """Abstract base class for data sinks (storage destinations)."""

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
