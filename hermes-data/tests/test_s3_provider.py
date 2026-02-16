
import io
from datetime import datetime
from unittest.mock import MagicMock, patch

import polars as pl
import pytest
from botocore.exceptions import ClientError

from hermes_data.providers.s3 import S3Provider


class TestS3Provider:
    """Tests for S3Provider."""

    @pytest.fixture
    def mock_boto3(self):
        with patch("hermes_data.providers.s3.boto3") as mock:
            yield mock

    @pytest.fixture
    def provider(self, mock_boto3):
        provider = S3Provider(
            endpoint_url="https://test.r2.cloudflarestorage.com",
            access_key_id="test_key",
            secret_access_key="test_secret",
            bucket_name="test-bucket",
        )
        # Mock exception class
        provider._client.exceptions.NoSuchKey = ClientError
        return provider

    def test_init(self, mock_boto3):
        """Should initialize S3 client."""
        S3Provider("url", "key", "secret", "bucket")
        mock_boto3.client.assert_called_once()
    
    def test_init_connection_failure(self, mock_boto3):
        """Should handle connection failure gracefully."""
        mock_boto3.client.return_value.head_bucket.side_effect = Exception("Connection failed")
        # Should not raise
        S3Provider("url", "key", "secret", "bucket")

    def test_list_symbols(self, provider):
        """Should list symbols from S3."""
        # Mock paginator
        paginator = MagicMock()
        provider._client.get_paginator.return_value = paginator
        
        paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "minute/AAPL.parquet"},
                    {"Key": "minute/GOOGL.parquet"},
                    {"Key": "minute/ignore_me.txt"},
                ]
            },
            {
                "Contents": [
                    {"Key": "minute/MSFT.parquet"},
                ]
            }
        ]
        
        symbols = provider.list_symbols()
        assert symbols == ["AAPL", "GOOGL", "MSFT"]
        
    def test_list_symbols_error(self, provider):
        """Should handle errors when listing symbols."""
        provider._client.get_paginator.side_effect = Exception("Failed")
        assert provider.list_symbols() == []

    def test_load_single_symbol(self, provider):
        """Should load data for a single symbol."""
        # Mock get_object
        df = pl.DataFrame({"symbol": ["AAPL"], "close": [150.0]})
        buffer = io.BytesIO()
        df.write_parquet(buffer)
        buffer.seek(0)
        
        provider._client.get_object.return_value = {
            "Body": MagicMock(read=lambda: buffer.getvalue())
        }
        
        result = provider.load(["AAPL"])
        assert len(result) == 1
        assert result["symbol"][0] == "AAPL"

    def test_load_multiple_symbols(self, provider):
        """Should load data for multiple symbols."""
        # AAPL
        df1 = pl.DataFrame({"symbol": ["AAPL"], "close": [150.0]})
        buf1 = io.BytesIO()
        df1.write_parquet(buf1)
        
        # MSFT
        df2 = pl.DataFrame({"symbol": ["MSFT"], "close": [300.0]})
        buf2 = io.BytesIO()
        df2.write_parquet(buf2)
        
        def get_object_side_effect(**kwargs):
            key = kwargs["Key"]
            if "AAPL" in key:
                return {"Body": MagicMock(read=lambda: buf1.getvalue())}
            elif "MSFT" in key:
                return {"Body": MagicMock(read=lambda: buf2.getvalue())}
            return None
            
        provider._client.get_object.side_effect = get_object_side_effect
        
        result = provider.load(["AAPL", "MSFT"])
        assert len(result) == 2
        assert set(result["symbol"].to_list()) == {"AAPL", "MSFT"}

    def test_load_not_found(self, provider):
        """Should handle missing symbols."""
        # Mock NoSuchKey error
        error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Not Found'}}
        # Need to construct ClientError correctly or mock the exception class on the client
        # easiest way is to mock the exception class on the instance
        provider._client.exceptions.NoSuchKey = ClientError
        
        provider._client.get_object.side_effect = ClientError(error_response, "GetObject")
        
        with pytest.raises(ValueError, match="No data found"):
            provider.load(["UNKNOWN"])

    def test_load_empty_response(self, provider):
        """Should handle empty response body."""
        provider._client.get_object.return_value = {
            "Body": MagicMock(read=lambda: b"")
        }
        
        with pytest.raises(ValueError, match="No data found"):
            provider.load(["EMPTY"])

    def test_load_error(self, provider):
        """Should handle generic errors."""
        provider._client.get_object.side_effect = Exception("Generic error")
        
        with pytest.raises(ValueError, match="No data found"):
            provider.load(["ERROR"])

    def test_date_filter(self, provider):
        """Should filter loaded data by date."""
        df = pl.DataFrame({
            "timestamp": [
                datetime(2024, 1, 1),
                datetime(2024, 1, 2),
                datetime(2024, 1, 3)
            ],
            "close": [100, 101, 102]
        })
        buffer = io.BytesIO()
        df.write_parquet(buffer)
        
        provider._client.get_object.return_value = {
            "Body": MagicMock(read=lambda: buffer.getvalue())
        }
        
        # Filter range
        result = provider.load(["AAPL"], start_date="2024-01-02", end_date="2024-01-02")
        assert len(result) == 1
        assert result["timestamp"][0] == datetime(2024, 1, 2)

    def test_get_date_range(self, provider):
        """Should get date range."""
        df = pl.DataFrame({
            "timestamp": [
                datetime(2024, 1, 1),
                datetime(2024, 1, 10)
            ],
            "symbol": ["AAPL", "AAPL"]
        })
        buffer = io.BytesIO()
        df.write_parquet(buffer)
        
        provider._client.get_object.return_value = {
            "Body": MagicMock(read=lambda: buffer.getvalue())
        }
        
        start, end = provider.get_date_range("AAPL")
        assert start == "2024-01-01"
        assert end == "2024-01-10"

    def test_get_date_range_error(self, provider):
        """Should return N/A on error."""
        provider._client.get_object.side_effect = Exception("Fail")
        start, end = provider.get_date_range("ERROR")
        assert start == "N/A"
        assert end == "N/A"

    def test_health_check(self, provider):
        """Should check bucket existence."""
        assert provider.health_check() is True
        
        provider._client.head_bucket.side_effect = Exception("Down")
        assert provider.health_check() is False
