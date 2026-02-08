"""Tests for ZerodhaSource."""

from unittest.mock import AsyncMock, patch

import polars as pl
import pytest

from hermes_ingest.sources.zerodha import RateLimiter, ZerodhaSource


class TestRateLimiter:
    """Test suite for RateLimiter."""

    @pytest.mark.asyncio
    async def test_wait_allows_first_request(self):
        """Test that first request is allowed immediately."""
        limiter = RateLimiter(rate_limit_per_sec=10.0)

        # Should not raise
        await limiter.wait()

    @pytest.mark.asyncio
    async def test_wait_limits_requests(self):
        """Test that rate limiting kicks in after tokens exhausted."""
        limiter = RateLimiter(rate_limit_per_sec=2.0)

        # Consume two tokens quickly
        await limiter.wait()
        await limiter.wait()

        # Third should wait (but we don't want to actually wait in tests)
        # Just verify the tokens are depleted
        assert limiter.tokens < 1


class TestZerodhaSource:
    """Test suite for ZerodhaSource."""

    def test_init_requires_enctoken(self):
        """Test that init fails without enctoken."""
        with patch("hermes_ingest.sources.zerodha.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = None

            with pytest.raises(ValueError, match="enctoken required"):
                ZerodhaSource()

    def test_init_with_enctoken(self):
        """Test init with enctoken."""
        source = ZerodhaSource(enctoken="test_token")

        assert source.enctoken == "test_token"

    def test_headers_include_token(self):
        """Test that headers include authorization token."""
        source = ZerodhaSource(enctoken="test_token")

        headers = source.headers

        assert "Authorization" in headers
        assert "test_token" in headers["Authorization"]

    def test_list_instruments_requires_file(self, temp_data_dir):
        """Test list_instruments fails when file missing."""
        with patch("hermes_ingest.sources.zerodha.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = "test"
            mock_settings.return_value.get_instrument_file.return_value = (
                temp_data_dir / "missing.csv"
            )

            source = ZerodhaSource(enctoken="test")

            with pytest.raises(FileNotFoundError):
                source.list_instruments()

    def test_list_instruments_loads_file(self, temp_data_dir, sample_instruments_df):
        """Test list_instruments loads CSV file."""
        # Create test file
        csv_path = temp_data_dir / "instruments.csv"
        sample_instruments_df.write_csv(csv_path)

        with patch("hermes_ingest.sources.zerodha.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = "test"
            mock_settings.return_value.get_instrument_file.return_value = csv_path

            source = ZerodhaSource(enctoken="test")
            df = source.list_instruments()

            assert len(df) == 3
            assert "tradingsymbol" in df.columns

    def test_list_instruments_filters_equity(self, temp_data_dir):
        """Test list_instruments filters to EQ instruments only."""
        # Create test file with mixed types
        df = pl.DataFrame({
            "instrument_token": [1, 2, 3],
            "tradingsymbol": ["RELIANCE", "NIFTY24JANFUT", "TCS"],
            "instrument_type": ["EQ", "FUT", "EQ"],
        })
        csv_path = temp_data_dir / "instruments.csv"
        df.write_csv(csv_path)

        with patch("hermes_ingest.sources.zerodha.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = "test"
            mock_settings.return_value.get_instrument_file.return_value = csv_path

            source = ZerodhaSource(enctoken="test")
            result = source.list_instruments()

            assert len(result) == 2
            symbols = result["tradingsymbol"].to_list()
            assert "RELIANCE" in symbols
            assert "TCS" in symbols
            assert "NIFTY24JANFUT" not in symbols

    @pytest.mark.asyncio
    async def test_close_closes_session(self):
        """Test close method closes aiohttp session."""
        source = ZerodhaSource(enctoken="test")

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.closed = False
        source._session = mock_session

        await source.close()

        mock_session.close.assert_called_once()
