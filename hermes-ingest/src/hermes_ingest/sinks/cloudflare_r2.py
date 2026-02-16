"""Cloudflare R2 data sink for Parquet files (S3-compatible)."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

from hermes_ingest.sinks.base import Compression, DataSink

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)


class CloudflareR2Sink(DataSink):
    """Writes market data to Cloudflare R2 (S3-compatible storage).

    This sink implements the DataSink interface for cloud storage,
    providing the same functionality as LocalFileSink but stored in R2.

    Requires boto3 to be installed: pip install hermes-ingest[cloud]
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        prefix: str = "minute",
        compression: Compression = "zstd",
    ):
        """Initialize the Cloudflare R2 sink.

        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 API access key ID
            secret_access_key: R2 API secret access key
            bucket_name: R2 bucket name
            prefix: Object key prefix (e.g., "minute" for minute data)
            compression: Parquet compression codec (default: zstd)
        """
        super().__init__(compression=compression)

        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "boto3 is required for R2 sink. Install with: pip install hermes-ingest[cloud]"
            ) from None

        self.bucket_name = bucket_name
        self.prefix = prefix

        # Cloudflare R2 endpoint URL
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        # Configure boto3 with S3v4 signatures (required by R2)
        boto_config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
        )

        self._client: S3Client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",  # R2 uses 'auto' region
            config=boto_config,
        )

        logger.info(f"CloudflareR2Sink initialized: bucket={bucket_name}, prefix={prefix}")

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

        self._client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body,
            ContentType="application/octet-stream",
        )

        logger.info(f"[{symbol}] Wrote {len(df)} rows to r2://{self.bucket_name}/{key}")
        return Path(key)  # Return virtual path

    def read(self, symbol: str) -> pl.DataFrame | None:
        """Read existing data for a symbol from R2."""
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
            logger.warning(f"[{symbol}] Error reading from R2: {e}")
            return None

    def exists(self, symbol: str) -> bool:
        """Check if data exists for a symbol in R2."""
        key = self._get_key(symbol)

        try:
            self._client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    def list_symbols(self) -> list[str]:
        """List all available symbols in the R2 bucket."""
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
