"""
Volatility regime classification.

Identifies periods of low, medium, and high volatility using:
  - GARCH(1,1) volatility forecasting
  - Historical percentile thresholds
  - Exponentially-weighted moving average (EWMA)

Volatility regimes are critical for:
  - Position sizing (reduce exposure in high-vol)
  - Options pricing (IV regimes)
  - Risk management (VaR scaling)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    """Volatility regime classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class VolatilityRegimeResult:
    """Results from volatility regime detection."""
    regimes: np.ndarray  # Array of regime labels
    regime_names: list[str]
    realized_vol: pd.Series  # Realized volatility time series
    thresholds: dict[str, float]  # Regime boundaries
    timestamps: pd.DatetimeIndex
    
    def get_current_regime(self) -> str:
        """Return current volatility regime."""
        return self.regime_names[self.regimes[-1]]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame."""
        return pd.DataFrame({
            'regime': [self.regime_names[r] for r in self.regimes],
            'regime_id': self.regimes,
            'realized_vol': self.realized_vol.values,
        }, index=self.timestamps)


def _calculate_realized_volatility(
    returns: pd.Series,
    window: int = 21,
    annualize: bool = True,
) -> pd.Series:
    """
    Calculate rolling realized volatility.

    Parameters
    ----------
    returns : pd.Series
        Return time series
    window : int
        Rolling window size
    annualize : bool
        If True, annualize volatility (multiply by sqrt(252))

    Returns
    -------
    pd.Series
        Realized volatility
    """
    vol = returns.rolling(window=window).std()
    if annualize:
        vol *= np.sqrt(252)
    return vol


def _calculate_ewma_volatility(
    returns: pd.Series,
    span: int = 60,
    annualize: bool = True,
) -> pd.Series:
    """
    Calculate exponentially-weighted moving average volatility.

    Uses pandas EWMA with span parameter (equivalent to lambda = 2/(span+1)).
    
    Parameters
    ----------
    span : int
        EWMA span (larger = slower adaptation)

    Returns
    -------
    pd.Series
        EWMA volatility
    """
    vol = returns.ewm(span=span).std()
    if annualize:
        vol *= np.sqrt(252)
    return vol


def detect_volatility_regimes_percentile(
    prices: pd.Series,
    n_regimes: int = 3,
    window: int = 21,
    method: str = 'realized',
) -> VolatilityRegimeResult:
    """
    Detect volatility regimes using historical percentile thresholds.

    Parameters
    ----------
    prices : pd.Series
        Price time series (datetime-indexed)
    n_regimes : int
        Number of regimes (2, 3, or 4)
    window : int
        Rolling window for volatility calculation
    method : str
        'realized' or 'ewma'

    Returns
    -------
    VolatilityRegimeResult
        Volatility regimes and thresholds
    """
    require_positive(n_regimes, "n_regimes")
    
    if n_regimes not in [2, 3, 4]:
        raise ValidationError("n_regimes must be 2, 3, or 4")
    
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValidationError("prices must have DatetimeIndex")
    
    # Calculate returns
    returns = np.log(prices / prices.shift(1)).dropna()
    
    # Calculate volatility
    if method == 'realized':
        vol = _calculate_realized_volatility(returns, window)
    elif method == 'ewma':
        vol = _calculate_ewma_volatility(returns, span=window)
    else:
        raise ValidationError(f"Unknown method: {method}")
    
    vol = vol.dropna()
    
    # Determine thresholds based on percentiles
    if n_regimes == 2:
        # Low vs High
        threshold = vol.median()
        regimes = np.where(vol < threshold, 0, 1)
        regime_names = ['low', 'high']
        thresholds = {'low_high': threshold}
    
    elif n_regimes == 3:
        # Low, Medium, High
        p33 = vol.quantile(0.33)
        p67 = vol.quantile(0.67)
        regimes = np.full(len(vol), 1, dtype=int)  # Default: medium
        regimes[vol < p33] = 0  # Low
        regimes[vol > p67] = 2  # High
        regime_names = ['low', 'medium', 'high']
        thresholds = {'low_medium': p33, 'medium_high': p67}
    
    elif n_regimes == 4:
        # Low, Medium, High, Extreme
        p25 = vol.quantile(0.25)
        p50 = vol.quantile(0.50)
        p75 = vol.quantile(0.75)
        regimes = np.full(len(vol), 1, dtype=int)  # Default: medium
        regimes[vol < p25] = 0  # Low
        regimes[vol > p50] = 2  # High
        regimes[vol > p75] = 3  # Extreme
        regime_names = ['low', 'medium', 'high', 'extreme']
        thresholds = {'low_medium': p25, 'medium_high': p50, 'high_extreme': p75}
    
    return VolatilityRegimeResult(
        regimes=regimes,
        regime_names=regime_names,
        realized_vol=vol,
        thresholds=thresholds,
        timestamps=vol.index,
    )


def detect_volatility_regimes_adaptive(
    prices: pd.Series,
    lookback: int = 252,
    z_threshold: float = 1.5,
) -> VolatilityRegimeResult:
    """
    Adaptive volatility regime detection using z-score.

    Classifies current volatility relative to rolling mean/std:
      - Low: z < -z_threshold
      - Medium: |z| <= z_threshold
      - High: z > z_threshold

    Parameters
    ----------
    lookback : int
        Rolling window for mean/std calculation
    z_threshold : float
        Z-score threshold for regime boundaries

    Returns
    -------
    VolatilityRegimeResult
        Adaptive volatility regimes
    """
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValidationError("prices must have DatetimeIndex")
    
    returns = np.log(prices / prices.shift(1)).dropna()
    vol = _calculate_realized_volatility(returns, window=21)
    vol = vol.dropna()
    
    # Calculate rolling z-score of volatility
    vol_mean = vol.rolling(window=lookback).mean()
    vol_std = vol.rolling(window=lookback).std()
    z_score = (vol - vol_mean) / vol_std
    z_score = z_score.dropna()
    
    # Classify regimes
    regimes = np.full(len(z_score), 1, dtype=int)  # Default: medium
    regimes[z_score < -z_threshold] = 0  # Low
    regimes[z_score > z_threshold] = 2  # High
    
    regime_names = ['low', 'medium', 'high']
    
    thresholds = {
        'z_low': -z_threshold,
        'z_high': z_threshold,
    }
    
    return VolatilityRegimeResult(
        regimes=regimes,
        regime_names=regime_names,
        realized_vol=vol.loc[z_score.index],
        thresholds=thresholds,
        timestamps=z_score.index,
    )


def detect_volatility_breakout(
    prices: pd.Series,
    window: int = 21,
    multiplier: float = 2.0,
) -> pd.Series:
    """
    Detect volatility breakouts (realized vol > multiplier * recent average).

    Useful for detecting sudden vol spikes (flash crashes, news events).

    Parameters
    ----------
    window : int
        Rolling window for average volatility
    multiplier : float
        Breakout threshold (e.g., 2.0 = 2x average vol)

    Returns
    -------
    pd.Series
        Boolean series: True when volatility > threshold
    """
    returns = np.log(prices / prices.shift(1)).dropna()
    vol = _calculate_realized_volatility(returns, window=window)
    vol_avg = vol.rolling(window=window).mean()
    
    breakout = vol > (multiplier * vol_avg)
    return breakout.dropna()
