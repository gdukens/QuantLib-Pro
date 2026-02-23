"""
Market sentiment analysis.

Analyzes:
  - Fear/greed indicators (VIX, put/call ratios)
  - Sentiment surveys (AAII, consumer confidence)
  - Technical sentiment (advance/decline, new highs/lows)
  - Positioning and flows
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


class SentimentRegime(Enum):
    """Market sentiment regime."""
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"


@dataclass
class SentimentSnapshot:
    """Snapshot of sentiment indicators."""
    timestamp: float
    vix: Optional[float] = None
    put_call_ratio: Optional[float] = None
    aaii_bull_pct: Optional[float] = None
    aaii_bear_pct: Optional[float] = None
    advance_decline: Optional[float] = None
    new_high_low: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'vix': self.vix,
            'put_call_ratio': self.put_call_ratio,
            'aaii_bull_pct': self.aaii_bull_pct,
            'aaii_bear_pct': self.aaii_bear_pct,
            'advance_decline': self.advance_decline,
            'new_high_low': self.new_high_low,
        }


def vix_sentiment_level(vix: float) -> SentimentRegime:
    """
    Classify sentiment based on VIX level.
    
    Parameters
    ----------
    vix : float
        VIX index level
    
    Returns
    -------
    SentimentRegime
        Sentiment classification
    """
    if vix < 12:
        return SentimentRegime.EXTREME_GREED
    elif vix < 16:
        return SentimentRegime.GREED
    elif vix < 20:
        return SentimentRegime.NEUTRAL
    elif vix < 30:
        return SentimentRegime.FEAR
    else:
        return SentimentRegime.EXTREME_FEAR


def put_call_ratio_sentiment(ratio: float) -> SentimentRegime:
    """
    Classify sentiment based on put/call ratio.
    
    High ratio = more puts = fearful
    Low ratio = more calls = greedy
    
    Parameters
    ----------
    ratio : float
        Put/call ratio
    
    Returns
    -------
    SentimentRegime
        Sentiment classification
    """
    if ratio < 0.6:
        return SentimentRegime.EXTREME_GREED
    elif ratio < 0.8:
        return SentimentRegime.GREED
    elif ratio < 1.0:
        return SentimentRegime.NEUTRAL
    elif ratio < 1.2:
        return SentimentRegime.FEAR
    else:
        return SentimentRegime.EXTREME_FEAR


def aaii_sentiment_score(
    bull_pct: float,
    bear_pct: float,
) -> float:
    """
    Compute AAII sentiment score.
    
    Score = (bull% - bear%) / 100
    
    Parameters
    ----------
    bull_pct : float
        % bulls (0-100)
    bear_pct : float
        % bears (0-100)
    
    Returns
    -------
    float
        Bull-bear spread [-1, 1]
    """
    return (bull_pct - bear_pct) / 100.0


def fear_greed_index(
    vix: float,
    put_call_ratio: float,
    advance_decline: float,
    new_high_low: float,
    vix_weight: float = 0.3,
    pc_weight: float = 0.3,
    ad_weight: float = 0.2,
    nhl_weight: float = 0.2,
) -> float:
    """
    Compute composite fear/greed index.
    
    Combines multiple sentiment indicators.
    Returns score [0, 100] where:
      0-25 = extreme fear
      25-45 = fear
      45-55 = neutral
      55-75 = greed
      75-100 = extreme greed
    
    Parameters
    ----------
    vix : float
        VIX level
    put_call_ratio : float
        Put/call ratio
    advance_decline : float
        Advance/decline ratio
    new_high_low : float
        New highs / new lows ratio
    vix_weight : float
        VIX weight
    pc_weight : float
        Put/call weight
    ad_weight : float
        Advance/decline weight
    nhl_weight : float
        New high/low weight
    
    Returns
    -------
    float
        Fear/greed index [0, 100]
    """
    # Normalize each indicator to [0, 100]
    
    # VIX: invert (high VIX = low score)
    vix_score = max(0, min(100, 100 * (1 - (vix - 10) / 50)))
    
    # Put/call: invert (high ratio = low score)
    pc_score = max(0, min(100, 100 * (1 - (put_call_ratio - 0.5) / 1.0)))
    
    # Advance/decline: normalize around 1.0
    ad_score = max(0, min(100, 50 + 50 * (advance_decline - 1.0)))
    
    # New high/low: normalize
    nhl_score = max(0, min(100, 50 + 20 * np.log(new_high_low + 1e-6)))
    
    # Weighted average
    index = (
        vix_weight * vix_score +
        pc_weight * pc_score +
        ad_weight * ad_score +
        nhl_weight * nhl_score
    )
    
    return max(0.0, min(100.0, index))


def contrarian_signal(
    sentiment_score: float,
    extreme_threshold: float = 0.8,
) -> str:
    """
    Generate contrarian signal from sentiment.
    
    Extreme sentiment often precedes reversals.
    
    Parameters
    ----------
    sentiment_score : float
        Normalized sentiment [0, 1]
    extreme_threshold : float
        Threshold for extreme
    
    Returns
    -------
    str
        'buy', 'sell', or 'neutral'
    """
    if sentiment_score > extreme_threshold:
        # Extreme greed → contrarian sell
        return 'sell'
    elif sentiment_score < (1 - extreme_threshold):
        # Extreme fear → contrarian buy
        return 'buy'
    else:
        return 'neutral'


def advance_decline_line(
    advances: pd.Series,
    declines: pd.Series,
) -> pd.Series:
    """
    Compute cumulative advance/decline line.
    
    Parameters
    ----------
    advances : pd.Series
        Number of advancing stocks
    declines : pd.Series
        Number of declining stocks
    
    Returns
    -------
    pd.Series
        Cumulative A/D line
    """
    net_advances = advances - declines
    return net_advances.cumsum()


def mcclellan_oscillator(
    advances: pd.Series,
    declines: pd.Series,
    fast: int = 19,
    slow: int = 39,
) -> pd.Series:
    """
    Compute McClellan Oscillator.
    
    Oscillator = EMA(net_advances, fast) - EMA(net_advances, slow)
    
    Parameters
    ----------
    advances : pd.Series
        Advancing stocks
    declines : pd.Series
        Declining stocks
    fast : int
        Fast EMA period
    slow : int
        Slow EMA period
    
    Returns
    -------
    pd.Series
        McClellan Oscillator
    """
    net_advances = advances - declines
    
    ema_fast = net_advances.ewm(span=fast, adjust=False).mean()
    ema_slow = net_advances.ewm(span=slow, adjust=False).mean()
    
    return ema_fast - ema_slow


def new_high_low_ratio(
    new_highs: pd.Series,
    new_lows: pd.Series,
    smooth: int = 10,
) -> pd.Series:
    """
    Compute new high/low ratio.
    
    Parameters
    ----------
    new_highs : pd.Series
        Number of 52-week highs
    new_lows : pd.Series
        Number of 52-week lows
    smooth : int
        Smoothing period
    
    Returns
    -------
    pd.Series
        High/low ratio (smoothed)
    """
    ratio = new_highs / (new_lows + 1e-6)  # Avoid division by zero
    return ratio.rolling(smooth).mean()


def skew_sentiment(skew: float) -> SentimentRegime:
    """
    Sentiment from option skew.
    
    High skew = investors buying downside protection = fear.
    
    Parameters
    ----------
    skew : float
        25-delta put/call skew (vol_put - vol_call)
    
    Returns
    -------
    SentimentRegime
        Sentiment
    """
    if skew < -5:
        return SentimentRegime.EXTREME_GREED
    elif skew < -2:
        return SentimentRegime.GREED
    elif skew < 2:
        return SentimentRegime.NEUTRAL
    elif skew < 5:
        return SentimentRegime.FEAR
    else:
        return SentimentRegime.EXTREME_FEAR


def vix_term_structure_slope(
    vix_spot: float,
    vix_3m: float,
) -> str:
    """
    Analyze VIX term structure.
    
    Contango (upward sloping) = normal, calm
    Backwardation (inverted) = stress, fear
    
    Parameters
    ----------
    vix_spot : float
        VIX spot level
    vix_3m : float
        3-month forward VIX
    
    Returns
    -------
    str
        'backwardation', 'flat', or 'contango'
    """
    slope = vix_3m - vix_spot
    
    if slope < -2:
        return 'backwardation'
    elif slope < 2:
        return 'flat'
    else:
        return 'contango'


def sentiment_divergence(
    price: pd.Series,
    sentiment: pd.Series,
    window: int = 20,
) -> pd.Series:
    """
    Detect divergence between price and sentiment.
    
    Bearish divergence: price rising, sentiment falling
    Bullish divergence: price falling, sentiment rising
    
    Parameters
    ----------
    price : pd.Series
        Price time series
    sentiment : pd.Series
        Sentiment index
    window : int
        Comparison window
    
    Returns
    -------
    pd.Series
        Divergence score (positive = bearish, negative = bullish)
    """
    price_change = price.pct_change(window)
    sentiment_change = sentiment.pct_change(window)
    
    # Divergence = price direction opposite sentiment direction
    divergence = price_change * -sentiment_change
    
    return divergence


def aggregate_sentiment_score(
    indicators: dict[str, float],
    weights: Optional[dict[str, float]] = None,
) -> float:
    """
    Aggregate multiple sentiment indicators.
    
    Parameters
    ----------
    indicators : dict[str, float]
        Indicator name → normalized score [0, 1]
    weights : dict[str, float], optional
        Indicator weights
    
    Returns
    -------
    float
        Composite sentiment [0, 1]
    """
    if not indicators:
        return 0.5  # Neutral
    
    if weights is None:
        weights = {k: 1.0 / len(indicators) for k in indicators}
    
    score = sum(indicators[k] * weights.get(k, 0.0) for k in indicators)
    return max(0.0, min(1.0, score))
