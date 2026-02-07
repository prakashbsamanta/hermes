"""Tests for DataService."""

from pathlib import Path
from unittest.mock import patch

import polars as pl

from hermes_data import DataService, DataSettings
from hermes_data.cache.memory import MemoryCache
from hermes_data.providers.local import LocalFileProvider


class TestDataService:
    """Tests for the DataService class."""

    def test_init_with_defaults(self, temp_data_dir: Path):
        """Should initialize with default settings when HERMES_DATA_DIR is set."""
        with patch.dict("os.environ", {"HERMES_DATA_DIR": str(temp_data_dir)}):
            from hermes_data.config import get_settings
            get_settings.cache_clear()
            
            service = DataService()
            assert isinstance(service.provider, LocalFileProvider)
            assert isinstance(service.cache, MemoryCache)

    def test_init_with_custom_provider(self, temp_data_dir: Path):
        """Should use custom provider when provided."""
        provider = LocalFileProvider(temp_data_dir)
        service = DataService(provider=provider)
        
        assert service.provider is provider

    def test_init_with_cache_disabled(self, temp_data_dir: Path):
        """Should not create cache when disabled in settings."""
        settings = DataSettings(
            data_dir=str(temp_data_dir),
            cache_enabled=False,
        )
        service = DataService(settings=settings)
        
        assert service.cache is None

    def test_get_market_data(self, temp_data_dir: Path):
        """Should load market data correctly."""
        provider = LocalFileProvider(temp_data_dir)
        service = DataService(provider=provider, cache=None)
        
        df = service.get_market_data(["TESTSYM"])
        
        assert len(df) == 100
        assert "close" in df.columns

    def test_get_market_data_with_cache(self, temp_data_dir: Path):
        """Should use cache for repeated requests."""
        provider = LocalFileProvider(temp_data_dir)
        cache = MemoryCache(max_size_mb=100)
        service = DataService(provider=provider, cache=cache)
        
        # First request - cache miss
        df1 = service.get_market_data(["TESTSYM"])
        stats1 = cache.stats()
        
        # Second request - cache hit
        df2 = service.get_market_data(["TESTSYM"])
        stats2 = cache.stats()
        
        assert stats1["misses"] == 1
        assert stats1["hits"] == 0
        assert stats2["hits"] == 1
        assert len(df1) == len(df2)

    def test_get_market_data_bypass_cache(self, temp_data_dir: Path):
        """Should bypass cache when use_cache=False."""
        provider = LocalFileProvider(temp_data_dir)
        cache = MemoryCache(max_size_mb=100)
        service = DataService(provider=provider, cache=cache)
        
        # Request with cache disabled
        service.get_market_data(["TESTSYM"], use_cache=False)
        
        stats = cache.stats()
        assert stats["entries"] == 0

    def test_list_instruments(self, temp_data_dir: Path):
        """Should list all available instruments."""
        provider = LocalFileProvider(temp_data_dir)
        service = DataService(provider=provider)
        
        symbols = service.list_instruments()
        
        assert "TESTSYM" in symbols
        assert "ANOTHERSYM" in symbols

    def test_get_date_range(self, temp_data_dir: Path):
        """Should return date range for a symbol."""
        provider = LocalFileProvider(temp_data_dir)
        service = DataService(provider=provider)
        
        start, end = service.get_date_range("testsym")  # lowercase to test normalization
        
        assert start == "2024-01-01"

    def test_health_check(self, temp_data_dir: Path):
        """Should return health status."""
        provider = LocalFileProvider(temp_data_dir)
        cache = MemoryCache(max_size_mb=100)
        service = DataService(provider=provider, cache=cache)
        
        health = service.health_check()
        
        assert health["provider"]["healthy"] is True
        assert health["provider"]["type"] == "LocalFileProvider"
        assert health["cache"]["type"] == "MemoryCache"

    def test_clear_cache(self, temp_data_dir: Path, sample_ohlcv_data: pl.DataFrame):
        """Should clear the cache."""
        provider = LocalFileProvider(temp_data_dir)
        cache = MemoryCache(max_size_mb=100)
        service = DataService(provider=provider, cache=cache)
        
        # Populate cache
        service.get_market_data(["TESTSYM"])
        assert cache.stats()["entries"] == 1
        
        # Clear
        service.clear_cache()
        assert cache.stats()["entries"] == 0

    def test_symbol_normalization(self, temp_data_dir: Path):
        """Should normalize symbols to uppercase."""
        provider = LocalFileProvider(temp_data_dir)
        service = DataService(provider=provider)
        
        # Lowercase input
        df = service.get_market_data(["testsym"])
        
        assert len(df) > 0
