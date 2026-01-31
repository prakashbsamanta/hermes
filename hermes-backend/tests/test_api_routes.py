from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Hermes API is running"}

def test_backtest_rsi(temp_data_dir):
    with patch("api.routes.get_data_dir", return_value=temp_data_dir):
        payload = {
            "symbol": "TEST_SYM",
            "strategy": "RSIStrategy",
            "params": {"period": 14}
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "equity_curve" in data
        assert "signals" in data
        assert "candles" in data
        assert data["symbol"] == "TEST_SYM"

def test_backtest_invalid_strategy(temp_data_dir):
    with patch("api.routes.get_data_dir", return_value=temp_data_dir):
        payload = {
            "symbol": "TEST_SYM",
            "strategy": "InvalidStrategy",
            "params": {}
        }
        response = client.post("/backtest", json=payload)
        # The API catches missing strategy and returns 400
        assert response.status_code == 400

def test_backtest_missing_params():
    # Helper to check partial payload if needed, 
    # but strictly typed Pydantic might reject it 422
    payload = {
        "symbol": "AARTIIND",
        # Missing strategy
        "params": {}
    }
    response = client.post("/backtest", json=payload)
    assert response.status_code == 422 

def test_get_instruments(temp_data_dir):
    with patch("api.routes.get_data_dir", return_value=temp_data_dir):
        response = client.get("/instruments")
        assert response.status_code == 200
        assert "TEST_SYM" in response.json()

def test_get_market_data(temp_data_dir):
    with patch("api.routes.get_data_dir", return_value=temp_data_dir):
        response = client.get("/data/TEST_SYM")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TEST_SYM"
        assert len(data["candles"]) > 0
        assert "open" in data["candles"][0]

def test_get_market_data_not_found(temp_data_dir):
    with patch("api.routes.get_data_dir", return_value=temp_data_dir):
        response = client.get("/data/NON_EXISTENT")
        assert response.status_code == 404
