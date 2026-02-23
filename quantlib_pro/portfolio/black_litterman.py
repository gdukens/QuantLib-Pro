"""
Black-Litterman model for portfolio optimization.

Combines market equilibrium returns (from CAPM) with investor views
to produce a refined expected return vector.

Reference:
  Black, F., & Litterman, R. (1992). Global Portfolio Optimization.
  Financial Analysts Journal, 48(5), 28-43.

The model starts with a market-implied return vector (π) derived from
reverse optimization:

  π = δ * Σ * w_mkt

where:
  - δ = risk aversion coefficient
  - Σ = covariance matrix
  - w_mkt = market-cap weights

Investor views are expressed as:

  P * μ = Q + ε,  ε ~ N(0, Ω)

where:
  - P = pick matrix (which assets the views reference)
  - Q = vector of view returns
  - Ω = uncertainty in views

The posterior (blended) expected return is:

  E[R] = [(τΣ)^-1 + P'Ω^-1 P]^-1 * [(τΣ)^-1 π + P'Ω^-1 Q]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


@dataclass
class MarketView:
    """A single investor view on expected returns."""
    assets: list[int]  # Indices of assets involved
    weights: list[float]  # Weights for each asset (e.g., [1.0, -1.0] for relative view)
    expected_return: float  # Expected return for this view
    confidence: float = 0.5  # Confidence level (0-1), lower = more uncertain


def _implied_returns(
    cov_matrix: np.ndarray,
    market_weights: np.ndarray,
    risk_aversion: float = 2.5,
) -> np.ndarray:
    """
    Compute market-implied equilibrium returns using reverse optimization.

    π = δ * Σ * w_mkt

    Parameters
    ----------
    cov_matrix : np.ndarray
        Covariance matrix of asset returns
    market_weights : np.ndarray
        Market-capitalization weights
    risk_aversion : float
        Risk aversion coefficient (typically 2.5)

    Returns
    -------
    np.ndarray
        Implied equilibrium returns
    """
    return risk_aversion * np.dot(cov_matrix, market_weights)


def black_litterman(
    cov_matrix: pd.DataFrame | np.ndarray,
    market_weights: pd.Series | np.ndarray,
    views: list[MarketView],
    risk_aversion: float = 2.5,
    tau: float = 0.05,
    tickers: Optional[list[str]] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute Black-Litterman posterior expected returns.

    Parameters
    ----------
    cov_matrix : array-like
        Covariance matrix of asset returns
    market_weights : array-like
        Market-capitalization weights (must sum to 1)
    views : list[MarketView]
        List of investor views
    risk_aversion : float
        Risk aversion coefficient (typical: 2.5)
    tau : float
        Uncertainty scalar for prior (typical: 0.025 to 0.05)
    tickers : list[str], optional
        Asset names

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (posterior_returns, posterior_cov)
    """
    if isinstance(cov_matrix, pd.DataFrame):
        cov = cov_matrix.values
        if tickers is None:
            tickers = cov_matrix.index.tolist()
    else:
        cov = np.array(cov_matrix)
    
    if isinstance(market_weights, pd.Series):
        w_mkt = market_weights.values
    else:
        w_mkt = np.array(market_weights)
    
    n_assets = cov.shape[0]
    require_positive(n_assets, "n_assets")
    
    if len(w_mkt) != n_assets:
        raise ValidationError(
            f"Market weights length ({len(w_mkt)}) must match "
            f"covariance matrix size ({n_assets})"
        )
    
    if not np.isclose(w_mkt.sum(), 1.0):
        raise ValidationError(f"Market weights must sum to 1, got {w_mkt.sum()}")
    
    # Step 1: Compute implied equilibrium returns
    pi = _implied_returns(cov, w_mkt, risk_aversion)
    
    if not views:
        # No views: return equilibrium
        return pi, cov
    
    # Step 2: Construct P (pick matrix) and Q (view returns)
    n_views = len(views)
    P = np.zeros((n_views, n_assets))
    Q = np.zeros(n_views)
    
    for i, view in enumerate(views):
        for asset_idx, weight in zip(view.assets, view.weights):
            if asset_idx >= n_assets:
                raise ValidationError(f"View references asset {asset_idx}, but only {n_assets} assets exist")
            P[i, asset_idx] = weight
        Q[i] = view.expected_return
    
    # Step 3: Construct Ω (view uncertainty matrix)
    # Diagonal matrix: Ω_ii = (1/confidence_i - 1) * P_i Σ P_i'
    Omega = np.zeros((n_views, n_views))
    for i, view in enumerate(views):
        P_i = P[i, :].reshape(-1, 1)
        view_variance = np.dot(P_i.T, np.dot(cov, P_i))[0, 0]
        if view.confidence == 0:
            raise ValidationError(f"View {i} has zero confidence")
        # Higher confidence → lower uncertainty
        Omega[i, i] = tau * view_variance / view.confidence
    
    # Step 4: Compute posterior expected returns (Black-Litterman formula)
    # E[R] = [(τΣ)^-1 + P'Ω^-1 P]^-1 * [(τΣ)^-1 π + P'Ω^-1 Q]
    
    tau_cov = tau * cov
    tau_cov_inv = np.linalg.inv(tau_cov)
    omega_inv = np.linalg.inv(Omega)
    
    # Posterior precision
    posterior_precision = tau_cov_inv + np.dot(P.T, np.dot(omega_inv, P))
    posterior_cov_scaled = np.linalg.inv(posterior_precision)
    
    # Posterior mean
    prior_term = np.dot(tau_cov_inv, pi)
    view_term = np.dot(P.T, np.dot(omega_inv, Q))
    posterior_returns = np.dot(posterior_cov_scaled, prior_term + view_term)
    
    # Step 5: Compute posterior covariance
    posterior_cov = cov + posterior_cov_scaled
    
    return posterior_returns, posterior_cov


def create_absolute_view(asset_idx: int, expected_return: float, confidence: float = 0.5) -> MarketView:
    """
    Create an absolute view: "Asset i will return X%".

    Parameters
    ----------
    asset_idx : int
        Index of the asset
    expected_return : float
        Expected return (e.g., 0.10 for 10%)
    confidence : float
        Confidence level (0-1)

    Returns
    -------
    MarketView
    """
    return MarketView(
        assets=[asset_idx],
        weights=[1.0],
        expected_return=expected_return,
        confidence=confidence,
    )


def create_relative_view(
    asset_idx_1: int,
    asset_idx_2: int,
    outperformance: float,
    confidence: float = 0.5,
) -> MarketView:
    """
    Create a relative view: "Asset i will outperform asset j by X%".

    Parameters
    ----------
    asset_idx_1 : int
        Index of asset expected to outperform
    asset_idx_2 : int
        Index of benchmark asset
    outperformance : float
        Expected outperformance (e.g., 0.03 for 3%)
    confidence : float
        Confidence level (0-1)

    Returns
    -------
    MarketView
    """
    return MarketView(
        assets=[asset_idx_1, asset_idx_2],
        weights=[1.0, -1.0],
        expected_return=outperformance,
        confidence=confidence,
    )
