import os
import time
import logging
import asyncio
import aiohttp
import argparse
import polars as pl
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

ENCTOKEN = os.getenv('ZERODHA_ENCTOKEN')
BASE_URL = "https://kite.zerodha.com/oms"

DATA_DIR = os.path.join(SCRIPT_DIR, "data/minute")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
INSTRUMENT_FILE = os.path.join(SCRIPT_DIR, "data/instruments/NSE.csv")

START_DATE = "2000-01-01"

# --- Logging Setup ---
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_filename = os.path.join(LOG_DIR, f"download_minute_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

# --- Classes ---

class RateLimiter:
    """
    Token Bucket Rate Limiter to enforce Global Request Limits.
    Zerodha limit is approx 3 requests/second.
    """
    def __init__(self, rate_limit_per_sec=2.5):
        self.rate_limit = rate_limit_per_sec
        self.tokens = rate_limit_per_sec
        self.max_tokens = rate_limit_per_sec
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            while self.tokens < 1:
                now = time.monotonic()
                elapsed = now - self.updated_at
                self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate_limit)
                self.updated_at = now
                
                if self.tokens < 1:
                    wait_time = (1 - self.tokens) / self.rate_limit
                    await asyncio.sleep(wait_time)
            
            self.tokens -= 1

class ZerodhaClient:
    def __init__(self, rate_limiter):
        self.headers = {
            'Authorization': f'enctoken {ENCTOKEN}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        self.rate_limiter = rate_limiter

    async def fetch_chunk(self, session, token, from_date, to_date):
        url = f"{BASE_URL}/instruments/historical/{token}/minute"
        params = {
            'from': from_date,
            'to': to_date,
            'user_id': 'AG5883', 
            'oi': 1              
        }
        
        for attempt in range(3):
            try:
                await self.rate_limiter.wait()
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    # Rate Limit
                    if response.status == 429:
                        logging.warning(f"Rate limit hit for {token}. Retrying in 2s...")
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    
                    if response.status == 400:
                        # logging.debug(f"No data for {token} [{from_date} to {to_date}] (400 Bad Request).")
                        return []
                        
                    response.raise_for_status()
                    data = await response.json()
                    
                    if data['status'] == 'success':
                        return data['data']['candles']
                    else:
                        logging.error(f"API Error for {token}: {data.get('message')}")
                        return None
                        
            except aiohttp.ClientError as e:
                logging.warning(f"Request failed for {token} (Attempt {attempt+1}/3): {e}")
                await asyncio.sleep(1 * (attempt + 1))
                
        return None

# --- Helper Functions ---

def fetch_local_instruments():
    logging.info(f"Reading instruments from {INSTRUMENT_FILE}...")
    try:
        df = pl.read_csv(INSTRUMENT_FILE, infer_schema_length=10000, ignore_errors=True)
        if "instrument_type" in df.columns:
            df = df.filter(pl.col("instrument_type") == "EQ")
        logging.info(f"Loaded {len(df)} instruments.")
        return df
    except Exception as e:
        logging.error(f"Failed to read local instruments file: {e}")
        raise

# --- Core Logic ---

async def process_stock_async(client, session, sem, stock_row):
    """
    Worker function to process a single stock.
    Controlled by a semaphore to limit concurrency.
    """
    async with sem:
        token = stock_row['instrument_token']
        symbol = stock_row['tradingsymbol']
        
        output_path = os.path.join(DATA_DIR, f"{symbol}.parquet")
        
        # logging.info(f"--- Processing {symbol} (Token: {token}) ---")
        
        # Defaults
        end_date = datetime.now().replace(tzinfo=None) # Naive
        start_date_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
        
        # SMART RESUME logic (Sync file checking is fine here as it's once per stock)
        if os.path.exists(output_path):
            try:
                # Use scan_parquet for lazy/faster check if possible, or just read
                existing_df = pl.read_parquet(output_path)
                if not existing_df.is_empty():
                    last_ts = existing_df.select(pl.col("timestamp").max()).item()
                     # If last_ts is a string, convert to datetime (sanity check)
                    if isinstance(last_ts, str):
                         last_ts = datetime.strptime(last_ts, "%Y-%m-%dT%H:%M:%S%z") # Adjust format if needed

                    if last_ts:
                        if last_ts.tzinfo is not None:
                            last_ts = last_ts.replace(tzinfo=None)
                        start_date_dt = last_ts + timedelta(minutes=1)
                        logging.info(f"[{symbol}] Resuming from {start_date_dt}")
            except Exception as e:
                 logging.error(f"[{symbol}] Error reading existing file: {e}")

        if start_date_dt >= end_date:
            logging.info(f"[{symbol}] Already up to date.")
            return

        # Prepare Chunks
        current_dt = start_date_dt
        CHUNK_DAYS = 60
        
        # To avoid holding open file handle too often, we can buffer slightly, 
        # but incremental save per chunk is safer for the requested robustness.
        
        chunks_processed = 0
        
        while current_dt < end_date:
            next_dt = min(current_dt + timedelta(days=CHUNK_DAYS), end_date)
            f_date = current_dt.strftime('%Y-%m-%d')
            t_date = next_dt.strftime('%Y-%m-%d')
            
            # logging.info(f"[{symbol}] Fetching {f_date} -> {t_date}")
            
            # ASYNC Call
            candles = await client.fetch_chunk(session, token, f_date, t_date)
            
            if candles:
                logging.info(f"[{symbol}] {f_date} -> {t_date}: Got {len(candles)} candles.")
                
                # Save Logic (Sync - Polars is fast enough for file I/O)
                try:
                    schema = ["timestamp", "open", "high", "low", "close", "volume", "oi"]
                    chunk_df = pl.DataFrame(candles, schema=schema, orient="row")
                    chunk_df = chunk_df.with_columns(
                        pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S%z", strict=False)
                    )
                    
                    if os.path.exists(output_path):
                        current_disk_df = pl.read_parquet(output_path)
                        final_df = pl.concat([current_disk_df, chunk_df])
                    else:
                        final_df = chunk_df
                        
                    final_df = final_df.unique(subset=["timestamp"]).sort("timestamp")
                    final_df.write_parquet(output_path)
                    
                    chunks_processed += 1
                except Exception as e:
                    logging.error(f"[{symbol}] CRITICAL Save Error: {e}")
                    break
            else:
                 logging.info(f"[{symbol}] {f_date} -> {t_date}: No data.")

            current_dt = next_dt + timedelta(days=1)
            
        if chunks_processed > 0:
            logging.info(f"[{symbol}] SUCCESS. Saved {chunks_processed} chunks.")
        else:
            logging.warning(f"[{symbol}] Processed but no new data saved.")


async def main_async():
    # Ensure data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Argument Parser
    parser = argparse.ArgumentParser(description="Hermes Async Data Seeder")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbol", type=str, help="Process a single stock symbol (e.g., RELIANCE)")
    group.add_argument("--all", action="store_true", help="Process ALL stocks")
    
    parser.add_argument("--start-index", type=int, default=0, help="Start from index")
    parser.add_argument("--limit", type=int, help="Limit number of stocks")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of parallel downloads (default: 5)")
    
    args = parser.parse_args()

    try:
        instruments_df = fetch_local_instruments()
    except Exception:
        return

    # Determine Work List
    work_list = []
    
    if args.symbol:
        target_stock = args.symbol.upper()
        target_row = instruments_df.filter(pl.col("tradingsymbol") == target_stock)
        if len(target_row) > 0:
            work_list.append(target_row.row(0, named=True))
        else:
            logging.error(f"Symbol {target_stock} not found.")
            return
            
    elif args.all:
        total = len(instruments_df)
        start = args.start_index
        end = total
        if args.limit:
            end = min(start + args.limit, total)
            
        logging.info(f"Queuing stocks from index {start} to {end} (Total: {total})")
        
        # Slicing
        subset = instruments_df.slice(start, end - start)
        work_list = [row for row in subset.iter_rows(named=True)]

    # Async Orchestration
    rate_limiter = RateLimiter(rate_limit_per_sec=2.5) # Global Limit
    client = ZerodhaClient(rate_limiter)
    sem = asyncio.Semaphore(args.concurrency) # Concurrency Limit
    
    logging.info(f"Starting execution with {len(work_list)} stocks. Concurrency: {args.concurrency}")
    
    async with aiohttp.ClientSession() as session:
        tasks = [process_stock_async(client, session, sem, row) for row in work_list]
        await asyncio.gather(*tasks)
        
    logging.info("All tasks completed.")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
