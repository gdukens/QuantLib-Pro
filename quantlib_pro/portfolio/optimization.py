"""
Mean-variance portfolio optimization (Markowitz, 1952).

Solves for optimal portfolio weights given expected returns and a
covariance matrix.  Includes:
  - Maximum Sharpe ratio portfolio
  - Minimum variance portfolio
  - Efficient frontier construction
  - Target return/volatility portfolios

Uses scipy.optimize for constrained optimization with bounds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


@dataclass
class PortfolioResult:
    """Results from a portfolio optimization."""
    weights: np.ndarray
    expected_return: float
    volatility: float
    sharpe_ratio: float
    tickers: list[str]
    method: str
    
    def to_dict(self) -> dict:
        """Return weights as {ticker: weight} dict."""
        return dict(zip(self.tickers, self.weights))
    
    def summary(self) -> str:
        return (
            f"{self.method} Portfolio:\n"
            f"  Expected Return: {self.expected_return:.2%}\n"
            f"  Volatility: {self.volatility:.2%}\n"
            f"  Sharpe Ratio: {self.sharpe_ratio:.4f}\n"
            f"  Weights: {self.to_dict()}"
        )


def _portfolio_return(weights: np.ndarray, expected_returns: np.ndarray) -> float:
    """Calculate portfolio expected return."""
    return np.dot(weights, expected_returns)


def _portfolio_volatility(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Calculate portfolio volatility (standard deviation)."""
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))


def _negative_sharpe(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
) -> float:
    """Negative Sharpe ratio (for minimization)."""
    ret = _portfolio_return(weights, expected_returns)
    vol = _portfolio_volatility(weights, cov_matrix)
    if vol == 0:
        return 1e10  # Penalize zero-volatility portfolios
    return -(ret - risk_free_rate) / vol


def max_sharpe_portfolio(
    expected_returns: pd.Series | np.ndarray,
    cov_matrix: pd.DataFrame | np.ndarray,
    risk_free_rate: float = 0.02,
    allow_short: bool = False,
) -> PortfolioResult:
    """
    Compute maximum Sharpe ratio portfolio.

    Parameters
    ----------
    expected_returns : array-like
        Expected annual returns for each asset
    cov_matrix : array-like
        Covariance matrix (annualized)
    risk_free_rate : float
        Annual risk-free rate (e.g., 0.02 for 2%)
    allow_short : bool
        If True, allow negative weights (short selling)

    Returns
    -------
    PortfolioResult
        Optimal weights and metrics
    """
    if isinstance(expected_returns, pd.Series):
        tickers = expected_returns.index.tolist()
        exp_ret = expected_returns.values
    else:
        exp_ret = np.array(expected_returns)
        tickers = [f"Asset{i+1}" for i in range(len(exp_ret))]
    
    if isinstance(cov_matrix, pd.DataFrame):
        cov = cov_matrix.values
    else:
        cov = np.array(cov_matrix)
    
    n_assets = len(exp_ret)
    require_positive(n_assets, "n_assets")
    
    # Initial guess: equal weights
    x0 = np.ones(n_assets) / n_assets
    
    # Constraints: weights sum to 1
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    
    # Bounds: [0, 1] for long-only, or [-1, 1] for short-allowed
    if allow_short:
        bounds = [(-1.0, 1.0)] * n_assets
    else:
        bounds = [(0.0, 1.0)] * n_assets
    
    result = minimize(
        _negative_sharpe,
        x0,
        args=(exp_ret, cov, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    
    if not result.success:
        raise ValidationError(f"Optimization failed: {result.message}")
    
    weights = result.x
    ret = _portfolio_return(weights, exp_ret)
    vol = _portfolio_volatility(weights, cov)
    sharpe = (ret - risk_free_rate) / vol if vol > 0 else 0.0
    
    return PortfolioResult(
        weights=weights,
        expected_return=ret,
        volatility=vol,
        sharpe_ratio=sharpe,
        tickers=tickers,
        method="Max Sharpe",
    )


def min_volatility_portfolio(
    expected_returns: pd.Series | np.ndarray,
    cov_matrix: pd.DataFrame | np.ndarray,
    allow_short: bool = False,
) -> PortfolioResult:
    """
    Compute minimum volatility portfolio.

    Parameters
    ----------
    expected_returns : array-like
        Expected returns (needed for PortfolioResult, not optimization)
    cov_matrix : array-like
        Covariance matrix
    allow_short : bool
        Allow short selling

    Returns
    -------
    PortfolioResult
        Minimum variance portfolio
    """
    if isinstance(expected_returns, pd.Series):
        tickers = expected_returns.index.tolist()
        exp_ret = expected_returns.values
    else:
        exp_ret = np.array(expected_returns)
        tickers = [f"Asset{i+1}" for i in range(len(exp_ret))]
    
    if isinstance(cov_matrix, pd.DataFrame):
        cov = cov_matrix.values
    else:
        cov = np.array(cov_matrix)
    
    n_assets = len(exp_ret)
    x0 = np.ones(n_assets) / n_assets
    
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    bounds = [(-1.0, 1.0)] * n_assets if allow_short else [(0.0, 1.0)] * n_assets
    
    result = minimize(
        lambda w: _portfolio_volatility(w, cov),
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    
    if not result.success:
        raise ValidationError(f"Optimization failed: {result.message}")
    
    weights = result.x
    ret = _portfolio_return(weights, exp_ret)
    vol = _portfolio_volatility(weights, cov)
    sharpe = ret / vol if vol > 0 else 0.0
    
    return PortfolioResult(
        weights=weights,
        expected_return=ret,
        volatility=vol,
        sharpe_ratio=sharpe,
        tickers=tickers,
        method="Min Volatility",
    )


def target_return_portfolio(
    expected_returns: pd.Series | np.ndarray,
    cov_matrix: pd.DataFrame | np.ndarray,
    target_return: float,
    allow_short: bool = False,
) -> PortfolioResult:
    """
    Find minimum volatility portfolio with a target expected return.

    Parameters
    ----------
    target_return : float
        Desired portfolio return (e.g., 0.10 for 10%)

    Returns
    -------
    PortfolioResult
        Portfolio achieving target return with minimum variance
    """
    if isinstance(expected_returns, pd.Series):
        tickers = expected_returns.index.tolist()
        exp_ret = expected_returns.values
    else:
        exp_ret = np.array(expected_returns)
        tickers = [f"Asset{i+1}" for i in range(len(exp_ret))]
    
    if isinstance(cov_matrix, pd.DataFrame):
        cov = cov_matrix.values
    else:
        cov = np.array(cov_matrix)
    
    n_assets = len(exp_ret)
    x0 = np.ones(n_assets) / n_assets
    
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "eq", "fun": lambda w: _portfolio_return(w, exp_ret) - target_return},
    ]
    bounds = [(-1.0, 1.0)] * n_assets if allow_short else [(0.0, 1.0)] * n_assets
    
    result = minimize(
        lambda w: _portfolio_volatility(w, cov),
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    
    if not result.success:
        raise ValidationError(
            f"Cannot achieve target return {target_return:.2%}. "
            "Try allowing short selling or adjusting the target."
        )
    
    weights = result.x
    ret = _portfolio_return(weights, exp_ret)
    vol = _portfolio_volatility(weights, cov)
    sharpe = ret / vol if vol > 0 else 0.0
    
    return PortfolioResult(
        weights=weights,
        expected_return=ret,
        volatility=vol,
        sharpe_ratio=sharpe,
        tickers=tickers,
        method=f"Target Return ({target_return:.2%})",
    )


def efficient_frontier(
    expected_returns: pd.Series | np.ndarray,
    cov_matrix: pd.DataFrame | np.ndarray,
    n_points: int = 50,
    allow_short: bool = False,
) -> list[PortfolioResult]:
    """
    Construct the efficient frontier.

    Parameters
    ----------
    n_points : int
        Number of portfolios to compute along the frontier

    Returns
    -------
    list[PortfolioResult]
        Portfolios from minimum variance to maximum return
    """
    if isinstance(expected_returns, pd.Series):
        exp_ret = expected_returns.values
    else:
        exp_ret = np.array(expected_returns)
    
    # Find min and max achievable returns
    min_var = min_volatility_portfolio(expected_returns, cov_matrix, allow_short)
    
    # Max return portfolio: all weight on highest-return asset (if long-only)
    if allow_short:
        max_ret = exp_ret.max() * 2  # Arbitrary upper bound for short-allowed
    else:
        max_ret = exp_ret.max()
    
    target_returns = np.linspace(min_var.expected_return, max_ret, n_points)
    frontier = []
    
    for target in target_returns:
        try:
            portfolio = target_return_portfolio(
                expected_returns, cov_matrix, target, allow_short
            )
            frontier.append(portfolio)
        except ValidationError:
            # Skip infeasible target returns
            continue
    
    return frontier
