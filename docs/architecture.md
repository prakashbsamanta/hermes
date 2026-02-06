# Architecture Guidelines

## Core Architectural Paradigms

### 1. Event-Driven Architecture (EDA)
**"Everything is an Event."**
- The core engine (when not in "fast vector mode") must operate as an event loop interacting with an Event Bus.
- Key Events: `MarketEvent` (Price Update), `SignalEvent` (Strategy Logic), `OrderEvent` (Execution Request), `FillEvent` (Trade Confirmation).
- Services should be loosely coupled consumers of these events.

### 2. Hexagonal Architecture (Ports & Adapters)
**"Protect the Domain."**
- **Domain Layer**: Pure business logic (Strategy, PositionMgmt, Risk). NO external dependencies (no API calls, no database imports).
- **Ports**: Interfaces defined by the Domain (e.g., `DataFeedPort`, `ExecutionHandlerPort`).
- **Adapters**: Implementations that talk to the outside world (e.g., `InteractiveBrokersAdapter`, `CSVDataLoader`, `PolarsBacktestAdapter`).
- **Rule**: The Strategy should never know if it's backtesting or trading live.

### 3. Functional Core, Imperative Shell
**"Make logic testable."**
- **Core Logic**: Use pure functions where possible, especially for calculations (Indicators, Sizing).
    - *Good*: `calculate_rsi(prices: List[float]) -> float`
    - *Bad*: `self.calculate_rsi()` (modifying internal state unpredictably)
- **Immutability**: Prefer immutable data structures for passing data between services.
- **Polars**: Continue using Polars for vectorized backtesting, treating DataFrames as immutable transformation pipelines.
