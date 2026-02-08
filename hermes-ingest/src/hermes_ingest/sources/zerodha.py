"""Zerodha Kite data source."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import polars as pl

from hermes_ingest.config import IngestSettings, get_settings
from hermes_ingest.sources.base import DataSource

logger = logging.getLogger(__name__)

BASE_URL = "https://kite.zerodha.com/oms"


class RateLimiter:
    """Token Bucket Rate Limiter to enforce Global Request Limits.

    Zerodha limit is approx 3 requests/second.
    """

    def __init__(self, rate_limit_per_sec: float = 2.5):
        self.rate_limit = rate_limit_per_sec
        self.tokens = rate_limit_per_sec
        self.max_tokens = rate_limit_per_sec
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def wait(self) -> None:
        """Wait until a token is available."""
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


class ZerodhaSource(DataSource):
    """Data source for Zerodha Kite historical data.

    Fetches minute-level OHLCV data from Zerodha's unofficial API.
    """

    def __init__(
        self,
        enctoken: str | None = None,
        user_id: str | None = None,
        settings: IngestSettings | None = None,
    ):
        """Initialize the Zerodha source.

        Args:
            enctoken: Zerodha enctoken (or from settings)
            user_id: Zerodha user ID (or from settings)
            settings: Optional IngestSettings instance
        """
        self._settings = settings or get_settings()
        self.enctoken = enctoken or self._settings.zerodha_enctoken
        self.user_id = user_id or self._settings.zerodha_user_id

        if not self.enctoken:
            raise ValueError(
                "Zerodha enctoken required. "
                "Set HERMES_ZERODHA_ENCTOKEN environment variable."
            )

        self.rate_limiter = RateLimiter(self._settings.rate_limit_per_sec)
        self._session: aiohttp.ClientSession | None = None

    @property
    def headers(self) -> dict[str, str]:
        """Get HTTP headers for Zerodha API."""
        return {
            "Authorization": f"enctoken {self.enctoken}",
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            ),
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def fetch(
        self,
        symbol: str,
        token: int,
        start_date: str,
        end_date: str,
    ) -> pl.DataFrame | None:
        """Fetch OHLCV data for a symbol.

        Fetches in chunks to avoid API limits.
        """
        session = await self._get_session()
        all_candles: list[list[Any]] = []
        chunk_days = self._settings.chunk_days

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        current_dt = start_dt

        while current_dt < end_dt:
            next_dt = min(current_dt + timedelta(days=chunk_days), end_dt)
            f_date = current_dt.strftime("%Y-%m-%d")
            t_date = next_dt.strftime("%Y-%m-%d")

            candles = await self._fetch_chunk(session, token, f_date, t_date)
            if candles:
                all_candles.extend(candles)
                logger.info(f"[{symbol}] {f_date} -> {t_date}: Got {len(candles)} candles")

            current_dt = next_dt + timedelta(days=1)

        if not all_candles:
            return None

        # Convert to DataFrame
        schema = ["timestamp", "open", "high", "low", "close", "volume", "oi"]
        df = pl.DataFrame(all_candles, schema=schema, orient="row")

        # Parse timestamp
        df = df.with_columns(
            pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S%z", strict=False)
        )

        return df

    async def _fetch_chunk(
        self,
        session: aiohttp.ClientSession,
        token: int,
        from_date: str,
        to_date: str,
    ) -> list[Any] | None:
        """Fetch a single chunk of data."""
        url = f"{BASE_URL}/instruments/historical/{token}/minute"
        params: dict[str, Any] = {
            "from": from_date,
            "to": to_date,
            "oi": 1,
        }
        if self.user_id:
            params["user_id"] = self.user_id

        for attempt in range(3):
            try:
                await self.rate_limiter.wait()

                async with session.get(url, headers=self.headers, params=params) as response:
                    # Rate Limit
                    if response.status == 429:
                        logger.warning(f"Rate limit hit for token {token}. Retrying...")
                        await asyncio.sleep(2 * (attempt + 1))
                        continue

                    if response.status == 400:
                        # No data for this range
                        return []

                    response.raise_for_status()
                    data = await response.json()

                    if data.get("status") == "success":
                        candles = data["data"]["candles"]
                        return list(candles) if candles else []
                    else:
                        logger.error(f"API Error for token {token}: {data.get('message')}")
                        return None

            except aiohttp.ClientError as e:
                logger.warning(f"Request failed for token {token} (Attempt {attempt + 1}/3): {e}")
                await asyncio.sleep(1 * (attempt + 1))

        return None

    def list_instruments(self) -> pl.DataFrame:
        """List available instruments from local CSV file."""
        instrument_file = self._settings.get_instrument_file()

        if not instrument_file.exists():
            raise FileNotFoundError(
                f"Instrument file not found: {instrument_file}. "
                "Download from Zerodha or provide a valid path."
            )

        logger.info(f"Reading instruments from {instrument_file}...")
        df = pl.read_csv(str(instrument_file), infer_schema_length=10000, ignore_errors=True)

        # Filter to equity instruments only
        if "instrument_type" in df.columns:
            df = df.filter(pl.col("instrument_type") == "EQ")

        logger.info(f"Loaded {len(df)} instruments")
        return df

    async def close(self) -> None:
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
