"""
Correlation analysis and regime detection.

Analyzes:
  - Rolling correlations across asset classes
  - Correlation regime shifts (calm → stress → crisis)
  - Eigenvalue spectrum and diversification collapse
  - Correlation contagion and breakdown
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy.linalg import eigh

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


@dataclass
class CorrelationMetrics:
    """Correlation matrix metrics."""
    timestamp: float
    avg_correlation: float
    max_correlation: float
    min_correlation: float
    eigenvalues: np.ndarray
    diversification_ratio: float  # Largest eigenvalue / sum
    regime: str  # 'calm', 'stress', 'crisis'


def rolling_correlation(
    returns: pd.DataFrame,
    window: int = 30,
) -> list[pd.DataFrame]:
    """
    Compute rolling correlation matrices.
    
    Parameters
    ----------
    returns : pd.DataFrame
        Asset returns (rows=time, columns=assets)
    window : int
        Rolling window size
    
    Returns
    -------
    list[pd.DataFrame]
        Rolling correlation matrices
    """
    require_positive(window, "window")
    
    if len(returns) < window:
        raise ValidationError(f"Returns length {len(returns)} < window {window}")
    
    corr_matrices = []
    
    for i in range(window, len(returns) + 1):
        window_returns = returns.iloc[i - window:i]
        corr = window_returns.corr()
        corr_matrices.append(corr)
    
    return corr_matrices


def correlation_regime(avg_corr: float) -> str:
    """
    Classify correlation regime.
    
    Parameters
    ----------
    avg_corr : float
        Average pairwise correlation
    
    Returns
    -------
    str
        'calm', 'stress', or 'crisis'
    """
    if avg_corr < 0.3:
        return 'calm'
    elif avg_corr < 0.6:
        return 'stress'
    else:
        return 'crisis'


def compute_correlation_metrics(
    corr_matrix: pd.DataFrame,
    timestamp: float = 0.0,
) -> CorrelationMetrics:
    """
    Compute metrics from correlation matrix.
    
    Parameters
    ----------
    corr_matrix : pd.DataFrame
        Correlation matrix (n x n)
    timestamp : float
        Timestamp for metrics
    
    Returns
    -------
    CorrelationMetrics
        Correlation metrics
    """
    n = len(corr_matrix)
    
    # Extract off-diagonal correlations
    mask = ~np.eye(n, dtype=bool)
    off_diag = corr_matrix.values[mask]
    
    avg_corr = float(np.mean(off_diag))
    max_corr = float(np.max(off_diag))
    min_corr = float(np.min(off_diag))
    
    # Eigenvalue analysis
    eigvals, _ = eigh(corr_matrix.values)
    eigvals = np.sort(eigvals)[::-1]  # Descending order
    
    # Diversification ratio
    div_ratio = eigvals[0] / np.sum(eigvals)
    
    regime = correlation_regime(avg_corr)
    
    return CorrelationMetrics(
        timestamp=timestamp,
        avg_correlation=avg_corr,
        max_correlation=max_corr,
        min_correlation=min_corr,
        eigenvalues=eigvals,
        diversification_ratio=float(div_ratio),
        regime=regime,
    )


def detect_correlation_breakdowns(
    corr_history: list[pd.DataFrame],
    threshold: float = 0.3,
) -> list[int]:
    """
    Detect correlation breakdown events.
    
    Breakdown = sudden jump in average correlation.
    
    Parameters
    ----------
    corr_history : list[pd.DataFrame]
        Historical correlation matrices
    threshold : float
        Minimum correlation increase to trigger breakdown
    
    Returns
    -------
    list[int]
        Indices of breakdown events
    """
    if len(corr_history) < 2:
        return []
    
    avg_corrs = []
    for corr in corr_history:
        n = len(corr)
        mask = ~np.eye(n, dtype=bool)
        avg_corrs.append(np.mean(corr.values[mask]))
    
    breakdowns = []
    
    for i in range(1, len(avg_corrs)):
        delta = avg_corrs[i] - avg_corrs[i - 1]
        if delta > threshold:
            breakdowns.append(i)
    
    return breakdowns


def correlation_contagion_score(
    corr_matrix: pd.DataFrame,
    baseline_corr: float = 0.3,
) -> float:
    """
    Measure correlation contagion.
    
    Contagion score = (avg_corr - baseline) / (1 - baseline)
    
    Parameters
    ----------
    corr_matrix : pd.DataFrame
        Current correlation matrix
    baseline_corr : float
        Baseline correlation level
    
    Returns
    -------
    float
        Contagion score [0, 1]
    """
    n = len(corr_matrix)
    mask = ~np.eye(n, dtype=bool)
    avg_corr = np.mean(corr_matrix.values[mask])
    
    if baseline_corr >= 1.0:
        return 0.0
    
    score = (avg_corr - baseline_corr) / (1.0 - baseline_corr)
    return max(0.0, min(1.0, score))


def eigenvalue_concentration(eigvals: np.ndarray, top_k: int = 3) -> float:
    """
    Measure eigenvalue concentration.
    
    Concentration = sum(top_k eigenvalues) / sum(all eigenvalues)
    
    High concentration → low diversification.
    
    Parameters
    ----------
    eigvals : np.ndarray
        Eigenvalues (sorted descending)
    top_k : int
        Number of top eigenvalues to consider
    
    Returns
    -------
    float
        Concentration ratio [0, 1]
    """
    if len(eigvals) == 0:
        return 0.0
    
    top_k = min(top_k, len(eigvals))
    return np.sum(eigvals[:top_k]) / np.sum(eigvals)


def make_psd(matrix: np.ndarray, tol: float = 1e-8) -> np.ndarray:
    """
    Make matrix positive semi-definite.
    
    Parameters
    ----------
    matrix : np.ndarray
        Symmetric matrix
    tol : float
        Minimum eigenvalue tolerance
    
    Returns
    -------
    np.ndarray
        PSD matrix
    """
    # Symmetrize
    sym = (matrix + matrix.T) / 2.0
    
    # Eigenvalue decomposition
    eigvals, eigvecs = eigh(sym)
    
    # Clip negative eigenvalues
    eigvals[eigvals < tol] = tol
    
    # Reconstruct
    psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
    
    # Re-symmetrize
    return (psd + psd.T) / 2.0


def simulate_correlation_shock(
    base_corr: float,
    shock_intensity: float,
    n_assets: int,
) -> np.ndarray:
    """
    Simulate a correlation shock.
    
    Nonlinear transformation pushes correlations toward 1.
    
    Parameters
    ----------
    base_corr : float
        Base correlation level
    shock_intensity : float
        Shock intensity [0, 1]
    n_assets : int
        Number of assets
    
    Returns
    -------
    np.ndarray
        Shocked correlation matrix
    """
    require_positive(n_assets, "n_assets")
    
    if not 0 <= shock_intensity <= 1:
        raise ValidationError("shock_intensity must be in [0, 1]")
    
    # Base correlation matrix
    corr = np.full((n_assets, n_assets), base_corr)
    np.fill_diagonal(corr, 1.0)
    
    # Nonlinear shock: corr → corr + (1 - corr) * (1 - exp(-k * shock))
    k = 3.0
    shocked_corr = corr + (1.0 - corr) * (1.0 - np.exp(-k * shock_intensity))
    
    # Ensure PSD
    shocked_corr = make_psd(shocked_corr)
    
    # Re-normalize diagonal
    np.fill_diagonal(shocked_corr, 1.0)
    
    return shocked_corr


def cross_asset_correlation(
    returns: pd.DataFrame,
    asset1: str,
    asset2: str,
    window: int = 30,
) -> pd.Series:
    """
    Compute rolling correlation between two assets.
    
    Parameters
    ----------
    returns : pd.DataFrame
        Asset returns
    asset1 : str
        First asset
    asset2 : str
        Second asset
    window : int
        Rolling window
    
    Returns
    -------
    pd.Series
        Rolling correlation time series
    """
    if asset1 not in returns.columns:
        raise ValidationError(f"Asset {asset1} not in returns")
    if asset2 not in returns.columns:
        raise ValidationError(f"Asset {asset2} not in returns")
    
    return returns[asset1].rolling(window).corr(returns[asset2])


def correlation_heatmap_data(
    corr_matrix: pd.DataFrame,
) -> dict:
    """
    Prepare correlation matrix for heatmap visualization.
    
    Parameters
    ----------
    corr_matrix : pd.DataFrame
        Correlation matrix
    
    Returns
    -------
    dict
        Heatmap data with z, x, y, labels
    """
    return {
        'z': corr_matrix.values.tolist(),
        'x': corr_matrix.columns.tolist(),
        'y': corr_matrix.index.tolist(),
        'labels': corr_matrix.columns.tolist(),
    }
