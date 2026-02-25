"""
Statistical hypothesis testing for stochastic processes.

Implements comprehensive testing framework for:
- Stationarity testing  
- Long memory testing
- Goodness-of-fit testing
- Model specification testing
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, List
from scipy import stats
from scipy.linalg import eigvals
import warnings


@dataclass
class StationarityTestResult:
    """Results from stationarity tests."""
    test_name: str
    statistic: float
    p_value: float
    critical_values: dict
    is_stationary: bool
    null_hypothesis: str
    alternative_hypothesis: str


@dataclass  
class LongMemoryTestResult:
    """Results from long memory tests."""
    test_name: str
    statistic: float
    p_value: float
    memory_parameter: float
    is_long_memory: bool
    null_hypothesis: str
    alternative_hypothesis: str


@dataclass
class GoodnessOfFitResult:
    """Results from goodness-of-fit tests."""
    test_name: str
    statistic: float
    p_value: float
    is_good_fit: bool
    null_hypothesis: str
    alternative_hypothesis: str


class HypothesisTests:
    """
    Comprehensive hypothesis testing suite for stochastic processes.
    
    Provides rigorous statistical tests with proper p-values and 
    critical values based on asymptotic theory.
    """
    
    def __init__(self, significance_level: float = 0.05):
        self.alpha = significance_level
    
    def augmented_dickey_fuller_test(self, data: np.ndarray, 
                                   regression_type: str = 'c',
                                   lags: Optional[int] = None) -> StationarityTestResult:
        """
        Augmented Dickey-Fuller test for unit root (non-stationarity).
        
        H₀: Series has unit root (non-stationary)
        H₁: Series is stationary
        
        Parameters
        ----------
        data : np.ndarray
            Time series data
        regression_type : str, default='c'  
            Type of regression: 'c' (constant), 'ct' (constant+trend), 'nc' (none)
        lags : int, optional
            Number of lags. If None, automatically selected.
            
        Returns
        -------
        StationarityTestResult
            ADF test results
        """
        from statsmodels.tsa.stattools import adfuller
        
        try:
            if lags is None:
                # Automatic lag selection
                max_lags = int(12 * (len(data) / 100) ** (1/4))
                result = adfuller(data, regression=regression_type, autolag='AIC', maxlag=max_lags)
            else:
                result = adfuller(data, regression=regression_type, maxlag=lags)
            
            adf_stat, p_value = result[0], result[1]
            critical_values = result[4]
            
            is_stationary = p_value < self.alpha
            
            return StationarityTestResult(
                test_name="Augmented Dickey-Fuller",
                statistic=adf_stat,
                p_value=p_value,
                critical_values=critical_values,
                is_stationary=is_stationary,
                null_hypothesis="Series has unit root (non-stationary)",
                alternative_hypothesis="Series is stationary"
            )
            
        except ImportError:
            # Fallback implementation
            warnings.warn("statsmodels not available, using simplified ADF test")
            return self._simple_adf_test(data)
    
    def kpss_test(self, data: np.ndarray, 
                  regression_type: str = 'c') -> StationarityTestResult:
        """
        KPSS test for stationarity.
        
        H₀: Data is stationary around deterministic trend
        H₁: Data has unit root
        
        Parameters
        ----------
        data : np.ndarray
            Time series data  
        regression_type : str, default='c'
            Type of regression: 'c' (level stationary) or 'ct' (trend stationary)
            
        Returns
        -------
        StationarityTestResult
            KPSS test results
        """
        try:
            from statsmodels.tsa.stattools import kpss
            
            kpss_stat, p_value, lags, critical_values = kpss(data, regression=regression_type)
            
            is_stationary = p_value > self.alpha  # Note: reversed logic for KPSS
            
            return StationarityTestResult(
                test_name="KPSS",
                statistic=kpss_stat,
                p_value=p_value,
                critical_values=critical_values,
                is_stationary=is_stationary,
                null_hypothesis="Data is stationary",
                alternative_hypothesis="Data has unit root"
            )
            
        except ImportError:
            warnings.warn("statsmodels not available, KPSS test unavailable")
            raise NotImplementedError("KPSS test requires statsmodels")
    
    def ljung_box_test(self, data: np.ndarray, 
                      lags: int = 10) -> GoodnessOfFitResult:
        """
        Ljung-Box test for autocorrelation in residuals.
        
        H₀: No autocorrelation (white noise)
        H₁: Autocorrelation present
        
        Parameters
        ----------
        data : np.ndarray
            Residuals or time series data
        lags : int, default=10
            Number of lags to test
            
        Returns
        -------
        GoodnessOfFitResult  
            Ljung-Box test results
        """
        n = len(data)
        k = min(lags, n - 1)
        
        # Sample autocorrelations
        autocorrs = []
        for lag in range(1, k + 1):
            if lag >= n:
                break
            corr = np.corrcoef(data[:-lag], data[lag:])[0, 1]
            if np.isnan(corr):
                corr = 0.0
            autocorrs.append(corr)
        
        # Ljung-Box statistic
        lb_stat = n * (n + 2) * sum(
            autocorrs[i]**2 / (n - i - 1) 
            for i in range(len(autocorrs))
        )
        
        # Chi-squared p-value
        p_value = 1 - stats.chi2.cdf(lb_stat, df=len(autocorrs))
        
        is_white_noise = p_value > self.alpha
        
        return GoodnessOfFitResult(
            test_name="Ljung-Box",
            statistic=lb_stat,
            p_value=p_value,
            is_good_fit=is_white_noise,
            null_hypothesis="No autocorrelation (white noise)",
            alternative_hypothesis="Autocorrelation present"
        )
    
    def jarque_bera_test(self, data: np.ndarray) -> GoodnessOfFitResult:
        """
        Jarque-Bera test for normality.
        
        H₀: Data is normally distributed  
        H₁: Data is not normally distributed
        
        Parameters
        ----------
        data : np.ndarray
            Sample data
            
        Returns
        -------
        GoodnessOfFitResult
            Jarque-Bera test results
        """
        jb_stat, p_value = stats.jarque_bera(data)
        
        is_normal = p_value > self.alpha
        
        return GoodnessOfFitResult(
            test_name="Jarque-Bera",
            statistic=jb_stat,
            p_value=p_value,
            is_good_fit=is_normal,
            null_hypothesis="Data is normally distributed",
            alternative_hypothesis="Data is not normally distributed"
        )
    
    def anderson_darling_test(self, data: np.ndarray, 
                            distribution: str = 'norm') -> GoodnessOfFitResult:
        """
        Anderson-Darling test for distributional assumptions.
        
        Parameters
        ----------
        data : np.ndarray
            Sample data
        distribution : str, default='norm'
            Distribution to test against: 'norm', 'expon', 'logistic', 'gumbel'
            
        Returns
        -------
        GoodnessOfFitResult
            Anderson-Darling test results
        """
        ad_result = stats.anderson(data, dist=distribution)
        
        ad_stat = ad_result.statistic
        critical_values = ad_result.critical_values
        significance_levels = ad_result.significance_level
        
        # Find appropriate critical value
        critical_value = np.interp(self.alpha * 100, significance_levels, critical_values)
        
        # Approximate p-value (not exact for all distributions)
        if distribution == 'norm':
            # Approximation for normal distribution
            p_value = np.exp(-0.5 * ad_stat * (1 + 0.75/len(data)))
        else:
            p_value = None  # Exact p-value not available
        
        is_good_fit = ad_stat < critical_value
        
        return GoodnessOfFitResult(
            test_name=f"Anderson-Darling ({distribution})",
            statistic=ad_stat,
            p_value=p_value,
            is_good_fit=is_good_fit,
            null_hypothesis=f"Data follows {distribution} distribution",
            alternative_hypothesis=f"Data does not follow {distribution} distribution"
        )
    
    def variance_ratio_test(self, data: np.ndarray, 
                           periods: List[int] = [2, 4, 8, 16]) -> List[GoodnessOfFitResult]:
        """
        Lo-MacKinlay variance ratio test for random walk hypothesis.
        
        H₀: Data follows random walk (unit root with drift)
        H₁: Data does not follow random walk
        
        Parameters
        ---------- 
        data : np.ndarray
            Time series data (levels or returns)
        periods : List[int], default=[2, 4, 8, 16]
            Holding periods for variance ratios
            
        Returns
        -------
        List[GoodnessOfFitResult]
            VR test results for each period
        """
        n = len(data)
        results = []
        
        # Compute returns if data looks like levels
        if np.std(np.diff(data)) / np.std(data) < 0.1:
            returns = np.diff(np.log(data))
        else:
            returns = data
        
        n_returns = len(returns)
        
        for q in periods:
            if q >= n_returns:
                continue
            
            # q-period returns
            q_returns = []
            for i in range(q, n_returns + 1, q):
                q_returns.append(np.sum(returns[i-q:i]))
            
            if len(q_returns) < 2:
                continue
                
            # Variance ratio
            var_1 = np.var(returns, ddof=1)
            var_q = np.var(q_returns, ddof=1) / q
            
            if var_1 > 0:
                vr = var_q / var_1
            else:
                continue
            
            # Test statistic (assuming homoskedasticity)
            nq = len(q_returns) * q
            z_stat = np.sqrt(nq) * (vr - 1) / np.sqrt(2 * (q - 1))
            
            # Two-tailed p-value
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            
            is_random_walk = p_value > self.alpha
            
            results.append(GoodnessOfFitResult(
                test_name=f"Variance Ratio (q={q})",
                statistic=z_stat,
                p_value=p_value,
                is_good_fit=is_random_walk,
                null_hypothesis="Data follows random walk",
                alternative_hypothesis="Data does not follow random walk"
            ))
        
        return results
    
    def _simple_adf_test(self, data: np.ndarray) -> StationarityTestResult:
        """Simplified ADF test implementation."""
        n = len(data)
        
        # First difference
        dy = np.diff(data)
        y_lag = data[:-1]
        
        # Regression: Δy_t = α + βy_{t-1} + ε_t
        X = np.column_stack([np.ones(len(y_lag)), y_lag])
        
        try:
            beta = np.linalg.lstsq(X, dy, rcond=None)[0]
            residuals = dy - X @ beta
            
            # Standard error of β
            mse = np.sum(residuals**2) / (len(residuals) - 2)
            se_beta = np.sqrt(mse * np.linalg.inv(X.T @ X)[1, 1])
            
            # t-statistic  
            t_stat = beta[1] / se_beta
            
            # Approximate critical values (MacKinnon)
            critical_values = {
                '1%': -3.43,
                '5%': -2.86, 
                '10%': -2.57
            }
            
            # Approximate p-value (very rough)
            p_value = 0.05 if t_stat > critical_values['5%'] else 0.01 if t_stat > critical_values['1%'] else 0.001
            
            is_stationary = t_stat < critical_values['5%']
            
            return StationarityTestResult(
                test_name="Simplified ADF",
                statistic=t_stat,
                p_value=p_value,
                critical_values=critical_values,
                is_stationary=is_stationary,
                null_hypothesis="Series has unit root (non-stationary)",
                alternative_hypothesis="Series is stationary"
            )
            
        except np.linalg.LinAlgError:
            # Degenerate case
            return StationarityTestResult(
                test_name="Simplified ADF",
                statistic=np.nan,
                p_value=np.nan,
                critical_values={},
                is_stationary=False,
                null_hypothesis="Series has unit root (non-stationary)",
                alternative_hypothesis="Series is stationary"
            )