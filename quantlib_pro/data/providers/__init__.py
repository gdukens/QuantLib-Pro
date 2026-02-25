"""
Alternative data provider integrations.

Supports multiple market data sources with unified interface.
"""

from .alpha_vantage import AlphaVantageProvider, create_alpha_vantage_fetcher
from .factset import FactsetProvider, create_factset_fetcher
from .capital_iq import CapitalIQProvider, create_capital_iq_fetcher
from .multi_provider import MultiProviderDataFetcher

# Import base class from legacy providers for backward compatibility
from ..providers_legacy import DataProvider

__all__ = [
    "AlphaVantageProvider",
    "FactsetProvider", 
    "CapitalIQProvider",
    "create_alpha_vantage_fetcher",
    "create_factset_fetcher",
    "create_capital_iq_fetcher",
    "MultiProviderDataFetcher",
    "DataProvider",  # For backward compatibility
]
