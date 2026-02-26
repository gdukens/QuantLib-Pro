"""
QuantLib Pro SDK — Health Resource
"""
from typing import Any, Dict
from quantlib_api.resources.base import BaseResource


class HealthResource(BaseResource):
    """API health checks."""

    PREFIX = ""

    def check(self) -> Dict[str, Any]:
        """
        Check API health status.

        Returns
        -------
        dict
            Health status, uptime, version
        """
        return self._http.get("/health")

    def detailed(self) -> Dict[str, Any]:
        """Get detailed health check with component status."""
        return self._http.get("/health/detailed")

    def readiness(self) -> Dict[str, Any]:
        """Check if API is ready to accept traffic."""
        return self._http.get("/health/readiness")

    def liveness(self) -> Dict[str, Any]:
        """Check if API process is alive."""
        return self._http.get("/health/liveness")
