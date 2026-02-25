"""
Portfolio optimizer - convenience wrapper module.

This module re-exports the optimization functionality for cleaner imports.
"""

from quantlib_pro.portfolio.optimization import (
    PortfolioResult,
    max_sharpe_portfolio,
    min_volatility_portfolio,
    target_return_portfolio,
    efficient_frontier,
)

__all__ = [
    "PortfolioOptimizer",
    "PortfolioResult",
    "max_sharpe_portfolio",
    "min_volatility_portfolio",
    "target_return_portfolio",
    "efficient_frontier",
]


class PortfolioOptimizer:
    """
    Portfolio optimization class using Modern Portfolio Theory.
    
    Provides methods for:
    - Maximum Sharpe ratio optimization
    - Minimum variance optimization
    - Target return/volatility portfolios
    - Efficient frontier construction
    
    Parameters
    ----------
    expected_returns : np.ndarray
        Expected returns for each asset
    cov_matrix : np.ndarray
        Covariance matrix of asset returns
    risk_free_rate : float, optional
        Risk-free rate for Sharpe ratio calculation (default: 0.02)
    tickers : list[str], optional
        Asset ticker symbols
    """
    
    def __init__(
        self,
        expected_returns,
        cov_matrix,
        risk_free_rate=0.02,
        tickers=None
    ):
        import numpy as np
        import pandas as pd
        
        # Store as pandas Series to preserve tickers
        if isinstance(expected_returns, pd.Series):
            self.expected_returns = expected_returns
            self.tickers = expected_returns.index.tolist()
        else:
            exp_ret_array = np.asarray(expected_returns)
            if tickers is None:
                tickers = [f"Asset_{i+1}" for i in range(len(exp_ret_array))]
            self.tickers = list(tickers)
            self.expected_returns = pd.Series(exp_ret_array, index=self.tickers)
        
        # Store as pandas DataFrame to preserve structure
        if isinstance(cov_matrix, pd.DataFrame):
            self.cov_matrix = cov_matrix
        else:
            cov_array = np.asarray(cov_matrix)
            self.cov_matrix = pd.DataFrame(cov_array, index=self.tickers, columns=self.tickers)
        
        self.risk_free_rate = risk_free_rate
        self.n_assets = len(self.expected_returns)
    
    def max_sharpe(self, allow_short=False):
        """Optimize for maximum Sharpe ratio."""
        return max_sharpe_portfolio(
            self.expected_returns,
            self.cov_matrix,
            risk_free_rate=self.risk_free_rate,
            allow_short=allow_short
        )
    
    def min_variance(self, allow_short=False):
        """Optimize for minimum variance."""
        return min_volatility_portfolio(
            self.expected_returns,
            self.cov_matrix,
            allow_short=allow_short
        )
    
    def target_return(self, target_return, allow_short=False):
        """
        Optimize for minimum variance at a target return.
        
        Parameters
        ----------
        target_return : float
            Target expected return (e.g., 0.10 for 10%)
        allow_short : bool
            Allow short selling
        """
        return target_return_portfolio(
            self.expected_returns,
            self.cov_matrix,
            target_return=target_return,
            allow_short=allow_short
        )
    
    def target_volatility(self, target_vol, allow_short=False):
        """
        Optimize for maximum return at a target volatility.
        
        NOTE: This feature is not directly implemented in the underlying
        optimization module. Using target_return as workaround.
        
        Parameters
        ----------
        target_vol : float
            Target volatility (e.g., 0.15 for 15%)
        allow_short : bool
            Allow short selling
        """
        # Estimate a return target based on current portfolio metrics
        # This is a workaround since target_volatility_portfolio doesn't exist
        min_var = self.min_variance(allow_short=allow_short)
        
        if target_vol < min_var.volatility:
            raise ValueError(
                f"Target volatility {target_vol:.2%} is below minimum "
                f"achievable volatility {min_var.volatility:.2%}"
            )
        
        # Use binary search to find portfolio with approximately target volatility
        frontier = self.efficient_frontier(n_points=100, allow_short=allow_short)
        
        # Find portfolio closest to target volatility
        closest = min(frontier, key=lambda p: abs(p.volatility - target_vol))
        return closest
    
    def efficient_frontier(self, n_points=50, allow_short=False):
        """
        Compute the efficient frontier.
        
        Parameters
        ----------
        n_points : int
            Number of points on the frontier
        allow_short : bool
            Allow short selling
        
        Returns
        -------
        list[PortfolioResult]
            Portfolios along the efficient frontier
        """
        return efficient_frontier(
            self.expected_returns,
            self.cov_matrix,
            n_points=n_points,
            allow_short=allow_short
        )
