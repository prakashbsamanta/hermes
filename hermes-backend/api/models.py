from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class BacktestRequest(BaseModel):
    symbol: str
    strategy: str  # e.g. "SMACrossover"
    params: Dict[str, Any] = {}
    initial_cash: float = 100000.0

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
