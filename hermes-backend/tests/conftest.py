"""Test fixtures for hermes-backend tests."""

import pytest
import polars as pl
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_df():
    """Generate 200 rows of minute data for testing."""
    base_time = datetime(2023, 1, 1, 10, 0, 0)
    timestamps = [base_time + timedelta(minutes=i) for i in range(200)]

    # Random walk for close
    np.random.seed(42)
    close = np.cumprod(1 + np.random.normal(0, 0.001, 200)) * 100

    return pl.DataFrame(
        {
            "timestamp": timestamps,
            "open": close,  # Simple approximation
            "high": close * 1.001,
            "low": close * 0.999,
            "close": close,
            "volume": [1000] * 200,
            "symbol": ["TEST"] * 200,
        }
    )


@pytest.fixture
def temp_data_dir(tmp_path, sample_ohlcv_df):
    """Create a temporary data directory with sample parquet file."""
    d = tmp_path / "data"
    d.mkdir()
    d_minute = d / "minute"
    d_minute.mkdir()

    # Write sample parquet file
    sample_ohlcv_df.write_parquet(d_minute / "TEST_SYM.parquet")

    return str(d_minute)


@pytest.fixture
def mock_data_service(temp_data_dir):
    """Create a DataService pointing to the temp data directory."""
    from hermes_data import DataService, DataSettings
    from hermes_data.providers.local import LocalFileProvider
    
    provider = LocalFileProvider(temp_data_dir)
    settings = DataSettings(data_dir=temp_data_dir, cache_enabled=False)
    return DataService(provider=provider, settings=settings)


@pytest.fixture
def mock_market_data_service(mock_data_service):
    """Create a MarketDataService with mocked data service."""
    from services.market_data_service import MarketDataService
    
    return MarketDataService(data_service=mock_data_service)


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset the hermes_data settings cache between tests."""
    from hermes_data.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
