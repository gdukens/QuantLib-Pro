"""
black_scholes.py
----------------
Pricing and Greeks calculations for European options using the Black-Scholes model.
"""
import numpy as np
from scipy.stats import norm

def d1(S, K, T, r, sigma):
    return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

def d2(S, K, T, r, sigma):
    return d1(S, K, T, r, sigma) - sigma * np.sqrt(T)

def black_scholes_price(S, K, T, r, sigma, option_type='call'):
    D1 = d1(S, K, T, r, sigma)
    D2 = d2(S, K, T, r, sigma)
    if option_type == 'call':
        price = S * norm.cdf(D1) - K * np.exp(-r * T) * norm.cdf(D2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-D2) - S * norm.cdf(-D1)
    return price

def delta(S, K, T, r, sigma, option_type='call'):
    D1 = d1(S, K, T, r, sigma)
    if option_type == 'call':
        return norm.cdf(D1)
    else:
        return norm.cdf(D1) - 1

def gamma(S, K, T, r, sigma):
    D1 = d1(S, K, T, r, sigma)
    return norm.pdf(D1) / (S * sigma * np.sqrt(T))

def vega(S, K, T, r, sigma):
    D1 = d1(S, K, T, r, sigma)
    return S * norm.pdf(D1) * np.sqrt(T) / 100

def theta(S, K, T, r, sigma, option_type='call'):
    D1 = d1(S, K, T, r, sigma)
    D2 = d2(S, K, T, r, sigma)
    if option_type == 'call':
        theta = (-S * norm.pdf(D1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(D2)) / 365
    else:
        theta = (-S * norm.pdf(D1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-D2)) / 365
    return theta

def rho(S, K, T, r, sigma, option_type='call'):
    D2 = d2(S, K, T, r, sigma)
    if option_type == 'call':
        return K * T * np.exp(-r * T) * norm.cdf(D2) / 100
    else:
        return -K * T * np.exp(-r * T) * norm.cdf(-D2) / 100
