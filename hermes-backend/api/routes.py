from fastapi import APIRouter, HTTPException
import logging
import os
import sys
from typing import List, Dict, Any

# Add parent directory to path to allow imports if running from top level
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from services.market_data_service import MarketDataService  # noqa: E402
from services.backtest_service import BacktestService  # noqa: E402
from .models import BacktestRequest, BacktestResponse  # noqa: E402

router = APIRouter()

# Lazy service initialization to allow mocking in tests
_market_data_service = None
_backtest_service = None


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


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    try:
        return get_backtest_service().run_backtest(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.error(f"Backtest execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
