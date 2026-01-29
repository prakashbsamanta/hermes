# Hermes Project Status Report
**Date**: 2026-01-29
**Version**: Phase 2 Alpha

## 1. Executive Summary
Hermes is being built as a **High-Performance Systematic Trading Engine** targeting the Indian stock market (NSE). The system is designed to handle 9000+ instruments efficiently using **AsyncIO** for data fetching and **Polars** for vectorized backtesting.

## 2. Achievements (What is Done)

### Phase 1: Data Infrastructure 🗄️
-   **Robust Data Seeder**: Built `data_seeder.py` to fetch historical minute-level data from Zerodha.
-   **Async Performance**: Refactored to use `asyncio` and `aiohttp`, allowing **5x concurrent downloads** (fetching 5 stocks strictly respecting rate limits).
-   **Smart Resume**: The script automatically detects existing partial data and only fetches missing chunks.
-   **Format**: Data is saved as highly compressed **Parquet** files for blazing fast read speeds.

### Phase 2: Backtesting Engine (Alpha) ⚙️
-   **Vectorized Engine**: Built a custom engine (`BacktestEngine`) logic using `Polars` handling entire columns of data at once (vs row-by-row iteration).
-   **DataLoader**: Efficiently lazy-loads multiple parquet files into a single unified timeline.
-   **Strategy Interface**: created a clean `Strategy` base class for implementing logic.
-   **Proof of Concept**: Implemented `SMACrossover` (50/200) strategy and verified it against real data (`AARTIIND`), producing a correct Equity Curve.

## 3. Key Architectural Decisions

1.  **Polars vs Pandas vs Backtesting.py**:
    -   **Decision**: Custom Engine using **Polars**.
    -   **Reason**: `Backtesting.py` is excellent for single-stock testing but fails at **Portfolio-level simulation** (testing 9000 stocks at once). Polars provides multi-threaded performance necessary for this scale.

2.  **Parquet Storage**:
    -   **Decision**: Store data as individual `.parquet` files per stock.
    -   **Reason**: Faster IO than CSV, smaller disk footprint, and supports "Lazy Loading" (only reading columns we need).

3.  **Visualization Stack**:
    -   **Decision**: **TradingView Lightweight Charts** (React).
    -   **Reason**: We need professional-grade, zoomable, interactive financial charts. Python static plots (Matplotlib/Bokeh) are insufficient for deep analysis.

## 4. Current Status & Next Steps

### In Progress 🚧
-   **Strategy Expansion**: Expanding beyond SMA to include indicators like RSI, Bollinger Bands, and custom Multi-Timeframe logic.

### Roadmap (Upcoming) 🗺️

#### Phase 3: Frontend Visualization
-   Build a **FastAPI** backend to serve the backtest JSON results.
-   Build a **React** dashboard with TradingView charts to visualize the Equity Curve and Buy/Sell markers on index charts.

#### Phase 4: Portfolio Simulation
-   Enhance the engine to manage **Cash Constraints**.
-   Implement **Position Sizing** (e.g., "Allocate 5% equity per trade").

#### Phase 5: Live Trading Bridge
-   Connect the engine's signals to Zerodha Kite Connect for automated execution.

## 5. How to Run (Quick Ref)

**Fetch Data:**
```bash
# Fetch 50 stocks
python3 hermes-backend/data_seeder.py --all --limit 50
```

**Run Backtest:**
```bash
python3 hermes-backend/scripts/run_backtest.py --symbol AARTIIND
```
