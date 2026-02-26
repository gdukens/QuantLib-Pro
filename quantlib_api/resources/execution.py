"""
QuantLib Pro SDK — Execution Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class ExecutionResource(BaseResource):
    """Execution optimization: VWAP, TWAP, market impact models."""

    PREFIX = "/api/v1/execution"

    def market_impact(
        self,
        ticker: str,
        shares: int,
        models: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare market impact models.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        shares : int
            Number of shares to execute
        models : list of str
            Impact models to compare (e.g., ["almgren_chriss", "kyle", "jpm", "square_root"])

        Returns
        -------
        dict
            Impact estimates from each model
        """
        return self._http.post(
            self._url("/market-impact"),
            json={
                "ticker": ticker,
                "shares": shares,
                "models": models or ["almgren_chriss", "kyle", "square_root"],
            },
        )

    def vwap_schedule(
        self,
        ticker: str,
        shares: int,
        time_horizon_hours: float = 4.0,
        n_slices: int = 8,
    ) -> Dict[str, Any]:
        """Generate VWAP execution schedule."""
        return self._http.post(
            self._url("/vwap-schedule"),
            json={
                "ticker": ticker,
                "shares": shares,
                "time_horizon_hours": time_horizon_hours,
                "n_slices": n_slices,
            },
        )

    def twap_schedule(
        self,
        ticker: str,
        shares: int,
        time_horizon_hours: float = 4.0,
        n_slices: int = 8,
        randomize: bool = True,
    ) -> Dict[str, Any]:
        """Generate TWAP execution schedule."""
        return self._http.post(
            self._url("/twap-schedule"),
            json={
                "ticker": ticker,
                "shares": shares,
                "time_horizon_hours": time_horizon_hours,
                "n_slices": n_slices,
                "randomize": randomize,
            },
        )

    def optimal_trajectory(
        self,
        ticker: str,
        shares: int,
        risk_aversion: float = 1e-6,
        time_horizon_hours: float = 4.0,
    ) -> Dict[str, Any]:
        """Compute Almgren-Chriss optimal liquidation trajectory."""
        return self._http.post(
            self._url("/optimal-trajectory"),
            json={
                "ticker": ticker,
                "shares": shares,
                "risk_aversion": risk_aversion,
                "time_horizon_hours": time_horizon_hours,
            },
        )

    def cost_analysis(
        self,
        execution_log: List[Dict[str, Any]],
        arrival_price: float,
    ) -> Dict[str, Any]:
        """Analyze execution costs vs arrival price."""
        return self._http.post(
            self._url("/cost-analysis"),
            json={
                "execution_log": execution_log,
                "arrival_price": arrival_price,
            },
        )
