"""
QuantLib Pro SDK — Macro Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class MacroResource(BaseResource):
    """Macro analysis and economic indicators."""

    PREFIX = "/api/v1/macro"

    def indicators(
        self,
        indicators: List[str] = None,
        period: str = "1Y",
    ) -> Dict[str, Any]:
        """
        Get economic indicator values.

        Parameters
        ----------
        indicators : list of str
            Indicator codes (e.g., ["GDP", "CPI", "UNEMPLOYMENT", "FED_RATE"])
        period : str
            Time period (e.g., "1Y", "5Y", "10Y")

        Returns
        -------
        dict
            Indicator values and time series
        """
        return self._http.post(
            self._url("/indicators"),
            json={
                "indicators": indicators or ["GDP", "CPI", "UNEMPLOYMENT", "FED_RATE"],
                "period": period,
            },
        )

    def correlation_regime(
        self,
        asset: str,
        macro_indicators: List[str] = None,
    ) -> Dict[str, Any]:
        """Analyze correlation regime between asset and macro indicators."""
        return self._http.post(
            self._url("/correlation-regime"),
            json={
                "asset": asset,
                "macro_indicators": macro_indicators or ["SPY", "TLT", "GLD", "DXY"],
            },
        )

    def sentiment(
        self,
        sources: List[str] = None,
    ) -> Dict[str, Any]:
        """Get market sentiment indicators."""
        return self._http.get(
            self._url("/sentiment"),
            params={"sources": ",".join(sources or ["vix", "put_call", "aaii"])},
        )
