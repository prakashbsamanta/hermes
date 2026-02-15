"""Abstract base classes for data sources."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import polars as pl


class DataSource(ABC):
    """Abstract base class for data sources (brokers, exchanges, etc.)."""

    @abstractmethod
    async def fetch(
        self,
        symbol: str,
        token: int,
        start_date: str,
        end_date: str,
    ) -> pl.DataFrame | None:
        """Fetch OHLCV data for a symbol.

        Args:
            symbol: Instrument symbol (e.g., "RELIANCE")
            token: Instrument token (broker-specific identifier)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with OHLCV data, or None if fetch failed
        """
        pass

    def fetch_chunks(
        self,
        symbol: str,
        token: int,
        start_date: str,
        end_date: str,
    ) -> AsyncIterator[tuple[pl.DataFrame, str, str]]:
        """Fetch OHLCV data in chunks as async iterator.

        Yields chunks as they're fetched for incremental processing.

        Args:
            symbol: Instrument symbol (e.g., "RELIANCE")
            token: Instrument token (broker-specific identifier)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Yields:
            Tuples of (chunk_df, chunk_start_date, chunk_end_date)
        """
        # Default implementation: not supported
        raise NotImplementedError("fetch_chunks not implemented for this source")

    @abstractmethod
    def list_instruments(self) -> pl.DataFrame:
        """List available instruments.

        Returns:
            DataFrame with columns: instrument_token, tradingsymbol, name, etc.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources (close connections, etc.)."""
        pass

