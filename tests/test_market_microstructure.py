"""Tests for calibrated order book simulator."""

import pytest
import numpy as np
from quantlib_pro.market_microstructure import CalibratedOrderBookSimulator


class TestCalibratedOrderBook:
    """Test calibrated order book functionality."""
    
    def test_initialization_with_real_data(self):
        """Test initialization with real market data."""
        ob = CalibratedOrderBookSimulator(ticker="AAPL", use_real_data=True)
        
        assert ob.ticker == "AAPL"
        assert ob.bids
        assert ob.asks
        assert ob.get_spread() > 0
    
    def test_initialization_without_real_data(self):
        """Test fallback to simulation."""
        ob = CalibratedOrderBookSimulator(ticker="AAPL", use_real_data=False)
        
        assert ob.market_data is None
        assert ob.bids
        assert ob.asks
    
    def test_calibration_info(self):
        """Test calibration metadata."""
        ob = CalibratedOrderBookSimulator(ticker="AAPL", use_real_data=True)
        info = ob.get_calibration_info()
        
        assert 'ticker' in info
        assert 'is_calibrated' in info
        
        if info['is_calibrated']:
            assert 'real_spread' in info
            assert 'avg_volume' in info
    
    def test_market_order_execution(self):
        """Test market order simulation."""
        ob = CalibratedOrderBookSimulator(ticker="SPY", use_real_data=False)
        
        initial_bids = len(ob.bids)
        executed, avg_price = ob.simulate_market_order('sell', 1000)
        
        assert executed == 1000
        assert avg_price > 0
        assert len(ob.bids) <= initial_bids  # Some levels consumed
    
    def test_liquidity_shock(self):
        """Test liquidity shock scenario."""
        ob = CalibratedOrderBookSimulator(ticker="AAPL", use_real_data=False)
        
        initial_total_bids = sum(ob.bids.values())
        ob.apply_liquidity_shock(intensity=0.5)
        shocked_total_bids = sum(ob.bids.values())
        
        assert shocked_total_bids < initial_total_bids  # Liquidity reduced
    
    def test_spread_calculation(self):
        """Test spread calculation."""
        ob = CalibratedOrderBookSimulator(ticker="MSFT", use_real_data=False)
        spread = ob.get_spread()
        
        assert spread > 0
        assert isinstance(spread, float)
    
    def test_order_book_imbalance(self):
        """Test imbalance metric."""
        ob = CalibratedOrderBookSimulator(ticker="GOOGL", use_real_data=False)
        imbalance = ob.get_imbalance()
        
        assert -1 <= imbalance <= 1
    
    def test_reset_functionality(self):
        """Test order book reset."""
        ob = CalibratedOrderBookSimulator(ticker="NVDA", use_real_data=False)
        
        # Execute some orders
        ob.simulate_market_order('buy', 500)
        
        # Reset
        ob.reset()
        
        # Verify book is repopulated
        assert len(ob.bids) > 0
        assert len(ob.asks) > 0
    
    def test_get_depth(self):
        """Test depth retrieval."""
        ob = CalibratedOrderBookSimulator(ticker="TSLA", use_real_data=False)
        bids, asks = ob.get_depth(levels=10)
        
        assert len(bids) <= 10
        assert len(asks) <= 10
        assert all(isinstance(item, tuple) for item in bids)
        assert all(isinstance(item, tuple) for item in asks)
    
    def test_mid_price_calculation(self):
        """Test mid price calculation."""
        ob = CalibratedOrderBookSimulator(ticker="META", use_real_data=False)
        mid_price = ob.get_mid_price()
        
        assert mid_price > 0
        assert isinstance(mid_price, float)
