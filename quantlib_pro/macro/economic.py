"""
Economic indicator analysis and macro regime detection.

Tracks:
  - Growth indicators (GDP, PMI, employment)
  - Inflation indicators (CPI, PPI, wages)
  - Monetary policy (rates, money supply)
  - Leading/coincident/lagging indicators
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


class MacroRegime(Enum):
    """Macro economic regime."""
    EXPANSION = "expansion"
    SLOWDOWN = "slowdown"
    RECESSION = "recession"
    RECOVERY = "recovery"


@dataclass
class EconomicIndicator:
    """Single economic indicator."""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    category: str = "general"  # 'growth', 'inflation', 'monetary', 'employment'
    
    def z_score(self, mean: float, std: float) -> float:
        """Compute z-score."""
        if std == 0:
            return 0.0
        return (self.value - mean) / std


@dataclass
class MacroSnapshot:
    """Snapshot of macro indicators."""
    timestamp: float
    gdp_growth: Optional[float] = None
    unemployment: Optional[float] = None
    inflation: Optional[float] = None
    interest_rate: Optional[float] = None
    pmi: Optional[float] = None
    confidence: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'gdp_growth': self.gdp_growth,
            'unemployment': self.unemployment,
            'inflation': self.inflation,
            'interest_rate': self.interest_rate,
            'pmi': self.pmi,
            'confidence': self.confidence,
        }


def detect_macro_regime(
    gdp_growth: float,
    unemployment_change: float,
    pmi: Optional[float] = None,
) -> MacroRegime:
    """
    Detect current macro regime.
    
    Rules:
      - Expansion: GDP > 2%, unemployment falling, PMI > 50
      - Recession: GDP < 0%, unemployment rising
      - Slowdown: GDP slowing, unemployment stable/rising
      - Recovery: GDP turning positive, unemployment stabilizing
    
    Parameters
    ----------
    gdp_growth : float
        GDP growth rate (annualized %)
    unemployment_change : float
        Change in unemployment rate
    pmi : float, optional
        PMI index (50 = neutral)
    
    Returns
    -------
    MacroRegime
        Detected regime
    """
    # Expansion: strong growth, falling unemployment
    if gdp_growth > 2.0 and unemployment_change < 0:
        if pmi is None or pmi > 50:
            return MacroRegime.EXPANSION
    
    # Recession: negative growth
    if gdp_growth < 0:
        return MacroRegime.RECESSION
    
    # Slowdown: weak growth, rising unemployment
    if gdp_growth < 2.0 and unemployment_change > 0:
        return MacroRegime.SLOWDOWN
    
    # Recovery: positive growth from low levels
    if 0 < gdp_growth < 2.0 and unemployment_change <= 0:
        return MacroRegime.RECOVERY
    
    # Default to slowdown
    return MacroRegime.SLOWDOWN


def growth_momentum(
    gdp_series: pd.Series,
    window: int = 4,
) -> pd.Series:
    """
    Compute growth momentum.
    
    Momentum = change in growth rate over window.
    
    Parameters
    ----------
    gdp_series : pd.Series
        GDP growth rates
    window : int
        Lookback window
    
    Returns
    -------
    pd.Series
        Growth momentum
    """
    require_positive(window, "window")
    return gdp_series.diff(window)


def inflation_gap(
    actual_inflation: float,
    target_inflation: float = 2.0,
) -> float:
    """
    Compute inflation gap from target.
    
    Parameters
    ----------
    actual_inflation : float
        Actual inflation rate (%)
    target_inflation : float
        Target inflation rate (%)
    
    Returns
    -------
    float
        Inflation gap (positive = above target)
    """
    return actual_inflation - target_inflation


def real_interest_rate(
    nominal_rate: float,
    inflation: float,
) -> float:
    """
    Compute real interest rate.
    
    Real rate ≈ nominal - inflation (Fisher approximation)
    
    Parameters
    ----------
    nominal_rate : float
        Nominal interest rate (%)
    inflation : float
        Inflation rate (%)
    
    Returns
    -------
    float
        Real interest rate (%)
    """
    return nominal_rate - inflation


def yield_curve_slope(
    long_rate: float,
    short_rate: float,
) -> float:
    """
    Compute yield curve slope.
    
    Slope = long_rate - short_rate
    
    Inverted curve (negative slope) often precedes recession.
    
    Parameters
    ----------
    long_rate : float
        Long-term rate (e.g., 10Y)
    short_rate : float
        Short-term rate (e.g., 2Y)
    
    Returns
    -------
    float
        Yield curve slope (bp)
    """
    return long_rate - short_rate


def sahm_rule_indicator(
    unemployment_series: pd.Series,
    window: int = 3,
    threshold: float = 0.5,
) -> bool:
    """
    Sahm Rule recession indicator.
    
    Recession signal when 3-month average unemployment rises
    0.5pp above its 12-month low.
    
    Parameters
    ----------
    unemployment_series : pd.Series
        Unemployment rate time series
    window : int
        Averaging window (months)
    threshold : float
        Threshold for signal (pp)
    
    Returns
    -------
    bool
        True if recession signal triggered
    """
    if len(unemployment_series) < window + 12:
        return False
    
    # 3-month average
    avg = unemployment_series.rolling(window).mean()
    
    # 12-month low
    low_12m = unemployment_series.rolling(12).min()
    
    # Gap
    gap = avg - low_12m
    
    return bool(gap.iloc[-1] > threshold)


def leading_economic_index(
    indicators: dict[str, float],
    weights: Optional[dict[str, float]] = None,
) -> float:
    """
    Compute composite leading economic index.
    
    Parameters
    ----------
    indicators : dict[str, float]
        Indicator name → z-score mapping
    weights : dict[str, float], optional
        Indicator weights (default: equal weight)
    
    Returns
    -------
    float
        Composite LEI score
    """
    if not indicators:
        return 0.0
    
    if weights is None:
        weights = {k: 1.0 / len(indicators) for k in indicators}
    
    lei = sum(indicators[k] * weights.get(k, 0.0) for k in indicators)
    return lei


def diffusion_index(
    indicators: pd.DataFrame,
    threshold: float = 0.0,
) -> pd.Series:
    """
    Compute diffusion index.
    
    Diffusion = % of indicators above threshold.
    
    Parameters
    ----------
    indicators : pd.DataFrame
        Indicator time series (rows=time, columns=indicators)
    threshold : float
        Threshold for "improving"
    
    Returns
    -------
    pd.Series
        Diffusion index [0, 100]
    """
    above_threshold = (indicators > threshold).astype(float)
    diffusion = above_threshold.mean(axis=1) * 100
    return diffusion


def taylor_rule_rate(
    neutral_rate: float,
    inflation: float,
    target_inflation: float,
    output_gap: float,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> float:
    """
    Compute Taylor Rule policy rate.
    
    i = r* + π + α(π - π*) + β(y - y*)
    
    Where:
      r* = neutral real rate
      π = inflation
      π* = target inflation
      y - y* = output gap
    
    Parameters
    ----------
    neutral_rate : float
        Neutral real interest rate (%)
    inflation : float
        Current inflation (%)
    target_inflation : float
        Target inflation (%)
    output_gap : float
        Output gap (% deviation from potential)
    alpha : float
        Inflation gap weight
    beta : float
        Output gap weight
    
    Returns
    -------
    float
        Recommended policy rate (%)
    """
    inflation_gap = inflation - target_inflation
    
    rate = neutral_rate + inflation + alpha * inflation_gap + beta * output_gap
    
    return max(0.0, rate)  # ZLB constraint


def recession_probability(
    yield_spread: float,
    unemployment_change: float,
    pmi: float,
) -> float:
    """
    Estimate recession probability (simple heuristic).
    
    Combines:
      - Inverted yield curve
      - Rising unemployment
      - Weak manufacturing (PMI < 50)
    
    Parameters
    ----------
    yield_spread : float
        10Y - 2Y spread (bp)
    unemployment_change : float
        3-month change in unemployment (pp)
    pmi : float
        Manufacturing PMI
    
    Returns
    -------
    float
        Recession probability [0, 1]
    """
    prob = 0.0
    
    # Inverted curve
    if yield_spread < 0:
        prob += 0.4
    elif yield_spread < 50:
        prob += 0.2
    
    # Rising unemployment
    if unemployment_change > 0.5:
        prob += 0.3
    elif unemployment_change > 0.2:
        prob += 0.15
    
    # Weak PMI
    if pmi < 45:
        prob += 0.3
    elif pmi < 50:
        prob += 0.15
    
    return min(1.0, prob)


def normalize_indicator(
    series: pd.Series,
    method: str = 'zscore',
) -> pd.Series:
    """
    Normalize economic indicator.
    
    Parameters
    ----------
    series : pd.Series
        Indicator time series
    method : str
        'zscore', 'minmax', or 'pctile'
    
    Returns
    -------
    pd.Series
        Normalized series
    """
    if method == 'zscore':
        return (series - series.mean()) / series.std()
    elif method == 'minmax':
        return (series - series.min()) / (series.max() - series.min())
    elif method == 'pctile':
        return series.rank(pct=True)
    else:
        raise ValidationError(f"Unknown normalization method: {method}")
