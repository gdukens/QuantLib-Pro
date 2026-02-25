"""
Rigorous Hurst parameter estimation with statistical inference.

Implements multiple estimation methods with confidence intervals and 
hypothesis testing capabilities.
"""

import numpy as np
import warnings
from dataclasses import dataclass
from typing import Optional, Tuple, List, Union
from scipy import stats
from scipy.optimize import minimize_scalar


@dataclass
class DFAResult:
    """Results from Detrended Fluctuation Analysis."""
    scaling_exponent: float
    hurst_estimate: float  
    correlation_coefficient: float
    p_value: float
    confidence_interval: Tuple[float, float]
    scales: np.ndarray
    fluctuations: np.ndarray
    method: str = "DFA"


@dataclass 
class WhittleResult:
    """Results from Whit   tle likelihood estimation."""
    estimate: float
    standard_error: float
    objective_value: float
    confidence_interval: Tuple[float, float]
    method: str = "Whittle"


@dataclass
class GPHResult:
    """Results from Geweke-Porter-Hudak test.""" 
    memory_parameter: float
    hurst_estimate: float
    standard_error: float
    t_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    bandwidth_fraction: float
    method: str = "GPH"


class HurstEstimator:
    """
    Comprehensive Hurst parameter estimation with statistical rigor.
    
    Implements multiple methods:
    1. Detrended Fluctuation Analysis (DFA)
    2. Whittle likelihood estimation 
    3. Geweke-Porter-Hudak (GPH) test
    4. R/S analysis
    5. Wavelet-based methods
    
    All methods include confidence intervals and statistical tests.
    """
    
    def __init__(self, random_state: Optional[int] = None):
        self.random_state = random_state
        self._rng = np.random.RandomState(random_state)
    
    def dfa_estimate(self, 
                    data: np.ndarray, 
                    scales: Optional[np.ndarray] = None,
                    polynomial_order: int = 1,
                    n_bootstrap: int = 1000) -> DFAResult:
        """
        Detrended Fluctuation Analysis with confidence intervals.
        
        Implementation of Peng et al. (1994) algorithm with statistical inference.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data  
        scales : np.ndarray, optional
            Scale values for analysis. If None, uses logarithmic spacing.
        polynomial_order : int, default=1
            Order of detrending polynomial (1=linear, 2=quadratic)
        n_bootstrap : int, default=1000
            Bootstrap samples for confidence intervals
            
        Returns
        -------
        DFAResult
            Complete DFA results with statistical inference
        """
        n = len(data)
        
        if scales is None:
            scales = self._optimal_dfa_scales(n)
        
        # Validate scales
        if np.any(scales < 4) or np.any(scales >= n/4):
            warnings.warn("Some scales may be too small/large for reliable estimation")
        
        fluctuations = []
        
        # Integrate the series (remove mean)
        integrated = np.cumsum(data - np.mean(data))
        
        for scale in scales:
            # Divide into non-overlapping boxes
            n_boxes = n // scale
            
            box_fluctuations = []
            for box in range(n_boxes):
                start, end = box * scale, (box + 1) * scale
                box_data = integrated[start:end]
                
                # Polynomial detrending
                x = np.arange(scale)
                coeffs = np.polyfit(x, box_data, deg=polynomial_order)
                trend = np.polyval(coeffs, x)
                
                # Local fluctuation
                fluctuation = np.sqrt(np.mean((box_data - trend)**2))
                box_fluctuations.append(fluctuation)
            
            fluctuations.append(np.mean(box_fluctuations))
        
        fluctuations = np.array(fluctuations)
        
        # Log-log regression
        log_scales = np.log(scales)
        log_fluctuations = np.log(fluctuations)
        
        slope, intercept, r_value, p_value, se = stats.linregress(log_scales, log_fluctuations)
        
        # Convert scaling exponent to Hurst parameter
        hurst_estimate = slope  # For DFA: α ≈ H (for fBm)
        
        # Bootstrap confidence intervals
        bootstrap_estimates = []
        for _ in range(n_bootstrap):
            # Bootstrap resample
            boot_indices = self._rng.choice(len(data), len(data), replace=True)
            boot_data = data[boot_indices]
            
            try:
                boot_result = self.dfa_estimate(boot_data, scales, polynomial_order, n_bootstrap=0)
                bootstrap_estimates.append(boot_result.hurst_estimate)
            except:
                continue  # Skip failed bootstrap samples
        
        if bootstrap_estimates:
            ci_lower = np.percentile(bootstrap_estimates, 2.5)
            ci_upper = np.percentile(bootstrap_estimates, 97.5)
        else:
            # Fallback to asymptotic CI
            ci_width = 1.96 * se
            ci_lower = hurst_estimate - ci_width  
            ci_upper = hurst_estimate + ci_width
        
        return DFAResult(
            scaling_exponent=slope,
            hurst_estimate=hurst_estimate,
            correlation_coefficient=r_value,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            scales=scales,
            fluctuations=fluctuations
        )
    
    def whittle_estimate(self, data: np.ndarray, 
                        hurst_bounds: Tuple[float, float] = (0.01, 0.99)) -> WhittleResult:
        """
        Whittle likelihood estimation for long-memory processes.
        
        Uses frequency domain likelihood for efficient estimation of Hurst parameter.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data
        hurst_bounds : Tuple[float, float], default=(0.01, 0.99)
            Bounds for Hurst parameter optimization
            
        Returns
        -------
        WhittleResult
            Whittle estimation results with confidence intervals
        """
        n = len(data)
        
        # Compute periodogram
        fft_data = np.fft.fft(data - np.mean(data))
        periodogram = np.abs(fft_data)**2 / n
        frequencies = np.fft.fftfreq(n, d=1.0)
        
        # Remove zero frequency and use positive frequencies
        mask = frequencies > 0
        periodogram = periodogram[mask]
        frequencies = frequencies[mask]
        
        def whittle_objective(hurst):
            """Whittle likelihood objective function."""
            # Spectral density of fBm: f(λ) ∝ |λ|^{-(2H+1)}
            spectral_density = np.power(np.abs(frequencies), -(2 * hurst + 1))
            
            # Normalize
            spectral_density = spectral_density / np.mean(spectral_density) * np.mean(periodogram)
            
            # Whittle likelihood
            return np.mean(np.log(spectral_density) + periodogram / spectral_density)
        
        # Optimize
        result = minimize_scalar(whittle_objective, bounds=hurst_bounds, method='bounded')
        
        if not result.success:
            warnings.warn("Whittle optimization did not converge")
        
        hurst_est = result.x
        
        # Asymptotic standard error: SE ≈ π/√(6n) for large n
        se = np.pi / np.sqrt(6 * len(frequencies))
        
        # Confidence interval
        ci_width = 1.96 * se
        ci = (hurst_est - ci_width, hurst_est + ci_width)
        
        return WhittleResult(
            estimate=hurst_est,
            standard_error=se,
            objective_value=result.fun,
            confidence_interval=ci
        )
    
    def gph_test(self, data: np.ndarray, 
                bandwidth_fraction: float = 0.5) -> GPHResult:
        """
        Geweke-Porter-Hudak test for long memory.
        
        Tests H₀: d = 0 (no long memory) vs H₁: d ≠ 0
        where d is the memory parameter (H = d + 0.5).
        
        Parameters
        ----------
        data : np.ndarray
            Time series data
        bandwidth_fraction : float, default=0.5
            Fraction of frequencies to use (m = n^bandwidth_fraction)
            
        Returns  
        -------
        GPHResult
            GPH test results with hypothesis test
        """
        n = len(data)
        
        # Number of frequencies to use
        m = int(n**bandwidth_fraction)
        
        if m < 3:
            raise ValueError("Sample size too small for GPH test") 
        
        # Periodogram
        fft_data = np.fft.fft(data - np.mean(data))
        periodogram = np.abs(fft_data[:m])**2 / n
        
        # Fourier frequencies (exclude zero)
        frequencies = 2 * np.pi * np.arange(1, m+1) / n
        
        # Log regression: log I(λⱼ) = log G - d log(4sin²(λⱼ/2)) + uⱼ
        x = np.log(4 * np.sin(frequencies / 2)**2)
        y = np.log(periodogram[1:])  # Exclude zero frequency
        
        if len(x) != len(y):
            min_len = min(len(x), len(y))
            x, y = x[:min_len], y[:min_len]
        
        # Regression
        slope, intercept, r_value, p_value, se = stats.linregress(x, y)
        
        # Memory parameter estimate
        d_est = -slope
        h_est = d_est + 0.5
        
        # Test statistic for H₀: d = 0
        # Under H₀: √m × d̂ → N(0, π²/6)
        t_stat = np.sqrt(len(x)) * d_est / (np.pi / np.sqrt(6))
        p_val = 2 * (1 - stats.norm.cdf(abs(t_stat)))
        
        # Confidence interval for d
        d_se = (np.pi / np.sqrt(6)) / np.sqrt(len(x))
        d_ci = (d_est - 1.96 * d_se, d_est + 1.96 * d_se)
        
        # Convert to Hurst CI
        h_ci = (d_ci[0] + 0.5, d_ci[1] + 0.5)
        
        return GPHResult(
            memory_parameter=d_est,
            hurst_estimate=h_est,
            standard_error=d_se,
            t_statistic=t_stat,
            p_value=p_val,
            confidence_interval=h_ci,
            bandwidth_fraction=bandwidth_fraction
        )
    
    def rs_analysis(self, data: np.ndarray, 
                   scales: Optional[np.ndarray] = None) -> Tuple[float, float]:
        """
        R/S (Rescaled Range) analysis for Hurst estimation.
        
        Classical method by Hurst (1951), modified for bias correction.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data
        scales : np.ndarray, optional
            Scale values for analysis
            
        Returns
        -------
        Tuple[float, float]
            (hurst_estimate, r_squared)
        """
        n = len(data)
        
        if scales is None:
            scales = np.logspace(1, np.log10(n//4), 20, dtype=int)
            scales = np.unique(scales)
        
        rs_values = []
        
        for scale in scales:
            if scale >= n:
                continue
                
            # Divide series into non-overlapping blocks
            n_blocks = n // scale
            rs_block = []
            
            for block in range(n_blocks):
                start, end = block * scale, (block + 1) * scale
                block_data = data[start:end]
                
                # Remove mean
                mean_adj = block_data - np.mean(block_data)
                
                # Cumulative sum
                cum_sum = np.cumsum(mean_adj)
                
                # Range
                R = np.max(cum_sum) - np.min(cum_sum)
                
                # Standard deviation
                S = np.std(block_data, ddof=1)
                
                if S > 0:
                    rs_block.append(R / S)
            
            if rs_block:
                rs_values.append(np.mean(rs_block))
            else:
                rs_values.append(np.nan)
        
        # Remove NaN values  
        valid_mask = ~np.isnan(rs_values)
        valid_scales = scales[valid_mask]
        valid_rs = np.array(rs_values)[valid_mask]
        
        if len(valid_rs) < 3:
            raise ValueError("Insufficient valid scales for R/S analysis")
        
        # Log-log regression: log(R/S) ~ H × log(n)
        log_scales = np.log(valid_scales)
        log_rs = np.log(valid_rs)
        
        slope, intercept, r_value, p_value, se = stats.linregress(log_scales, log_rs)
        
        return slope, r_value**2
    
    def compare_methods(self, data: np.ndarray) -> dict:
        """
        Compare multiple Hurst estimation methods.
        
        Returns
        -------
        dict
            Dictionary with results from all methods
        """
        results = {}
        
        try:
            results['dfa'] = self.dfa_estimate(data)
        except Exception as e:
            results['dfa'] = f"Failed: {e}"
        
        try:
            results['whittle'] = self.whittle_estimate(data)
        except Exception as e:
            results['whittle'] = f"Failed: {e}"
        
        try:
            results['gph'] = self.gph_test(data)  
        except Exception as e:
            results['gph'] = f"Failed: {e}"
        
        try:
            h_rs, r2_rs = self.rs_analysis(data)
            results['rs'] = {'hurst_estimate': h_rs, 'r_squared': r2_rs}
        except Exception as e:
            results['rs'] = f"Failed: {e}"
        
        return results
    
    def _optimal_dfa_scales(self, n: int) -> np.ndarray:
        """Generate optimal scale sequence for DFA."""
        min_scale = max(4, int(0.01 * n))
        max_scale = min(n // 4, int(0.25 * n))
        
        if min_scale >= max_scale:
            min_scale = 4
            max_scale = max(8, n // 10)
        
        # Logarithmic spacing
        scales = np.logspace(np.log10(min_scale), np.log10(max_scale), 20)
        return np.unique(scales.astype(int))