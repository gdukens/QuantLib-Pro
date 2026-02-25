"""
Rigorous Fractional Brownian Motion implementation with mathematical guarantees.

Implements multiple algorithms including Davies-Harte, Cholesky decomposition,
and approximation methods with full theoretical validation.
"""

import numpy as np
from typing import Optional, Union, Literal
from enum import Enum
from .base import GaussianProcess, SimulationResult
import warnings


class FBMMethod(Enum):
    """Available methods for fBM simulation."""
    DAVIES_HARTE = "davies_harte"
    CHOLESKY = "cholesky" 
    WOOD_CHAN = "wood_chan"
    HOSKING = "hosking"


class FractionalBrownianMotion(GaussianProcess):
    """
    Fractional Brownian Motion with rigorous mathematical implementation.
    
    Mathematical Definition:
    B_H = {B_H(t) : t ≥ 0} is fractional Brownian motion with Hurst parameter H ∈ (0,1) if:
    1. B_H(0) = 0 almost surely
    2. B_H is Gaussian process with covariance:
       R_H(s,t) = ½σ²(|t|^{2H} + |s|^{2H} - |t-s|^{2H})
    3. B_H has stationary increments  
    4. B_H has continuous sample paths
    
    The increments process {X_k = B_H(k+1) - B_H(k)} is called fractional
    Gaussian noise (fGn) with covariance:
    γ(k) = ½(|k+1|^{2H} - 2|k|^{2H} + |k-1|^{2H})
    
    Parameters
    ----------
    hurst : float
        Hurst parameter H ∈ (0,1). Controls long-range dependence:
        - H = 0.5: Standard Brownian motion (independent increments)
        - H > 0.5: Persistent behavior (positive correlations)  
        - H < 0.5: Anti-persistent behavior (negative correlations)
    volatility : float, default=1.0
        Volatility parameter σ
    random_state : int, optional
        Random seed for reproducibility
        
    References
    ----------
    .. [1] Davies, R.B. and Harte, D.S. (1987). Tests for Hurst effect. 
           Biometrika, 74(1), 95-101.
    .. [2] Wood, A.T.A. and Chan, G. (1994). Simulation of stationary Gaussian
           processes. Journal of Computational and Graphical Statistics, 3(4), 409-432.
    """
    
    def __init__(self, 
                 hurst: float,
                 volatility: float = 1.0,
                 random_state: Optional[int] = None):
        super().__init__(random_state)
        self.hurst = hurst
        self.volatility = volatility
        
        if not self.validate_parameters():
            raise ValueError(f"Invalid parameters: hurst={hurst}, volatility={volatility}")
    
    def validate_parameters(self) -> bool:
        """Validate mathematical constraints on parameters."""
        return (0 < self.hurst < 1) and (self.volatility > 0)
    
    def sample(self, 
               times: np.ndarray,
               n_paths: int = 1,
               method: Union[str, FBMMethod] = FBMMethod.DAVIES_HARTE) -> SimulationResult:
        """
        Generate fractional Brownian motion paths.
        
        Parameters
        ---------- 
        times : np.ndarray
            Time points (must start at 0 and be equally spaced for Davies-Harte)
        n_paths : int, default=1
            Number of independent paths
        method : str or FBMMethod, default='davies_harte'
            Simulation algorithm to use
            
        Returns
        -------
        SimulationResult
            Simulation results with paths and metadata
        """
        if times[0] != 0:
            raise ValueError("Time array must start at t=0")
        
        # Convert string to enum if needed
        if isinstance(method, str):
            method = FBMMethod(method)
        
        # Check if times are equally spaced (required for Davies-Harte)
        if method == FBMMethod.DAVIES_HARTE:
            dt_values = np.diff(times)
            if not np.allclose(dt_values, dt_values[0], rtol=1e-10):
                raise ValueError("Davies-Harte method requires equally spaced time points")
        
        if method == FBMMethod.DAVIES_HARTE:
            paths = self._simulate_davies_harte(times, n_paths)
        elif method == FBMMethod.CHOLESKY:
            paths = self._simulate_cholesky(times, n_paths)
        elif method == FBMMethod.WOOD_CHAN:
            paths = self._simulate_wood_chan(times, n_paths)
        elif method == FBMMethod.HOSKING:
            paths = self._simulate_hosking(times, n_paths)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return SimulationResult(
            paths=paths,
            times=times,
            n_paths=n_paths, 
            n_steps=len(times),
            parameters={'hurst': self.hurst, 'volatility': self.volatility},
            method=method.value
        )
    
    def _simulate_davies_harte(self, times: np.ndarray, n_paths: int) -> np.ndarray:
        """
        Davies-Harte algorithm for exact fBM simulation.
        
        Uses circulant embedding of covariance matrix for O(N log N) complexity.
        Most efficient method for equally spaced time points.
        """
        N = len(times) - 1  # Number of increments
        T = times[-1]
        
        paths = np.zeros((n_paths, len(times)))
        
        for path_idx in range(n_paths):
            # Generate fGn using Davies-Harte
            fgn = self._generate_fgn_davies_harte(N, self.hurst, T)
            
            # Cumulative sum to get fBM
            fbm = np.cumsum(np.concatenate([[0], fgn]))
            
            # Apply volatility scaling
            paths[path_idx] = self.volatility * fbm
            
        return paths
    
    def _generate_fgn_davies_harte(self, N: int, H: float, T: float) -> np.ndarray:
        """
        Generate fractional Gaussian noise using Davies-Harte algorithm.
        
        Implementation from the notebook with mathematical rigor added.
        """
        # Autocovariance function of fGn
        def gamma(k):
            return 0.5 * (abs(k + 1)**(2 * H) - 2 * abs(k)**(2 * H) + abs(k - 1)**(2 * H))
        
        # Circulant vector construction
        c = np.concatenate([
            np.array([gamma(k) for k in range(N + 1)]),
            np.array([gamma(k) for k in range(N - 1, 0, -1)])
        ])
        
        # Compute eigenvalues via FFT
        L = np.fft.fft(c).real
        
        # Validate mathematical conditions
        if not np.allclose(np.fft.fft(c).imag, 0, atol=1e-10):
            raise ValueError("FFT has significant imaginary components - invalid covariance structure")
        
        if np.any(L < -1e-10):  # Allow small numerical errors
            raise ValueError("Negative eigenvalues encountered - invalid circulant embedding")
        
        # Clip small negative eigenvalues to zero
        L = np.maximum(L, 0)
        
        # FFT length
        M = 2 * N
        
        # Generate complex Gaussian vector
        Z = np.zeros(M, dtype=np.complex128)
        
        # Real components at boundaries
        Z[0] = np.sqrt(L[0]) * self._rng.normal()
        if N > 0:
            Z[N] = np.sqrt(L[N]) * self._rng.normal()
        
        # Complex components for intermediate frequencies
        if N > 1:
            X = self._rng.normal(0, 1, N - 1)  
            Y = self._rng.normal(0, 1, N - 1)
            
            for k in range(1, N):
                Z[k] = np.sqrt(L[k] / 2) * (X[k-1] + 1j * Y[k-1])
                Z[M - k] = np.conj(Z[k])
        
        # Inverse FFT to recover fGn
        fgn = np.fft.ifft(Z).real[:N] * np.sqrt(M) * (T / N) ** H
        
        return fgn
    
    def _simulate_cholesky(self, times: np.ndarray, n_paths: int) -> np.ndarray:
        """
        Exact simulation via Cholesky decomposition.
        
        Mathematically exact but O(N³) complexity. Use for small N or validation.
        """
        n_steps = len(times)
        cov_matrix = self.theoretical_covariance_matrix(times)
        
        try:
            L = np.linalg.cholesky(cov_matrix)
        except np.linalg.LinAlgError:
            # Add small regularization for numerical stability
            reg = 1e-12 * np.eye(n_steps)
            L = np.linalg.cholesky(cov_matrix + reg)
        
        # Generate paths
        paths = np.zeros((n_paths, n_steps))
        
        for i in range(n_paths):
            z = self._rng.normal(0, 1, n_steps)
            paths[i] = self.volatility * (L @ z)
            
        return paths
    
    def _simulate_wood_chan(self, times: np.ndarray, n_paths: int) -> np.ndarray:
        """
        Wood-Chan method for approximate fBM simulation.
        
        Faster than Cholesky but approximate. Good for large N.
        """
        warnings.warn("Wood-Chan method not yet implemented, using Cholesky", UserWarning)
        return self._simulate_cholesky(times, n_paths)
    
    def _simulate_hosking(self, times: np.ndarray, n_paths: int) -> np.ndarray:
        """
        Hosking's method for exact fBM simulation.
        
        O(N²) algorithm based on recursive construction.
        """
        warnings.warn("Hosking method not yet implemented, using Cholesky", UserWarning)
        return self._simulate_cholesky(times, n_paths)
    
    def covariance_function(self, s: float, t: float) -> float:
        """
        Fractional Brownian motion covariance function.
        
        R_H(s,t) = ½σ²(|s|^{2H} + |t|^{2H} - |t-s|^{2H})
        """
        return 0.5 * self.volatility**2 * (
            abs(s)**(2 * self.hurst) + 
            abs(t)**(2 * self.hurst) - 
            abs(t - s)**(2 * self.hurst)
        )
    
    def mean_function(self, times: np.ndarray) -> np.ndarray:
        """Mean function: 𝔼[B_H(t)] = 0 for all t."""
        return np.zeros_like(times)
    
    def fgn_autocovariance(self, lag: int) -> float:
        """
        Autocovariance function of fractional Gaussian noise.
        
        γ(k) = ½(|k+1|^{2H} - 2|k|^{2H} + |k-1|^{2H})
        """
        H = self.hurst
        return 0.5 * self.volatility**2 * (
            abs(lag + 1)**(2 * H) - 
            2 * abs(lag)**(2 * H) + 
            abs(lag - 1)**(2 * H)
        )
    
    def spectral_density(self, frequency: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Spectral density of fBM (for |ω| → 0):
        
        f_H(ω) ∝ |ω|^{-(2H+1)}
        """
        return np.power(np.abs(frequency), -(2 * self.hurst + 1))
    
    def variance_at_time(self, t: float) -> float:
        """Variance: Var[B_H(t)] = σ² t^{2H}."""
        return self.volatility**2 * t**(2 * self.hurst)
    
    def increments_variance(self, dt: float) -> float:
        """Variance of increments over time dt: Var[B_H(t+dt) - B_H(t)] = σ² dt^{2H}."""
        return self.volatility**2 * dt**(2 * self.hurst)
    
    def long_range_dependence_parameter(self) -> float:
        """
        Long-range dependence parameter d = H - 0.5.
        
        d > 0: Long memory (persistent)
        d = 0: No memory (Brownian motion)  
        d < 0: Anti-persistent
        """
        return self.hurst - 0.5
    
    def is_persistent(self) -> bool:
        """Check if process exhibits persistence (H > 0.5)."""
        return self.hurst > 0.5
    
    def is_antipersistent(self) -> bool:
        """Check if process exhibits anti-persistence (H < 0.5)."""
        return self.hurst < 0.5