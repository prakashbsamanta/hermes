"""Factory function for creating data sinks based on configuration."""

from hermes_ingest.config import IngestSettings
from hermes_ingest.sinks.base import DataSink
from hermes_ingest.sinks.local import LocalFileSink


def create_sink(settings: IngestSettings | None = None) -> DataSink:
    """Create a data sink based on configuration.

    This factory function provides easy switching between local and cloud storage.
    The sink type is determined by the HERMES_SINK_TYPE environment variable
    or the sink_type field in IngestSettings.

    Args:
        settings: Optional IngestSettings instance. If not provided, will
                  load settings from environment variables.

    Returns:
        DataSink instance (LocalFileSink or CloudflareR2Sink)

    Raises:
        ValueError: If sink_type is unknown
        ImportError: If R2 sink is requested but boto3 is not installed
        ValueError: If R2 sink is requested but credentials are missing
    """
    if settings is None:
        from hermes_ingest.config import get_settings
        settings = get_settings()

    if settings.sink_type == "local":
        return LocalFileSink(settings.get_sink_path())

    elif settings.sink_type == "cloudflare_r2":
        # Validate required R2 settings
        if not all([
            settings.r2_account_id,
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
        ]):
            raise ValueError(
                "Cloudflare R2 sink requires HERMES_R2_ACCOUNT_ID, "
                "HERMES_R2_ACCESS_KEY_ID, and HERMES_R2_SECRET_ACCESS_KEY "
                "environment variables to be set."
            )

        # Import lazily to avoid requiring boto3 for local-only usage
        from hermes_ingest.sinks.cloudflare_r2 import CloudflareR2Sink

        # Type assertions (we validated above they are non-None)
        assert settings.r2_account_id is not None
        assert settings.r2_access_key_id is not None
        assert settings.r2_secret_access_key is not None

        return CloudflareR2Sink(
            account_id=settings.r2_account_id,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            bucket_name=settings.r2_bucket_name,
            prefix=settings.r2_prefix,
        )

    else:
        raise ValueError(
            f"Unknown sink type: {settings.sink_type}. "
            f"Valid options are: 'local', 'cloudflare_r2'"
        )
