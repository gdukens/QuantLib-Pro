import numpy as np
import pandas as pd

def rolling_ic(alpha, future_returns, window=60):
    """
    Compute rolling Information Coefficient (IC) between alpha and future returns.
    """
    return alpha.rolling(window).corr(future_returns)

def alpha_decay_half_life(ic_series):
    """
    Estimate half-life of alpha decay from rolling IC series.
    """
    ic = ic_series.dropna().values
    if len(ic) < 2:
        return np.nan
    lags = np.arange(1, min(100, len(ic)))
    acf = [np.corrcoef(ic[:-lag], ic[lag:])[0,1] for lag in lags]
    acf = np.array(acf)
    # Fit exponential decay: acf ~ exp(-lag/half_life)
    try:
        from scipy.optimize import curve_fit
        def exp_decay(x, hl):
            return np.exp(-x/hl)
        popt, _ = curve_fit(exp_decay, lags, acf, bounds=(0.1, 100))
        return popt[0]
    except Exception:
        return np.nan
