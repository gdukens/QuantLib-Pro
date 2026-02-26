"""
QuantLib Pro SDK — Market Regime Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class RegimeResource(BaseResource):
    """Market regime detection and analysis."""

    PREFIX = "/api/v1/regime"

    def detect(
        self,
        tickers: List[str],
        lookback_days: int = 252,
        n_regimes: int = 3,
    ) -> Dict[str, Any]:
        """
        Detect current market regime using Hidden Markov Model.

        Parameters
        ----------
        tickers : list of str
            Tickers to analyze
        lookback_days : int
            Historical lookback period
        n_regimes : int
            Number of hidden states (default: 3 for Bull/Bear/Neutral)

        Returns
        -------
        dict
            Current regime, probabilities, transition matrix
        """
        return self._http.post(
            self._url("/detect"),
            json={
                "tickers": tickers,
                "lookback_days": lookback_days,
                "n_regimes": n_regimes,
            },
        )

    def current(self, ticker: str = "SPY") -> Dict[str, Any]:
        """Get current market regime for a ticker."""
        return self._http.get(self._url(f"/current/{ticker}"))

    def history(
        self,
        ticker: str,
        period_days: int = 252,
    ) -> Dict[str, Any]:
        """Get regime history over a time period."""
        return self._http.get(
            self._url("/history"),
            params={"ticker": ticker, "period_days": period_days},
        )

    def probabilities(
        self,
        tickers: List[str],
    ) -> Dict[str, Any]:
        """Get regime transition probabilities."""
        return self._http.post(
            self._url("/probabilities"),
            json={"tickers": tickers},
        )
