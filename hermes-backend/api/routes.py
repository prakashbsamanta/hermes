from fastapi import APIRouter, HTTPException
import polars as pl
import os
import sys
import logging
import inspect
from typing import Dict, Type

# Add parent directory to path to allow imports if running from top level
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from engine.loader import DataLoader
from engine.core import BacktestEngine
from engine.strategy import Strategy
import strategies
from .models import BacktestRequest, BacktestResponse, ChartPoint, SignalPoint

router = APIRouter()

# Setup Data Directory (Assumption: running from project root or hermes-backend)
# We try to be robust finding the data dir.
BASE_DIR = os.path.dirname(parent_dir) # TheForge/hermes/
DATA_DIR_CANDIDATES = [
    os.path.join(parent_dir, "data", "minute"),
    os.path.join(BASE_DIR, "hermes-backend", "data", "minute"),
    "hermes-backend/data/minute",
    "data/minute"
]

def get_data_dir():
    for d in DATA_DIR_CANDIDATES:
        if os.path.exists(d):
            return d
    raise FileNotFoundError("Could not find data/minute directory.")

def get_strategies() -> Dict[str, Type[Strategy]]:
    return {
        name: cls for name, cls in inspect.getmembers(strategies, inspect.isclass)
        if name != "Strategy"
    }

@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    try:
        data_dir = get_data_dir()
        logging.info(f"Using Data Dir: {data_dir}")
        
        # 1. Load Data
        loader = DataLoader(data_dir=data_dir)
        try:
            df = loader.load_data([request.symbol.upper()])
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Data load failed for {request.symbol}: {str(e)}")

        # 2. Get Strategy Class
        avail_strategies = get_strategies()
        if request.strategy not in avail_strategies:
            raise HTTPException(status_code=400, detail=f"Strategy '{request.strategy}' not found. Available: {list(avail_strategies.keys())}")
        
        strategy_cls = avail_strategies[request.strategy]
        
        # 3. Instantiate Strategy
        try:
            strategy = strategy_cls(params=request.params)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid params for strategy: {str(e)}")
            
        # 4. Run Engine
        engine = BacktestEngine(initial_cash=request.initial_cash)
        try:
            result_df = engine.run(strategy, df)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")
            
        # 5. Process Results
        metrics = engine.calculate_metrics(result_df)
        
        # Convert Equity Curve to List[ChartPoint]
        # We need timestamp (int seconds) and equity (float)
        # Polars to list of dicts is fast.
        
        # Ensure timestamp is datetime and sort
        # Assuming Data Loader sorts it.
        
        # Downsample for chart? Not for now, send all minute points or maybe 1h if huge?
        # AARTIIND minute data is ~101k rows. Sending 101k JSON objects is heavy (~10MB+).
        # For a responsive API, we might want to downsample to e.g. 500-1000 points.
        # But for "Authenticity" user requested, let's send full data first or reasonable resample.
        # Let's resample to 1-hour for the chart if length > 5000 points, to keep UI snappy.
        
        eq_df = result_df.select(["timestamp", "equity"])
        if len(eq_df) > 5000:
            # Resample to hourly to reduce payload size for UI visualization
            eq_df = (
                eq_df.sort("timestamp")
                .group_by_dynamic("timestamp", every="1h")
                .agg(pl.col("equity").last())
                .drop_nulls()
            )
            
        # Convert timestamps to unix seconds
        eq_curve = []
        rows = eq_df.rows(named=True)
        for row in rows:
            ts = row["timestamp"].timestamp() # float seconds
            eq_curve.append(ChartPoint(time=int(ts), value=row["equity"]))
            
        # Extract Signals
        # Where signal != 0 AND != null
        # We need to know if it was a BUY (1) or SELL (-1) event vs just holding (1).
        # Our engine returns 'position' (state) and 'signal'.
        # 'signal' column from strategy is the LATCH state (1=Long, 0=Flat).
        # We want TRADES.
        # Trade happens when Position changes.
        # Delta = Position - Position.shift(1).
        # 1 - 0 = +1 (Buy)
        # 0 - 1 = -1 (Sell)
        
        trades_df = result_df.with_columns([
            (pl.col("position") - pl.col("position").shift(1).fill_null(0)).alias("trade_action")
        ]).filter(pl.col("trade_action") != 0).select(["timestamp", "trade_action", "close"])
        
        signals = []
        t_rows = trades_df.rows(named=True)
        for row in t_rows:
            ts = row["timestamp"].timestamp()
            action = "buy" if row["trade_action"] > 0 else "sell"
            signals.append(SignalPoint(time=int(ts), type=action, price=row["close"]))

        return BacktestResponse(
            symbol=request.symbol,
            strategy=request.strategy,
            metrics=metrics,
            equity_curve=eq_curve,
            signals=signals
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Backtest execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
