# ⚡ Hermes Quantitative Engine

![Hermes Dashboard](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Polars-blue)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20Tailwind-cyan)

**Hermes** is a high-performance, vectorized algorithmic trading engine designed for the Indian Stock Market. It combines the raw speed of **Rust-based Polars** for backtesting with a premium **React + Lightweight Charts** dashboard for visualization.

---

## 🚀 Features

- **⚡ Vectorized Engine**: Backtest years of minute-level data in milliseconds using `Polars`.
- **📊 Interactive Dashboard**: Professional-grade charts with Zoom/Pan, powered by TradingView's `Lightweight Charts`.
- **🛡️ Robust Data Guard**: Automatically filters corrupt/zero-price data to ensure test authenticity.
- **🧠 Advanced Strategies**:
    - **MACD** (Moving Average Convergence Divergence) /w Signal Latching.
    - **Boliinger Bands** (Mean Reversion).
    - **RSI** (Momentum).
    - **Multi-Timeframe (MTF)**: Trade Minute charts based on Daily Trends.

---

## 🛠️ Architecture

```mermaid
graph LR
    A[Data Source (Parquet)] --> B(Polars Loader);
    B --> C{Backtest Engine};
    D[Strategies] --> C;
    C --> E[FastAPI Server];
    E --> F[React Dashboard];
    F --> G[End User];
```

---

## 🏁 Get Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Clone & Setup Backend
```bash
# Clone repository
git clone https://github.com/yourusername/hermes.git
cd hermes

# Create Virtual Environment
python3 -m venv hermes-backend/venv
source hermes-backend/venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
# (OR manually: pip install polars fastapi uvicorn pandas requests)
```

### 2. Run the API Server
```bash
# From project root
hermes-backend/venv/bin/uvicorn hermes-backend.main:app --reload --port 8000
```
> API is now live at `http://localhost:8000`

### 3. Setup & Run Frontend
```bash
# Open new terminal
cd hermes-frontend

# Install Node Modules
npm install

# Start Dev Server
npm run dev
```
> Dashboard is now live at `http://localhost:5173` (or 5175 if busy)

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

### `POST /backtest`
Run a simulation on historical data.

**Payload:**
```json
{
  "symbol": "AARTIIND",
  "strategy": "RSIStrategy",
  "params": {
    "period": 14,
    "overbought": 70
  },
  "initial_cash": 100000
}
```

**Response:**
Returns `equity_curve` (time-series), `signals` (buy/sell markers), and `metrics` (Sharpe, Drawdown).

---

## 🛡️ Robustness

Hermes includes a **Data Guard** layer that:
1.  Drops rows where `Price <= 0`.
2.  Fills `NaN` values in calculations to prevent `Infinity` returns.
3.  Ensures `Signal` states are latched (Held) correctly to simulate real positions.

---

*Built with ❤️ by The Forge.*
