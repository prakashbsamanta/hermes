# Hermes Data

A separated data layer package for the Hermes backtesting platform. This package provides:

- **Abstract DataProvider interface** for pluggable storage backends
- **LocalFileProvider** for loading data from local Parquet files
- **MemoryCache** for efficient caching with LRU eviction
- **DataService** facade for unified data access
- **RegistryService** for instrument metadata and data availability tracking (PostgreSQL)

## Installation

### Development (Editable)

```bash
cd hermes-data
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### As Dependency

```bash
pip install -e ../hermes-data
```

## Configuration

All settings are configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_STORAGE_PROVIDER` | `local` | Storage backend: `local`, `s3` (future), `gcs` (future) |
| `HERMES_DATA_DIR` | `hermes-backend/data/minute` | Path to data directory |
| `HERMES_CACHE_ENABLED` | `true` | Enable in-memory caching |
| `HERMES_CACHE_MAX_SIZE_MB` | `512` | Maximum cache size in MB |
| `HERMES_DATABASE_URL` | `postgresql://hermes:hermes_secret@localhost:5432/hermes` | PostgreSQL connection |
| `HERMES_REGISTRY_ENABLED` | `true` | Enable data registry |

## Usage

### Basic Usage

```python
from hermes_data import DataService

# Uses environment-based configuration
service = DataService()

# Load market data (with caching)
df = service.get_market_data(["RELIANCE", "INFY"], "2024-01-01", "2024-12-31")

# List available instruments
symbols = service.list_instruments()

# Get date range for a symbol
start, end = service.get_date_range("RELIANCE")

# Check health
health = service.health_check()
```

### With Registry

```python
from hermes_data import DataService

service = DataService()

# Search instruments
results = service.search_instruments("RELIANCE")

# Get detailed instrument info
info = service.get_instrument_info("RELIANCE")
# Returns: {symbol, name, exchange, start_date, end_date, row_count}

# Sync registry with filesystem
count = service.sync_registry()
print(f"Synced {count} instruments")

# Access registry directly
if service.registry:
    instrument = service.registry.get_or_create_instrument(
        symbol="NEWSTOCK",
        name="New Stock Ltd",
        exchange="NSE",
    )
```

### Custom Configuration

```python
from hermes_data import DataService, DataSettings
from hermes_data.providers.local import LocalFileProvider

# Custom settings
settings = DataSettings(
    data_dir="/path/to/data",
    cache_enabled=True,
    cache_max_size_mb=1024,
    database_url="postgresql://user:pass@localhost/hermes",
    registry_enabled=True,
)

# Custom provider
provider = LocalFileProvider("/custom/path")

# Create service
service = DataService(provider=provider, settings=settings)
```

### Dependency Injection (Testing)

```python
from hermes_data import DataService, DataSettings
from hermes_data.providers.local import LocalFileProvider

# Create mock provider
provider = LocalFileProvider(temp_data_dir)
settings = DataSettings(
    data_dir=str(temp_data_dir),
    cache_enabled=False,
    registry_enabled=False,  # Disable for unit tests
)

# Inject into your service
data_service = DataService(provider=provider, settings=settings, enable_registry=False)
```

## Architecture

```
hermes_data/
├── __init__.py          # Package exports
├── config.py            # Configuration management
├── service.py           # Main DataService facade
├── providers/
│   ├── base.py          # Abstract DataProvider interface
│   └── local.py         # LocalFileProvider implementation
├── cache/
│   ├── base.py          # Abstract CacheProvider interface
│   └── memory.py        # MemoryCache implementation
└── registry/
    ├── models.py        # SQLAlchemy models (Instrument, DataAvailability, DataLoadLog)
    ├── database.py      # Database connection management
    └── service.py       # RegistryService operations
```

## Database Schema

### Instruments Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| symbol | VARCHAR(50) | Unique stock symbol |
| name | VARCHAR(255) | Display name |
| exchange | VARCHAR(50) | Exchange code (NSE, BSE) |
| instrument_type | VARCHAR(50) | EQUITY, INDEX, FUTURE, OPTION |
| sector | VARCHAR(100) | Industry sector |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Data Availability Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| instrument_id | INTEGER | Foreign key to instruments |
| timeframe | VARCHAR(10) | 1m, 5m, 1h, 1d, etc. |
| start_date | TIMESTAMP | Earliest data point |
| end_date | TIMESTAMP | Latest data point |
| row_count | INTEGER | Total rows |
| data_quality_score | FLOAT | 0.0 - 1.0 quality score |
| last_updated | TIMESTAMP | When data was last refreshed |

### Data Load Logs Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| symbol | VARCHAR(50) | Loaded symbol |
| status | VARCHAR(20) | SUCCESS, ERROR, PARTIAL |
| rows_loaded | INTEGER | Number of rows |
| load_time_ms | INTEGER | Load duration |
| cache_hit | INTEGER | 0 = miss, 1 = hit |
| created_at | TIMESTAMP | Log timestamp |

## Running Tests

```bash
cd hermes-data
source .venv/bin/activate
pytest tests/ -v
```

## Future Additions

- **S3Provider** - AWS S3 storage adapter
- **GCSProvider** - Google Cloud Storage adapter
- **RedisCache** - Distributed caching

## License

MIT
