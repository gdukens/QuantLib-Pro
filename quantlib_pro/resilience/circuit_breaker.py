"""
Circuit Breaker pattern for external API calls.
Prevents cascade failures when data providers fail.

State machine:
  CLOSED   -> normal operation, failure count tracked
  OPEN     -> rejecting calls, waiting for recovery_timeout
  HALF_OPEN -> testing recovery, one probe call allowed
"""

from __future__ import annotations

import threading
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""


class CircuitBreaker:
    """
    Thread-safe circuit breaker for a named external service.

    Args:
        name:              Human-readable service name (used in logs/metrics).
        failure_threshold: Number of consecutive failures before opening.
        recovery_timeout:  Seconds to wait in OPEN before probing.
        success_threshold: Consecutive successes in HALF_OPEN to close again.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ state

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and self._last_failure_time is not None
                and datetime.utcnow() - self._last_failure_time
                >= timedelta(seconds=self.recovery_timeout)
            ):
                log.info("[%s] OPEN → HALF_OPEN (recovery timeout elapsed)", self.name)
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            return self._state

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    # ----------------------------------------------------------------- public

    def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute *func* with circuit-breaker protection.

        If the circuit is OPEN and *fallback* is provided, the fallback is
        called instead of raising :class:`CircuitBreakerOpenError`.
        """
        current_state = self.state

        if current_state == CircuitState.OPEN:
            log.warning("[%s] Circuit OPEN – call rejected", self.name)
            if fallback is not None:
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN – service unavailable"
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            if fallback is not None:
                log.info("[%s] Call failed – using fallback", self.name)
                return fallback(*args, **kwargs)
            raise

    def reset(self) -> None:
        """Manually close the circuit (for testing / ops runbooks)."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
        log.info("[%s] Circuit manually reset to CLOSED", self.name)

    def snapshot(self) -> dict:
        """Return a JSON-serialisable health snapshot."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": (
                self._last_failure_time.isoformat()
                if self._last_failure_time
                else None
            ),
        }

    # --------------------------------------------------------------- internal

    def _on_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    log.info("[%s] HALF_OPEN → CLOSED", self.name)
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            log.error(
                "[%s] failure #%d/%d: %s",
                self.name,
                self._failure_count,
                self.failure_threshold,
                exc,
            )
            if self._failure_count >= self.failure_threshold:
                if self._state != CircuitState.OPEN:
                    log.critical("[%s] → OPEN after %d failures", self.name, self._failure_count)
                    self._state = CircuitState.OPEN


# ------------------------------------------------------------------- registry


class CircuitBreakerRegistry:
    """Singleton registry – one circuit breaker per named service."""

    _instance: Optional["CircuitBreakerRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "CircuitBreakerRegistry":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._breakers: dict[str, CircuitBreaker] = {}
                cls._instance = inst
        return cls._instance

    def get(self, name: str, **kwargs: Any) -> CircuitBreaker:
        """Get or create a :class:`CircuitBreaker` by service name."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self._breakers[name]

    def all_snapshots(self) -> dict[str, dict]:
        """Return health snapshots for all registered breakers."""
        return {name: cb.snapshot() for name, cb in self._breakers.items()}

    def reset_all(self) -> None:
        """Reset every breaker (test helper)."""
        for cb in self._breakers.values():
            cb.reset()


# Module-level singleton
registry = CircuitBreakerRegistry()
