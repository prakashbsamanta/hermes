"""Test fixtures for hermes-data tests."""

import tempfile
from pathlib import Path

import polars as pl
import pytest


@pytest.fixture
def sample_ohlcv_data() -> pl.DataFrame:
    """Create sample OHLCV data for testing."""
    import datetime
    
    base_date = datetime.datetime(2024, 1, 1, 9, 15)
    rows = []
    
    for i in range(100):
        timestamp = base_date + datetime.timedelta(minutes=i)
        price = 100.0 + (i * 0.1)
        rows.append({
            "timestamp": timestamp,
            "open": price,
            "high": price + 0.5,
            "low": price - 0.3,
            "close": price + 0.2,
            "volume": 1000 + i * 10,
        })
    
    return pl.DataFrame(rows)


@pytest.fixture
def temp_data_dir(sample_ohlcv_data: pl.DataFrame) -> Path:
    """Create a temporary directory with sample parquet files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir)
        
        # Write sample data for two symbols
        sample_ohlcv_data.write_parquet(data_path / "TESTSYM.parquet")
        sample_ohlcv_data.write_parquet(data_path / "ANOTHERSYM.parquet")
        
        yield data_path


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset the settings cache between tests."""
    from hermes_data.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
