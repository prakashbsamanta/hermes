"""Configuration management for the data layer."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class DataSettings(BaseSettings):
    """Data layer configuration - all settings via environment variables."""

    # Storage Provider: "local" | "s3" | "gcs" (future)
    storage_provider: str = "local"

    # Local file system settings
    data_dir: str = "data/minute"  # Shared data directory (relative to project root or absolute)

    # Cache settings
    cache_enabled: bool = True
    cache_max_size_mb: int = 512  # Memory cache limit in MB

    # PostgreSQL Database settings
    database_url: str = "postgresql://hermes:hermes_secret@localhost:5432/hermes"
    
    # Registry settings
    registry_enabled: bool = True

    model_config = {
        "env_prefix": "HERMES_",
        "env_file": str(Path(__file__).parents[3] / ".env"),
        "extra": "ignore",
    }

    def get_data_path(self, base_path: Optional[Path] = None) -> Path:
        """Resolve data directory to absolute path.
        
        Args:
            base_path: Optional base path to resolve relative paths against.
                       If not provided, uses the hermes project root.
        """
        path = Path(self.data_dir)
        if path.is_absolute():
            return path

        # Resolve relative to provided base or project root
        if base_path:
            return base_path / path
        
        # Default: hermes project root (4 levels up from this file)
        # hermes/hermes-data/src/hermes_data/config.py -> hermes/
        project_root = Path(__file__).parents[3]
        return project_root / path


@lru_cache
def get_settings() -> DataSettings:
    """Get cached settings instance."""
    return DataSettings()
