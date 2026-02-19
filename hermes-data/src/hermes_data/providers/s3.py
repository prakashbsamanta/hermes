import io
import logging
from typing import List, Optional, Tuple

import boto3  # type: ignore
import polars as pl
from botocore.config import Config  # type: ignore

from .base import DataProvider

logger = logging.getLogger(__name__)


class S3Provider(DataProvider):
    """Data provider for S3-compatible storage (Cloudflare R2, Oracle Object Storage)."""

    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        region_name: str = "auto",
        prefix: str = "minute",
    ):
        """Initialize S3 provider.
        
        Args:
            endpoint_url: S3-compatible endpoint URL
            access_key_id: Access Key ID
            secret_access_key: Secret Access Key
            bucket_name: Bucket name
            region_name: Region name (default: "auto")
            prefix: Object prefix (default: "minute")
        """
        self.bucket_name = bucket_name
        self.prefix = prefix

        # Configure boto3
        # Oracle strict S3 compatibility config
        boto_config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            s3={"payload_signing_enabled": True},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        )

        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name,
            config=boto_config,
        )
        
        # Verify connection
        try:
            self._client.head_bucket(Bucket=bucket_name)
            logger.info(f"Connected to S3 bucket: {bucket_name}")
        except Exception as e:
            logger.warning(f"Failed to connect to buckets {bucket_name}: {e}")

    def list_symbols(self) -> List[str]:
        """List available symbols in the bucket."""
        symbols = []
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            prefix_arg = f"{self.prefix}/" if self.prefix else ""
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix_arg):
                if "Contents" not in page:
                    continue
                    
                for obj in page["Contents"]:
                    key = obj["Key"]
                    if key.endswith(".parquet"):
                        # Extract symbol: "minute/AAPL.parquet" -> "AAPL"
                        symbol = key.split("/")[-1].replace(".parquet", "")
                        symbols.append(symbol)
            return sorted(symbols)
        except Exception as e:
            logger.error(f"Failed to list symbols from S3: {e}")
            return []

    def load(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pl.DataFrame:
        """Load data for multiple symbols."""
        dfs = []
        
        for symbol in symbols:
            try:
                if self.prefix:
                    key = f"{self.prefix}/{symbol}.parquet"
                else:
                    key = f"{symbol}.parquet"
                response = self._client.get_object(Bucket=self.bucket_name, Key=key)
                data = response["Body"].read()
                
                # Check for empty body
                if not data:
                    logger.warning(f"Empty object for {symbol}")
                    continue
                    
                df = pl.read_parquet(io.BytesIO(data))
                
                # Filter by date if needed
                if start_date or end_date:
                    df = self._filter_date(df, start_date, end_date)
                
                # Add symbol column if missing
                if "symbol" not in df.columns:
                    df = df.with_columns(pl.lit(symbol).alias("symbol"))
                
                dfs.append(df)
            except self._client.exceptions.NoSuchKey:
                logger.warning(f"Symbol not found in S3: {symbol}")
            except Exception as e:
                logger.error(f"Error loading {symbol} from S3: {e}")
        
        if not dfs:
            raise ValueError(f"No data found for symbols: {symbols}")
            
        return pl.concat(dfs) if len(dfs) > 1 else dfs[0]

    def _filter_date(
        self, df: pl.DataFrame, start_date: Optional[str], end_date: Optional[str]
    ) -> pl.DataFrame:
        """Filter DataFrame by date range."""
        # Assume 'timestamp' column exists
        if "timestamp" not in df.columns:
            return df
            
        if start_date:
            df = df.filter(pl.col("timestamp").dt.replace_time_zone(None) >= pl.lit(start_date).str.to_datetime())
        if end_date:
            df = df.filter(pl.col("timestamp").dt.replace_time_zone(None) <= pl.lit(end_date).str.to_datetime())
            
        return df

    def get_date_range(self, symbol: str) -> Tuple[str, str]:
        """Get date range for a symbol (downloads header only if possible, else full file)."""
        # S3 doesn't support reading just footer for Parquet easily without range requests
        # For simplicity, we read the whole file or just rely on metadata if we had it.
        # Here we just load the file efficiently.
        try:
            # Range request for footer? Parquet footer is at end.
            # For now, just load it. Parquet read is fast.
            df = self.load([symbol])
            if "timestamp" not in df.columns:
                return ("N/A", "N/A")
            
            min_date = df["timestamp"].min()
            max_date = df["timestamp"].max()
            
            min_str = "N/A"
            if hasattr(min_date, "strftime"):
                min_str = min_date.strftime("%Y-%m-%d")  # type: ignore

            max_str = "N/A"
            if hasattr(max_date, "strftime"):
                max_str = max_date.strftime("%Y-%m-%d")  # type: ignore

            return (min_str, max_str)
        except Exception:
            return ("N/A", "N/A")

    def health_check(self) -> bool:
        """Check if S3 connection is healthy."""
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False
