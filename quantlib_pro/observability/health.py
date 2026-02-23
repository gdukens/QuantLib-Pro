"""
Health check system for QuantLib Pro.

Provides:
  - Component health checks (database, cache, APIs)
  - Liveness and readiness probes
  - Dependency health tracking
  - Health check aggregation
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

log = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component: str
    status: HealthStatus
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    latency_ms: Optional[float] = None
    details: dict = field(default_factory=dict)
    
    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self.status == HealthStatus.HEALTHY
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'latency_ms': self.latency_ms,
            'details': self.details,
        }


@dataclass
class SystemHealth:
    """Overall system health."""
    status: HealthStatus
    checks: list[HealthCheckResult]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'status': self.status.value,
            'timestamp': self.timestamp,
            'checks': [check.to_dict() for check in self.checks],
        }


class HealthChecker:
    """Health check manager."""
    
    def __init__(self):
        """Initialize health checker."""
        self._checks: dict[str, Callable[[], HealthCheckResult]] = {}
        self._last_results: dict[str, HealthCheckResult] = {}
    
    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """
        Register a health check.
        
        Parameters
        ----------
        name : str
            Check name
        check_func : Callable
            Function that returns HealthCheckResult
        """
        self._checks[name] = check_func
        log.info(f"Registered health check: {name}")
    
    def run_check(self, name: str) -> HealthCheckResult:
        """
        Run a specific health check.
        
        Parameters
        ----------
        name : str
            Check name
        
        Returns
        -------
        HealthCheckResult
            Check result
        """
        if name not in self._checks:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.UNKNOWN,
                message=f"Check {name} not registered",
            )
        
        start = time.perf_counter()
        
        try:
            result = self._checks[name]()
            result.latency_ms = (time.perf_counter() - start) * 1000
            self._last_results[name] = result
            return result
        except Exception as e:
            log.error(f"Health check {name} failed: {e}")
            result = HealthCheckResult(
                component=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                latency_ms=(time.perf_counter() - start) * 1000,
            )
            self._last_results[name] = result
            return result
    
    def run_all_checks(self) -> SystemHealth:
        """
        Run all registered health checks.
        
        Returns
        -------
        SystemHealth
            Overall system health
        """
        results = [self.run_check(name) for name in self._checks]
        
        # Determine overall status
        if all(r.is_healthy() for r in results):
            overall_status = HealthStatus.HEALTHY
        elif any(r.status == HealthStatus.UNHEALTHY for r in results):
            overall_status = HealthStatus.UNHEALTHY
        elif any(r.status == HealthStatus.DEGRADED for r in results):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return SystemHealth(status=overall_status, checks=results)
    
    def get_last_results(self) -> dict[str, HealthCheckResult]:
        """Get last health check results."""
        return self._last_results.copy()


# === Global Health Checker ===

_health_checker = HealthChecker()


def register_health_check(name: str, check_func: Callable[[], HealthCheckResult]):
    """Register a global health check."""
    _health_checker.register_check(name, check_func)


def check_health() -> SystemHealth:
    """Run all health checks."""
    return _health_checker.run_all_checks()


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    return _health_checker


# === Built-in Health Checks ===

def check_memory() -> HealthCheckResult:
    """
    Check memory usage.
    
    Returns
    -------
    HealthCheckResult
        Memory health check result
    """
    try:
        import psutil
        
        mem = psutil.virtual_memory()
        percent_used = mem.percent
        
        if percent_used < 80:
            status = HealthStatus.HEALTHY
            message = f"Memory usage: {percent_used:.1f}%"
        elif percent_used < 90:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {percent_used:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Critical memory usage: {percent_used:.1f}%"
        
        return HealthCheckResult(
            component='memory',
            status=status,
            message=message,
            details={
                'percent_used': percent_used,
                'available_mb': mem.available / (1024 * 1024),
                'total_mb': mem.total / (1024 * 1024),
            }
        )
    except Exception as e:
        return HealthCheckResult(
            component='memory',
            status=HealthStatus.UNKNOWN,
            message=f"Failed to check memory: {str(e)}",
        )


def check_disk() -> HealthCheckResult:
    """
    Check disk usage.
    
    Returns
    -------
    HealthCheckResult
        Disk health check result
    """
    try:
        import psutil
        
        disk = psutil.disk_usage('/')
        percent_used = disk.percent
        
        if percent_used < 80:
            status = HealthStatus.HEALTHY
            message = f"Disk usage: {percent_used:.1f}%"
        elif percent_used < 90:
            status = HealthStatus.DEGRADED
            message = f"High disk usage: {percent_used:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Critical disk usage: {percent_used:.1f}%"
        
        return HealthCheckResult(
            component='disk',
            status=status,
            message=message,
            details={
                'percent_used': percent_used,
                'free_gb': disk.free / (1024 ** 3),
                'total_gb': disk.total / (1024 ** 3),
            }
        )
    except Exception as e:
        return HealthCheckResult(
            component='disk',
            status=HealthStatus.UNKNOWN,
            message=f"Failed to check disk: {str(e)}",
        )


def check_cpu() -> HealthCheckResult:
    """
    Check CPU usage.
    
    Returns
    -------
    HealthCheckResult
        CPU health check result
    """
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        if cpu_percent < 70:
            status = HealthStatus.HEALTHY
            message = f"CPU usage: {cpu_percent:.1f}%"
        elif cpu_percent < 90:
            status = HealthStatus.DEGRADED
            message = f"High CPU usage: {cpu_percent:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Critical CPU usage: {cpu_percent:.1f}%"
        
        return HealthCheckResult(
            component='cpu',
            status=status,
            message=message,
            details={
                'percent_used': cpu_percent,
                'cpu_count': psutil.cpu_count(),
            }
        )
    except Exception as e:
        return HealthCheckResult(
            component='cpu',
            status=HealthStatus.UNKNOWN,
            message=f"Failed to check CPU: {str(e)}",
        )


def liveness_probe() -> bool:
    """
    Kubernetes liveness probe.
    
    Returns True if application is alive (should not be restarted).
    
    Returns
    -------
    bool
        True if alive
    """
    # Simple liveness check - just return True
    # In production, might check for deadlocks or critical failures
    return True


def readiness_probe() -> bool:
    """
    Kubernetes readiness probe.
    
    Returns True if application is ready to serve traffic.
    
    Returns
    -------
    bool
        True if ready
    """
    # Check critical dependencies
    health = check_health()
    
    # Ready if overall status is healthy or degraded (not unhealthy)
    return health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


# === Register default checks ===

def register_default_checks():
    """Register default system health checks."""
    register_health_check('memory', check_memory)
    register_health_check('disk', check_disk)
    register_health_check('cpu', check_cpu)
