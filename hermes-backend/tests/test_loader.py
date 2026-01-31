import pytest
import polars as pl
from engine.loader import DataLoader
import os
from datetime import datetime

def test_loader_valid_data(temp_data_dir):
    # Create valid parquet file
    df = pl.DataFrame({
        "timestamp": [1, 2],
        "open": [10.0, 11.0],
        "high": [12.0, 13.0],
        "low": [9.0, 10.0],
        "close": [11.0, 12.0],
    }).with_columns(pl.col("timestamp").cast(pl.Datetime))
    
    df.write_parquet(os.path.join(temp_data_dir, "TEST.parquet"))
    
    loader = DataLoader(data_dir=temp_data_dir)
    loaded_df = loader.load_data(["TEST"])
    
    assert len(loaded_df) == 2
    assert "symbol" in loaded_df.columns
    assert loaded_df["symbol"][0] == "TEST"

def test_loader_integrity_check_failure(temp_data_dir):
    # Create invalid data (High < Low)
    df = pl.DataFrame({
        "timestamp": [1],
        "open": [10.0],
        "high": [8.0],  # Invalid: High < Low (9)
        "low": [9.0],
        "close": [10.0],
    }).with_columns(pl.col("timestamp").cast(pl.Datetime))
    
    df.write_parquet(os.path.join(temp_data_dir, "BAD.parquet"))
    
    loader = DataLoader(data_dir=temp_data_dir)
    loaded_df = loader.load_data(["BAD"])
    
    # Should filtered out the bad row
    assert len(loaded_df) == 0

def test_loader_integrity_check_mixed(temp_data_dir):
    # 1 valid, 1 invalid
    df = pl.DataFrame({
        "timestamp": [1, 2],
        "open": [10.0, 10.0],
        "high": [12.0, 8.0], # 2nd row invalid
        "low": [9.0, 9.0],
        "close": [11.0, 10.0],
    }).with_columns(pl.col("timestamp").cast(pl.Datetime))
    
    df.write_parquet(os.path.join(temp_data_dir, "MIXED.parquet"))
    
    loader = DataLoader(data_dir=temp_data_dir)
    loaded_df = loader.load_data(["MIXED"])
    
    assert len(loaded_df) == 1
    assert loaded_df["high"][0] == 12.0

def test_loader_date_filtering(temp_data_dir):
    df = pl.DataFrame({
        "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "open": [10, 10, 10],
        "high": [12, 12, 12],
        "low": [9, 9, 9],
        "close": [11, 11, 11],
    }).with_columns(pl.col("timestamp").str.to_datetime("%Y-%m-%d"))
    
    df.write_parquet(os.path.join(temp_data_dir, "DATES.parquet"))
    
    loader = DataLoader(data_dir=temp_data_dir)
    
    # Test Start Date
    res1 = loader.load_data(["DATES"], start_date="2023-01-02")
    assert len(res1) == 2
    assert res1["timestamp"][0].date() == datetime(2023, 1, 2).date()
    
    # Test End Date
    res2 = loader.load_data(["DATES"], end_date="2023-01-02")
    assert len(res2) == 2
    assert res2["timestamp"][-1].date() == datetime(2023, 1, 2).date()

