"""
Market data provider - unified interface for fetching financial data.

This module provides a high-level interface to the ResilientDataFetcher
for easier use in UI components.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from quantlib_pro.data.fetcher import ResilientDataFetcher, DataFetchError
from quantlib_pro.data.providers import DataProvider

log = logging.getLogger(__name__)


class MarketDataProvider:
    """
    High-level market data provider with caching and fallback.
    
    This class wraps the ResilientDataFetcher to provide a simpler
    interface for UI components and analysis tools.
    
    Parameters
    ----------
    redis_client : optional
        Pre-built Redis client for caching (default: None)
    cache_ttl : int
        Cache time-to-live in seconds (default: 3600 = 1 hour)
    """
    
    def __init__(self, redis_client=None, cache_ttl=3600):
        self.fetcher = ResilientDataFetcher(
            redis_client=redis_client,
            cache_ttl=cache_ttl
        )
    
    def get_stock_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Fetch historical stock price data.
        
        Parameters
        ----------
        ticker : str
            Stock ticker symbol (e.g., 'AAPL', 'SPY')
        start_date : str, optional
            Start date in 'YYYY-MM-DD' format
        end_date : str, optional
            End date in 'YYYY-MM-DD' format
        period : str, optional
            Period string ('1y', '6mo', '3mo', etc.) if dates not specified
        
        Returns
        -------
        pd.DataFrame
            DataFrame with OHLCV columns and DatetimeIndex
        
        Raises
        ------
        DataFetchError
            If data cannot be fetched from any source
        """
        try:
            result = self.fetcher.fetch(
                ticker=ticker,
                start=start_date,
                end=end_date,
                period=period
            )
            return result.df
        except DataFetchError as e:
            log.error(f"Failed to fetch data for {ticker}: {e}")
            raise
    
    def get_multiple_stocks(
        self,
        tickers: list[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks.
        
        Parameters
        ----------
        tickers : list[str]
            List of ticker symbols
        start_date, end_date, period : optional
            Same as get_stock_data()
        
        Returns
        -------
        dict[str, pd.DataFrame]
            Dictionary mapping ticker to DataFrame
        """
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = self.get_stock_data(
                    ticker, start_date, end_date, period
                )
                log.info(f"Fetched data for {ticker}")
            except DataFetchError as e:
                log.warning(f"Skipping {ticker}: {e}")
        
        return results
    
    def get_returns(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.Series:
        """
        Fetch historical returns (percent change in adjusted close).
        
        Returns
        -------
        pd.Series
            Daily returns as decimal (e.g., 0.01 = 1% return)
        """
        data = self.get_stock_data(ticker, start_date, end_date, period)
        
        # Use Adj Close if available, otherwise Close
        price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
        returns = data[price_col].pct_change().dropna()
        
        return returns
    
    def get_correlation_matrix(
        self,
        tickers: list[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for a set of stocks.
        
        Parameters
        ----------
        tickers : list[str]
            List of ticker symbols
        start_date, end_date, period : optional
            Date range parameters
        
        Returns
        -------
        pd.DataFrame
            Correlation matrix (tickers x tickers)
        """
        # Fetch returns for all tickers
        returns_dict = {}
        for ticker in tickers:
            try:
                returns_dict[ticker] = self.get_returns(
                    ticker, start_date, end_date, period
                )
            except DataFetchError:
                log.warning(f"Skipping {ticker} in correlation calculation")
        
        if not returns_dict:
            raise DataFetchError("No data available for correlation matrix")
        
        # Combine into DataFrame and calculate correlation
        returns_df = pd.DataFrame(returns_dict)
        return returns_df.corr()
    
    def get_covariance_matrix(
        self,
        tickers: list[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Calculate covariance matrix for a set of stocks.
        
        Returns
        -------
        pd.DataFrame
            Covariance matrix (annualized)
        """
        returns_dict = {}
        for ticker in tickers:
            try:
                returns_dict[ticker] = self.get_returns(
                    ticker, start_date, end_date, period
                )
            except DataFetchError:
                log.warning(f"Skipping {ticker} in covariance calculation")
        
        if not returns_dict:
            raise DataFetchError("No data available for covariance matrix")
        
        returns_df = pd.DataFrame(returns_dict)
        # Annualize covariance (assuming daily data, 252 trading days)
        return returns_df.cov() * 252
    
    def get_expected_returns(
        self,
        tickers: list[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.Series:
        """
        Calculate expected returns (historical mean).
        
        Returns
        -------
        pd.Series
            Dictionary of expected annual returns
        """
        expected_returns = {}
        for ticker in tickers:
            try:
                returns = self.get_returns(ticker, start_date, end_date, period)
                # Annualize mean return (assuming 252 trading days)
                expected_returns[ticker] = returns.mean() * 252
            except DataFetchError:
                log.warning(f"Skipping {ticker} in expected returns calculation")
        
        return pd.Series(expected_returns)
