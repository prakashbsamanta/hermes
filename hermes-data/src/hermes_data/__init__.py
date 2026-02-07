"""Hermes Data - Separated data layer for Hermes backtesting platform.

This package provides:
- Abstract DataProvider interface for pluggable storage backends
- LocalFileProvider for loading data from local Parquet files
- MemoryCache for efficient caching with LRU eviction
- DataService facade for unified data access
- RegistryService for instrument metadata and data availability tracking
"""

from .config import DataSettings, get_settings
from .service import DataService
from .providers.base import DataProvider
from .providers.local import LocalFileProvider
from .cache.base import CacheProvider
from .cache.memory import MemoryCache

# Registry exports (may fail if database not configured)
try:
    from .registry import Base, Instrument, DataAvailability, RegistryService  # noqa: F401
    from .registry.database import Database, get_database  # noqa: F401
    _registry_available = True
except ImportError:
    _registry_available = False

__version__ = "0.2.0"

__all__ = [
    # Core
    "DataService",
    "DataSettings",
    "get_settings",
    # Providers
    "DataProvider",
    "LocalFileProvider",
    # Cache
    "CacheProvider",
    "MemoryCache",
]

# Add registry exports if available
if _registry_available:
    __all__.extend([
        "Base",
        "Instrument",
        "DataAvailability",
        "RegistryService",
        "Database",
        "get_database",
    ])
