import numpy as np
import polars as pl
from typing import Dict, List, Union, cast

class MetricsService:
    @staticmethod
    def calculate_metrics(equity_curve: Union[List[float], pl.Series], initial_cash: float) -> Dict[str, str]:
        """
        Calculates standarized performance metrics from an equity curve.
        """
        if isinstance(equity_curve, list):
            equity_curve = pl.Series("equity", equity_curve)
            
        if len(equity_curve) < 2:
            return {
                "Total Return": "0.00%",
                "Max Drawdown": "0.00%",
                "Sharpe Ratio": "0.00",
                "Final Equity": f"{initial_cash:.2f}"
            }

        # 1. Total Return
        final_equity = equity_curve[-1]
        total_return = (final_equity / initial_cash) - 1

        # 2. Max Drawdown
        running_max = equity_curve.cum_max()
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = drawdown.min()

        # 3. Sharpe Ratio
        # Calculate returns from equity curve
        returns = equity_curve.diff() / equity_curve.shift(1)
        returns = returns.drop_nulls().fill_nan(0.0)
        
        sharpe = 0.0
        if len(returns) > 0:
            # Polars mean() returns a float or None for Series
            raw_mean = returns.mean()
            raw_std = returns.std()
            
            mean_ret = float(raw_mean) if raw_mean is not None else 0.0 # type: ignore
            std_dev = float(raw_std) if raw_std is not None else 0.0 # type: ignore
            
            # Annualize
            if raw_mean is not None and raw_std is not None and std_dev != 0:
                sharpe = (mean_ret / std_dev) * np.sqrt(252 * 375)

        return {
            "Total Return": f"{total_return:.2%}",
            "Max Drawdown": f"{cast(float, max_drawdown or 0.0):.2%}",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Final Equity": f"{final_equity:.2f}"
        }
