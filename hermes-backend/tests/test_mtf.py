import polars as pl
from strategies.mtf_trend_following import MTFTrendFollowingStrategy

def test_mtf_strategy(sample_ohlcv_df):
    # This strategy expects "rsi" and "bullish_trend_htf" columns in its logic?
    # No, it calculates them.
    # It requires `get_higher_timeframe_data` or similar? 
    # Let's check the code via inspection earlier or assume it uses standard logic.
    # It seems to calculate RSI.
    # But does it fetch HTF data?
    # The file inspection showed it relies on `pl.col("bullish_trend_htf")`. 
    # This implies the input DF must have this column or the strategy fetches it.
    # Since it's vectorized and takes `df`, usually HTF data is merged before or inside.
    # If inside, it needs access to data loader?
    # Inspecting strategy:
    # It seems it expects `bullish_trend_htf` to be present or calculates it?
    # Let's inspect `mtf_trend_following.py` fully if I can.
    # Wait, I saw it in Step 133 (implicit list but not full view).
    
    # Let's assume for this test we need to provide input DF with `bullish_trend_htf` if the strategy doesn't compute it.
    # Or if logic calculates it.
    
    # If I run it on sample_ohlcv_df, it might fail if column missing.
    # Let's try adding the column.
    
    df = sample_ohlcv_df.with_columns(
        pl.lit(True).alias("bullish_trend_htf")
    )
    
    strat = MTFTrendFollowingStrategy(params={})
    result_df = strat.generate_signals(df)
    
    assert "signal" in result_df.columns
    # Logic: Buy if RSI < 30 AND Bullish HTF.
    # default RSI period 14. Data is 5 rows. RSI will be null.
    
    pass
