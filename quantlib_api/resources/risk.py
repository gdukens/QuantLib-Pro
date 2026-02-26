"""
QuantLib Pro SDK — Risk Resource
"""
from typing import Any, Dict, List, Optional
from quantlib_api.resources.base import BaseResource


class RiskResource(BaseResource):
    """Risk analysis: VaR, CVaR, stress testing."""

    PREFIX = "/api/v1/risk"

    def var(
        self,
        portfolio_id: str = "DEMO_PORT",
        confidence_level: float = 0.95,
        method: str = "historical",
        horizon_days: int = 10,
    ) -> Dict[str, Any]:
        """
        Compute Value at Risk (VaR) and Conditional VaR (CVaR).

        Parameters
        ----------
        portfolio_id : str
            Portfolio identifier
        confidence_level : float
            VaR confidence level (e.g., 0.95 for 95%)
        method : str
            One of "historical", "parametric", "monte_carlo"
        horizon_days : int
            Risk horizon in trading days

        Returns
        -------
        dict
            VaR, CVaR values and metadata
        """
        return self._http.post(
            self._url("/var"),
            json={
                "portfolio_id": portfolio_id,
                "confidence_level": confidence_level,
                "method": method,
                "horizon_days": horizon_days,
            },
        )

    def stress_test(
        self,
        portfolio_id: str,
        scenarios: List[str],
    ) -> Dict[str, Any]:
        """
        Run stress test scenarios on portfolio.

        Parameters
        ----------
        portfolio_id : str
            Portfolio identifier
        scenarios : list of str
            Scenario names (e.g., ["2008_crisis", "covid_crash", "rate_shock"])
        """
        return self._http.post(
            self._url("/stress-test"),
            json={"portfolio_id": portfolio_id, "scenarios": scenarios},
        )

    def tail_risk(
        self,
        portfolio_id: str,
        distribution: str = "student_t",
        tail_percentile: float = 0.05,
    ) -> Dict[str, Any]:
        """Analyze tail risk using fat-tailed distributions."""
        return self._http.post(
            self._url("/tail-risk"),
            json={
                "portfolio_id": portfolio_id,
                "distribution": distribution,
                "tail_percentile": tail_percentile,
            },
        )

    def drawdown(
        self,
        portfolio_id: str,
        period_days: int = 252,
    ) -> Dict[str, Any]:
        """Calculate maximum drawdown and drawdown duration."""
        return self._http.get(
            self._url("/drawdown"),
            params={"portfolio_id": portfolio_id, "period_days": period_days},
        )

    def correlation_stress(
        self,
        tickers: List[str],
        stress_factor: float = 1.5,
    ) -> Dict[str, Any]:
        """Analyze correlation breakdown under stress scenarios."""
        return self._http.post(
            self._url("/correlation-stress"),
            json={"tickers": tickers, "stress_factor": stress_factor},
        )
