"""
QuantLib Pro SDK — Signals Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class SignalsResource(BaseResource):
    """Trading signal generation and backtesting."""

    PREFIX = "/api/v1/signals"

    def generate(
        self,
        ticker: str,
        strategies: List[str] = None,
        lookback_days: int = 60,
    ) -> Dict[str, Any]:
        """
        Generate trading signals.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        strategies : list of str
            Signal strategies (e.g., ["MA_CROSSOVER", "RSI", "MACD", "BOLLINGER", "MOMENTUM"])
        lookback_days : int
            Historical lookback period

        Returns
        -------
        dict
            Signals per strategy with confidence scores
        """
        return self._http.post(
            self._url("/generate"),
            json={
                "ticker": ticker,
                "strategies": strategies or ["MA_CROSSOVER", "RSI", "MACD"],
                "lookback_days": lookback_days,
            },
        )

    def current(self, ticker: str) -> Dict[str, Any]:
        """Get current signals for a ticker."""
        return self._http.get(self._url(f"/current/{ticker}"))

    def backtest(
        self,
        ticker: str,
        strategy: str,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """Backtest a signal strategy."""
        return self._http.post(
            self._url("/backtest"),
            json={
                "ticker": ticker,
                "strategy": strategy,
                "lookback_days": lookback_days,
            },
        )

    def screen(
        self,
        criteria: Dict[str, Any],
        universe: List[str] = None,
    ) -> Dict[str, Any]:
        """Screen universe for signals matching criteria."""
        return self._http.post(
            self._url("/screen"),
            json={
                "criteria": criteria,
                "universe": universe,
            },
        )
