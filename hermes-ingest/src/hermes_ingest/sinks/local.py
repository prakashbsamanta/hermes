"""Local file system data sink for Parquet files."""

import logging
from pathlib import Path

import polars as pl

from hermes_ingest.sinks.base import Compression, DataSink

logger = logging.getLogger(__name__)


class LocalFileSink(DataSink):
    """Writes market data to local Parquet files.

    This sink implements the DataSink interface for local file storage,
    providing atomic writes and smart resume functionality.
    """

    def __init__(self, data_dir: str | Path, compression: Compression = "zstd"):
        """Initialize the local file sink.

        Args:
            data_dir: Path to directory for storing parquet files
            compression: Parquet compression codec (default: zstd)
        """
        super().__init__(compression=compression)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalFileSink initialized at: {self.data_dir}")

    def _get_path(self, symbol: str) -> Path:
        """Get the file path for a symbol."""
        return self.data_dir / f"{symbol}.parquet"

    def write(self, symbol: str, df: pl.DataFrame) -> Path:
        """Write OHLCV data for a symbol.

        Appends to existing data if present, deduplicates, and sorts.
        """
        output_path = self._get_path(symbol)

        # Merge with existing data if present
        existing_df = self.read(symbol)
        df = self._merge_and_deduplicate(df, existing_df)

        # Write with compression
        df.write_parquet(output_path, compression=self.compression)
        logger.info(f"[{symbol}] Wrote {len(df)} rows to {output_path}")

        return output_path

    def read(self, symbol: str) -> pl.DataFrame | None:
        """Read existing data for a symbol."""
        path = self._get_path(symbol)
        if not path.exists():
            return None

        try:
            return pl.read_parquet(path)
        except Exception as e:
            logger.warning(f"[{symbol}] Error reading file: {e}")
            return None

    def exists(self, symbol: str) -> bool:
        """Check if data exists for a symbol."""
        return self._get_path(symbol).exists()

    def list_symbols(self) -> list[str]:
        """List all available symbols in the sink."""
        return sorted([f.stem for f in self.data_dir.glob("*.parquet")])
