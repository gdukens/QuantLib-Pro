"""
Streamlit Caching Strategies

Week 13: Performance optimization through strategic caching.
"""

import streamlit as st
import pandas as pd
import numpy as np
from functools import wraps
from typing import Any, Callable
import hashlib
import json


def cache_data_with_ttl(ttl: int = 3600):
    """
    Decorator for caching data with time-to-live.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
    
    Usage:
        @cache_data_with_ttl(ttl=300)  # 5 minutes
        def expensive_calculation():
            ...
    """
    return st.cache_data(ttl=ttl, show_spinner=False)


def cache_resource_singleton():
    """
    Decorator for caching resources (connections, models, etc).
    These are shared across all users and sessions.
    
    Usage:
        @cache_resource_singleton()
        def get_database_connection():
            ...
    """
    return st.cache_resource(show_spinner=False)


@cache_data_with_ttl(ttl=3600)
def cached_market_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch and cache market data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        DataFrame with price data
    """
    from quantlib_pro.data.market_data import MarketDataProvider
    
    provider = MarketDataProvider()
    df = provider.get_stock_data(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date
    )
    
    if df.empty:
        raise ValueError(f"No data available for {ticker}")
    
    # Calculate returns
    returns = df['Close'].pct_change().dropna()
    
    return pd.DataFrame({
        "date": df.index,
        "close": df['Close'].values,
        "returns": returns.values if len(returns) > 0 else [],
    })


@cache_data_with_ttl(ttl=1800)
def cached_portfolio_optimization(
    tickers: tuple,  # Must be hashable (tuple, not list)
    weights: tuple,
    risk_free_rate: float,
    num_points: int,
) -> dict:
    """
    Cache portfolio optimization results.
    
    Args:
        tickers: Tuple of ticker symbols
        weights: Tuple of portfolio weights
        risk_free_rate: Risk-free rate
        num_points: Number of efficient frontier points
    
    Returns:
        Dict with optimization results
    """
    from quantlib_pro.portfolio.optimizer import PortfolioOptimizer
    from quantlib_pro.data.market_data import MarketDataProvider
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Fetch real market data
    provider = MarketDataProvider()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    returns_data = {}
    for ticker in tickers:
        df = provider.get_stock_data(ticker, start_date, end_date)
        if not df.empty:
            returns_data[ticker] = df['Close'].pct_change().dropna()
    
    if not returns_data:
        raise ValueError("No data available for any ticker")
    
    # Align returns
    returns_df = pd.DataFrame(returns_data)
    expected_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    
    # Run optimization
    optimizer = PortfolioOptimizer(
        expected_returns=expected_returns,
        cov_matrix=cov_matrix,
        risk_free_rate=risk_free_rate,
        tickers=list(tickers)
    )
    
    frontier = optimizer.efficient_frontier(num_points=num_points)
    
    return {
        "returns": frontier['returns'],
        "volatilities": frontier['volatilities'],
        "sharpe_ratios": frontier['sharpe_ratios'],
        "optimal_idx": frontier.get('optimal_idx', 0),
    }


@cache_data_with_ttl(ttl=1800)
def cached_option_pricing(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    risk_free_rate: float,
    option_type: str,
) -> dict:
    """
    Cache option pricing calculations.
    
    Args:
        spot: Spot price
        strike: Strike price
        time_to_expiry: Time to expiration (years)
        volatility: Implied volatility
        risk_free_rate: Risk-free rate
        option_type: 'call' or 'put'
    
    Returns:
        Dict with option price and Greeks
    """
    from quantlib_pro.options.black_scholes import price_with_greeks
    
    return price_with_greeks(
        spot=spot,
        strike=strike,
        T=time_to_expiry,
        r=risk_free_rate,
        sigma=volatility,
        option_type=option_type,
    )


@cache_data_with_ttl(ttl=600)
def cached_var_calculation(
    returns_hash: str,  # Hash of returns array
    confidence_level: float,
    method: str,
) -> dict:
    """
    Cache VaR calculations.
    
    Note: We hash the returns array because numpy arrays aren't hashable.
    
    Args:
        returns_hash: MD5 hash of returns array
        confidence_level: Confidence level (0.95, 0.99, etc)
        method: VaR method (historical, parametric, monte_carlo)
    
    Returns:
        Dict with VaR results
    """
    # This is a placeholder - actual implementation would unhash returns
    # and call calculate_var
    return {
        "var": -0.02,
        "cvar": -0.03,
        "confidence_level": confidence_level,
        "method": method,
    }


def hash_numpy_array(arr: np.ndarray) -> str:
    """
    Create a hash of a numpy array for caching.
    
    Args:
        arr: Numpy array
    
    Returns:
        MD5 hash string
    """
    return hashlib.md5(arr.tobytes()).hexdigest()


@cache_resource_singleton()
def get_hmm_model():
    """
    Load and cache HMM model.
    This is expensive to initialize, so cache it.
    
    Returns:
        Fitted HMM model
    """
    from hmmlearn import hmm
    
    # Initialize model (would be pre-trained in production)
    model = hmm.GaussianHMM(n_components=3, covariance_type="full", n_iter=100)
    
    return model


@cache_data_with_ttl(ttl=3600)
def cached_correlation_matrix(tickers: tuple, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Cache correlation matrix calculation.
    
    Args:
        tickers: Tuple of ticker symbols
        start_date: Start date
        end_date: End date
    
    Returns:
        Correlation matrix DataFrame
    """
    from quantlib_pro.data.market_data import MarketDataProvider
    
    provider = MarketDataProvider()
    returns_dict = {}
    
    for ticker in tickers:
        try:
            df = provider.get_stock_data(ticker, start_date, end_date)
            if not df.empty:
                returns_dict[ticker] = df['Close'].pct_change().dropna()
        except Exception as e:
            # Skip tickers that fail to load
            continue
    
    if not returns_dict:
        raise ValueError("No data available for any ticker")
    
    returns_df = pd.DataFrame(returns_dict)
    return returns_df.corr()


@cache_data_with_ttl(ttl=300)
def cached_volatility_surface(
    spot: float,
    strikes: tuple,
    maturities: tuple,
    atm_vol: float,
) -> np.ndarray:
    """
    Cache volatility surface construction.
    
    Args:
        spot: Spot price
        strikes: Tuple of strike prices
        maturities: Tuple of maturities (days)
        atm_vol: At-the-money volatility
    
    Returns:
        2D array of implied volatilities
    """
    surface = np.zeros((len(strikes), len(maturities)))
    
    for i, strike in enumerate(strikes):
        for j, maturity in enumerate(maturities):
            moneyness = np.log(strike / spot)
            time_years = maturity / 365.0
            
            # Simple parametric model
            term_factor = 1.0 + 0.3 * np.exp(-time_years * 0.5)
            skew_factor = moneyness * (1 - 0.5 * moneyness)
            convexity_factor = 0.3 * moneyness ** 2
            
            vol = atm_vol * term_factor + skew_factor + convexity_factor
            surface[i, j] = max(vol, 0.05)
    
    return surface


def clear_all_caches():
    """Clear all Streamlit caches."""
    st.cache_data.clear()
    st.cache_resource.clear()


def get_cache_stats() -> dict:
    """
    Get statistics about cache usage.
    
    Returns:
        Dict with cache statistics
    """
    # Streamlit doesn't expose cache stats directly
    # This is a placeholder for monitoring
    return {
        "data_cache_enabled": True,
        "resource_cache_enabled": True,
        "ttl_default": 3600,
    }


# Session state helpers for caching across page navigations

def get_session_state(key: str, default: Any = None) -> Any:
    """
    Get value from session state with default.
    
    Args:
        key: Session state key
        default: Default value if key not found
    
    Returns:
        Value from session state or default
    """
    return st.session_state.get(key, default)


def set_session_state(key: str, value: Any):
    """
    Set value in session state.
    
    Args:
        key: Session state key
        value: Value to store
    """
    st.session_state[key] = value


def memoize_in_session(key: str, default: Any = None):
    """
    Decorator to memoize function results in session state.
    
    Args:
        key: Session state key
        default: Default value
    
    Usage:
        @memoize_in_session("expensive_calculation")
        def expensive_calculation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key not in st.session_state:
                st.session_state[key] = func(*args, **kwargs)
            return st.session_state[key]
        return wrapper
    return decorator


# Caching strategy guidelines

CACHING_GUIDELINES = """
# Streamlit Caching Best Practices

## Use @st.cache_data for:
- DataFrame transformations
- API calls
- Database queries
- Computationally expensive calculations
- Data loading/processing

## Use @st.cache_resource for:
- Database connections
- ML model loading
- API clients
- Thread pools
- Any object that should be shared across all users

## Use session_state for:
- User-specific temporary data
- Form inputs
- Page navigation state
- Calculated results that don't need to persist

## TTL (Time-to-Live) Guidelines:
- Real-time data: 60-300 seconds
- Intraday data: 300-900 seconds (5-15 minutes)
- Daily data: 1800-3600 seconds (30-60 minutes)
- Static/reference data: 7200+ seconds (2+ hours)

## Cache Invalidation:
- Automatic: Based on TTL
- Manual: Call st.cache_data.clear() or st.cache_resource.clear()
- Parameter-based: Cache is invalidated when function arguments change

## Performance Tips:
1. Cache at the highest level possible
2. Use tuples instead of lists for hashable arguments
3. Hash large numpy arrays before passing to cached functions
4. Clear caches during deployments
5. Monitor memory usage with large caches
"""
