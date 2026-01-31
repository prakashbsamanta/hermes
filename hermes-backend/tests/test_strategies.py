import polars as pl
from strategies.rsi import RSIStrategy

def test_rsi_strategy_calculation(sample_ohlcv_df):
    strat = RSIStrategy(params={"period": 2}) # Small period for small data
    
    # Run signal generation
    result_df = strat.generate_signals(sample_ohlcv_df)
    
    assert "rsi" in result_df.columns
    assert "signal" in result_df.columns
    
    # Check RSI values logic roughly
    # We rely on polars calculation but ensure columns are produced and no crash
    assert result_df.select(pl.col("rsi").null_count()).item() == 0
    
    # Check signal values are 0, 1, or -1 (or whatever strategy uses)
    # Our RSI uses 1 (Long) or 0 (Flat).
    unique_signals = result_df["signal"].unique().to_list()
    assert set(unique_signals).issubset({0, 1, None}) 
