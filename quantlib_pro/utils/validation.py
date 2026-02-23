"""
Input validation helpers reused across every module.
Fail-fast with informative messages rather than propagating bad numbers.
"""

from __future__ import annotations

import math
from typing import Any


class ValidationError(ValueError):
    """Raised when a domain input fails validation."""


def require_positive(value: float, name: str) -> float:
    """Value must be > 0 and finite."""
    _check_finite(value, name)
    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")
    return value


def require_non_negative(value: float, name: str) -> float:
    """Value must be >= 0 and finite."""
    _check_finite(value, name)
    if value < 0:
        raise ValidationError(f"{name} must be non-negative, got {value}")
    return value


def require_probability(value: float, name: str) -> float:
    """Value must be in [0, 1]."""
    _check_finite(value, name)
    if not 0.0 <= value <= 1.0:
        raise ValidationError(f"{name} must be in [0, 1], got {value}")
    return value


def require_range(value: float, name: str, lo: float, hi: float) -> float:
    """Value must be in [lo, hi]."""
    _check_finite(value, name)
    if not lo <= value <= hi:
        raise ValidationError(f"{name} must be in [{lo}, {hi}], got {value}")
    return value


def require_ticker(ticker: Any) -> str:
    """Ticker must be a non-empty string of reasonable length."""
    if not isinstance(ticker, str):
        raise ValidationError(f"Ticker must be a string, got {type(ticker).__name__}")
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValidationError("Ticker cannot be empty")
    if len(ticker) > 20:
        raise ValidationError(f"Ticker too long ({len(ticker)} chars): {ticker!r}")
    return ticker


def validate_black_scholes_inputs(
    S: float, K: float, T: float, r: float, sigma: float
) -> None:
    """
    Validate all Black-Scholes inputs.
    Raises :class:`ValidationError` on the first failure found.
    """
    require_positive(S, "Spot price (S)")
    require_positive(K, "Strike price (K)")
    require_non_negative(T, "Time to expiry (T)")
    _check_finite(r, "Risk-free rate (r)")
    require_non_negative(sigma, "Volatility (sigma)")

    if sigma > 3.0:   # 300% annualised vol
        raise ValidationError(
            f"Volatility {sigma:.1%} exceeds maximum allowed 300%. "
            "Check your inputs – this value is unrealistic."
        )


# ----------------------------------------------------------------- internal


def _check_finite(value: Any, name: str) -> None:
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric, got {type(value).__name__}")
    if math.isnan(value):
        raise ValidationError(f"{name} is NaN")
    if math.isinf(value):
        raise ValidationError(f"{name} is infinite")
