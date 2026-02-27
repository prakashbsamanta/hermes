import inspect
import logging
import polars as pl
from typing import Dict, Type, List
from api.models import BacktestRequest, BacktestResponse, ChartPoint, SignalPoint, CandlePoint, IndicatorPoint
from engine.core import BacktestEngine
from engine.strategy import Strategy
import strategies
from services.market_data_service import MarketDataService

class BacktestService:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    def get_strategies(self) -> Dict[str, Type[Strategy]]:
        return {
            name: cls for name, cls in inspect.getmembers(strategies, inspect.isclass)
            if name != "Strategy"
        }

    def run_backtest(self, request: BacktestRequest) -> BacktestResponse:
        logging.info(f"Running backtest for {request.symbol} with {request.strategy}")
        
        # 1. Load Data using the data service (provides caching)
        try:
            df = self.market_data_service.data_service.get_market_data(
                [request.symbol.upper()],
                start_date=request.start_date,
                end_date=request.end_date,
            )
        except Exception as e:
            raise ValueError(f"Data load failed for {request.symbol}: {str(e)}")

        # 2. Get Strategy Class
        avail_strategies = self.get_strategies()
        if request.strategy not in avail_strategies:
            raise ValueError(f"Strategy '{request.strategy}' not found. Available: {list(avail_strategies.keys())}")
        
        strategy_cls = avail_strategies[request.strategy]
        
        # 3. Instantiate Strategy
        try:
            strategy = strategy_cls(params=request.params)
        except Exception as e:
            raise ValueError(f"Invalid params for strategy: {str(e)}")
            
        if request.mode == "event":
            return self._run_event_backtest(request, df, strategy_cls)
            
        # 4. Run Vector Engine
        # Support Multi-Timeframe (MTF)
        # If execution is vector, we execute on the most granular data (minute),
        # but the strategy might run on a higher timeframe (e.g. "1h").
        
        execution_df = df
        
        # If analysis timeframe is different from raw data (1m), we resample
        # Note: We assume raw data is 1m. If request.timeframe is > 1m, we resample for analysis.
        # If analysis timeframe is different from raw data (1m), we resample
        # Note: We assume raw data is 1m. If request.timeframe is > 1m, we resample for analysis.
        if request.timeframe != "1m":
            logging.info(f"Resampling data to {request.timeframe} for strategy analysis...")
            analysis_df = self.market_data_service.resample_data(execution_df, interval=request.timeframe)
        else:
            analysis_df = execution_df 

        # Run Strategy on Analysis DF
        logging.info("Running strategy on analysis data...")
        strategy_result_df = strategy.generate_signals(analysis_df)
        
        if request.timeframe != "1m":
            # Broadcast signals and indicators back to execution (1m) dataframe
            # We use join_asof to forward-fill the higher timeframe signals to the minute data
            logging.info("Broadcasting signals to execution timeframe (1m)...")
            
            # Identify columns to broadcast (Signal + Indicators)
            # We exclude OHLCV as execution_df already has them (at 1m resolution)
            exclude_cols = {"timestamp", "open", "high", "low", "close", "volume", "symbol"}
            broadcast_cols = [c for c in strategy_result_df.columns if c not in exclude_cols]
            
            if "signal" not in broadcast_cols and "signal" in strategy_result_df.columns:
                 broadcast_cols.append("signal")

            # CRITICAL: Prevent Look-Ahead Bias
            # The strategy runs on aggregated bars (e.g. 1h).
            # The bar at 10:00 contains data from 10:00 to 10:59.
            # The signal is generated at 10:59 (close).
            # If we join this signal to 10:05 minute data, we are peeking into the future.
            # We must SHIFT the signals by 1 period so they become available only at the START of the next bar (11:00).
            
            shifted_strategy = strategy_result_df.select(
                [pl.col("timestamp")] + 
                [pl.col(c).shift(1) for c in broadcast_cols]
            )

            # Polars join_asof
            # backward strategy: for a time t in execution, find the latest time t' <= t in analysis
            execution_df = execution_df.sort("timestamp").join_asof(
                shifted_strategy.sort("timestamp"),
                on="timestamp",
                strategy="backward"
            )
        else:
            execution_df = strategy_result_df

        if request.mode == "event":
            return self._run_event_backtest(request, execution_df, strategy_cls)
            
        # Run Vector Engine on the Execution DF (Minute resolution with signals)
        engine = BacktestEngine(initial_cash=request.initial_cash)
        try:
            result_df = engine.run(strategy, execution_df)
        except Exception as e:
            raise RuntimeError(f"Backtest execution failed: {str(e)}")
            
        # 5. Process Results
        from services.metrics_service import MetricsService
        metrics = MetricsService.calculate_metrics(result_df["equity"], request.initial_cash)
        
        # 6. Optimize for Visualization (Downsampling)
        chart_df = self.market_data_service.resample_data(result_df, interval="1h")

        return self._format_response(request, metrics, result_df, chart_df)

    def _run_event_backtest(self, request, df, strategy_cls):
        from engine.event_engine import EventEngine
        from engine.events import MarketEvent
        from engine.portfolio import PortfolioManager, RiskParams
        from engine.execution import VolumeAwareExecutionHandler
        
        # Setup Engine
        engine = EventEngine()
        bus = engine.bus
        
        # Setup Strategy
        strategy = strategy_cls(params=request.params)
        strategy.set_bus(bus)
        engine.register_strategy(strategy)

        # Map API RiskParams to engine RiskParams
        risk_params = RiskParams(
            sizing_method=request.risk_params.sizing_method,
            fixed_quantity=request.risk_params.fixed_quantity,
            pct_equity=request.risk_params.pct_equity,
            atr_multiplier=request.risk_params.atr_multiplier,
            max_position_pct=request.risk_params.max_position_pct,
            stop_loss_pct=request.risk_params.stop_loss_pct,
        )
        
        # Setup Portfolio Manager (subscribes to Signal, Fill, Market events)
        portfolio = PortfolioManager(
            bus=bus,
            initial_cash=request.initial_cash,
            risk_params=risk_params,
        )

        # Setup Volume-Aware Execution Handler
        execution = VolumeAwareExecutionHandler(
            bus=bus,
            slippage=request.slippage,
            commission=request.commission,
            max_participation_rate=0.10,
        )
        
        # Collect visualization data
        candles = []
        signals_viz = []
        
        # Data Generator
        rows = df.rows(named=True)
        
        def data_gen():
            for row in rows:
                ts = int(row["timestamp"].timestamp())
                evt = MarketEvent(
                    time=ts,
                    symbol=request.symbol,
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"]
                )
                yield evt
                
                # Record equity snapshot every hour
                if ts % 3600 == 0:
                    portfolio.snapshot(ts)
                    candles.append(CandlePoint(
                        time=ts, open=row["open"], high=row["high"],
                        low=row["low"], close=row["close"], volume=row["volume"]
                    ))

        engine.run(data_gen())
        
        # Build equity curve from portfolio snapshots
        equity_curve = [
            ChartPoint(time=snap["time"], value=snap["equity"])
            for snap in portfolio.equity_history
        ]
        
        # Build signal markers from fills log
        for fill in portfolio.fills_log:
            sig_type = "buy" if fill["direction"] == "BUY" else "sell"
            signals_viz.append(SignalPoint(
                time=int(fill["time"]),
                type=sig_type,
                price=fill["price"],
            ))
        
        # Calculate Metrics
        from services.metrics_service import MetricsService
        equity_values = [p["equity"] for p in portfolio.equity_history]
        metrics = MetricsService.calculate_metrics(
            equity_values, request.initial_cash, fills=portfolio.fills_log
        )
        metrics["Status"] = "Event Backtest Completed"
        metrics["Sizing Method"] = risk_params.sizing_method
        metrics["Execution Stats"] = execution.stats()
        
        return BacktestResponse(
            symbol=request.symbol,
            strategy=request.strategy,
            metrics=metrics, 
            equity_curve=equity_curve,
            signals=signals_viz,
            candles=candles,
            indicators={}
        )

    def _format_response(self, request, metrics, result_df, chart_df):
         # Identify Indicator Columns
        exclude_cols = {"timestamp", "open", "high", "low", "close", "volume", "signal", "position", "strategy_return", "market_return", "equity", "trade_action"}
        indicator_cols = [c for c in result_df.columns if c not in exclude_cols and result_df[c].dtype in [pl.Float64, pl.Float32]]
        
        # Convert to Output Models
        chart_rows = chart_df.rows(named=True)
        
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
            
        # Extract Signals (Trades)
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
