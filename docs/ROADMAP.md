# 🗺️ Hermes Project Roadmap

**Mission**: Build a high-performance, institutional-grade algorithmic trading engine for the Indian Markets (NSE), capable of backtesting 9000+ instruments in seconds with eventual live trading capability.

**Last Updated**: 2026-02-15

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           HERMES ROADMAP                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ Phase 1     ✅ Phase 2     ✅ Phase 3     🚧 Phase 4     🔮 Phase 5     │
│  ─────────     ─────────     ─────────     ─────────     ─────────         │
│   Genesis      Fortify       Visual        Scanner       Reality           │
│   (Data)       (Quality)     (Dashboard)   (Batch)       (Simulation)      │
│     │             │             │             │             │               │
│     ▼             ▼             ▼             ▼             ▼               │
│  ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐ │
│  │ Jan │──────│ Feb │──────│ Mar │──────│ Apr │──────│ May │──────│ Jun │ │
│  │ 26  │      │ 26  │      │ 26  │      │ 26  │      │ 26  │      │ 26  │ │
│  └─────┘      └─────┘      └─────┘      └─────┘      └─────┘      └─────┘ │
│                                                                             │
│                                                        🔮 Phase 6           │
│                                                        ─────────           │
│                                                        Live Trading         │
│                                                        (Q3-Q4 2026)         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Phase 1: Genesis (The Foundation)

**Status**: ✅ **COMPLETED**  
**Timeline**: January 2026  
**Focus**: Data Infrastructure & Core Engine

### Deliverables

- [x] **Data Seeder**: AsyncIO downloader for Zerodha (Kite) data
  - 5x concurrent downloads with rate limiting
  - Smart resume for interrupted downloads
  - Automatic chunk detection for missing data

- [x] **Storage Layer**: High-performance Parquet file system
  - Individual files per instrument (`data/minute/RELIANCE.parquet`)
  - Columnar format for fast analytical queries
  - zstd compression (~70% vs CSV)

- [x] **Vectorized Engine**: Custom Polars-based backtesting engine
  - `BacktestEngine` class for high-speed simulations
  - Equity curve calculation with cumulative product
  - Signal-to-position shift to avoid look-ahead bias

- [x] **Basic Strategies**: Core strategy implementations
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - SMA Crossover

- [x] **API Layer**: FastAPI backend
  - `/backtest` endpoint for running simulations
  - `/instruments` endpoint for available symbols
  - `/data/{symbol}` endpoint for raw OHLCV data

---

## ✅ Phase 2: Fortification (Reliability)

**Status**: ✅ **COMPLETED**  
**Timeline**: February 2026  
**Focus**: Code Quality, Testing, & Compliance

### Deliverables

- [x] **CI/CD Pipeline**: GitHub Actions workflow
  - Backend: Ruff, Mypy, Bandit, pip-audit, pytest
  - Frontend: ESLint, Prettier, TypeScript, npm audit, Vitest
  - Coverage thresholds enforced at 90%

- [x] **Test Suite**: Comprehensive unit testing
  - Backend: 31 tests, 96% coverage
  - hermes-data: 79 tests, 92% coverage
  - hermes-ingest: 100 tests, 91% coverage
  - Frontend: 26 tests, 91% coverage

- [x] **Data Guard**: Strict validation
  - OHLC price relationship validation
  - Zero/negative price rejection
  - Missing data gap detection

- [x] **Strict Typing**: Full type coverage
  - Mypy for Python (backend + hermes-data)
  - TypeScript strict mode (frontend)

- [x] **Local Enforcement**: Pre-push hooks
  - `run_checks.sh` quality gate script
  - Blocks commits that fail any check
  - Parallel execution for speed

- [x] **hermes-data Package**: Reusable data layer
  - DataService facade for unified access
  - Provider abstraction (Local, future: S3, GCS)
  - MemoryCache with LRU eviction
  - PostgreSQL registry for metadata

- [x] **hermes-ingest Package**: Production-grade data ingestion
  - ZerodhaSource with rate limiting & async chunks
  - 3 storage sinks: Local, Cloudflare R2, Oracle OCI
  - DataSink base class with centralized compression, merge/dedup
  - Rich CLI with real-time progress bars & candle counts
  - Factory pattern for seamless sink switching

---

## ✅ Phase 3: Visual Insight (The Dashboard)

**Status**: ✅ **COMPLETED**  
**Timeline**: February 2026  
**Focus**: Making data visible and debuggable

### Deliverables

- [x] **Candlestick Charts**: Professional OHLCV visualization
  - TradingView Lightweight Charts integration
  - Responsive, zoomable, pannable
  - Crosshair with price/time display

- [x] **Signal Markers**: Buy/sell visualization
  - Arrow markers on chart
  - Color-coded (green=buy, red=sell)
  - Hover tooltips with signal details

- [x] **Strategy Controls**: Interactive configuration
  - Dynamic parameter panels per strategy
  - Slider and numeric inputs
  - Real-time parameter updates

- [x] **Backtest Results**: Metrics dashboard
  - Total Return percentage
  - Final Equity value
  - Sharpe Ratio
  - Maximum Drawdown

- [x] **Mode Selection**: Vector vs Event
  - Toggle between fast/realistic modes
  - Date range filtering
  - Slippage/commission inputs

### Remaining Items (Deferred to Phase 4)

- [ ] **Indicator Overlays**: Plot RSI line, Bollinger bands on chart
- [ ] **Visual Debugging**: Hover over candle to see signal context
- [ ] **Multi-Chart Layout**: Stacked view (Price + RSI subcharts)

---

## 🚧 Phase 4: The Scanner (Market Breadth)

**Status**: 🚧 **IN PROGRESS**  
**Timeline**: March 2026  
**Focus**: Running strategies on *all* stocks, not just one

### Planned Deliverables

- [ ] **Batch Engine**: Parallel strategy execution
  - `ScannerService` — run any strategy on N tickers concurrently
  - `/scan` REST endpoint with async processing
  - Progress tracking via WebSocket (or SSE)
  - Memory-efficient streaming results

- [ ] **Screener Page**: Top signals UI
  - Sortable table of buy/sell signals
  - Filter by sector, exchange, signal type
  - Click to drill down into backtest

- [ ] **Performance Heatmap**: Strategy comparison
  - Sector-level aggregation
  - Color gradient for returns
  - Interactive drill-down

- [ ] **Indicator Overlays**: Chart enhancements
  - RSI line overlay
  - Bollinger bands overlay
  - MACD histogram

- [ ] **API Improvements**
  - `/scan` endpoint for batch processing
  - Pagination for large result sets
  - WebSocket for progress updates

---

## 🔮 Phase 5: Reality (Simulation)

**Status**: 📅 **PLANNED**  
**Timeline**: April-May 2026  
**Focus**: Real-world constraints (Cash, Fees, Slippage)

### Planned Deliverables

- [ ] **Wallet Management**: Finite cash constraints
- [ ] **Advanced Slippage**: Volume-based market impact modeling
- [ ] **Position Sizing**: Risk management (Fixed fractional, Kelly, ATR)
- [ ] **Walk-Forward Optimization**: Rolling window out-of-sample testing
- [ ] **Monte Carlo Simulation**: Robustness testing with confidence intervals

---

## 🔮 Phase 6: Live Executive (The Bridge)

**Status**: 📅 **PLANNED (LONG TERM)**  
**Timeline**: Q3-Q4 2026  
**Focus**: Connecting to Broker APIs for real trading

### Planned Deliverables

- [ ] **Broker Bridge**: Zerodha Kite Connect
- [ ] **Paper Trading**: Forward testing with simulated execution
- [ ] **Live Execution**: Strategy → Signal → Order pipeline
- [ ] **Multi-Broker Support**: Shoonya, Angel Broking

---

## 🛠️ Infrastructure Roadmap

### Near Term (Q1 2026)

- [x] GitHub Actions CI/CD
- [x] Podman/Docker containers
- [x] PostgreSQL metadata registry
- [x] Pre-commit quality hooks
- [x] Multi-cloud storage sinks (R2 + OCI)
- [x] zstd Parquet compression
- [ ] Swagger/OpenAPI documentation

### Medium Term (Q2 2026)

- [ ] Redis distributed cache
- [ ] S3/GCS data providers
- [ ] Kubernetes deployment
- [ ] Prometheus metrics
- [ ] Grafana dashboards

### Long Term (H2 2026)

- [ ] Multi-region deployment
- [ ] Auto-scaling workers
- [ ] Feature flags
- [ ] A/B testing framework
- [ ] Disaster recovery

---

## 📊 Success Metrics

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Backtest Speed (1 symbol) | 200ms | <100ms | Q2 2026 |
| Batch Scan (100 symbols) | N/A | <10s | Q1 2026 |
| Test Coverage (avg) | 91%+ | ≥95% | Ongoing |
| Data Freshness | Manual | T+1 auto | Q2 2026 |
| Uptime (Production) | N/A | 99.9% | Q3 2026 |

---

## 🔗 Related Documents

- [Architecture Documentation](./architecture.md) - System design and data flows
- [Project Status](./project_status.md) - Current state and recent changes
- [Development Log](./development_progress.log) - Detailed changelog
- [AI Coder Instructions](./AI_CODER_INSTRUCTIONS.md) - Guidelines for AI assistants
- [Getting Started](./GETTING_STARTED.md) - Setup and onboarding guide
- [Cloudflare R2 Setup](./CLOUDFLARE_R2_SETUP.md) - Cloud storage configuration
- [Oracle OCI Setup](./ORACLE_OBJECT_STORAGE_SETUP.md) - Oracle cloud configuration

---

*Version: 3.0*  
*Last Updated: 2026-02-15*
