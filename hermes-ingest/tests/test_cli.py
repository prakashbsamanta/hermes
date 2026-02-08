"""Tests for CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from hermes_ingest.cli import main


class TestCLI:
    """Test suite for CLI commands."""

    def test_config_command(self):
        """Test config command shows settings."""
        runner = CliRunner()

        result = runner.invoke(main, ["config"])

        assert result.exit_code == 0
        assert "Sink type:" in result.output
        assert "Sink path:" in result.output

    def test_list_symbols_empty(self, temp_data_dir):
        """Test list-symbols with empty directory."""
        runner = CliRunner()

        with patch("hermes_ingest.cli.get_settings") as mock_settings:
            mock_settings.return_value.get_sink_path.return_value = temp_data_dir

            result = runner.invoke(main, ["list-symbols"])

            assert result.exit_code == 0
            assert "No symbols found" in result.output

    def test_list_symbols_with_data(self, temp_data_dir, sample_ohlcv_df):
        """Test list-symbols with data files."""
        runner = CliRunner()

        # Create test files
        sample_ohlcv_df.write_parquet(temp_data_dir / "TEST1.parquet")
        sample_ohlcv_df.write_parquet(temp_data_dir / "TEST2.parquet")

        with patch("hermes_ingest.cli.get_settings") as mock_settings:
            mock_settings.return_value.get_sink_path.return_value = temp_data_dir

            result = runner.invoke(main, ["list-symbols"])

            assert result.exit_code == 0
            assert "TEST1" in result.output
            assert "TEST2" in result.output

    def test_fetch_without_token(self):
        """Test fetch fails without enctoken."""
        runner = CliRunner()

        with patch("hermes_ingest.cli.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = None

            result = runner.invoke(main, ["fetch", "--symbol", "RELIANCE"])

            assert result.exit_code == 1
            assert "HERMES_ZERODHA_ENCTOKEN not set" in result.output

    def test_sync_without_token(self):
        """Test sync fails without enctoken."""
        runner = CliRunner()

        with patch("hermes_ingest.cli.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = None

            result = runner.invoke(main, ["sync"])

            assert result.exit_code == 1
            assert "HERMES_ZERODHA_ENCTOKEN not set" in result.output

    def test_version_option(self):
        """Test --version option."""
        runner = CliRunner()

        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_help_option(self):
        """Test --help option."""
        runner = CliRunner()

        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Hermes data ingestion CLI" in result.output
        assert "fetch" in result.output
        assert "sync" in result.output

    def test_fetch_symbol_not_found(self, temp_data_dir, sample_instruments_df):
        """Test fetch with unknown symbol."""
        runner = CliRunner()

        # Create instrument file
        csv_path = temp_data_dir / "instruments.csv"
        sample_instruments_df.write_csv(csv_path)

        with patch("hermes_ingest.cli.get_settings") as mock_settings:
            mock_settings.return_value.zerodha_enctoken = "test_token"
            mock_settings.return_value.rate_limit_per_sec = 2.5
            mock_settings.return_value.get_instrument_file.return_value = csv_path

            result = runner.invoke(main, ["fetch", "--symbol", "UNKNOWN"])

            assert result.exit_code == 1
            assert "not found" in result.output

    def test_fetch_success(self, temp_data_dir, sample_instruments_df, sample_ohlcv_df):
        """Test fetch command success path."""
        runner = CliRunner()

        # Create instrument file
        csv_path = temp_data_dir / "instruments.csv"
        sample_instruments_df.write_csv(csv_path)

        with (
            patch("hermes_ingest.cli.get_settings") as mock_settings,
            patch("hermes_ingest.cli.IngestOrchestrator") as mock_orch_cls,
        ):
            mock_settings.return_value.zerodha_enctoken = "test_token"
            mock_settings.return_value.rate_limit_per_sec = 2.5
            mock_settings.return_value.get_instrument_file.return_value = csv_path

            mock_orch = MagicMock()
            mock_orch.source.list_instruments.return_value = sample_instruments_df
            mock_orch.fetch_symbol = AsyncMock(return_value=True)
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(main, ["fetch", "--symbol", "RELIANCE"])

            assert result.exit_code == 0
            assert "Successfully fetched" in result.output

    def test_fetch_failure(self, temp_data_dir, sample_instruments_df):
        """Test fetch command failure path."""
        runner = CliRunner()

        csv_path = temp_data_dir / "instruments.csv"
        sample_instruments_df.write_csv(csv_path)

        with (
            patch("hermes_ingest.cli.get_settings") as mock_settings,
            patch("hermes_ingest.cli.IngestOrchestrator") as mock_orch_cls,
        ):
            mock_settings.return_value.zerodha_enctoken = "test_token"
            mock_settings.return_value.rate_limit_per_sec = 2.5
            mock_settings.return_value.get_instrument_file.return_value = csv_path

            mock_orch = MagicMock()
            mock_orch.source.list_instruments.return_value = sample_instruments_df
            mock_orch.fetch_symbol = AsyncMock(return_value=False)
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(main, ["fetch", "--symbol", "RELIANCE"])

            assert result.exit_code == 1
            assert "Failed to fetch" in result.output

    def test_sync_success(self, temp_data_dir, sample_instruments_df):
        """Test sync command success path."""
        runner = CliRunner()

        with (
            patch("hermes_ingest.cli.get_settings") as mock_settings,
            patch("hermes_ingest.cli.IngestOrchestrator") as mock_orch_cls,
        ):
            mock_settings.return_value.zerodha_enctoken = "test_token"

            mock_orch = MagicMock()
            mock_orch.sync = AsyncMock(return_value={"RELIANCE": True, "TCS": True})
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(main, ["sync", "--limit", "2"])

            assert result.exit_code == 0
            assert "2 succeeded" in result.output
            assert "0 failed" in result.output

    def test_sync_with_failures(self, temp_data_dir):
        """Test sync command with some failures."""
        runner = CliRunner()

        with (
            patch("hermes_ingest.cli.get_settings") as mock_settings,
            patch("hermes_ingest.cli.IngestOrchestrator") as mock_orch_cls,
        ):
            mock_settings.return_value.zerodha_enctoken = "test_token"

            mock_orch = MagicMock()
            mock_orch.sync = AsyncMock(return_value={"RELIANCE": True, "TCS": False})
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(main, ["sync"])

            assert result.exit_code == 1  # Has failures
            assert "1 succeeded" in result.output
            assert "1 failed" in result.output
