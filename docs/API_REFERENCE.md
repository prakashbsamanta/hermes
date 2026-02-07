# 🔌 Hermes API Reference

**Base URL**: `http://localhost:8000`  
**Version**: 1.0.0

---

## Overview

The Hermes API provides endpoints for running backtests, retrieving market data, and managing instruments.

---

## Endpoints

### Health Check

```http
GET /
```

**Description**: Verify API is running.

**Response**:
```json
{
  "status": "Hermes API is running"
}
```

---

### Run Backtest

```http
POST /backtest
```

**Description**: Execute a backtest with specified strategy and parameters.

**Request Body**:
```json
{
  "symbol": "RELIANCE",
  "strategy": "RSIStrategy",
  "params": {
    "period": 14,
    "overbought": 70,
    "oversold": 30
  },
  "initial_cash": 100000.0,
  "mode": "vector",
  "slippage": 0.001,
  "commission": 0.0,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

**Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `symbol` | string | ✅ | - | Instrument symbol (e.g., "RELIANCE") |
| `strategy` | string | ✅ | - | Strategy name (see Available Strategies) |
| `params` | object | ❌ | `{}` | Strategy-specific parameters |
| `initial_cash` | float | ❌ | `100000.0` | Starting capital |
| `mode` | string | ❌ | `"vector"` | `"vector"` (fast) or `"event"` (realistic) |
| `slippage` | float | ❌ | `0.0` | Slippage as decimal (0.01 = 1%) |
| `commission` | float | ❌ | `0.0` | Commission per unit traded |
| `start_date` | string | ❌ | `null` | Start date filter (YYYY-MM-DD) |
| `end_date` | string | ❌ | `null` | End date filter (YYYY-MM-DD) |

**Response** (`200 OK`):
```json
{
  "symbol": "RELIANCE",
  "strategy": "RSIStrategy",
  "metrics": {
    "Total Return": "12.45%",
    "Max Drawdown": "-5.23%",
    "Sharpe Ratio": "1.85",
    "Final Equity": "112450.00"
  },
  "equity_curve": [
    {"time": 1704067200, "value": 100000.0},
    {"time": 1704153600, "value": 100250.0}
  ],
  "signals": [
    {"time": 1704240000, "type": "buy", "price": 2450.50},
    {"time": 1704499200, "type": "sell", "price": 2510.25}
  ],
  "candles": [
    {"time": 1704067200, "open": 2400.0, "high": 2420.0, "low": 2395.0, "close": 2415.0, "volume": 150000}
  ],
  "indicators": {
    "rsi": [
      {"time": 1704067200, "value": 45.5}
    ]
  },
  "status": "success",
  "error": null
}
```

**Error Response** (`400 Bad Request`):
```json
{
  "detail": "Strategy 'InvalidStrategy' not found. Available: RSIStrategy, MACDStrategy, ..."
}
```

---

### List Instruments

```http
GET /instruments
```

**Description**: Get list of available instrument symbols.

**Response** (`200 OK`):
```json
["AARTIIND", "ABB", "ABBOTINDIA", "ABCAPITAL", ...]
```

---

### Get Market Data

```http
GET /data/{symbol}?timeframe=1h
```

**Description**: Retrieve raw OHLCV data for a symbol.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Instrument symbol |

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | string | `"1m"` | Data timeframe |

**Response** (`200 OK`):
```json
{
  "symbol": "RELIANCE",
  "timeframe": "1h",
  "candles": [
    {"time": 1704067200, "open": 2400.0, "high": 2420.0, "low": 2395.0, "close": 2415.0, "volume": 150000}
  ]
}
```

**Error Response** (`404 Not Found`):
```json
{
  "detail": "Symbol 'INVALID' not found"
}
```

---

## Available Strategies

| Strategy | Description | Parameters |
|----------|-------------|------------|
| `RSIStrategy` | Relative Strength Index | `period`, `overbought`, `oversold` |
| `MACDStrategy` | Moving Average Convergence Divergence | `fast`, `slow`, `signal` |
| `BollingerBandsStrategy` | Bollinger Bands | `period`, `std_dev` |
| `SMACrossover` | Simple Moving Average Crossover | `fast_period`, `slow_period` |
| `MTFTrendFollowingStrategy` | Multi-Timeframe Trend Following | `primary_tf`, `htf` |

### Strategy Parameters

#### RSIStrategy

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | int | 14 | RSI calculation period |
| `overbought` | int | 70 | Overbought threshold (sell signal) |
| `oversold` | int | 30 | Oversold threshold (buy signal) |

#### MACDStrategy

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fast` | int | 12 | Fast EMA period |
| `slow` | int | 26 | Slow EMA period |
| `signal` | int | 9 | Signal line period |

#### BollingerBandsStrategy

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | int | 20 | Moving average period |
| `std_dev` | float | 2.0 | Standard deviation multiplier |

#### SMACrossover

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fast_period` | int | 50 | Fast SMA period |
| `slow_period` | int | 200 | Slow SMA period |

---

## Error Codes

| Code | Description |
|------|-------------|
| `400` | Bad Request - Invalid parameters or strategy |
| `404` | Not Found - Symbol or resource not found |
| `422` | Validation Error - Missing required fields |
| `500` | Internal Server Error - Unexpected error |

---

## Rate Limits

Currently no rate limits are enforced. This will be added in a future version.

---

## CORS

The API allows requests from:
- `http://localhost:5173` (development frontend)

---

## Examples

### cURL

```bash
# Health check
curl http://localhost:8000/

# Run backtest
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "strategy": "RSIStrategy",
    "params": {"period": 14}
  }'

# List instruments
curl http://localhost:8000/instruments

# Get market data
curl http://localhost:8000/data/RELIANCE?timeframe=1h
```

### Python

```python
import requests

# Run backtest
response = requests.post(
    "http://localhost:8000/backtest",
    json={
        "symbol": "RELIANCE",
        "strategy": "RSIStrategy",
        "params": {"period": 14},
        "mode": "event",
        "start_date": "2024-01-01",
        "end_date": "2024-06-30"
    }
)

result = response.json()
print(f"Return: {result['metrics']['Total Return']}")
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/backtest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbol: 'RELIANCE',
    strategy: 'RSIStrategy',
    params: { period: 14 }
  })
});

const result = await response.json();
console.log(`Return: ${result.metrics['Total Return']}`);
```

---

*Last Updated: 2026-02-07*
