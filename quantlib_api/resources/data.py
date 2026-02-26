"""
QuantLib Pro SDK — Data Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class DataResource(BaseResource):
    """Market data access and management."""

    PREFIX = "/api/v1/data"

    def market_status(self) -> Dict[str, Any]:
        """Get current market status (open/closed, session info)."""
        return self._http.get(self._url("/market-status"))

    def quote(self, ticker: str) -> Dict[str, Any]:
        """Get real-time quote for a ticker."""
        return self._http.get(self._url(f"/quote/{ticker}"))

    def historical(
        self,
        ticker: str,
        start_date: str = None,
        end_date: str = None,
        interval: str = "1d",
    ) -> Dict[str, Any]:
        """
        Get historical price data.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        start_date : str
            Start date (YYYY-MM-DD)
        end_date : str
            End date (YYYY-MM-DD)
        interval : str
            Data interval ("1m", "5m", "1h", "1d", "1w")

        Returns
        -------
        dict
            OHLCV data
        """
        return self._http.post(
            self._url("/historical"),
            json={
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
            },
        )

    def quality_check(
        self,
        ticker: str,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """Check data quality for a ticker."""
        return self._http.get(
            self._url("/quality-check"),
            params={"ticker": ticker, "period_days": period_days},
        )
