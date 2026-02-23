"""
strategies.py

Contains trading strategy classes for the Algorithmic Trading Battle Simulator.
- MomentumStrategy: Moving Average Crossover
- MeanReversionStrategy: RSI-based mean reversion
- RandomStrategy: Random buy/sell baseline
"""

import numpy as np
import pandas as pd

class MomentumStrategy:
    """
    Moving Average Crossover Strategy
    Buys when short MA crosses above long MA, sells on opposite cross.
    """
    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data):
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['short_ma'] = data['Close'].rolling(window=self.short_window, min_periods=1).mean()
        signals['long_ma'] = data['Close'].rolling(window=self.long_window, min_periods=1).mean()
        signals.loc[signals.index[self.short_window:], 'signal'] = np.where(
            signals['short_ma'][self.short_window:] > signals['long_ma'][self.short_window:], 1, 0)
        signals['signal'] = signals['signal'].astype(float)
        signals['positions'] = signals['signal'].diff().fillna(0)
        return signals

class MeanReversionStrategy:
    """
    RSI-based Mean Reversion Strategy
    Buys when RSI < lower, sells when RSI > upper.
    """
    def __init__(self, rsi_period=14, lower=30, upper=70):
        self.rsi_period = rsi_period
        self.lower = lower
        self.upper = upper

    def compute_rsi(self, series):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period, min_periods=1).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, data):
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['rsi'] = self.compute_rsi(data['Close'])
        signals['signal'] = np.where(signals['rsi'] < self.lower, 1, np.where(signals['rsi'] > self.upper, -1, 0))
        signals['signal'] = signals['signal'].astype(float)
        signals['positions'] = signals['signal'].diff().fillna(0)
        return signals

class RandomStrategy:
    """
    Random Buy/Sell Strategy
    Randomly buys, sells, or holds at each step.
    """
    def __init__(self, seed=None):
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate_signals(self, data):
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = np.random.choice([1, 0, -1], size=len(data)).astype(float)
        signals['positions'] = signals['signal'].diff().fillna(0)
        return signals
