"""
Multi-Provider Data Ingestion System.

Supports multiple data sources with unified interface:
- Yahoo Finance (yfinance) - free, delayed data
- Alpha Vantage - free tier with API key
- IEX Cloud - real-time market data
- CSV/Parquet files - local data storage

Example
-------
>>> provider = DataProviderFactory.create('yahoo')
>>> data = provider.fetch_historical('AAPL', '2023-01-01', '2024-01-01')
>>> 
>>> # Multi-provider aggregation
>>> aggregator = MultiProviderAggregator(['yahoo', 'alphavantage'])
>>> data = aggregator.fetch_with_fallback('AAPL', '2023-01-01', '2024-01-01')
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class DataProvider(ABC):
    """Base class for data providers."""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        log.info(f"Initialized {name} data provider")
    
    @abstractmethod
    def fetch_historical(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = '1d',
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        
        Parameters
        ----------
        symbol : str
            Ticker symbol
        start_date : str or datetime
            Start date
        end_date : str or datetime
            End date
        interval : str
            Data interval ('1d', '1h', '5m', etc.)
        
        Returns
        -------
        pd.DataFrame
            OHLCV data with DatetimeIndex
        """
        pass
    
    @abstractmethod
    def fetch_quote(self, symbol: str) -> Dict:
        """
        Fetch real-time quote.
        
        Parameters
        ----------
        symbol : str
            Ticker symbol
        
        Returns
        -------
        dict
            Quote data with price, volume, bid, ask, etc.
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean OHLCV data."""
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_cols if col not in data.columns]
        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Remove NaN rows
        data = data.dropna(subset=required_cols)
        
        # Validate price sanity
        if (data['High'] < data['Low']).any():
            log.warning("Found High < Low, correcting...")
            data.loc[data['High'] < data['Low'], 'High'] = data['Low']
        
        if (data['High'] < data['Close']).any():
            log.warning("Found High < Close, correcting...")
            data.loc[data['High'] < data['Close'], 'High'] = data['Close']
        
        if (data['Low'] > data['Close']).any():
            log.warning("Found Low > Close, correcting...")
            data.loc[data['Low'] > data['Close'], 'Low'] = data['Close']
        
        return data


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider using yfinance."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__('Yahoo Finance', config)
    
    def fetch_historical(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = '1d',
    ) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance."""
        try:
            import yfinance as yf
        except ImportError:
            log.error("yfinance not installed. Run: pip install yfinance")
            raise
        
        log.info(f"Fetching {symbol} from Yahoo Finance: {start_date} to {end_date}")
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if data.empty:
            raise ValueError(f"No data returned for {symbol}")
        
        return self.validate_data(data)
    
    def fetch_quote(self, symbol: str) -> Dict:
        """Fetch real-time quote from Yahoo Finance."""
        try:
            import yfinance as yf
        except ImportError:
            log.error("yfinance not installed. Run: pip install yfinance")
            raise
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'symbol': symbol,
            'price': info.get('currentPrice', info.get('regularMarketPrice')),
            'bid': info.get('bid'),
            'ask': info.get('ask'),
            'volume': info.get('volume'),
            'market_cap': info.get('marketCap'),
            'timestamp': datetime.now(),
        }


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage data provider."""
    
    def __init__(self, api_key: str, config: Optional[Dict] = None):
        super().__init__('Alpha Vantage', config)
        self.api_key = api_key
    
    def fetch_historical(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = '1d',
    ) -> pd.DataFrame:
        """Fetch historical data from Alpha Vantage."""
        log.info(f"Fetching {symbol} from Alpha Vantage: {start_date} to {end_date}")
        
        # Note: This is a placeholder implementation
        # In production, would use requests to call Alpha Vantage API
        # API: https://www.alphavantage.co/documentation/
        
        import requests
        
        function_map = {
            '1d': 'TIME_SERIES_DAILY',
            '1h': 'TIME_SERIES_INTRADAY',
            '5m': 'TIME_SERIES_INTRADAY',
        }
        
        function = function_map.get(interval, 'TIME_SERIES_DAILY')
        
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full',
        }
        
        if interval in ['1h', '5m']:
            params['interval'] = interval
        
        url = 'https://www.alphavantage.co/query'
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data_json = response.json()
            
            # Parse response (simplified)
            time_series_key = [k for k in data_json.keys() if 'Time Series' in k][0]
            time_series = data_json[time_series_key]
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Rename columns
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.astype(float)
            
            # Filter by date range
            df = df.loc[start_date:end_date]
            
            return self.validate_data(df)
        
        except Exception as e:
            log.error(f"Alpha Vantage API error: {e}")
            raise
    
    def fetch_quote(self, symbol: str) -> Dict:
        """Fetch real-time quote from Alpha Vantage."""
        import requests
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key,
        }
        
        url = 'https://www.alphavantage.co/query'
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data_json = response.json()
            
            quote = data_json.get('Global Quote', {})
            
            return {
                'symbol': symbol,
                'price': float(quote.get('05. price', 0)),
                'volume': float(quote.get('06. volume', 0)),
                'timestamp': datetime.now(),
            }
        
        except Exception as e:
            log.error(f"Alpha Vantage API error: {e}")
            raise


class CSVProvider(DataProvider):
    """CSV file data provider for local data."""
    
    def __init__(self, data_dir: Union[str, Path], config: Optional[Dict] = None):
        super().__init__('CSV', config)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_historical(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = '1d',
    ) -> pd.DataFrame:
        """Fetch historical data from CSV file."""
        filepath = self.data_dir / f"{symbol}_{interval}.csv"
        
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        log.info(f"Reading {symbol} from CSV: {filepath}")
        
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        df = df.sort_index()
        
        # Filter by date range
        df = df.loc[start_date:end_date]
        
        return self.validate_data(df)
    
    def fetch_quote(self, symbol: str) -> Dict:
        """Fetch latest data point from CSV (simulated quote)."""
        # Get latest row from historical data
        try:
            df = self.fetch_historical(symbol, '2020-01-01', datetime.now(), '1d')
            latest = df.iloc[-1]
            
            return {
                'symbol': symbol,
                'price': latest['Close'],
                'volume': latest['Volume'],
                'timestamp': df.index[-1],
            }
        except Exception as e:
            log.error(f"CSV quote error: {e}")
            raise
    
    def save_data(self, symbol: str, data: pd.DataFrame, interval: str = '1d') -> None:
        """Save data to CSV file."""
        filepath = self.data_dir / f"{symbol}_{interval}.csv"
        data.to_csv(filepath)
        log.info(f"Saved {symbol} data to {filepath}")


class SimulatedProvider(DataProvider):
    """Simulated data provider for testing."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__('Simulated', config)
        self.seed = config.get('seed', 42) if config else 42
    
    def fetch_historical(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = '1d',
    ) -> pd.DataFrame:
        """Generate simulated historical data."""
        log.info(f"Generating simulated data for {symbol}: {start_date} to {end_date}")
        
        # Convert to datetime
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Generate date range
        dates = pd.date_range(start=start, end=end, freq='D')
        n_periods = len(dates)
        
        # Simulate price with geometric Brownian motion
        np.random.seed(self.seed)
        
        S0 = 100.0  # Initial price
        mu = 0.0002  # Drift (daily)
        sigma = 0.02  # Volatility (daily)
        
        returns = np.random.normal(mu, sigma, n_periods)
        prices = S0 * np.exp(np.cumsum(returns))
        
        # Generate OHLCV
        close = prices
        open_prices = close * (1 + np.random.normal(0, 0.005, n_periods))
        high = np.maximum(open_prices, close) * (1 + np.abs(np.random.normal(0, 0.01, n_periods)))
        low = np.minimum(open_prices, close) * (1 - np.abs(np.random.normal(0, 0.01, n_periods)))
        volume = np.random.lognormal(15, 0.5, n_periods)
        
        df = pd.DataFrame({
            'Open': open_prices,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume,
        }, index=dates)
        
        return self.validate_data(df)
    
    def fetch_quote(self, symbol: str) -> Dict:
        """Generate simulated quote."""
        price = 100 + np.random.normal(0, 5)
        
        return {
            'symbol': symbol,
            'price': price,
            'bid': price - 0.01,
            'ask': price + 0.01,
            'volume': int(np.random.lognormal(15, 0.5)),
            'timestamp': datetime.now(),
        }


class DataProviderFactory:
    """Factory for creating data providers."""
    
    _providers = {
        'yahoo': YahooFinanceProvider,
        'alphavantage': AlphaVantageProvider,
        'csv': CSVProvider,
        'simulated': SimulatedProvider,
    }
    
    @classmethod
    def create(cls, provider_type: str, **kwargs) -> DataProvider:
        """
        Create a data provider instance.
        
        Parameters
        ----------
        provider_type : str
            Type of provider ('yahoo', 'alphavantage', 'csv', 'simulated')
        **kwargs
            Provider-specific configuration
        
        Returns
        -------
        DataProvider
            Provider instance
        
        Examples
        --------
        >>> provider = DataProviderFactory.create('yahoo')
        >>> provider = DataProviderFactory.create('alphavantage', api_key='YOUR_KEY')
        >>> provider = DataProviderFactory.create('csv', data_dir='./data')
        """
        provider_cls = cls._providers.get(provider_type.lower())
        
        if not provider_cls:
            raise ValueError(f"Unknown provider: {provider_type}. Available: {list(cls._providers.keys())}")
        
        return provider_cls(**kwargs)
    
    @classmethod
    def available_providers(cls) -> List[str]:
        """Get list of available provider types."""
        return list(cls._providers.keys())


class MultiProviderAggregator:
    """
    Aggregates data from multiple providers with fallback.
    
    Attempts to fetch from providers in order until successful.
    """
    
    def __init__(self, providers: List[Union[str, DataProvider]]):
        """
        Initialize aggregator.
        
        Parameters
        ----------
        providers : list
            List of provider names or DataProvider instances
        """
        self.providers = []
        
        for p in providers:
            if isinstance(p, str):
                self.providers.append(DataProviderFactory.create(p))
            elif isinstance(p, DataProvider):
                self.providers.append(p)
            else:
                raise ValueError(f"Invalid provider: {p}")
        
        log.info(f"Initialized aggregator with {len(self.providers)} providers")
    
    def fetch_with_fallback(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = '1d',
    ) -> pd.DataFrame:
        """
        Fetch data with provider fallback.
        
        Tries each provider in order until successful.
        """
        errors = []
        
        for provider in self.providers:
            try:
                log.info(f"Attempting to fetch from {provider.name}")
                data = provider.fetch_historical(symbol, start_date, end_date, interval)
                log.info(f"Successfully fetched from {provider.name}")
                return data
            
            except Exception as e:
                log.warning(f"{provider.name} failed: {e}")
                errors.append((provider.name, str(e)))
        
        # All providers failed
        error_msg = "\n".join([f"  - {name}: {err}" for name, err in errors])
        raise RuntimeError(f"All providers failed:\n{error_msg}")
    
    def fetch_quote_with_fallback(self, symbol: str) -> Dict:
        """Fetch quote with provider fallback."""
        errors = []
        
        for provider in self.providers:
            try:
                log.info(f"Attempting quote from {provider.name}")
                quote = provider.fetch_quote(symbol)
                log.info(f"Successfully fetched quote from {provider.name}")
                return quote
            
            except Exception as e:
                log.warning(f"{provider.name} failed: {e}")
                errors.append((provider.name, str(e)))
        
        # All providers failed
        error_msg = "\n".join([f"  - {name}: {err}" for name, err in errors])
        raise RuntimeError(f"All providers failed:\n{error_msg}")
