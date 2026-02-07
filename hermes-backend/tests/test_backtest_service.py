"""Tests for backtest service including event mode."""

import pytest


class TestBacktestServiceEventMode:
    """Tests for backtest service event-driven mode."""

    def test_event_mode_backtest(self, mock_market_data_service):
        """Test event-mode backtest execution."""
        from services.backtest_service import BacktestService
        from api.models import BacktestRequest
        
        service = BacktestService(mock_market_data_service)
        
        request = BacktestRequest(
            symbol="TEST_SYM",
            strategy="RSIStrategy",
            params={"period": 5},
            mode="event",
            initial_cash=100000,
        )
        
        result = service.run_backtest(request)
        
        assert result.symbol == "TEST_SYM"
        assert "metrics" in result.model_dump()
        assert "equity_curve" in result.model_dump()

    def test_event_mode_with_signals(self, mock_market_data_service):
        """Test event mode generates signals."""
        from services.backtest_service import BacktestService
        from api.models import BacktestRequest
        
        service = BacktestService(mock_market_data_service)
        
        request = BacktestRequest(
            symbol="TEST_SYM",
            strategy="RSIStrategy",
            params={"period": 3, "oversold": 40, "overbought": 60},
            mode="event",
        )
        
        result = service.run_backtest(request)
        
        # Event mode should complete and return response
        assert result.symbol == "TEST_SYM"

    def test_get_strategies(self, mock_market_data_service):
        """Test getting available strategies."""
        from services.backtest_service import BacktestService
        
        service = BacktestService(mock_market_data_service)
        strategies = service.get_strategies()
        
        assert "RSIStrategy" in strategies
        assert "MACDStrategy" in strategies
        assert "BollingerBandsStrategy" in strategies
        assert "SMACrossover" in strategies

    def test_backtest_data_load_error(self, mock_market_data_service):
        """Test backtest with data load failure."""
        from services.backtest_service import BacktestService
        from api.models import BacktestRequest
        from unittest.mock import MagicMock
        
        # Create a mock that raises an error on data load
        mock_service = MagicMock()
        mock_service.data_service.get_market_data.side_effect = Exception("Data not found")
        
        service = BacktestService(mock_service)
        
        request = BacktestRequest(
            symbol="INVALID",
            strategy="RSIStrategy",
            params={},
        )
        
        with pytest.raises(ValueError, match="Data load failed"):
            service.run_backtest(request)

    def test_backtest_invalid_strategy_params(self, mock_market_data_service):
        """Test backtest with invalid strategy params."""
        from services.backtest_service import BacktestService
        from api.models import BacktestRequest
        
        service = BacktestService(mock_market_data_service)
        
        request = BacktestRequest(
            symbol="TEST_SYM",
            strategy="InvalidStrategy",
            params={},
        )
        
        with pytest.raises(ValueError, match="not found"):
            service.run_backtest(request)
