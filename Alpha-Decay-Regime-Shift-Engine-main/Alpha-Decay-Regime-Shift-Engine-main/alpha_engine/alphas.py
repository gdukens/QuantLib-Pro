import numpy as np
import pandas as pd

def momentum_alpha(prices, lookback=20):
    """
    Simple momentum: return over lookback window.
    """
    return prices.pct_change(periods=lookback)

def mean_reversion_alpha(prices, lookback=20):
    """
    Mean reversion: negative z-score of price vs rolling mean.
    """
    roll_mean = prices.rolling(lookback).mean()
    roll_std = prices.rolling(lookback).std()
    zscore = (prices - roll_mean) / roll_std
    return -zscore

def volatility_carry_alpha(prices, lookback=20):
    """
    Volatility carry: realized volatility minus rolling mean volatility.
    """
    returns = prices.pct_change()
    realized_vol = returns.rolling(lookback).std()
    mean_vol = realized_vol.rolling(lookback).mean()
    return realized_vol - mean_vol
