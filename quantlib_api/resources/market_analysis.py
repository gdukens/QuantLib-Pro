"""
QuantLib Pro SDK — Market Analysis Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class MarketAnalysisResource(BaseResource):
    """Technical indicators and market analysis."""

    PREFIX = "/api/v1/market-analysis"

    def technical_analysis(
        self,
        ticker: str,
        indicators: List[str] = None,
        lookback_days: int = 60,
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        indicators : list of str
            Indicators to compute (e.g., ["RSI", "MACD", "BB", "ATR", "SMA", "EMA"])
        lookback_days : int
            Historical lookback period

        Returns
        -------
        dict
            Indicator values and signals
        """
        return self._http.post(
            self._url("/technical-analysis"),
            json={
                "ticker": ticker,
                "indicators": indicators or ["RSI", "MACD", "BB", "ATR", "SMA_20", "EMA_12"],
                "lookback_days": lookback_days,
            },
        )

    def volatility_comparison(
        self,
        tickers: List[str],
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """Compare volatility across multiple tickers."""
        return self._http.post(
            self._url("/volatility-comparison"),
            json={"tickers": tickers, "period_days": period_days},
        )

    def trend_analysis(
        self,
        ticker: str,
        lookback_days: int = 60,
    ) -> Dict[str, Any]:
        """Analyze price trend using linear regression and Hurst exponent."""
        return self._http.post(
            self._url("/trend-analysis"),
            json={"ticker": ticker, "lookback_days": lookback_days},
        )

    def screener(
        self,
        criteria: str = "oversold",
        universe: List[str] = None,
    ) -> Dict[str, Any]:
        """Screen stocks by technical criteria."""
        return self._http.get(
            self._url("/screener"),
            params={
                "criteria": criteria,
                "universe": ",".join(universe) if universe else None,
            },
        )

    def price_levels(self, ticker: str) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        return self._http.get(self._url(f"/price-levels/{ticker}"))
