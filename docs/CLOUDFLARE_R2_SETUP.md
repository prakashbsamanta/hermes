# Cloudflare R2 Setup Guide

This guide walks you through setting up Cloudflare R2 as cloud storage for Hermes market data.

## Overview

Cloudflare R2 is an S3-compatible object storage with **zero egress fees**, making it ideal for storing and retrieving large market data files.

**Benefits:**
- **Zero egress fees** (no cost when downloading data)
- S3-compatible API (works with existing tools like boto3)
- 10 GB free storage on the free tier
- Fast global access via Cloudflare's network

---

## Step 1: Create Cloudflare Account

1. Go to [cloudflare.com](https://cloudflare.com) and sign up
2. No domain or payment required for R2 free tier
3. Navigate to **R2 Object Storage** in the dashboard sidebar

---

## Step 2: Create an R2 Bucket

1. Click **Create bucket**
2. Enter bucket name: `hermes-market-data` (or your preferred name)
3. Select default location (automatic is fine)
4. Click **Create bucket**

> **Note**: Bucket names must be globally unique. If `hermes-market-data` is taken, try `hermes-data-<your-name>`.

---

## Step 3: Create API Token

1. In R2 dashboard, click **Manage R2 API Tokens**
2. Click **Create API token**
3. Configure the token:
   - **Token name**: `hermes-ingest`
   - **Permissions**: `Object Read & Write`
   - **Specify buckets**: Select your bucket (`hermes-market-data`)
   - **TTL**: Optional (leave blank for no expiration)
4. Click **Create API Token**
5. **IMPORTANT**: Copy and save these values immediately:
   - `Access Key ID`
   - `Secret Access Key`
   - You'll also need your `Account ID` from the R2 overview page

---

## Step 4: Configure Hermes

### Option A: Using .env file (Recommended)

Copy `.env.example` to `.env` and configure:

```bash
# Switch to Cloudflare R2 storage
HERMES_SINK_TYPE=cloudflare_r2
HERMES_STORAGE_PROVIDER=cloudflare_r2

# Cloudflare R2 credentials
HERMES_R2_ACCOUNT_ID=your_account_id_here
HERMES_R2_ACCESS_KEY_ID=your_access_key_here
HERMES_R2_SECRET_ACCESS_KEY=your_secret_key_here
HERMES_R2_BUCKET_NAME=hermes-market-data
HERMES_R2_PREFIX=minute
```

### Option B: Using Environment Variables

```bash
export HERMES_SINK_TYPE=cloudflare_r2
export HERMES_R2_ACCOUNT_ID=your_account_id
export HERMES_R2_ACCESS_KEY_ID=your_access_key
export HERMES_R2_SECRET_ACCESS_KEY=your_secret_key
export HERMES_R2_BUCKET_NAME=hermes-market-data
export HERMES_R2_PREFIX=minute
```

---

## Step 5: Install Cloud Dependencies

Install the cloud extras for hermes-ingest:

```bash
cd hermes-ingest
pip install -e ".[cloud]"
```

This installs `boto3` which is required for R2 communication.

---

## Step 6: Verify Connection

Test the R2 connection by running:

```bash
# Fetch data for one symbol (it should upload to R2)
hermes-ingest fetch RELIANCE --days 1
```

You can verify in the Cloudflare R2 dashboard that objects are being created.

---

## Switching Between Local and Cloud

### Use Local Storage

```bash
# In .env
HERMES_SINK_TYPE=local
HERMES_SINK_PATH=data/minute
```

### Use Cloudflare R2

```bash
# In .env
HERMES_SINK_TYPE=cloudflare_r2
# ... R2 credentials ...
```

The `create_sink()` factory automatically creates the appropriate sink based on configuration.

---

## Programmatic Usage

```python
from hermes_ingest.sinks import create_sink

# Automatically uses config from environment
sink = create_sink()

# Explicitly create R2 sink
from hermes_ingest.sinks import CloudflareR2Sink

r2_sink = CloudflareR2Sink(
    account_id="your_account_id",
    access_key_id="your_key",
    secret_access_key="your_secret",
    bucket_name="hermes-market-data",
    prefix="minute",
)

# Write data
r2_sink.write("RELIANCE", df)

# Read data
df = r2_sink.read("RELIANCE")

# List all symbols
symbols = r2_sink.list_symbols()
```

---

## Pricing Reference

| Resource | Free Tier | Paid |
|----------|-----------|------|
| Storage | 10 GB/month | $0.015/GB/month |
| Class A ops (writes) | 1M/month | $4.50/million |
| Class B ops (reads) | 10M/month | $0.36/million |
| **Egress** | **Unlimited** | **$0** |

For typical usage with minute data for ~100 symbols over 5 years, you'll need approximately 1-2 GB of storage.

---

## Troubleshooting

### "boto3 is required for R2 sink"

Install cloud dependencies:
```bash
pip install hermes-ingest[cloud]
```

### "Cloudflare R2 sink requires credentials"

Make sure all three environment variables are set:
- `HERMES_R2_ACCOUNT_ID`
- `HERMES_R2_ACCESS_KEY_ID`
- `HERMES_R2_SECRET_ACCESS_KEY`

### "Access Denied" errors

1. Check that your API token has `Object Read & Write` permissions
2. Verify the bucket name matches exactly
3. Ensure the token is scoped to the correct bucket

---

## Security Notes

- **Never commit `.env` to git** (it's already in `.gitignore`)
- Rotate API tokens periodically
- Use bucket-specific tokens with minimal permissions
- Consider using Cloudflare Workers for additional access control
