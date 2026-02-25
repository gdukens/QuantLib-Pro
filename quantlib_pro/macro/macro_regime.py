"""
Macro regime detection - identify macro-economic regimes from market data.

This module provides functionality to detect macro regimes using
correlation analysis, volatility patterns, and economic indicators.
"""

from __future__ import annotations

import logging
from enum import Enum

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class MacroRegime(Enum):
    """Macro-economic regime types."""
    RISK_ON = "Risk On"
    RISK_OFF = "Risk Off"
    ROTATION = "Sector Rotation"
    CRISIS = "Crisis"
    RECOVERY = "Recovery"
    NORMAL = "Normal"


def detect_macro_regime(
    correlation_matrix: pd.DataFrame,
    volatility_series: pd.Series,
    threshold_high_corr: float = 0.7,
    threshold_high_vol: float = 0.25
) -> MacroRegime:
    """
    Detect current macro regime based on correlations and volatility.
    
    Parameters
    ----------
    correlation_matrix : pd.DataFrame
        Asset correlation matrix
    volatility_series : pd.Series
        Historical volatility for assets
    threshold_high_corr : float
        Threshold for high correlation (default: 0.7)
    threshold_high_vol : float
        Threshold for high volatility (default: 0.25 or 25%)
    
    Returns
    -------
    MacroRegime
        Detected macro regime
    
    Notes
    -----
    Regime detection logic:
    - Crisis: High correlation (>0.7) + High volatility (>25%)
    - Risk Off: High correlation + Moderate volatility
    - Risk On: Low correlation + Low volatility
    - Rotation: Moderate correlation + Low volatility
    - Normal: Otherwise
    """
    # Calculate average correlation (excluding diagonal)
    mask = np.ones_like(correlation_matrix, dtype=bool)
    np.fill_diagonal(mask, False)
    avg_correlation = correlation_matrix.values[mask].mean()
    
    # Calculate average volatility
    avg_volatility = volatility_series.mean()
    
    # Classify regime
    if avg_correlation > threshold_high_corr:
        if avg_volatility > threshold_high_vol:
            return MacroRegime.CRISIS
        else:
            return MacroRegime.RISK_OFF
    elif avg_volatility < threshold_high_vol * 0.5:
        if avg_correlation < 0.3:
            return MacroRegime.RISK_ON
        else:
            return MacroRegime.ROTATION
    else:
        return MacroRegime.NORMAL


def calculate_regime_scores(
    correlation_matrix: pd.DataFrame,
    volatility_series: pd.Series
) -> dict[str, float]:
    """
    Calculate scores for each macro regime.
    
    Parameters
    ----------
    correlation_matrix : pd.DataFrame
        Asset correlation matrix
    volatility_series : pd.Series
        Historical volatility for assets
    
    Returns
    -------
    dict[str, float]
        Regime scores (0-100 scale)
    """
    # Calculate key metrics
    mask = np.ones_like(correlation_matrix, dtype=bool)
    np.fill_diagonal(mask, False)
    avg_correlation = correlation_matrix.values[mask].mean()
    avg_volatility = volatility_series.mean()
    
    # Score each regime (0-100)
    scores = {}
    
    # Crisis score: high when both correlation and volatility are high
    scores['Crisis'] = min(100, (avg_correlation + avg_volatility) * 100)
    
    # Risk Off score: high correlation, moderate vol
    scores['Risk Off'] = min(100, avg_correlation * 150 * (1 - avg_volatility))
    
    # Risk On score: low correlation, low vol
    scores['Risk On'] = min(100, (1 - avg_correlation) * (1 - avg_volatility) * 100)
    
    # Rotation score: moderate correlation, low vol
    rotation_score = 50 * (1 - abs(avg_correlation - 0.5)) * (1 - avg_volatility)
    scores['Rotation'] = min(100, rotation_score)
    
    # Normal score: balanced
    scores['Normal'] = min(100, (1 - abs(avg_correlation - 0.4)) * 100)
    
    return scores


def get_regime_description(regime: MacroRegime) -> str:
    """Get a human-readable description of a macro regime."""
    descriptions = {
        MacroRegime.CRISIS: (
            "Crisis Mode: Markets showing high correlation and volatility. "
            "Assets moving together in a risk-off environment. "
            "Consider defensive positioning and capital preservation."
        ),
        MacroRegime.RISK_OFF: (
            "Risk Off: High correlation among assets indicates defensive behavior. "
            "Flight to quality and safe haven assets. "
            "Reduce equity exposure, increase bonds/cash."
        ),
        MacroRegime.RISK_ON: (
            "Risk On: Low correlation and volatility suggest healthy markets. "
            "Risk assets performing well with stock-specific dynamics. "
            "Favorable environment for active strategies."
        ),
        MacroRegime.ROTATION: (
            "Sector Rotation: Moderate correlations with sector-specific dynamics. "
            "Capital rotating between sectors and styles. "
            "Opportunities in sector-focused strategies."
        ),
        MacroRegime.RECOVERY: (
            "Recovery: Market transitioning from stress to normalization. "
            "Decreasing correlations and volatility. "
            "Early-stage risk-on behavior emerging."
        ),
        MacroRegime.NORMAL: (
            "Normal Market: Balanced correlation and volatility patterns. "
            "No extreme regime characteristics. "
            "Standard portfolio construction appropriate."
        ),
    }
    return descriptions.get(regime, "Unknown regime")
