"""Tests for the ScannerService and /scan endpoint."""

import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app
from api.models import ScanRequest, BacktestResponse, ChartPoint, SignalPoint

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_service_singletons():
    """Reset service singletons before each test."""
    import api.routes as routes_module
    routes_module._market_data_service = None
    routes_module._backtest_service = None
    routes_module._scanner_service = None
    yield
    routes_module._market_data_service = None
    routes_module._backtest_service = None
    routes_module._scanner_service = None


def _make_mock_response(symbol: str, total_return: str = "5.00%") -> BacktestResponse:
    """Create a mock BacktestResponse for testing."""
    return BacktestResponse(
        symbol=symbol,
        strategy="RSIStrategy",
        metrics={"Total Return": total_return, "Sharpe Ratio": "1.5", "Max Drawdown": "-3.00%"},
        equity_curve=[ChartPoint(time=1000, value=100000), ChartPoint(time=2000, value=105000)],
        signals=[
            SignalPoint(time=1500, type="buy", price=100.0),
            SignalPoint(time=1800, type="sell", price=105.0),
        ],
        candles=[],
    )


class TestScannerService:
    """Unit tests for ScannerService."""

    def test_scan_single_symbol(self, mock_market_data_service):
        """Scan a single symbol returns correct ScanResult."""
        from services.backtest_service import BacktestService
        from services.scanner_service import ScannerService

        backtest_svc = BacktestService(mock_market_data_service)
        scanner = ScannerService(backtest_svc)

        request = ScanRequest(strategy="RSIStrategy", symbols=["TEST_SYM"])
        result = asyncio.run(scanner.scan(request))

        assert result.total_symbols == 1
        assert result.completed == 1
        assert result.failed == 0
        assert len(result.results) == 1
        assert result.results[0].symbol == "TEST_SYM"
        assert result.results[0].status == "success"
        assert result.elapsed_ms >= 0

    def test_scan_multiple_symbols(self, mock_market_data_service):
        """Scan multiple symbols returns results for all."""
        from services.backtest_service import BacktestService
        from services.scanner_service import ScannerService

        backtest_svc = BacktestService(mock_market_data_service)
        scanner = ScannerService(backtest_svc)

        # TEST_SYM exists, FAKE_SYM does not
        request = ScanRequest(strategy="RSIStrategy", symbols=["TEST_SYM", "FAKE_SYM"])
        result = asyncio.run(scanner.scan(request))

        assert result.total_symbols == 2
        assert len(result.results) == 2

        symbols = {r.symbol for r in result.results}
        assert "TEST_SYM" in symbols
        assert "FAKE_SYM" in symbols

    def test_scan_all_instruments(self, mock_market_data_service):
        """symbols=None resolves to full instrument list."""
        from services.backtest_service import BacktestService
        from services.scanner_service import ScannerService

        backtest_svc = BacktestService(mock_market_data_service)
        scanner = ScannerService(backtest_svc)

        request = ScanRequest(strategy="RSIStrategy", symbols=None)
        result = asyncio.run(scanner.scan(request))

        # Should resolve to instruments from the mock service
        instruments = mock_market_data_service.list_instruments()
        assert result.total_symbols == len(instruments)

    def test_scan_handles_missing_data(self, mock_market_data_service):
        """Bad symbol returns status='error' without crashing the batch."""
        from services.backtest_service import BacktestService
        from services.scanner_service import ScannerService

        backtest_svc = BacktestService(mock_market_data_service)
        scanner = ScannerService(backtest_svc)

        request = ScanRequest(strategy="RSIStrategy", symbols=["NONEXISTENT"])
        result = asyncio.run(scanner.scan(request))

        assert result.total_symbols == 1
        assert result.failed == 1
        assert result.results[0].status == "error"
        assert result.results[0].error is not None

    def test_scan_invalid_strategy(self, mock_market_data_service):
        """Invalid strategy raises ValueError before executing batch."""
        from services.backtest_service import BacktestService
        from services.scanner_service import ScannerService

        backtest_svc = BacktestService(mock_market_data_service)
        scanner = ScannerService(backtest_svc)

        request = ScanRequest(strategy="NonExistentStrategy", symbols=["TEST_SYM"])
        with pytest.raises(ValueError, match="not found"):
            asyncio.run(scanner.scan(request))

    def test_scan_results_sorted(self):
        """Results are sorted by Total Return descending."""
        from services.scanner_service import ScannerService

        mock_backtest_svc = MagicMock()
        mock_backtest_svc.get_strategies.return_value = {"RSIStrategy": MagicMock}
        mock_backtest_svc.market_data_service.list_instruments.return_value = []

        # Mock run_backtest to return different returns
        def mock_run(req):
            returns = {"SYM_A": "10.00%", "SYM_B": "25.00%", "SYM_C": "-5.00%"}
            return _make_mock_response(req.symbol, returns.get(req.symbol, "0%"))

        mock_backtest_svc.run_backtest.side_effect = mock_run

        scanner = ScannerService(mock_backtest_svc)
        request = ScanRequest(strategy="RSIStrategy", symbols=["SYM_A", "SYM_B", "SYM_C"])

        result = asyncio.run(scanner.scan(request))

        returns = [scanner._extract_return(r.metrics) for r in result.results]
        assert returns == sorted(returns, reverse=True)
        assert result.results[0].symbol == "SYM_B"  # 25%
        assert result.results[-1].symbol == "SYM_C"  # -5%

    def test_scan_empty_symbols(self):
        """Empty symbol list returns empty response immediately."""
        from services.scanner_service import ScannerService

        mock_backtest_svc = MagicMock()
        mock_backtest_svc.get_strategies.return_value = {"RSIStrategy": MagicMock}
        mock_backtest_svc.market_data_service.list_instruments.return_value = []

        scanner = ScannerService(mock_backtest_svc)
        request = ScanRequest(strategy="RSIStrategy", symbols=[])

        result = asyncio.run(scanner.scan(request))

        assert result.total_symbols == 0
        assert result.completed == 0
        assert len(result.results) == 0

    def test_scan_deduplicates_symbols(self):
        """Duplicate symbols in request are deduplicated."""
        from services.scanner_service import ScannerService

        mock_backtest_svc = MagicMock()
        mock_backtest_svc.get_strategies.return_value = {"RSIStrategy": MagicMock}
        mock_backtest_svc.run_backtest.side_effect = lambda req: _make_mock_response(req.symbol)

        scanner = ScannerService(mock_backtest_svc)
        request = ScanRequest(
            strategy="RSIStrategy",
            symbols=["SYM_A", "sym_a", "SYM_A"],  # All resolve to SYM_A
        )

        result = asyncio.run(scanner.scan(request))

        assert result.total_symbols == 1  # Deduplicated
        assert len(result.results) == 1

    def test_extract_return_helper(self):
        """Test the _extract_return static method."""
        from services.scanner_service import ScannerService

        assert ScannerService._extract_return({"Total Return": "5.23%"}) == 5.23
        assert ScannerService._extract_return({"Total Return": "-3.00%"}) == -3.0
        assert ScannerService._extract_return({"Total Return": "0%"}) == 0.0
        assert ScannerService._extract_return({}) == 0.0
        assert ScannerService._extract_return({"Total Return": "N/A"}) == 0.0

    def test_params_hash_deterministic(self):
        """Same params produce the same hash."""
        from services.scanner_service import _compute_params_hash

        h1 = _compute_params_hash({"period": 14}, "vector", "1h", None, None)
        h2 = _compute_params_hash({"period": 14}, "vector", "1h", None, None)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256

    def test_params_hash_varies(self):
        """Different params produce different hashes."""
        from services.scanner_service import _compute_params_hash

        h1 = _compute_params_hash({"period": 14}, "vector", "1h", None, None)
        h2 = _compute_params_hash({"period": 20}, "vector", "1h", None, None)
        h3 = _compute_params_hash({"period": 14}, "event", "1h", None, None)
        h4 = _compute_params_hash({"period": 14}, "vector", "1d", None, None)
        assert h1 != h2
        assert h1 != h3
        assert h1 != h4


class TestScanEndpoint:
    """Integration tests for the POST /scan API endpoint."""

    def test_scan_endpoint_success(self, mock_market_data_service):
        """POST /scan returns 200 with valid request."""
        import api.routes as routes_module
        from services.backtest_service import BacktestService
        from services.scanner_service import ScannerService

        routes_module._market_data_service = mock_market_data_service
        backtest_svc = BacktestService(mock_market_data_service)
        routes_module._backtest_service = backtest_svc
        routes_module._scanner_service = ScannerService(backtest_svc)

        payload = {
            "strategy": "RSIStrategy",
            "symbols": ["TEST_SYM"],
        }
        response = client.post("/scan", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["strategy"] == "RSIStrategy"
        assert data["total_symbols"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["symbol"] == "TEST_SYM"

    def test_scan_endpoint_invalid_strategy(self, mock_market_data_service):
        """POST /scan with bad strategy returns 400."""
        import api.routes as routes_module
        from services.backtest_service import BacktestService
        from services.scanner_service import ScannerService

        routes_module._market_data_service = mock_market_data_service
        backtest_svc = BacktestService(mock_market_data_service)
        routes_module._backtest_service = backtest_svc
        routes_module._scanner_service = ScannerService(backtest_svc)

        payload = {
            "strategy": "FakeStrategy",
            "symbols": ["TEST_SYM"],
        }
        response = client.post("/scan", json=payload)
        assert response.status_code == 400

    def test_scan_endpoint_missing_strategy(self):
        """POST /scan with missing strategy field returns 422."""
        payload = {"symbols": ["TEST_SYM"]}
        response = client.post("/scan", json=payload)
        assert response.status_code == 422
