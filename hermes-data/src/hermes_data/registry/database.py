"""Database connection and session management."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ..config import DataSettings, get_settings
from .models import Base

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager for PostgreSQL."""
    
    def __init__(self, settings: Optional[DataSettings] = None):
        """Initialize database connection.
        
        Args:
            settings: Optional DataSettings. Uses get_settings() if not provided.
        """
        self.settings = settings or get_settings()
        self._engine = None
        self._session_factory: Optional[sessionmaker[Session]] = None
    
    @property
    def engine(self):
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.settings.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Verify connections before use
                pool_size=5,
                max_overflow=10,
            )
            logger.info(f"Database engine created for: {self._mask_url(self.settings.database_url)}")
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker[Session]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory
    
    def _mask_url(self, url: str) -> str:
        """Mask password in database URL for logging."""
        import re
        return re.sub(r':([^:@]+)@', ':***@', url)
    
    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/verified")
    
    def drop_tables(self) -> None:
        """Drop all tables. USE WITH CAUTION!"""
        Base.metadata.drop_all(self.engine)
        logger.warning("All database tables dropped")
    
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions.
        
        Usage:
            with db.session() as session:
                session.add(instrument)
                session.commit()
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """Get a new session (caller is responsible for closing)."""
        return self.session_factory()
    
    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            with self.session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance (lazy initialization)
_database: Optional[Database] = None


def get_database(settings: Optional[DataSettings] = None) -> Database:
    """Get the global database instance."""
    global _database
    if _database is None:
        _database = Database(settings)
    return _database


def reset_database() -> None:
    """Reset the global database instance (for testing)."""
    global _database
    _database = None
