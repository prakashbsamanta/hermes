"""Configuration management for the ingest layer."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class IngestSettings(BaseSettings):
    """Ingest layer configuration - all settings via environment variables."""

    # Zerodha credentials
    zerodha_enctoken: str | None = None
    zerodha_user_id: str | None = None

    # Sink configuration
    sink_type: str = "local"  # "local" | "cloudflare_r2"
    sink_path: str = "data/minute"  # For local sink (relative to project root or absolute)

    # Cloudflare R2 settings (optional - for cloud sink)
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str = "hermes-market-data"
    r2_prefix: str = "minute"  # Object prefix in bucket

    # Rate limiting
    rate_limit_per_sec: float = 2.5
    max_concurrency: int = 5

    # Chunk settings
    chunk_days: int = 60
    start_date: str = "2020-01-01"

    # Instrument file
    instrument_file: str = "data/instruments/NSE.csv"

    model_config = {
        "env_prefix": "HERMES_",
        "env_file": str(Path(__file__).parents[3] / ".env"),
        "extra": "ignore",
    }

    def get_sink_path(self, base_path: Path | None = None) -> Path:
        """Resolve sink directory to absolute path."""
        path = Path(self.sink_path)
        if path.is_absolute():
            return path

        if base_path:
            return base_path / path

        # Default: hermes project root (3 levels up from this file)
        project_root = Path(__file__).parents[3]
        return project_root / path

    def get_instrument_file(self, base_path: Path | None = None) -> Path:
        """Resolve instrument file to absolute path."""
        path = Path(self.instrument_file)
        if path.is_absolute():
            return path

        if base_path:
            return base_path / path

        project_root = Path(__file__).parents[3]
        return project_root / path


@lru_cache
def get_settings() -> IngestSettings:
    """Get cached settings instance."""
    return IngestSettings()
