"""Tests for the data registry."""

import pytest
from unittest.mock import MagicMock, patch

# Skip tests if PostgreSQL not available
pytest.importorskip("psycopg2")


class TestRegistryModels:
    """Tests for registry SQLAlchemy models."""

    def test_instrument_repr(self):
        """Test Instrument string representation."""
        from hermes_data.registry.models import Instrument
        
        inst = Instrument(symbol="RELIANCE", exchange="NSE")
        assert "RELIANCE" in repr(inst)
        assert "NSE" in repr(inst)

    def test_data_availability_repr(self):
        """Test DataAvailability string representation."""
        from hermes_data.registry.models import DataAvailability
        
        avail = DataAvailability(
            instrument_id=1,
            timeframe="1m",
            row_count=1000,
        )
        assert "1m" in repr(avail)
        assert "1000" in repr(avail)

    def test_data_load_log_repr(self):
        """Test DataLoadLog string representation."""
        from hermes_data.registry.models import DataLoadLog
        
        log = DataLoadLog(symbol="RELIANCE", status="SUCCESS")
        assert "RELIANCE" in repr(log)
        assert "SUCCESS" in repr(log)


class TestRegistryServiceMocked:
    """Tests for RegistryService with mocked database."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        mock_session = MagicMock()
        mock_db.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.session.return_value.__exit__ = MagicMock(return_value=False)
        
        return mock_db, mock_session

    def test_registry_service_init(self, mock_database):
        """Test RegistryService initialization."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, _ = mock_database
        service = RegistryService(database=mock_db)
        
        assert service._database is mock_db

    def test_health_check_success(self, mock_database):
        """Test health check when database is healthy."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_db.health_check.return_value = True
        mock_session.query.return_value.scalar.return_value = 10
        
        service = RegistryService(database=mock_db)
        health = service.health_check()
        
        assert health["healthy"] is True
        assert health["database"] == "connected"


class TestDatabaseMocked:
    """Tests for Database class with mocked engine."""

    def test_mask_url(self):
        """Test password masking in URLs."""
        from hermes_data.registry.database import Database
        
        db = Database.__new__(Database)
        masked = db._mask_url("postgresql://user:secret123@localhost:5432/db")
        
        assert "secret123" not in masked
        assert "***" in masked
        assert "user" in masked

    def test_session_context_manager(self):
        """Test session context manager behavior."""
        from hermes_data.registry.database import Database
        from hermes_data import DataSettings
        
        # Mock the engine creation
        with patch("hermes_data.registry.database.create_engine"):
            mock_session = MagicMock()
            mock_session_factory = MagicMock(return_value=mock_session)
            
            settings = DataSettings(
                database_url="postgresql://test:test@localhost/test",
                registry_enabled=True,
            )
            db = Database(settings)
            db._session_factory = mock_session_factory
            
            with db.session() as _:
                pass
            
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_session_rollback_on_error(self):
        """Test session rollback on exception."""
        from hermes_data.registry.database import Database
        from hermes_data import DataSettings
        
        with patch("hermes_data.registry.database.create_engine"):
            mock_session = MagicMock()
            mock_session_factory = MagicMock(return_value=mock_session)
            
            settings = DataSettings(
                database_url="postgresql://test:test@localhost/test",
                registry_enabled=True,
            )
            db = Database(settings)
            db._session_factory = mock_session_factory
            
            with pytest.raises(ValueError):
                with db.session() as _:
                    raise ValueError("Test error")
            
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
