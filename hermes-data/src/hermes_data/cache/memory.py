"""In-memory LRU cache implementation."""

import hashlib
import logging
import threading
from collections import OrderedDict
from typing import List, Optional

import polars as pl

from .base import CacheProvider

logger = logging.getLogger(__name__)


class MemoryCache(CacheProvider):
    """Thread-safe in-memory cache with LRU eviction.
    
    Uses an OrderedDict for O(1) access and LRU tracking.
    Evicts oldest entries when memory limit is exceeded.
    """

    def __init__(self, max_size_mb: int | float = 512):
        """Initialize the memory cache.
        
        Args:
            max_size_mb: Maximum cache size in megabytes
        """
        self.max_size_mb = max_size_mb
        self._cache: OrderedDict[str, pl.DataFrame] = OrderedDict()
        self._sizes: dict[str, float] = {}  # Track size per key
        self._current_size_mb: float = 0.0
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def _make_key(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> str:
        """Create a deterministic cache key."""
        raw = f"{','.join(sorted(symbols))}:{start_date or ''}:{end_date or ''}"
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()

    def get(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Optional[pl.DataFrame]:
        """Retrieve cached data if available."""
        key = self._make_key(symbols, start_date, end_date)
        
        with self._lock:
            if key in self._cache:
                self._hits += 1
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                logger.debug(f"Cache HIT for key {key[:8]}...")
                return self._cache[key]
            
            self._misses += 1
            logger.debug(f"Cache MISS for key {key[:8]}...")
            return None

    def set(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
        data: pl.DataFrame,
    ) -> None:
        """Store data in cache with LRU eviction."""
        key = self._make_key(symbols, start_date, end_date)
        
        # Estimate size
        size_mb = data.estimated_size("mb")
        
        # Don't cache if single item exceeds limit
        if size_mb > self.max_size_mb:
            logger.warning(
                f"Data too large to cache: {size_mb:.1f}MB > {self.max_size_mb}MB limit"
            )
            return

        with self._lock:
            # Evict if already exists (will be replaced)
            if key in self._cache:
                self._current_size_mb -= self._sizes[key]
                del self._cache[key]
                del self._sizes[key]

            # Evict LRU entries until we have space
            while self._current_size_mb + size_mb > self.max_size_mb and self._cache:
                oldest_key, _ = self._cache.popitem(last=False)
                self._current_size_mb -= self._sizes.pop(oldest_key)
                logger.debug(f"Evicted cache entry {oldest_key[:8]}...")

            # Insert new entry
            self._cache[key] = data
            self._sizes[key] = size_mb
            self._current_size_mb += size_mb
            logger.debug(
                f"Cached {size_mb:.1f}MB for key {key[:8]}... "
                f"(total: {self._current_size_mb:.1f}/{self.max_size_mb}MB)"
            )

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._sizes.clear()
            self._current_size_mb = 0.0
            self._hits = 0
            self._misses = 0
            logger.info("Cache cleared")

    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                "entries": len(self._cache),
                "size_mb": round(self._current_size_mb, 2),
                "max_size_mb": self.max_size_mb,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 1),
            }
