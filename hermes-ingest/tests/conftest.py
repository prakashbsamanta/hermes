"""Pytest configuration and fixtures for hermes-ingest tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
import pytest


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_ohlcv_df():
    """Create a sample OHLCV DataFrame for testing."""
    return pl.DataFrame({
        "timestamp": [
            "2024-01-01T09:15:00",
            "2024-01-01T09:16:00",
            "2024-01-01T09:17:00",
        ],
        "open": [100.0, 101.0, 102.0],
        "high": [101.0, 102.0, 103.0],
        "low": [99.0, 100.0, 101.0],
        "close": [100.5, 101.5, 102.5],
        "volume": [1000, 1100, 1200],
        "oi": [0, 0, 0],
    }).with_columns(
        pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
    )


@pytest.fixture
def sample_instruments_df():
    """Create a sample instruments DataFrame for testing."""
    return pl.DataFrame({
        "instrument_token": [738561, 341249, 779521],
        "tradingsymbol": ["RELIANCE", "TCS", "INFY"],
        "name": ["Reliance Industries", "Tata Consultancy", "Infosys"],
        "instrument_type": ["EQ", "EQ", "EQ"],
        "exchange": ["NSE", "NSE", "NSE"],
    })
