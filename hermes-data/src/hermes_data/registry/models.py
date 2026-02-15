"""SQLAlchemy models for the data registry."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class Instrument(Base):
    """Represents a tradeable instrument (stock, index, etc.)."""
    
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    exchange = Column(String(50), nullable=True)
    instrument_type = Column(String(50), nullable=True)  # EQUITY, INDEX, FUTURE, OPTION
    sector = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    data_availability = relationship(
        "DataAvailability",
        back_populates="instrument",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Instrument(symbol='{self.symbol}', exchange='{self.exchange}')>"


class DataAvailability(Base):
    """Tracks data availability for each instrument and timeframe."""
    
    __tablename__ = "data_availability"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    
    # Date Range
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Quality Metrics
    row_count = Column(Integer, nullable=True)
    missing_days = Column(Integer, default=0)
    data_quality_score = Column(Float, default=1.0)  # 0.0 - 1.0
    
    # Storage Info
    file_path = Column(String(500), nullable=True)
    file_size_mb = Column(Float, nullable=True)
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_verified = Column(DateTime, nullable=True)
    
    # Relationships
    instrument = relationship("Instrument", back_populates="data_availability")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("instrument_id", "timeframe", name="uq_instrument_timeframe"),
        Index("ix_data_availability_timeframe", "timeframe"),
    )

    def __repr__(self) -> str:
        return (
            f"<DataAvailability(instrument_id={self.instrument_id}, "
            f"timeframe='{self.timeframe}', rows={self.row_count})>"
        )


class DataLoadLog(Base):
    """Logs data load operations for auditing and debugging."""
    
    __tablename__ = "data_load_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=True)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=True)
    
    # Request Info
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    rows_loaded = Column(Integer, nullable=True)
    
    # Performance
    load_time_ms = Column(Integer, nullable=True)
    cache_hit = Column(Integer, default=0)  # 0 = miss, 1 = hit
    
    # Status
    status = Column(String(20), nullable=False)  # SUCCESS, ERROR, PARTIAL
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for querying recent loads
    __table_args__ = (
        Index("ix_data_load_logs_created_at", "created_at"),
        Index("ix_data_load_logs_symbol", "symbol"),
    )

    def __repr__(self) -> str:
        return f"<DataLoadLog(symbol='{self.symbol}', status='{self.status}')>"


class ScanResultCache(Base):
    """Cached scan results — one row per (symbol, strategy, params_hash)."""

    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    strategy = Column(String(100), nullable=False)
    params_hash = Column(String(64), nullable=False)
    mode = Column(String(10), default="vector")

    # Result Data
    metrics = Column(JSON, nullable=False)
    signal_count = Column(Integer, default=0)
    last_signal = Column(String(10), nullable=True)
    last_signal_time = Column(Integer, nullable=True)

    # Cache Management
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    scan_time_ms = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_scan_results_lookup", "symbol", "strategy", "params_hash"),
        Index("ix_scan_results_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<ScanResultCache(symbol='{self.symbol}', strategy='{self.strategy}')>"
