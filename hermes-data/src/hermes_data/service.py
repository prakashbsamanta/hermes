"""Main DataService facade for unified data access."""

import logging
import time
from datetime import datetime
from typing import List, Optional, Tuple

import polars as pl

from .cache.base import CacheProvider
from .cache.memory import MemoryCache
from .config import DataSettings, get_settings
from .providers.base import DataProvider
from .providers.local import LocalFileProvider

logger = logging.getLogger(__name__)


class DataService:
    """Unified data access facade.
    
    Combines data provider, caching layer, and optional registry into a single interface.
    This is the main entry point for all data operations.
    
    Example:
        >>> from hermes_data import DataService
        >>> service = DataService()
        >>> df = service.get_market_data(["RELIANCE"], "2024-01-01", "2024-12-31")
        >>> symbols = service.list_instruments()
    """

    def __init__(
        self,
        provider: Optional[DataProvider] = None,
        cache: Optional[CacheProvider] = None,
        settings: Optional[DataSettings] = None,
        enable_registry: Optional[bool] = None,
    ):
        """Initialize the DataService.
        
        Args:
            provider: Optional custom data provider. If not provided,
                      creates one based on settings.
            cache: Optional custom cache provider. If not provided,
                   creates a MemoryCache based on settings.
            settings: Optional settings. Uses get_settings() if not provided.
            enable_registry: Override registry_enabled from settings.
        """
        self.settings = settings or get_settings()
        self.provider = provider or self._create_provider()
        self.cache = cache or self._create_cache()
        
        # Registry (optional, for tracking metadata and logs)
        registry_enabled = enable_registry if enable_registry is not None else self.settings.registry_enabled
        self._registry = None
        if registry_enabled:
            self._registry = self._create_registry()

    def _create_provider(self) -> DataProvider:
        """Create a data provider based on settings."""
        if self.settings.storage_provider == "local":
            data_path = self.settings.get_data_path()
            logger.info(f"Using LocalFileProvider with path: {data_path}")
            return LocalFileProvider(data_path)
        
        # Future: Add S3, GCS providers here
        raise ValueError(f"Unknown storage provider: {self.settings.storage_provider}")

    def _create_cache(self) -> Optional[CacheProvider]:
        """Create a cache provider based on settings."""
        if not self.settings.cache_enabled:
            logger.info("Caching disabled")
            return None
        
        logger.info(f"Using MemoryCache with {self.settings.cache_max_size_mb}MB limit")
        return MemoryCache(max_size_mb=self.settings.cache_max_size_mb)

    def _create_registry(self):
        """Create and initialize the registry service."""
        try:
            from .registry.service import RegistryService
            registry = RegistryService(settings=self.settings)
            registry.initialize()
            logger.info("Registry service initialized")
            return registry
        except Exception as e:
            logger.warning(f"Failed to initialize registry: {e}. Continuing without registry.")
            return None

    @property
    def registry(self):
        """Access the registry service (may be None if disabled/unavailable)."""
        return self._registry

    def get_market_data(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
    ) -> pl.DataFrame:
        """Load market data for given symbols.
        
        Args:
            symbols: List of instrument symbols
            start_date: Optional start date "YYYY-MM-DD"
            end_date: Optional end date "YYYY-MM-DD"
            use_cache: Whether to use cache (default: True)
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            ValueError: If no data available for symbols
            FileNotFoundError: If data files not found
        """
        symbols = [s.upper() for s in symbols]
        start_time = time.time()
        
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(symbols, start_date, end_date)
            if cached is not None:
                logger.debug(f"Returning cached data for {symbols}")
                self._log_load(
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    rows=len(cached),
                    load_time_ms=int((time.time() - start_time) * 1000),
                    cache_hit=True,
                )
                return cached

        # Load from provider
        logger.info(f"Loading data for {symbols} ({start_date} to {end_date})")
        try:
            data = self.provider.load(symbols, start_date, end_date)
            
            # Cache the result
            if use_cache and self.cache:
                self.cache.set(symbols, start_date, end_date, data)
            
            # Log success
            self._log_load(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                rows=len(data),
                load_time_ms=int((time.time() - start_time) * 1000),
                cache_hit=False,
            )
            
            return data
            
        except Exception as e:
            # Log failure
            self._log_load(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                rows=0,
                load_time_ms=int((time.time() - start_time) * 1000),
                cache_hit=False,
                status="ERROR",
                error=str(e),
            )
            raise

    def _log_load(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
        rows: int,
        load_time_ms: int,
        cache_hit: bool,
        status: str = "SUCCESS",
        error: Optional[str] = None,
    ) -> None:
        """Log a data load to the registry if available."""
        if not self._registry:
            return
        
        try:
            for symbol in symbols:
                self._registry.log_data_load(
                    symbol=symbol,
                    status=status,
                    timeframe="1m",  # Default for now
                    start_date=datetime.strptime(start_date, "%Y-%m-%d") if start_date else None,
                    end_date=datetime.strptime(end_date, "%Y-%m-%d") if end_date else None,
                    rows_loaded=rows // len(symbols),  # Approximate split
                    load_time_ms=load_time_ms,
                    cache_hit=cache_hit,
                    error_message=error,
                )
        except Exception as e:
            logger.debug(f"Failed to log data load: {e}")

    def list_instruments(self) -> List[str]:
        """List all available instrument symbols.
        
        Returns:
            Sorted list of symbol names
        """
        return self.provider.list_symbols()

    def get_date_range(self, symbol: str) -> Tuple[str, str]:
        """Get available date range for a symbol.
        
        Args:
            symbol: Instrument symbol
            
        Returns:
            Tuple of (start_date, end_date)
        """
        return self.provider.get_date_range(symbol.upper())

    def get_instrument_info(self, symbol: str) -> Optional[dict]:
        """Get detailed instrument information from registry.
        
        Args:
            symbol: Instrument symbol
            
        Returns:
            Dictionary with instrument details or None
        """
        if not self._registry:
            # Fallback to basic info from provider
            try:
                start, end = self.get_date_range(symbol)
                return {
                    "symbol": symbol.upper(),
                    "start_date": start,
                    "end_date": end,
                }
            except Exception:
                return None
        
        instrument = self._registry.get_instrument(symbol)
        if not instrument:
            return None
        
        availability = self._registry.get_data_availability(symbol)
        
        return {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "exchange": instrument.exchange,
            "instrument_type": instrument.instrument_type,
            "sector": instrument.sector,
            "data_available": availability is not None,
            "start_date": availability.start_date.isoformat() if availability and availability.start_date else None,
            "end_date": availability.end_date.isoformat() if availability and availability.end_date else None,
            "row_count": availability.row_count if availability else None,
        }

    def search_instruments(self, query: str, limit: int = 20) -> List[dict]:
        """Search instruments by symbol or name.
        
        Args:
            query: Search query string
            limit: Maximum results
            
        Returns:
            List of matching instruments as dictionaries
        """
        if not self._registry:
            # Fallback: filter provider symbols
            symbols = self.provider.list_symbols()
            matches = [s for s in symbols if query.upper() in s.upper()]
            return [{"symbol": s} for s in matches[:limit]]
        
        instruments = self._registry.search_instruments(query, limit)
        return [
            {
                "symbol": inst.symbol,
                "name": inst.name,
                "exchange": inst.exchange,
            }
            for inst in instruments
        ]

    def sync_registry(self) -> int:
        """Sync registry with filesystem data.
        
        Returns:
            Number of instruments synced
        """
        if not self._registry:
            logger.warning("Registry not available, cannot sync")
            return 0
        
        return self._registry.sync_from_filesystem(self.provider)

    def health_check(self) -> dict:
        """Check health of data layer components.
        
        Returns:
            Dictionary with health status of provider, cache, and registry
        """
        result = {
            "provider": {
                "type": type(self.provider).__name__,
                "healthy": self.provider.health_check(),
            },
            "cache": None,
            "registry": None,
        }
        
        if self.cache:
            result["cache"] = {
                "type": type(self.cache).__name__,
                "stats": self.cache.stats(),
            }
        
        if self._registry:
            result["registry"] = self._registry.health_check()
        
        return result

    def clear_cache(self) -> None:
        """Clear the data cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Data cache cleared")
