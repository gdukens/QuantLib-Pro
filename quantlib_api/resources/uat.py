"""
QuantLib Pro SDK — UAT Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class UATResource(BaseResource):
    """UAT scenarios and stress monitoring."""

    PREFIX = "/api/v1/uat"

    def run_scenarios(
        self,
        scenario_ids: List[str] = None,
        environment: str = "staging",
    ) -> Dict[str, Any]:
        """
        Execute UAT test scenarios.

        Parameters
        ----------
        scenario_ids : list of str
            Scenario IDs to run (None = all)
        environment : str
            Target environment

        Returns
        -------
        dict
            Scenario results with pass/fail status
        """
        return self._http.post(
            self._url("/scenarios/run"),
            json={
                "scenario_ids": scenario_ids,
                "environment": environment,
            },
        )

    def bugs(
        self,
        severity: str = None,
        status: str = None,
    ) -> Dict[str, Any]:
        """List bug reports with filtering."""
        return self._http.get(
            self._url("/bugs"),
            params={"severity": severity, "status": status},
        )

    def feedback(
        self,
        feedback_type: str,
        title: str,
        description: str,
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """Submit user feedback (bug, feature request, usability)."""
        return self._http.post(
            self._url("/feedback"),
            json={
                "feedback_type": feedback_type,
                "title": title,
                "description": description,
                "priority": priority,
            },
        )

    def performance_validation(self) -> Dict[str, Any]:
        """Get module performance benchmarks vs SLAs."""
        return self._http.get(self._url("/performance-validation"))

    def stress_monitor(
        self,
        trader_id: str,
        session_duration_hours: float = 4.0,
        trades_count: int = 50,
    ) -> Dict[str, Any]:
        """Analyze trader cognitive load and fatigue."""
        return self._http.post(
            self._url("/stress-monitor/analyze"),
            json={
                "trader_id": trader_id,
                "session_duration_hours": session_duration_hours,
                "trades_count": trades_count,
            },
        )

    def ab_tests(self) -> Dict[str, Any]:
        """Get A/B test configurations and results."""
        return self._http.get(self._url("/ab-tests"))
