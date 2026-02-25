"""
Rigorous Brownian Motion implementation with mathematical guarantees.
"""

import numpy as np
from typing import Optional, Union
from .base import GaussianProcess, SimulationResult


class BrownianMotion(GaussianProcess):
    """
    Standard Brownian Motion with rigorous mathematical properties.
    
    Mathematical Definition:
    B = {B(t) : t ≥ 0} is standard Brownian motion if:
    1. B(0) = 0 almost surely
    2. B has independent increments
    3. B(t) - B(s) ~ N(0, t-s) for 0 ≤ s < t  
    4. B has continuous sample paths
    
    Parameters
    ----------
    drift : float, default=0.0
        Drift parameter μ (for arithmetic BM: dX = μdt + σdB)
    volatility : float, default=1.0  
        Volatility parameter σ
    random_state : int, optional
        Random seed for reproducibility
    """
    
    def __init__(self, 
                 drift: float = 0.0,
                 volatility: float = 1.0, 
                 random_state: Optional[int] = None):
        super().__init__(random_state)
        self.drift = drift
        self.volatility = volatility
        
        if not self.validate_parameters():
            raise ValueError("Invalid parameters for Brownian Motion")
    
    def validate_parameters(self) -> bool:
        """Validate mathematical constraints on parameters."""
        return self.volatility > 0
    
    def sample(self, 
               times: np.ndarray,
               n_paths: int = 1,
               method: str = 'increments') -> SimulationResult:
        """
        Generate Brownian motion paths.
        
        Parameters
        ----------
        times : np.ndarray
            Time points (must start at 0)
        n_paths : int, default=1
            Number of independent paths
        method : str, default='increments'
            Simulation method: 'increments' or 'continuous_decomposition'
            
        Returns
        -------
        SimulationResult
            Simulation results with paths and metadata
        """
        if times[0] != 0:
            raise ValueError("Time array must start at t=0")
        
        if method == 'increments':
            paths = self._simulate_via_increments(times, n_paths)
        elif method == 'continuous_decomposition':
            paths = self._simulate_via_continuous_decomposition(times, n_paths)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return SimulationResult(
            paths=paths,
            times=times,
            n_paths=n_paths,
            n_steps=len(times),
            parameters={'drift': self.drift, 'volatility': self.volatility},
            method=method
        )
    
    def _simulate_via_increments(self, times: np.ndarray, n_paths: int) -> np.ndarray:
        """Standard method: cumulative sum of independent increments."""
        dt = np.diff(times)
        increments = self._rng.normal(0, np.sqrt(dt), size=(n_paths, len(dt)))
        
        # Add drift component
        if self.drift != 0:
            increments += self.drift * dt
        
        # Scale by volatility
        if self.volatility != 1:
            increments *= self.volatility
        
        # Cumulative sum starting from 0
        paths = np.zeros((n_paths, len(times)))
        paths[:, 1:] = np.cumsum(increments, axis=1)
        
        return paths
    
    def _simulate_via_continuous_decomposition(self, 
                                             times: np.ndarray, 
                                             n_paths: int,
                                             n_terms: int = 500) -> np.ndarray:
        """
        Continuous-time decomposition method from original notebook.
        
        Uses series representation:
        B(t) = √2 Σₖ Zₖ sin((k-½)πt) / ((k-½)π)
        
        where Zₖ ~ N(0,1) independent
        """
        T = times[-1]  # Terminal time
        paths = np.zeros((n_paths, len(times)))
        
        for path_idx in range(n_paths):
            # Generate random coefficients
            Z = self._rng.normal(0, 1, n_terms)
            k = np.arange(1, n_terms + 1)
            
            for i, t in enumerate(times):
                # Normalized time
                t_norm = t / T
                
                # Compute sine terms
                sin_terms = np.sin((k - 0.5) * np.pi * t_norm) / ((k - 0.5) * np.pi)
                
                # Series sum
                paths[path_idx, i] = np.sqrt(2 * T) * np.dot(Z, sin_terms)
        
        # Apply drift and volatility
        if self.drift != 0:
            paths += self.drift * times.reshape(1, -1)
        
        if self.volatility != 1:
            paths *= self.volatility
            
        return paths
    
    def covariance_function(self, s: float, t: float) -> float:
        """
        Brownian motion covariance: Cov(B(s), B(t)) = σ² min(s,t).
        """
        return self.volatility**2 * min(s, t)
    
    def mean_function(self, times: np.ndarray) -> np.ndarray:
        """Mean function: 𝔼[B(t)] = μt for arithmetic BM."""
        return self.drift * times
    
    def quadratic_variation(self, times: np.ndarray) -> np.ndarray:
        """
        Theoretical quadratic variation: [B,B]ₜ = σ²t.
        """
        return self.volatility**2 * times
    
    def first_passage_time_density(self, level: float, times: np.ndarray) -> np.ndarray:
        """
        Density of first passage time to level a:
        f(t) = |a|/√(2πt³) exp(-a²/(2t))
        """
        if level == 0:
            raise ValueError("Level must be non-zero")
        
        density = (np.abs(level) / np.sqrt(2 * np.pi * times**3) * 
                  np.exp(-level**2 / (2 * times)))
        
        return density
    
    def maximum_distribution(self, t: float, x: float) -> float:
        """
        CDF of maximum up to time t: P(max_{s≤t} B(s) ≤ x).
        
        For x ≥ 0: P(M_t ≤ x) = 2Φ(x/√t) - 1
        """
        if x < 0:
            return 0.0
        
        from scipy.stats import norm
        return 2 * norm.cdf(x / np.sqrt(t)) - 1
    
    def variance_at_time(self, t: float) -> float:
        """
        Variance of B(t).
        
        For Brownian motion: Var[B(t)] = σ²t
        """
        return self.volatility**2 * t