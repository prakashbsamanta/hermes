"""Tests for API routes."""

from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Hermes API is running"}


def test_backtest_rsi(mock_market_data_service):
    """Test backtest endpoint with RSI strategy."""
    with patch("api.routes.market_data_service", mock_market_data_service):
        with patch("api.routes.backtest_service.market_data_service", mock_market_data_service):
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
    with patch("api.routes.market_data_service", mock_market_data_service):
        with patch("api.routes.backtest_service.market_data_service", mock_market_data_service):
            payload = {
                "symbol": "TEST_SYM",
                "strategy": "InvalidStrategy",
                "params": {},
            }
            response = client.post("/backtest", json=payload)
            assert response.status_code == 400


def test_backtest_missing_params():
    """Test backtest with missing required fields returns 422."""
    payload = {
        "symbol": "AARTIIND",
        # Missing strategy
        "params": {},
    }
    response = client.post("/backtest", json=payload)
    assert response.status_code == 422


def test_get_instruments(mock_market_data_service):
    """Test listing instruments."""
    with patch("api.routes.market_data_service", mock_market_data_service):
        response = client.get("/instruments")
        assert response.status_code == 200
        assert "TEST_SYM" in response.json()


def test_get_market_data(mock_market_data_service):
    """Test fetching market data for a symbol."""
    with patch("api.routes.market_data_service", mock_market_data_service):
        response = client.get("/data/TEST_SYM")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TEST_SYM"
        assert len(data["candles"]) > 0
        assert "open" in data["candles"][0]


def test_get_market_data_not_found(mock_market_data_service):
    """Test fetching non-existent symbol returns 404."""
    with patch("api.routes.market_data_service", mock_market_data_service):
        response = client.get("/data/NON_EXISTENT")
        assert response.status_code == 404


def test_backtest_rsi_event_mode(mock_market_data_service):
    """Test backtest in event mode."""
    with patch("api.routes.market_data_service", mock_market_data_service):
        with patch("api.routes.backtest_service.market_data_service", mock_market_data_service):
            payload = {
                "symbol": "TEST_SYM",
                "strategy": "RSIStrategy",
                "params": {"period": 14},
                "mode": "event",
            }
            response = client.post("/backtest", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["metrics"]["Status"] == "Event Backtest Completed"
            assert len(data["equity_curve"]) > 0
            assert "signals" in data
