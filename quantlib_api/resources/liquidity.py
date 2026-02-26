"""
QuantLib Pro SDK — Liquidity Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class LiquidityResource(BaseResource):
    """Liquidity analysis and market microstructure."""

    PREFIX = "/api/v1/liquidity"

    def order_book(
        self,
        ticker: str,
        depth: int = 10,
    ) -> Dict[str, Any]:
        """
        Simulate order book with calibrated depth.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        depth : int
            Order book depth (number of levels)

        Returns
        -------
        dict
            Bid/ask levels with sizes
        """
        return self._http.post(
            self._url("/order-book"),
            json={"ticker": ticker, "depth": depth},
        )

    def metrics(
        self,
        ticker: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Calculate liquidity metrics (Amihud, Kyle's lambda, Roll's spread)."""
        return self._http.post(
            self._url("/metrics"),
            json={"ticker": ticker, "lookback_days": lookback_days},
        )

    def market_impact(
        self,
        ticker: str,
        order_size: int,
        order_type: str = "market",
    ) -> Dict[str, Any]:
        """Estimate market impact for an order."""
        return self._http.post(
            self._url("/market-impact"),
            json={
                "ticker": ticker,
                "order_size": order_size,
                "order_type": order_type,
            },
        )

    def flash_crash(
        self,
        ticker: str,
        shock_magnitude: float = 0.05,
        recovery_minutes: int = 30,
    ) -> Dict[str, Any]:
        """Simulate flash crash scenario."""
        return self._http.post(
            self._url("/flash-crash"),
            json={
                "ticker": ticker,
                "shock_magnitude": shock_magnitude,
                "recovery_minutes": recovery_minutes,
            },
        )

    def heatmap(self, ticker: str) -> Dict[str, Any]:
        """Get intraday liquidity heatmap."""
        return self._http.get(self._url(f"/heatmap/{ticker}"))
