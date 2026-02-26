"""
QuantLib Pro SDK — Volatility Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class VolatilityResource(BaseResource):
    """Volatility surface construction and analysis."""

    PREFIX = "/api/v1/volatility"

    def surface(
        self,
        ticker: str,
        expiries: List[int] = None,
        moneyness_range: List[float] = None,
    ) -> Dict[str, Any]:
        """
        Construct implied volatility surface.

        Parameters
        ----------
        ticker : str
            Underlying ticker
        expiries : list of int
            Days to expiration (e.g., [30, 60, 90, 180, 365])
        moneyness_range : list of float
            Moneyness levels (e.g., [0.8, 0.9, 1.0, 1.1, 1.2])

        Returns
        -------
        dict
            IV surface grid and metadata
        """
        return self._http.post(
            self._url("/surface"),
            json={
                "ticker": ticker,
                "expiries": expiries or [30, 60, 90, 180, 365],
                "moneyness_range": moneyness_range or [0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2],
            },
        )

    def term_structure(
        self,
        ticker: str,
        expiries: List[int] = None,
    ) -> Dict[str, Any]:
        """Get ATM volatility term structure."""
        return self._http.post(
            self._url("/term-structure"),
            json={
                "ticker": ticker,
                "expiries": expiries or [7, 14, 30, 60, 90, 180, 365],
            },
        )

    def smile(
        self,
        ticker: str,
        expiry_days: int = 30,
    ) -> Dict[str, Any]:
        """Get volatility smile for a specific expiry."""
        return self._http.post(
            self._url("/smile"),
            json={"ticker": ticker, "expiry_days": expiry_days},
        )

    def garch(
        self,
        ticker: str,
        lookback_days: int = 252,
        forecast_days: int = 20,
    ) -> Dict[str, Any]:
        """Fit GARCH model and forecast volatility."""
        return self._http.post(
            self._url("/garch"),
            json={
                "ticker": ticker,
                "lookback_days": lookback_days,
                "forecast_days": forecast_days,
            },
        )
