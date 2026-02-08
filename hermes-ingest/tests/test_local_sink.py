"""Tests for LocalFileSink."""

import polars as pl

from hermes_ingest.sinks.local import LocalFileSink


class TestLocalFileSink:
    """Test suite for LocalFileSink."""

    def test_write_creates_file(self, temp_data_dir, sample_ohlcv_df):
        """Test that write creates a parquet file."""
        sink = LocalFileSink(temp_data_dir)

        path = sink.write("TEST", sample_ohlcv_df)

        assert path.exists()
        assert path.suffix == ".parquet"
        assert path.name == "TEST.parquet"

    def test_exists_returns_true_when_file_exists(self, temp_data_dir, sample_ohlcv_df):
        """Test exists returns True when file exists."""
        sink = LocalFileSink(temp_data_dir)
        sink.write("TEST", sample_ohlcv_df)

        assert sink.exists("TEST") is True

    def test_exists_returns_false_when_file_missing(self, temp_data_dir):
        """Test exists returns False when file missing."""
        sink = LocalFileSink(temp_data_dir)

        assert sink.exists("NONEXISTENT") is False

    def test_read_returns_dataframe(self, temp_data_dir, sample_ohlcv_df):
        """Test read returns the stored DataFrame."""
        sink = LocalFileSink(temp_data_dir)
        sink.write("TEST", sample_ohlcv_df)

        df = sink.read("TEST")

        assert df is not None
        assert len(df) == 3

    def test_read_returns_none_when_file_missing(self, temp_data_dir):
        """Test read returns None when file missing."""
        sink = LocalFileSink(temp_data_dir)

        result = sink.read("NONEXISTENT")

        assert result is None

    def test_list_symbols_returns_sorted_list(self, temp_data_dir, sample_ohlcv_df):
        """Test list_symbols returns sorted symbol list."""
        sink = LocalFileSink(temp_data_dir)

        # Write multiple symbols
        sink.write("ZZTEST", sample_ohlcv_df)
        sink.write("AATEST", sample_ohlcv_df)
        sink.write("MMTEST", sample_ohlcv_df)

        symbols = sink.list_symbols()

        assert symbols == ["AATEST", "MMTEST", "ZZTEST"]

    def test_write_merges_with_existing_data(self, temp_data_dir):
        """Test that write merges new data with existing."""
        sink = LocalFileSink(temp_data_dir)

        # Write initial data
        df1 = pl.DataFrame({
            "timestamp": ["2024-01-01T09:15:00"],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000],
            "oi": [0],
        }).with_columns(
            pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
        )
        sink.write("TEST", df1)

        # Write additional data
        df2 = pl.DataFrame({
            "timestamp": ["2024-01-01T09:16:00"],
            "open": [101.0],
            "high": [102.0],
            "low": [100.0],
            "close": [101.5],
            "volume": [1100],
            "oi": [0],
        }).with_columns(
            pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
        )
        sink.write("TEST", df2)

        # Verify merged
        result = sink.read("TEST")
        assert result is not None
        assert len(result) == 2

    def test_write_deduplicates_by_timestamp(self, temp_data_dir, sample_ohlcv_df):
        """Test that write deduplicates by timestamp."""
        sink = LocalFileSink(temp_data_dir)

        # Write same data twice
        sink.write("TEST", sample_ohlcv_df)
        sink.write("TEST", sample_ohlcv_df)

        result = sink.read("TEST")
        assert result is not None
        assert len(result) == 3  # Not 6

    def test_get_last_timestamp(self, temp_data_dir, sample_ohlcv_df):
        """Test get_last_timestamp returns correct value."""
        sink = LocalFileSink(temp_data_dir)
        sink.write("TEST", sample_ohlcv_df)

        last_ts = sink.get_last_timestamp("TEST")

        assert last_ts is not None
        assert "2024-01-01T09:17:00" in last_ts

    def test_get_last_timestamp_returns_none_when_missing(self, temp_data_dir):
        """Test get_last_timestamp returns None when file missing."""
        sink = LocalFileSink(temp_data_dir)

        result = sink.get_last_timestamp("NONEXISTENT")

        assert result is None

    def test_creates_directory_if_missing(self, temp_data_dir):
        """Test that LocalFileSink creates the directory if missing."""
        nested_path = temp_data_dir / "nested" / "path"

        LocalFileSink(nested_path)

        assert nested_path.exists()
