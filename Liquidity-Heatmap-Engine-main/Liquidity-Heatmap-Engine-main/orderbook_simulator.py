import numpy as np
import pandas as pd

class OrderBookSimulator:
    def __init__(self, n_levels=40, n_steps=300, price_start=100.0, tick_size=0.1):
        self.n_levels = n_levels
        self.n_steps = n_steps
        self.price_start = price_start
        self.tick_size = tick_size
        self.mid_prices = []
        self.order_books = []
        self.stats = []

    def _generate_order_book(self, mid_price):
        # Simulate bid/ask prices and volumes
        prices = np.arange(mid_price - self.n_levels//2 * self.tick_size,
                          mid_price + self.n_levels//2 * self.tick_size,
                          self.tick_size)
        bid_volumes = np.random.poisson(20, self.n_levels)
        ask_volumes = np.random.poisson(20, self.n_levels)
        # Random large order injection
        if np.random.rand() < 0.15:
            idx = np.random.randint(0, self.n_levels)
            if np.random.rand() < 0.5:
                bid_volumes[idx] += np.random.randint(100, 300)
            else:
                ask_volumes[idx] += np.random.randint(100, 300)
        return prices, bid_volumes, ask_volumes

    def _compute_stats(self, bid_volumes, ask_volumes):
        bid_sum = np.sum(bid_volumes)
        ask_sum = np.sum(ask_volumes)
        imbalance = (bid_sum - ask_sum) / (bid_sum + ask_sum + 1e-6)
        # Volume clustering: find price levels with high volume
        clustering = np.where((bid_volumes > np.percentile(bid_volumes, 90)) |
                              (ask_volumes > np.percentile(ask_volumes, 90)))[0]
        # Liquidity walls: large orders
        wall_threshold = np.percentile(np.concatenate([bid_volumes, ask_volumes]), 98)
        walls = np.where((bid_volumes > wall_threshold) |
                         (ask_volumes > wall_threshold))[0]
        return {
            'bid_sum': bid_sum,
            'ask_sum': ask_sum,
            'imbalance': imbalance,
            'clustering': clustering,
            'walls': walls
        }

    def run_simulation(self):
        mid_price = self.price_start
        for step in range(self.n_steps):
            prices, bid_volumes, ask_volumes = self._generate_order_book(mid_price)
            self.order_books.append((prices, bid_volumes, ask_volumes))
            self.mid_prices.append(mid_price)
            stats = self._compute_stats(bid_volumes, ask_volumes)
            self.stats.append(stats)
            # Mid-price moves randomly, influenced by imbalance
            mid_price += np.random.normal(loc=stats['imbalance']*0.2, scale=0.05)
