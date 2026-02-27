import numpy as np
import polars as pl
from typing import Dict, List, Optional, Union, cast

class MetricsService:
    @staticmethod
    def calculate_metrics(
        equity_curve: Union[List[float], pl.Series],
        initial_cash: float,
        fills: Optional[List[Dict]] = None,
    ) -> Dict[str, str]:
        """
        Calculates standardized performance metrics from an equity curve.
        
        Args:
            equity_curve: List of equity values over time
            initial_cash: Starting capital
            fills: Optional list of fill dicts from PortfolioManager for trade-level metrics
        """
        if isinstance(equity_curve, list):
            equity_curve = pl.Series("equity", equity_curve)
            
        if len(equity_curve) < 2:
            return {
                "Total Return": "0.00%",
                "Max Drawdown": "0.00%",
                "Sharpe Ratio": "0.00",
                "Final Equity": f"{initial_cash:.2f}",
                "Total Trades": "0",
                "Win Rate": "N/A",
                "Profit Factor": "N/A",
                "Max Capital at Risk": "N/A",
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

        metrics: Dict[str, str] = {
            "Total Return": f"{total_return:.2%}",
            "Max Drawdown": f"{cast(float, max_drawdown or 0.0):.2%}",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Final Equity": f"{final_equity:.2f}",
        }

        # 4. Trade-level metrics (from PortfolioManager fills)
        if fills and len(fills) > 0:
            # Build round-trip trades from fills
            buy_fills = [f for f in fills if f.get("direction") == "BUY"]
            sell_fills = [f for f in fills if f.get("direction") == "SELL"]
            
            total_trades = min(len(buy_fills), len(sell_fills))
            metrics["Total Trades"] = str(total_trades)
            
            if total_trades > 0:
                # Calculate P&L per round-trip
                winning_trades = 0
                gross_profit = 0.0
                gross_loss = 0.0
                max_capital_in_trade = 0.0
                
                for i in range(total_trades):
                    buy_price = buy_fills[i].get("price", 0)
                    sell_price = sell_fills[i].get("price", 0)
                    qty = buy_fills[i].get("quantity", 0)
                    trade_pnl = (sell_price - buy_price) * qty
                    trade_capital = buy_price * qty
                    
                    if trade_pnl > 0:
                        winning_trades += 1
                        gross_profit += trade_pnl
                    else:
                        gross_loss += abs(trade_pnl)
                    
                    max_capital_in_trade = max(max_capital_in_trade, trade_capital)
                
                win_rate = winning_trades / total_trades
                metrics["Win Rate"] = f"{win_rate:.1%}"
                
                # Profit Factor = Gross Profit / Gross Loss
                if gross_loss > 0:
                    profit_factor = gross_profit / gross_loss
                    metrics["Profit Factor"] = f"{profit_factor:.2f}"
                else:
                    metrics["Profit Factor"] = "∞" if gross_profit > 0 else "N/A"
                
                # Max Capital at Risk (as % of initial)
                max_risk_pct = max_capital_in_trade / initial_cash
                metrics["Max Capital at Risk"] = f"{max_risk_pct:.1%}"
            else:
                metrics["Win Rate"] = "N/A"
                metrics["Profit Factor"] = "N/A"
                metrics["Max Capital at Risk"] = "N/A"
        else:
            metrics["Total Trades"] = "0"
            metrics["Win Rate"] = "N/A"
            metrics["Profit Factor"] = "N/A"
            metrics["Max Capital at Risk"] = "N/A"

        return metrics

