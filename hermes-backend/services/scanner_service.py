"""Scanner service for batch strategy execution across multiple symbols.

Implements Check-Store-Serve logic with Postgres-backed caching:
1. CHECK: Query scan_results for fresh cached results
2. STORE: Batch insert new results after computation
3. SERVE: Merge cached + fresh, sorted by Total Return
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from api.models import (
    BacktestRequest,
    ScanRequest,
    ScanResponse,
    ScanResult,
)
from services.backtest_service import BacktestService
from services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

# Default cache TTL in hours
SCAN_CACHE_TTL_HOURS = 24


def _compute_params_hash(
    params: Dict,
    mode: str,
    start_date: Optional[str],
    end_date: Optional[str],
) -> str:
    """Compute a deterministic hash for scan parameters."""
    payload = json.dumps(
        {
            "params": params,
            "mode": mode,
            "start_date": start_date,
            "end_date": end_date,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class ScannerService:
    """Batch scanner with Postgres-backed result caching."""

    def __init__(
        self,
        backtest_service: BacktestService,
        market_data_service: Optional[MarketDataService] = None,
        db=None,
    ):
        self.backtest_service = backtest_service
        self.market_data_service = (
            market_data_service or backtest_service.market_data_service
        )
        self._db = db  # Optional Database instance for caching

    async def scan(self, request: ScanRequest) -> ScanResponse:
        """Run strategy across multiple symbols concurrently."""
        start_time = time.time()

        # 1. Validate strategy exists
        avail_strategies = self.backtest_service.get_strategies()
        if request.strategy not in avail_strategies:
            raise ValueError(
                f"Strategy '{request.strategy}' not found. "
                f"Available: {list(avail_strategies.keys())}"
            )

        # 2. Resolve symbol list
        if request.symbols:
            symbols = list(set(s.upper() for s in request.symbols))
        else:
            symbols = self.market_data_service.list_instruments()

        if not symbols:
            return ScanResponse(
                strategy=request.strategy,
                total_symbols=0,
                completed=0,
                failed=0,
                cached_count=0,
                fresh_count=0,
                results=[],
                elapsed_ms=0,
            )

        # 3. Compute params hash for cache lookups
        params_hash = _compute_params_hash(
            request.params, request.mode, request.start_date, request.end_date
        )

        # 4. CHECK: Try to load cached results from Postgres
        cached_results: Dict[str, ScanResult] = {}
        symbols_to_compute: List[str] = list(symbols)

        if self._db is not None:
            cached_results = self._get_cached_results(
                symbols, request.strategy, params_hash
            )
            symbols_to_compute = [s for s in symbols if s not in cached_results]
            logger.info(
                f"Cache hit for {len(cached_results)}/{len(symbols)} symbols"
            )

        # 5. RUN: Backtest missing/stale symbols concurrently
        fresh_results: List[ScanResult] = []
        if symbols_to_compute:
            sem = asyncio.Semaphore(request.max_concurrency)
            tasks = [
                self._backtest_symbol(sym, request, sem)
                for sym in symbols_to_compute
            ]
            fresh_results = await asyncio.gather(*tasks)

            # 6. STORE: Cache fresh results in Postgres
            if self._db is not None:
                successful = [r for r in fresh_results if r.status == "success"]
                if successful:
                    self._store_results(
                        successful, request.strategy, params_hash, request.mode
                    )

        # 7. SERVE: Merge cached + fresh, sort by Total Return desc
        all_results: List[ScanResult] = []
        all_results.extend(cached_results.values())
        all_results.extend(fresh_results)

        # Sort by Total Return (descending)
        all_results.sort(
            key=lambda r: self._extract_return(r.metrics),
            reverse=True,
        )

        completed = sum(1 for r in all_results if r.status != "error")
        failed = sum(1 for r in all_results if r.status == "error")
        elapsed_ms = int((time.time() - start_time) * 1000)

        return ScanResponse(
            strategy=request.strategy,
            total_symbols=len(symbols),
            completed=completed,
            failed=failed,
            cached_count=len(cached_results),
            fresh_count=len(fresh_results),
            results=all_results,
            elapsed_ms=elapsed_ms,
        )

    async def _backtest_symbol(
        self,
        symbol: str,
        request: ScanRequest,
        sem: asyncio.Semaphore,
    ) -> ScanResult:
        """Backtest one symbol. Never raises — catches all exceptions."""
        async with sem:
            try:
                backtest_req = BacktestRequest(
                    symbol=symbol,
                    strategy=request.strategy,
                    params=request.params,
                    initial_cash=request.initial_cash,
                    mode=request.mode,
                    start_date=request.start_date,
                    end_date=request.end_date,
                )

                # Run in executor to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.backtest_service.run_backtest,
                    backtest_req,
                )

                # Extract last signal
                last_signal = None
                last_signal_time = None
                signal_count = len(result.signals)
                if result.signals:
                    last = result.signals[-1]
                    last_signal = last.type
                    last_signal_time = last.time

                return ScanResult(
                    symbol=symbol,
                    metrics=result.metrics,
                    signal_count=signal_count,
                    last_signal=last_signal,
                    last_signal_time=last_signal_time,
                    status="success",
                    cached=False,
                )

            except Exception as e:
                logger.warning(f"Scan failed for {symbol}: {e}")
                return ScanResult(
                    symbol=symbol,
                    status="error",
                    error=str(e),
                    cached=False,
                )

    def _get_cached_results(
        self,
        symbols: List[str],
        strategy: str,
        params_hash: str,
    ) -> Dict[str, ScanResult]:
        """Check Postgres for non-expired cached results."""
        try:
            from hermes_data.registry.models import ScanResultCache

            cached: Dict[str, ScanResult] = {}
            now = datetime.utcnow()

            with self._db.session() as session:
                rows = (
                    session.query(ScanResultCache)
                    .filter(
                        ScanResultCache.symbol.in_(symbols),
                        ScanResultCache.strategy == strategy,
                        ScanResultCache.params_hash == params_hash,
                        ScanResultCache.expires_at > now,
                        ScanResultCache.status == "success",
                    )
                    .all()
                )

                for row in rows:
                    cached[row.symbol] = ScanResult(
                        symbol=row.symbol,
                        metrics=row.metrics or {},
                        signal_count=row.signal_count or 0,
                        last_signal=row.last_signal,
                        last_signal_time=row.last_signal_time,
                        status="cached",
                        cached=True,
                    )

            return cached

        except Exception as e:
            logger.warning(f"Cache read failed, computing all: {e}")
            return {}

    def _store_results(
        self,
        results: List[ScanResult],
        strategy: str,
        params_hash: str,
        mode: str,
    ) -> None:
        """Batch upsert scan results into Postgres."""
        try:
            from hermes_data.registry.models import ScanResultCache

            now = datetime.utcnow()
            expires = now + timedelta(hours=SCAN_CACHE_TTL_HOURS)

            with self._db.session() as session:
                for result in results:
                    # Check if row exists
                    existing = (
                        session.query(ScanResultCache)
                        .filter(
                            ScanResultCache.symbol == result.symbol,
                            ScanResultCache.strategy == strategy,
                            ScanResultCache.params_hash == params_hash,
                        )
                        .first()
                    )

                    if existing:
                        existing.metrics = result.metrics
                        existing.signal_count = result.signal_count
                        existing.last_signal = result.last_signal
                        existing.last_signal_time = result.last_signal_time
                        existing.created_at = now
                        existing.expires_at = expires
                        existing.status = "success"
                        existing.error_message = None
                    else:
                        cache_entry = ScanResultCache(
                            symbol=result.symbol,
                            strategy=strategy,
                            params_hash=params_hash,
                            mode=mode,
                            metrics=result.metrics,
                            signal_count=result.signal_count,
                            last_signal=result.last_signal,
                            last_signal_time=result.last_signal_time,
                            created_at=now,
                            expires_at=expires,
                            status="success",
                        )
                        session.add(cache_entry)

        except Exception as e:
            logger.warning(f"Cache store failed: {e}")

    @staticmethod
    def _extract_return(metrics: Dict) -> float:
        """Extract numeric return value from metrics dict for sorting."""
        val = metrics.get("Total Return", "0%")
        if isinstance(val, str):
            val = val.replace("%", "").replace(",", "").strip()
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0
