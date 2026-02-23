"""Suite A: Options Pricing & Derivatives

Consolidates:
- Black-Scholes-Visual-Explainer
- Monte-Carlo-Option-Pricing-Simulator
- Volatility-Surface-Builder
"""
# Black-Scholes analytical pricing
from quantlib_pro.options.black_scholes import (
    delta as bs_delta,
    gamma as bs_gamma,
    implied_volatility,
    price as bs_price,
    price_call,
    price_put,
    price_with_greeks,
    rho as bs_rho,
    theta as bs_theta,
    vega as bs_vega,
)

# Monte Carlo simulation
from quantlib_pro.options.monte_carlo import (
    MonteCarloConfig,
    price_asian_call,
    price_barrier_up_and_out_call,
    price_european,
    price_lookback_call,
)

# Greeks computation
from quantlib_pro.options.greeks import (
    GreeksProfile,
    compute_delta_fd,
    compute_gamma_fd,
    compute_greeks,
    compute_rho_fd,
    compute_theta_fd,
    compute_vega_fd,
)

__all__ = [
    # Black-Scholes
    "price_call",
    "price_put",
    "bs_price",
    "price_with_greeks",
    "implied_volatility",
    "bs_delta",
    "bs_gamma",
    "bs_vega",
    "bs_theta",
    "bs_rho",
    # Monte Carlo
    "MonteCarloConfig",
    "price_european",
    "price_asian_call",
    "price_lookback_call",
    "price_barrier_up_and_out_call",
    # Greeks
    "GreeksProfile",
    "compute_greeks",
    "compute_delta_fd",
    "compute_gamma_fd",
    "compute_vega_fd",
    "compute_theta_fd",
    "compute_rho_fd",
]