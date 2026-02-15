# Oracle Cloud Object Storage Setup Guide

This guide walks you through setting up Oracle Cloud Infrastructure (OCI) Object Storage for Hermes market data.

## Overview

Oracle Cloud Object Storage provides an S3-compatible API, making it seamlessly work with the same tools (boto3) used by the Cloudflare R2 sink.

**Benefits:**
- **Always Free tier**: 20 GB Object Storage (standard)
- **10 TB/month outbound data transfer** (free tier)
- S3-compatible API via Customer Secret Keys
- Multiple regions including **ap-mumbai-1** (India)
- Enterprise-grade durability and availability

---

## Step 1: Create an Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and sign up
2. Oracle offers an **Always Free** tier with no time limit
3. After account creation, navigate to the **OCI Console**

---

## Step 2: Find Your Namespace

Your namespace is a unique identifier for your tenancy's Object Storage.

1. In the OCI Console, go to **Storage** → **Object Storage & Archive Storage**
2. Your **namespace** is displayed in the overview section
3. It's typically a random string like `axaxnpcrorw5` or similar
4. **Save this value** — you'll need it for the configuration

---

## Step 3: Create a Bucket

1. In **Object Storage**, click **Create Bucket**
2. Enter bucket name: `hermes-market-data` (or your preferred name)
3. **Storage Tier**: Standard
4. **Emit Object Events**: Leave unchecked (not needed)
5. Click **Create**

---

## Step 4: Create Customer Secret Keys

Customer Secret Keys provide S3-compatible access to your Object Storage.

1. Click on your **Profile icon** (top-right) → **User Settings**
2. Under **Resources** (left sidebar), click **Customer Secret Keys**
3. Click **Generate Secret Key**
4. Enter a name: `hermes-ingest`
5. Click **Generate Secret Key**
6. **IMPORTANT**: Copy the **Secret Key** immediately — it's only shown once!
7. After closing the dialog, copy the **Access Key** from the list

You now have:
- **Access Key ID** (visible in the list)
- **Secret Access Key** (copied from the generation dialog)

---

## Step 5: Identify Your Region

Your region is the OCI region identifier where your bucket is located.

Common regions:
| Region | Identifier |
|--------|-----------|
| Mumbai, India | `ap-mumbai-1` |
| Hyderabad, India | `ap-hyderabad-1` |
| US East (Ashburn) | `us-ashburn-1` |
| US West (Phoenix) | `us-phoenix-1` |
| UK South (London) | `uk-london-1` |
| Germany (Frankfurt) | `eu-frankfurt-1` |

Find your region in the OCI Console URL: `https://console.{region}.oraclecloud.com/`

---

## Step 6: Configure Hermes

### Option A: Using .env file (Recommended)

Add the following to your `.env` file:

```bash
# Switch to Oracle Object Storage
HERMES_SINK_TYPE=oracle_object_storage
HERMES_STORAGE_PROVIDER=oracle_object_storage

# Oracle OCI credentials
HERMES_OCI_NAMESPACE=your_namespace_here
HERMES_OCI_REGION=ap-hyderabad-1
HERMES_OCI_ACCESS_KEY_ID=your_access_key_here
HERMES_OCI_SECRET_ACCESS_KEY=your_secret_key_here
HERMES_OCI_BUCKET_NAME=hermes-market-data
HERMES_OCI_PREFIX=minute
```

### Option B: Using Environment Variables

```bash
export HERMES_SINK_TYPE=oracle_object_storage
export HERMES_OCI_NAMESPACE=your_namespace
export HERMES_OCI_REGION=ap-hyderabad-1
export HERMES_OCI_ACCESS_KEY_ID=your_access_key
export HERMES_OCI_SECRET_ACCESS_KEY=your_secret_key
export HERMES_OCI_BUCKET_NAME=hermes-market-data
export HERMES_OCI_PREFIX=minute
```

---

## Step 7: Install Cloud Dependencies

Install the cloud extras for hermes-ingest (same as for Cloudflare R2):

```bash
cd hermes-ingest
pip install -e ".[cloud]"
```

This installs `boto3` which is required for OCI's S3 Compatibility API.

---

## Step 8: Verify Connection

Test the OCI connection:

```bash
# Fetch data for one symbol (it should upload to OCI)
hermes-ingest fetch RELIANCE --days 1
```

You can verify in the OCI Console under **Object Storage** → **Buckets** → **hermes-market-data** that objects are being created.

---

## Switching Between Storage Options

Hermes supports three storage backends. Switch between them by changing `HERMES_SINK_TYPE`:

### Use Local Storage (Default)

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

### Use Oracle Cloud Object Storage

```bash
# In .env
HERMES_SINK_TYPE=oracle_object_storage
# ... OCI credentials ...
```

The `create_sink()` factory automatically creates the appropriate sink based on configuration.

---

## Programmatic Usage

```python
from hermes_ingest.sinks import create_sink

# Automatically uses config from environment
sink = create_sink()

# Explicitly create OCI sink
from hermes_ingest.sinks import OracleObjectStorageSink

oci_sink = OracleObjectStorageSink(
    namespace="your_namespace",
    region="ap-mumbai-1",
    access_key_id="your_access_key",
    secret_access_key="your_secret_key",
    bucket_name="hermes-market-data",
    prefix="minute",
)

# Write data
oci_sink.write("RELIANCE", df)

# Read data
df = oci_sink.read("RELIANCE")

# List all symbols
symbols = oci_sink.list_symbols()
```

---

## Pricing Reference (Oracle Cloud Free Tier)

| Resource | Always Free Tier | Paid |
|----------|-----------------|------|
| Storage (Standard) | 20 GB | $0.0255/GB/month |
| Storage (Archive) | - | $0.0026/GB/month |
| PUT/Copy/POST requests | 50,000/month | $0.0040/10,000 |
| GET/HEAD requests | 50,000/month | $0.0003/10,000 |
| **Outbound Data Transfer** | **10 TB/month** | $0.0085/GB |

For typical usage with minute data for ~100 symbols over 5 years, you'll need approximately 1-2 GB of storage — well within the free tier.

---

## Troubleshooting

### "boto3 is required for Oracle Object Storage sink"

Install cloud dependencies:
```bash
pip install hermes-ingest[cloud]
```

### "Oracle Object Storage sink requires credentials"

Make sure all four environment variables are set:
- `HERMES_OCI_NAMESPACE`
- `HERMES_OCI_REGION`
- `HERMES_OCI_ACCESS_KEY_ID`
- `HERMES_OCI_SECRET_ACCESS_KEY`

### "Access Denied" errors

1. Check that your Customer Secret Key is active (not expired)
2. Verify the namespace and region are correct
3. Ensure the user has the correct IAM policies (at minimum: `manage objects in compartment <compartment>`)
4. Confirm the bucket name matches exactly

### "Connection Refused" or Timeouts

1. Verify the endpoint format: `https://{namespace}.compat.objectstorage.{region}.oraclecloud.com`
2. Check your internet connectivity
3. Ensure the region is correct for your bucket

### "InvalidAccessKeyId" errors

1. Customer Secret Keys can take a few minutes to become active after creation
2. Verify you're using the correct Access Key ID (not the OCID)
3. Check if the key has been deleted or expired

---

## Security Notes

- **Never commit `.env` to git** (it's already in `.gitignore`)
- Rotate Customer Secret Keys periodically
- Use IAM policies to restrict access to specific buckets/compartments
- Consider using Oracle Vault for managing secrets in production
- Customer Secret Keys can be deleted/rotated from User Settings in OCI Console
