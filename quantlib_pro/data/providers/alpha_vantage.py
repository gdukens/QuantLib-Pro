"""
Alpha Vantage data provider integration.

Free tier: 5 API calls per minute, 500 calls per day.
Premium tiers available for higher limits.

API Documentation: https://www.alphavantage.co/documentation/
"""

import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from quantlib_pro.utils.validation import require_ticker

log = logging.getLogger(__name__)


class AlphaVantageError(Exception):
    """Raised when Alpha Vantage API returns an error."""


class AlphaVantageProvider:
    """
    Alpha Vantage market data provider.
    
    Features:
    - Real-time and historical stock data
    - Intraday data (1min, 5min, 15min, 30min, 60min)
    - Daily, weekly, monthly data
    - Adjusted data (splits & dividends)
    - Global coverage (50+ exchanges)
    
    Parameters
    ----------
    api_key : str, optional
        Alpha Vantage API key. If None, reads from ALPHA_VANTAGE_API_KEY env var.
    timeout : int
        Request timeout in seconds (default: 30)
    retries : int
        Number of retry attempts (default: 3)
    
    Examples
    --------
    >>> provider = AlphaVantageProvider(api_key="YOUR_KEY")
    >>> data = provider.fetch("AAPL", start="2024-01-01", end="2024-12-31")
    >>> print(data.head())
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key required. "
                "Set ALPHA_VANTAGE_API_KEY environment variable or pass api_key parameter."
            )
        
        self.timeout = timeout
        self.retries = retries
        self._session = requests.Session()
    
    def fetch(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        output_size: str = "full",
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV data for a ticker.
        
        Parameters
        ----------
        ticker : str
            Stock symbol (e.g., "AAPL", "MSFT")
        start : str, optional
            Start date "YYYY-MM-DD" (used for filtering)
        end : str, optional
            End date "YYYY-MM-DD" (used for filtering)
        output_size : str
            "compact" (last 100 data points) or "full" (full history)
        
        Returns
        -------
        pd.DataFrame
            OHLCV data with DatetimeIndex
        
        Raises
        ------
        AlphaVantageError
            If API returns an error or rate limit exceeded
        """
        ticker = require_ticker(ticker)
        
        log.info(f"Fetching {ticker} from Alpha Vantage (outputsize={output_size})")
        
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": ticker,
            "outputsize": output_size,
            "apikey": self.api_key,
        }
        
        for attempt in range(self.retries):
            try:
                response = self._session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if "Error Message" in data:
                    raise AlphaVantageError(f"API Error: {data['Error Message']}")
                
                if "Note" in data:
                    raise AlphaVantageError(
                        f"Rate limit exceeded: {data['Note']}. "
                        "Free tier: 5 calls/min, 500 calls/day."
                    )
                
                if "Time Series (Daily)" not in data:
                    raise AlphaVantageError(
                        f"Unexpected response format. Keys: {list(data.keys())}"
                    )
                
                # Parse time series data
                time_series = data["Time Series (Daily)"]
                
                df = pd.DataFrame.from_dict(time_series, orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # Rename columns to standard OHLCV format
                df = df.rename(columns={
                    "1. open": "Open",
                    "2. high": "High",
                    "3. low": "Low",
                    "4. close": "Close",
                    "5. adjusted close": "Adj Close",
                    "6. volume": "Volume",
                    "7. dividend amount": "Dividend",
                    "8. split coefficient": "Split",
                })
                
                # Convert to numeric
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                
                # Filter by date range if provided
                if start:
                    df = df[df.index >= pd.to_datetime(start)]
                if end:
                    df = df[df.index <= pd.to_datetime(end)]
                
                # Keep only OHLCV columns (match yfinance format)
                df = df[["Open", "High", "Low", "Close", "Volume"]]
                
                log.info(f"✅ Alpha Vantage: Retrieved {len(df)} rows for {ticker}")
                return df
            
            except requests.exceptions.RequestException as e:
                log.warning(f"Alpha Vantage attempt {attempt + 1}/{self.retries} failed: {e}")
                if attempt == self.retries - 1:
                    raise AlphaVantageError(f"Failed after {self.retries} attempts: {e}")
        
        raise AlphaVantageError("Unexpected fetch failure")
    
    def fetch_intraday(
        self,
        ticker: str,
        interval: str = "5min",
        output_size: str = "compact",
    ) -> pd.DataFrame:
        """
        Fetch intraday data.
        
        Parameters
        ----------
        ticker : str
            Stock symbol
        interval : str
            Time interval: "1min", "5min", "15min", "30min", "60min"
        output_size : str
            "compact" (last 100 data points) or "full" (full history)
        
        Returns
        -------
        pd.DataFrame
            Intraday OHLCV data
        """
        ticker = require_ticker(ticker)
        
        valid_intervals = ["1min", "5min", "15min", "30min", "60min"]
        if interval not in valid_intervals:
            raise ValueError(f"interval must be one of {valid_intervals}")
        
        log.info(f"Fetching {ticker} intraday data ({interval}) from Alpha Vantage")
        
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": ticker,
            "interval": interval,
            "outputsize": output_size,
            "apikey": self.api_key,
        }
        
        response = self._session.get(
            self.BASE_URL,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        
        # Check for errors
        if "Error Message" in data:
            raise AlphaVantageError(f"API Error: {data['Error Message']}")
        
        if "Note" in data:
            raise AlphaVantageError(f"Rate limit: {data['Note']}")
        
        # Parse intraday data
        key = f"Time Series ({interval})"
        if key not in data:
            raise AlphaVantageError(f"Missing key: {key}")
        
        time_series = data[key]
        df = pd.DataFrame.from_dict(time_series, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Rename and convert
        df = df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume",
        })
        
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        log.info(f"✅ Alpha Vantage intraday: {len(df)} rows for {ticker}")
        return df
    
    def get_quote(self, ticker: str) -> dict:
        """
        Get real-time quote for a ticker.
        
        Parameters
        ----------
        ticker : str
            Stock symbol
        
        Returns
        -------
        dict
            Quote data with price, volume, change, etc.
        """
        ticker = require_ticker(ticker)
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": self.api_key,
        }
        
        response = self._session.get(
            self.BASE_URL,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        
        if "Global Quote" not in data:
            raise AlphaVantageError(f"No quote data for {ticker}")
        
        quote = data["Global Quote"]
        
        return {
            "symbol": quote.get("01. symbol"),
            "price": float(quote.get("05. price", 0)),
            "volume": int(quote.get("06. volume", 0)),
            "latest_trading_day": quote.get("07. latest trading day"),
            "previous_close": float(quote.get("08. previous close", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%"),
        }
    
    def __repr__(self):
        return f"AlphaVantageProvider(api_key='***{self.api_key[-4:]}')"


def create_alpha_vantage_fetcher(api_key: Optional[str] = None):
    """
    Create a function compatible with ResilientDataFetcher's alt_api_fn.
    
    Parameters
    ----------
    api_key : str, optional
        Alpha Vantage API key
    
    Returns
    -------
    callable
        Function(ticker, start, end) -> pd.DataFrame
    
    Examples
    --------
    >>> from quantlib_pro.data.fetcher import ResilientDataFetcher
    >>> from quantlib_pro.data.providers.alpha_vantage import create_alpha_vantage_fetcher
    >>> 
    >>> alt_fn = create_alpha_vantage_fetcher()
    >>> fetcher = ResilientDataFetcher(alt_api_fn=alt_fn)
    >>> data = fetcher.fetch("AAPL")  # Falls back to Alpha Vantage if yfinance fails
    """
    provider = AlphaVantageProvider(api_key=api_key)
    
    def fetch_function(ticker: str, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
        return provider.fetch(ticker, start=start, end=end, output_size="full")
    
    return fetch_function
