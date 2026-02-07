"""Comprehensive tests for RegistryService to achieve 90%+ coverage."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Skip tests if PostgreSQL not available
pytest.importorskip("psycopg2")


class TestRegistryServiceCRUD:
    """Tests for RegistryService CRUD operations."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database with session context manager."""
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        mock_session = MagicMock()
        
        # Configure context manager
        mock_db.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.session.return_value.__exit__ = MagicMock(return_value=False)
        
        return mock_db, mock_session

    @pytest.fixture
    def registry_service(self, mock_database):
        """Create a RegistryService with mocked database."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, _ = mock_database
        service = RegistryService(database=mock_db)
        return service

    def test_get_instrument_found(self, mock_database):
        """Test get_instrument when instrument exists."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import Instrument
        
        mock_db, mock_session = mock_database
        mock_instrument = Instrument(id=1, symbol="RELIANCE", exchange="NSE")
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_instrument
        
        service = RegistryService(database=mock_db)
        result = service.get_instrument("RELIANCE")
        
        assert result is mock_instrument

    def test_get_instrument_not_found(self, mock_database):
        """Test get_instrument when instrument doesn't exist."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        service = RegistryService(database=mock_db)
        result = service.get_instrument("UNKNOWN")
        
        assert result is None

    def test_get_or_create_instrument_existing(self, mock_database):
        """Test get_or_create_instrument when instrument exists."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import Instrument
        
        mock_db, mock_session = mock_database
        mock_instrument = MagicMock(spec=Instrument)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_instrument
        
        service = RegistryService(database=mock_db)
        result = service.get_or_create_instrument("RELIANCE", name="Reliance", exchange="NSE")
        
        assert result is mock_instrument
        mock_session.add.assert_not_called()

    def test_get_or_create_instrument_new(self, mock_database):
        """Test get_or_create_instrument when creating new instrument."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        service = RegistryService(database=mock_db)
        service.get_or_create_instrument("NEWSTOCK", name="New Stock", exchange="NSE")
        
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called()

    def test_search_instruments(self, mock_database):
        """Test search_instruments."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import Instrument
        
        mock_db, mock_session = mock_database
        mock_instruments = [
            MagicMock(spec=Instrument),
            MagicMock(spec=Instrument),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_instruments
        
        service = RegistryService(database=mock_db)
        results = service.search_instruments("REL", limit=10)
        
        assert len(results) == 2

    def test_list_all_instruments(self, mock_database):
        """Test list_all_instruments."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import Instrument
        
        mock_db, mock_session = mock_database
        mock_instruments = [MagicMock(spec=Instrument) for _ in range(5)]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_instruments
        
        service = RegistryService(database=mock_db)
        results = service.list_all_instruments()
        
        assert len(results) == 5


class TestRegistryServiceDataAvailability:
    """Tests for data availability operations."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        mock_session = MagicMock()
        mock_db.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.session.return_value.__exit__ = MagicMock(return_value=False)
        
        return mock_db, mock_session

    def test_get_data_availability_found(self, mock_database):
        """Test get_data_availability when record exists."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import DataAvailability
        
        mock_db, mock_session = mock_database
        mock_availability = MagicMock(spec=DataAvailability)
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_availability
        
        service = RegistryService(database=mock_db)
        result = service.get_data_availability("RELIANCE", "1m")
        
        assert result is mock_availability

    def test_get_data_availability_not_found(self, mock_database):
        """Test get_data_availability when record doesn't exist."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        service = RegistryService(database=mock_db)
        result = service.get_data_availability("UNKNOWN", "1m")
        
        assert result is None

    def test_update_data_availability_new(self, mock_database):
        """Test update_data_availability creating new record."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        # Simulate no existing instrument or availability
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        service = RegistryService(database=mock_db)
        service.update_data_availability(
            symbol="NEWSTOCK",
            timeframe="1m",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            row_count=10000,
            file_path="/data/NEWSTOCK.parquet",
            file_size_mb=5.5,
        )
        
        # Should add instrument and availability
        assert mock_session.add.call_count >= 2

    def test_get_symbols_with_data(self, mock_database):
        """Test get_symbols_with_data."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_session.execute.return_value.scalars.return_value.all.return_value = ["RELIANCE", "TCS"]
        
        service = RegistryService(database=mock_db)
        results = service.get_symbols_with_data("1m")
        
        assert results == ["RELIANCE", "TCS"]


class TestRegistryServiceLogging:
    """Tests for logging operations."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        mock_session = MagicMock()
        mock_db.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.session.return_value.__exit__ = MagicMock(return_value=False)
        
        return mock_db, mock_session

    def test_log_data_load_success(self, mock_database):
        """Test logging a successful data load."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import Instrument
        
        mock_db, mock_session = mock_database
        mock_instrument = MagicMock(spec=Instrument)
        mock_instrument.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_instrument
        
        service = RegistryService(database=mock_db)
        service.log_data_load(
            symbol="RELIANCE",
            status="SUCCESS",
            timeframe="1m",
            rows_loaded=10000,
            load_time_ms=50,
            cache_hit=False,
        )
        
        mock_session.add.assert_called_once()

    def test_log_data_load_cache_hit(self, mock_database):
        """Test logging a cache hit."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        service = RegistryService(database=mock_db)
        service.log_data_load(
            symbol="RELIANCE",
            status="SUCCESS",
            cache_hit=True,
        )
        
        mock_session.add.assert_called_once()

    def test_log_data_load_error(self, mock_database):
        """Test logging an error."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        service = RegistryService(database=mock_db)
        service.log_data_load(
            symbol="RELIANCE",
            status="ERROR",
            error_message="Connection timeout",
        )
        
        mock_session.add.assert_called_once()

    def test_get_recent_loads_no_filter(self, mock_database):
        """Test get_recent_loads without symbol filter."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import DataLoadLog
        
        mock_db, mock_session = mock_database
        mock_logs = [MagicMock(spec=DataLoadLog) for _ in range(3)]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_logs
        
        service = RegistryService(database=mock_db)
        results = service.get_recent_loads(limit=50)
        
        assert len(results) == 3

    def test_get_recent_loads_with_filter(self, mock_database):
        """Test get_recent_loads with symbol filter."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.models import DataLoadLog
        
        mock_db, mock_session = mock_database
        mock_logs = [MagicMock(spec=DataLoadLog)]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_logs
        
        service = RegistryService(database=mock_db)
        results = service.get_recent_loads(symbol="RELIANCE", limit=10)
        
        assert len(results) == 1


class TestRegistryServiceSync:
    """Tests for sync operations."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        mock_session = MagicMock()
        mock_db.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.session.return_value.__exit__ = MagicMock(return_value=False)
        
        return mock_db, mock_session

    def test_sync_from_filesystem(self, mock_database):
        """Test sync_from_filesystem."""
        from hermes_data.registry.service import RegistryService
        import polars as pl
        
        mock_db, mock_session = mock_database
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        mock_provider = MagicMock()
        mock_provider.list_symbols.return_value = ["STOCK1", "STOCK2"]
        mock_provider.get_date_range.return_value = ("2024-01-01", "2024-12-31")
        mock_provider.load.return_value = pl.DataFrame({"close": [1, 2, 3]})
        
        service = RegistryService(database=mock_db)
        count = service.sync_from_filesystem(mock_provider, timeframe="1m")
        
        assert count == 2

    def test_sync_from_filesystem_with_errors(self, mock_database):
        """Test sync_from_filesystem when some symbols fail."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        
        mock_provider = MagicMock()
        mock_provider.list_symbols.return_value = ["GOOD", "BAD"]
        mock_provider.get_date_range.side_effect = [("2024-01-01", "2024-12-31"), Exception("No data")]
        mock_provider.load.return_value = MagicMock(__len__=lambda s: 100)
        
        # Make get_or_create work for the first call
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        service = RegistryService(database=mock_db)
        count = service.sync_from_filesystem(mock_provider)
        
        # Only one should succeed
        assert count == 1


class TestRegistryServiceHealth:
    """Tests for health check operations."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        mock_session = MagicMock()
        mock_db.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.session.return_value.__exit__ = MagicMock(return_value=False)
        
        return mock_db, mock_session

    def test_health_check_healthy(self, mock_database):
        """Test health_check when database is healthy."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_db.health_check.return_value = True
        mock_session.query.return_value.scalar.side_effect = [10, 5]
        
        service = RegistryService(database=mock_db)
        health = service.health_check()
        
        assert health["healthy"] is True
        assert health["database"] == "connected"
        assert health["instruments"] == 10
        assert health["availability_records"] == 5

    def test_health_check_unhealthy(self, mock_database):
        """Test health_check when database is unhealthy."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, mock_session = mock_database
        mock_db.health_check.return_value = False
        mock_session.query.return_value.scalar.side_effect = [0, 0]
        
        service = RegistryService(database=mock_db)
        health = service.health_check()
        
        assert health["healthy"] is False
        assert health["database"] == "disconnected"

    def test_health_check_error(self, mock_database):
        """Test health_check when exception occurs."""
        from hermes_data.registry.service import RegistryService
        
        mock_db, _ = mock_database
        mock_db.health_check.side_effect = Exception("Connection error")
        
        service = RegistryService(database=mock_db)
        health = service.health_check()
        
        assert health["healthy"] is False
        assert health["database"] == "error"
        assert "Connection error" in health["error"]


class TestRegistryServiceInitialization:
    """Tests for registry service initialization."""

    def test_initialize_creates_tables(self):
        """Test that initialize creates tables."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        service = RegistryService(database=mock_db)
        
        service.initialize()
        
        mock_db.create_tables.assert_called_once()
        assert service._initialized is True

    def test_initialize_only_once(self):
        """Test that initialize only runs once."""
        from hermes_data.registry.service import RegistryService
        from hermes_data.registry.database import Database
        
        mock_db = MagicMock(spec=Database)
        service = RegistryService(database=mock_db)
        
        service.initialize()
        service.initialize()  # Second call
        
        # Should only be called once
        assert mock_db.create_tables.call_count == 1

    def test_database_property_creates_if_none(self):
        """Test database property creates database if not provided."""
        from hermes_data.registry.service import RegistryService
        from hermes_data import DataSettings
        
        with patch("hermes_data.registry.service.get_database") as mock_get_db:
            mock_get_db.return_value = MagicMock()
            
            settings = DataSettings(
                database_url="postgresql://test:test@localhost/test",
                registry_enabled=True,
            )
            service = RegistryService(settings=settings)
            
            # Access database property
            _ = service.database
            
            mock_get_db.assert_called_once_with(settings)
