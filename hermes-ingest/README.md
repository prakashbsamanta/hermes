# hermes-ingest

**Data ingestion package for the Hermes trading platform.**

## Overview

`hermes-ingest` handles all data ingestion operations for Hermes:
- Fetching historical OHLCV data from brokers
- Writing to local storage or cloud (Cloudflare R2 / Oracle Object Storage)
- Smart resume for interrupted downloads
- Rate limiting and concurrent downloads

## Installation

```bash
# From the hermes project root
pip install -e hermes-ingest

# With cloud support (Cloudflare R2 or Oracle Object Storage)
pip install -e "hermes-ingest[cloud]"

# With test dependencies
pip install -e "hermes-ingest[test]"
```

## Usage

### CLI Commands

```bash
# Show current configuration
hermes-ingest config

# Fetch a single symbol
hermes-ingest fetch --symbol RELIANCE

# Sync all instruments (with limit)
hermes-ingest sync --limit 50 --concurrency 5

# List available symbols in storage
hermes-ingest list-symbols
```

## Storage Options

### Local Storage (Default)

Data is stored as Parquet files in the local filesystem:

```bash
HERMES_SINK_TYPE=local
HERMES_SINK_PATH=data/minute
```

### Cloudflare R2 (Cloud)

S3-compatible cloud storage with **zero egress fees**:

```bash
HERMES_SINK_TYPE=cloudflare_r2
HERMES_R2_ACCOUNT_ID=your_account_id
HERMES_R2_ACCESS_KEY_ID=your_access_key
HERMES_R2_SECRET_ACCESS_KEY=your_secret_key
HERMES_R2_BUCKET_NAME=hermes-market-data
```

See [CLOUDFLARE_R2_SETUP.md](../docs/CLOUDFLARE_R2_SETUP.md) for complete setup guide.

### Oracle Cloud Object Storage (Cloud)

S3-compatible cloud storage with generous free tier:

```bash
HERMES_SINK_TYPE=oracle_object_storage
HERMES_OCI_NAMESPACE=your_namespace
HERMES_OCI_REGION=ap-hyderabad-1
HERMES_OCI_ACCESS_KEY_ID=your_access_key
HERMES_OCI_SECRET_ACCESS_KEY=your_secret_key
HERMES_OCI_BUCKET_NAME=hermes-market-data
```

See [ORACLE_OBJECT_STORAGE_SETUP.md](../docs/ORACLE_OBJECT_STORAGE_SETUP.md) for complete setup guide.

### Programmatic Usage

```python
from hermes_ingest.sinks import create_sink

# Auto-create sink based on environment
sink = create_sink()

# Write data
sink.write("RELIANCE", df)

# Read data
df = sink.read("RELIANCE")
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HERMES_ZERODHA_ENCTOKEN` | Zerodha authentication token | Required |
| `HERMES_SINK_TYPE` | Storage type: `local`, `cloudflare_r2`, or `oracle_object_storage` | `local` |
| `HERMES_SINK_PATH` | Path for local storage | `data/minute` |
| `HERMES_RATE_LIMIT_PER_SEC` | API rate limit | `2.5` |
| `HERMES_MAX_CONCURRENCY` | Parallel downloads | `5` |

### Getting Zerodha Enctoken

1. Log in to [Kite Web](https://kite.zerodha.com/)
2. Open browser developer tools (F12)
3. Go to Application → Cookies
4. Copy the `enctoken` value
5. Set in `.env`:
   ```bash
   HERMES_ZERODHA_ENCTOKEN="your_token_here"
   ```

## Architecture

```
hermes-ingest/
├── src/hermes_ingest/
│   ├── sources/          # Data sources (brokers)
│   │   ├── base.py       # Abstract DataSource
│   │   └── zerodha.py    # Zerodha Kite adapter
│   ├── sinks/            # Storage destinations
│   │   ├── base.py       # Abstract DataSink
│   │   ├── local.py      # Local parquet files
│   │   ├── cloudflare_r2.py  # Cloudflare R2 (S3-compatible)
│   │   ├── oracle_object_storage.py  # Oracle OCI (S3-compatible)
│   │   └── factory.py    # Sink factory for easy switching
│   ├── config.py         # Configuration via env vars
│   ├── orchestrator.py   # Job orchestration
│   └── cli.py            # CLI entry point
└── tests/
```

## Adding a New Source

```python
from hermes_ingest.sources.base import DataSource

class ShoonyaSource(DataSource):
    async def fetch(self, symbol, token, start_date, end_date):
        # Implementation
        pass

    def list_instruments(self):
        # Implementation
        pass

    async def close(self):
        # Cleanup
        pass
```

## Adding a New Sink

```python
from hermes_ingest.sinks.base import DataSink

class NewCloudSink(DataSink):
    def write(self, symbol, df):
        # Write to cloud
        pass

    def read(self, symbol):
        # Read from cloud
        pass

    def exists(self, symbol):
        # Check cloud
        pass

    def list_symbols(self):
        # List cloud objects
        pass
```

## Testing

```bash
cd hermes-ingest
pip install -e ".[test]"
pytest --cov=src/hermes_ingest --cov-fail-under=90
```

## License

MIT
