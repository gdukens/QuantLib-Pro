"""
Brownian Bridge implementation with mathematical rigor.
"""

import numpy as np
from typing import Optional, Tuple
from .base import GaussianProcess, SimulationResult


class BrownianBridge(GaussianProcess):
    """
    Brownian Bridge with rigorous mathematical implementation.
    
    Mathematical Definition:
    A Brownian bridge B^b(t) on [0,T] from a to b is defined as:
    B^b(t) = a + (b-a)t/T + B(t) - tB(T)/T
    
    where B(t) is standard Brownian motion.
    
    Equivalently, it's a Gaussian process with:
    - B^b(0) = a, B^b(T) = b (deterministic endpoints)
    - Covariance: Cov(B^b(s), B^b(t)) = σ²s(T-t)/T for s ≤ t
    
    Parameters
    ----------
    start_value : float, default=0.0
        Starting value a = B^b(0)
    end_value : float, default=0.0  
        Ending value b = B^b(T)
    volatility : float, default=1.0
        Volatility parameter σ
    random_state : int, optional
        Random seed for reproducibility
    """
    
    def __init__(self,
                 start_value: float = 0.0,
                 end_value: float = 0.0,
                 volatility: float = 1.0,
                 random_state: Optional[int] = None):
        super().__init__(random_state)
        self.start_value = start_value
        self.end_value = end_value
        self.volatility = volatility
        
        if not self.validate_parameters():
            raise ValueError("Invalid parameters for Brownian Bridge")
    
    def validate_parameters(self) -> bool:
        """Validate mathematical constraints on parameters."""
        return self.volatility > 0
    
    def sample(self,
               times: np.ndarray,
               n_paths: int = 1,
               method: str = 'sequential') -> SimulationResult:
        """
        Generate Brownian bridge paths.
        
        Parameters
        ----------
        times : np.ndarray
            Time points (must start at 0)
        n_paths : int, default=1
            Number of independent paths
        method : str, default='sequential'  
            Simulation method: 'sequential' or 'brownian_motion'
            
        Returns
        -------
        SimulationResult
            Simulation results with paths and metadata
        """
        if times[0] != 0:
            raise ValueError("Time array must start at t=0")
        
        T = times[-1]
        if T <= 0:
            raise ValueError("Terminal time must be positive") 
        
        if method == 'sequential':
            paths = self._simulate_sequential(times, n_paths, T)
        elif method == 'brownian_motion':
            paths = self._simulate_from_brownian_motion(times, n_paths, T)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return SimulationResult(
            paths=paths,
            times=times,
            n_paths=n_paths,
            n_steps=len(times),
            parameters={
                'start_value': self.start_value,
                'end_value': self.end_value, 
                'volatility': self.volatility
            },
            method=method
        )
    
    def _simulate_sequential(self, times: np.ndarray, n_paths: int, T: float) -> np.ndarray:
        """
        Sequential simulation method for Brownian bridge.
        
        Uses the recursive property of Brownian bridge for efficient simulation.
        """
        n_steps = len(times)
        paths = np.zeros((n_paths, n_steps))
        
        # Set deterministic endpoints
        paths[:, 0] = self.start_value
        paths[:, -1] = self.end_value
        
        # Recursive construction using bridge property
        for path_idx in range(n_paths):
            self._construct_bridge_recursive(paths[path_idx], times, 0, n_steps-1, T)
        
        return paths
    
    def _construct_bridge_recursive(self, path: np.ndarray, times: np.ndarray, 
                                   left_idx: int, right_idx: int, T: float):
        """Recursively construct Brownian bridge using bridge property."""
        if right_idx - left_idx <= 1:
            return
        
        # Find middle point
        mid_idx = (left_idx + right_idx) // 2
        
        t_left, t_mid, t_right = times[left_idx], times[mid_idx], times[right_idx]
        x_left, x_right = path[left_idx], path[right_idx]
        
        # Bridge conditional mean and variance
        mu = x_left + (x_right - x_left) * (t_mid - t_left) / (t_right - t_left)
        var = self.volatility**2 * (t_mid - t_left) * (t_right - t_mid) / (t_right - t_left)
        
        # Sample from conditional Gaussian
        path[mid_idx] = mu + np.sqrt(var) * self._rng.normal()
        
        # Recursively fill left and right segments
        self._construct_bridge_recursive(path, times, left_idx, mid_idx, T)
        self._construct_bridge_recursive(path, times, mid_idx, right_idx, T)
    
    def _simulate_from_brownian_motion(self, times: np.ndarray, n_paths: int, T: float) -> np.ndarray:
        """
        Generate bridge from Brownian motion transformation.
        
        B^b(t) = a + (b-a)t/T + B(t) - tB(T)/T
        """
        from .brownian_motion import BrownianMotion
        
        # Generate underlying Brownian motion
        bm = BrownianMotion(volatility=self.volatility, random_state=self._rng.randint(0, 2**31))
        bm_result = bm.sample(times, n_paths=n_paths)
        bm_paths = bm_result.paths
        
        # Transform to bridge
        bridge_paths = np.zeros_like(bm_paths)
        
        for i, t in enumerate(times):
            # Bridge transformation
            linear_interp = self.start_value + (self.end_value - self.start_value) * t / T
            bridge_correction = bm_paths[:, i] - (t / T) * bm_paths[:, -1]
            bridge_paths[:, i] = linear_interp + bridge_correction
        
        return bridge_paths
    
    def covariance_function(self, s: float, t: float) -> float:
        """
        Brownian bridge covariance function.
        
        For bridge on [0,T] from a to b:
        Cov(B^b(s), B^b(t)) = σ²s(T-t)/T for s ≤ t
        """
        T_total = 1.0  # Assume unit time interval for covariance calculation
        if s > t:
            s, t = t, s  # Ensure s ≤ t
        
        return self.volatility**2 * s * (T_total - t) / T_total
    
    def mean_function(self, times: np.ndarray) -> np.ndarray:
        """
        Mean function: deterministic linear interpolation between endpoints.
        
        μ(t) = a + (b-a)t/T
        """
        T = times[-1] if len(times) > 1 else 1.0
        return self.start_value + (self.end_value - self.start_value) * times / T
    
    def conditional_distribution(self, t: float, s: float, x_s: float, T: float) -> Tuple[float, float]:
        """
        Conditional distribution B^b(t) | B^b(s) = x_s.
        
        Returns
        -------
        Tuple[float, float]
            (conditional_mean, conditional_variance)
        """
        if not (0 <= s <= t <= T):
            raise ValueError("Time ordering must be 0 ≤ s ≤ t ≤ T")
        
        # Conditional mean
        a, b = self.start_value, self.end_value
        mu_cond = x_s + (b - x_s) * (t - s) / (T - s)
        
        # Conditional variance  
        var_cond = self.volatility**2 * (t - s) * (T - t) / (T - s)
        
        return mu_cond, var_cond
    
    def maximum_distribution_cdf(self, x: float, T: float = 1.0) -> float:
        """
        CDF of maximum of Brownian bridge on [0,T] from 0 to 0.
        
        P(max_{0≤t≤T} B^b(t) ≤ x) = 1 - exp(-2x²/T) for x ≥ 0
        """
        if x < 0:
            return 0.0
        
        # Only valid for bridge from 0 to 0
        if self.start_value != 0 or self.end_value != 0:
            raise NotImplementedError("Maximum distribution only implemented for bridge from 0 to 0")
        
        return 1 - np.exp(-2 * x**2 / (self.volatility**2 * T))