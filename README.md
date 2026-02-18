# ⚡ Hermes Quantitative Engine

[![Typing SVG](https://readme-typing-svg.herokuapp.com?font=Fira+Code&pause=1000&color=2962FF&width=435&lines=Algo+Trading+Engine+for+India;Vectorized+Backtesting+in+Rust;Premium+Visualizations)](https://git.io/typing-svg)

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Polars-blue)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20Tailwind-cyan)
![Data](https://img.shields.io/badge/Data-PostgreSQL%20%7C%20Parquet%20%7C%20R2%20%7C%20OCI-orange)

**Hermes** is a high-performance, vectorized algorithmic trading engine designed for the Indian Stock Market. It combines the raw speed of **Rust-based Polars** for backtesting with a premium **React + Lightweight Charts** dashboard for visualization.

![Hermes Demo](demo.webp)

---

## 🚀 Features

- **⚡ Vectorized Engine**: Backtest years of minute-level data in milliseconds using `Polars`.
- **📊 Interactive Dashboard**: Professional-grade charts with Zoom/Pan, powered by TradingView's `Lightweight Charts`.
- **🛡️ Robust Data Guard**: Automatically filters corrupt/zero-price data to ensure test authenticity.
- **💾 Separated Data Layer**: Pluggable storage with caching and PostgreSQL registry.
- **🧠 Advanced Strategies**:
    - **MACD** (Moving Average Convergence Divergence) /w Signal Latching.
    - **Bollinger Bands** (Mean Reversion).
    - **RSI** (Momentum).
    - **Multi-Timeframe (MTF)**: Trade Minute charts based on Daily Trends.

---

## 🛠️ Architecture

```mermaid
graph TB
    subgraph Frontend
        A[React Dashboard]
    end
    
    subgraph Backend
        B[FastAPI Server]
        C[MarketDataService]
        D[BacktestService]
        K[ScannerService]
    end
    
    subgraph hermes-data
        E[DataService]
        F[LocalFileProvider]
        G[MemoryCache]
        H[RegistryService]
    end
    
    subgraph Storage
        I[(PostgreSQL)]
        J[(Parquet Files)]
    end
    
    A --> B
    B --> C --> E
    B --> D --> E
    B --> K --> E
    E --> F --> J
    E --> G
    E --> H --> I
```

---

## 🏁 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Podman** (or Docker) for containers
- **PostgreSQL 16** (can use containerized version)

### Project Structure

```
hermes/
├── data/               # Shared market data (parquet files)
│   ├── minute/         # Minute OHLCV data
│   ├── daily/          # Daily OHLCV data
│   └── instruments/    # Instrument master files
├── hermes-backend/     # FastAPI backend
├── hermes-frontend/    # React dashboard
├── hermes-data/        # Data access layer package
├── hermes-ingest/      # Data ingestion package
├── podman-compose.yml  # Container orchestration
└── docs/               # Documentation
```

---

## 🏁 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker** or **Podman** (for container mode)
- **PostgreSQL 16** (can use containerized version)

### 🚀 Quick Start (Recommended)

Use the unified startup script to run the application with real-time logs.

```bash
# Run with Containers (Default)
./start_hermes.sh

# Run locally (uses local venv and node)
./start_hermes.sh --mode local

# View logs with DEBUG level
./start_hermes.sh --level DEBUG
```

**Options:**
- `-m, --mode`: `container` (default) or `local`
- `-l, --level`: `INFO` (default), `DEBUG`, `WARNING`, `ERROR`
- `-b, --build`: Rebuild containers (container mode only)

---

## 💻 Manual Setup (Advanced)

If you prefer to run components individually without the script:

### Step 1: Start PostgreSQL

```bash
podman-compose up -d postgres
```

### Step 2: Setup hermes-data Package

```bash
cd hermes-data
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Step 3: Setup Backend

```bash
cd hermes-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Step 4: Setup Frontend

```bash
cd hermes-frontend
npm install
npm run dev
```

### Access Application

- **Dashboard**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## ⚙️ Configuration

All configuration is done via environment variables (or `.env` file).

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_STORAGE_PROVIDER` | `local` | Storage backend: `local`, `cloudflare_r2`, `oracle_object_storage` |
| `HERMES_DATA_DIR` | `data/minute` | Path to Parquet data files |
| `HERMES_SINK_TYPE` | `local` | Ingest sink: `local`, `cloudflare_r2`, `oracle_object_storage` |
| `HERMES_COMPRESSION` | `zstd` | Parquet compression: `zstd`, `snappy`, `lz4`, `gzip`, `uncompressed` |
| `HERMES_CACHE_ENABLED` | `true` | Enable in-memory caching |
| `HERMES_CACHE_MAX_SIZE_MB` | `512` | Maximum cache size in MB |
| `HERMES_DATABASE_URL` | `postgresql://...` | PostgreSQL connection |
| `HERMES_REGISTRY_ENABLED` | `true` | Enable data registry |

### Cloudflare R2 Settings (Optional)

| Variable | Description |
|----------|-------------|
| `HERMES_R2_ACCOUNT_ID` | Cloudflare account ID |
| `HERMES_R2_ACCESS_KEY_ID` | R2 API access key |
| `HERMES_R2_SECRET_ACCESS_KEY` | R2 API secret |
| `HERMES_R2_BUCKET_NAME` | R2 bucket name |

See [docs/CLOUDFLARE_R2_SETUP.md](docs/CLOUDFLARE_R2_SETUP.md) for complete setup guide.

### Oracle Cloud Object Storage Settings (Optional)

| Variable | Description |
|----------|-------------|
| `HERMES_OCI_NAMESPACE` | OCI tenancy namespace |
| `HERMES_OCI_REGION` | OCI region (e.g., `ap-hyderabad-1`) |
| `HERMES_OCI_ACCESS_KEY_ID` | Customer Secret Key access key |
| `HERMES_OCI_SECRET_ACCESS_KEY` | Customer Secret Key secret |
| `HERMES_OCI_BUCKET_NAME` | OCI bucket name |

See [docs/ORACLE_OBJECT_STORAGE_SETUP.md](docs/ORACLE_OBJECT_STORAGE_SETUP.md) for complete setup guide.

### Example .env file

```bash
# Storage
HERMES_STORAGE_PROVIDER=local
HERMES_DATA_DIR=data/minute
HERMES_SINK_TYPE=local
HERMES_SINK_PATH=data/minute

# S3/R2 Prefix (Default: "minute", leave empty for root)
# HERMES_S3_PREFIX=minute

# Cache
HERMES_CACHE_ENABLED=true
HERMES_CACHE_MAX_SIZE_MB=512

# Database
HERMES_DATABASE_URL=postgresql://hermes:hermes_secret@localhost:5432/hermes
HERMES_REGISTRY_ENABLED=true

# Cloudflare R2 (optional - uncomment for cloud storage)
# HERMES_SINK_TYPE=cloudflare_r2
# HERMES_R2_ACCOUNT_ID=your_account_id
# HERMES_R2_ACCESS_KEY_ID=your_access_key
# HERMES_R2_SECRET_ACCESS_KEY=your_secret_key
# HERMES_R2_BUCKET_NAME=hermes-market-data
```

## 🛠️ Logging & Diagnostics

Hermes includes a unified structured logging system with request tracing.

**Key Features:**
- **Correlation ID:** Every request is tagged with a `correlation_id` to trace flow across services.
- **JSON Logs:** Default format is JSON for easy parsing by tools like Datadog/ELK.
- **Middleware:** Automatically logs request duration and status codes.

To configure logging level:
```bash
LOG_LEVEL=DEBUG  # Default: INFO
```


---

## 📈 Strategies

| Strategy | Type | Logic |
| :--- | :--- | :--- |
| **SMA Crossover** | Trend | Buy when Fast SMA > Slow SMA. |
| **RSI** | Momentum | Buy < 30 (Oversold), Sell > 70 (Overbought). |
| **Bollinger Bands** | Mean Reversion | Buy when price breaks Lower Band. |
| **MACD** | Momentum/Trend | Buy on MACD > Signal Line crossover. |
| **MTF Trend** | **Hybrid** | Only take RSI Buy signals if **Daily Trend** is Bullish (SMA50 > SMA200). |

---

## 🖥️ API Reference

### Health Check
```bash
GET /
# Returns: {"status": "Hermes API is running"}
```

### List Instruments
```bash
GET /instruments
# Returns: ["AARTIIND", "ABB", "RELIANCE", ...]
```

### Get Market Data
```bash
GET /data/{symbol}?timeframe=1h
# Returns: {symbol, candles: [...]}
```

### Run Backtest
```bash
POST /backtest
Content-Type: application/json

{
  "symbol": "AARTIIND",
  "strategy": "RSIStrategy",
  "params": {
    "period": 14,
    "overbought": 70
  },
  "initial_cash": 100000
}

# Returns: {equity_curve, signals, metrics, candles}
```

---

## 🧪 Running Tests & Quality Gates

### 🛡️ The Guardian (All-in-One Check)

Running the centralized quality gate script is the most reliable way to verify the entire project. This script runs linting, type checking, security scans, and tests (with coverage thresholds) for all packages.

```bash
# From the project root
./run_checks.sh
```

### Manual Individual Tests

```bash
# hermes-ingest tests
cd hermes-ingest && source venv/bin/activate && pytest tests/ -v --cov

# hermes-data tests
cd hermes-data && source .venv/bin/activate && pytest tests/ -v

# hermes-backend tests
cd hermes-backend && source venv/bin/activate && pytest tests/ -v --cov
```

### Test Coverage

```bash
cd hermes-backend
pytest tests/ -v --cov --cov-report=html
open htmlcov/index.html
```

### Fetch New Data

```bash
cd hermes-ingest && source venv/bin/activate
hermes-ingest sync --limit 50 --concurrency 5
```

---

## 🛡️ Data Guard

Hermes includes a robust **Data Guard** layer that:
1. Drops rows where `Price <= 0`.
2. Fills `NaN` values in calculations to prevent `Infinity` returns.
3. Ensures `Signal` states are latched (held) correctly to simulate real positions.

---

## 📦 Package Structure

### hermes-ingest

Data ingestion package providing:

- **DataSource** - Abstract interface for broker data
- **ZerodhaSource** - Zerodha Kite data provider
- **DataSink** - Abstract interface with centralized compression, merge/dedup
- **LocalFileSink** - Write Parquet to local disk
- **CloudflareR2Sink** - Write Parquet to Cloudflare R2
- **OracleObjectStorageSink** - Write Parquet to Oracle OCI
- **create_sink()** - Factory for easy switching

```python
from hermes_ingest.sinks import create_sink

sink = create_sink()  # Auto-creates based on HERMES_SINK_TYPE
sink.write("RELIANCE", df)
```

### hermes-data

The separated data layer provides:

- **DataProvider** - Abstract interface for pluggable storage
- **LocalFileProvider** - Reads Parquet files from disk
- **MemoryCache** - LRU cache with size limits
- **DataService** - Unified facade for data access
- **RegistryService** - PostgreSQL-backed metadata catalog

```python
from hermes_data import DataService

service = DataService()
df = service.get_market_data(["RELIANCE"], "2024-01-01", "2024-12-31")
symbols = service.list_instruments()
```

---

## 🔮 Roadmap

- [x] **Cloudflare R2** - Cloud storage with zero egress fees
- [x] **Oracle OCI** - Cloud storage with generous free tier
- [x] **zstd Compression** - Configurable Parquet compression
- [x] **Scanner/Screener** - Batch strategy execution across all stocks
- [ ] **AWS S3 Provider** - Load data from AWS S3
- [ ] **Redis Cache** - Distributed caching for multi-instance deployments
- [ ] **Live Trading** - Connect to broker APIs
- [ ] **Strategy Builder** - No-code strategy creation

---

## 📅 Database Access

You can access the PostgreSQL registry database in two ways:

### 1. Command Line (via Container)

```bash
# Connect to psql shell inside the container
podman exec -it hermes-postgres psql -U hermes -d hermes

# List tables
\dt

# Query instruments
SELECT * FROM instruments;
```

### 2. GUI Clients (DBeaver, TablePlus, PgAdmin)

- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `hermes`
- **User**: `hermes`
- **Password**: `hermes_secret`
- **URL**: `postgresql://hermes:hermes_secret@localhost:5432/hermes`

---

## 📝 Development Log

See `docs/development_progress.log` for detailed development history.

---

*Built with ❤️ by The Forge.*
