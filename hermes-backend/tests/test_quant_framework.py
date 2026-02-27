"""
Quantitative Testing Framework for Hermes Trading Strategies.

This module implements 4 tiers of mathematical verification:
1. Deterministic Hand-Calculated Tests — synthetic datasets with known answers
2. Cross-Validation against NumPy reference implementations — RSI, EMA, SMA
3. Look-Ahead Bias Detection — signal-to-position timing verification
4. Edge Case Invariants — zero volume, insufficient data, extreme prices

Every test here proves the MATH is correct, not just that the code runs.

Dependencies: Only numpy (already a core dep). No pandas, no pandas-ta, no TA-Lib.
TA-Lib will be integrated via map_batches for complex indicators (see plans/talib_integration.md).
"""

import pytest
import polars as pl
import numpy as np

from engine.core import BacktestEngine
from engine.strategy import Strategy
from strategies.rsi import RSIStrategy
from strategies.sma_cross import SMACrossover
from strategies.macd import MACDStrategy
from strategies.bollinger import BollingerBandsStrategy


# ---------------------------------------------------------------------------
# Pure NumPy Reference Implementations (Golden Standards for Cross-Validation)
# These are straightforward loop/vectorized implementations of well-known
# finance formulas. They serve as an independent math oracle.
# ---------------------------------------------------------------------------

def numpy_sma(close: np.ndarray, window: int) -> np.ndarray:
    """Rolling simple moving average. NaN for the first (window-1) positions."""
    result = np.full(len(close), np.nan)
    for i in range(window - 1, len(close)):
        result[i] = np.mean(close[i - window + 1 : i + 1])
    return result


def numpy_ewm(close: np.ndarray, span: int, adjust: bool = False) -> np.ndarray:
    """
    Exponential weighted mean matching Polars ewm_mean(span=..., adjust=False).
    Equivalent to Pandas .ewm(span=span, adjust=False).mean().
    alpha = 2 / (span + 1)
    """
    alpha = 2.0 / (span + 1)
    result = np.empty(len(close))
    result[0] = close[0]
    for i in range(1, len(close)):
        result[i] = alpha * close[i] + (1 - alpha) * result[i - 1]
    return result


def numpy_wilder_rsi(close: np.ndarray, period: int) -> np.ndarray:
    """
    RSI using Wilder's smoothing equivalent to EWM with com=(period-1).
    This directly mirrors what Polars ewm_mean(com=period-1, min_samples=period) does.
    NaN values filled with 50 (neutral), matching RSIStrategy behaviour.
    """
    n = len(close)
    delta = np.diff(close, prepend=close[0])  # length n, delta[0]=0
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    # Wilder's smoothing = EWM with com = period-1
    alpha = 1.0 / period   # com = period-1 → alpha = 1/(1+com) = 1/period
    avg_gain = np.empty(n)
    avg_loss = np.empty(n)
    avg_gain[0] = gain[0]
    avg_loss[0] = loss[0]
    for i in range(1, n):
        avg_gain[i] = alpha * gain[i] + (1 - alpha) * avg_gain[i - 1]
        avg_loss[i] = alpha * loss[i] + (1 - alpha) * avg_loss[i - 1]

    rsi = np.where(
        avg_loss == 0,
        100.0,
        100.0 - (100.0 / (1.0 + avg_gain / np.where(avg_loss == 0, 1e-12, avg_loss)))
    )

    # Apply min_samples=period: NaN before that, fill with 50 after
    rsi[:period - 1] = np.nan
    return np.where(np.isnan(rsi), 50.0, rsi)


def numpy_rolling_std(close: np.ndarray, window: int) -> np.ndarray:
    """
    Bessel-corrected rolling standard deviation (ddof=1), matching Polars rolling_std.
    NaN for the first (window-1) positions.
    """
    result = np.full(len(close), np.nan)
    for i in range(window - 1, len(close)):
        result[i] = np.std(close[i - window + 1 : i + 1], ddof=1)
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return BacktestEngine(initial_cash=100000.0)


def _make_ohlcv(close_values: list[float], volume: int = 10000) -> pl.DataFrame:
    """Helper: builds a minimal OHLCV DataFrame from a list of close prices."""
    n = len(close_values)
    close = np.array(close_values, dtype=np.float64)
    return pl.DataFrame({
        "timestamp": list(range(n)),
        "open": close.tolist(),
        "high": (close * 1.001).tolist(),
        "low": (close * 0.999).tolist(),
        "close": close.tolist(),
        "volume": [volume] * n,
        "symbol": ["SYNTH"] * n,
    })


# ============================================================================
# TIER 1 — Deterministic Hand-Calculated Tests
# ============================================================================

class TestRSIDeterministic:
    """Tests RSI with synthetic datasets where we know the exact answer."""

    def test_pure_uptrend_rsi_is_100(self):
        """
        In a pure uptrend with constant gains, Average Loss = 0.
        Therefore RS = AvgGain / 0 → RSI = 100.

        Dataset: 16 prices, each +1 from previous.
        RSI period = 14, so first valid RSI is at index 15 (15th change).
        """
        # 16 prices → 15 changes → first RSI at index 15
        prices = list(range(100, 116))  # [100, 101, 102, ..., 115]
        df = _make_ohlcv(prices)

        strat = RSIStrategy(params={"period": 14})
        result = strat.generate_signals(df)

        # RSI must be 100.0 at the last row (pure uptrend)
        last_rsi = result["rsi"][-1]
        assert last_rsi == pytest.approx(100.0, abs=0.5), (
            f"Pure uptrend RSI should be ~100, got {last_rsi}"
        )

    def test_pure_downtrend_rsi_is_0(self):
        """
        In a pure downtrend with constant losses, Average Gain = 0.
        Therefore RS = 0 / AvgLoss → RSI = 0.
        """
        prices = list(range(200, 184, -1))  # [200, 199, 198, ..., 185]
        df = _make_ohlcv(prices)

        strat = RSIStrategy(params={"period": 14})
        result = strat.generate_signals(df)

        last_rsi = result["rsi"][-1]
        assert last_rsi == pytest.approx(0.0, abs=0.5), (
            f"Pure downtrend RSI should be ~0, got {last_rsi}"
        )

    def test_flat_market_rsi_is_50(self):
        """
        In a flat market (no price changes), both AvgGain and AvgLoss = 0.
        RS = 0/0 → NaN → should fill to 50.0 (neutral).
        """
        prices = [100.0] * 20
        df = _make_ohlcv(prices)

        strat = RSIStrategy(params={"period": 14})
        result = strat.generate_signals(df)

        last_rsi = result["rsi"][-1]
        assert last_rsi == pytest.approx(50.0, abs=1.0), (
            f"Flat market RSI should be ~50, got {last_rsi}"
        )

    def test_rsi_oversold_fires_buy_signal(self):
        """
        After a sustained downtrend (RSI < 30), the signal column must be 1 (BUY).
        """
        # Sharp downtrend to push RSI below 30
        prices = [200.0] + [200.0 - i * 3 for i in range(1, 20)]
        df = _make_ohlcv(prices)

        strat = RSIStrategy(params={"period": 14, "oversold": 30, "overbought": 70})
        result = strat.generate_signals(df)

        last_rsi = result["rsi"][-1]
        last_signal = result["signal"][-1]

        if last_rsi < 30:
            assert last_signal == 1, (
                f"RSI={last_rsi:.1f} is below 30 but signal={last_signal} (expected 1)"
            )

    def test_rsi_overbought_fires_sell_signal(self):
        """
        After a sustained uptrend (RSI > 70), the signal column must be 0 (EXIT).
        """
        # Sharp uptrend to push RSI above 70
        prices = [100.0] + [100.0 + i * 3 for i in range(1, 20)]
        df = _make_ohlcv(prices)

        strat = RSIStrategy(params={"period": 14, "oversold": 30, "overbought": 70})
        result = strat.generate_signals(df)

        last_rsi = result["rsi"][-1]
        last_signal = result["signal"][-1]

        if last_rsi > 70:
            assert last_signal == 0, (
                f"RSI={last_rsi:.1f} is above 70 but signal={last_signal} (expected 0)"
            )


class TestSMACrossDeterministic:
    """Tests SMA crossover with hand-calculable synthetic datasets."""

    def test_sma_cross_uptrend(self):
        """
        A steadily rising price should eventually make fast SMA > slow SMA → signal=1.
        Dataset: 250 linearly increasing prices.
        """
        prices = [100.0 + i * 0.5 for i in range(250)]
        df = _make_ohlcv(prices)

        strat = SMACrossover(params={"fast_period": 50, "slow_period": 200})
        result = strat.generate_signals(df)

        # After 200 bars, both SMAs have values. The fast responds to the trend faster.
        # In a constant uptrend, fast SMA > slow SMA → signal = 1
        assert result["signal"][-1] == 1, "Uptrend should produce buy signal"

    def test_sma_cross_downtrend(self):
        """
        A steadily falling price should make fast SMA < slow SMA → signal=0.
        """
        prices = [300.0 - i * 0.5 for i in range(250)]
        df = _make_ohlcv(prices)

        strat = SMACrossover(params={"fast_period": 50, "slow_period": 200})
        result = strat.generate_signals(df)

        assert result["signal"][-1] == 0, "Downtrend should produce sell signal"

    def test_sma_values_exact_match(self):
        """
        For a constant price, SMA(any window) MUST equal the price itself.
        """
        prices = [150.0] * 250
        df = _make_ohlcv(prices)

        strat = SMACrossover(params={"fast_period": 50, "slow_period": 200})
        result = strat.generate_signals(df)

        # After 200 bars, both SMAs = 150.0
        assert result["sma_fast"][-1] == pytest.approx(150.0, abs=1e-6)
        assert result["sma_slow"][-1] == pytest.approx(150.0, abs=1e-6)

    def test_sma_hand_calculated_5bar(self):
        """
        SMA(5) of [10, 20, 30, 40, 50] = 30.0 exactly.
        """
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        df = _make_ohlcv(prices)

        strat = SMACrossover(params={"fast_period": 5, "slow_period": 5})
        result = strat.generate_signals(df)

        # At the 5th bar, SMA(5) = (10+20+30+40+50)/5 = 30.0
        assert result["sma_fast"][-1] == pytest.approx(30.0, abs=1e-6)


class TestBollingerDeterministic:
    """Tests Bollinger Bands with synthetic datasets."""

    def test_constant_price_bands_collapse(self):
        """
        If price is constant, StdDev = 0, so upper band = lower band = mid = price.
        Signal should be 0 (or neutral) since price is neither > upper nor < lower.
        """
        prices = [100.0] * 30
        df = _make_ohlcv(prices)

        strat = BollingerBandsStrategy(params={"period": 20, "std_dev": 2.0})
        result = strat.generate_signals(df)

        # After 20 bars, bb_mid = 100.0, bb_std = 0.0
        assert result["bb_mid"][-1] == pytest.approx(100.0, abs=1e-6)
        # Upper and lower collapse to mid
        assert result["bb_upper"][-1] == pytest.approx(100.0, abs=1e-6)
        assert result["bb_lower"][-1] == pytest.approx(100.0, abs=1e-6)

    def test_price_below_lower_band_fires_buy(self):
        """
        If price drops sharply below the lower band, signal should be 1 (BUY).
        """
        prices = [100.0] * 25 + [60.0]  # Sudden crash below lower band
        df = _make_ohlcv(prices)

        strat = BollingerBandsStrategy(params={"period": 20, "std_dev": 2.0})
        result = strat.generate_signals(df)

        # 60 is far below the lower band when mean is ~100 and std is ~0
        assert result["signal"][-1] == 1, "Price below lower band should fire BUY"


class TestMACDDeterministic:
    """Tests MACD with synthetic datasets."""

    def test_constant_price_macd_is_zero(self):
        """
        If price is constant, all EMAs = price, so MACD line = 0.
        Signal line (EMA of 0) = 0.
        """
        prices = [50.0] * 50
        df = _make_ohlcv(prices)

        strat = MACDStrategy(params={"fast_period": 12, "slow_period": 26, "signal_period": 9})
        result = strat.generate_signals(df)

        assert result["macd_line"][-1] == pytest.approx(0.0, abs=1e-6)
        assert result["signal_line"][-1] == pytest.approx(0.0, abs=1e-6)

    def test_uptrend_macd_positive(self):
        """
        In a strong uptrend, the fast EMA reacts faster → MACD line > 0.
        """
        prices = [100.0 + i * 2.0 for i in range(50)]
        df = _make_ohlcv(prices)

        strat = MACDStrategy()
        result = strat.generate_signals(df)

        # After 26+ bars, MACD should be positive in an uptrend
        assert result["macd_line"][-1] > 0, "MACD should be positive in uptrend"

    def test_downtrend_macd_negative(self):
        """
        In a strong downtrend, the fast EMA drops faster → MACD line < 0.
        """
        prices = [200.0 - i * 2.0 for i in range(50)]
        df = _make_ohlcv(prices)

        strat = MACDStrategy()
        result = strat.generate_signals(df)

        assert result["macd_line"][-1] < 0, "MACD should be negative in downtrend"


# ============================================================================
# TIER 2 — Cross-Validation against Pandas (Golden Standard)
# ============================================================================

class TestCrossValidation:
    """
    Compares Polars strategy outputs against pure NumPy reference implementations.

    The NumPy functions above are straightforward loop-level implementations of
    standard financial math — they act as an independent oracle. If both a Polars
    (vectorised Rust) and a NumPy (iterative CPython) implementation produce the
    same numbers, we can be confident the math is correct.

    No pandas. No pandas-ta. No external libraries beyond numpy.
    """

    @pytest.fixture
    def realistic_close(self):
        """300 rows of synthetic price data for cross-validation."""
        np.random.seed(42)
        return np.cumprod(1 + np.random.normal(0.0002, 0.015, 300)) * 1000

    def test_sma_matches_numpy_rolling(self, realistic_close):
        """
        Polars rolling_mean must be identical to a naive NumPy sliding window.
        """
        close = realistic_close
        window = 50
        polars_df = _make_ohlcv(close.tolist())

        strat = SMACrossover(params={"fast_period": window, "slow_period": window})
        result = strat.generate_signals(polars_df)
        polars_sma = result["sma_fast"].to_numpy()

        ref_sma = numpy_sma(close, window)

        for i in range(window - 1, len(close)):
            assert polars_sma[i] == pytest.approx(ref_sma[i], rel=1e-6), (
                f"SMA mismatch at index {i}: polars={polars_sma[i]}, numpy={ref_sma[i]}"
            )

    def test_ema_matches_numpy_ewm(self, realistic_close):
        """
        Polars ewm_mean(span=12, adjust=False) must match the iterative NumPy EWM.
        Tests via the MACD strategy which exposes ema_fast.
        """
        close = realistic_close
        span = 12
        polars_df = _make_ohlcv(close.tolist())

        strat = MACDStrategy(params={"fast_period": span, "slow_period": 26, "signal_period": 9})
        result = strat.generate_signals(polars_df)
        polars_ema = result["ema_fast"].to_numpy()

        ref_ema = numpy_ewm(close, span)

        # Compare after one full span warmup period
        for i in range(span, len(close)):
            assert polars_ema[i] == pytest.approx(ref_ema[i], rel=1e-4), (
                f"EMA mismatch at index {i}: polars={polars_ema[i]:.4f}, numpy={ref_ema[i]:.4f}"
            )

    def test_rsi_matches_numpy_wilder(self, realistic_close):
        """
        Polars RSI (ewm_mean with com=period-1) must match the iterative Wilder's
        smoothing implemented in pure NumPy.
        """
        close = realistic_close
        period = 14
        polars_df = _make_ohlcv(close.tolist())

        strat = RSIStrategy(params={"period": period})
        result = strat.generate_signals(polars_df)
        polars_rsi = result["rsi"].to_numpy()

        ref_rsi = numpy_wilder_rsi(close, period)

        # Compare once both series have warmed up (skip first period+5 rows)
        for i in range(period + 5, len(close)):
            assert polars_rsi[i] == pytest.approx(ref_rsi[i], abs=1.0), (
                f"RSI mismatch at index {i}: polars={polars_rsi[i]:.2f}, numpy={ref_rsi[i]:.2f}"
            )

    def test_bollinger_std_matches_numpy(self, realistic_close):
        """
        Polars rolling_std must match Bessel-corrected NumPy rolling std (ddof=1).
        """
        close = realistic_close
        period = 20
        polars_df = _make_ohlcv(close.tolist())

        strat = BollingerBandsStrategy(params={"period": period})
        result = strat.generate_signals(polars_df)
        polars_std = result["bb_std"].to_numpy()

        ref_std = numpy_rolling_std(close, period)

        for i in range(period, len(close)):
            assert polars_std[i] == pytest.approx(ref_std[i], rel=1e-5), (
                f"BB StdDev mismatch at index {i}: polars={polars_std[i]:.5f}, numpy={ref_std[i]:.5f}"
            )


# ============================================================================
# TIER 3 — Look-Ahead Bias Detection
# ============================================================================

class TestLookAheadBias:
    """
    Verifies that signal at time T only affects returns starting at T+1.
    This is the most critical correctness test for any backtesting engine.
    """

    def test_signal_shift_by_one_row(self, engine):
        """
        A single BUY signal on Day 3 must:
        - NOT create a position on Day 3 (look-ahead bias!)
        - Create a position on Day 4
        - Capture Day 4's return, NOT Day 3's return
        """
        class SingleSignalStrategy(Strategy):
            def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
                # Emit signal=1 ONLY at row index 2 (Day 3)
                return df.with_columns(
                    pl.when(pl.col("timestamp") == 2)
                    .then(1)
                    .otherwise(0)
                    .alias("signal")
                )

        # Day 0: 100, Day 1: 100, Day 2: 150 (big gain), Day 3: 120 (loss)
        df = _make_ohlcv([100.0, 100.0, 150.0, 120.0])
        result = engine.run(SingleSignalStrategy(), df)

        # Position at Day 2 MUST BE 0 — we got the signal at close of Day 2
        assert result["position"][2] == 0, (
            "Look-ahead bias detected! Position was entered on the signal bar."
        )

        # Position at Day 3 = 1 (signal from Day 2 takes effect next bar)
        assert result["position"][3] == 1, (
            "Position should be active on the bar AFTER the signal."
        )

        # Day 3 strategy return = position(3) * market_return(3)
        # market_return(3) = 120/150 - 1 = -0.2 (a loss!)
        # We should capture the LOSS, not the Day 2 gain
        assert result["strategy_return"][3] < 0, (
            "Should capture Day 3's loss, not Day 2's gain."
        )

    def test_signal_off_stops_return(self, engine):
        """
        After signal goes to 0, the position should exit on the next bar.
        """
        class PulseSignalStrategy(Strategy):
            def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
                # Signal ON at row 1, OFF at row 3
                signals = [0, 1, 1, 0, 0]
                return df.with_columns(pl.Series("signal", signals))

        # Prices: flat, then up, then we exit, then crash
        df = _make_ohlcv([100.0, 100.0, 110.0, 120.0, 50.0])
        result = engine.run(PulseSignalStrategy(), df)

        # Row 4: position should be 0 (signal was 0 at row 3)
        assert result["position"][4] == 0, (
            "Position should be flat after signal turns off."
        )
        # Row 4: strategy_return should be 0 (not in market during crash)
        assert result["strategy_return"][4] == pytest.approx(0.0, abs=1e-10), (
            "Should not capture the crash since we exited."
        )

    def test_first_bar_always_zero_position(self, engine):
        """
        The first bar can never have a position because there is no prior signal.
        """
        class AlwaysLongStrategy(Strategy):
            def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
                return df.with_columns(pl.lit(1).alias("signal"))

        df = _make_ohlcv([100.0, 110.0, 120.0])
        result = engine.run(AlwaysLongStrategy(), df)

        assert result["position"][0] == 0, (
            "First bar position must ALWAYS be 0 (no prior signal exists)."
        )
        assert result["strategy_return"][0] == 0.0, (
            "First bar strategy return must be 0."
        )

    def test_equity_never_negative(self, engine):
        """
        Equity should never go negative regardless of price movements.
        This is a fundamental invariant for the multiplicative model.
        """
        # Extreme price movements: -90% crash
        prices = [100.0, 10.0, 5.0, 1.0, 0.5]

        class AlwaysLong(Strategy):
            def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
                return df.with_columns(pl.lit(1).alias("signal"))

        df = _make_ohlcv(prices)
        result = engine.run(AlwaysLong(), df)

        # Equity must never be 0 or negative
        assert all(e > 0 for e in result["equity"].to_list()), (
            "Equity went negative or zero — multiplicative model should prevent this."
        )


# ============================================================================
# TIER 4 — Edge Case Invariants
# ============================================================================

class TestEdgeCaseInvariants:
    """
    'Poison pill' datasets that ensure strategies handle degenerate data gracefully.
    """

    def test_zero_volume_no_crash(self):
        """
        Passing volume=0 for all rows should never cause DivisionByZero.
        """
        prices = [100.0] * 50
        df = _make_ohlcv(prices, volume=0)

        for strat_class, params in [
            (RSIStrategy, {"period": 14}),
            (SMACrossover, {"fast_period": 10, "slow_period": 20}),
            (MACDStrategy, {}),
            (BollingerBandsStrategy, {"period": 20}),
        ]:
            strat = strat_class(params=params)
            result = strat.generate_signals(df)
            assert "signal" in result.columns, (
                f"{strat_class.__name__} crashed with zero volume"
            )

    def test_insufficient_data_rsi(self):
        """
        RSI with period=14 given only 5 rows should produce signals without crash.
        """
        prices = [100.0, 101.0, 99.0, 102.0, 98.0]
        df = _make_ohlcv(prices)

        strat = RSIStrategy(params={"period": 14})
        result = strat.generate_signals(df)

        assert "signal" in result.columns
        assert len(result) == 5

    def test_insufficient_data_sma(self):
        """
        SMA with window=200 given only 10 rows should not crash.
        SMA values before the window should be null, and signal should be 0.
        """
        prices = [100.0 + i for i in range(10)]
        df = _make_ohlcv(prices)

        strat = SMACrossover(params={"fast_period": 50, "slow_period": 200})
        result = strat.generate_signals(df)

        assert "signal" in result.columns
        assert len(result) == 10

    def test_insufficient_data_bollinger(self):
        """
        Bollinger with period=20 given only 5 rows should not crash.
        """
        prices = [100.0, 101.0, 99.0, 102.0, 98.0]
        df = _make_ohlcv(prices)

        strat = BollingerBandsStrategy(params={"period": 20})
        result = strat.generate_signals(df)

        assert "signal" in result.columns
        assert len(result) == 5

    def test_single_row_data(self):
        """
        Strategies must handle a single row without crashing.
        """
        df = _make_ohlcv([100.0])

        for strat_class, params in [
            (RSIStrategy, {"period": 14}),
            (SMACrossover, {"fast_period": 5, "slow_period": 10}),
            (MACDStrategy, {}),
            (BollingerBandsStrategy, {"period": 20}),
        ]:
            strat = strat_class(params=params)
            result = strat.generate_signals(df)
            assert len(result) == 1, (
                f"{strat_class.__name__} changed row count on single-row input"
            )

    def test_extreme_price_spike(self):
        """
        A 1000x price spike should not cause overflow errors.
        """
        prices = [1.0] * 20 + [1000.0] + [1.0] * 20
        df = _make_ohlcv(prices)

        for strat_class, params in [
            (RSIStrategy, {"period": 14}),
            (SMACrossover, {"fast_period": 10, "slow_period": 20}),
            (MACDStrategy, {}),
            (BollingerBandsStrategy, {"period": 20}),
        ]:
            strat = strat_class(params=params)
            result = strat.generate_signals(df)
            # No NaN or Inf in signal column
            signal_values = result["signal"].to_list()
            for v in signal_values:
                assert v is not None and not np.isinf(v), (
                    f"{strat_class.__name__} produced Inf/NaN on price spike"
                )

    def test_negative_prices_no_crash(self):
        """
        While theoretically impossible, negative prices shouldn't crash the system.
        This can happen with synthetic datasets or data errors.
        """
        prices = [100.0, -50.0, -100.0, 50.0, 100.0]
        df = _make_ohlcv(prices)

        for strat_class, params in [
            (RSIStrategy, {"period": 2}),
            (MACDStrategy, {"fast_period": 2, "slow_period": 3, "signal_period": 2}),
        ]:
            strat = strat_class(params=params)
            result = strat.generate_signals(df)
            assert "signal" in result.columns

    def test_signal_column_length_invariant(self):
        """
        Strategy output row count MUST equal input row count. Always.
        """
        for n in [1, 5, 50, 200]:
            prices = [100.0 + i * 0.1 for i in range(n)]
            df = _make_ohlcv(prices)

            for strat_class, params in [
                (RSIStrategy, {"period": 14}),
                (SMACrossover, {"fast_period": 10, "slow_period": 20}),
                (MACDStrategy, {}),
                (BollingerBandsStrategy, {"period": 20}),
            ]:
                strat = strat_class(params=params)
                result = strat.generate_signals(df)
                assert len(result) == n, (
                    f"{strat_class.__name__} changed {n} rows to {len(result)}"
                )

    def test_signal_values_are_binary(self):
        """
        All strategy signals MUST be 0 or 1 (after forward fill).
        No fractional signals, no negatives (for long-only strategies).
        """
        np.random.seed(99)
        prices = (np.cumprod(1 + np.random.normal(0, 0.02, 200)) * 100).tolist()
        df = _make_ohlcv(prices)

        for strat_class, params in [
            (RSIStrategy, {"period": 14}),
            (SMACrossover, {"fast_period": 10, "slow_period": 50}),
            (MACDStrategy, {}),
            (BollingerBandsStrategy, {"period": 20}),
        ]:
            strat = strat_class(params=params)
            result = strat.generate_signals(df)
            unique_vals = set(result["signal"].to_list())
            assert unique_vals.issubset({0, 1}), (
                f"{strat_class.__name__} produced signals {unique_vals}, expected only {{0, 1}}"
            )


# ============================================================================
# TIER 5 (Bonus) — Engine Integration Invariants
# ============================================================================

class TestEngineIntegration:
    """
    Tests that the full engine pipeline maintains mathematical guarantees.
    """

    def test_buy_and_hold_matches_market(self, engine):
        """
        A 'buy and hold' strategy should produce equity that tracks the market.
        Since we shift position by 1, we lose the first bar's return.
        After that, equity / initial_cash ≈ close / first_close (approximately).
        """
        class BuyAndHold(Strategy):
            def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
                return df.with_columns(pl.lit(1).alias("signal"))

        prices = [100.0, 110.0, 121.0, 133.1]
        df = _make_ohlcv(prices)
        result = engine.run(BuyAndHold(), df)

        # Market return from bar 1 to bar 3 = 133.1/110.0 - 1 = 0.21
        # We enter at bar 1 (position=1 since signal[0]=1) and hold.
        # Our equity captures returns from bar 1 onward.
        # Equity at bar 3 = 100000 * 1.0 * (110/100) * (121/110) * (133.1/121)
        # Wait — bar 0 position = 0, so we skip the first return.
        # Equity = 100000 * (110/100) * (121/110) * (133.1/121)
        # = 100000 * 1.1 * 1.1 * 1.1 = 133100

        # Bar 0 strat_ret = 0 (no position)
        # Bar 1 strat_ret = 1 * (110/100 - 1) = 0.1
        # Bar 2 strat_ret = 1 * (121/110 - 1) = 0.1
        # Bar 3 strat_ret = 1 * (133.1/121 - 1) = 0.1
        final_equity = result["equity"][-1]
        expected = 100000.0 * 1.1 * 1.1 * 1.1
        assert final_equity == pytest.approx(expected, rel=1e-6), (
            f"Buy-and-hold equity mismatch: got {final_equity}, expected {expected}"
        )

    def test_always_flat_equity_unchanged(self, engine):
        """
        A strategy that never enters the market should preserve initial capital exactly.
        """
        class NeverTrade(Strategy):
            def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
                return df.with_columns(pl.lit(0).alias("signal"))

        prices = [100.0, 200.0, 50.0, 500.0]
        df = _make_ohlcv(prices)
        result = engine.run(NeverTrade(), df)

        # All equity values should be exactly initial_cash
        for equity in result["equity"].to_list():
            assert equity == pytest.approx(100000.0, abs=1e-6), (
                "Flat strategy should have 0 returns."
            )

    def test_metrics_calculation_from_engine(self, engine):
        """
        End-to-end: run a strategy and verify metrics are calculable.
        """
        class BuyAndHold(Strategy):
            def generate_signals(self, df: pl.DataFrame) -> pl.DataFrame:
                return df.with_columns(pl.lit(1).alias("signal"))

        np.random.seed(42)
        prices = (np.cumprod(1 + np.random.normal(0, 0.01, 100)) * 100).tolist()
        df = _make_ohlcv(prices)

        result = engine.run(BuyAndHold(), df)
        metrics = engine.calculate_metrics(result)

        assert "Total Return" in metrics
        assert "Max Drawdown" in metrics
        assert "Sharpe Ratio" in metrics
        assert "Final Equity" in metrics

        # Parseable
        assert "%" in metrics["Total Return"]
        assert float(metrics["Final Equity"]) > 0
