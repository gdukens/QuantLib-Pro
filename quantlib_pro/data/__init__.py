"""Market data pipeline: resilient fetching, multi-tier caching, quality validation."""

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
