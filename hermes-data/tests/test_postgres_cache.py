import pytest
import datetime
from unittest.mock import MagicMock, patch
import polars as pl
import hashlib

from hermes_data.cache.postgres import PostgresCache

@pytest.fixture
def mock_session_factory():
    def factory():
        return MagicMock()
    return factory

@pytest.fixture
def pg_cache(mock_session_factory):
    return PostgresCache(session_factory=mock_session_factory, max_size_mb=2048, ttl_hours=24)

def test_make_key():
    symbols = ["AAPL", "MSFT"]
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    key = PostgresCache._make_key(symbols, start_date, end_date)
    expected_raw = "AAPL,MSFT:2024-01-01:2024-12-31"
    assert key == hashlib.md5(expected_raw.encode(), usedforsecurity=False).hexdigest()

def test_serialize_deserialize():
    df = pl.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
    # Mocking read_ipc within deserialize
    payload = PostgresCache._serialize(df)
    result_df = PostgresCache._deserialize(payload)
    assert result_df.shape == df.shape
    assert result_df.columns == df.columns

def test_get_cache_miss(pg_cache):
    # Mock query to return None
    session_mock = MagicMock()
    session_mock.query.return_value.filter.return_value.first.return_value = None
    pg_cache.session_factory = lambda: session_mock

    result = pg_cache.get(["AAPL"], "2024-01-01", "2024-01-31")
    assert result is None
    assert pg_cache._misses == 1

@patch("hermes_data.cache.postgres.datetime")
def test_get_cache_expired(mock_datetime, pg_cache):
    mock_datetime.now.return_value = datetime.datetime.now(datetime.timezone.utc)
    
    session_mock = MagicMock()
    mock_row = MagicMock()
    # Expired 1 hour ago
    mock_row.expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    session_mock.query.return_value.filter.return_value.first.return_value = mock_row
    pg_cache.session_factory = lambda: session_mock

    result = pg_cache.get(["AAPL"], "2024-01-01", "2024-01-31")
    assert result is None
    assert pg_cache._misses == 1
    session_mock.delete.assert_called_once_with(mock_row)
    session_mock.commit.assert_called_once()

@patch("hermes_data.cache.postgres.datetime")
@patch.object(PostgresCache, '_deserialize')
def test_get_cache_hit(mock_deserialize, mock_datetime, pg_cache):
    mock_datetime.now.return_value = datetime.datetime.now(datetime.timezone.utc)
    
    session_mock = MagicMock()
    mock_row = MagicMock()
    mock_row.id = 1
    mock_row.expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    mock_row.payload = b"testdata"
    session_mock.query.return_value.filter.return_value.first.return_value = mock_row
    pg_cache.session_factory = lambda: session_mock

    mock_df = pl.DataFrame({"a": [1]})
    mock_deserialize.return_value = mock_df

    result = pg_cache.get(["AAPL"], "2024-01-01", "2024-01-31")
    assert result is mock_df
    assert pg_cache._hits == 1
    session_mock.execute.assert_called_once()
    session_mock.commit.assert_called_once()
    mock_deserialize.assert_called_once_with(b"testdata")

def test_get_exception(pg_cache):
    session_mock = MagicMock()
    session_mock.query.side_effect = Exception("DB Error")
    pg_cache.session_factory = lambda: session_mock

    result = pg_cache.get(["AAPL"], "2024-01-01", "2024-01-31")
    assert result is None
    session_mock.rollback.assert_called_once()

@patch.object(PostgresCache, '_serialize')
def test_set_size_too_large(mock_serialize, pg_cache):
    pg_cache.max_size_mb = 1.0  # limit 1MB
    mock_serialize.return_value = b"x" * int(2 * 1024 * 1024)  # 2MB payload
    
    df = pl.DataFrame({"a": [1]})
    
    # Should exit early
    pg_cache.set(["AAPL"], "2024-01-01", "2024-01-31", df)
    # The session_factory should never be called
    mock_serialize.assert_called_once()

@patch("hermes_data.cache.postgres.datetime")
@patch.object(PostgresCache, '_serialize')
def test_set_success(mock_serialize, mock_datetime, pg_cache):
    mock_datetime.now.return_value = datetime.datetime.now(datetime.timezone.utc)
    mock_serialize.return_value = b"testdata"
    
    session_mock = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 100.0  # current size 100MB
    session_mock.execute.side_effect = [None, None, mock_result]  # delete existing, evict, get size
    pg_cache.session_factory = lambda: session_mock

    df = pl.DataFrame({"a": [1, 2, 3]})
    pg_cache.set(["AAPL", "MSFT"], "2024-01-01", "2024-01-31", df)

    assert session_mock.add.call_count == 1
    assert session_mock.commit.call_count == 1

@patch("hermes_data.cache.postgres.datetime")
@patch.object(PostgresCache, '_serialize')
def test_set_evicts_lru(mock_serialize, mock_datetime, pg_cache):
    mock_datetime.now.return_value = datetime.datetime.now(datetime.timezone.utc)
    mock_serialize.return_value = b"testdata"
    
    pg_cache.max_size_mb = 50.0  # tiny limit
    
    session_mock = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 60.0  # currently over size limit!
    
    old_entry1 = MagicMock()
    old_entry1.payload_size_mb = 15.0
    
    # We will evict this old entry
    session_mock.query.return_value.order_by.return_value.first.side_effect = [old_entry1, None]
    
    def side_effect(*args):
        if "SUM(payload_size_mb)" in str(args[0]):
            return mock_result
        return None
    session_mock.execute.side_effect = side_effect
    
    pg_cache.session_factory = lambda: session_mock

    df = pl.DataFrame({"a": [1]})
    pg_cache.set(["AAPL"], "2024-01-01", "2024-01-31", df)

    # Evicted old_entry1
    session_mock.delete.assert_any_call(old_entry1)
    assert session_mock.add.call_count == 1
    assert session_mock.commit.call_count == 1

def test_set_exception(pg_cache):
    session_mock = MagicMock()
    session_mock.execute.side_effect = Exception("DB Error")
    pg_cache.session_factory = lambda: session_mock

    df = pl.DataFrame({"a": [1]})
    pg_cache.set(["AAPL"], "2024-01-01", "2024-01-31", df)
    
    session_mock.rollback.assert_called_once()

def test_clear_success(pg_cache):
    session_mock = MagicMock()
    pg_cache.session_factory = lambda: session_mock
    pg_cache._hits = 5
    pg_cache._misses = 5
    
    pg_cache.clear()
    
    session_mock.execute.assert_called_once()
    session_mock.commit.assert_called_once()
    assert pg_cache._hits == 0
    assert pg_cache._misses == 0

def test_clear_exception(pg_cache):
    session_mock = MagicMock()
    session_mock.execute.side_effect = Exception("DB Error")
    pg_cache.session_factory = lambda: session_mock
    
    pg_cache.clear()
    session_mock.rollback.assert_called_once()

def test_stats_success(pg_cache):
    session_mock = MagicMock()
    pg_cache.session_factory = lambda: session_mock
    
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (10, 20.5, 50)  # entries, size_mb, hits
    session_mock.execute.return_value = mock_result
    
    pg_cache._hits = 20
    pg_cache._misses = 5
    
    stats = pg_cache.stats()
    assert stats["backend"] == "postgres_unlogged"
    assert stats["entries"] == 10
    assert stats["size_mb"] == 20.5
    assert stats["hits"] == 20
    assert stats["misses"] == 5
    assert stats["hit_rate_percent"] == 80.0
    assert stats["total_db_hits"] == 50

def test_stats_exception(pg_cache):
    session_mock = MagicMock()
    session_mock.execute.side_effect = Exception("DB Error")
    pg_cache.session_factory = lambda: session_mock
    
    stats = pg_cache.stats()
    assert stats["backend"] == "postgres_unlogged"
    assert "error" in stats
