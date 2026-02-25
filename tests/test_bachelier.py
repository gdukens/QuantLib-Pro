"""
Unit Tests for Bachelier Option Pricing Model
==============================================

Tests the implementation of the Bachelier (1900) model against:
1. Known analytical results
2. Put-call parity
3. Boundary conditions
4. Greeks calculations
5. Monte Carlo simulation convergence

Author: QuantLib Pro
Date: February 24, 2026
"""

import pytest
import numpy as np
from scipy.stats import norm

from quantlib_pro.options.bachelier import (
    BachelierModel,
    BachelierParams,
    bachelier_call,
    bachelier_put,
)


class TestBachelierParams:
    """Test parameter validation."""
    
    def test_valid_params(self):
        """Test valid parameter initialization."""
        params = BachelierParams(sigma=20.0)
        assert params.sigma == 20.0
    
    def test_negative_sigma(self):
        """Test that negative sigma raises error."""
        with pytest.raises(ValueError, match="Sigma must be positive"):
            BachelierParams(sigma=-5.0)
    
    def test_zero_sigma(self):
        """Test that zero sigma raises error."""
        with pytest.raises(ValueError, match="Sigma must be positive"):
            BachelierParams(sigma=0.0)
    
    def test_nan_sigma(self):
        """Test that NaN sigma raises error."""
        with pytest.raises(ValueError, match="Sigma must be finite"):
            BachelierParams(sigma=np.nan)
    
    def test_inf_sigma(self):
        """Test that infinite sigma raises error."""
        with pytest.raises(ValueError, match="Sigma must be finite"):
            BachelierParams(sigma=np.inf)


class TestBachelierPricing:
    """Test option pricing formulas."""
    
    def test_atm_call_put_equivalence(self):
        """Test that ATM call and put have same price."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 100, 1.0
        
        call = model.price(F0, K, T, 'call')
        put = model.price(F0, K, T, 'put')
        
        assert abs(call - put) < 1e-10
    
    def test_known_atm_price(self):
        """Test against known ATM price."""
        # For ATM: C = σ√T × φ(0) = σ√T / √(2π)
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 100, 1.0
        
        expected = 20.0 * np.sqrt(1.0) / np.sqrt(2 * np.pi)
        actual = model.price(F0, K, T, 'call')
        
        assert abs(actual - expected) < 1e-10
    
    def test_put_call_parity_general(self):
        """Test put-call parity for general strikes."""
        model = BachelierModel(sigma=20.0)
        F0, T = 100, 1.0
        
        for K in [80, 90, 100, 110, 120]:
            call = model.price(F0, K, T, 'call')
            put = model.price(F0, K, T, 'put')
            
            # For Bachelier: C - P = F - K
            parity_lhs = call - put
            parity_rhs = F0 - K
            
            assert abs(parity_lhs- parity_rhs) < 1e-10, f"Failed for K={K}"
    
    def test_deep_itm_call(self):
        """Test deep ITM call approximates intrinsic value."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 150, 100, 1.0
        
        call = model.price(F0, K, T, 'call')
        intrinsic = F0 - K
        
        # Deep ITM should be close to intrinsic
        assert call > intrinsic
        assert call < intrinsic + 10  # Time value should be small relative to moneyness
    
    def test_deep_otm_call(self):
        """Test deep OTM call is close to zero."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 200, 1.0
        
        call = model.price(F0, K, T, 'call')
        
        assert call > 0
        assert call < 1.0  # Very small for this moneyness
    
    def test_expiry_convergence_call(self):
        """Test that price converges to intrinsic at expiry."""
        model = BachelierModel(sigma=20.0)
        F0, K = 105, 100
        
        # As T → 0, price should approach max(F-K, 0)
        price_at_expiry = model.price(F0, K, 1e-10, 'call')
        intrinsic = max(F0 - K, 0)
        
        assert abs(price_at_expiry - intrinsic) < 1e-8
    
    def test_convenience_functions(self):
        """Test quick pricing functions."""
        F0, K, T, sigma = 100, 100, 1.0, 20.0
        
        model = BachelierModel(sigma=sigma)
        call_model = model.price(F0, K, T, 'call')
        put_model = model.price(F0, K, T, 'put')
        
        call_func = bachelier_call(F0, K, T, sigma)
        put_func = bachelier_put(F0, K, T, sigma)
        
        assert abs(call_model - call_func) < 1e-10
        assert abs(put_model - put_func) < 1e-10


class TestBachelierGreeks:
    """Test Greeks calculations."""
    
    def test_call_delta_range(self):
        """Test call delta is in [0, 1]."""
        model = BachelierModel(sigma=20.0)
        F0, T = 100, 1.0
        
        for K in [80, 90, 100, 110, 120]:
            delta = model.delta(F0, K, T, 'call')
            assert 0 <= delta <= 1, f"Delta out of range for K={K}"
    
    def test_put_delta_range(self):
        """Test put delta is in [-1, 0]."""
        model = BachelierModel(sigma=20.0)
        F0, T = 100, 1.0
        
        for K in [80, 90, 100, 110, 120]:
            delta = model.delta(F0, K, T, 'put')
            assert -1 <= delta <= 0, f"Delta out of range for K={K}"
    
    def test_delta_put_call_relation(self):
        """Test that put_delta = call_delta - 1."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 105, 1.0
        
        call_delta = model.delta(F0, K, T, 'call')
        put_delta = model.delta(F0, K, T, 'put')
        
        assert abs(put_delta - (call_delta - 1)) < 1e-10
    
    def test_atm_delta(self):
        """Test ATM delta is 0.5 for calls."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 100, 1.0
        
        delta = model.delta(F0, K, T, 'call')
        
        assert abs(delta - 0.5) < 1e-10
    
    def test_gamma_positive(self):
        """Test gamma is always positive."""
        model = BachelierModel(sigma=20.0)
        F0, T = 100, 1.0
        
        for K in [80, 90, 100, 110, 120]:
            gamma = model.gamma(F0, K, T)
            assert gamma > 0, f"Gamma not positive for K={K}"
    
    def test_gamma_symmetric(self):
        """Test gamma is symmetric around ATM."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 100, 1.0
        
        gamma_atm = model.gamma(F0, K, T)
        gamma_below = model.gamma(F0, K - 10, T)
        gamma_above = model.gamma(F0, K + 10, T)
        
        # Gamma should be lower on both sides
        assert gamma_below < gamma_atm
        assert gamma_above < gamma_atm
    
    def test_vega_positive(self):
        """Test vega is always positive."""
        model = BachelierModel(sigma=20.0)
        F0, T = 100, 1.0
        
        for K in [80, 90, 100, 110, 120]:
            vega = model.vega(F0, K, T)
            assert vega > 0, f"Vega not positive for K={K}"
    
    def test_theta_negative(self):
        """Test theta is negative (time decay)."""
        model = BachelierModel(sigma=20.0)
        F0, T = 100, 1.0
        
        for K in [90, 100, 110]:
            theta_call = model.theta(F0, K, T, 'call')
            theta_put = model.theta(F0, K, T, 'put')
            
            assert theta_call < 0, f"Call theta not negative for K={K}"
            assert theta_put < 0, f"Put theta not negative for K={K}"
    
    def test_delta_by_finite_difference(self):
        """Test delta against finite difference approximation."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 100, 1.0
        
        delta_analytical = model.delta(F0, K, T, 'call')
        
        # Finite difference
        h = 0.01
        price_up = model.price(F0 + h, K, T, 'call')
        price_down = model.price(F0 - h, K, T, 'call')
        delta_fd = (price_up - price_down) / (2 * h)
        
        assert abs(delta_analytical - delta_fd) < 1e-6
    
    def test_gamma_by_finite_difference(self):
        """Test gamma against finite difference approximation."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 100, 1.0
        
        gamma_analytical = model.gamma(F0, K, T)
        
        # Finite difference
        h = 0.01
        delta_up = model.delta(F0 + h, K, T, 'call')
        delta_down = model.delta(F0 - h, K, T, 'call')
        gamma_fd = (delta_up - delta_down) / (2 * h)
        
        assert abs(gamma_analytical - gamma_fd) < 1e-4


class TestBachelierSimulation:
    """Test Monte Carlo simulation."""
    
    def test_simulation_mean(self):
        """Test that simulated paths have correct mean."""
        model = BachelierModel(sigma=20.0)
        F0 = 100
        paths = model.simulate(F0, n_paths=10000, n_steps=100, T=1.0, seed=42)
        
        terminal_values = [path[-1] for path in paths]
        mean_terminal = np.mean(terminal_values)
        
        # ABM has no drift, so mean should be F0
        assert abs(mean_terminal - F0) < 1.0  # Within 1 due to sampling error
    
    def test_simulation_std(self):
        """Test that simulated paths have correct std dev."""
        model = BachelierModel(sigma=20.0)
        F0 = 100
        T = 1.0
        paths = model.simulate(F0, n_paths=10000, n_steps=100, T=T, seed=42)
        
        terminal_values = [path[-1] for path in paths]
        std_terminal = np.std(terminal_values, ddof=1)
        
        # ABM: std = σ√T
        expected_std = model.sigma * np.sqrt(T)
        
        assert abs(std_terminal - expected_std) < 1.0  # Within 1 due to sampling error
    
    def test_vectorized_simulation_shape(self):
        """Test vectorized simulation returns correct shape."""
        model = BachelierModel(sigma=20.0)
        paths = model.simulate_vectorized(100, n_paths=1000, n_steps=252, T=1.0, seed=42)
        
        assert paths.shape == (1000, 253)  # 252 steps + initial point
    
    def test_vectorized_vs_loop_simulation(self):
        """Test vectorized and loop simulations give similar results."""
        model = BachelierModel(sigma=20.0)
        F0, n_paths, n_steps, T = 100, 1000, 100, 1.0
        
        # Loop version
        paths_loop = model.simulate(F0, n_paths, n_steps, T, seed=42)
        mean_loop = np.mean([p[-1] for p in paths_loop])
        
        # Vectorized version
        paths_vec = model.simulate_vectorized(F0, n_paths, n_steps, T, seed=42)
        mean_vec = np.mean(paths_vec[:, -1])
        
        # Should be identical with same seed
        assert abs(mean_loop - mean_vec) < 1e-10
    
    def test_monte_carlo_option_pricing(self):
        """Test option pricing via Monte Carlo converges to analytical."""
        model = BachelierModel(sigma=20.0)
        F0, K, T = 100, 100, 1.0
        
        # Analytical price
        analytical = model.price(F0, K, T, 'call')
        
        # Monte Carlo price
        paths = model.simulate_vectorized(F0, n_paths=50000, n_steps=1, T=T, seed=42)
        terminal = paths[:, -1]
        payoffs = np.maximum(terminal - K, 0)
        mc_price = np.mean(payoffs)
        
        # Should be close (within 2% due to MC error)
        relative_error = abs(mc_price - analytical) / analytical
        assert relative_error < 0.02


class TestBachelierImpliedVol:
    """Test implied volatility calculation."""
    
    def test_implied_vol_recovery(self):
        """Test that we can recover sigma from price."""
        sigma_true = 20.0
        model = BachelierModel(sigma=sigma_true)
        F0, K, T = 100, 100, 1.0
        
        # Get theoretical price
        price = model.price(F0, K, T, 'call')
        
        # Recover implied vol
        sigma_implied = model.implied_volatility(price, F0, K, T, 'call')
        
        assert abs(sigma_implied - sigma_true) < 1e-6
    
    def test_implied_vol_multiple_strikes(self):
        """Test implied vol for various strikes."""
        sigma_true = 25.0
        model = BachelierModel(sigma=sigma_true)
        F0, T = 100, 1.0
        
        for K in [90, 95, 100, 105, 110]:
            price = model.price(F0, K, T, 'call')
            sigma_implied = model.implied_volatility(price, F0, K, T, 'call')
            
            assert abs(sigma_implied - sigma_true) < 1e-5, f"Failed for K={K}"


class TestInputValidation:
    """Test input validation."""
    
    def test_negative_forward_price(self):
        """Test that negative forward raises error."""
        model = BachelierModel(sigma=20.0)
        
        with pytest.raises(ValueError, match="Forward price F0 must be positive"):
            model.price(F0=-100, K=100, T=1.0)
    
    def test_negative_strike(self):
        """Test that negative strike raises error."""
        model = BachelierModel(sigma=20.0)
        
        with pytest.raises(ValueError, match="Strike K must be positive"):
            model.price(F0=100, K=-100, T=1.0)
    
    def test_negative_time(self):
        """Test that negative time raises error."""
        model = BachelierModel(sigma=20.0)
        
        with pytest.raises(ValueError, match="Time to maturity T must be positive"):
            model.price(F0=100, K=100, T=-1.0)
    
    def test_invalid_option_type(self):
        """Test that invalid option type raises error."""
        model = BachelierModel(sigma=20.0)
        
        with pytest.raises(ValueError, match="option_type must be 'call' or 'put'"):
            model.price(F0=100, K=100, T=1.0, option_type='invalid')


class TestModelRepresentation:
    """Test string representations."""
    
    def test_repr(self):
        """Test __repr__ method."""
        model = BachelierModel(sigma=20.0)
        repr_str = repr(model)
        
        assert "BachelierModel" in repr_str
        assert "20" in repr_str
    
    def test_str(self):
        """Test __str__ method."""
        model = BachelierModel(sigma=20.0)
        str_repr = str(model)
        
        assert "Bachelier" in str_repr
        assert "20.0000" in str_repr
        assert "dF = σ dW" in str_repr


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
