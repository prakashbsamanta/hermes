"""Tests for MemoryCache."""

import polars as pl

from hermes_data.cache.memory import MemoryCache


class TestMemoryCache:
    """Tests for the MemoryCache class."""

    def test_get_returns_none_for_missing_key(self):
        """Should return None for missing cache entries."""
        cache = MemoryCache(max_size_mb=100)
        result = cache.get(["SYM"], "2024-01-01", "2024-12-31")
        assert result is None

    def test_set_and_get(self, sample_ohlcv_data: pl.DataFrame):
        """Should store and retrieve data correctly."""
        cache = MemoryCache(max_size_mb=100)
        symbols = ["TESTSYM"]
        start = "2024-01-01"
        end = "2024-12-31"
        
        cache.set(symbols, start, end, sample_ohlcv_data)
        result = cache.get(symbols, start, end)
        
        assert result is not None
        assert len(result) == len(sample_ohlcv_data)

    def test_different_keys_are_separate(self, sample_ohlcv_data: pl.DataFrame):
        """Should store different keys separately."""
        cache = MemoryCache(max_size_mb=100)
        
        cache.set(["SYM1"], "2024-01-01", None, sample_ohlcv_data)
        cache.set(["SYM2"], "2024-01-01", None, sample_ohlcv_data)
        
        assert cache.get(["SYM1"], "2024-01-01", None) is not None
        assert cache.get(["SYM2"], "2024-01-01", None) is not None
        assert cache.get(["SYM3"], "2024-01-01", None) is None

    def test_lru_eviction(self, sample_ohlcv_data: pl.DataFrame):
        """Should evict oldest entries when size limit is exceeded."""
        # Get actual size of sample data
        size_mb = sample_ohlcv_data.estimated_size("mb")
        
        # Cache that can only hold ~2 entries
        cache = MemoryCache(max_size_mb=max(0.001, size_mb * 2.5))
        
        # Add 5 entries - should trigger eviction
        for i in range(5):
            cache.set([f"SYM{i}"], None, None, sample_ohlcv_data)
        
        # Some entries should be evicted
        stats = cache.stats()
        assert stats["entries"] < 5

    def test_stats_tracking(self, sample_ohlcv_data: pl.DataFrame):
        """Should track cache statistics correctly."""
        cache = MemoryCache(max_size_mb=100)
        
        # Initial stats
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Miss
        cache.get(["SYM"], None, None)
        
        # Set then hit
        cache.set(["SYM"], None, None, sample_ohlcv_data)
        cache.get(["SYM"], None, None)
        
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["entries"] == 1

    def test_clear(self, sample_ohlcv_data: pl.DataFrame):
        """Should clear all cache entries."""
        cache = MemoryCache(max_size_mb=100)
        cache.set(["SYM"], None, None, sample_ohlcv_data)
        
        cache.clear()
        
        assert cache.get(["SYM"], None, None) is None
        stats = cache.stats()
        assert stats["entries"] == 0
        assert stats["size_mb"] == 0

    def test_thread_safety(self, sample_ohlcv_data: pl.DataFrame):
        """Should be thread-safe for concurrent access."""
        import threading
        
        cache = MemoryCache(max_size_mb=100)
        errors = []
        
        def writer():
            try:
                for i in range(50):
                    cache.set([f"SYM{i}"], None, None, sample_ohlcv_data)
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for i in range(50):
                    cache.get([f"SYM{i}"], None, None)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
