from fastapi import APIRouter, HTTPException
import polars as pl
import os
import sys
import logging
import inspect
from typing import Dict, Type, List, Any

# Add parent directory to path to allow imports if running from top level
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from engine.loader import DataLoader # noqa: E402
from engine.core import BacktestEngine # noqa: E402
from engine.strategy import Strategy # noqa: E402
import strategies # noqa: E402
from .models import BacktestRequest, BacktestResponse, ChartPoint, SignalPoint, CandlePoint, IndicatorPoint # noqa: E402

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

@router.get("/instruments", response_model=List[str])
async def list_instruments():
    try:
        data_dir = get_data_dir()
        # List all parquet files
        files = [f for f in os.listdir(data_dir) if f.endswith(".parquet")]
        # Extract symbol names (filename without extension)
        symbols = [os.path.splitext(f)[0] for f in files]
        return sorted(symbols)
    except Exception as e:
        # If data dir not found or empty, return empty list
        logging.warning(f"Could not list instruments: {str(e)}")
        return []

def resample_data(df: pl.DataFrame, min_points: int = 5000) -> pl.DataFrame:
    """Downsample large datasets to hourly candles for visualization."""
    if len(df) <= min_points:
        return df
        
    # Define aggregation dict for basic OHLCV
    agg_dict = {
        "open": pl.col("open").first(),
        "high": pl.col("high").max(),
        "low": pl.col("low").min(),
        "close": pl.col("close").last(),
        "volume": pl.col("volume").sum(),
    }
    
    # If equity/indicators exist, add them
    if "equity" in df.columns:
        agg_dict["equity"] = pl.col("equity").last()
        
    # Add other float columns as indicators
    exclude = {"timestamp", "open", "high", "low", "close", "volume", "signal", "position", "strategy_return", "equity", "trade_action"}
    for col in df.columns:
        if col not in exclude and df[col].dtype in [pl.Float64, pl.Float32]:
            agg_dict[col] = pl.col(col).last()

    return (
        df.sort("timestamp")
        .group_by_dynamic("timestamp", every="1h")
        .agg(**agg_dict)
        .drop_nulls()
    )

@router.get("/data/{symbol}", response_model=Dict[str, Any])
async def get_market_data(symbol: str):
    try:
        data_dir = get_data_dir()
        loader = DataLoader(data_dir=data_dir)
        try:
            df = loader.load_data([symbol.upper()])
        except Exception:
            raise HTTPException(status_code=404, detail=f"Data not found for {symbol}")

        # Resample for chart
        chart_df = resample_data(df)
        
        # Convert to CandlePoint list
        candles = []
        rows = chart_df.rows(named=True)
        for row in rows:
            ts = int(row["timestamp"].timestamp())
            candles.append(CandlePoint(
                time=ts,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"]
            ))
            
        return {
            "symbol": symbol,
            "candles": candles
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Failed to fetch data for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # 6. Optimize for Visualization (Downsampling)
        chart_df = resample_data(result_df)

        # Identify Indicator Columns (Float columns that are not OHLCV or Signal/Pos)
        exclude_cols = {"timestamp", "open", "high", "low", "close", "volume", "signal", "position", "strategy_return", "equity", "trade_action"}
        indicator_cols = [c for c in result_df.columns if c not in exclude_cols and result_df[c].dtype in [pl.Float64, pl.Float32]]
        
        # Convert to Output Models
        chart_rows = chart_df.rows(named=True)
        
        # Initialize lists
        eq_curve = []
        candles = []
        indicators: Dict[str, List[IndicatorPoint]] = {}
        for col in indicator_cols:
            indicators[col] = []
            
        for row in chart_rows:
            ts = int(row["timestamp"].timestamp())
            
            # Equity Curve
            eq_curve.append(ChartPoint(time=ts, value=row["equity"]))
            
            # Candles
            candles.append(CandlePoint(
                time=ts,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"]
            ))
            
            # Indicators
            for col in indicator_cols:
                if row[col] is not None:
                    indicators[col].append(IndicatorPoint(time=ts, value=row[col]))
            
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
            signals=signals,
            candles=candles,
            indicators=indicators
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Backtest execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
