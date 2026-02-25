"""
Calibrated Order Book Simulator
Combines real market microstructure data with academically-validated simulation model.
"""

import logging
from typing import Optional, Dict, Tuple
import numpy as np

log = logging.getLogger(__name__)


class MarketMicrostructureData:
    """Real-time market microstructure parameters from Yahoo Finance."""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.is_calibrated = False
        self._fetch_real_data()
    
    def _fetch_real_data(self):
        """Fetch real bid/ask/volume from Yahoo Finance."""
        try:
            import yfinance as yf
            
            ticker_obj = yf.Ticker(self.ticker)
            info = ticker_obj.info
            
            # Real market parameters
            self.current_price = info.get('currentPrice') or info.get('regularMarketPrice', 100.0)
            self.bid = info.get('bid', self.current_price - 0.01)
            self.ask = info.get('ask', self.current_price + 0.01)
            self.spread = self.ask - self.bid
            self.avg_volume = info.get('averageVolume', 1000000)
            self.volume_10d = info.get('averageVolume10days', self.avg_volume)
            
            # Market quality metrics
            self.spread_bps = (self.spread / self.current_price) * 10000
            
            # Liquidity classification
            if self.avg_volume > 10_000_000:
                self.liquidity_tier = "High"  # Large cap
            elif self.avg_volume > 1_000_000:
                self.liquidity_tier = "Medium"  # Mid cap
            else:
                self.liquidity_tier = "Low"  # Small cap
            
            self.is_calibrated = True
            log.info(f"✅ Calibrated {self.ticker}: Spread={self.spread:.4f}, ADV={self.avg_volume:,.0f}")
            
        except Exception as e:
            log.warning(f"⚠️ Could not fetch real data for {self.ticker}: {e}")
            # Fallback to defaults
            self.current_price = 100.0
            self.bid = 99.99
            self.ask = 100.01
            self.spread = 0.02
            self.avg_volume = 1_000_000
            self.volume_10d = 1_000_000
            self.spread_bps = 2.0
            self.liquidity_tier = "Medium"
            self.is_calibrated = False


class CalibratedOrderBookSimulator:
    """
    Order book simulator calibrated to real market microstructure.
    
    Features:
    - Real bid-ask spread from Yahoo Finance
    - Depth scaled to actual average daily volume
    - Exponential decay validated by Cont et al. (2010)
    - Graceful fallback to pure simulation
    
    Parameters
    ----------
    ticker : str
        Stock ticker for calibration
    n_levels : int
        Number of price levels (default: 50)
    use_real_data : bool
        If True, calibrate to real market data (default: True)
    """
    
    def __init__(self, ticker: str = "AAPL", n_levels: int = 50, use_real_data: bool = True):
        self.ticker = ticker.upper()
        self.n_levels = n_levels
        self.use_real_data = use_real_data
        
        # Fetch real market parameters
        if use_real_data:
            self.market_data = MarketMicrostructureData(ticker)
            self.mid_price = self.market_data.current_price
            self.tick_size = max(self.market_data.spread / 4, 0.01)  # Quarter spread or penny
        else:
            self.market_data = None
            self.mid_price = 100.0
            self.tick_size = 0.01
        
        self.bids: Dict[float, int] = {}
        self.asks: Dict[float, int] = {}
        self.reset()
    
    def reset(self):
        """Reset order book to initial calibrated state."""
        self.bids = {}
        self.asks = {}
        self._initialize_book()
    
    def _initialize_book(self):
        """
        Initialize order book with real market calibration.
        
        Model: Exponential depth decay (validated by Bouchaud et al. 2002)
        Depth(level) = base_depth * exp(-decay_rate * level) * noise
        """
        if self.market_data and self.market_data.is_calibrated:
            # ✅ Calibrated to real market
            # Average 5-minute volume (ADV / 78 trading periods per day)
            base_depth = self.market_data.avg_volume / (252 * 78)
            
            # Decay rate based on liquidity tier
            if self.market_data.liquidity_tier == "High":
                decay_rate = 0.03  # Slower decay for liquid stocks
            elif self.market_data.liquidity_tier == "Medium":
                decay_rate = 0.05
            else:
                decay_rate = 0.08  # Faster decay for illiquid stocks
            
            # Use real bid/ask as anchors
            best_bid = self.market_data.bid
            best_ask = self.market_data.ask
            
        else:
            # ⚠️ Fallback to simulation
            base_depth = 1000
            decay_rate = 0.05
            best_bid = self.mid_price - self.tick_size
            best_ask = self.mid_price + self.tick_size
        
        # Build order book levels
        for i in range(self.n_levels):
            # Exponential decay with random noise (±20%)
            depth_factor = np.exp(-decay_rate * i)
            noise = 1 + 0.2 * (np.random.rand() - 0.5)
            
            # Bid side (below best bid)
            bid_price = round(best_bid - i * self.tick_size, 4)
            bid_volume = max(int(base_depth * depth_factor * noise), 100)
            self.bids[bid_price] = bid_volume
            
            # Ask side (above best ask)
            ask_price = round(best_ask + i * self.tick_size, 4)
            ask_volume = max(int(base_depth * depth_factor * noise), 100)
            self.asks[ask_price] = ask_volume
    
    def get_spread(self) -> float:
        """Calculate current bid-ask spread."""
        best_bid = max(self.bids.keys()) if self.bids else 0
        best_ask = min(self.asks.keys()) if self.asks else 0
        return best_ask - best_bid if (best_ask and best_bid) else 0
    
    def get_mid_price(self) -> float:
        """Calculate mid price."""
        best_bid = max(self.bids.keys()) if self.bids else self.mid_price
        best_ask = min(self.asks.keys()) if self.asks else self.mid_price
        return (best_bid + best_ask) / 2 if (best_bid and best_ask) else self.mid_price
    
    def get_imbalance(self) -> float:
        """
        Calculate order book imbalance.
        
        Returns
        -------
        float
            Imbalance in [-1, 1] where positive = more bids
        """
        total_bid = sum(self.bids.values())
        total_ask = sum(self.asks.values())
        return (total_bid - total_ask) / (total_bid + total_ask + 1e-10)
    
    def get_depth(self, levels: int = 10) -> Tuple[list, list]:
        """
        Get top N levels of depth.
        
        Returns
        -------
        tuple
            (sorted_bids, sorted_asks) as [(price, volume), ...]
        """
        sorted_bids = sorted(self.bids.items(), reverse=True)[:levels]
        sorted_asks = sorted(self.asks.items())[:levels]
        return sorted_bids, sorted_asks
    
    def simulate_market_order(self, side: str, volume: int) -> Tuple[int, float]:
        """
        Simulate market order execution.
        
        Parameters
        ----------
        side : str
            'buy' or 'sell'
        volume : int
            Order size in shares
        
        Returns
        -------
        tuple
            (executed_volume, average_price)
        """
        executed = 0
        total_cost = 0.0
        
        if side.lower() == 'buy':
            # Execute against asks
            sorted_asks = sorted(self.asks.items())
            for price, available in sorted_asks:
                if executed >= volume:
                    break
                execute_qty = min(available, volume - executed)
                total_cost += price * execute_qty
                executed += execute_qty
                
                # Update order book
                self.asks[price] -= execute_qty
                if self.asks[price] <= 0:
                    del self.asks[price]
        
        else:  # sell
            # Execute against bids
            sorted_bids = sorted(self.bids.items(), reverse=True)
            for price, available in sorted_bids:
                if executed >= volume:
                    break
                execute_qty = min(available, volume - executed)
                total_cost += price * execute_qty
                executed += execute_qty
                
                # Update order book
                self.bids[price] -= execute_qty
                if self.bids[price] <= 0:
                    del self.bids[price]
        
        avg_price = total_cost / executed if executed > 0 else self.get_mid_price()
        return executed, avg_price
    
    def apply_liquidity_shock(self, intensity: float = 0.5):
        """
        Simulate liquidity withdrawal (flash crash scenario).
        
        Parameters
        ----------
        intensity : float
            Shock intensity in [0, 1]
        """
        for price in list(self.bids.keys()):
            if np.random.rand() < intensity:
                reduction = 1 - intensity * 0.8
                self.bids[price] = int(self.bids[price] * reduction)
                if self.bids[price] <= 0:
                    del self.bids[price]
        
        for price in list(self.asks.keys()):
            if np.random.rand() < intensity:
                reduction = 1 - intensity * 0.8
                self.asks[price] = int(self.asks[price] * reduction)
                if self.asks[price] <= 0:
                    del self.asks[price]
    
    def get_calibration_info(self) -> Dict:
        """Get calibration metadata for transparency."""
        if self.market_data and self.market_data.is_calibrated:
            return {
                'ticker': self.ticker,
                'is_calibrated': True,
                'mid_price': self.market_data.current_price,
                'real_bid': self.market_data.bid,
                'real_ask': self.market_data.ask,
                'real_spread': self.market_data.spread,
                'spread_bps': self.market_data.spread_bps,
                'avg_volume': self.market_data.avg_volume,
                'liquidity_tier': self.market_data.liquidity_tier,
            }
        else:
            return {
                'ticker': self.ticker,
                'is_calibrated': False,
                'note': 'Using default simulation parameters'
            }
