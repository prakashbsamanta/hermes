"""Abstract base classes for data sources."""

from abc import ABC, abstractmethod

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
