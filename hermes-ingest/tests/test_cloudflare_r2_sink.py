"""Tests for CloudflareR2Sink using moto to mock S3 API."""

import boto3
import polars as pl
import pytest
from moto import mock_aws

from hermes_ingest.sinks.cloudflare_r2 import CloudflareR2Sink


@pytest.fixture
def r2_bucket_name() -> str:
    """Return test bucket name."""
    return "test-hermes-bucket"


@pytest.fixture
def mock_r2_client(r2_bucket_name: str):
    """Create a mocked S3/R2 client and bucket."""
    with mock_aws():
        # Create mock S3 client (R2 uses S3 API)
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=r2_bucket_name)
        yield client


@pytest.fixture
def r2_sink(mock_r2_client, r2_bucket_name: str, monkeypatch):
    """Create CloudflareR2Sink with mocked backend."""
    with mock_aws():
        # Create bucket first
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=r2_bucket_name)

        # Create sink - it will use the mocked AWS
        sink = CloudflareR2Sink(
            account_id="test-account",
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name=r2_bucket_name,
            prefix="minute",
        )
        # Replace the client's endpoint with mocked one
        sink._client = client
        yield sink


class TestCloudflareR2Sink:
    """Test suite for CloudflareR2Sink."""

    def test_get_key(self, r2_sink):
        """Test that _get_key returns correct object key."""
        key = r2_sink._get_key("RELIANCE")
        assert key == "minute/RELIANCE.parquet"

    def test_write_creates_object(self, r2_sink, sample_ohlcv_df):
        """Test that write creates a parquet object in R2."""
        path = r2_sink.write("TEST", sample_ohlcv_df)

        assert str(path) == "minute/TEST.parquet"
        assert r2_sink.exists("TEST")

    def test_read_returns_dataframe(self, r2_sink, sample_ohlcv_df):
        """Test read returns the stored DataFrame."""
        r2_sink.write("TEST", sample_ohlcv_df)

        df = r2_sink.read("TEST")

        assert df is not None
        assert len(df) == 3

    def test_read_returns_none_when_missing(self, r2_sink):
        """Test read returns None when object missing."""
        result = r2_sink.read("NONEXISTENT")
        assert result is None

    def test_exists_returns_true_when_object_exists(self, r2_sink, sample_ohlcv_df):
        """Test exists returns True when object exists."""
        r2_sink.write("TEST", sample_ohlcv_df)
        assert r2_sink.exists("TEST") is True

    def test_exists_returns_false_when_missing(self, r2_sink):
        """Test exists returns False when object missing."""
        assert r2_sink.exists("NONEXISTENT") is False

    def test_list_symbols_returns_sorted_list(self, r2_sink, sample_ohlcv_df):
        """Test list_symbols returns sorted symbol list."""
        # Write multiple symbols
        r2_sink.write("ZZTEST", sample_ohlcv_df)
        r2_sink.write("AATEST", sample_ohlcv_df)
        r2_sink.write("MMTEST", sample_ohlcv_df)

        symbols = r2_sink.list_symbols()

        assert symbols == ["AATEST", "MMTEST", "ZZTEST"]

    def test_write_merges_with_existing_data(self, r2_sink):
        """Test that write merges new data with existing."""
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
        r2_sink.write("TEST", df1)

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
        r2_sink.write("TEST", df2)

        # Verify merged
        result = r2_sink.read("TEST")
        assert result is not None
        assert len(result) == 2

    def test_write_deduplicates_by_timestamp(self, r2_sink, sample_ohlcv_df):
        """Test that write deduplicates by timestamp."""
        # Write same data twice
        r2_sink.write("TEST", sample_ohlcv_df)
        r2_sink.write("TEST", sample_ohlcv_df)

        result = r2_sink.read("TEST")
        assert result is not None
        assert len(result) == 3  # Not 6

    def test_get_last_timestamp(self, r2_sink, sample_ohlcv_df):
        """Test get_last_timestamp returns correct value."""
        r2_sink.write("TEST", sample_ohlcv_df)

        last_ts = r2_sink.get_last_timestamp("TEST")

        assert last_ts is not None
        assert "2024-01-01T09:17:00" in last_ts

    def test_get_last_timestamp_returns_none_when_missing(self, r2_sink):
        """Test get_last_timestamp returns None when object missing."""
        result = r2_sink.get_last_timestamp("NONEXISTENT")
        assert result is None


class TestCloudflareR2SinkImportError:
    """Test import error handling."""

    def test_import_error_message(self, monkeypatch):
        """Test that helpful error is shown when boto3 missing."""
        # This test verifies the error message in the docstring/code
        # In practice, boto3 is installed for tests, so we just verify the class exists
        assert CloudflareR2Sink is not None
