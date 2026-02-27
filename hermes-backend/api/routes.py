from fastapi import APIRouter, HTTPException
import logging
import os
import sys
import uuid
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import List, Dict, Any

# Add parent directory to path to allow imports if running from top level
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from services.market_data_service import MarketDataService  # noqa: E402
from services.backtest_service import BacktestService  # noqa: E402
from services.scanner_service import ScannerService  # noqa: E402
from .models import (  # noqa: E402
    BacktestRequest,
    BacktestResponse,
    BacktestTaskResponse,
    BacktestStatusResponse,
    ScanRequest,
    ScanResponse,
    StorageSettingsUpdate,
)
from hermes_data.config import get_settings  # noqa: E402

router = APIRouter()

# Lazy service initialization to allow mocking in tests
_market_data_service = None
_backtest_service = None
_scanner_service = None

# Async task store (in-memory; production should use Redis/DB)
_task_store: Dict[str, Dict[str, Any]] = {}

# Process pool for CPU-bound backtest computations
_executor = ProcessPoolExecutor(max_workers=min(4, (os.cpu_count() or 2)))


def get_market_data_service() -> MarketDataService:
    """Get or create the MarketDataService singleton."""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service


def get_backtest_service() -> BacktestService:
    """Get or create the BacktestService singleton."""
    global _backtest_service
    if _backtest_service is None:
        _backtest_service = BacktestService(get_market_data_service())
    return _backtest_service


@router.get("/instruments", response_model=List[str])
async def list_instruments():
    return get_market_data_service().list_instruments()


@router.post("/instruments/sync", response_model=Dict[str, Any])
async def sync_instruments():
    """Sync instrument registry with storage."""
    try:
        count = get_market_data_service().data_service.sync_registry()
        return {
            "status": "success",
            "message": f"Synced {count} instruments",
            "count": count
        }
    except Exception as e:
        logging.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{symbol}", response_model=Dict[str, Any])
async def get_market_data(symbol: str, timeframe: str = "1h"):
    try:
        candles = get_market_data_service().get_candles(symbol, timeframe)
        return {
            "symbol": symbol,
            "candles": candles,
            "timeframe": timeframe
        }
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Failed to fetch data for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _run_backtest_sync(request_dict: dict) -> dict:
    """Run backtest synchronously (for use in process pool).

    Must be a top-level function for ProcessPoolExecutor pickling.
    """
    from services.backtest_service import BacktestService
    from services.market_data_service import MarketDataService
    from api.models import BacktestRequest

    svc = BacktestService(MarketDataService())
    req = BacktestRequest(**request_dict)
    result = svc.run_backtest(req)
    return result.model_dump()


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run a backtest synchronously (original behavior, backward-compatible)."""
    try:
        return get_backtest_service().run_backtest(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.error(f"Backtest execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/async", response_model=BacktestTaskResponse)
async def run_backtest_async(request: BacktestRequest):
    """Submit a backtest for async execution and return immediately with a task_id.

    The backtest runs in a separate process to avoid blocking the ASGI event loop.
    Poll /backtest/status/{task_id} for results.
    """
    task_id = str(uuid.uuid4())

    # Store initial task state
    _task_store[task_id] = {
        "status": "processing",
        "result": None,
        "error": None,
    }

    # Submit to process pool
    loop = asyncio.get_event_loop()

    async def _run_task():
        try:
            result_dict = await loop.run_in_executor(
                _executor,
                _run_backtest_sync,
                request.model_dump(),
            )
            _task_store[task_id]["status"] = "completed"
            _task_store[task_id]["result"] = result_dict
        except Exception as e:
            logging.error(f"Async backtest {task_id} failed: {e}", exc_info=True)
            _task_store[task_id]["status"] = "failed"
            _task_store[task_id]["error"] = str(e)

    # Fire and forget — runs in background
    asyncio.ensure_future(_run_task())

    return BacktestTaskResponse(task_id=task_id)


@router.get("/backtest/status/{task_id}", response_model=BacktestStatusResponse)
async def get_backtest_status(task_id: str):
    """Poll the status of an async backtest task."""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = _task_store[task_id]

    result = None
    if task["result"]:
        result = BacktestResponse(**task["result"])

    return BacktestStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=result,
        error=task.get("error"),
    )


def get_scanner_service() -> ScannerService:
    """Get or create the ScannerService singleton."""
    global _scanner_service
    if _scanner_service is None:
        _scanner_service = ScannerService(get_backtest_service())
    return _scanner_service


@router.post("/scan", response_model=ScanResponse)
async def run_scan(request: ScanRequest):
    try:
        return await get_scanner_service().scan(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Scan execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/storage")
async def get_storage_provider():
    """Get current storage provider configuration."""
    return {"provider": os.environ.get("HERMES_STORAGE_PROVIDER", "local")}


@router.post("/settings/storage")
async def update_storage_provider(settings: StorageSettingsUpdate):
    """Update storage provider and reload services."""
    start_provider = os.environ.get("HERMES_STORAGE_PROVIDER", "local")
    
    if settings.provider not in ["local", "cloudflare_r2", "oracle_object_storage"]:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {settings.provider}")
    
    # Update environment variable for the process
    os.environ["HERMES_STORAGE_PROVIDER"] = settings.provider
    logging.info(f"Switching storage provider: {start_provider} -> {settings.provider}")
    
    try:
        # Clear DataSettings cache
        get_settings.cache_clear()
        
        # Reset singletons to force recreation with new settings
        global _market_data_service, _backtest_service, _scanner_service
        _market_data_service = None
        _backtest_service = None
        _scanner_service = None
        
        # Validate connection by attempting to list instruments
        svc = get_market_data_service()
        instruments = svc.list_instruments()
        
        return {
            "status": "success",
            "provider": settings.provider,
            "message": f"Switched to {settings.provider}",
            "instrument_count": len(instruments)
        }
    except Exception as e:
        # Revert on failure
        logging.error(f"Failed to switch provider: {e}")
        os.environ["HERMES_STORAGE_PROVIDER"] = start_provider
        get_settings.cache_clear()
        _market_data_service = None # Reset again to be safe
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to switch provider: {str(e)}. Reverted to {start_provider}."
        )

