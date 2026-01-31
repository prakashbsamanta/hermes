# 🤖 AI Coder Constitution: Project Hermes

**Version**: 2.0
**Mission**: Build a High-Frequency, Vectorized Algorithmic Trading Engine with Institutional-Grade Quality.

This document serves as the supreme law for this project. All contributors (AI and Human) must adhere to these principles to maintain integrity, speed, and elegance.

---

## 1. 🏛️ Core Philosophy & Architecture

### **Scalability First**
*   **Vectorization is King**: The engine is built on `Polars` (Rust). **NEVER** use Python loops for data processing. All operations must be vectorized (O(1) or O(N) optimized).
*   **Lazy Evaluation**: Use `LazyFrame` scanning (`.scan_parquet()`) for large datasets. Materialize (`.collect()`) only when necessary.
*   **Async By Design**: The API layer (`FastAPI`) must remain non-blocking. Heavy computations should offload to worker threads or separate processes if they exceed 500ms.

### **Authentication & Truth**
*   **Point-in-Time Correctness**: Strictly prevent **Lookahead Bias**. Strategies must only access data available at time `T` to make decisions for `T+1`.
*   **Data Integrity**: Inputs are guilty until proven innocent. The `Data Guard` (Sanitizer) must validate all OHLCV data for:
    *   Zero/Negative prices.
    *   Missing candles (Gaps).
    *   Impossible moves (High < Low).
*   **Precision Matters**: Be aware of floating-point drifts. When dealing with currency or strict accounting, treat numbers carefully. For vectorized performance, `float64` is acceptable for backtesting, but execution logic needs strict checks.

---

## 2. 💻 Coding Standards & Best Practices

### **Python (Backend)**
*   **Type Safety**: 100% Type Hints are mandatory. Use `mypy` or `pyright` standards.
    *   *Bad*: `def calculate(df):`
    *   *Good*: `def calculate(df: pl.DataFrame) -> pl.DataFrame:`
*   **Modern Features**: Use Python 3.10+ features (e.g., `match/case`, union types `X | Y`).
*   **DRY & SOLID**: Extract reusable logic into utility modules (`hermes-backend/utils`). Do not duplicate signal logic across strategies.
*   **Docstrings**: All public functions/classes must have Google-style docstrings explaining *Args*, *Returns*, and *Raises*.

### **TypeScript/React (Frontend)**
*   **Strict Mode**: No `any` types. Define Interfaces for all API responses and Props.
*   **Functional Components**: Use Hooks (`useBacktest`, `useMarketData`) to separate Logic from View.
*   **Atomic Design**: Small, single-responsibility components (`MetricCard`, `ChartComponent`).
*   **State Management**: Use `TanStack Query` for server state. Avoid Redux unless local complex state demands it.

---

## 3. 🎨 Visual Design & Experience

*   **Premium Aesthetic**: The UI must feel expensive.
    *   **Dark Mode Only**: Deep Slate/Navy backgrounds (`bg-slate-950`), not pure black.
    *   **Glassmorphism**: Use backdrops (`backdrop-blur-md`, `bg-white/5`) for depth.
    *   **Neon Accents**: Use high-contrast colors (Cyan `#00E5FF`, Emerald `#10B981`) sparingly for data points.
*   **Alive Interface**:
    *   **Feedback**: Buttons must react (scale/lighten) on hover/click.
    *   **Transitions**: Elements should not "pop" into existence; they should fade/slide in (`framer-motion`).
    *   **Data Vis**: Numbers should count up. Charts should use smooth/area fills.

---

## 4. 🔒 Security & Production Readiness

*   **Secrets Management**: **NEVER** hardcode API Keys, Passwords, or Tokens. Use `.env` files and `pydantic-settings`.
*   **Input Sanitization**: Validate all API inputs using Pydantic Models. Assume the user will send strings where numbers belong.
*   **Error Handling**:
    *   **Backend**: Catch specific exceptions and return standard HTTP error codes (400, 404, 500). **Never** leak raw stack traces to the frontend in production.
    *   **Frontend**: Use Error Boundaries. If the Chart crashes, the Navigation bar should still work.
*   **Dependency Management**: Lock versions in `requirements.txt` / `package.json` to prevent "it works on my machine" issues.

---

## 5. ⚙️ Automatability & QA

*   **Testing**:
    *   **Unit Tests**: Test strategy logic with deterministic mock data.
    *   **Integration Tests**: Test the full API flow (`/backtest`) with known inputs.
*   **Linting**: Use `ruff` (Python) and `eslint` (JS) to enforce standard formatting automatically.
*   **Logging**: Use structured logging (JSON preferred for prod). Log *events* ("Strategy Started"), not just noise.
*   **Coverage**: Maintain **>90%** global code coverage.
    *   **CI Enforcement**: The GitHub Actions pipeline will fail if checks are not met.
    *   **Local Enforcement**: A git `pre-push` hook is installed to prevent pushing if tests or coverage fail locally.

---

## 6. 🚫 Critical "NEVER" Rules (Immediate Fail)

1.  **Iterative Processing**: Writing a `for` loop to iterate over millions of candles is strictly forbidden. Use Vectorization.
2.  **Generic Styling**: Using default browser inputs or raw HTML tables without styling.
3.  **Hardcoded Paths**: Do not assume files are at `/home/user/code`. Use `pathlib` for relative paths.
4.  **Silent Failures**: Implementing `try: ... except: pass`. Always log the error.

---

## 7. 🧠 Efficiency & Algorithms

*   **Time Complexity**: Be mindful of Big O. Rolling window calculations should use Polars' optimized `rolling_*` kernels.
*   **Memory Efficiency**: Drop unused columns early (`lazy.select(...)`). Do not load entire datasets into RAM if only a slice is needed.
*   **Caching**: Cache heavy results (like loaded Parquet files) in memory if accessed frequently (`lru_cache`).

---
**Adhere to this Constitution, and we will build a legacy.**
