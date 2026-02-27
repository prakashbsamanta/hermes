"""PostgreSQL UNLOGGED table cache implementation.

Uses Arrow IPC format for zero-copy serialization of Polars DataFrames
into a PostgreSQL UNLOGGED table for near-memory write speeds with
shared-nothing horizontal scalability.
"""

import hashlib
import io
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, cast

import polars as pl
from sqlalchemy import delete, text, update
from sqlalchemy.orm import Session

from .base import CacheProvider

logger = logging.getLogger(__name__)


class PostgresCache(CacheProvider):
    """Distributed cache backed by PostgreSQL UNLOGGED tables.

    Key features:
    - Uses Arrow IPC binary serialization for zero-copy DataFrame storage
    - UNLOGGED tables bypass WAL for maximum write throughput
    - Supports TTL-based expiry and LRU eviction
    - Thread-safe via database transactions
    - Enables stateless horizontal scaling of the FastAPI backend
    """

    def __init__(
        self,
        session_factory,
        max_size_mb: float = 2048,
        ttl_hours: int = 24,
    ):
        """Initialize the PostgreSQL cache.

        Args:
            session_factory: SQLAlchemy session factory (from Database)
            max_size_mb: Maximum total cache size in megabytes
            ttl_hours: Default TTL for cache entries in hours
        """
        self.session_factory = session_factory
        self.max_size_mb = max_size_mb
        self.ttl_hours = ttl_hours
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> str:
        """Create a deterministic cache key."""
        raw = f"{','.join(sorted(symbols))}:{start_date or ''}:{end_date or ''}"
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()

    @staticmethod
    def _serialize(df: pl.DataFrame) -> bytes:
        """Serialize a Polars DataFrame to Arrow IPC binary."""
        buf = io.BytesIO()
        df.write_ipc(buf)
        return buf.getvalue()

    @staticmethod
    def _deserialize(data: bytes) -> pl.DataFrame:
        """Deserialize Arrow IPC binary to a Polars DataFrame."""
        return pl.read_ipc(io.BytesIO(data))

    def get(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Optional[pl.DataFrame]:
        """Retrieve cached data if available."""
        # Lazy import to avoid circular dependency
        from ..registry.models import DataFrameCache

        key = self._make_key(symbols, start_date, end_date)
        session: Session = self.session_factory()

        try:
            row = (
                session.query(DataFrameCache)
                .filter(DataFrameCache.cache_key == key)
                .first()
            )

            if row is None:
                self._misses += 1
                logger.debug(f"PG Cache MISS for key {key[:8]}...")
                return None

            # Check TTL expiry
            if row.expires_at and row.expires_at < datetime.now(timezone.utc):
                logger.debug(f"PG Cache EXPIRED for key {key[:8]}...")
                session.delete(row)
                session.commit()
                self._misses += 1
                return None

            # Update LRU tracking
            session.execute(
                update(DataFrameCache)
                .where(DataFrameCache.id == row.id)
                .values(
                    last_accessed_at=datetime.now(timezone.utc),
                    hit_count=DataFrameCache.hit_count + 1,
                )
            )
            session.commit()

            self._hits += 1
            logger.debug(f"PG Cache HIT for key {key[:8]}...")
            return self._deserialize(cast(bytes, row.payload))

        except Exception as e:
            session.rollback()
            logger.warning(f"PG Cache get failed: {e}")
            self._misses += 1
            return None
        finally:
            session.close()

    def set(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
        data: pl.DataFrame,
    ) -> None:
        """Store data in cache with LRU eviction."""
        from ..registry.models import DataFrameCache

        key = self._make_key(symbols, start_date, end_date)
        payload = self._serialize(data)
        size_mb = len(payload) / (1024 * 1024)

        if size_mb > self.max_size_mb:
            logger.warning(
                f"Data too large to cache: {size_mb:.1f}MB > {self.max_size_mb}MB limit"
            )
            return

        session: Session = self.session_factory()

        try:
            # Delete existing entry if present
            session.execute(
                delete(DataFrameCache).where(DataFrameCache.cache_key == key)
            )

            # Evict expired entries
            session.execute(
                delete(DataFrameCache).where(
                    DataFrameCache.expires_at < datetime.now(timezone.utc)
                )
            )

            # Check total size and evict LRU if needed
            total_size_result = session.execute(
                text("SELECT COALESCE(SUM(payload_size_mb), 0) FROM dataframe_cache")
            )
            total_size = float(total_size_result.scalar() or 0)

            while total_size + size_mb > self.max_size_mb:
                # Evict oldest accessed entry
                oldest = (
                    session.query(DataFrameCache)
                    .order_by(DataFrameCache.last_accessed_at.asc())
                    .first()
                )
                if oldest is None:
                    break
                total_size -= cast(float, oldest.payload_size_mb)
                session.delete(oldest)
                logger.debug(f"Evicted PG cache entry {oldest.cache_key[:8]}...")

            # Insert new entry
            now = datetime.now(timezone.utc)
            symbol_str = symbols[0] if len(symbols) == 1 else ",".join(sorted(symbols))

            entry = DataFrameCache(
                cache_key=key,
                symbol=symbol_str,
                start_date=start_date,
                end_date=end_date,
                payload=payload,
                payload_size_mb=size_mb,
                row_count=len(data),
                created_at=now,
                last_accessed_at=now,
                expires_at=now + timedelta(hours=self.ttl_hours),
                hit_count=0,
            )
            session.add(entry)
            session.commit()

            logger.debug(
                f"PG Cached {size_mb:.1f}MB for key {key[:8]}... "
                f"({len(data)} rows, symbol={symbol_str})"
            )

        except Exception as e:
            session.rollback()
            logger.warning(f"PG Cache set failed: {e}")
        finally:
            session.close()

    def clear(self) -> None:
        """Clear all cached data."""
        from ..registry.models import DataFrameCache

        session: Session = self.session_factory()
        try:
            session.execute(delete(DataFrameCache))
            session.commit()
            self._hits = 0
            self._misses = 0
            logger.info("PG Cache cleared")
        except Exception as e:
            session.rollback()
            logger.warning(f"PG Cache clear failed: {e}")
        finally:
            session.close()

    def stats(self) -> dict:
        """Get cache statistics."""

        session: Session = self.session_factory()
        try:
            result = session.execute(
                text(
                    "SELECT COUNT(*), COALESCE(SUM(payload_size_mb), 0), "
                    "COALESCE(SUM(hit_count), 0) FROM dataframe_cache"
                )
            )
            row = result.fetchone()
            entries = int(row[0]) if row else 0
            size_mb = float(row[1]) if row else 0.0
            total_hits_db = int(row[2]) if row else 0

            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "backend": "postgres_unlogged",
                "entries": entries,
                "size_mb": round(size_mb, 2),
                "max_size_mb": self.max_size_mb,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 1),
                "total_db_hits": total_hits_db,
            }
        except Exception as e:
            logger.warning(f"PG Cache stats failed: {e}")
            return {
                "backend": "postgres_unlogged",
                "error": str(e),
            }
        finally:
            session.close()
