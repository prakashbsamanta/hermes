from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Hermes API is running"}

def test_backtest_rsi():
    payload = {
        "symbol": "AARTIIND",
        "strategy": "RSIStrategy",
        "params": {"period": 14}
    }
    response = client.post("/backtest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "equity_curve" in data
    assert "signals" in data
    assert data["symbol"] == "AARTIIND"

def test_backtest_invalid_strategy():
    payload = {
        "symbol": "AARTIIND",
        "strategy": "InvalidStrategy",
        "params": {}
    }
    response = client.post("/backtest", json=payload)
    # The API might error out or return 500/400.
    # checking code: routes.py raises exception?
    # It catches exception and returns 500.
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
