# Hermes: TA-Lib Integration Plan

> **Status: DEFERRED — Not yet implemented. This is the agreed-upon blueprint.**
> Created: 2026-02-28 | Author: Antigravity

---

## Background

The current indicator architecture is **Tier 1 only**: pure native Polars expressions
(RSI via `ewm_mean`, SMA via `rolling_mean`, Bollinger via `rolling_std`, MACD via `ewm_mean`).

This is correct and fast for simple indicators. But for complex indicators (ADX, Ichimoku,
Hilbert Transform, candlestick pattern recognition), writing them in native Polars is error-prone
and unmaintainable. TA-Lib solves this via C-level execution.

---

## Decision: The Three-Tier Indicator Architecture

### Tier 1 — Native Polars (Current, keep as-is)
**Use for:** SMA, EMA, RSI, MACD, Bollinger Bands, Stochastic (basic)

**Why:** Polars can multithread native expressions across instruments in Rust.
When scanning 9000+ instruments, Polars parallelises across columns automatically.
No serialization overhead.

**Files:** `strategies/rsi.py`, `strategies/sma_cross.py`, `strategies/macd.py`, `strategies/bollinger.py`

---

### Tier 2 — TA-Lib via `map_batches` (To implement)
**Use for:** ADX, ATR, Ichimoku, Hilbert Transform, DEMA, TEMA, candlestick patterns

**Why:** TA-Lib is written in optimised C. Polars `.to_numpy()` extracts
columns as zero-copy Arrow-backed arrays that TA-Lib consumes directly —
no serialization, no pandas roundtrip.

**Pattern:**
```python
import polars as pl
import talib
import numpy as np

def add_adx(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    def calculate_adx(struct: pl.Series) -> pl.Series:
        high  = struct.struct.field("high").to_numpy()
        low   = struct.struct.field("low").to_numpy()
        close = struct.struct.field("close").to_numpy()
        result = talib.ADX(high, low, close, timeperiod=period)
        return pl.Series("adx", result)

    return df.with_columns(
        pl.struct(["high", "low", "close"])
          .map_batches(calculate_adx)
          .alias("adx")
    )
```

**Location:** Create `engine/indicators/talib_bridge.py` — a pure utility module
with zero strategy logic, only TA-Lib wrappers following the pattern above.

---

### Tier 3 — PostgreSQL UNLOGGED Cache (Deferred, separate plan)
Pre-compute and cache expensive indicator results in PostgreSQL UNLOGGED tables
(WAL-bypassed for max write speed) for horizontal scaling. Requires:
- PostgreSQL setup + pgbouncer connection pooling
- Polars read_database integration
- Serialization strategy for Polars DataFrames (Parquet bytes in bytea column)

---

## Planned Indicators to Implement via TA-Lib

| Indicator | TA-Lib Function | Use Case |
|-----------|----------------|----------|
| ADX | `talib.ADX()` | Trend strength filter in MTFTrendFollowing |
| ATR | `talib.ATR()` | Volatility-based position sizing (currently approximated) |
| Ichimoku | Manual (TA-Lib lacks it) | Cloud support/resistance for swing trading |
| Hilbert Transform | `talib.HT_TRENDMODE()` | Cycle detection |
| DEMA / TEMA | `talib.DEMA()`, `talib.TEMA()` | Faster trend following |
| Candlestick Patterns | `talib.CDLENGULFING()` etc. | Pattern-based signal generation |
| Stochastic | `talib.STOCH()` | Momentum confirmation |
| CCI | `talib.CCI()` | Mean reversion confirmation |

---

## Installation

### Development (macOS)
```bash
brew install ta-lib
source venv/bin/activate
pip install TA-Lib
```

### Docker / CI (Ubuntu)
```dockerfile
RUN apt-get install -y libta-lib-dev
RUN pip install TA-Lib
```

> **Note:** Python 3.14 support for TA-Lib Python bindings — verify compatibility
> before installing. As of Feb 2026, the C library works fine; the Python wrapper
> may need `pip install ta-lib --pre` for 3.14 support.

---

## Test Strategy for TA-Lib Indicators

When TA-Lib indicators are added, extend `test_quant_framework.py` with:

1. **Known-value tests**: Use the same `_make_ohlcv()` + synthetic dataset pattern.
   For example, ATR on a constant-range dataset should equal the constant range.

2. **Cross-validation against NumPy oracle**: Compare TA-Lib output against the pure
   NumPy reference functions in `test_quant_framework.py`. Match to 4 decimal places.

3. **Never use pandas** in tests — the NumPy oracle pattern eliminates all
   serialisation overhead and external dependencies from the test suite.

---

## Migration Path

1. `brew install ta-lib && pip install TA-Lib` in dev env (check Python 3.14 compat first)
2. Create `engine/indicators/__init__.py` and `engine/indicators/talib_bridge.py`
3. Implement `add_adx`, `add_atr`, `add_stoch` wrappers using `map_batches` pattern
4. Update `MTFTrendFollowingStrategy` to use `talib_bridge.add_adx()` as a trend filter
5. Update `RiskManager` to use `talib_bridge.add_atr()` for true ATR-based sizing
6. Add deterministic + NumPy cross-validation tests for each new indicator
7. Benchmark: compare scan time for 9000 instruments before and after

---

## What We Are NOT Doing

- NO `pandas-ta` anywhere (Python/pandas overhead, numba incompatibility with Python 3.14)
- NO pandas conversion in the production engine path
- NO replacing existing Tier 1 native Polars indicators with TA-Lib
- NO pandas in tests (NumPy oracle approach is established and dependency-free)
