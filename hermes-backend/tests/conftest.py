import pytest
import polars as pl

@pytest.fixture
def sample_ohlcv_df():
    # Generate 200 rows of minute data
    import numpy as np
    from datetime import datetime, timedelta
    
    base_time = datetime(2023, 1, 1, 10, 0, 0)
    timestamps = [base_time + timedelta(minutes=i) for i in range(200)]
    
    # Random walk for close
    np.random.seed(42)
    close = np.cumprod(1 + np.random.normal(0, 0.001, 200)) * 100
    
    return pl.DataFrame({
        "timestamp": timestamps,
        "open": close, # Simple approximation
        "high": close * 1.001,
        "low": close * 0.999,
        "close": close,
        "volume": [1000] * 200,
        "symbol": ["TEST"] * 200
    })

@pytest.fixture
def temp_data_dir(tmp_path, sample_ohlcv_df):
    d = tmp_path / "data"
    d.mkdir()
    d_minute = d / "minute"
    d_minute.mkdir()
    
    # Write sample parquet file
    sample_ohlcv_df.write_parquet(d_minute / "TEST_SYM.parquet")
    
    return str(d_minute)
