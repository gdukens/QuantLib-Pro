import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

def detect_regimes(returns, n_regimes=3, regime_sensitivity=1.0, random_state=42):
    """
    Fit a Gaussian HMM to returns and return regime states.
    """
    # Scale returns for sensitivity
    scaled_returns = returns * regime_sensitivity
    model = GaussianHMM(n_components=n_regimes, covariance_type="diag", n_iter=200, random_state=random_state)
    model.fit(scaled_returns.reshape(-1, 1))
    hidden_states = model.predict(scaled_returns.reshape(-1, 1))
    return hidden_states, model

def regime_persistence(model):
    """
    Calculate regime persistence (average diagonal of transition matrix).
    """
    transmat = model.transmat_
    return np.mean(np.diag(transmat))
