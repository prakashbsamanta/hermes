"""Tests for LocalFileProvider."""

from pathlib import Path

import polars as pl
import pytest

from hermes_data.providers.local import LocalFileProvider


class TestLocalFileProvider:
    """Tests for the LocalFileProvider class."""

    def test_init_with_valid_path(self, temp_data_dir: Path):
        """Should initialize successfully with valid data directory."""
        provider = LocalFileProvider(temp_data_dir)
        assert provider.data_dir == temp_data_dir

    def test_init_with_invalid_path(self):
        """Should raise FileNotFoundError for invalid path."""
        with pytest.raises(FileNotFoundError):
            LocalFileProvider("/nonexistent/path")

    def test_list_symbols(self, temp_data_dir: Path):
        """Should list all available symbols."""
        provider = LocalFileProvider(temp_data_dir)
        symbols = provider.list_symbols()
        
        assert len(symbols) == 2
        assert "ANOTHERSYM" in symbols
        assert "TESTSYM" in symbols

    def test_load_single_symbol(self, temp_data_dir: Path):
        """Should load data for a single symbol."""
        provider = LocalFileProvider(temp_data_dir)
        df = provider.load(["TESTSYM"])
        
        assert len(df) == 100
        assert "timestamp" in df.columns
        assert "open" in df.columns
        assert "close" in df.columns
        assert "symbol" in df.columns
        assert df["symbol"][0] == "TESTSYM"

    def test_load_multiple_symbols(self, temp_data_dir: Path):
        """Should load and combine data for multiple symbols."""
        provider = LocalFileProvider(temp_data_dir)
        df = provider.load(["TESTSYM", "ANOTHERSYM"])
        
        assert len(df) == 200  # 100 rows each
        symbols = df["symbol"].unique().to_list()
        assert set(symbols) == {"TESTSYM", "ANOTHERSYM"}

    def test_load_with_date_filter(self, temp_data_dir: Path):
        """Should apply date filters correctly."""
        provider = LocalFileProvider(temp_data_dir)
        df = provider.load(["TESTSYM"], start_date="2024-01-01")
        
        assert len(df) > 0
        assert len(df) <= 100

    def test_load_nonexistent_symbol(self, temp_data_dir: Path):
        """Should raise ValueError when no data is available."""
        provider = LocalFileProvider(temp_data_dir)
        
        with pytest.raises(ValueError, match="No data loaded"):
            provider.load(["NONEXISTENT"])

    def test_get_date_range(self, temp_data_dir: Path):
        """Should return correct date range for a symbol."""
        provider = LocalFileProvider(temp_data_dir)
        start, end = provider.get_date_range("TESTSYM")
        
        assert start == "2024-01-01"
        assert end == "2024-01-01"  # Same day for our test data

    def test_health_check(self, temp_data_dir: Path):
        """Should return True for healthy provider."""
        provider = LocalFileProvider(temp_data_dir)
        assert provider.health_check() is True

    def test_data_guard_filters_invalid_prices(self, temp_data_dir: Path):
        """Should filter out rows with invalid prices."""
        # Create data with some invalid prices
        import datetime
        
        bad_data = pl.DataFrame({
            "timestamp": [
                datetime.datetime(2024, 1, 1, 9, 15),
                datetime.datetime(2024, 1, 1, 9, 16),
                datetime.datetime(2024, 1, 1, 9, 17),
            ],
            "open": [100.0, 0.0, 100.0],  # Second row invalid
            "high": [101.0, 101.0, 101.0],
            "low": [99.0, 99.0, 99.0],
            "close": [100.5, 100.5, 100.5],
            "volume": [1000, 1000, 1000],
        })
        bad_data.write_parquet(temp_data_dir / "BADSYM.parquet")
        
        provider = LocalFileProvider(temp_data_dir)
        df = provider.load(["BADSYM"])
        
        # Invalid row should be filtered
        assert len(df) == 2
