"""Registry service for managing instrument metadata and data availability."""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, or_, select

from ..config import DataSettings, get_settings
from .database import Database, get_database
from .models import DataAvailability, DataLoadLog, Instrument

logger = logging.getLogger(__name__)


class RegistryService:
    """Service for managing the data registry.
    
    Provides CRUD operations for instruments and data availability tracking.
    """
    
    def __init__(
        self,
        database: Optional[Database] = None,
        settings: Optional[DataSettings] = None,
    ):
        """Initialize the registry service.
        
        Args:
            database: Optional Database instance.
            settings: Optional DataSettings.
        """
        self.settings = settings or get_settings()
        self._database = database
        self._initialized = False
    
    @property
    def database(self) -> Database:
        """Get the database instance."""
        if self._database is None:
            self._database = get_database(self.settings)
        return self._database
    
    def initialize(self) -> None:
        """Initialize the registry (create tables if needed)."""
        if not self._initialized:
            self.database.create_tables()
            self._initialized = True
    
    # ==================== Instrument Operations ====================
    
    def get_instrument(self, symbol: str) -> Optional[Instrument]:
        """Get an instrument by symbol.
        
        Args:
            symbol: Instrument symbol (case-insensitive)
            
        Returns:
            Instrument or None if not found
        """
        with self.database.session() as session:
            stmt = select(Instrument).where(
                func.upper(Instrument.symbol) == symbol.upper()
            )
            return session.execute(stmt).scalar_one_or_none()
    
    def get_or_create_instrument(
        self,
        symbol: str,
        name: Optional[str] = None,
        exchange: Optional[str] = None,
        instrument_type: Optional[str] = None,
    ) -> Instrument:
        """Get existing instrument or create a new one.
        
        Args:
            symbol: Instrument symbol
            name: Optional display name
            exchange: Optional exchange code
            instrument_type: Optional type (EQUITY, INDEX, etc.)
            
        Returns:
            Instrument instance
        """
        with self.database.session() as session:
            instrument = session.query(Instrument).filter(
                func.upper(Instrument.symbol) == symbol.upper()
            ).first()
            
            if instrument is None:
                instrument = Instrument(
                    symbol=symbol.upper(),
                    name=name,
                    exchange=exchange,
                    instrument_type=instrument_type,
                )
                session.add(instrument)
                session.flush()  # Get the ID
                logger.info(f"Created new instrument: {symbol}")
            
            # Detach from session for return
            session.expunge(instrument)
            return instrument
    
    def search_instruments(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Instrument]:
        """Search instruments by symbol or name.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching instruments
        """
        with self.database.session() as session:
            pattern = f"%{query}%"
            stmt = (
                select(Instrument)
                .where(
                    or_(
                        Instrument.symbol.ilike(pattern),
                        Instrument.name.ilike(pattern),
                    )
                )
                .order_by(Instrument.symbol)
                .limit(limit)
            )
            result = session.execute(stmt).scalars().all()
            # Detach from session
            for inst in result:
                session.expunge(inst)
            return list(result)
    
    def list_all_instruments(self) -> List[Instrument]:
        """List all registered instruments.
        
        Returns:
            List of all instruments
        """
        with self.database.session() as session:
            stmt = select(Instrument).order_by(Instrument.symbol)
            result = session.execute(stmt).scalars().all()
            for inst in result:
                session.expunge(inst)
            return list(result)
    
    # ==================== Data Availability Operations ====================
    
    def get_data_availability(
        self,
        symbol: str,
        timeframe: str = "1m",
    ) -> Optional[DataAvailability]:
        """Get data availability for a symbol and timeframe.
        
        Args:
            symbol: Instrument symbol
            timeframe: Data timeframe (e.g., "1m", "1h", "1d")
            
        Returns:
            DataAvailability or None
        """
        with self.database.session() as session:
            stmt = (
                select(DataAvailability)
                .join(Instrument)
                .where(
                    func.upper(Instrument.symbol) == symbol.upper(),
                    DataAvailability.timeframe == timeframe,
                )
            )
            result = session.execute(stmt).scalar_one_or_none()
            if result:
                session.expunge(result)
            return result
    
    def update_data_availability(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        row_count: int,
        file_path: Optional[str] = None,
        file_size_mb: Optional[float] = None,
    ) -> DataAvailability:
        """Update or create data availability record.
        
        Args:
            symbol: Instrument symbol
            timeframe: Data timeframe
            start_date: Earliest data timestamp
            end_date: Latest data timestamp
            row_count: Total number of rows
            file_path: Optional path to data file
            file_size_mb: Optional file size in MB
            
        Returns:
            Updated DataAvailability record
        """
        with self.database.session() as session:
            # Get or create instrument
            instrument = session.query(Instrument).filter(
                func.upper(Instrument.symbol) == symbol.upper()
            ).first()
            
            if instrument is None:
                instrument = Instrument(symbol=symbol.upper())
                session.add(instrument)
                session.flush()
            
            # Get or create availability record
            availability = session.query(DataAvailability).filter(
                DataAvailability.instrument_id == instrument.id,
                DataAvailability.timeframe == timeframe,
            ).first()
            
            if availability is None:
                availability = DataAvailability(
                    instrument_id=instrument.id,
                    timeframe=timeframe,
                )
                session.add(availability)
            
            # Update fields
            availability.start_date = start_date  # type: ignore
            availability.end_date = end_date  # type: ignore
            availability.row_count = row_count  # type: ignore
            availability.file_path = file_path  # type: ignore
            availability.file_size_mb = file_size_mb  # type: ignore
            availability.last_updated = datetime.utcnow()  # type: ignore
            
            session.flush()
            session.expunge(availability)
            
            logger.debug(f"Updated availability for {symbol}/{timeframe}: {row_count} rows")
            return availability
    
    def get_symbols_with_data(self, timeframe: str = "1m") -> List[str]:
        """Get list of symbols that have data for a timeframe.
        
        Args:
            timeframe: Data timeframe
            
        Returns:
            List of symbol names
        """
        with self.database.session() as session:
            stmt = (
                select(Instrument.symbol)
                .join(DataAvailability)
                .where(DataAvailability.timeframe == timeframe)
                .order_by(Instrument.symbol)
            )
            result = session.execute(stmt).scalars().all()
            return list(result)
    
    # ==================== Logging Operations ====================
    
    def log_data_load(
        self,
        symbol: str,
        status: str,
        timeframe: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        rows_loaded: Optional[int] = None,
        load_time_ms: Optional[int] = None,
        cache_hit: bool = False,
        error_message: Optional[str] = None,
    ) -> DataLoadLog:
        """Log a data load operation.
        
        Args:
            symbol: Symbol that was loaded
            status: Load status (SUCCESS, ERROR, PARTIAL)
            timeframe: Optional timeframe
            start_date: Optional start date requested
            end_date: Optional end date requested
            rows_loaded: Number of rows loaded
            load_time_ms: Load time in milliseconds
            cache_hit: Whether data came from cache
            error_message: Optional error message
            
        Returns:
            Created log entry
        """
        with self.database.session() as session:
            # Try to get instrument ID
            instrument = session.query(Instrument).filter(
                func.upper(Instrument.symbol) == symbol.upper()
            ).first()
            
            log_entry = DataLoadLog(
                instrument_id=instrument.id if instrument else None,
                symbol=symbol.upper(),
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                rows_loaded=rows_loaded,
                load_time_ms=load_time_ms,
                cache_hit=1 if cache_hit else 0,
                status=status,
                error_message=error_message,
            )
            session.add(log_entry)
            session.flush()
            session.expunge(log_entry)
            return log_entry
    
    def get_recent_loads(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[DataLoadLog]:
        """Get recent data load logs.
        
        Args:
            symbol: Optional symbol filter
            limit: Maximum logs to return
            
        Returns:
            List of recent log entries
        """
        with self.database.session() as session:
            stmt = select(DataLoadLog).order_by(DataLoadLog.created_at.desc())
            
            if symbol:
                stmt = stmt.where(
                    func.upper(DataLoadLog.symbol) == symbol.upper()
                )
            
            stmt = stmt.limit(limit)
            result = session.execute(stmt).scalars().all()
            for log in result:
                session.expunge(log)
            return list(result)
    
    # ==================== Sync Operations ====================
    
    def sync_from_filesystem(
        self,
        provider,
        timeframe: str = "1m",
    ) -> int:
        """Sync registry with data available in the filesystem.
        
        Args:
            provider: DataProvider instance to scan
            timeframe: Timeframe to register
            
        Returns:
            Number of instruments synchronized
        """
        symbols = provider.list_symbols()
        count = 0
        
        for symbol in symbols:
            try:
                start_str, end_str = provider.get_date_range(symbol)
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                
                # Load to get row count
                df = provider.load([symbol], start_str, end_str)
                row_count = len(df)
                
                # Update registry
                self.get_or_create_instrument(symbol)
                self.update_data_availability(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    row_count=row_count,
                )
                count += 1
                
            except Exception as e:
                logger.warning(f"Failed to sync {symbol}: {e}")
                continue
        
        logger.info(f"Synced {count} instruments from filesystem")
        return count
    
    # ==================== Health ====================
    
    def health_check(self) -> dict:
        """Check registry health.
        
        Returns:
            Health status dictionary
        """
        try:
            db_healthy = self.database.health_check()
            
            with self.database.session() as session:
                instrument_count = session.query(func.count(Instrument.id)).scalar()
                availability_count = session.query(func.count(DataAvailability.id)).scalar()
            
            return {
                "healthy": db_healthy,
                "database": "connected" if db_healthy else "disconnected",
                "instruments": instrument_count,
                "availability_records": availability_count,
            }
        except Exception as e:
            return {
                "healthy": False,
                "database": "error",
                "error": str(e),
            }
