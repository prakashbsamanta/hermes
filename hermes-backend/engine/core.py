import polars as pl
import numpy as np
import logging
from typing import cast
from .strategy import Strategy

class BacktestEngine:
    """
    Vectorized Backtesting Engine using Polars.
    """
    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash

    def run(self, strategy: Strategy, data: pl.DataFrame):
        """
        Executes the strategy on the provided data.
        Returns the data with added columns: ['signal', 'position', 'strategy_returns', 'equity']
        """
        logging.info("Generating signals...")
        # 1. Generate Signals (1, -1, 0)
        df = strategy.generate_signals(data)
        
        # 2. Derive Positions
        # If Signal=1 (Buy), we hold position (1) until Signal=-1 (Sell).
        # We forward fill the position to show "Holding".
        # This logic is for a simple "Long Only" or "Long/Short" switch.
        # For this engine, we assume:
        # Signal 1 = Enter Long
        # Signal -1 = Exit (Go to 0)
        # Signal 0 = No Change
        
        # We need to forward fill the signals to get continuous 'position' state
        # But we need to handle the logic carefully: -1 should make it 0.
        
        # Easier Approach for First Version:
        # Signal column is "Target Position" (1 = Invested, 0 = Cash)
        # If the strategy returns Buy/Sell signals, we need to convert to Position.
        
        # Let's assume Strategy returns the TARGET POSITION (1 means "be long", 0 means "be flat").
        # If it returns "Action" (Buy/Sell), we need a cumulative sum logic or similar.
        # Let's standardize Strategy to return TARGET POSITION for Vectorized simplicity.
        # If 'signal' is meant to be Position:
        
        if "signal" not in df.columns:
            raise ValueError("Strategy must output a DataFrame with a 'signal' column.")

        # 3. Calculate Returns
        # We shift position by 1 because we enter at the OPEN of the NEXT bar 
        # based on the signal from the CURRENT bar (Close).
        # strategy_return = position(t-1) * (Price(t) / Price(t-1) - 1)
        
        logging.info("Calculating equity curve...")
        
        # Calculate Asset Returns (Close to Close)
        # Note: For minute data, this is minute-to-minute return.
        # Calculate Asset Returns (Close to Close)
        # Note: For minute data, this is minute-to-minute return.
        # SAFETY: Handle Division by Zero or NaN results immediately.
        # If prev_close is 0 or NaN (should be filtered, but double check), result is Inf/NaN.
        # We fill invalid returns with 0.0 (Flat).
        
        df = df.with_columns([
            (pl.col("close") / pl.col("close").shift(1) - 1)
            .fill_nan(0.0)
            .fill_null(0.0)
            .alias("market_return")
        ])
        
        # Position Logic: Signal at T affects Return at T+1
        df = df.with_columns([
            pl.col("signal").shift(1).fill_null(0).alias("position")
        ])
        
        # Strategy Returns
        # We handle both Nulls (shift artifact) and NaNs (div by zero potential)
        # Strategy Returns
        # We handle both Nulls (shift artifact) and NaNs (div by zero potential)
        # SAFETY: Ensure strategy return doesn't explode.
        df = df.with_columns([
            (pl.col("position") * pl.col("market_return"))
            .fill_null(0.0)
            .fill_nan(0.0)
            .alias("strategy_return")
        ])
        
        # Equity Curve
        # Cumulative Product of (1 + return) * initial_cash
        df = df.with_columns([
            (self.initial_cash * (1 + pl.col("strategy_return")).cum_prod()).alias("equity")
        ])
        
        return df

    def calculate_metrics(self, df: pl.DataFrame):
        """
        Calculates key performance metrics.
        """
        total_return = (df["equity"][-1] / self.initial_cash) - 1
        
        # Max Drawdown
        equity = df["equity"]
        running_max = equity.cum_max()
        drawdown = (equity - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Sharpe Ratio (Simplified for Minute Data)
        # We generalize to Annualized Sharpe
        # Minutes per year (trading) ~= 6.5 hours * 60 * 252 ~= 98280
        # This is a rough approximation.
        returns = df["strategy_return"].drop_nulls()
        if len(returns) > 0:
            mean_ret = cast(float, returns.mean())
            std_dev = cast(float, returns.std())
            sharpe = 0.0
            # Ensure not None and not zero
            if mean_ret is not None and std_dev is not None and std_dev != 0:
                sharpe = float((mean_ret / std_dev) * np.sqrt(252 * 375))
        else:
            sharpe = 0.0

        return {
            "Total Return": f"{total_return:.2%}",
            "Max Drawdown": f"{cast(float, max_drawdown or 0.0):.2%}",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Final Equity": f"{df['equity'][-1]:.2f}"
        }
