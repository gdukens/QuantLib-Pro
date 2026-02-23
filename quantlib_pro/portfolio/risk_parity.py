"""
Risk Parity portfolio allocation.

Allocates capital such that each asset contributes equally to the
total portfolio risk (as measured by volatility).

For a portfolio with weights w and covariance matrix Σ:

  Risk contribution of asset i:  RC_i = w_i * (Σw)_i
  Total risk:                    σ_p = √(w'Σw)
  Contribution to variance:      σ_i = w_i * (Σw)_i / σ_p

Risk parity sets:  σ_i = σ_p / N  for all i
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from quantlib_pro.portfolio.optimization import PortfolioResult
from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


def _risk_contribution(weights: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate each asset's contribution to portfolio variance.

    Returns
    -------
    np.ndarray
        Vector of marginal risk contributions (w_i * (Σw)_i)
    """
    portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    if portfolio_variance == 0:
        return np.zeros_like(weights)
    marginal_contrib = np.dot(cov_matrix, weights)
    risk_contrib = weights * marginal_contrib
    return risk_contrib


def _risk_parity_objective(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """
    Objective function for risk parity: sum of squared deviations
    from equal risk contribution.

    We want:  RC_i / RC_j = 1  for all i, j
    Equivalently, minimize: Σ_i Σ_j (RC_i - RC_j)²
    """
    risk_contrib = _risk_contribution(weights, cov_matrix)
    avg_risk = risk_contrib.mean()
    # Sum of squared deviations from average
    return np.sum((risk_contrib - avg_risk) ** 2)


def risk_parity_portfolio(
    cov_matrix: pd.DataFrame | np.ndarray,
    expected_returns: Optional[pd.Series | np.ndarray] = None,
    tickers: Optional[list[str]] = None,
) -> PortfolioResult:
    """
    Compute risk parity portfolio weights.

    Parameters
    ----------
    cov_matrix : array-like
        Covariance matrix of asset returns
    expected_returns : array-like, optional
        Expected returns (for reporting only, not used in optimization)
    tickers : list[str], optional
        Asset names

    Returns
    -------
    PortfolioResult
        Risk parity weights and metrics
    """
    if isinstance(cov_matrix, pd.DataFrame):
        cov = cov_matrix.values
        if tickers is None:
            tickers = cov_matrix.index.tolist()
    else:
        cov = np.array(cov_matrix)
    
    n_assets = cov.shape[0]
    require_positive(n_assets, "n_assets")
    
    if tickers is None:
        tickers = [f"Asset{i+1}" for i in range(n_assets)]
    
    # Initial guess: equal weights
    x0 = np.ones(n_assets) / n_assets
    
    # Constraints: weights sum to 1, all weights > 0
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    bounds = [(0.001, 1.0)] * n_assets  # small lower bound to avoid division by zero
    
    result = minimize(
        _risk_parity_objective,
        x0,
        args=(cov,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000},
    )
    
    if not result.success:
        raise ValidationError(f"Risk parity optimization failed: {result.message}")
    
    weights = result.x
    weights /= weights.sum()  # Normalize to ensure exact sum = 1
    
    # Calculate portfolio metrics
    portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    
    if expected_returns is not None:
        if isinstance(expected_returns, pd.Series):
            exp_ret = expected_returns.values
        else:
            exp_ret = np.array(expected_returns)
        portfolio_return = np.dot(weights, exp_ret)
        sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0.0
    else:
        portfolio_return = 0.0
        sharpe = 0.0
    
    return PortfolioResult(
        weights=weights,
        expected_return=portfolio_return,
        volatility=portfolio_vol,
        sharpe_ratio=sharpe,
        tickers=tickers,
        method="Risk Parity",
    )


def risk_budgeting_portfolio(
    cov_matrix: pd.DataFrame | np.ndarray,
    risk_budgets: np.ndarray,
    expected_returns: Optional[pd.Series | np.ndarray] = None,
    tickers: Optional[list[str]] = None,
) -> PortfolioResult:
    """
    Compute risk budgeting portfolio with custom risk allocations.

    Parameters
    ----------
    risk_budgets : np.ndarray
        Desired risk contribution for each asset (must sum to 1)
    
    Examples
    --------
    >>> # Allocate 60% risk to equities, 40% to bonds
    >>> cov = np.array([[0.04, 0.01], [0.01, 0.01]])
    >>> budgets = np.array([0.6, 0.4])
    >>> portfolio = risk_budgeting_portfolio(cov, budgets)
    """
    if isinstance(cov_matrix, pd.DataFrame):
        cov = cov_matrix.values
        if tickers is None:
            tickers = cov_matrix.index.tolist()
    else:
        cov = np.array(cov_matrix)
    
    n_assets = cov.shape[0]
    
    if len(risk_budgets) != n_assets:
        raise ValidationError(
            f"Risk budgets length ({len(risk_budgets)}) must match "
            f"number of assets ({n_assets})"
        )
    
    if not np.isclose(risk_budgets.sum(), 1.0):
        raise ValidationError(f"Risk budgets must sum to 1, got {risk_budgets.sum()}")
    
    if tickers is None:
        tickers = [f"Asset{i+1}" for i in range(n_assets)]
    
    x0 = risk_budgets  # Use budgets as initial guess
    
    def objective(weights):
        rc = _risk_contribution(weights, cov)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
        if portfolio_vol == 0:
            return 1e10
        # Normalize risk contributions to sum to 1
        rc_pct = rc / portfolio_vol**2
        # Minimize squared difference from target budgets
        return np.sum((rc_pct - risk_budgets) ** 2)
    
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    bounds = [(0.001, 1.0)] * n_assets
    
    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000},
    )
    
    if not result.success:
        raise ValidationError(f"Risk budgeting optimization failed: {result.message}")
    
    weights = result.x
    weights /= weights.sum()
    
    portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    
    if expected_returns is not None:
        if isinstance(expected_returns, pd.Series):
            exp_ret = expected_returns.values
        else:
            exp_ret = np.array(expected_returns)
        portfolio_return = np.dot(weights, exp_ret)
        sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0.0
    else:
        portfolio_return = 0.0
        sharpe = 0.0
    
    return PortfolioResult(
        weights=weights,
        expected_return=portfolio_return,
        volatility=portfolio_vol,
        sharpe_ratio=sharpe,
        tickers=tickers,
        method="Risk Budgeting",
    )
