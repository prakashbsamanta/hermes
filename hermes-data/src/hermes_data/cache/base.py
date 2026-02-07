"""Abstract base class for cache providers."""

from abc import ABC, abstractmethod
from typing import List, Optional

import polars as pl


class CacheProvider(ABC):
    """Abstract interface for caching market data.
    
    This enables swapping between in-memory cache, Redis, etc.
    """

    @abstractmethod
    def get(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Optional[pl.DataFrame]:
        """Retrieve cached data if available.
        
        Args:
            symbols: List of symbols in the cache key
            start_date: Start date component of cache key
            end_date: End date component of cache key
            
        Returns:
            Cached DataFrame or None if not found
        """
        pass

    @abstractmethod
    def set(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
        data: pl.DataFrame,
    ) -> None:
        """Store data in cache.
        
        Args:
            symbols: List of symbols for cache key
            start_date: Start date component of cache key
            end_date: End date component of cache key
            data: DataFrame to cache
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached data."""
        pass

    @abstractmethod
    def stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with hit_count, miss_count, size_mb, etc.
        """
        pass
