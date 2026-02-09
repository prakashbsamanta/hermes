"""CLI entry point for hermes-ingest."""

import asyncio
import logging
import sys

import click

from hermes_ingest.config import get_settings
from hermes_ingest.orchestrator import IngestOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


@click.group()
@click.version_option()
def main() -> None:
    """Hermes data ingestion CLI.

    Fetch and sync market data from brokers to local storage or cloud.
    """
    pass


@main.command()
@click.option(
    "--symbol",
    "-s",
    required=True,
    help="Symbol to fetch (e.g., RELIANCE)",
)
@click.option(
    "--source",
    type=click.Choice(["zerodha"]),
    default="zerodha",
    help="Data source",
)
def fetch(symbol: str, source: str) -> None:
    """Fetch data for a single symbol."""
    settings = get_settings()

    if not settings.zerodha_enctoken:
        click.echo("Error: HERMES_ZERODHA_ENCTOKEN not set", err=True)
        sys.exit(1)

    async def _fetch() -> bool:
        async with IngestOrchestrator(settings=settings) as orchestrator:
            # Get token for symbol
            instruments_df = orchestrator.source.list_instruments()
            matching = instruments_df.filter(
                instruments_df["tradingsymbol"] == symbol.upper()
            )

            if matching.is_empty():
                click.echo(f"Error: Symbol '{symbol}' not found in instruments", err=True)
                sys.exit(1)

            row = matching.row(0, named=True)
            token = row["instrument_token"]

            click.echo(f"Fetching {symbol} (token: {token})...")

            return await orchestrator.fetch_symbol(symbol.upper(), token)

    # Run async fetch with cleanup
    try:
        success = asyncio.run(_fetch())
    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if success:
        click.echo(f"✓ Successfully fetched {symbol}")
    else:
        click.echo(f"✗ Failed to fetch {symbol}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--source",
    type=click.Choice(["zerodha"]),
    default="zerodha",
    help="Data source",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit number of symbols",
)
@click.option(
    "--concurrency",
    "-c",
    type=int,
    default=5,
    help="Number of parallel downloads",
)
def sync(source: str, limit: int | None, concurrency: int) -> None:
    """Sync all instruments from a source."""
    settings = get_settings()

    if not settings.zerodha_enctoken:
        click.echo("Error: HERMES_ZERODHA_ENCTOKEN not set", err=True)
        sys.exit(1)

    async def _sync() -> dict[str, bool]:
        async with IngestOrchestrator(settings=settings) as orchestrator:
            click.echo(f"Starting sync from {source}...")
            if limit:
                click.echo(f"  Limit: {limit} symbols")
            click.echo(f"  Concurrency: {concurrency}")

            return await orchestrator.sync(limit=limit, concurrency=concurrency)

    # Run async sync
    results = asyncio.run(_sync())

    # Summary
    success = sum(1 for v in results.values() if v)
    failed = len(results) - success

    click.echo(f"\n✓ Completed: {success} succeeded, {failed} failed")

    if failed > 0:
        sys.exit(1)


@main.command()
def list_symbols() -> None:
    """List all available symbols in the sink."""
    settings = get_settings()
    sink_path = settings.get_sink_path()

    from hermes_ingest.sinks.local import LocalFileSink

    sink = LocalFileSink(sink_path)
    symbols = sink.list_symbols()

    if symbols:
        click.echo(f"Found {len(symbols)} symbols:")
        for sym in symbols:
            click.echo(f"  {sym}")
    else:
        click.echo("No symbols found in sink")


@main.command()
def config() -> None:
    """Show current configuration."""
    settings = get_settings()

    click.echo("Current configuration:")
    click.echo(f"  Sink type: {settings.sink_type}")
    click.echo(f"  Sink path: {settings.get_sink_path()}")
    click.echo(f"  Instrument file: {settings.get_instrument_file()}")
    click.echo(f"  Rate limit: {settings.rate_limit_per_sec}/sec")
    click.echo(f"  Concurrency: {settings.max_concurrency}")
    click.echo(f"  Chunk days: {settings.chunk_days}")
    click.echo(f"  Start date: {settings.start_date}")
    click.echo(f"  Zerodha token: {'set' if settings.zerodha_enctoken else 'not set'}")


if __name__ == "__main__":
    main()
