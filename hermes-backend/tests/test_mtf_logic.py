
import pytest
import polars as pl
from datetime import datetime, timedelta
from api.models import BacktestRequest
from services.backtest_service import BacktestService
from engine.strategy import Strategy
from unittest.mock import MagicMock

# Mock Strategy
class MockStrategy(Strategy):
    def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
        # Buy if close > 100
        return df.with_columns(
            pl.when(pl.col("close") > 100).then(1).otherwise(0).alias("signal")
        )

# Mock Market Data Service
class MockMarketDataService:
    def __init__(self):
        self.data_service = MagicMock()
        
    def resample_data(self, df, interval):
        # Initial primitive resampling
        agg = {
            "open": pl.col("open").first(),
            "high": pl.col("high").max(),
            "low": pl.col("low").min(),
            "close": pl.col("close").last(),
            "volume": pl.col("volume").sum(),
            "symbol": pl.col("symbol").first()
        }
        if "equity" in df.columns:
            agg["equity"] = pl.col("equity").last()
        
        return df.sort("timestamp").group_by_dynamic("timestamp", every=interval).agg(**agg)

@pytest.fixture
def backtest_service():
    mds = MockMarketDataService()
    service = BacktestService(mds)
    # Patch strategy lookup
    service.get_strategies = MagicMock(return_value={"MockStrategy": MockStrategy})
    return service

def test_mtf_signal_shifting(backtest_service):
    """
    Verify that signals from higher timeframe are shifted correctly
    to avoid look-ahead bias.
    """
    # Create 2 hours of minute data
    # 10:00 - 11:00: Price = 90 (No Signal)
    # 11:00 - 12:00: Price = 110 (Signal Generated at end of 12:00? No, aggregated at 11:00 includes data up to 11:59)
    # So 11:00 bar close > 100. Signal at 11:00 timestamp (representing 11:00-11:59).
    # Shifted Signal should appear at 12:00.
    # Execution should start at 12:00+.
    
    dates = [datetime(2024, 1, 1, 10, 0) + timedelta(minutes=i) for i in range(120)]
    prices = [90.0] * 60 + [110.0] * 60
    
    df = pl.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices,
        "low": prices,
        "close": prices,
        "volume": [100] * 120,
        "symbol": ["TEST"] * 120
    })
    
    # Setup mock return
    backtest_service.market_data_service.data_service.get_market_data.return_value = df
    
    request = BacktestRequest(
        symbol="TEST",
        strategy="MockStrategy",
        timeframe="1h", # Aggregates to 10:00 and 11:00 bars
        initial_cash=10000.0,
        mode="vector"
    )
    
    # Run
    response = backtest_service.run_backtest(request)
    
    # Verify in equity curve or signals
    # 10:00 to 11:00: Price 90. Signal 0.
    # 11:00 to 12:00: Price 110. Signal 1 (at 11:00 timestamp).
    # Shifted: Signal 1 appears at 12:00.
    # But data ends at 11:59.
    # So we should see NO trades because the signal appears after our data ends?
    # Wait.
    # 11:00 bar covers 11:00-11:59.
    # If we shift 11:00 signal to 12:00.
    # And our minute data goes up to 11:59.
    # join_asof(backward) for 11:59 looks for <= 11:59.
    # It finds 11:00 (which has signal from 10:00 bar).
    # 10:00 bar had price 90 -> Signal 0.
    # So 11:00 (shifted) has Signal 0.
    # So 11:00-11:59 should have Signal 0.
    # NO TRADES should happen.
    
    assert len(response.signals) == 0

def test_mtf_signal_execution(backtest_service):
    """
    Verify trade execution with 3 hours of data.
    10:00-11:00: 90
    11:00-12:00: 110 (Buy Signal generated)
    12:00-13:00: 120 (Execution should happen here)
    """
    dates = [datetime(2024, 1, 1, 10, 0) + timedelta(minutes=i) for i in range(180)]
    prices = [90.0] * 60 + [110.0] * 60 + [120.0] * 60
    
    df = pl.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices,
        "low": prices,
        "close": prices,
        "volume": [100] * 180,
        "symbol": ["TEST"] * 180
    })
    
    backtest_service.market_data_service.data_service.get_market_data.return_value = df
    
    request = BacktestRequest(
        symbol="TEST",
        strategy="MockStrategy",
        timeframe="1h",
        initial_cash=10000.0
    )
    
    response = backtest_service.run_backtest(request)
    
    # 10:00 Bar (90) -> Signal 0. Shifted to 11:00.
    # 11:00 Bar (110) -> Signal 1. Shifted to 12:00.
    # 12:00 Bar (120) -> Signal 1.
    
    # So trades should start at 12:00.
    # First trade at 12:00?
    
    assert len(response.signals) > 0
    first_signal = response.signals[0]
    expected_timestamp = datetime(2024, 1, 1, 12, 0).timestamp()
    
    print(f"First signal time: {datetime.fromtimestamp(first_signal.time)}")
    # We expect trade > 12:00 (likely 12:01 due to minute shift)
    assert first_signal.time >= expected_timestamp

def test_mtf_strategy_with_symbol_access(backtest_service):
    """
    Verify that a strategy accessing 'symbol' column works correctly
    after resampling (preventing regression of symbol loss).
    """
    class SymbolAccessStrategy(Strategy):
        def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
            # Check if symbol column exists and is not null
            if "symbol" not in df.columns:
                raise ValueError("Symbol column missing!")
            
            # Simple signal based on symbol (just checks access)
            return df.with_columns(
                pl.when(pl.col("symbol") == "TEST").then(1).otherwise(0).alias("signal")
            )

    # Patch strategy factory to return this local class
    backtest_service.get_strategies = MagicMock(return_value={"SymbolAccessStrategy": SymbolAccessStrategy})
    
    dates = [datetime(2024, 1, 1, 10, 0) + timedelta(minutes=i) for i in range(120)]
    prices = [100.0] * 120
    
    df = pl.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices,
        "low": prices,
        "close": prices,
        "volume": [100] * 120,
        "symbol": ["TEST"] * 120
    })
    
    backtest_service.market_data_service.data_service.get_market_data.return_value = df
    
    request = BacktestRequest(
        symbol="TEST",
        strategy="SymbolAccessStrategy",
        timeframe="1h",
        initial_cash=10000.0
    )
    
    # This should run without error
    response = backtest_service.run_backtest(request)
    assert response.metrics["Total Return"] is not None
