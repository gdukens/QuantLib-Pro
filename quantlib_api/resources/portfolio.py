"""
QuantLib Pro SDK — Portfolio Resource
"""
from typing import Any, Dict, List, Optional
from quantlib_api.resources.base import BaseResource


class PortfolioResource(BaseResource):
    """Portfolio optimization and management endpoints."""

    PREFIX = "/api/v1/portfolio"

    def optimize(
        self,
        tickers: List[str],
        budget: float = 100000.0,
        risk_free_rate: float = 0.045,
        optimization_target: str = "sharpe",
        max_position_size: float = 0.40,
    ) -> Dict[str, Any]:
        """
        Compute optimal portfolio weights using Modern Portfolio Theory.

        Parameters
        ----------
        tickers : list of str
            Stock ticker symbols (e.g., ["AAPL", "GOOGL", "MSFT"])
        budget : float
            Total investment amount in dollars
        risk_free_rate : float
            Risk-free rate (e.g., 0.045 for 4.5%)
        optimization_target : str
            One of "sharpe", "min_volatility", "max_return"
        max_position_size : float
            Maximum weight for any single position (0.0 to 1.0)

        Returns
        -------
        dict
            Optimal weights, expected return, volatility, Sharpe ratio
        """
        return self._http.post(
            self._url("/optimize"),
            json={
                "tickers": tickers,
                "budget": budget,
                "risk_free_rate": risk_free_rate,
                "optimization_target": optimization_target,
                "max_position_size": max_position_size,
            },
        )

    def performance(
        self,
        portfolio_id: str = "DEMO_PORT",
        period_days: int = 252,
    ) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        return self._http.get(
            self._url("/performance"),
            params={"portfolio_id": portfolio_id, "period_days": period_days},
        )

    def efficient_frontier(
        self,
        tickers: List[str],
        n_portfolios: int = 1000,
    ) -> Dict[str, Any]:
        """Compute efficient frontier curve."""
        return self._http.post(
            self._url("/efficient-frontier"),
            json={"tickers": tickers, "n_portfolios": n_portfolios},
        )

    def sharpe_analysis(
        self,
        tickers: List[str],
        lookback_days: int = 252,
        risk_free_rate: float = 0.045,
    ) -> Dict[str, Any]:
        """Analyze Sharpe ratios for multiple assets."""
        return self._http.post(
            self._url("/sharpe-analysis"),
            json={
                "tickers": tickers,
                "lookback_days": lookback_days,
                "risk_free_rate": risk_free_rate,
            },
        )

    def rebalance(
        self,
        portfolio_id: str,
        target_weights: Dict[str, float],
        threshold: float = 0.05,
    ) -> Dict[str, Any]:
        """Calculate rebalancing trades to reach target weights."""
        return self._http.post(
            self._url("/rebalance"),
            json={
                "portfolio_id": portfolio_id,
                "target_weights": target_weights,
                "threshold": threshold,
            },
        )


class AsyncPortfolioResource(BaseResource):
    """Async portfolio resource (for AsyncQuantLibClient)."""

    PREFIX = "/api/v1/portfolio"

    async def aoptimize(
        self,
        tickers: List[str],
        budget: float = 100000.0,
        risk_free_rate: float = 0.045,
        optimization_target: str = "sharpe",
        max_position_size: float = 0.40,
    ) -> Dict[str, Any]:
        """Async version of optimize()."""
        return await self._http.post(
            self._url("/optimize"),
            json={
                "tickers": tickers,
                "budget": budget,
                "risk_free_rate": risk_free_rate,
                "optimization_target": optimization_target,
                "max_position_size": max_position_size,
            },
        )
