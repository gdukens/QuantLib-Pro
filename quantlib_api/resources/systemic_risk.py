"""
QuantLib Pro SDK — Systemic Risk Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class SystemicRiskResource(BaseResource):
    """Systemic risk and contagion analysis."""

    PREFIX = "/api/v1/systemic-risk"

    def network_analysis(
        self,
        tickers: List[str],
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """
        Analyze correlation network with centrality metrics.

        Parameters
        ----------
        tickers : list of str
            Universe of tickers
        lookback_days : int
            Historical lookback period

        Returns
        -------
        dict
            Network nodes, edges, centrality measures
        """
        return self._http.post(
            self._url("/network-analysis"),
            json={"tickers": tickers, "lookback_days": lookback_days},
        )

    def covar(
        self,
        target_ticker: str,
        system_tickers: List[str],
        confidence: float = 0.95,
    ) -> Dict[str, Any]:
        """Compute CoVaR, Delta-CoVaR, SRISK, MES."""
        return self._http.post(
            self._url("/covar"),
            json={
                "target_ticker": target_ticker,
                "system_tickers": system_tickers,
                "confidence": confidence,
            },
        )

    def fragility_index(
        self,
        portfolio_weights: Dict[str, float],
        leverage: float = 1.0,
    ) -> Dict[str, Any]:
        """Compute portfolio fragility with hidden leverage."""
        return self._http.post(
            self._url("/fragility-index"),
            json={
                "portfolio_weights": portfolio_weights,
                "leverage": leverage,
            },
        )

    def contagion(
        self,
        initial_shock: Dict[str, float],
        network_tickers: List[str],
        rounds: int = 5,
    ) -> Dict[str, Any]:
        """Simulate multi-round contagion cascade."""
        return self._http.post(
            self._url("/contagion"),
            json={
                "initial_shock": initial_shock,
                "network_tickers": network_tickers,
                "rounds": rounds,
            },
        )

    def too_big_to_fail(self) -> Dict[str, Any]:
        """Get TBTF scoring (size, interconnectedness, complexity)."""
        return self._http.get(self._url("/too-big-to-fail"))
