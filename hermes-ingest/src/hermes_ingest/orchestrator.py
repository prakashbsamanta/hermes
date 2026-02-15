"""Orchestrator for running data ingestion jobs."""

import asyncio
import logging
from datetime import datetime
from typing import Any

import polars as pl

from hermes_ingest.config import IngestSettings, get_settings
from hermes_ingest.progress import ProgressTracker
from hermes_ingest.sinks.base import DataSink
from hermes_ingest.sources.base import DataSource
from hermes_ingest.sources.zerodha import ZerodhaSource

logger = logging.getLogger(__name__)


class IngestOrchestrator:
    """Orchestrator for running data ingestion jobs.

    Coordinates between sources and sinks, handles concurrency,
    and provides progress tracking.
    """

    def __init__(
        self,
        source: DataSource | None = None,
        sink: DataSink | None = None,
        settings: IngestSettings | None = None,
        progress: ProgressTracker | None = None,
    ):
        """Initialize the orchestrator.

        Args:
            source: Data source (defaults to ZerodhaSource)
            sink: Data sink (defaults to LocalFileSink)
            settings: Configuration settings
            progress: Optional progress tracker for UI updates
        """
        self._settings = settings or get_settings()
        self._source = source
        self._sink = sink
        self._progress = progress

    async def close(self) -> None:
        """Close resources (source connection)."""
        if self._source:
            await self._source.close()
            # Give underlying connectors time to close to avoid "Unclosed connector" errors
            await asyncio.sleep(0.250)

    async def __aenter__(self) -> "IngestOrchestrator":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    @property
    def source(self) -> DataSource:
        """Get or create the data source."""
        if self._source is None:
            self._source = ZerodhaSource(settings=self._settings)
        return self._source

    @property
    def sink(self) -> DataSink:
        """Get or create the data sink."""
        if self._sink is None:
            from hermes_ingest.sinks.factory import create_sink
            self._sink = create_sink(self._settings)
        return self._sink

    def _get_resume_date(self, symbol: str, default_start: str) -> str:
        """Get the date to resume fetching from.

        Implements smart resume: checks existing data and returns the next day
        after the last stored timestamp.

        Args:
            symbol: Instrument symbol
            default_start: Default start date if no existing data

        Returns:
            Start date for fetching (YYYY-MM-DD)
        """
        if not self.sink.exists(symbol):
            return default_start

        last_ts = (
            self.sink.get_last_timestamp(symbol)
            if hasattr(self.sink, "get_last_timestamp")
            else None
        )

        if not last_ts:
            return default_start

        # Parse and use the date of the last timestamp
        last_dt = datetime.fromisoformat(last_ts)
        resume_date = last_dt.strftime("%Y-%m-%d")
        logger.info(f"[{symbol}] Resuming from {resume_date}")
        return resume_date

    async def fetch_symbol(self, symbol: str, token: int) -> bool:
        """Fetch data for a single symbol with incremental writes.

        Implements:
        - Smart resume: only fetches data after the last stored timestamp
        - Incremental writes: writes each chunk immediately as it's fetched
        - Progress updates: updates progress tracker per chunk

        Args:
            symbol: Instrument symbol
            token: Instrument token

        Returns:
            True if successful, False otherwise
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = self._get_resume_date(symbol, self._settings.start_date)

        # Check if already up to date
        if start_date >= end_date:
            logger.info(f"[{symbol}] Already up to date")
            return True

        # Calculate chunks for progress tracking
        source = self.source
        if hasattr(source, "calculate_chunks"):
            total_chunks = source.calculate_chunks(start_date, end_date)
            if self._progress:
                self._progress.start_symbol(symbol, total_chunks)
        else:
            total_chunks = 0

        # Fetch and write incrementally
        try:
            chunks_written = 0
            total_rows = 0

            async for chunk_df, _from_date, _to_date in source.fetch_chunks(
                symbol, token, start_date, end_date
            ):
                if chunk_df is None or chunk_df.is_empty():
                    continue

                # Write immediately - sink handles append/dedupe
                self.sink.write(symbol, chunk_df)
                chunks_written += 1
                total_rows += len(chunk_df)

                # Update progress
                if self._progress:
                    self._progress.update_symbol(
                        symbol, chunks_done=1, rows_written=len(chunk_df)
                    )

            if chunks_written == 0:
                logger.info(f"[{symbol}] No new data")
            else:
                logger.info(f"[{symbol}] Wrote {chunks_written} chunks, {total_rows} total rows")

            if self._progress:
                self._progress.complete_symbol(symbol, success=True)
            return True

        except Exception as e:
            logger.error(f"[{symbol}] Fetch failed: {e}")
            if self._progress:
                self._progress.complete_symbol(symbol, success=False)
            return False

    async def sync(
        self,
        symbols: list[str] | None = None,
        limit: int | None = None,
        concurrency: int = 5,
    ) -> dict[str, bool]:
        """Sync multiple symbols with structured concurrency.

        Args:
            symbols: List of symbols to sync (or all from source)
            limit: Maximum number of symbols to process
            concurrency: Number of parallel downloads

        Returns:
            Dict mapping symbol to success status
        """
        # Get instruments
        instruments_df = self.source.list_instruments()

        # Filter by symbols if provided
        if symbols:
            instruments_df = instruments_df.filter(
                pl.col("tradingsymbol").is_in([s.upper() for s in symbols])
            )

        # Apply limit
        if limit:
            instruments_df = instruments_df.head(limit)

        if instruments_df.is_empty():
            logger.warning("No instruments to process")
            return {}

        total_symbols = len(instruments_df)
        logger.info(f"Starting sync for {total_symbols} symbols (concurrency: {concurrency})")

        # Start progress tracking
        if self._progress:
            self._progress.start(total_symbols)

        # Setup semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        results: dict[str, bool] = {}

        async def _process_one(row: dict[str, Any]) -> None:
            symbol = str(row["tradingsymbol"])
            token = int(row["instrument_token"])

            async with semaphore:
                result = await self.fetch_symbol(symbol, token)
                results[symbol] = result

        # Use TaskGroup for structured concurrency (Python 3.11+)
        async with asyncio.TaskGroup() as tg:
            for row in instruments_df.iter_rows(named=True):
                tg.create_task(_process_one(row))

        # Close source
        await self.source.close()

        # Summary
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Sync complete: {success_count}/{len(results)} succeeded")

        return results
