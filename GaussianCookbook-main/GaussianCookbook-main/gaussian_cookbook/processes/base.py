"""
Abstract base classes for stochastic processes with mathematical rigor.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
import numpy as np
from dataclasses import dataclass


@dataclass
class SimulationResult:
    """Results from stochastic process simulation."""
    paths: np.ndarray
    times: np.ndarray
    n_paths: int
    n_steps: int
    parameters: dict
    method: str


class StochasticProcess(ABC):
    """
    Abstract base class for stochastic processes.
    
    All implementations must satisfy mathematical properties:
    1. Well-defined probability space (Ω, ℱ, ℙ)
    2. Measurable sample paths
    3. Correct distributional properties
    """
    
    def __init__(self, random_state: Optional[int] = None):
        self.random_state = random_state
        self._rng = np.random.RandomState(random_state)
    
    @abstractmethod
    def sample(self, 
               times: np.ndarray,
               n_paths: int = 1) -> SimulationResult:
        """
        Generate sample paths of the stochastic process.
        
        Parameters
        ----------
        times : np.ndarray
            Time points for simulation
        n_paths : int, default=1
            Number of independent sample paths
            
        Returns
        -------
        SimulationResult
            Complete simulation results with metadata
        """
        pass
    
    @abstractmethod
    def covariance_function(self, s: float, t: float) -> float:
        """
        Theoretical covariance function Cov(X(s), X(t)).
        
        Must satisfy:
        1. Symmetry: K(s,t) = K(t,s)
        2. Positive definiteness
        3. Continuity (if process has continuous paths)
        """
        pass
    
    @abstractmethod
    def validate_parameters(self) -> bool:
        """Validate that process parameters are mathematically valid."""
        pass
    
    def theoretical_covariance_matrix(self, times: np.ndarray) -> np.ndarray:
        """Compute theoretical covariance matrix for given time points."""
        n = len(times)
        cov_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                cov_matrix[i, j] = self.covariance_function(times[i], times[j])
        
        return cov_matrix
    
    def verify_positive_definite(self, times: np.ndarray, tolerance: float = 1e-10) -> bool:
        """Verify covariance matrix is positive definite."""
        cov_matrix = self.theoretical_covariance_matrix(times)
        eigenvals = np.linalg.eigvals(cov_matrix)
        return np.all(eigenvals > -tolerance)


class GaussianProcess(StochasticProcess):
    """Base class for Gaussian stochastic processes."""
    
    def probability_density(self, 
                           x: np.ndarray, 
                           times: np.ndarray) -> float:
        """
        Multivariate Gaussian density for process values.
        
        f(x) = (2π)^{-n/2} |Σ|^{-1/2} exp(-½(x-μ)ᵀΣ⁻¹(x-μ))
        """
        n = len(times)
        mean = self.mean_function(times)
        cov = self.theoretical_covariance_matrix(times)
        
        # Numerical stability: use Cholesky decomposition
        try:
            L = np.linalg.cholesky(cov)
            log_det = 2 * np.sum(np.log(np.diag(L)))
        except np.linalg.LinAlgError:
            # Fallback to eigendecomposition
            eigenvals = np.linalg.eigvals(cov)
            log_det = np.sum(np.log(eigenvals))
        
        diff = x - mean
        inv_cov_diff = np.linalg.solve(cov, diff)
        
        log_prob = -0.5 * (n * np.log(2 * np.pi) + log_det + 
                          diff.T @ inv_cov_diff)
        
        return np.exp(log_prob)
    
    @abstractmethod
    def mean_function(self, times: np.ndarray) -> np.ndarray:
        """Mean function μ(t) = 𝔼[X(t)]."""
        pass


class MartingaleProcess(StochasticProcess):
    """Base class for martingale processes."""
    
    def verify_martingale_property(self, 
                                 paths: np.ndarray, 
                                 times: np.ndarray,
                                 n_tests: int = 100) -> bool:
        """
        Statistical test for martingale property.
        
        Test: 𝔼[X(t)|ℱ_s] = X(s) for s ≤ t
        """
        # Implementation would use conditional expectation estimation
        # This is a placeholder for the statistical test
        pass