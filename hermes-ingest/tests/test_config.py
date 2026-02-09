"""Tests for IngestSettings configuration."""

import os
from pathlib import Path
from unittest.mock import patch

from hermes_ingest.config import IngestSettings


class TestIngestSettings:
    """Test suite for IngestSettings."""

    def test_default_values(self):
        """Test default configuration values."""
        settings = IngestSettings()

        assert settings.sink_type == "local"
        assert settings.rate_limit_per_sec == 2.5
        assert settings.max_concurrency == 5
        assert settings.chunk_days == 60

    def test_env_prefix(self):
        """Test that environment variables use HERMES_ prefix."""
        with patch.dict(os.environ, {"HERMES_SINK_TYPE": "s3"}):
            settings = IngestSettings()
            assert settings.sink_type == "s3"

    def test_get_sink_path_absolute(self):
        """Test get_sink_path with absolute path."""
        settings = IngestSettings(sink_path="/absolute/path")

        result = settings.get_sink_path()

        assert result == Path("/absolute/path")

    def test_get_sink_path_relative(self):
        """Test get_sink_path with relative path."""
        settings = IngestSettings(sink_path="data/minute")

        result = settings.get_sink_path()

        assert result.is_absolute()
        assert str(result).endswith("data/minute")

    def test_get_sink_path_with_base(self):
        """Test get_sink_path with custom base path."""
        settings = IngestSettings(sink_path="data/minute")
        base = Path("/custom/base")

        result = settings.get_sink_path(base)

        assert result == Path("/custom/base/data/minute")

    def test_zerodha_settings_optional(self):
        """Test that Zerodha settings are optional."""
        settings = IngestSettings(_env_file=None)

        assert settings.zerodha_enctoken is None
        assert settings.zerodha_user_id is None

    def test_zerodha_settings_from_env(self):
        """Test Zerodha settings from environment."""
        with patch.dict(
            os.environ,
            {
                "HERMES_ZERODHA_ENCTOKEN": "test_token",
                "HERMES_ZERODHA_USER_ID": "test_user",
            },
        ):
            settings = IngestSettings()
            assert settings.zerodha_enctoken == "test_token"
            assert settings.zerodha_user_id == "test_user"

    def test_get_instrument_file_absolute(self):
        """Test get_instrument_file with absolute path."""
        settings = IngestSettings(instrument_file="/absolute/instruments.csv")

        result = settings.get_instrument_file()

        assert result == Path("/absolute/instruments.csv")

    def test_get_instrument_file_relative(self):
        """Test get_instrument_file with relative path."""
        settings = IngestSettings(instrument_file="data/instruments.csv")

        result = settings.get_instrument_file()

        assert result.is_absolute()
        assert str(result).endswith("data/instruments.csv")
