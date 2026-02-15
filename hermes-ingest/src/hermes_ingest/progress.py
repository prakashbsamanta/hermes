"""Progress tracking for data ingestion with rich terminal UI."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.progress import Progress, TaskID

logger = logging.getLogger(__name__)


@dataclass
class SymbolProgress:
    """Progress tracking for a single symbol."""

    symbol: str
    total_chunks: int = 0
    completed_chunks: int = 0
    rows_written: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, fetching, complete, failed


class ProgressTracker:
    """Track and display ingestion progress using rich.

    Supports both TTY (rich progress bars) and headless (logging only) modes.
    """

    def __init__(self, show_progress: bool = True) -> None:
        """Initialize the progress tracker.

        Args:
            show_progress: If True, show rich progress bars. If False, log only.
        """
        self.show_progress = show_progress
        self._progress: Progress | None = None
        self._overall_task: TaskID | None = None
        self._symbol_tasks: dict[str, TaskID] = {}
        self._symbol_progress: dict[str, SymbolProgress] = {}
        self._total_symbols: int = 0
        self._completed_symbols: int = 0
        self._started: bool = False

    def start(self, total_symbols: int) -> None:
        """Start progress tracking.

        Args:
            total_symbols: Total number of symbols to process
        """
        self._total_symbols = total_symbols
        self._started = True

        if self.show_progress:
            from rich.progress import (
                BarColumn,
                MofNCompleteColumn,
                Progress,
                SpinnerColumn,
                TextColumn,
                TimeElapsedColumn,
                TimeRemainingColumn,
            )

            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn("•"),
                TextColumn("[cyan]Candles: {task.fields[candles]}[/cyan]"),
                TextColumn("•"),
                TimeRemainingColumn(),
                refresh_per_second=4,
            )
            self._progress.start()
            self._overall_task = self._progress.add_task(
                "[cyan]Overall Progress",
                total=total_symbols,
                candles=0,
            )
        else:
            logger.info(f"Starting sync for {total_symbols} symbols")

    def start_symbol(self, symbol: str, total_chunks: int) -> None:
        """Start tracking a symbol.

        Args:
            symbol: Symbol name
            total_chunks: Expected number of chunks for this symbol
        """
        self._symbol_progress[symbol] = SymbolProgress(
            symbol=symbol,
            total_chunks=total_chunks,
            status="fetching",
        )

        if self.show_progress and self._progress:
            task_id = self._progress.add_task(
                f"[yellow]{symbol}",
                total=total_chunks,
                candles=0,
            )
            self._symbol_tasks[symbol] = task_id

    def update_symbol(self, symbol: str, chunks_done: int = 1, rows_written: int = 0) -> None:
        """Update progress for a symbol.

        Args:
            symbol: Symbol name
            chunks_done: Number of chunks completed in this update
            rows_written: Number of rows written in this update
        """
        if symbol in self._symbol_progress:
            prog = self._symbol_progress[symbol]
            prog.completed_chunks += chunks_done
            prog.rows_written += rows_written

        if self.show_progress and self._progress and symbol in self._symbol_tasks:
            self._progress.update(
                self._symbol_tasks[symbol],
                advance=chunks_done,
                candles=self._symbol_progress[symbol].rows_written,
            )

    def complete_symbol(self, symbol: str, success: bool = True) -> None:
        """Mark a symbol as complete.

        Args:
            symbol: Symbol name
            success: Whether the symbol completed successfully
        """
        self._completed_symbols += 1

        if symbol in self._symbol_progress:
            prog = self._symbol_progress[symbol]
            prog.status = "complete" if success else "failed"

        if self.show_progress and self._progress:
            # Remove symbol task and update overall
            if symbol in self._symbol_tasks:
                self._progress.remove_task(self._symbol_tasks[symbol])
                del self._symbol_tasks[symbol]

            if self._overall_task is not None:
                self._progress.update(self._overall_task, advance=1)
        else:
            symbol_prog = self._symbol_progress.get(symbol)
            if symbol_prog:
                status = "✓" if success else "✗"
                logger.info(
                    f"{status} [{symbol}] {symbol_prog.completed_chunks} chunks, "
                    f"{symbol_prog.rows_written} rows"
                )

    def stop(self) -> dict[str, SymbolProgress]:
        """Stop progress tracking and return summary.

        Returns:
            Dict mapping symbol to its progress stats
        """
        if self.show_progress and self._progress:
            self._progress.stop()

        return self._symbol_progress

    def __enter__(self) -> ProgressTracker:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        if self._started:
            self.stop()
