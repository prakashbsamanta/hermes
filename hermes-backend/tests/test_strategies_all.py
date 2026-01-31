from strategies.macd import MACDStrategy
from strategies.bollinger import BollingerBandsStrategy
from strategies.sma_cross import SMACrossover

def test_macd_strategy(sample_ohlcv_df):
    strat = MACDStrategy(params={"fast_period": 2, "slow_period": 3, "signal_period": 2})
    
    result_df = strat.generate_signals(sample_ohlcv_df)
    
    assert "macd_line" in result_df.columns
    assert "signal_line" in result_df.columns
    assert "signal" in result_df.columns
    assert result_df["signal"].null_count() == 0

def test_bollinger_strategy(sample_ohlcv_df):
    strat = BollingerBandsStrategy(params={"period": 3, "std_dev": 1.0})
    
    result_df = strat.generate_signals(sample_ohlcv_df)
    
    assert "bb_upper" in result_df.columns
    assert "bb_lower" in result_df.columns
    assert "signal" in result_df.columns
    
    # Check band logic: Upper > Lower
    assert (result_df["bb_upper"] >= result_df["bb_lower"]).all()

def test_sma_cross_strategy(sample_ohlcv_df):
    strat = SMACrossover(params={"fast_period": 2, "slow_period": 3})
    
    result_df = strat.generate_signals(sample_ohlcv_df)
    
    assert "sma_fast" in result_df.columns
    assert "sma_slow" in result_df.columns
    assert "signal" in result_df.columns
