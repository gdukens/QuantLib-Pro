"""
Black-Scholes-Merton analytical option pricing.

Closed-form solutions for European call and put options on non-dividend
paying stocks. Includes all first-order Greeks (delta, gamma, vega, theta, rho).

References:
    Black, F., & Scholes, M. (1973). "The Pricing of Options and Corporate
    Liabilities." Journal of Political Economy, 81(3), 637-654.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Optional

from scipy.stats import norm

from quantlib_pro.utils.types import CalculationResult, OptionType
from quantlib_pro.utils.validation import validate_black_scholes_inputs

log = logging.getLogger(__name__)

__version__ = "1.0.0"


def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Compute d₁ term from Black-Scholes formula."""
    return (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))


def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Compute d₂ term from Black-Scholes formula."""
    return _d1(S, K, T, r, sigma) - sigma * math.sqrt(T)


# ─── Option Pricing ───────────────────────────────────────────────────────────


def price_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """
    Price a European call option using Black-Scholes.

    Parameters
    ----------
    S : float
        Current spot price of the underlying asset.
    K : float
        Strike price.
    T : float
        Time to expiration in years.
    r : float
        Risk-free interest rate (annualized, continuously compounded).
    sigma : float
        Volatility of the underlying (annualized standard deviation).

    Returns
    -------
    float
        Fair value of the call option.

    Examples
    --------
    >>> price_call(S=100, K=100, T=1.0, r=0.05, sigma=0.2)
    10.450583572185565
    """
    validate_black_scholes_inputs(S, K, T, r, sigma)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)


def price_put(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """
    Price a European put option using Black-Scholes.

    Parameters
    ----------
    S, K, T, r, sigma : float
        Same as :func:`price_call`.

    Returns
    -------
    float
        Fair value of the put option.

    Examples
    --------
    >>> price_put(S=100, K=100, T=1.0, r=0.05, sigma=0.2)
    5.573526022256971
    """
    validate_black_scholes_inputs(S, K, T, r, sigma)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> float:
    """
    Price a European option using Black-Scholes.

    Parameters
    ----------
    option_type : OptionType
        Either ``OptionType.CALL`` or ``OptionType.PUT``.

    Returns
    -------
    float
        Fair value of the option.
    """
    if option_type == OptionType.CALL:
        return price_call(S, K, T, r, sigma)
    elif option_type == OptionType.PUT:
        return price_put(S, K, T, r, sigma)
    else:
        raise ValueError(f"Unknown option type: {option_type}")


# ─── Greeks ───────────────────────────────────────────────────────────────────


def delta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> float:
    """
    Compute option delta: ∂V/∂S.

    Delta measures the rate of change of option value with respect to
    changes in the underlying asset price.

    Returns
    -------
    float
        Delta (between 0 and 1 for call, -1 and 0 for put).
    """
    validate_black_scholes_inputs(S, K, T, r, sigma)
    d1 = _d1(S, K, T, r, sigma)
    if option_type == OptionType.CALL:
        return norm.cdf(d1)
    elif option_type == OptionType.PUT:
        return norm.cdf(d1) - 1.0
    else:
        raise ValueError(f"Unknown option type: {option_type}")


def gamma(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """
    Compute option gamma: ∂²V/∂S².

    Gamma measures the rate of change of delta with respect to changes
    in the underlying asset price. Gamma is the same for calls and puts.

    Returns
    -------
    float
        Gamma (always positive).
    """
    validate_black_scholes_inputs(S, K, T, r, sigma)
    d1 = _d1(S, K, T, r, sigma)
    return norm.pdf(d1) / (S * sigma * math.sqrt(T))


def vega(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """
    Compute option vega: ∂V/∂σ.

    Vega measures sensitivity to volatility changes. Vega is the same
    for calls and puts.

    Returns
    -------
    float
        Vega (dollars per 1% change in volatility).
    """
    validate_black_scholes_inputs(S, K, T, r, sigma)
    d1 = _d1(S, K, T, r, sigma)
    return S * norm.pdf(d1) * math.sqrt(T)


def theta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> float:
    """
    Compute option theta: -∂V/∂t (note the negative sign).

    Theta measures the rate of time decay. Typically reported as the
    change in value per 1 day (divide result by 365 for daily theta).

    Returns
    -------
    float
        Theta (annualized time decay, usually negative for long options).
    """
    validate_black_scholes_inputs(S, K, T, r, sigma)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
    
    if option_type == OptionType.CALL:
        term2 = -r * K * math.exp(-r * T) * norm.cdf(d2)
        return term1 + term2
    elif option_type == OptionType.PUT:
        term2 = r * K * math.exp(-r * T) * norm.cdf(-d2)
        return term1 + term2
    else:
        raise ValueError(f"Unknown option type: {option_type}")


def rho(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> float:
    """
    Compute option rho: ∂V/∂r.

    Rho measures sensitivity to the risk-free interest rate.

    Returns
    -------
    float
        Rho (dollars per 1% change in interest rate).
    """
    validate_black_scholes_inputs(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    
    if option_type == OptionType.CALL:
        return K * T * math.exp(-r * T) * norm.cdf(d2)
    elif option_type == OptionType.PUT:
        return -K * T * math.exp(-r * T) * norm.cdf(-d2)
    else:
        raise ValueError(f"Unknown option type: {option_type}")


# ─── High-level interface ─────────────────────────────────────────────────────


def price_with_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> CalculationResult:
    """
    Price an option and compute all first-order Greeks in one call.

    Returns a :class:`~quantlib_pro.utils.types.CalculationResult` with
    the option price and all Greeks.

    Examples
    --------
    >>> result = price_with_greeks(S=100, K=100, T=1.0, r=0.05, sigma=0.2, option_type=OptionType.CALL)
    >>> result.outputs["price"]
    10.450583572185565
    >>> result.outputs["delta"]
    0.6368...
    """
    t0 = time.perf_counter()
    validate_black_scholes_inputs(S, K, T, r, sigma)

    opt_price = price(S, K, T, r, sigma, option_type)
    opt_delta = delta(S, K, T, r, sigma, option_type)
    opt_gamma = gamma(S, K, T, r, sigma)
    opt_vega = vega(S, K, T, r, sigma)
    opt_theta = theta(S, K, T, r, sigma, option_type)
    opt_rho = rho(S, K, T, r, sigma, option_type)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    warnings = []
    if T < 0.01:  # < 4 days
        warnings.append("Very short time to expiration — theta is extremely large")
    if sigma > 1.5:
        warnings.append("High volatility (>150%) — verify input data quality")

    return CalculationResult(
        calculation_type="black_scholes",
        inputs={
            "S": S,
            "K": K,
            "T": T,
            "r": r,
            "sigma": sigma,
            "option_type": option_type.value,
        },
        outputs={
            "price": opt_price,
            "delta": opt_delta,
            "gamma": opt_gamma,
            "vega": opt_vega,
            "theta": opt_theta,
            "rho": opt_rho,
            "theta_daily": opt_theta / 365,  # convenient daily theta
        },
        model_version=__version__,
        execution_time_ms=elapsed_ms,
        warnings=warnings,
    )


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: OptionType,
    tolerance: float = 1e-6,
    max_iterations: int = 100,
) -> float:
    """
    Compute implied volatility via Newton-Raphson iteration.

    Parameters
    ----------
    market_price : float
        Observed market price of the option.
    tolerance : float
        Convergence tolerance for the iterative solver.
    max_iterations : int
        Maximum number of Newton-Raphson iterations.

    Returns
    -------
    float
        Implied volatility (annualized).

    Raises
    ------
    RuntimeError
        If the solver fails to converge.
    """
    validate_black_scholes_inputs(S, K, T, r, 0.2)  # use a fake sigma for validation
    
    # Initial guess: ATM approximation
    sigma_guess = math.sqrt(2 * math.pi / T) * (market_price / S)
    sigma_guess = max(0.01, min(sigma_guess, 3.0))  # clamp to [1%, 300%]

    for iteration in range(max_iterations):
        model_price = price(S, K, T, r, sigma_guess, option_type)
        diff = model_price - market_price

        if abs(diff) < tolerance:
            return sigma_guess

        # Newton step: vega is dPrice/dSigma
        vega_val = vega(S, K, T, r, sigma_guess)
        if vega_val < 1e-10:
            raise RuntimeError(
                f"Vega too small at iteration {iteration} — cannot invert for IV"
            )

        sigma_guess -= diff / vega_val
        sigma_guess = max(0.001, min(sigma_guess, 5.0))  # keep in bounds

    raise RuntimeError(
        f"Implied volatility did not converge after {max_iterations} iterations"
    )
