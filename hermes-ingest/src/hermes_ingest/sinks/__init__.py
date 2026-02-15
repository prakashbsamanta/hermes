"""Data sinks for hermes-ingest."""

from hermes_ingest.sinks.base import DataSink
from hermes_ingest.sinks.factory import create_sink
from hermes_ingest.sinks.local import LocalFileSink

__all__ = ["DataSink", "LocalFileSink", "create_sink"]


def __getattr__(name: str) -> type:
    """Lazy import for optional cloud sinks (require boto3)."""
    if name == "CloudflareR2Sink":
        from hermes_ingest.sinks.cloudflare_r2 import CloudflareR2Sink
        return CloudflareR2Sink
    if name == "OracleObjectStorageSink":
        from hermes_ingest.sinks.oracle_object_storage import OracleObjectStorageSink
        return OracleObjectStorageSink
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

