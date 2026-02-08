"""Tests for IngestOrchestrator."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import polars as pl
import pytest

from hermes_ingest.orchestrator import IngestOrchestrator
from hermes_ingest.sinks.local import LocalFileSink


class TestIngestOrchestrator:
    """Test suite for IngestOrchestrator."""

    def test_init_with_defaults(self):
        """Test init with default settings."""
        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = "test"
            mock_settings.return_value.get_sink_path.return_value = Path("/tmp/test")
            mock_settings.return_value.rate_limit_per_sec = 2.5

            orch = IngestOrchestrator()

            assert orch._settings is not None

    def test_source_property_creates_zerodha(self):
        """Test source property creates ZerodhaSource."""
        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = "test"
            mock_settings.return_value.rate_limit_per_sec = 2.5

            orch = IngestOrchestrator()
            source = orch.source

            assert source is not None

    def test_sink_property_creates_local(self, temp_data_dir):
        """Test sink property creates LocalFileSink."""
        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = "test"
            mock_settings.return_value.get_sink_path.return_value = temp_data_dir

            orch = IngestOrchestrator()
            sink = orch.sink

            assert isinstance(sink, LocalFileSink)

    def test_can_inject_custom_source_and_sink(self, temp_data_dir):
        """Test that custom source and sink can be injected."""
        mock_source = MagicMock()
        mock_sink = MagicMock()

        orch = IngestOrchestrator(source=mock_source, sink=mock_sink)

        assert orch.source is mock_source
        assert orch.sink is mock_sink

    @pytest.mark.asyncio
    async def test_fetch_symbol_when_up_to_date(self, temp_data_dir, sample_ohlcv_df):
        """Test fetch_symbol returns True when already up to date."""
        mock_sink = MagicMock()
        mock_sink.exists.return_value = True
        mock_sink.get_last_timestamp.return_value = "2099-12-31T23:59:00"

        mock_source = AsyncMock()

        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.start_date = "2020-01-01"

            orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
            result = await orch.fetch_symbol("TEST", 12345)

            assert result is True
            # Source fetch should not be called if up to date
            mock_source.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_symbol_no_new_data(self, temp_data_dir):
        """Test fetch_symbol when source returns no data."""
        mock_sink = MagicMock()
        mock_sink.exists.return_value = False

        mock_source = AsyncMock()
        mock_source.fetch.return_value = None

        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.start_date = "2020-01-01"

            orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
            result = await orch.fetch_symbol("TEST", 12345)

            assert result is True
            mock_sink.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_symbol_success(self, temp_data_dir, sample_ohlcv_df):
        """Test fetch_symbol writes data on success."""
        mock_sink = MagicMock()
        mock_sink.exists.return_value = False

        mock_source = AsyncMock()
        mock_source.fetch.return_value = sample_ohlcv_df

        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.start_date = "2020-01-01"

            orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
            result = await orch.fetch_symbol("TEST", 12345)

            assert result is True
            mock_sink.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_symbol_handles_exception(self, temp_data_dir):
        """Test fetch_symbol handles exceptions gracefully."""
        mock_sink = MagicMock()
        mock_sink.exists.return_value = False

        mock_source = AsyncMock()
        mock_source.fetch.side_effect = Exception("Network error")

        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.start_date = "2020-01-01"

            orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
            result = await orch.fetch_symbol("TEST", 12345)

            assert result is False

    @pytest.mark.asyncio
    async def test_sync_empty_instruments(self):
        """Test sync with no instruments."""
        mock_source = MagicMock()
        mock_source.list_instruments.return_value = pl.DataFrame({
            "instrument_token": [],
            "tradingsymbol": [],
        })
        mock_source.close = AsyncMock()
        mock_source.fetch = AsyncMock(return_value=None)

        mock_sink = MagicMock()

        orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
        results = await orch.sync()

        assert results == {}

    @pytest.mark.asyncio
    async def test_sync_processes_instruments(self, sample_instruments_df):
        """Test sync processes all instruments."""
        mock_source = MagicMock()
        mock_source.list_instruments.return_value = sample_instruments_df
        mock_source.fetch = AsyncMock(return_value=None)  # No data
        mock_source.close = AsyncMock()

        mock_sink = MagicMock()
        mock_sink.exists.return_value = False

        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.start_date = "2020-01-01"

            orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
            results = await orch.sync()

            assert len(results) == 3
            assert "RELIANCE" in results
            assert "TCS" in results
            assert "INFY" in results

    @pytest.mark.asyncio
    async def test_sync_respects_limit(self, sample_instruments_df):
        """Test sync respects limit parameter."""
        mock_source = MagicMock()
        mock_source.list_instruments.return_value = sample_instruments_df
        mock_source.fetch = AsyncMock(return_value=None)
        mock_source.close = AsyncMock()

        mock_sink = MagicMock()
        mock_sink.exists.return_value = False

        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.start_date = "2020-01-01"

            orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
            results = await orch.sync(limit=1)

            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_sync_filters_by_symbol(self, sample_instruments_df):
        """Test sync filters by symbol list."""
        mock_source = MagicMock()
        mock_source.list_instruments.return_value = sample_instruments_df
        mock_source.fetch = AsyncMock(return_value=None)
        mock_source.close = AsyncMock()

        mock_sink = MagicMock()
        mock_sink.exists.return_value = False

        with patch("hermes_ingest.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.start_date = "2020-01-01"

            orch = IngestOrchestrator(source=mock_source, sink=mock_sink)
            results = await orch.sync(symbols=["RELIANCE", "TCS"])

            assert len(results) == 2
            assert "RELIANCE" in results
            assert "TCS" in results
            assert "INFY" not in results
