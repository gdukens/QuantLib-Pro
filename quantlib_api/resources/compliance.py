"""
QuantLib Pro SDK — Compliance Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class ComplianceResource(BaseResource):
    """Compliance checks and regulatory reporting."""

    PREFIX = "/api/v1/compliance"

    def trade_check(
        self,
        ticker: str,
        side: str,
        quantity: int,
        portfolio_id: str = "DEMO_PORT",
    ) -> Dict[str, Any]:
        """
        Pre-trade compliance check.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        side : str
            "buy" or "sell"
        quantity : int
            Trade quantity
        portfolio_id : str
            Portfolio identifier

        Returns
        -------
        dict
            Compliance check results (position limits, restricted list, etc.)
        """
        return self._http.post(
            self._url("/trade-check"),
            json={
                "ticker": ticker,
                "side": side,
                "quantity": quantity,
                "portfolio_id": portfolio_id,
            },
        )

    def audit_log(
        self,
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Get paginated audit log entries."""
        return self._http.get(
            self._url("/audit-log"),
            params={
                "start_date": start_date,
                "end_date": end_date,
                "page": page,
                "page_size": page_size,
            },
        )

    def policy_evaluate(
        self,
        policy_rules: List[str],
        portfolio_id: str = "DEMO_PORT",
    ) -> Dict[str, Any]:
        """Evaluate portfolio against policy rules."""
        return self._http.post(
            self._url("/policy/evaluate"),
            json={"policy_rules": policy_rules, "portfolio_id": portfolio_id},
        )

    def regulatory_report(
        self,
        report_type: str,
        period: str = "Q4_2025",
    ) -> Dict[str, Any]:
        """Generate regulatory report (MiFID II, Dodd-Frank, Basel III, CCAR)."""
        return self._http.post(
            self._url("/regulatory-report"),
            json={"report_type": report_type, "period": period},
        )

    def gdpr_status(self) -> Dict[str, Any]:
        """Get GDPR compliance status and data subject requests."""
        return self._http.get(self._url("/gdpr/status"))

    def position_limits(self) -> Dict[str, Any]:
        """Get position limit monitoring with breach detection."""
        return self._http.get(self._url("/position-limits"))
