"""
Test suite for Brownian Motion implementation.

Validates mathematical properties and numerical accuracy.
"""

import numpy as np
import pytest
from scipy import stats

from gaussian_cookbook.processes import BrownianMotion


class TestBrownianMotionProperties:
    """Test mathematical properties of Brownian Motion."""
    
    @pytest.fixture
    def bm(self):
        """Standard Brownian motion for testing."""
        return BrownianMotion(random_state=42)
    
    def test_initial_value_zero(self, bm):
        """Test B(0) = 0 almost surely."""
        times = np.linspace(0, 1, 100)
        result = bm.sample(times, n_paths=100)
        
        # All paths should start at 0
        assert np.allclose(result.paths[:, 0], 0.0)
    
    def test_gaussian_increments(self, bm):
        """Test that increments B(t) - B(s) are Gaussian."""
        times = np.linspace(0, 1, 50)
        result = bm.sample(times, n_paths=1000)
        
        # Test several increment distributions
        for i in [10, 20, 30]:
            increments = result.paths[:, i+1] - result.paths[:, i]
            dt = times[i+1] - times[i]
            
            # Kolmogorov-Smirnov test for normality
            statistic, p_value = stats.kstest(
                increments, 
                lambda x: stats.norm.cdf(x, 0, np.sqrt(dt))
            )
            
            assert p_value > 0.01, f"Increments at step {i} not Gaussian (p={p_value:.4f})"
    
    def test_independent_increments(self, bm):
        """Test independence of non-overlapping increments."""
        times = np.linspace(0, 1, 101)  # 100 increments
        result = bm.sample(times, n_paths=2000)
        
        # Test correlation between non-overlapping increments
        inc1 = result.paths[:, 25] - result.paths[:, 0]   # B(0.25) - B(0)
        inc2 = result.paths[:, 75] - result.paths[:, 50]  # B(0.75) - B(0.5)
        
        correlation = np.corrcoef(inc1, inc2)[0, 1]
        
        # Should be approximately uncorrelated (within sampling error)
        assert abs(correlation) < 0.1, f"Non-overlapping increments correlated: r={correlation:.4f}"
    
    def test_covariance_structure(self, bm):
        """Test theoretical covariance Cov(B(s), B(t)) = min(s,t)."""
        times = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        result = bm.sample(times, n_paths=5000)
        
        empirical_cov = np.cov(result.paths.T)
        theoretical_cov = bm.theoretical_covariance_matrix(times)
        
        # Relative error should be small
        relative_error = np.abs(empirical_cov - theoretical_cov) / (np.abs(theoretical_cov) + 1e-8)
        max_error = np.max(relative_error)
        
        assert max_error < 0.1, f"Covariance structure error too large: {max_error:.4f}"
    
    def test_quadratic_variation_convergence(self, bm):
        """Test [B,B]_t → t as partition becomes finer."""
        
        for n in [100, 200, 400]:
            times = np.linspace(0, 1, n+1)
            result = bm.sample(times, n_paths=500)
            
            # Compute quadratic variation
            qv = np.sum(np.diff(result.paths, axis=1)**2, axis=1)
            
            # Should converge to T=1 in probability
            mean_qv = np.mean(qv)
            assert abs(mean_qv - 1.0) < 0.15, f"Quadratic variation convergence failed at n={n}: {mean_qv:.4f}"
    
    def test_continuous_decomposition_method(self, bm):
        """Test continuous decomposition method produces correct distribution."""
        times = np.linspace(0, 1, 20)
        
        # Compare two methods
        result_inc = bm.sample(times, n_paths=1000, method='increments')
        result_cont = bm.sample(times, n_paths=1000, method='continuous_decomposition')
        
        # Final values should have same distribution
        final_inc = result_inc.paths[:, -1]
        final_cont = result_cont.paths[:, -1]
        
        # Two-sample Kolmogorov-Smirnov test
        statistic, p_value = stats.ks_2samp(final_inc, final_cont)
        
        assert p_value > 0.05, f"Different methods produce different distributions (p={p_value:.4f})"


class TestBrownianMotionNumerical:
    """Test numerical accuracy and edge cases."""
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters
        bm = BrownianMotion(drift=0.1, volatility=2.0)
        assert bm.validate_parameters()
        
        # Invalid volatility
        with pytest.raises(ValueError):
            BrownianMotion(volatility=-1.0)
        
        with pytest.raises(ValueError):
            BrownianMotion(volatility=0.0)
    
    def test_drift_and_volatility(self):
        """Test drift and volatility parameters."""
        drift = 0.05
        volatility = 1.5
        bm = BrownianMotion(drift=drift, volatility=volatility, random_state=42)
        
        times = np.linspace(0, 2, 1000)
        result = bm.sample(times, n_paths=2000)
        
        # Check final mean (should be approximately drift * T)
        final_mean = np.mean(result.paths[:, -1])
        expected_mean = drift * times[-1]
        
        assert abs(final_mean - expected_mean) < 0.1, \
            f"Drift incorrect: got {final_mean:.4f}, expected {expected_mean:.4f}"
        
        # Check final variance (should be approximately volatility² * T)  
        final_var = np.var(result.paths[:, -1])
        expected_var = volatility**2 * times[-1]
        
        assert abs(final_var - expected_var) < 0.2, \
            f"Volatility incorrect: got {final_var:.4f}, expected {expected_var:.4f}"
    
    def test_reproducibility(self):
        """Test random seed reproducibility."""
        times = np.linspace(0, 1, 50)
        
        bm1 = BrownianMotion(random_state=123)
        bm2 = BrownianMotion(random_state=123)
        
        result1 = bm1.sample(times, n_paths=10)
        result2 = bm2.sample(times, n_paths=10)
        
        np.testing.assert_array_equal(result1.paths, result2.paths)
    
    def test_time_validation(self):
        """Test time array validation."""
        bm = BrownianMotion()
        
        # Should raise error if doesn't start at 0
        with pytest.raises(ValueError):
            bm.sample(np.linspace(0.1, 1, 10))
    
    @pytest.mark.parametrize("method", ['increments', 'continuous_decomposition'])
    def test_simulation_methods(self, method):
        """Test both simulation methods work correctly."""
        bm = BrownianMotion(random_state=42)
        times = np.linspace(0, 1, 100)
        
        result = bm.sample(times, n_paths=50, method=method)
        
        assert result.paths.shape == (50, 100)
        assert result.method == method
        assert np.allclose(result.paths[:, 0], 0.0)  # Starts at 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])