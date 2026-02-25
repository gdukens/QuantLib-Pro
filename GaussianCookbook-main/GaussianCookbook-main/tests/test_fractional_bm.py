"""
Comprehensive test suite for Fractional Brownian Motion.

Tests mathematical properties, numerical accuracy, and multiple algorithms.
"""

import numpy as np
import pytest
from scipy import stats

from gaussian_cookbook.processes import FractionalBrownianMotion, FBMMethod


class TestFractionalBrownianMotionProperties:
    """Test mathematical properties of fBM."""
    
    @pytest.fixture
    def fbm_persistent(self):
        """Persistent fBM (H > 0.5) for testing."""
        return FractionalBrownianMotion(hurst=0.7, random_state=42)
    
    @pytest.fixture  
    def fbm_antipersistent(self):
        """Anti-persistent fBM (H < 0.5) for testing.""" 
        return FractionalBrownianMotion(hurst=0.3, random_state=42)
    
    @pytest.fixture
    def fbm_brownian(self):
        """Standard Brownian motion (H = 0.5) for comparison."""
        return FractionalBrownianMotion(hurst=0.5, random_state=42)
    
    def test_initial_value_zero(self, fbm_persistent):
        """Test B_H(0) = 0 almost surely."""
        times = np.linspace(0, 1, 50)
        result = fbm_persistent.sample(times, n_paths=100)
        
        assert np.allclose(result.paths[:, 0], 0.0)
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters
        fbm = FractionalBrownianMotion(hurst=0.75, volatility=1.5)
        assert fbm.validate_parameters()
        
        # Invalid Hurst parameters
        with pytest.raises(ValueError):
            FractionalBrownianMotion(hurst=0.0)
            
        with pytest.raises(ValueError):
            FractionalBrownianMotion(hurst=1.0)
            
        with pytest.raises(ValueError):
            FractionalBrownianMotion(hurst=-0.1)
            
        with pytest.raises(ValueError):
            FractionalBrownianMotion(hurst=1.5)
        
        # Invalid volatility
        with pytest.raises(ValueError):
            FractionalBrownianMotion(hurst=0.6, volatility=0.0)
            
        with pytest.raises(ValueError):
            FractionalBrownianMotion(hurst=0.6, volatility=-1.0)
    
    def test_covariance_structure(self, fbm_persistent):
        """Test theoretical covariance structure."""
        times = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        result = fbm_persistent.sample(times, n_paths=2000)
        
        empirical_cov = np.cov(result.paths.T)
        theoretical_cov = fbm_persistent.theoretical_covariance_matrix(times)
        
        # Relative error should be reasonable for Monte Carlo
        relative_error = np.abs(empirical_cov - theoretical_cov) / (np.abs(theoretical_cov) + 1e-8)
        max_error = np.max(relative_error)
        
        assert max_error < 0.2, f"Covariance error too large: {max_error:.4f}"
    
    def test_self_similarity_property(self, fbm_persistent):
        """Test self-similarity: B_H(ct) =^d c^H B_H(t)."""
        H = fbm_persistent.hurst
        c = 2.0
        times = np.linspace(0, 1, 20)
        
        # Generate B_H(t)
        result1 = fbm_persistent.sample(times, n_paths=500)
        
        # Generate B_H(ct) rescaled by c^(-H) 
        scaled_times = c * times
        result2 = fbm_persistent.sample(scaled_times, n_paths=500)
        scaled_paths = result2.paths / (c**H)
        
        # Compare final value distributions
        final1 = result1.paths[:, -1]
        final2 = scaled_paths[:, -1]
        
        # Kolmogorov-Smirnov test for distributional equality
        statistic, p_value = stats.ks_2samp(final1, final2)
        
        assert p_value > 0.01, f"Self-similarity test failed (p={p_value:.4f})"
    
    def test_stationary_increments(self, fbm_persistent):
        """Test that increments are stationary."""
        times = np.linspace(0, 2, 100)  # Longer time series
        result = fbm_persistent.sample(times, n_paths=200)
        
        dt = times[1] - times[0]
        
        # Compare increments from different time periods
        increments1 = result.paths[:, 25:35] - result.paths[:, 24:34]  # Early increments
        increments2 = result.paths[:, 75:85] - result.paths[:, 74:84]  # Later increments
        
        # Flatten for comparison
        inc1_flat = increments1.flatten()
        inc2_flat = increments2.flatten()
        
        # Two-sample test for equal distributions
        statistic, p_value = stats.ks_2samp(inc1_flat, inc2_flat)
        
        assert p_value > 0.01, f"Stationarity of increments test failed (p={p_value:.4f})"
    
    def test_gaussian_increments(self, fbm_persistent):
        """Test that increments are Gaussian distributed."""
        times = np.linspace(0, 1, 50)
        result = fbm_persistent.sample(times, n_paths=1000)
        
        # Test several increment sets
        for i in [10, 20, 30]:
            increments = result.paths[:, i+1] - result.paths[:, i]
            
            # Theoretical variance for this increment
            dt = times[i+1] - times[i]
            expected_var = fbm_persistent.increments_variance(dt)
            
            # Normalize increments 
            normalized = increments / np.sqrt(expected_var)
            
            # Shapiro-Wilk test for normality
            statistic, p_value = stats.shapiro(normalized[:100])  # Subset for speed
            
            assert p_value > 0.01, f"Increments at step {i} not Gaussian (p={p_value:.4f})"
    
    @pytest.mark.parametrize("hurst", [0.2, 0.5, 0.8])
    def test_variance_scaling(self, hurst):
        """Test variance scaling: Var[B_H(t)] = σ²t^{2H}."""
        fbm = FractionalBrownianMotion(hurst=hurst, volatility=1.5, random_state=42)
        
        test_times = [0.25, 0.5, 0.75, 1.0]
        
        for t in test_times:
            times = np.linspace(0, t, int(50*t) + 1)
            result = fbm.sample(times, n_paths=2000)
            
            empirical_var = np.var(result.paths[:, -1])
            theoretical_var = fbm.variance_at_time(t)
            
            relative_error = abs(empirical_var - theoretical_var) / theoretical_var
            
            assert relative_error < 0.15, \
                f"Variance scaling failed at t={t}, H={hurst}: {relative_error:.4f}"
    
    def test_long_range_dependence(self, fbm_persistent):
        """Test long-range dependence for H > 0.5."""
        assert fbm_persistent.is_persistent()
        assert not fbm_persistent.is_antipersistent()
        assert fbm_persistent.long_range_dependence_parameter() > 0
    
    def test_anti_persistence(self, fbm_antipersistent):
        """Test anti-persistence for H < 0.5."""
        assert fbm_antipersistent.is_antipersistent()
        assert not fbm_antipersistent.is_persistent()
        assert fbm_antipersistent.long_range_dependence_parameter() < 0


class TestFractionalBrownianMotionMethods:
    """Test different simulation algorithms."""
    
    @pytest.fixture
    def fbm(self):
        """Standard fBM for testing."""
        return FractionalBrownianMotion(hurst=0.6, random_state=42)
    
    def test_davies_harte_method(self, fbm):
        """Test Davies-Harte algorithm.""" 
        times = np.linspace(0, 1, 65)  # Power of 2 + 1 for efficiency
        result = fbm.sample(times, n_paths=10, method=FBMMethod.DAVIES_HARTE)
        
        assert result.method == 'davies_harte'
        assert result.paths.shape == (10, 65)
        assert np.allclose(result.paths[:, 0], 0.0)
    
    def test_cholesky_method(self, fbm):
        """Test Cholesky decomposition method."""
        times = np.linspace(0, 1, 20)  # Smaller size for O(n³) method
        result = fbm.sample(times, n_paths=5, method=FBMMethod.CHOLESKY)
        
        assert result.method == 'cholesky'
        assert result.paths.shape == (5, 20)
        assert np.allclose(result.paths[:, 0], 0.0)
    
    def test_method_comparison(self, fbm):
        """Compare Davies-Harte vs Cholesky methods."""
        times = np.linspace(0, 1, 33)  # Size that works for both methods
        
        result_dh = fbm.sample(times, n_paths=500, method=FBMMethod.DAVIES_HARTE)
        result_chol = fbm.sample(times, n_paths=500, method=FBMMethod.CHOLESKY)
        
        # Compare final value distributions
        final_dh = result_dh.paths[:, -1]
        final_chol = result_chol.paths[:, -1]
        
        # Should have similar distributions
        statistic, p_value = stats.ks_2samp(final_dh, final_chol)
        
        assert p_value > 0.01, f"Methods produce different distributions (p={p_value:.4f})"
    
    def test_time_validation(self, fbm):
        """Test time array validation."""
        # Non-zero start
        with pytest.raises(ValueError):
            fbm.sample(np.linspace(0.1, 1, 10))
        
        # Unequally spaced (for Davies-Harte)
        unequal_times = np.array([0, 0.1, 0.3, 0.7, 1.0])
        with pytest.raises(ValueError):
            fbm.sample(unequal_times, method=FBMMethod.DAVIES_HARTE)
        
        # Should work with Cholesky
        result = fbm.sample(unequal_times, method=FBMMethod.CHOLESKY)
        assert result.paths.shape[1] == len(unequal_times)
    
    def test_reproducibility(self, fbm):
        """Test random seed reproducibility."""
        times = np.linspace(0, 1, 20)
        
        result1 = fbm.sample(times, n_paths=10, method=FBMMethod.DAVIES_HARTE)
        
        # Reset random state
        fbm._rng = np.random.RandomState(42)
        result2 = fbm.sample(times, n_paths=10, method=FBMMethod.DAVIES_HARTE)
        
        np.testing.assert_array_equal(result1.paths, result2.paths)


class TestFractionalBrownianMotionEdgeCases:
    """Test edge cases and numerical stability."""
    
    def test_extreme_hurst_values(self):
        """Test behavior near Hurst parameter boundaries."""
        # Very close to 0
        fbm_low = FractionalBrownianMotion(hurst=0.02, random_state=42)
        times = np.linspace(0, 1, 20)
        result_low = fbm_low.sample(times, n_paths=10)
        assert not np.any(np.isnan(result_low.paths))
        
        # Very close to 1
        fbm_high = FractionalBrownianMotion(hurst=0.98, random_state=42)
        result_high = fbm_high.sample(times, n_paths=10)
        assert not np.any(np.isnan(result_high.paths))
    
    def test_large_time_horizon(self):
        """Test simulation over large time horizons."""
        fbm = FractionalBrownianMotion(hurst=0.7, random_state=42)
        times = np.linspace(0, 100, 200)
        
        result = fbm.sample(times, n_paths=5)
        
        # Should scale properly
        final_var_empirical = np.var(result.paths[:, -1])
        final_var_theoretical = fbm.variance_at_time(100)
        
        relative_error = abs(final_var_empirical - final_var_theoretical) / final_var_theoretical
        
        # Allow larger tolerance for extreme case
        assert relative_error < 0.5
    
    def test_single_time_point(self):
        """Test with minimal time array."""
        fbm = FractionalBrownianMotion(hurst=0.6, random_state=42)
        times = np.array([0.0])
        
        result = fbm.sample(times, n_paths=10)
        
        assert result.paths.shape == (10, 1)
        assert np.allclose(result.paths, 0.0)
    
    def test_fgn_autocovariance(self):
        """Test fractional Gaussian noise autocovariance function."""
        fbm = FractionalBrownianMotion(hurst=0.75, volatility=2.0)
        
        # Test autocovariance properties
        gamma_0 = fbm.fgn_autocovariance(0)
        assert gamma_0 > 0  # Positive variance
        
        gamma_1 = fbm.fgn_autocovariance(1)
        gamma_neg1 = fbm.fgn_autocovariance(-1)
        assert np.isclose(gamma_1, gamma_neg1)  # Symmetry
    
    def test_numerical_stability_davies_harte(self):
        """Test numerical stability of Davies-Harte for challenging parameters."""
        # Test case that might cause numerical issues
        fbm = FractionalBrownianMotion(hurst=0.05, random_state=42)  # Very low H
        times = np.linspace(0, 1, 129)  # Large grid
        
        try:
            result = fbm.sample(times, n_paths=5, method=FBMMethod.DAVIES_HARTE)
            assert not np.any(np.isnan(result.paths))
            assert not np.any(np.isinf(result.paths))
        except ValueError as e:
            # Davies-Harte might fail for extreme parameters
            if "Negative eigenvalues" in str(e) or "invalid circulant embedding" in str(e):
                pytest.skip(f"Davies-Harte expected to fail for H={fbm.hurst}: {e}")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])