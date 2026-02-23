"""
Greeks computation via finite differences and automatic differentiation.

Provides:
  - First-order Greeks: delta, gamma, vega, theta, rho
  - Second-order Greeks: vanna, charm, vomma, speed
  - Unified interface for any pricing function

Uses central finite differences for numerical stability.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Callable, Optional

from quantlib_pro.utils.types import CalculationResult, OptionType
from quantlib_pro.utils.validation import require_positive

log = logging.getLogger(__name__)

__version__ = "1.0.0"


@dataclass
class GreeksProfile:
    """Complete Greeks profile for an option position."""
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    
    # Second-order
    vanna: Optional[float] = None     # ∂²V/∂S∂σ
    charm: Optional[float] = None     # ∂²V/∂S∂t (delta decay)
    vomma: Optional[float] = None     # ∂²V/∂σ² (volga)
    speed: Optional[float] = None     # ∂³V/∂S³ (gamma of gamma)


# ─── Finite Difference Helpers ────────────────────────────────────────────────


def _central_diff_1st(
    f: Callable[[float], float],
    x: float,
    h: Optional[float] = None,
) -> float:
    """
    First derivative via central difference: [f(x+h) - f(x-h)] / (2h).
    """
    if h is None:
        h = max(1e-4 * abs(x), 1e-6)
    return (f(x + h) - f(x - h)) / (2 * h)


def _central_diff_2nd(
    f: Callable[[float], float],
    x: float,
    h: Optional[float] = None,
) -> float:
    """
    Second derivative via central difference: [f(x+h) - 2f(x) + f(x-h)] / h².
    """
    if h is None:
        h = max(1e-4 * abs(x), 1e-6)
    return (f(x + h) - 2 * f(x) + f(x - h)) / (h**2)


def _cross_derivative(
    f: Callable[[float, float], float],
    x: float,
    y: float,
    hx: Optional[float] = None,
    hy: Optional[float] = None,
) -> float:
    """
    Mixed second derivative ∂²f/∂x∂y.

    Uses: [f(x+hx,y+hy) - f(x+hx,y-hy) - f(x-hx,y+hy) + f(x-hx,y-hy)] / (4hx*hy)
    """
    if hx is None:
        hx = max(1e-4 * abs(x), 1e-6)
    if hy is None:
        hy = max(1e-4 * abs(y), 1e-6)
    
    term1 = f(x + hx, y + hy)
    term2 = f(x + hx, y - hy)
    term3 = f(x - hx, y + hy)
    term4 = f(x - hx, y - hy)
    return (term1 - term2 - term3 + term4) / (4 * hx * hy)


# ─── First-Order Greeks via Finite Difference ─────────────────────────────────


def compute_delta_fd(
    pricing_fn: Callable[[float], float],
    S: float,
    h: Optional[float] = None,
) -> float:
    """
    Compute delta = ∂V/∂S via finite difference.

    Parameters
    ----------
    pricing_fn : callable
        Function that takes spot price S and returns option price.
    S : float
        Current spot price.
    h : float, optional
        Step size (default: 0.01% of S).
    """
    return _central_diff_1st(pricing_fn, S, h)


def compute_gamma_fd(
    pricing_fn: Callable[[float], float],
    S: float,
    h: Optional[float] = None,
) -> float:
    """Compute gamma = ∂²V/∂S² via finite difference."""
    return _central_diff_2nd(pricing_fn, S, h)


def compute_vega_fd(
    pricing_fn: Callable[[float], float],
    sigma: float,
    h: Optional[float] = None,
) -> float:
    """
    Compute vega = ∂V/∂σ via finite difference.

    Parameters
    ----------
    pricing_fn : callable
        Function that takes volatility sigma and returns option price.
    """
    return _central_diff_1st(pricing_fn, sigma, h)


def compute_theta_fd(
    pricing_fn: Callable[[float], float],
    T: float,
    h: Optional[float] = None,
) -> float:
    """
    Compute theta = -∂V/∂t via finite difference.

    Note: We differentiate with respect to T (time to expiration), so
    ∂V/∂T = -∂V/∂t. Therefore theta = -dV/dT.

    Parameters
    ----------
    pricing_fn : callable
        Function that takes time to expiration T and returns option price.
    """
    if h is None:
        h = 1 / 365  # 1 day in years
    # Theta is negative of the derivative w.r.t. T
    return -_central_diff_1st(pricing_fn, T, h)


def compute_rho_fd(
    pricing_fn: Callable[[float], float],
    r: float,
    h: float = 0.0001,
) -> float:
    """Compute rho = ∂V/∂r via finite difference."""
    return _central_diff_1st(pricing_fn, r, h)


# ─── Second-Order Greeks ──────────────────────────────────────────────────────


def compute_vanna_fd(
    pricing_fn: Callable[[float, float], float],
    S: float,
    sigma: float,
) -> float:
    """
    Compute vanna = ∂²V/∂S∂σ (cross-derivative of delta and vega).

    Parameters
    ----------
    pricing_fn : callable
        Function that takes (S, sigma) and returns option price.
    """
    return _cross_derivative(pricing_fn, S, sigma)


def compute_charm_fd(
    pricing_fn: Callable[[float, float], float],
    S: float,
    T: float,
) -> float:
    """
    Compute charm = ∂²V/∂S∂t (rate of change of delta over time).

    Note: charm = -∂²V/∂S∂T (negative because we use T, not t).

    Parameters
    ----------
    pricing_fn : callable
        Function that takes (S, T) and returns option price.
    """
    return -_cross_derivative(pricing_fn, S, T)


def compute_vomma_fd(
    pricing_fn: Callable[[float], float],
    sigma: float,
) -> float:
    """
    Compute vomma (volga) = ∂²V/∂σ² (convexity of option value w.r.t. volatility).

    Parameters
    ----------
    pricing_fn : callable
        Function that takes sigma and returns option price.
    """
    return _central_diff_2nd(pricing_fn, sigma)


def compute_speed_fd(
    pricing_fn: Callable[[float], float],
    S: float,
) -> float:
    """
    Compute speed = ∂³V/∂S³ (third derivative w.r.t. spot).

    Approximation: d³f/dx³ ≈ [f(x+2h) - 2f(x+h) + 2f(x-h) - f(x-2h)] / (2h³)
    """
    h = max(1e-4 * abs(S), 1e-6)
    term1 = pricing_fn(S + 2 * h)
    term2 = -2 * pricing_fn(S + h)
    term3 = 2 * pricing_fn(S - h)
    term4 = -pricing_fn(S - 2 * h)
    return (term1 + term2 + term3 + term4) / (2 * h**3)


# ─── Unified Interface ────────────────────────────────────────────────────────


def compute_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
    pricing_fn: Callable[[float, float, float, float, float, OptionType], float],
    include_second_order: bool = False,
) -> GreeksProfile:
    """
    Compute all Greeks for a given option using finite differences.

    Parameters
    ----------
    pricing_fn : callable
        Signature: ``pricing_fn(S, K, T, r, sigma, option_type) -> float``
        This can be any pricing function (Black-Scholes, Monte Carlo, etc.)
    include_second_order : bool
        If True, compute vanna, charm, vomma, speed.

    Returns
    -------
    GreeksProfile
        Dataclass containing all computed Greeks.

    Examples
    --------
    >>> from quantlib_pro.options.black_scholes import price
    >>> greeks = compute_greeks(100, 100, 1.0, 0.05, 0.2, OptionType.CALL, price)
    >>> greeks.delta
    0.636...
    """
    # Partial application to create single-variable functions
    price_of_S = lambda s: pricing_fn(s, K, T, r, sigma, option_type)
    price_of_sigma = lambda sig: pricing_fn(S, K, T, r, sig, option_type)
    price_of_T = lambda t: pricing_fn(S, K, t, r, sigma, option_type)
    price_of_r = lambda rate: pricing_fn(S, K, T, rate, sigma, option_type)

    opt_delta = compute_delta_fd(price_of_S, S)
    opt_gamma = compute_gamma_fd(price_of_S, S)
    opt_vega = compute_vega_fd(price_of_sigma, sigma)
    opt_theta = compute_theta_fd(price_of_T, T)
    opt_rho = compute_rho_fd(price_of_r, r)

    vanna = charm = vomma = speed = None

    if include_second_order:
        price_of_S_sigma = lambda s, sig: pricing_fn(s, K, T, r, sig, option_type)
        price_of_S_T = lambda s, t: pricing_fn(s, K, t, r, sigma, option_type)
        
        vanna = compute_vanna_fd(price_of_S_sigma, S, sigma)
        charm = compute_charm_fd(price_of_S_T, S, T)
        vomma = compute_vomma_fd(price_of_sigma, sigma)
        speed = compute_speed_fd(price_of_S, S)

    return GreeksProfile(
        delta=opt_delta,
        gamma=opt_gamma,
        vega=opt_vega,
        theta=opt_theta,
        rho=opt_rho,
        vanna=vanna,
        charm=charm,
        vomma=vomma,
        speed=speed,
    )


def compute_portfolio_greeks(
    positions: list[tuple[float, GreeksProfile]],
) -> GreeksProfile:
    """
    Aggregate Greeks for a portfolio of options.

    Parameters
    ----------
    positions : list[tuple[float, GreeksProfile]]
        List of (quantity, greeks) tuples. Quantity can be negative for shorts.

    Returns
    -------
    GreeksProfile
        Net Greeks for the entire portfolio.

    Examples
    --------
    >>> g1 = GreeksProfile(delta=0.5, gamma=0.02, vega=15, theta=-0.03, rho=0.4)
    >>> g2 = GreeksProfile(delta=-0.3, gamma=0.01, vega=10, theta=-0.02, rho=0.2)
    >>> portfolio = [(100, g1), (-50, g2)]  # 100 long g1, 50 short g2
    >>> net = compute_portfolio_greeks(portfolio)
    >>> net.delta
    65.0
    """
    net_delta = sum(qty * g.delta for qty, g in positions)
    net_gamma = sum(qty * g.gamma for qty, g in positions)
    net_vega = sum(qty * g.vega for qty, g in positions)
    net_theta = sum(qty * g.theta for qty, g in positions)
    net_rho = sum(qty * g.rho for qty, g in positions)

    # Second-order (only if all positions have them)
    has_second_order = all(g.vanna is not None for _, g in positions)
    if has_second_order:
        net_vanna = sum(qty * g.vanna for qty, g in positions)
        net_charm = sum(qty * g.charm for qty, g in positions)
        net_vomma = sum(qty * g.vomma for qty, g in positions)
        net_speed = sum(qty * g.speed for qty, g in positions)
    else:
        net_vanna = net_charm = net_vomma = net_speed = None

    return GreeksProfile(
        delta=net_delta,
        gamma=net_gamma,
        vega=net_vega,
        theta=net_theta,
        rho=net_rho,
        vanna=net_vanna,
        charm=net_charm,
        vomma=net_vomma,
        speed=net_speed,
    )
