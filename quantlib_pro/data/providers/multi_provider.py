"""
Multi-provider data fetcher with automatic failover.

Combines multiple data providers with intelligent fallback.
"""

import logging
from typing import Optional, Callable

import pandas as pd

from quantlib_pro.data.fetcher import ResilientDataFetcher
from quantlib_pro.data.providers.alpha_vantage import create_alpha_vantage_fetcher
from quantlib_pro.data.providers.factset import create_factset_fetcher

log = logging.getLogger(__name__)


class MultiProviderDataFetcher:
    """
    Enhanced data fetcher supporting multiple premium providers.
    
    Fallback hierarchy:
    1. Memory cache (L1)
    2. Redis cache (L2) 
    3. File cache (L3)
    4. Yahoo Finance (primary free source)
    5. Alpha Vantage (fallback #1)
    6. FactSet (fallback #2)
    7. Capital IQ (fallback #3, when available)
    8. Synthetic data (GBM simulation)
    
    Parameters
    ----------
    redis_client : optional
        Redis client for L2 cache
    cache_ttl : int
        Cache time-to-live in seconds
    enable_alpha_vantage : bool
        Enable Alpha Vantage as fallback (default: True)
    enable_factset : bool
        Enable FactSet as fallback (default: False, requires credentials)
    enable_capital_iq : bool
        Enable Capital IQ as fallback (default: False, not yet implemented)
    alpha_vantage_key : str, optional
        Alpha Vantage API key (or set ALPHA_VANTAGE_API_KEY env var)
    factset_username : str, optional
        FactSet username (or set FACTSET_USERNAME env var)
    factset_api_key : str, optional
        FactSet API key (or set FACTSET_API_KEY env var)
    
    Examples
    --------
    >>> # Use with Alpha Vantage fallback
    >>> fetcher = MultiProviderDataFetcher(
    ...     enable_alpha_vantage=True,
    ...     alpha_vantage_key="YOUR_KEY"
    ... )
    >>> data = fetcher.fetch("AAPL", period="1y")
    
    >>> # Use with multiple providers
    >>> fetcher = MultiProviderDataFetcher(
    ...     enable_alpha_vantage=True,
    ...     enable_factset=True,
    ...     factset_username="your-username",
    ...     factset_api_key="your-key"
    ... )
    >>> data = fetcher.fetch("AAPL-US", start="2024-01-01", end="2024-12-31")
    """
    
    def __init__(
        self,
        redis_client=None,
        cache_ttl: int = 3600,
        enable_alpha_vantage: bool = True,
        enable_factset: bool = False,
        enable_capital_iq: bool = False,
        alpha_vantage_key: Optional[str] = None,
        factset_username: Optional[str] = None,
        factset_api_key: Optional[str] = None,
        capital_iq_client_id: Optional[str] = None,
        capital_iq_client_secret: Optional[str] = None,
    ):
        self.providers = []
        
        # Try to configure providers in priority order
        if enable_alpha_vantage:
            try:
                av_fetcher = create_alpha_vantage_fetcher(api_key=alpha_vantage_key)
                self.providers.append(("Alpha Vantage", av_fetcher))
                log.info("✅ Alpha Vantage provider configured")
            except ValueError as e:
                log.warning(f"⚠️  Alpha Vantage not configured: {e}")
        
        if enable_factset:
            try:
                fs_fetcher = create_factset_fetcher(
                    username=factset_username,
                    api_key=factset_api_key
                )
                self.providers.append(("FactSet", fs_fetcher))
                log.info("✅ FactSet provider configured")
            except ValueError as e:
                log.warning(f"⚠️  FactSet not configured: {e}")
        
        if enable_capital_iq:
            log.warning(
                "⚠️  Capital IQ provider not yet implemented. "
                "This feature is coming soon."
            )
        
        # Create composite fallback function
        alt_api_fn = self._create_composite_fetcher() if self.providers else None
        
        # Initialize resilient fetcher with all configured providers
        self._fetcher = ResilientDataFetcher(
            redis_client=redis_client,
            cache_ttl=cache_ttl,
            alt_api_fn=alt_api_fn,
        )
        
        log.info(
            f"MultiProviderDataFetcher initialized with {len(self.providers)} "
            f"alternative provider(s): {[name for name, _ in self.providers]}"
        )
    
    def _create_composite_fetcher(self) -> Callable:
        """
        Create a composite fetcher that tries all configured providers in order.
        
        Returns
        -------
        callable
            Function(ticker, start, end) -> pd.DataFrame
        """
        def composite_fetch(ticker: str, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
            for provider_name, provider_fn in self.providers:
                try:
                    log.debug(f"Trying {provider_name} for {ticker}...")
                    df = provider_fn(ticker, start, end)
                    
                    if df is not None and not df.empty:
                        log.info(f"✅ {provider_name} succeeded for {ticker}")
                        return df
                    else:
                        log.debug(f"{provider_name} returned empty data for {ticker}")
                
                except Exception as e:
                    log.warning(f"❌ {provider_name} failed for {ticker}: {e}")
                    continue
            
            # All providers failed
            log.error(f"All {len(self.providers)} alternative providers failed for {ticker}")
            return None
        
        return composite_fetch
    
    def fetch(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: str = "1y",
    ):
        """
        Fetch data with full provider fallback chain.
        
        Parameters
        ----------
        ticker : str
            Stock symbol (e.g., "AAPL")
        start : str, optional
            Start date "YYYY-MM-DD"
        end : str, optional
            End date "YYYY-MM-DD"
        period : str
            Period (e.g., "1y", "6mo") if start/end not provided
        
        Returns
        -------
        PriceData
            Data with source information
        """
        return self._fetcher.fetch(ticker, start, end, period)
    
    def get_provider_status(self) -> dict:
        """
        Get status of all configured providers.
        
        Returns
        -------
        dict
            Provider status information
        """
        return {
            "configured_providers": len(self.providers),
            "providers": [name for name, _ in self.providers],
            "fallback_chain": [
                "L1: Memory Cache",
                "L2: Redis Cache (if configured)",
                "L3: File Cache",
                "L4: Yahoo Finance",
                *[f"L{5+i}: {name}" for i, (name, _) in enumerate(self.providers)],
                f"L{5+len(self.providers)}: Synthetic Data (GBM)",
            ],
        }
    
    def __repr__(self):
        providers_str = ", ".join([name for name, _ in self.providers])
        return f"MultiProviderDataFetcher(providers=[{providers_str}])"
