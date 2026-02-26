"""
QuantLib Pro Python SDK
~~~~~~~~~~~~~~~~~~~~~~~

A Python client library for the QuantLib Pro quantitative finance API.

Usage::

    from quantlib_api import QuantLibClient

    client = QuantLibClient(
        base_url="http://localhost:8000",
        username="demo",
        password="demo123",
        auto_login=True
    )

    result = client.portfolio.optimize(
        tickers=["AAPL", "GOOGL", "MSFT"],
        budget=100_000,
        optimization_target="sharpe"
    )
    print(result)

:license: MIT
"""

from quantlib_api.client import QuantLibClient
from quantlib_api.exceptions import (
    QuantLibError,
    QuantLibAPIError,
    QuantLibAuthError,
    QuantLibNotFoundError,
    QuantLibRateLimitError,
    QuantLibNetworkError,
    QuantLibValidationError,
)

__version__ = "1.0.0"
__author__ = "tubakhxn"
__all__ = [
    "QuantLibClient",
    "QuantLibError",
    "QuantLibAPIError",
    "QuantLibAuthError",
    "QuantLibNotFoundError",
    "QuantLibRateLimitError",
    "QuantLibNetworkError",
    "QuantLibValidationError",
]
