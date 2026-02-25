"""Market data pipeline: resilient fetching, multi-tier caching, quality validation, multi-provider support."""

from quantlib_pro.data.cache import get_dataframe, set_dataframe
from quantlib_pro.data.fetcher import DataFetchError, ResilientDataFetcher
from quantlib_pro.data.quality import (
    DataQualityError,
    DataQualityValidator,
    OHLCV_CONTRACT,
    PORTFOLIO_CONTRACT,
    QualityContract,
    QualityReport,
)
# Legacy providers (providers.py) - kept for backward compatibility
try:
    from quantlib_pro.data.providers_legacy import (
        DataProvider,
        YahooFinanceProvider,
        CSVProvider,
        SimulatedProvider,
        DataProviderFactory,
        MultiProviderAggregator,
    )
except ImportError:
    # If legacy providers don't exist, skip them
    DataProvider = None
    YahooFinanceProvider = None
    CSVProvider = None
    SimulatedProvider = None
    DataProviderFactory = None
    MultiProviderAggregator = None

__all__ = [
    # fetcher
    "ResilientDataFetcher",
    "DataFetchError",
    # cache helpers
    "get_dataframe",
    "set_dataframe",
    # quality
    "DataQualityValidator",
    "DataQualityError",
    "QualityContract",
    "QualityReport",
    "OHLCV_CONTRACT",
    "PORTFOLIO_CONTRACT",
]

# Add legacy providers to __all__ if they're available
if DataProvider is not None:
    __all__.extend([
        "DataProvider",
        "YahooFinanceProvider",
        "CSVProvider",
        "SimulatedProvider",
        "DataProviderFactory",
        "MultiProviderAggregator",
    ])
