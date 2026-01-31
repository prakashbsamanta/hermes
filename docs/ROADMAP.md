# 🗺️ Hermes Project Roadmap

**Mission**: Build a high-performance, institutional-grade algorithmic trading engine for the Indian Markets (NSE), capable of backtesting 9000+ instruments in seconds.

---

## ✅ Phase 1: Genesis (The Foundation)
**Status**: Completed
**Focus**: Data Infrastructure & Core Engine

- [x] **Data Seeder**: AsyncIO downloader for Zerodha (Kite) data.
- [x] **Storage**: High-performance Parquet file system (`data/minute/`).
- [x] **Vectorized Engine**: Custom Polars-based backtesting engine.
- [x] **Basic Strategies**: Implementation of RSI, MACD, Bollinger Bands, SMA.
- [x] **API**: FastAPI backend to serve results.

## ✅ Phase 2: Fortification (Reliability)
**Status**: Completed
**Focus**: Code Quality, Testing, & Compliance

- [x] **CI/CD Pipeline**: GitHub Actions for automated integrity checks.
- [x] **Test Suite**: >95% Unit Test Coverage (`pytest`).
- [x] **Data Guard**: Strict validation to reject corrupt OHLC data.
- [x] **Strict Typing**: Mypy (Backend) & TypeScript (Frontend) compliance.
- [x] **Local Enforcement**: Pre-push hooks to prevent bad code commits.

---

## 🚧 Phase 3: Visual Insight (The Dashboard)
**Status**: **Use this phase now?**
**Focus**: Making the data visible and debuggable.

*Currently, we only show an Equity Curve. We cannot "see" the trade context.*

- [ ] **Candlestick Charts**: Render actual OHLCV data on the frontend.
- [ ] **Indicator Overlays**: Plot the computed indicators (e.g., RSI line, Bollinger Bands) directly on the chart.
- [ ] **Visual Debugging**: Hover over a candle to see why a signal fired (or didn't).
- [ ] **Multi-Chart Layout**: Stacked view (Price on top, RSI below).

---

## 🔮 Phase 4: The Scanner (Market Breadth)
**Status**: Planned
**Focus**: Running strategies on *all* stocks, not just one.

- [ ] **Batch Engine**: Logic to run `RSIStrategy` on 50+ tickers in parallel.
- [ ] **Screener UI**: A table view showing "Top Buy Signals" for the day.
- [ ] **Performance Heatmap**: Compare strategies across sectors.

---

## 🔮 Phase 5: Reality (Simulation)
**Status**: Planned (Deferred)
**Focus**: Real-world constraints (Cash, Fees, Slippage).

- [ ] **Wallet Logic**: Finite cash management.
- [ ] **Transaction Costs**: Commission & Slippage simulation.
- [ ] **Position Sizing**: Risk management logic (e.g., "1% Risk per trade").

---

## 🔮 Phase 6: Live Executive (The Bridge)
**Status**: Long Term
**Focus**: Connecting to Broker APIs.

- [ ] **Broker Bridge**: Kite Connect / Shoonya API integration.
- [ ] **Paper Trading**: Forward testing in real-time.
- [ ] **Live Execution**: Real money automated trading.
