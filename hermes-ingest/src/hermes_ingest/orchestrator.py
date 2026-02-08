"""Orchestrator for running data ingestion jobs."""

import asyncio
import logging
from datetime import datetime
from typing import Any

import polars as pl

from hermes_ingest.config import IngestSettings, get_settings
from hermes_ingest.sinks.base import DataSink
from hermes_ingest.sinks.local import LocalFileSink
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
    ):
        """Initialize the orchestrator.

        Args:
            source: Data source (defaults to ZerodhaSource)
            sink: Data sink (defaults to LocalFileSink)
            settings: Configuration settings
        """
        self._settings = settings or get_settings()
        self._source = source
        self._sink = sink

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
            sink_path = self._settings.get_sink_path()
            self._sink = LocalFileSink(sink_path)
        return self._sink

    async def fetch_symbol(self, symbol: str, token: int) -> bool:
        """Fetch data for a single symbol.

        Implements smart resume: only fetches data after the last stored timestamp.

        Args:
            symbol: Instrument symbol
            token: Instrument token

        Returns:
            True if successful, False otherwise
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = self._settings.start_date

        # Smart resume: check existing data
        if self.sink.exists(symbol):
            last_ts = (
                self.sink.get_last_timestamp(symbol)
                if hasattr(self.sink, "get_last_timestamp")
                else None
            )
            if last_ts:
                # Parse and add one minute
                last_dt = datetime.fromisoformat(last_ts)
                start_date = last_dt.strftime("%Y-%m-%d")
                logger.info(f"[{symbol}] Resuming from {start_date}")

        # Check if already up to date
        if start_date >= end_date:
            logger.info(f"[{symbol}] Already up to date")
            return True

        # Fetch data
        try:
            df = await self.source.fetch(symbol, token, start_date, end_date)
            if df is None or df.is_empty():
                logger.info(f"[{symbol}] No new data")
                return True

            # Write to sink
            self.sink.write(symbol, df)
            return True

        except Exception as e:
            logger.error(f"[{symbol}] Fetch failed: {e}")
            return False

    async def sync(
        self,
        symbols: list[str] | None = None,
        limit: int | None = None,
        concurrency: int = 5,
    ) -> dict[str, bool]:
        """Sync multiple symbols.

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

        logger.info(f"Starting sync for {len(instruments_df)} symbols (concurrency: {concurrency})")

        # Setup semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        results: dict[str, bool] = {}

        async def _process_one(row: dict[str, Any]) -> None:
            symbol = str(row["tradingsymbol"])
            token = int(row["instrument_token"])

            async with semaphore:
                result = await self.fetch_symbol(symbol, token)
                results[symbol] = result

        # Create tasks
        tasks = [
            _process_one(row) for row in instruments_df.iter_rows(named=True)
        ]

        # Run all tasks
        await asyncio.gather(*tasks)

        # Close source
        await self.source.close()

        # Summary
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Sync complete: {success_count}/{len(results)} succeeded")

        return results
