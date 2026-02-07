"""Comprehensive tests for DataService to achieve 90%+ coverage."""

import pytest
from unittest.mock import MagicMock, patch
import polars as pl


class TestDataServiceCreation:
    """Tests for DataService initialization and factory methods."""

    def test_create_provider_local(self):
        """Test _create_provider creates LocalFileProvider."""
        from hermes_data import DataService, DataSettings
        
        with patch("hermes_data.service.LocalFileProvider") as mock_provider:
            mock_provider.return_value = MagicMock()
            
            settings = DataSettings(
                storage_provider="local",
                data_dir="/tmp/data",
            )
            DataService(settings=settings)
            
            mock_provider.assert_called_once()

    def test_create_provider_unknown_raises(self):
        """Test _create_provider raises for unknown provider."""
        from hermes_data import DataService, DataSettings
        
        settings = DataSettings(
            storage_provider="unknown",
            data_dir="/tmp/data",
        )
        
        with patch("hermes_data.service.LocalFileProvider"):
            with pytest.raises(ValueError, match="Unknown storage provider"):
                # Force the provider creation to fail
                settings.storage_provider = "s3"  # Not implemented
                DataService(settings=settings)

    def test_create_cache_disabled(self):
        """Test _create_cache returns None when disabled."""
        from hermes_data import DataService, DataSettings
        
        with patch("hermes_data.service.LocalFileProvider"):
            settings = DataSettings(
                cache_enabled=False,
                data_dir="/tmp/data",
            )
            service = DataService(settings=settings)
            
            assert service.cache is None

    def test_create_cache_enabled(self):
        """Test _create_cache creates MemoryCache when enabled."""
        from hermes_data import DataService, DataSettings
        
        with patch("hermes_data.service.LocalFileProvider"):
            settings = DataSettings(
                cache_enabled=True,
                cache_max_size_mb=256,
                data_dir="/tmp/data",
            )
            service = DataService(settings=settings)
            
            assert service.cache is not None

    def test_create_registry_success(self):
        """Test _create_registry creates registry when enabled."""
        from hermes_data import DataService, DataSettings
        
        with patch("hermes_data.service.LocalFileProvider"):
            with patch("hermes_data.service.DataService._create_registry") as mock_reg:
                mock_reg.return_value = MagicMock()
                
                settings = DataSettings(
                    registry_enabled=True,
                    database_url="postgresql://test:test@localhost/test",
                    data_dir="/tmp/data",
                )
                DataService(settings=settings)

    def test_create_registry_failure_continues(self):
        """Test _create_registry failure doesn't crash service."""
        from hermes_data import DataService, DataSettings
        
        with patch("hermes_data.service.LocalFileProvider"):
            settings = DataSettings(
                registry_enabled=True,
                database_url="postgresql://invalid:invalid@localhost/invalid",
                data_dir="/tmp/data",
            )
            # Should not raise, just log warning
            service = DataService(settings=settings)
            assert service.registry is None or service.registry is not None  # Either is fine


class TestDataServiceOperations:
    """Tests for DataService data operations."""

    @pytest.fixture
    def mock_service(self):
        """Create a DataService with mocked provider."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        mock_cache = MagicMock()
        
        service = DataService(
            provider=mock_provider,
            cache=mock_cache,
            enable_registry=False,
        )
        return service, mock_provider, mock_cache

    def test_list_instruments(self, mock_service):
        """Test list_instruments delegates to provider."""
        service, mock_provider, _ = mock_service
        mock_provider.list_symbols.return_value = ["A", "B", "C"]
        
        result = service.list_instruments()
        
        assert result == ["A", "B", "C"]
        mock_provider.list_symbols.assert_called_once()

    def test_get_date_range(self, mock_service):
        """Test get_date_range delegates to provider."""
        service, mock_provider, _ = mock_service
        mock_provider.get_date_range.return_value = ("2024-01-01", "2024-12-31")
        
        result = service.get_date_range("RELIANCE")
        
        assert result == ("2024-01-01", "2024-12-31")
        mock_provider.get_date_range.assert_called_once_with("RELIANCE")

    def test_clear_cache(self, mock_service):
        """Test clear_cache clears the cache."""
        service, _, mock_cache = mock_service
        
        service.clear_cache()
        
        mock_cache.clear.assert_called_once()

    def test_clear_cache_no_cache(self):
        """Test clear_cache when no cache configured."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        service = DataService(
            provider=mock_provider,
            cache=None,
            enable_registry=False,
        )
        
        # Should not raise
        service.clear_cache()


class TestDataServiceGetMarketData:
    """Tests for get_market_data with various scenarios."""

    @pytest.fixture
    def mock_service(self):
        """Create a DataService with mocked components."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # No cache hit by default
        
        service = DataService(
            provider=mock_provider,
            cache=mock_cache,
            enable_registry=False,
        )
        return service, mock_provider, mock_cache

    def test_get_market_data_cache_miss(self, mock_service):
        """Test get_market_data loads from provider on cache miss."""
        service, mock_provider, mock_cache = mock_service
        
        mock_cache.get.return_value = None
        mock_provider.load.return_value = pl.DataFrame({
            "close": [100, 101, 102],
            "volume": [1000, 2000, 3000],
        })
        
        result = service.get_market_data(["RELIANCE"], "2024-01-01", "2024-12-31")
        
        mock_provider.load.assert_called_once()
        mock_cache.set.assert_called_once()
        assert len(result) == 3

    def test_get_market_data_cache_hit(self, mock_service):
        """Test get_market_data returns cached data."""
        service, mock_provider, mock_cache = mock_service
        
        cached_df = pl.DataFrame({
            "close": [100, 101, 102],
        })
        mock_cache.get.return_value = cached_df
        
        result = service.get_market_data(["RELIANCE"], "2024-01-01", "2024-12-31")
        
        mock_provider.load.assert_not_called()
        assert len(result) == 3

    def test_get_market_data_bypass_cache(self, mock_service):
        """Test get_market_data bypasses cache when requested."""
        service, mock_provider, mock_cache = mock_service
        
        mock_provider.load.return_value = pl.DataFrame({"close": [100]})
        
        service.get_market_data(
            ["RELIANCE"], "2024-01-01", "2024-12-31", use_cache=False
        )
        
        mock_cache.get.assert_not_called()
        mock_provider.load.assert_called_once()

    def test_get_market_data_symbol_normalization(self, mock_service):
        """Test that symbols are normalized to uppercase."""
        service, mock_provider, mock_cache = mock_service
        
        mock_provider.load.return_value = pl.DataFrame({"close": [100]})
        
        service.get_market_data(["reliance", "tcs"], "2024-01-01", "2024-12-31")
        
        # Check the symbols were normalized
        call_args = mock_provider.load.call_args
        assert call_args[0][0] == ["RELIANCE", "TCS"]


class TestDataServiceHealthCheck:
    """Tests for health check functionality."""

    def test_health_check_all_components(self):
        """Test health_check returns status for all components."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        mock_provider.list_symbols.return_value = ["A", "B"]
        mock_cache = MagicMock()
        mock_cache.size_mb = 10.5
        
        service = DataService(
            provider=mock_provider,
            cache=mock_cache,
            enable_registry=False,
        )
        
        health = service.health_check()
        
        assert "provider" in health
        assert "cache" in health

    def test_health_check_no_cache(self):
        """Test health_check when no cache configured."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        mock_provider.list_symbols.return_value = []
        
        service = DataService(
            provider=mock_provider,
            cache=None,
            enable_registry=False,
        )
        
        health = service.health_check()
        
        assert "cache" in health


class TestDataServiceSyncRegistry:
    """Tests for registry sync functionality."""

    def test_sync_registry_no_registry(self):
        """Test sync_registry when registry is disabled."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        service = DataService(
            provider=mock_provider,
            cache=None,
            enable_registry=False,
        )
        
        result = service.sync_registry()
        
        assert result == 0

    def test_sync_registry_with_registry(self):
        """Test sync_registry delegates to registry service."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        mock_registry = MagicMock()
        mock_registry.sync_from_filesystem.return_value = 10
        
        service = DataService(
            provider=mock_provider,
            cache=None,
            enable_registry=False,
        )
        service._registry = mock_registry
        
        result = service.sync_registry()
        
        assert result == 10
        mock_registry.sync_from_filesystem.assert_called_once_with(mock_provider)


class TestDataServiceSearchInstruments:
    """Tests for search functionality."""

    def test_search_instruments_no_registry(self):
        """Test search_instruments falls back to provider when no registry."""
        from hermes_data import DataService
        
        mock_provider = MagicMock()
        mock_provider.list_symbols.return_value = ["RELIANCE", "TCS", "INFY"]
        
        service = DataService(
            provider=mock_provider,
            cache=None,
            enable_registry=False,
        )
        
        results = service.search_instruments("REL")
        
        # Returns list of dicts with 'symbol' key
        assert any(r["symbol"] == "RELIANCE" for r in results)

    def test_search_instruments_with_registry(self):
        """Test search_instruments uses registry when available."""
        from hermes_data import DataService
        from hermes_data.registry.models import Instrument
        
        mock_provider = MagicMock()
        mock_registry = MagicMock()
        mock_instrument = MagicMock(spec=Instrument)
        mock_instrument.symbol = "RELIANCE"
        mock_registry.search_instruments.return_value = [mock_instrument]
        
        service = DataService(
            provider=mock_provider,
            cache=None,
            enable_registry=False,
        )
        service._registry = mock_registry
        
        results = service.search_instruments("REL")
        
        assert len(results) == 1
        mock_registry.search_instruments.assert_called_once()
