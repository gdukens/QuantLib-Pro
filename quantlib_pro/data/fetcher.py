"""
ResilientDataFetcher — 6-level fallback chain for market data.

Level  Label            Description
-----  ---------------  -------------------------------------------------
  1    memory_cache     In-process LRU dict  (sub-ms)
  2    redis_cache      Redis  (1-5 ms)
  3    file_cache       Parquet files  (10-50 ms)
  4    yfinance         Yahoo Finance HTTP  (300-2000 ms)
  5    alternative_api  Placeholder for a secondary data provider
  6    synthetic        GBM simulation — flagged, never cached
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd

from quantlib_pro.resilience import CircuitBreakerOpenError, registry
from quantlib_pro.utils.types import DataSource, PriceData
from quantlib_pro.utils.validation import require_ticker

from .cache import get_dataframe, set_dataframe

log = logging.getLogger(__name__)


class DataFetchError(RuntimeError):
    """Raised only when all 6 levels fail."""


class ResilientDataFetcher:
    """
    Fetch OHLCV price history for a ticker using a 6-level fallback chain.

    Parameters
    ----------
    redis_client:
        Optional pre-built redis.Redis instance.  If None, Redis levels
        are silently skipped.
    cache_ttl:
        Seconds to keep cached data in memory / Redis.
    alt_api_fn:
        Optional callable ``(ticker, start, end) -> pd.DataFrame`` for
        the alternative data provider (Level 5).
    """

    def __init__(
        self,
        redis_client: Any = None,
        cache_ttl: int = 3600,
        alt_api_fn: Optional[Any] = None,
    ) -> None:
        self._redis = redis_client
        self._ttl = cache_ttl
        self._alt_api_fn = alt_api_fn

    # ------------------------------------------------------------------ public

    def fetch(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: str = "1y",
    ) -> PriceData:
        """
        Fetch OHLCV data for *ticker*.

        Returns a :class:`~quantlib_pro.utils.types.PriceData` whose
        ``source`` field describes which level was used.

        Raises
        ------
        DataFetchError
            If all 6 levels fail.
        """
        ticker = require_ticker(ticker)
        cache_key = self._build_key(ticker, start, end, period)

        methods = [
            ("cache",         self._try_cache,       DataSource.MEMORY_CACHE),
            ("yfinance",      self._try_yfinance,    DataSource.YFINANCE),
            ("alternative",   self._try_alt_api,     DataSource.ALTERNATIVE_API),
            ("synthetic",     self._try_synthetic,   DataSource.SYNTHETIC),
        ]

        for level_name, method, source in methods:
            t0 = time.perf_counter()
            try:
                df = method(ticker, cache_key, start, end, period)
            except Exception as exc:
                log.warning("Level %s failed for %s: %s", level_name, ticker, exc)
                continue

            if df is None or df.empty:
                log.debug("Level %s returned empty for %s", level_name, ticker)
                continue

            elapsed_ms = (time.perf_counter() - t0) * 1000
            log.info(
                "Fetched %s from %s in %.0f ms (%d rows)",
                ticker,
                source.value,
                elapsed_ms,
                len(df),
            )

            # Cache live data only (not synthetic)
            if source != DataSource.SYNTHETIC:
                self._prime_cache(cache_key, df)

            return PriceData(
                ticker=ticker,
                df=df,
                source=source,
                fetched_at=datetime.utcnow(),
            )

        raise DataFetchError(
            f"All data sources exhausted for '{ticker}'. "
            "Check network connectivity and retry."
        )

    # ----------------------------------------------------------------- levels

    def _try_cache(
        self,
        ticker: str,
        cache_key: str,
        start: Optional[str],
        end: Optional[str],
        period: str,
    ) -> Optional[pd.DataFrame]:
        df, source_label = get_dataframe(cache_key, redis_client=self._redis)
        if df is not None and not df.empty:
            log.debug("Cache HIT [%s] for %s", source_label, ticker)
            return df
        return None

    def _try_yfinance(
        self,
        ticker: str,
        cache_key: str,
        start: Optional[str],
        end: Optional[str],
        period: str,
    ) -> Optional[pd.DataFrame]:
        def _download() -> pd.DataFrame:
            import yfinance as yf  # type: ignore[import]
            t = yf.Ticker(ticker)
            if start and end:
                df = t.history(start=start, end=end, auto_adjust=True)
            else:
                df = t.history(period=period, auto_adjust=True)
            return df

        cb = registry.get("yfinance", failure_threshold=3, recovery_timeout=120)
        return cb.call(_download)

    def _try_alt_api(
        self,
        ticker: str,
        cache_key: str,
        start: Optional[str],
        end: Optional[str],
        period: str,
    ) -> Optional[pd.DataFrame]:
        if self._alt_api_fn is None:
            return None

        def _call() -> pd.DataFrame:
            return self._alt_api_fn(ticker, start, end)

        cb = registry.get("alternative_api", failure_threshold=3, recovery_timeout=300)
        return cb.call(_call)

    def _try_synthetic(
        self,
        ticker: str,
        cache_key: str,
        start: Optional[str],
        end: Optional[str],
        period: str,
    ) -> pd.DataFrame:
        """
        Geometric Brownian Motion fallback.

        Only produced when *all* live sources are unavailable.
        The resulting :class:`PriceData` is clearly flagged as
        ``DataSource.SYNTHETIC``.
        """
        log.warning(
            "⚠  Generating SYNTHETIC data for %s — live sources unavailable", ticker
        )
        n_days = 252
        dt = 1 / 252
        mu = 0.07
        sigma = 0.20
        s0 = 100.0

        rng = np.random.default_rng(abs(hash(ticker)) % (2**32))
        z = rng.standard_normal(n_days)
        log_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
        prices = s0 * np.exp(np.cumsum(log_returns))
        prices = np.insert(prices, 0, s0)[:-1]

        dates = pd.bdate_range(end=datetime.utcnow().date(), periods=n_days)
        volumes = rng.integers(1_000_000, 10_000_000, size=n_days).astype(float)

        df = pd.DataFrame(
            {
                "Open": prices * (1 + rng.uniform(-0.005, 0.005, n_days)),
                "High": prices * (1 + rng.uniform(0.000, 0.015, n_days)),
                "Low": prices * (1 - rng.uniform(0.000, 0.015, n_days)),
                "Close": prices,
                "Volume": volumes,
            },
            index=dates,
        )
        # Enforce OHLCV constraints post-generation
        df["High"] = df[["Open", "High", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "Low", "Close"]].min(axis=1)
        return df

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _build_key(
        ticker: str,
        start: Optional[str],
        end: Optional[str],
        period: str,
    ) -> str:
        parts = [ticker]
        if start:
            parts.append(f"s{start}")
        if end:
            parts.append(f"e{end}")
        if not (start or end):
            parts.append(f"p{period}")
        return ":".join(parts)

    def _prime_cache(self, cache_key: str, df: pd.DataFrame) -> None:
        set_dataframe(cache_key, df, redis_client=self._redis, ttl_seconds=self._ttl)
