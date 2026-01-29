# Hermes Data Seeder

This utility downloads historical minute-level stock data from Zerodha and saves it as efficient Parquet files.

## Features
- **Smart Resume**: Automatically detecting existing data and only fetches what's missing.
- **Incremental Saving**: Saves progress after every 60-day chunk, preventing data loss.
- **Rate Limit Handling**: Respects Zerodha's API limits.
- **Optimized Storage**: Uses Polars and Parquet for high performance.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables**:
    Ensure your `.env` file has the valid `ZERODHA_ENCTOKEN`.

## Usage

Run the script using `python3 data_seeder.py` with the following arguments:

### 1. Fetch a Single Stock
To download data for a specific symbol (e.g., RELIANCE, INFHY, TCS):
```bash
python3 data_seeder.py --symbol RELIANCE
```

### 2. Fetch All Stocks
To download data for **all** stocks found in `data/instruments/NSE.csv`:
```bash
python3 data_seeder.py --all
```

### 3. Fetch Batch (Range)
Useful if you want to run multiple instances or just test minimal load.
Process 10 stocks starting from index 100:
```bash
python3 data_seeder.py --all --start-index 100 --limit 10
```

### 4. Help
View all available options:
```bash
python3 data_seeder.py --help
```

## Logs
Logs are saved in the `logs/` directory with timestamps (e.g., `download_minute_20260129_213000.log`).
Empty chunks (e.g., years 2000-2007 for newer stocks) will be logged as `-> No data in this chunk.`
