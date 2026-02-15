"""Tests for API routes."""

from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from main import app

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


def test_health_check():
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Hermes API is running"}


def test_backtest_rsi(mock_market_data_service):
    """Test backtest endpoint with RSI strategy."""
    import api.routes as routes_module
    routes_module._market_data_service = mock_market_data_service
    routes_module._backtest_service = None  # Force recreation with new service
    
    from services.backtest_service import BacktestService
    routes_module._backtest_service = BacktestService(mock_market_data_service)
    
    payload = {
        "symbol": "TEST_SYM",
        "strategy": "RSIStrategy",
        "params": {"period": 14},
    }
    response = client.post("/backtest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "equity_curve" in data
    assert "signals" in data
    assert "candles" in data
    assert data["symbol"] == "TEST_SYM"


def test_backtest_invalid_strategy(mock_market_data_service):
    """Test backtest with non-existent strategy returns 400."""
    import api.routes as routes_module
    routes_module._market_data_service = mock_market_data_service
    
    from services.backtest_service import BacktestService
    routes_module._backtest_service = BacktestService(mock_market_data_service)
    
    payload = {
        "symbol": "TEST_SYM",
        "strategy": "InvalidStrategy",
        "params": {},
    }
    response = client.post("/backtest", json=payload)
    assert response.status_code == 400


def test_backtest_missing_params():
    """Test backtest with missing required fields returns 422."""
    payload = {"symbol": "TEST_SYM"}  # Missing strategy
    response = client.post("/backtest", json=payload)
    assert response.status_code == 422


def test_list_instruments(mock_market_data_service):
    """Test instruments list endpoint."""
    import api.routes as routes_module
    routes_module._market_data_service = mock_market_data_service
    
    response = client.get("/instruments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_market_data(mock_market_data_service):
    """Test market data endpoint."""
    import api.routes as routes_module
    routes_module._market_data_service = mock_market_data_service
    
    response = client.get("/data/TEST_SYM?timeframe=1h")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "TEST_SYM"
    assert data["timeframe"] == "1h"
    assert "candles" in data


def test_get_market_data_not_found():
    """Test market data endpoint with non-existent symbol."""
    mock_service = MagicMock()
    mock_service.get_candles.side_effect = FileNotFoundError("Symbol not found")
    
    import api.routes as routes_module
    routes_module._market_data_service = mock_service
    
    response = client.get("/data/NONEXISTENT")
    assert response.status_code == 404
