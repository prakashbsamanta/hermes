from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class BacktestRequest(BaseModel):
    symbol: str
    strategy: str  # e.g. "SMACrossover"
    params: Dict[str, Any] = {}
    initial_cash: float = 100000.0
    mode: str = "vector" # "vector" | "event"
    slippage: float = 0.0 # Percent (0.01 = 1%)
    commission: float = 0.0 # Per unit (dollar)
    start_date: str | None = None # "YYYY-MM-DD"
    end_date: str | None = None # "YYYY-MM-DD"

class ChartPoint(BaseModel):
    time: int # Unix timestamp (seconds) or formatted string
    value: float
    
class SignalPoint(BaseModel):
    time: int
    type: str # "buy" or "sell"
    price: float

class CandlePoint(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class IndicatorPoint(BaseModel):
    time: int
    value: float

class BacktestResponse(BaseModel):
    symbol: str
    strategy: str
    metrics: Dict[str, Any]
    equity_curve: List[ChartPoint]
    signals: List[SignalPoint]
    candles: List[CandlePoint] = []
    indicators: Dict[str, List[IndicatorPoint]] = {}
    status: str = "success"
    error: Optional[str] = None


class ScanRequest(BaseModel):
    strategy: str
    params: Dict[str, Any] = {}
    symbols: List[str] | None = None  # None = all instruments
    initial_cash: float = 100000.0
    mode: str = "vector"
    start_date: str | None = None
    end_date: str | None = None
    max_concurrency: int = 10


class ScanResult(BaseModel):
    symbol: str
    metrics: Dict[str, Any] = {}
    signal_count: int = 0
    last_signal: str | None = None
    last_signal_time: int | None = None
    status: str = "success"  # "success" | "error" | "cached"
    error: str | None = None
    cached: bool = False



class ScanResponse(BaseModel):
    strategy: str
    total_symbols: int
    completed: int
    failed: int
    cached_count: int = 0
    fresh_count: int = 0
    results: List[ScanResult]
    elapsed_ms: int

class StorageSettingsUpdate(BaseModel):
    provider: str  # "local", "cloudflare_r2", "oracle_object_storage"

