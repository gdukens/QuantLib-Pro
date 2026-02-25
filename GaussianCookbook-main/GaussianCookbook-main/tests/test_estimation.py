"""
Test suite for parameter estimation methods.

Tests Hurst parameter estimation, MLE, and statistical inference.
"""

import numpy as np
import pytest
import warnings

from gaussian_cookbook.processes import FractionalBrownianMotion
from gaussian_cookbook.estimation import HurstEstimator, MaximumLikelihoodEstimator


class TestHurstEstimation:
    """Test Hurst parameter estimation methods."""
    
    @pytest.fixture
    def estimator(self):
        """Hurst estimator for testing."""
        return HurstEstimator(random_state=42)
    
    @pytest.fixture
    def fbm_data(self):
        """Generate known fBM data for estimation."""
        true_hurst = 0.7
        fbm = FractionalBrownianMotion(hurst=true_hurst, random_state=123)
        times = np.linspace(0, 1, 1000)
        result = fbm.sample(times, n_paths=1)
        return result.paths[0], times, true_hurst
    
    def test_dfa_estimation(self, estimator, fbm_data):
        """Test Detrended Fluctuation Analysis."""
        data, times, true_hurst = fbm_data
        
        # Use increments for DFA
        increments = np.diff(data)
        
        result = estimator.dfa_estimate(increments, n_bootstrap=100)
        
        assert hasattr(result, 'hurst_estimate')
        assert hasattr(result, 'confidence_interval') 
        assert result.correlation_coefficient > 0.8  # Should have good linear fit
        
        # Hurst estimate should be reasonably close 
        error = abs(result.hurst_estimate - true_hurst)
        assert error < 0.3, f"DFA estimate error too large: {error:.4f}"
        
        # Confidence interval should contain estimate
        ci = result.confidence_interval
        assert ci[0] <= result.hurst_estimate <= ci[1]
    
    def test_whittle_estimation(self, estimator, fbm_data):
        """Test Whittle likelihood estimation."""
        data, times, true_hurst = fbm_data
        
        # Use increments 
        increments = np.diff(data)
        
        result = estimator.whittle_estimate(increments)
        
        assert hasattr(result, 'estimate')
        assert hasattr(result, 'standard_error')
        assert hasattr(result, 'confidence_interval')
        
        # Should be reasonably close
        error = abs(result.estimate - true_hurst)
        assert error < 0.4, f"Whittle estimate error too large: {error:.4f}"
        
        # Standard error should be positive
        assert result.standard_error > 0
    
    def test_gph_test(self, estimator, fbm_data):
        """Test Geweke-Porter-Hudak test."""
        data, times, true_hurst = fbm_data
        
        # Use increments
        increments = np.diff(data)
        
        result = estimator.gph_test(increments)
        
        assert hasattr(result, 'hurst_estimate')
        assert hasattr(result, 'memory_parameter')
        assert hasattr(result, 'p_value')
        
        # Check relationship: H = d + 0.5
        expected_hurst = result.memory_parameter + 0.5
        assert np.isclose(result.hurst_estimate, expected_hurst, atol=1e-10)
        
        # For H > 0.5, should detect long memory (reject H₀: d = 0)
        if true_hurst > 0.5:
            if result.p_value < 0.05:  # Significant long memory detected
                assert result.memory_parameter > 0
    
    def test_rs_analysis(self, estimator, fbm_data):
        """Test R/S analysis."""
        data, times, true_hurst = fbm_data
        
        # Use increments
        increments = np.diff(data)
        
        hurst_est, r_squared = estimator.rs_analysis(increments)
        
        assert 0 < hurst_est < 1, f"R/S Hurst estimate out of bounds: {hurst_est}"
        assert 0 <= r_squared <= 1, f"R² out of bounds: {r_squared}"
        
        # Should have reasonable fit
        assert r_squared > 0.5, f"R/S has poor fit: R²={r_squared:.4f}"
    
    def test_compare_methods(self, estimator, fbm_data):
        """Test comparison across multiple methods."""
        data, times, true_hurst = fbm_data
        
        increments = np.diff(data)
        
        results = estimator.compare_methods(increments)
        
        # Check that methods ran successfully
        successful_methods = []
        for method_name, result in results.items():
            if not isinstance(result, str):  # Not an error message
                successful_methods.append(method_name)
        
        assert len(successful_methods) >= 2, "At least 2 methods should succeed"
        
        # Extract Hurst estimates from successful methods
        hurst_estimates = []
        for method_name in successful_methods:
            result = results[method_name]
            if hasattr(result, 'hurst_estimate'):
                hurst_estimates.append(result.hurst_estimate)
            elif hasattr(result, 'estimate'):
                hurst_estimates.append(result.estimate)
            elif isinstance(result, dict) and 'hurst_estimate' in result:
                hurst_estimates.append(result['hurst_estimate'])
        
        # Methods should give somewhat consistent results
        if len(hurst_estimates) >= 2:
            hurst_range = max(hurst_estimates) - min(hurst_estimates)
            assert hurst_range < 0.5, f"Methods too inconsistent: range={hurst_range:.4f}"
    
    def test_edge_cases(self, estimator):
        """Test estimation with edge cases."""
        # Very short series
        short_data = np.random.randn(50)
        
        # Should handle gracefully or raise informative error
        try:
            result = estimator.dfa_estimate(short_data, n_bootstrap=10)
            assert hasattr(result, 'hurst_estimate')
        except (ValueError, Warning):
            pass  # Expected for very short series
        
        # Constant series
        constant_data = np.ones(500)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                result = estimator.dfa_estimate(constant_data, n_bootstrap=10)
                # May succeed with degenerate result
            except (ValueError, RuntimeWarning):
                pass  # Expected for constant data


class TestMaximumLikelihoodEstimation:
    """Test Maximum Likelihood Estimation."""
    
    @pytest.fixture
    def mle(self):
        """MLE estimator for testing."""
        return MaximumLikelihoodEstimator(random_state=42)
    
    @pytest.fixture  
    def fbm_path_data(self):
        """Generate single fBM path for MLE."""
        true_hurst = 0.65
        true_volatility = 1.5
        
        fbm = FractionalBrownianMotion(
            hurst=true_hurst, 
            volatility=true_volatility,
            random_state=234
        )
        
        times = np.linspace(0, 1, 100)  # Moderate size for MLE
        result = fbm.sample(times, n_paths=1, method='cholesky')  # Use exact method
        
        return result.paths[0], times, true_hurst, true_volatility
    
    def test_fbm_parameter_estimation(self, mle, fbm_path_data):
        """Test MLE for fBM parameters."""
        path, times, true_hurst, true_volatility = fbm_path_data
        
        result = mle.estimate_fbm_parameters(path, times)
        
        assert result.convergence, "MLE optimization should converge"
        
        # Check parameter estimates
        estimated_hurst = result.parameters['hurst']
        estimated_volatility = result.parameters['volatility']
        
        assert 0 < estimated_hurst < 1, f"Hurst estimate out of bounds: {estimated_hurst}"
        assert estimated_volatility > 0, f"Volatility estimate negative: {estimated_volatility}"
        
        # Should be reasonably close (allowing for estimation uncertainty)
        hurst_error = abs(estimated_hurst - true_hurst)
        vol_error = abs(estimated_volatility - true_volatility) / true_volatility
        
        assert hurst_error < 0.4, f"Hurst MLE error too large: {hurst_error:.4f}"
        assert vol_error < 0.8, f"Volatility MLE error too large: {vol_error:.4f}"
        
        # Check Fisher Information
        assert result.fisher_information.shape == (2, 2)
        
        # Standard errors should be positive
        for param, se in result.standard_errors.items():
            if not np.isnan(se):
                assert se > 0, f"Standard error for {param} should be positive"
        
        # Confidence intervals should contain estimates
        for param, ci in result.confidence_intervals.items():
            if not (np.isnan(ci[0]) or np.isnan(ci[1])):
                estimate = result.parameters[param]
                assert ci[0] <= estimate <= ci[1], f"CI for {param} doesn't contain estimate"
    
    def test_mle_with_bounds(self, mle, fbm_path_data):
        """Test MLE with parameter bounds."""
        path, times, true_hurst, true_volatility = fbm_path_data
        
        # Tight bounds around true values
        bounds = {
            'hurst': (true_hurst - 0.1, true_hurst + 0.1),
            'volatility': (true_volatility * 0.5, true_volatility * 2.0)
        }
        
        result = mle.estimate_fbm_parameters(path, times, bounds=bounds)
        
        # Estimates should respect bounds
        h_est = result.parameters['hurst'] 
        v_est = result.parameters['volatility']
        
        assert bounds['hurst'][0] <= h_est <= bounds['hurst'][1]
        assert bounds['volatility'][0] <= v_est <= bounds['volatility'][1]
    
    def test_profile_likelihood(self, mle, fbm_path_data):
        """Test profile likelihood computation."""
        path, times, true_hurst, true_volatility = fbm_path_data
        
        # Profile over Hurst parameter
        hurst_values = np.linspace(0.3, 0.9, 10)
        
        profile_ll = mle.profile_likelihood(
            path, times, 
            param_name='hurst',
            param_values=hurst_values
        )
        
        assert len(profile_ll) == len(hurst_values)
        assert not np.all(np.isinf(profile_ll)), "Profile likelihood should have finite values"
        
        # Maximum should be near true value (within tolerance)
        max_idx = np.argmax(profile_ll)
        optimal_hurst = hurst_values[max_idx]
        
        hurst_error = abs(optimal_hurst - true_hurst)
        assert hurst_error < 0.3, f"Profile likelihood maximum far from truth: {hurst_error:.4f}"
    
    def test_mle_numerical_stability(self, mle):
        """Test MLE numerical stability."""
        # Generate challenging case: very small increments
        fbm = FractionalBrownianMotion(hurst=0.8, volatility=0.1, random_state=42)
        times = np.linspace(0, 0.1, 50)  # Small time horizon, small increments
        result = fbm.sample(times, n_paths=1)
        path = result.paths[0]
        
        # Should handle without overflow/underflow
        mle_result = mle.estimate_fbm_parameters(path, times)
        
        # Parameters should be finite
        for param, value in mle_result.parameters.items():
            assert np.isfinite(value), f"Parameter {param} is not finite: {value}"
        
        # Log-likelihood should be finite
        assert np.isfinite(mle_result.log_likelihood), "Log-likelihood not finite"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])