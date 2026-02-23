"""
Global pytest fixtures — shared across all test modules.
"""

import os
import pytest

# Set test environment before any imports
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ENABLE_AUTH", "false")
os.environ.setdefault("ENABLE_AUDIT_LOG", "false")
os.environ.setdefault("ENABLE_RATE_LIMITING", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest.fixture(scope="session")
def sample_price_data():
    """Return a minimal OHLCV DataFrame for use in unit tests."""
    import numpy as np
    import pandas as pd

    np.random.seed(42)
    n = 252  # 1 trading year
    dates = pd.date_range("2024-01-01", periods=n, freq="B")

    prices = 100 * np.exp(np.cumsum(np.random.normal(0.0003, 0.015, n)))
    df = pd.DataFrame(
        {
            "Open": prices * (1 + np.random.normal(0, 0.002, n)),
            "High": prices * (1 + np.abs(np.random.normal(0, 0.005, n))),
            "Low": prices * (1 - np.abs(np.random.normal(0, 0.005, n))),
            "Close": prices,
            "Volume": np.random.randint(1_000_000, 10_000_000, n).astype(float),
        },
        index=dates,
    )
    return df


@pytest.fixture(scope="session")
def sample_returns(sample_price_data):
    """Daily log returns derived from sample price data."""
    import numpy as np

    return np.log(sample_price_data["Close"] / sample_price_data["Close"].shift(1)).dropna()


@pytest.fixture(scope="session")
def multi_asset_returns():
    """Multi-asset return DataFrame (5 tickers, 2 years) for portfolio tests."""
    import numpy as np
    import pandas as pd

    np.random.seed(99)
    n = 504
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    dates = pd.date_range("2023-01-01", periods=n, freq="B")

    data = {}
    for t in tickers:
        mu = np.random.uniform(0.0002, 0.0008)
        sigma = np.random.uniform(0.01, 0.025)
        data[t] = np.random.normal(mu, sigma, n)

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def bs_base_params():
    """Standard Black-Scholes parameters for ATM option."""
    return {"S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20}


@pytest.fixture
def mock_redis(monkeypatch):
    """Fake Redis client — no real Redis required for unit tests."""
    try:
        import fakeredis

        return fakeredis.FakeRedis(decode_responses=True)
    except ImportError:
        pytest.skip("fakeredis not installed")
