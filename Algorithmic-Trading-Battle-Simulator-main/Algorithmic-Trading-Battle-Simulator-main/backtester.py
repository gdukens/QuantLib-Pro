"""
backtester.py

Backtesting engine for Algorithmic Trading Battle Simulator.
Calculates equity curve, returns, and performance metrics for a given strategy.
"""

import numpy as np
import pandas as pd

class Backtester:
    def __init__(self, data, signals, initial_capital=10000):
        self.data = data
        self.signals = signals
        self.initial_capital = initial_capital
        self.results = None

    def run(self):
        positions = self.signals['signal'].shift(1).fillna(0).values
        if positions.ndim > 1:
            positions = positions.flatten()
        returns = self.data['Close'].pct_change().fillna(0).values
        if returns.ndim > 1:
            returns = returns.flatten()
        equity = np.zeros(len(returns))
        equity[0] = self.initial_capital
        for i in range(1, len(returns)):
            try:
                r = float(returns[i])
                pos = float(positions[i])
            except Exception as e:
                print(f"Error: r={returns[i]}, pos={positions[i]}, types=({type(returns[i])}, {type(positions[i])})")
                pos = 0.0
                r = 0.0
            equity[i] = equity[i-1] * (1 + r * pos)
        self.results = pd.DataFrame({
            'Equity': equity,
            'Returns': returns,
            'Position': positions
        }, index=self.data.index)
        return self.results

    def cumulative_return(self):
        if self.results is None:
            self.run()
        return self.results['Equity'].iloc[-1] / self.initial_capital - 1

    def sharpe_ratio(self):
        if self.results is None:
            self.run()
        excess = self.results['Returns']
        return np.sqrt(252) * excess.mean() / (excess.std() + 1e-10)

    def max_drawdown(self):
        if self.results is None:
            self.run()
        equity = self.results['Equity']
        roll_max = equity.cummax()
        drawdown = (equity - roll_max) / roll_max
        return drawdown.min()

    def win_rate(self):
        if self.results is None:
            self.run()
        wins = (self.results['Returns'] > 0).sum()
        total = (self.results['Returns'] != 0).sum()
        return wins / total if total > 0 else 0
