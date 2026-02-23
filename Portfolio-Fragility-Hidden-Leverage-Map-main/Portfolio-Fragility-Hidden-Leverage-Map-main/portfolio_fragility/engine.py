# Core logic for portfolio construction, risk, and scenario simulation
import numpy as np
import pandas as pd

class Portfolio:
    def __init__(self, assets, weights, vol_target=0.1, leverage=1.0, convexity=0.0):
        self.assets = assets
        self.weights = np.array(weights)
        self.vol_target = vol_target
        self.leverage = leverage
        self.convexity = convexity

    def simulate(self, mu, cov, n_days=252, rebalance_freq=21, vol_shock=1.0, corr_shock=1.0, liquidity_haircut=0.0, seed=None):
        '''
        Simulate portfolio returns under stress scenarios.
        mu: expected returns (array)
        cov: base covariance matrix
        vol_shock: multiplier for asset vols
        corr_shock: multiplier for off-diagonal correlations
        liquidity_haircut: percent loss on illiquid assets
        '''
        if seed is not None:
            np.random.seed(seed)
        # Shock covariance
        base_vols = np.sqrt(np.diag(cov))
        base_corr = cov / np.outer(base_vols, base_vols)
        np.fill_diagonal(base_corr, 1.0)
        shocked_vols = base_vols * vol_shock
        shocked_corr = base_corr * corr_shock
        np.fill_diagonal(shocked_corr, 1.0)
        shocked_cov = np.outer(shocked_vols, shocked_vols) * shocked_corr
        # Simulate returns
        returns = np.random.multivariate_normal(mu, shocked_cov, n_days)
        # Apply liquidity haircut
        returns[:, -1] -= liquidity_haircut
        # Portfolio returns
        port_rets = returns @ self.weights
        # Vol targeting and leverage
        realized_vol = np.std(port_rets) * np.sqrt(252)
        if realized_vol > 0:
            scaling = self.vol_target / realized_vol
        else:
            scaling = 1.0
        port_rets = port_rets * scaling * self.leverage
        # Optional convex payoff (e.g., long gamma)
        if self.convexity > 0:
            port_rets += self.convexity * (port_rets ** 2)
        return port_rets, returns

    @staticmethod
    def drawdown(returns):
        cum = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cum)
        dd = (cum - peak) / peak
        return dd

    @staticmethod
    def max_drawdown(returns):
        dd = Portfolio.drawdown(returns)
        return np.min(dd)

    @staticmethod
    def tail_loss(returns, q=0.01):
        return np.percentile(returns, 100 * q)

    @staticmethod
    def fragility_index(returns):
        # Fragility: sensitivity of loss to vol/corr shocks
        # Here: ratio of tail loss to mean return
        mean = np.mean(returns)
        tail = Portfolio.tail_loss(returns)
        if mean == 0:
            return np.inf
        return abs(tail / mean)

    @staticmethod
    def convexity_score(returns):
        # Convexity: difference between up-vol and down-vol
        up = returns[returns > 0]
        down = returns[returns < 0]
        if len(up) == 0 or len(down) == 0:
            return 0
        return np.std(up) - np.std(down)

    @staticmethod
    def hidden_leverage_score(returns, leverage):
        # Hidden leverage: excess loss in tail vs. stated leverage
        tail = abs(Portfolio.tail_loss(returns))
        return tail / leverage if leverage > 0 else np.nan
