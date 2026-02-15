"""CLI entry point for hermes-ingest."""

import asyncio
import logging
import sys

import click
from rich.console import Console
from rich.table import Table

from hermes_ingest.config import get_settings
from hermes_ingest.orchestrator import IngestOrchestrator
from hermes_ingest.progress import ProgressTracker

# Configure logging - suppress when using rich progress
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

console = Console()


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
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Disable progress bars",
)
def fetch(symbol: str, source: str, quiet: bool) -> None:
    """Fetch data for a single symbol."""
    settings = get_settings()

    if not settings.zerodha_enctoken:
        click.echo("Error: HERMES_ZERODHA_ENCTOKEN not set", err=True)
        sys.exit(1)

    async def _fetch() -> bool:
        # Create progress tracker
        progress = ProgressTracker(show_progress=not quiet)

        async with IngestOrchestrator(settings=settings, progress=progress) as orchestrator:
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

            if not quiet:
                console.print(f"[bold blue]Fetching {symbol}[/] (token: {token})...")
                progress.start(1)

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
        console.print(f"[bold green]✓ Successfully fetched {symbol}[/]")
    else:
        console.print(f"[bold red]✗ Failed to fetch {symbol}[/]")
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
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Disable progress bars (logging only)",
)
def sync(source: str, limit: int | None, concurrency: int, quiet: bool) -> None:
    """Sync all instruments from a source."""
    settings = get_settings()

    if not settings.zerodha_enctoken:
        click.echo("Error: HERMES_ZERODHA_ENCTOKEN not set", err=True)
        sys.exit(1)

    # Adjust logging for progress mode
    if not quiet:
        # Suppress verbose logging when using rich progress
        logging.getLogger("hermes_ingest").setLevel(logging.WARNING)

    async def _sync() -> dict[str, bool]:
        # Create progress tracker
        progress = ProgressTracker(show_progress=not quiet)

        async with IngestOrchestrator(settings=settings, progress=progress) as orchestrator:
            if not quiet:
                console.print(f"[bold blue]Starting sync from {source}...[/]")
                if limit:
                    console.print(f"  Limit: {limit} symbols")
                console.print(f"  Concurrency: {concurrency}")

            return await orchestrator.sync(limit=limit, concurrency=concurrency)

    # Run async sync
    results = asyncio.run(_sync())

    # Summary table
    success = sum(1 for v in results.values() if v)
    failed = len(results) - success

    if not quiet:
        console.print()  # Blank line after progress

        # Create summary table
        table = Table(title="Sync Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Symbols", str(len(results)))
        table.add_row("Succeeded", f"[green]{success}[/]")
        table.add_row("Failed", f"[red]{failed}[/]" if failed > 0 else "0")

        console.print(table)
    else:
        click.echo(f"\n✓ Completed: {success} succeeded, {failed} failed")

    if failed > 0:
        sys.exit(1)


@main.command()
def list_symbols() -> None:
    """List all available symbols in the configured sink."""
    settings = get_settings()

    from hermes_ingest.sinks.factory import create_sink

    try:
        sink = create_sink(settings)
    except Exception as e:
        click.echo(f"Error creating sink: {e}", err=True)
        sys.exit(1)

    console.print(f"[dim]Sink: {type(sink).__name__} ({settings.sink_type})[/]")
    symbols = sink.list_symbols()

    if symbols:
        console.print(f"[bold]Found {len(symbols)} symbols:[/]")
        for sym in symbols:
            console.print(f"  • {sym}")
    else:
        console.print("[yellow]No symbols found in sink[/]")


@main.command()
def config() -> None:
    """Show current configuration."""
    settings = get_settings()

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Sink type", f"[bold]{settings.sink_type}[/]")

    if settings.sink_type == "local":
        table.add_row("Sink path", str(settings.get_sink_path()))
    elif settings.sink_type == "cloudflare_r2":
        table.add_row("R2 Account ID", settings.r2_account_id or "[red]not set[/]")
        r2_key = (
            f"{settings.r2_access_key_id[:8]}..."
            if settings.r2_access_key_id
            else "[red]not set[/]"
        )
        table.add_row("R2 Access Key", r2_key)
        table.add_row("R2 Bucket", settings.r2_bucket_name)
        table.add_row("R2 Prefix", settings.r2_prefix)
    elif settings.sink_type == "oracle_object_storage":
        table.add_row("OCI Namespace", settings.oci_namespace or "[red]not set[/]")
        table.add_row("OCI Region", settings.oci_region or "[red]not set[/]")
        oci_key = (
            f"{settings.oci_access_key_id[:8]}..."
            if settings.oci_access_key_id
            else "[red]not set[/]"
        )
        table.add_row("OCI Access Key", oci_key)
        table.add_row("OCI Bucket", settings.oci_bucket_name)
        table.add_row("OCI Prefix", settings.oci_prefix)

    table.add_row("Instrument file", str(settings.get_instrument_file()))
    table.add_row("Rate limit", f"{settings.rate_limit_per_sec}/sec")
    table.add_row("Concurrency", str(settings.max_concurrency))
    table.add_row("Chunk days", str(settings.chunk_days))
    table.add_row("Start date", settings.start_date)
    table.add_row(
        "Zerodha token",
        "[green]set[/]" if settings.zerodha_enctoken else "[red]not set[/]",
    )

    console.print(table)


if __name__ == "__main__":
    main()
