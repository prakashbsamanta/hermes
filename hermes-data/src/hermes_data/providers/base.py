"""Abstract base class for data providers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import polars as pl


class DataProvider(ABC):
    """Abstract interface for market data access.
    
    This defines the contract that all storage adapters must implement,
    enabling easy switching between local files, S3, GCS, etc.
    """

    @abstractmethod
    def load(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pl.DataFrame:
        """Load OHLCV data for given symbols within date range.
        
        Args:
            symbols: List of instrument symbols (e.g., ["RELIANCE", "INFY"])
            start_date: Optional start date in "YYYY-MM-DD" format
            end_date: Optional end date in "YYYY-MM-DD" format
            
        Returns:
            Polars DataFrame with columns: 
            [timestamp, open, high, low, close, volume, symbol]
            
        Raises:
            FileNotFoundError: If data for symbols is not found
            ValueError: If no data is available in the specified range
        """
        pass

    @abstractmethod
    def list_symbols(self) -> List[str]:
        """List all available instrument symbols.
        
        Returns:
            Sorted list of symbol names
        """
        pass

    @abstractmethod
    def get_date_range(self, symbol: str) -> Tuple[str, str]:
        """Get available date range for a symbol.
        
        Args:
            symbol: Instrument symbol
            
        Returns:
            Tuple of (start_date, end_date) in "YYYY-MM-DD" format
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify provider is accessible and has data.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass
