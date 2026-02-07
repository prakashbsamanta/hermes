# 🚀 Getting Started with Hermes

This guide will help you set up and run Hermes on your local machine.

---

## Prerequisites

- **Python 3.12+** (backend)
- **Node.js 18+** (frontend)
- **PostgreSQL 16** (optional, for registry)
- **Podman** or **Docker** (optional, for containers)

---

## Quick Start (Development)

### 1. Clone the Repository

```bash
git clone https://github.com/prakashbsamanta/hermes.git
cd hermes
```

### 2. Set Up Backend

```bash
cd hermes-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install hermes-data package (from local)
pip install -e ../hermes-data

# Copy environment template
cp ../.env.example .env
# Edit .env if needed (e.g., data path)

# Start the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 3. Set Up Frontend

```bash
cd hermes-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/

# Expected response:
# {"status": "Hermes API is running"}
```

Open `http://localhost:5173` in your browser to see the dashboard.

---

## Quick Start (Containers)

If you prefer using containers:

```bash
# Start all services
podman-compose up -d

# Or with Docker
docker-compose -f podman-compose.yml up -d

# Check status
podman-compose ps
```

Services:
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **PostgreSQL**: localhost:5432

---

## Getting Data

Hermes requires OHLCV (minute-level) data in Parquet format. 

### Option 1: Use Sample Data

Sample data is included in `hermes-backend/data/minute/` for testing.

### Option 2: Fetch from Zerodha

If you have a Zerodha Kite account:

```bash
cd hermes-backend

# Set your Kite credentials in .env
export KITE_API_KEY="your_api_key"
export KITE_ACCESS_TOKEN="your_access_token"

# Fetch data for top 50 stocks
python data_seeder.py --all --limit 50
```

### Option 3: Use Your Own Data

Place Parquet files in `hermes-backend/data/minute/`:

```
hermes-backend/data/minute/
├── RELIANCE.parquet
├── TCS.parquet
├── INFY.parquet
└── ...
```

Required columns:
- `timestamp` (datetime)
- `open` (float)
- `high` (float)
- `low` (float)
- `close` (float)
- `volume` (int/float)

---

## Running Your First Backtest

### Via Dashboard

1. Open http://localhost:5173
2. Select a symbol (e.g., "RELIANCE")
3. Select a strategy (e.g., "RSIStrategy")
4. Adjust parameters if desired
5. Click **Run Backtest**
6. View the results chart and metrics

### Via API

```bash
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "strategy": "RSIStrategy",
    "params": {"period": 14}
  }'
```

### Via Python

```python
import requests

response = requests.post(
    "http://localhost:8000/backtest",
    json={
        "symbol": "RELIANCE",
        "strategy": "RSIStrategy",
        "params": {"period": 14, "oversold": 30, "overbought": 70},
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)

result = response.json()
print(f"Total Return: {result['metrics']['Total Return']}")
print(f"Sharpe Ratio: {result['metrics']['Sharpe Ratio']}")
```

---

## Available Strategies

| Strategy | Description |
|----------|-------------|
| `RSIStrategy` | Buy when RSI < 30, sell when RSI > 70 |
| `MACDStrategy` | Buy on MACD cross above signal, sell on cross below |
| `BollingerBandsStrategy` | Buy at lower band, sell at upper band |
| `SMACrossover` | Buy when fast SMA crosses above slow SMA |
| `MTFTrendFollowingStrategy` | Multi-timeframe trend following |

---

## Running Tests

```bash
# Run all quality checks
./run_checks.sh

# Backend tests only
cd hermes-backend
source venv/bin/activate
pytest --cov=. --cov-fail-under=90

# hermes-data tests only
cd hermes-data
pip install -e ".[test]"
pytest --cov=src/hermes_data --cov-fail-under=90

# Frontend tests only
cd hermes-frontend
npm run test:coverage
```

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Storage
HERMES_STORAGE_PROVIDER=local
HERMES_DATA_DIR=./data/minute

# Cache
HERMES_CACHE_ENABLED=true
HERMES_CACHE_MAX_SIZE_MB=512

# Registry (optional)
HERMES_REGISTRY_ENABLED=false
HERMES_DATABASE_URL=postgresql://hermes:password@localhost:5432/hermes
```

### Data Path

By default, Hermes looks for data in `hermes-backend/data/minute/`. Change this with:

```bash
export HERMES_DATA_DIR=/path/to/your/data
```

---

## Troubleshooting

### "No module named 'hermes_data'"

Make sure to install the hermes-data package:

```bash
cd hermes-backend
pip install -e ../hermes-data
```

### "Symbol not found"

Ensure you have data for the symbol:

```bash
ls hermes-backend/data/minute/
# Should show SYMBOL.parquet files
```

### Port already in use

```bash
# Kill existing process
lsof -i :8000 | grep LISTEN
kill -9 <PID>

# Or use a different port
uvicorn main:app --reload --port 8001
```

### Tests failing

```bash
# Ensure all dependencies installed
pip install -r requirements.txt
pip install pytest pytest-cov ruff mypy bandit pip-audit

# Run tests with verbose output
pytest -v
```

---

## Next Steps

1. **Explore Strategies**: Try different strategies and parameters
2. **Add Custom Data**: Download more instruments
3. **Read Architecture**: See [architecture.md](./architecture.md)
4. **Contribute**: Check [CONTRIBUTING.md](../CONTRIBUTING.md) (coming soon)

---

*Need help? Open an issue on GitHub!*
