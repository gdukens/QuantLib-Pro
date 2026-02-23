"""
Trend regime detection using technical indicators.

Identifies market trend regimes:
  - Uptrend: price > MA, positive momentum
  - Downtrend: price < MA, negative momentum
  - Sideways: choppy, no clear direction

Uses moving averages, ADX (Average Directional Index), and momentum.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


class TrendRegime(Enum):
    """Trend regime classifications."""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"


@dataclass
class TrendRegimeResult:
    """Results from trend regime detection."""
    regimes: np.ndarray
    regime_names: list[str]
    indicators: pd.DataFrame  # MA, momentum, ADX, etc.
    timestamps: pd.DatetimeIndex
    
    def get_current_regime(self) -> str:
        """Return current trend regime."""
        return self.regime_names[self.regimes[-1]]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame."""
        df = pd.DataFrame({
            'regime': [self.regime_names[r] for r in self.regimes],
            'regime_id': self.regimes,
        }, index=self.timestamps)
        return pd.concat([df, self.indicators], axis=1)


def _calculate_sma(prices: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return prices.rolling(window=window).mean()


def _calculate_ema(prices: pd.Series, span: int) -> pd.Series:
    """Exponential moving average."""
    return prices.ewm(span=span, adjust=False).mean()


def _calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (ADX).

    ADX measures trend strength (0-100):
      - ADX < 25: weak trend (sideways)
      - ADX > 25: strong trend (up or down)

    Parameters
    ----------
    high, low, close : pd.Series
        OHLC data
    window : int
        Smoothing period

    Returns
    -------
    pd.Series
        ADX values
    """
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    
    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    pos_dm_series = pd.Series(pos_dm, index=high.index)
    neg_dm_series = pd.Series(neg_dm, index=high.index)
    
    # Smoothed directional indicators
    pos_di = 100 * (pos_dm_series.rolling(window=window).mean() / atr)
    neg_di = 100 * (neg_dm_series.rolling(window=window).mean() / atr)
    
    # ADX
    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    adx = dx.rolling(window=window).mean()
    
    return adx


def detect_trend_regimes_ma(
    prices: pd.Series,
    short_window: int = 50,
    long_window: int = 200,
) -> TrendRegimeResult:
    """
    Detect trend regimes using moving average crossovers.

    Rules:
      - Uptrend: price > MA_short > MA_long
      - Downtrend: price < MA_short < MA_long
      - Sideways: otherwise

    Parameters
    ----------
    prices : pd.Series
        Price time series (datetime-indexed)
    short_window : int
        Short moving average period (e.g., 50)
    long_window : int
        Long moving average period (e.g., 200)

    Returns
    -------
    TrendRegimeResult
        Trend regimes based on MA
    """
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValidationError("prices must have DatetimeIndex")
    
    require_positive(short_window, "short_window")
    require_positive(long_window, "long_window")
    
    if short_window >= long_window:
        raise ValidationError("short_window must be < long_window")
    
    # Calculate moving averages
    ma_short = _calculate_sma(prices, short_window)
    ma_long = _calculate_sma(prices, long_window)
    
    indicators = pd.DataFrame({
        'price': prices,
        'ma_short': ma_short,
        'ma_long': ma_long,
    }).dropna()
    
    # Classify regimes
    regimes = np.full(len(indicators), 2, dtype=int)  # Default: sideways
    
    # Uptrend: price > MA_short AND MA_short > MA_long
    uptrend = (indicators['price'] > indicators['ma_short']) & \
              (indicators['ma_short'] > indicators['ma_long'])
    regimes[uptrend] = 0
    
    # Downtrend: price < MA_short AND MA_short < MA_long
    downtrend = (indicators['price'] < indicators['ma_short']) & \
                (indicators['ma_short'] < indicators['ma_long'])
    regimes[downtrend] = 1
    
    regime_names = ['uptrend', 'downtrend', 'sideways']
    
    return TrendRegimeResult(
        regimes=regimes,
        regime_names=regime_names,
        indicators=indicators,
        timestamps=indicators.index,
    )


def detect_trend_regimes_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    adx_window: int = 14,
    adx_threshold: float = 25.0,
) -> TrendRegimeResult:
    """
    Detect trend regimes using ADX (Average Directional Index).

    Rules:
      - Strong trend: ADX > threshold
      - Weak trend (sideways): ADX <= threshold
      - Direction determined by price vs EMA(50)

    Parameters
    ----------
    high, low, close : pd.Series
        OHLC data
    adx_window : int
        ADX smoothing period
    adx_threshold : float
        ADX threshold for strong trend

    Returns
    -------
    TrendRegimeResult
        Trend regimes based on ADX
    """
    if not isinstance(close.index, pd.DatetimeIndex):
        raise ValidationError("close must have DatetimeIndex")
    
    # Calculate ADX
    adx = _calculate_adx(high, low, close, window=adx_window)
    
    # Calculate EMA for direction
    ema_50 = _calculate_ema(close, span=50)
    
    indicators = pd.DataFrame({
        'close': close,
        'ema_50': ema_50,
        'adx': adx,
    }).dropna()
    
    # Classify regimes
    regimes = np.full(len(indicators), 2, dtype=int)  # Default: sideways
    
    # Strong uptrend: ADX > threshold AND price > EMA
    uptrend = (indicators['adx'] > adx_threshold) & (indicators['close'] > indicators['ema_50'])
    regimes[uptrend] = 0
    
    # Strong downtrend: ADX > threshold AND price < EMA
    downtrend = (indicators['adx'] > adx_threshold) & (indicators['close'] < indicators['ema_50'])
    regimes[downtrend] = 1
    
    regime_names = ['uptrend', 'downtrend', 'sideways']
    
    return TrendRegimeResult(
        regimes=regimes,
        regime_names=regime_names,
        indicators=indicators,
        timestamps=indicators.index,
    )


def detect_trend_regimes_momentum(
    prices: pd.Series,
    momentum_window: int = 20,
    threshold_pct: float = 0.02,
) -> TrendRegimeResult:
    """
    Detect trend regimes using momentum (rate of change).

    Rules:
      - Uptrend: momentum > threshold
      - Downtrend: momentum < -threshold
      - Sideways: |momentum| <= threshold

    Parameters
    ----------
    prices : pd.Series
        Price time series
    momentum_window : int
        Lookback period for momentum
    threshold_pct : float
        Threshold for trend (e.g., 0.02 = 2% price change)

    Returns
    -------
    TrendRegimeResult
        Trend regimes based on momentum
    """
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValidationError("prices must have DatetimeIndex")
    
    # Calculate momentum (% change over window)
    momentum = prices.pct_change(momentum_window)
    
    indicators = pd.DataFrame({
        'price': prices,
        'momentum': momentum,
    }).dropna()
    
    # Classify regimes
    regimes = np.full(len(indicators), 2, dtype=int)  # Default: sideways
    regimes[indicators['momentum'] > threshold_pct] = 0  # Uptrend
    regimes[indicators['momentum'] < -threshold_pct] = 1  # Downtrend
    
    regime_names = ['uptrend', 'downtrend', 'sideways']
    
    return TrendRegimeResult(
        regimes=regimes,
        regime_names=regime_names,
        indicators=indicators,
        timestamps=indicators.index,
    )
