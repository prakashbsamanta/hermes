"""Oracle Cloud Object Storage data sink for Parquet files (S3-compatible).

Uses Oracle's S3 Compatibility API with Customer Secret Keys for authentication.
Endpoint format: https://{namespace}.compat.objectstorage.{region}.oraclecloud.com
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

from hermes_ingest.sinks.base import DataSink

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)


class OracleObjectStorageSink(DataSink):
    """Writes market data to Oracle Cloud Object Storage (S3-compatible).

    This sink implements the DataSink interface for Oracle Cloud Infrastructure
    Object Storage, using the S3 Compatibility API. It provides the same
    functionality as LocalFileSink and CloudflareR2Sink but stored in OCI.

    Requires boto3 to be installed: pip install hermes-ingest[cloud]

    Authentication uses Customer Secret Keys, which provide:
    - Access Key ID
    - Secret Access Key

    The endpoint is constructed from:
    - Namespace: unique tenancy identifier (found in OCI Console)
    - Region: OCI region (e.g., 'ap-mumbai-1', 'us-ashburn-1')
    """

    def __init__(
        self,
        namespace: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        prefix: str = "minute",
        compression: str = "zstd",
    ):
        """Initialize the Oracle Object Storage sink.

        Args:
            namespace: OCI Object Storage namespace (unique tenancy identifier)
            region: OCI region (e.g., 'ap-mumbai-1', 'us-ashburn-1')
            access_key_id: Customer Secret Key Access Key ID
            secret_access_key: Customer Secret Key Secret Access Key
            bucket_name: OCI Object Storage bucket name
            prefix: Object key prefix (e.g., "minute" for minute data)
            compression: Parquet compression codec (default: zstd)
        """
        super().__init__(compression=compression)

        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "boto3 is required for Oracle Object Storage sink. "
                "Install with: pip install hermes-ingest[cloud]"
            ) from None

        self.bucket_name = bucket_name
        self.prefix = prefix

        # Oracle OCI S3-compatible endpoint URL
        endpoint_url = (
            f"https://{namespace}.compat.objectstorage.{region}.oraclecloud.com"
        )

        # Configure boto3 for OCI S3 compatibility
        # Oracle OCI requires Content-Length header and does NOT support
        # chunked transfer encoding, so we disable it explicitly.
        boto_config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            s3={"payload_signing_enabled": True},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        )

        self._client: S3Client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=boto_config,
        )

        logger.info(
            f"OracleObjectStorageSink initialized: "
            f"namespace={namespace}, region={region}, "
            f"bucket={bucket_name}, prefix={prefix}"
        )

    def _get_key(self, symbol: str) -> str:
        """Get the object key for a symbol."""
        return f"{self.prefix}/{symbol}.parquet"

    def write(self, symbol: str, df: pl.DataFrame) -> Path:
        """Write OHLCV data for a symbol.

        Appends to existing data if present, deduplicates, and sorts.
        """
        key = self._get_key(symbol)

        # Merge with existing data if present
        existing_df = self.read(symbol)
        df = self._merge_and_deduplicate(df, existing_df)

        # Serialize to compressed Parquet and upload
        body = self._to_parquet_bytes(df)

        # Oracle OCI S3-compatible API requires explicit Content-Length
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body,
            ContentLength=len(body),
            ContentType="application/octet-stream",
        )

        logger.info(f"[{symbol}] Wrote {len(df)} rows to oci://{self.bucket_name}/{key}")
        return Path(key)  # Return virtual path

    def read(self, symbol: str) -> pl.DataFrame | None:
        """Read existing data for a symbol from Oracle Object Storage."""
        key = self._get_key(symbol)

        try:
            response = self._client.get_object(Bucket=self.bucket_name, Key=key)
            data = response["Body"].read()
            return self._from_parquet_bytes(data)
        except self._client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            # Handle both NoSuchKey and general ClientError for missing objects
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
                return None
            logger.warning(f"[{symbol}] Error reading from Oracle Object Storage: {e}")
            return None

    def exists(self, symbol: str) -> bool:
        """Check if data exists for a symbol in Oracle Object Storage."""
        key = self._get_key(symbol)

        try:
            self._client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    def list_symbols(self) -> list[str]:
        """List all available symbols in the OCI bucket."""
        symbols = []

        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=f"{self.prefix}/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".parquet"):
                    # Extract symbol from key: "minute/RELIANCE.parquet" -> "RELIANCE"
                    symbol = key.rsplit("/", 1)[-1].replace(".parquet", "")
                    symbols.append(symbol)

        return sorted(symbols)
