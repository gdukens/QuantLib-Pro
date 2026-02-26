"""
QuantLib Pro SDK — Analytics Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class AnalyticsResource(BaseResource):
    """Advanced analytics: correlation, PCA, factor analysis."""

    PREFIX = "/api/v1/analytics"

    def correlation(
        self,
        tickers: List[str],
        lookback_days: int = 252,
        method: str = "pearson",
    ) -> Dict[str, Any]:
        """
        Compute correlation matrix.

        Parameters
        ----------
        tickers : list of str
            Tickers to analyze
        lookback_days : int
            Historical lookback period
        method : str
            Correlation method: "pearson", "spearman", "kendall"

        Returns
        -------
        dict
            Correlation matrix and metadata
        """
        return self._http.post(
            self._url("/correlation"),
            json={
                "tickers": tickers,
                "lookback_days": lookback_days,
                "method": method,
            },
        )

    def pca(
        self,
        tickers: List[str],
        n_components: int = 3,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """Perform PCA on asset returns."""
        return self._http.post(
            self._url("/pca"),
            json={
                "tickers": tickers,
                "n_components": n_components,
                "lookback_days": lookback_days,
            },
        )

    def factor_analysis(
        self,
        ticker: str,
        factors: List[str] = None,
    ) -> Dict[str, Any]:
        """Analyze factor exposures for an asset."""
        return self._http.post(
            self._url("/factor-analysis"),
            json={
                "ticker": ticker,
                "factors": factors or ["MKT", "SMB", "HML", "MOM"],
            },
        )

    def return_attribution(
        self,
        portfolio_id: str,
        period_days: int = 252,
    ) -> Dict[str, Any]:
        """Get return attribution breakdown."""
        return self._http.post(
            self._url("/return-attribution"),
            json={"portfolio_id": portfolio_id, "period_days": period_days},
        )
