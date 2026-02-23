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
from quantlib_pro.data.providers import (
    DataProvider,
    YahooFinanceProvider,
    AlphaVantageProvider,
    CSVProvider,
    SimulatedProvider,
    DataProviderFactory,
    MultiProviderAggregator,
)

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
    # providers
    "DataProvider",
    "YahooFinanceProvider",
    "AlphaVantageProvider",
    "CSVProvider",
    "SimulatedProvider",
    "DataProviderFactory",
    "MultiProviderAggregator",
]
