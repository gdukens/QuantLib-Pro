"""
Order book simulation engine.

Simulates a limit order book with realistic microstructure:
  - Multiple price levels (bids and asks)
  - Limit orders, market orders, cancellations
  - Spread dynamics and liquidity replenishment
  - Market impact from large orders

Used for:
  - Execution strategy backtesting
  - Slippage estimation
  - Market impact analysis
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


@dataclass
class Order:
    """Represents a single order."""
    order_id: int
    side: str  # 'buy' or 'sell'
    price: float
    size: int
    order_type: str  # 'limit' or 'market'
    timestamp: float = 0.0


@dataclass
class Trade:
    """Executed trade."""
    timestamp: float
    price: float
    size: int
    side: str  # 'buy' or 'sell' (from aggressor perspective)


@dataclass
class OrderBookSnapshot:
    """Snapshot of order book state."""
    timestamp: float
    bids: dict[float, int]  # {price: volume}
    asks: dict[float, int]
    mid_price: float
    spread: float
    depth: tuple[int, int]  # (bid_depth, ask_depth)
    
    def get_best_bid(self) -> Optional[float]:
        """Return best bid price."""
        return max(self.bids.keys()) if self.bids else None
    
    def get_best_ask(self) -> Optional[float]:
        """Return best ask price."""
        return min(self.asks.keys()) if self.asks else None


class OrderBookSimulator:
    """
    Limit order book simulator with realistic microstructure.
    
    Features:
      - N-level order book (bids and asks)
      - Market and limit order execution
      - Spread mean-reversion
      - Liquidity replenishment (Poisson arrivals)
    """
    
    def __init__(
        self,
        mid_price: float = 100.0,
        tick_size: float = 0.01,
        n_levels: int = 10,
        initial_liquidity: int = 1000,
        replenishment_rate: float = 0.5,
    ):
        """
        Initialize order book.
        
        Parameters
        ----------
        mid_price : float
            Initial mid price
        tick_size : float
            Minimum price increment
        n_levels : int
            Number of price levels on each side
        initial_liquidity : int
            Initial volume per level
        replenishment_rate : float
            Liquidity replenishment rate (orders per time step)
        """
        require_positive(mid_price, "mid_price")
        require_positive(tick_size, "tick_size")
        require_positive(n_levels, "n_levels")
        
        self.mid_price = mid_price
        self.tick_size = tick_size
        self.n_levels = n_levels
        self.initial_liquidity = initial_liquidity
        self.replenishment_rate = replenishment_rate
        
        self.bids: dict[float, int] = {}  # {price: volume}
        self.asks: dict[float, int] = {}
        self.time = 0.0
        self.trades: list[Trade] = []
        self.next_order_id = 0
        
        self._initialize_book()
    
    def _initialize_book(self):
        """Create initial order book with symmetric liquidity."""
        # Create bid levels below mid_price
        for i in range(1, self.n_levels + 1):
            price = self.mid_price - i * self.tick_size
            self.bids[round(price, 2)] = self.initial_liquidity
        
        # Create ask levels above mid_price
        for i in range(1, self.n_levels + 1):
            price = self.mid_price + i * self.tick_size
            self.asks[round(price, 2)] = self.initial_liquidity
    
    def get_snapshot(self) -> OrderBookSnapshot:
        """Return current order book state."""
        best_bid = max(self.bids.keys()) if self.bids else self.mid_price
        best_ask = min(self.asks.keys()) if self.asks else self.mid_price
        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        
        bid_depth = sum(self.bids.values())
        ask_depth = sum(self.asks.values())
        
        return OrderBookSnapshot(
            timestamp=self.time,
            bids=self.bids.copy(),
            asks=self.asks.copy(),
            mid_price=mid,
            spread=spread,
            depth=(bid_depth, ask_depth),
        )
    
    def submit_market_order(self, side: str, size: int) -> list[Trade]:
        """
        Execute a market order by walking the book.
        
        Parameters
        ----------
        side : str
            'buy' or 'sell'
        size : int
            Order size (shares)
        
        Returns
        -------
        list[Trade]
            Executed trades
        """
        trades = []
        remaining_size = size
        
        if side == 'buy':
            # Walk the ask side
            sorted_asks = sorted(self.asks.keys())
            for price in sorted_asks:
                if remaining_size == 0:
                    break
                available = self.asks[price]
                fill_size = min(remaining_size, available)
                
                # Execute trade
                trades.append(Trade(
                    timestamp=self.time,
                    price=price,
                    size=fill_size,
                    side='buy',
                ))
                
                # Update book
                self.asks[price] -= fill_size
                if self.asks[price] == 0:
                    del self.asks[price]
                
                remaining_size -= fill_size
        
        else:  # sell
            # Walk the bid side
            sorted_bids = sorted(self.bids.keys(), reverse=True)
            for price in sorted_bids:
                if remaining_size == 0:
                    break
                available = self.bids[price]
                fill_size = min(remaining_size, available)
                
                # Execute trade
                trades.append(Trade(
                    timestamp=self.time,
                    price=price,
                    size=fill_size,
                    side='sell',
                ))
                
                # Update book
                self.bids[price] -= fill_size
                if self.bids[price] == 0:
                    del self.bids[price]
                
                remaining_size -= fill_size
        
        if remaining_size > 0:
            log.warning(f"Market order partially filled: {size - remaining_size}/{size}")
        
        self.trades.extend(trades)
        return trades
    
    def submit_limit_order(self, side: str, price: float, size: int):
        """
        Submit a limit order to the book.
        
        Parameters
        ----------
        side : str
            'buy' or 'sell'
        price : float
            Limit price
        size : int
            Order size
        """
        price = round(price, 2)
        
        if side == 'buy':
            self.bids[price] = self.bids.get(price, 0) + size
        else:
            self.asks[price] = self.asks.get(price, 0) + size
    
    def step(self, dt: float = 1.0):
        """
        Advance simulation by one time step.
        
        Simulates:
          - Liquidity replenishment (random limit orders)
          - Random cancellations
        
        Parameters
        ----------
        dt : float
            Time increment
        """
        self.time += dt
        
        # Replenish liquidity (Poisson arrivals)
        n_arrivals = np.random.poisson(self.replenishment_rate * dt)
        
        for _ in range(n_arrivals):
            side = np.random.choice(['buy', 'sell'])
            
            if side == 'buy':
                # Add to bid side
                best_bid = max(self.bids.keys()) if self.bids else self.mid_price - self.tick_size
                price = best_bid - np.random.randint(0, 3) * self.tick_size
            else:
                # Add to ask side
                best_ask = min(self.asks.keys()) if self.asks else self.mid_price + self.tick_size
                price = best_ask + np.random.randint(0, 3) * self.tick_size
            
            size = np.random.randint(50, 200)
            self.submit_limit_order(side, round(price, 2), size)
    
    def calculate_vwap(self, trades: list[Trade]) -> float:
        """
        Calculate volume-weighted average price of trades.
        
        Parameters
        ----------
        trades : list[Trade]
            List of executed trades
        
        Returns
        -------
        float
            VWAP
        """
        if not trades:
            return 0.0
        
        total_value = sum(t.price * t.size for t in trades)
        total_volume = sum(t.size for t in trades)
        
        return total_value / total_volume if total_volume > 0 else 0.0
    
    def reset(self):
        """Reset order book to initial state."""
        self.bids.clear()
        self.asks.clear()
        self.trades.clear()
        self.time = 0.0
        self.next_order_id = 0
        self._initialize_book()
