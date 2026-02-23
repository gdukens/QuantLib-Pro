from scipy.optimize import brentq
from black_scholes import black_scholes_price

def implied_volatility(price, S, K, T, r, option_type='call', tol=1e-6, max_iter=100):
    """
    Numerically solve for implied volatility using Brent's method.
    """
    def objective(sigma):
        return black_scholes_price(S, K, T, r, sigma, option_type) - price
    try:
        iv = brentq(objective, 1e-6, 5.0, xtol=tol, maxiter=max_iter)
        return iv
    except Exception:
        return None
