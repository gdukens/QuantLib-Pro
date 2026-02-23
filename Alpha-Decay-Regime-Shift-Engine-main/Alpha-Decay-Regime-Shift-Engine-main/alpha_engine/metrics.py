import numpy as np
import pandas as pd

def turnover_adjusted_returns(alpha, returns, transaction_cost=0.001):
    """
    Calculate turnover-adjusted returns for an alpha signal.
    """
    # Position: sign of alpha
    position = np.sign(alpha)
    # Turnover: change in position
    turnover = position.diff().abs().fillna(0)
    gross_returns = position.shift(1) * returns
    net_returns = gross_returns - turnover * transaction_cost
    return net_returns.cumsum(), turnover.sum()
