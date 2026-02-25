"""
Maximum Likelihood Estimation for Gaussian processes.

Provides rigorous MLE implementation with Fisher Information and 
asymptotic confidence intervals.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
from scipy.optimize import minimize
from scipy.linalg import solve
from scipy.linalg import det
import warnings


@dataclass
class MLEResult:
    """Results from Maximum Likelihood Estimation."""
    parameters: Dict[str, float]
    log_likelihood: float
    fisher_information: np.ndarray
    standard_errors: Dict[str, float] 
    confidence_intervals: Dict[str, Tuple[float, float]]
    convergence: bool
    n_iterations: int
    method: str = "MLE"


class MaximumLikelihoodEstimator:
    """
    Maximum Likelihood Estimation for Gaussian stochastic processes.
    
    Provides rigorous implementation with:
    1. Numerical stability via Cholesky decomposition
    2. Fisher Information Matrix computation
    3. Asymptotic confidence intervals
    4. Convergence diagnostics
    5. Parameter constraints handling
    """
    
    def __init__(self, random_state: Optional[int] = None):
        self.random_state = random_state
        self._rng = np.random.RandomState(random_state)
    
    def estimate_fbm_parameters(self, 
                               data: np.ndarray,
                               times: np.ndarray,
                               initial_guess: Optional[Dict[str, float]] = None,
                               bounds: Optional[Dict[str, Tuple[float, float]]] = None) -> MLEResult:
        """
        MLE for Fractional Brownian Motion parameters.
        
        Estimates Hurst parameter and volatility from path observations.
        
        Parameters
        ----------
        data : np.ndarray
            Observed path values (single path)
        times : np.ndarray  
            Observation times
        initial_guess : Dict[str, float], optional
            Initial parameter guesses {'hurst': H, 'volatility': σ}
        bounds : Dict[str, Tuple[float, float]], optional
            Parameter bounds
            
        Returns
        -------
        MLEResult
            Complete MLE results with statistical inference
        """
        if len(data.shape) > 1:
            raise ValueError("MLE currently supports single path only")
        
        if len(data) != len(times):
            raise ValueError("Data and times must have same length")
        
        if times[0] != 0:
            raise ValueError("Times must start at 0")
        
        # Default initial guess
        if initial_guess is None:
            initial_guess = {'hurst': 0.6, 'volatility': 1.0}
        
        # Default bounds
        if bounds is None:
            bounds = {
                'hurst': (0.01, 0.99),
                'volatility': (0.01, 10.0)
            }
        
        # Parameter vector and bounds for optimization
        param_names = ['hurst', 'volatility']
        x0 = [initial_guess[name] for name in param_names]
        opt_bounds = [bounds[name] for name in param_names]
        
        # Define negative log-likelihood
        def neg_log_likelihood(params):
            param_dict = dict(zip(param_names, params))
            return -self._fbm_log_likelihood(data, times, param_dict)
        
        # Optimization
        result = minimize(
            neg_log_likelihood,
            x0,
            method='L-BFGS-B',
            bounds=opt_bounds,
        )
        
        if not result.success:
            warnings.warn(f"MLE optimization failed: {result.message}")
        
        # Extract optimal parameters
        optimal_params = dict(zip(param_names, result.x))
        
        # Compute Fisher Information at optimum
        fisher_info = self._compute_fisher_information(data, times, optimal_params)
        
        # Standard errors from inverse Fisher Information
        try:
            fisher_inv = np.linalg.inv(fisher_info)
            standard_errors = {name: np.sqrt(fisher_inv[i, i]) 
                             for i, name in enumerate(param_names)}
        except np.linalg.LinAlgError:
            warnings.warn("Fisher Information matrix is singular")
            standard_errors = {name: np.nan for name in param_names}
            fisher_inv = np.full_like(fisher_info, np.nan)
        
        # Confidence intervals (asymptotic normality)
        confidence_intervals = {}
        for i, name in enumerate(param_names):
            se = standard_errors[name]
            if not np.isnan(se):
                ci = (optimal_params[name] - 1.96 * se, 
                     optimal_params[name] + 1.96 * se)
                confidence_intervals[name] = ci
            else:
                confidence_intervals[name] = (np.nan, np.nan)
        
        return MLEResult(
            parameters=optimal_params,
            log_likelihood=-result.fun,
            fisher_information=fisher_info,
            standard_errors=standard_errors,
            confidence_intervals=confidence_intervals,
            convergence=result.success,
            n_iterations=result.nit,
        )
    
    def _fbm_log_likelihood(self, data: np.ndarray, times: np.ndarray, 
                           params: Dict[str, float]) -> float:
        """
        Log-likelihood for Fractional Brownian Motion.
        
        L(H,σ) = -½ log|Σ| - ½ x'Σ⁻¹x - (n/2) log(2π)
        """
        hurst = params['hurst']
        volatility = params['volatility']
        
        n = len(data)
        
        # Covariance matrix
        cov_matrix = self._fbm_covariance_matrix(times, hurst, volatility)
        
        try:
            # Cholesky decomposition for numerical stability
            L = np.linalg.cholesky(cov_matrix)
            log_det = 2 * np.sum(np.log(np.diag(L)))
            
            # Solve L y = data for y, then compute y'y = data' Σ⁻¹ data
            y = solve(L, data, lower=True)
            quadratic_form = np.dot(y, y)
            
        except np.linalg.LinAlgError:
            # Fallback to eigendecomposition
            try:
                eigenvals, eigenvecs = np.linalg.eigh(cov_matrix)
                if np.any(eigenvals <= 0):
                    return -np.inf  # Invalid covariance matrix
                
                log_det = np.sum(np.log(eigenvals))
                
                # data' Σ⁻¹ data = data' V Λ⁻¹ V' data
                v_data = eigenvecs.T @ data
                quadratic_form = np.sum(v_data**2 / eigenvals)
                
            except np.linalg.LinAlgError:
                return -np.inf
        
        # Log-likelihood
        log_lik = -0.5 * (log_det + quadratic_form + n * np.log(2 * np.pi))
        
        return log_lik
    
    def _fbm_covariance_matrix(self, times: np.ndarray, hurst: float, 
                              volatility: float) -> np.ndarray:
        """Construct fBM covariance matrix."""
        n = len(times)
        cov = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                s, t = times[i], times[j]
                cov[i, j] = 0.5 * volatility**2 * (
                    abs(s)**(2 * hurst) + 
                    abs(t)**(2 * hurst) - 
                    abs(t - s)**(2 * hurst)
                )
        
        return cov
    
    def _compute_fisher_information(self, data: np.ndarray, times: np.ndarray,
                                   params: Dict[str, float], 
                                   epsilon: float = 1e-5) -> np.ndarray:
        """
        Compute Fisher Information Matrix numerically.
        
        I(θ) = -E[∂²ℓ/∂θ∂θ'] ≈ -∂²ℓ/∂θ∂θ'
        """
        param_names = ['hurst', 'volatility']
        n_params = len(param_names)
        
        fisher = np.zeros((n_params, n_params))
        
        # Compute Hessian of negative log-likelihood
        for i in range(n_params):
            for j in range(i, n_params):
                
                # Parameter perturbations
                params_pp = params.copy()
                params_pp[param_names[i]] += epsilon
                params_pp[param_names[j]] += epsilon
                
                params_pm = params.copy()  
                params_pm[param_names[i]] += epsilon
                params_pm[param_names[j]] -= epsilon
                
                params_mp = params.copy()
                params_mp[param_names[i]] -= epsilon
                params_mp[param_names[j]] += epsilon
                
                params_mm = params.copy()
                params_mm[param_names[i]] -= epsilon
                params_mm[param_names[j]] -= epsilon
                
                # Finite difference approximation
                try:
                    hess_ij = (
                        self._fbm_log_likelihood(data, times, params_pp) -
                        self._fbm_log_likelihood(data, times, params_pm) -
                        self._fbm_log_likelihood(data, times, params_mp) +
                        self._fbm_log_likelihood(data, times, params_mm)
                    ) / (4 * epsilon**2)
                    
                    fisher[i, j] = -hess_ij
                    if i != j:
                        fisher[j, i] = fisher[i, j]
                        
                except:
                    fisher[i, j] = np.nan
                    if i != j:
                        fisher[j, i] = np.nan
        
        return fisher
    
    def profile_likelihood(self, data: np.ndarray, times: np.ndarray,
                          param_name: str, param_values: np.ndarray,
                          fixed_params: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        Compute profile likelihood for parameter inference.
        
        Parameters
        ----------
        data : np.ndarray
            Observed data
        times : np.ndarray
            Observation times  
        param_name : str
            Parameter to profile over
        param_values : np.ndarray
            Values of parameter to evaluate
        fixed_params : Dict[str, float], optional
            Parameters to keep fixed
            
        Returns
        -------
        np.ndarray
            Profile log-likelihood values
        """
        if fixed_params is None:
            fixed_params = {}
        
        log_likelihoods = []
        
        for value in param_values:
            # Fix the parameter of interest
            params = fixed_params.copy()
            params[param_name] = value
            
            # If other parameters not specified, use MLE with this parameter fixed
            if param_name == 'hurst' and 'volatility' not in params:
                # Optimize over volatility only
                def neg_ll(vol):
                    p = params.copy()
                    p['volatility'] = vol[0]
                    return -self._fbm_log_likelihood(data, times, p)
                
                result = minimize(neg_ll, [1.0], bounds=[(0.01, 10.0)])
                if result.success:
                    params['volatility'] = result.x[0]
                    ll = -result.fun
                else:
                    ll = -np.inf
                    
            elif param_name == 'volatility' and 'hurst' not in params:
                # Optimize over hurst only  
                def neg_ll(h):
                    p = params.copy()  
                    p['hurst'] = h[0]
                    return -self._fbm_log_likelihood(data, times, p)
                
                result = minimize(neg_ll, [0.6], bounds=[(0.01, 0.99)])
                if result.success:
                    params['hurst'] = result.x[0]
                    ll = -result.fun
                else:
                    ll = -np.inf
            else:
                # All parameters specified
                ll = self._fbm_log_likelihood(data, times, params)
            
            log_likelihoods.append(ll)
        
        return np.array(log_likelihoods)