import pytest
import polars as pl

@pytest.fixture
def sample_ohlcv_df():
    return pl.DataFrame({
        "timestamp": [1, 2, 3, 4, 5],
        "open": [100, 102, 101, 103, 104],
        "high": [105, 106, 104, 108, 110],
        "low": [99, 101, 100, 102, 103],
        "close": [102, 104, 103, 107, 109],
        "volume": [1000, 1200, 1100, 1500, 2000],
        "symbol": ["TEST"] * 5
    }).with_columns(
        pl.col("timestamp").cast(pl.Datetime)
    )

@pytest.fixture
def temp_data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    d_minute = d / "minute"
    d_minute.mkdir()
    return str(d_minute)
