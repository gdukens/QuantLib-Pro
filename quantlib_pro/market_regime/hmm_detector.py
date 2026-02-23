"""
Market regime detection using Hidden Markov Models.

Identifies distinct market states (Bull, Bear, Sideways, High Volatility)
based on price/volatility patterns using statistical regime-switching models.

Uses hmmlearn for Gaussian HMM estimation with:
  - Observable features: returns, volatility, momentum
  - Hidden states: discrete regimes with transition probabilities
  - Viterbi algorithm for most likely state sequence
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd
from hmmlearn import hmm

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


class RegimeType(Enum):
    """Market regime classifications."""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class RegimeResult:
    """Results from regime detection."""
    regimes: np.ndarray  # Array of regime labels (integers)
    regime_names: list[str]  # Human-readable names
    transition_matrix: np.ndarray  # P(state_t+1 | state_t)
    timestamps: pd.DatetimeIndex  # Time index
    confidence: Optional[np.ndarray] = None  # Posterior probabilities
    
    def get_current_regime(self) -> str:
        """Return the most recent regime name."""
        return self.regime_names[self.regimes[-1]]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame with timestamps."""
        return pd.DataFrame({
            'regime': [self.regime_names[r] for r in self.regimes],
            'regime_id': self.regimes,
        }, index=self.timestamps)


def _build_features(
    prices: pd.Series,
    volatility_window: int = 21,
    momentum_window: int = 21,
) -> pd.DataFrame:
    """
    Construct feature matrix for regime detection.

    Parameters
    ----------
    prices : pd.Series
        Price time series (indexed by date)
    volatility_window : int
        Rolling window for volatility estimation
    momentum_window : int
        Lookback period for momentum

    Returns
    -------
    pd.DataFrame
        Features: returns, volatility, momentum
    """
    features = pd.DataFrame(index=prices.index)
    
    # Feature 1: Log returns
    features['returns'] = np.log(prices / prices.shift(1))
    
    # Feature 2: Rolling volatility (annualized)
    features['volatility'] = features['returns'].rolling(window=volatility_window).std() * np.sqrt(252)
    
    # Feature 3: Momentum (price change over N days)
    features['momentum'] = prices.pct_change(momentum_window)
    
    # Feature 4: Volume-weighted momentum (if volume available)
    # features['volume_momentum'] = (prices.pct_change() * volume).rolling(20).mean()
    
    features = features.dropna()
    return features


def detect_regimes_hmm(
    prices: pd.Series,
    n_regimes: int = 3,
    volatility_window: int = 21,
    momentum_window: int = 21,
    random_state: int = 42,
) -> RegimeResult:
    """
    Detect market regimes using Gaussian Hidden Markov Model.

    Parameters
    ----------
    prices : pd.Series
        Price time series (must have datetime index)
    n_regimes : int
        Number of discrete regimes to detect (typically 2-4)
    volatility_window : int
        Rolling window for volatility calculation
    momentum_window : int
        Lookback for momentum feature
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    RegimeResult
        Detected regimes and transition probabilities
    """
    require_positive(n_regimes, "n_regimes")
    require_positive(len(prices), "prices length")
    
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValidationError("prices must have DatetimeIndex")
    
    # Build feature matrix
    features = _build_features(prices, volatility_window, momentum_window)
    X = features[['returns', 'volatility', 'momentum']].values
    
    if len(X) < n_regimes * 10:
        raise ValidationError(
            f"Insufficient data: need at least {n_regimes * 10} observations, got {len(X)}"
        )
    
    # Fit Gaussian HMM with diagonal covariance
    model = hmm.GaussianHMM(
        n_components=n_regimes,
        covariance_type='diag',
        n_iter=1000,
        random_state=random_state,
        init_params='stmc',  # Initialize start probabilities, transition matrix, means, covariances
    )
    
    try:
        model.fit(X)
    except Exception as e:
        raise ValidationError(f"HMM fitting failed: {e}")
    
    # Predict most likely state sequence (Viterbi)
    regimes = model.predict(X)
    
    # Compute posterior probabilities
    posteriors = model.predict_proba(X)
    confidence = posteriors.max(axis=1)  # Max probability for each time step
    
    # Label regimes based on mean returns
    regime_stats = pd.DataFrame({
        'mean_return': features['returns'].groupby(regimes).mean(),
        'mean_volatility': features['volatility'].groupby(regimes).mean(),
    })
    
    # Assign labels: highest return = bull, lowest = bear
    sorted_by_return = regime_stats['mean_return'].sort_values(ascending=False)
    
    if n_regimes == 2:
        regime_names = ['bull', 'bear']
        mapping = {sorted_by_return.index[0]: 0, sorted_by_return.index[1]: 1}
    elif n_regimes == 3:
        regime_names = ['bull', 'sideways', 'bear']
        bull = sorted_by_return.index[0]
        bear = sorted_by_return.index[-1]
        sideways = [i for i in regime_stats.index if i not in [bull, bear]][0]
        mapping = {bull: 0, sideways: 1, bear: 2}
    elif n_regimes == 4:
        # Bull, sideways, bear, high-vol
        sorted_by_vol = regime_stats['mean_volatility'].sort_values(ascending=False)
        high_vol = sorted_by_vol.index[0]
        bull = sorted_by_return.index[0] if sorted_by_return.index[0] != high_vol else sorted_by_return.index[1]
        bear = sorted_by_return.index[-1]
        sideways = [i for i in regime_stats.index if i not in [bull, bear, high_vol]][0]
        regime_names = ['bull', 'sideways', 'bear', 'high_volatility']
        mapping = {bull: 0, sideways: 1, bear: 2, high_vol: 3}
    else:
        # Generic numeric labels
        regime_names = [f'regime_{i}' for i in range(n_regimes)]
        mapping = {i: i for i in range(n_regimes)}
    
    # Remap regimes to standardized labels
    regimes_labeled = np.array([mapping[r] for r in regimes])
    
    return RegimeResult(
        regimes=regimes_labeled,
        regime_names=regime_names,
        transition_matrix=model.transmat_,
        timestamps=features.index,
        confidence=confidence,
    )


def detect_regimes_fast(
    prices: pd.Series,
    n_regimes: int = 3,
) -> RegimeResult:
    """
    Fast regime detection using simple thresholds on returns and volatility.

    Faster than HMM but less statistically rigorous.
    Useful for real-time applications.

    Parameters
    ----------
    prices : pd.Series
        Price time series
    n_regimes : int
        Number of regimes (2 or 3 supported)

    Returns
    -------
    RegimeResult
        Detected regimes (no transition matrix)
    """
    if n_regimes not in [2, 3]:
        raise ValidationError("Fast method only supports 2 or 3 regimes")
    
    features = _build_features(prices)
    returns = features['returns'].values
    volatility = features['volatility'].values
    
    # Percentile-based thresholds
    return_25 = np.percentile(returns, 25)
    return_75 = np.percentile(returns, 75)
    
    if n_regimes == 2:
        # Bull vs Bear (based on returns)
        regimes = np.where(returns > np.median(returns), 0, 1)
        regime_names = ['bull', 'bear']
    else:  # n_regimes == 3
        # Bull, Sideways, Bear
        regimes = np.full(len(returns), 1, dtype=int)  # Default: sideways
        regimes[returns > return_75] = 0  # Bull
        regimes[returns < return_25] = 2  # Bear
        regime_names = ['bull', 'sideways', 'bear']
    
    # Dummy transition matrix (uniform)
    transition_matrix = np.ones((n_regimes, n_regimes)) / n_regimes
    
    return RegimeResult(
        regimes=regimes,
        regime_names=regime_names,
        transition_matrix=transition_matrix,
        timestamps=features.index,
    )
