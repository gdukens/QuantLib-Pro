"""
Shared domain types, dataclasses and enums used across all suites.
Import from here rather than defining the same type in multiple modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional

import pandas as pd


# ------------------------------------------------------------------ enums


class DataSource(str, Enum):
    """Origin / fallback level of a data response."""
    MEMORY_CACHE = "memory_cache"
    REDIS_CACHE = "redis_cache"
    FILE_CACHE = "file_cache"
    YFINANCE = "yfinance"
    ALTERNATIVE_API = "alternative_api"
    SYNTHETIC = "synthetic_DEGRADED_MODE"

    @property
    def is_degraded(self) -> bool:
        return self == DataSource.SYNTHETIC

    @property
    def is_live(self) -> bool:
        return self in (DataSource.YFINANCE, DataSource.ALTERNATIVE_API)


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class RegimeState(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    VOLATILE = "volatile"
    LOW_VOL = "low_volatility"
    CRISIS = "crisis"


# ------------------------------------------------------------------ data containers


@dataclass
class PriceData:
    """Validated OHLCV price data for a single ticker."""
    ticker: str
    df: pd.DataFrame                        # columns: Open/High/Low/Close/Volume
    source: DataSource
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    is_synthetic: bool = False

    def returns(self, method: str = "log") -> pd.Series:
        if method == "log":
            import numpy as np
            return np.log(self.df["Close"] / self.df["Close"].shift(1)).dropna()
        return self.df["Close"].pct_change().dropna()


@dataclass
class OptionContract:
    ticker: str
    strike: float
    expiry: date
    option_type: OptionType
    spot_price: float
    risk_free_rate: float
    volatility: Optional[float] = None      # implied vol if known
    dividend_yield: float = 0.0


@dataclass
class Portfolio:
    """Collection of tickers and their portfolio weights (sum to 1.0)."""
    name: str
    weights: dict[str, float]               # ticker -> weight
    prices: Optional[dict[str, PriceData]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def validate_weights(self) -> bool:
        return abs(sum(self.weights.values()) - 1.0) < 1e-6

    @property
    def tickers(self) -> list[str]:
        return list(self.weights.keys())


@dataclass
class CalculationResult:
    """Wrapper for any calculation output with provenance metadata."""
    calculation_type: str
    inputs: dict
    outputs: dict
    model_version: str
    execution_time_ms: float
    warnings: list[str] = field(default_factory=list)
    calculation_id: Optional[str] = None    # filled by audit log
    timestamp: datetime = field(default_factory=datetime.utcnow)
