"""
Bachelier Option Pricing Model
==============================

Implementation of the Bachelier (1900) model for option pricing under
arithmetic Brownian motion. This is the first mathematical model of
derivatives pricing, predating Black-Scholes by 73 years.

Mathematical Foundation
-----------------------
The Bachelier model assumes the underlying asset follows arithmetic Brownian motion:
    dF = σ dW

Where:
    F: Forward/futures price
    σ: Absolute volatility (not percentage)
    W: Wiener process

Closed-Form Solutions
--------------------
Call Option:
    C = (F - K)×Φ(d) + σ√T×φ(d)

Put Option:
    P = (K - F)×Φ(-d) + σ√T×φ(d)

Where:
    d = (F - K) / (σ√T)
    Φ: Standard normal CDF
    φ: Standard normal PDF

Use Cases
---------
1. Futures and forwards pricing (constant strike)
2. Low or negative interest rate environments
3. Short-dated options near at-the-money
4. Historical analysis and academic research
5. Situations where absolute price changes are more relevant than percentages

References
----------
- Bachelier, L. (1900). "Théorie de la spéculation."
  Annales scientifiques de l'École normale supérieure, 17, 21-86.

Author: Extracted from Q-Fin, Enhanced for QuantLib Pro
Date: February 24, 2026
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Tuple, List, Optional, Literal
import numpy as np
from scipy.stats import norm


@dataclass
class BachelierParams:
    """
    Parameters for the Bachelier model.
    
    Attributes
    ----------
    sigma : float
        Absolute volatility (not percentage). Must be positive.
        Typical values: 10-50 for equity indices, 0.5-2.0 for FX.
    """
    sigma: float
    
    def __post_init__(self):
        """Validate parameters."""
        if self.sigma <= 0:
            raise ValueError(f"Sigma must be positive, got {self.sigma}")
        if np.isnan(self.sigma) or np.isinf(self.sigma):
            raise ValueError(f"Sigma must be finite, got {self.sigma}")


class BachelierModel:
    """
    Bachelier option pricing model with arithmetic Brownian motion.
    
    This model is particularly useful for:
    - Futures/forwards (no carry cost complications)
    - Low/negative rate environments
    - Short-dated ATM options
    - Academic research and historical analysis
    
    Examples
    --------
    >>> # Create model with absolute volatility of 20
    >>> model = BachelierModel(sigma=20.0)
    >>> 
    >>> # Price a call option
    >>> call_price = model.price(F0=100, K=100, T=1.0, option_type='call')
    >>> print(f"Call price: {call_price:.4f}")
    Call price: 7.9788
    >>> 
    >>> # Price a put option (put-call parity verified)
    >>> put_price = model.price(F0=100, K=100, T=1.0, option_type='put')
    >>> print(f"Put price: {put_price:.4f}")
    Put price: 7.9788
    >>> 
    >>> # Simulate paths
    >>> paths = model.simulate(F0=100, n_paths=1000, n_steps=252, T=1.0, seed=42)
    >>> print(f"Terminal mean: {np.mean([p[-1] for p in paths]):.2f}")
    Terminal mean: 100.12
    """
    
    def __init__(self, sigma: float):
        """
        Initialize Bachelier model.
        
        Parameters
        ----------
        sigma : float
            Absolute volatility (must be positive).
        """
        self.params = BachelierParams(sigma=sigma)
    
    @property
    def sigma(self) -> float:
        """Get current volatility parameter."""
        return self.params.sigma
    
    def price(
        self,
        F0: float,
        K: float,
        T: float,
        option_type: Literal['call', 'put'] = 'call'
    ) -> float:
        """
        Price a European option using the Bachelier formula.
        
        Parameters
        ----------
        F0 : float
            Current forward/futures price (must be positive).
        K : float
            Strike price (must be positive).
        T : float
            Time to maturity in years (must be positive).
        option_type : {'call', 'put'}, default='call'
            Type of option to price.
        
        Returns
        -------
        float
            Option price.
        
        Raises
        ------
        ValueError
            If any parameter is invalid.
        
        Examples
        --------
        >>> model = BachelierModel(sigma=20.0)
        >>> call = model.price(F0=100, K=100, T=1.0, option_type='call')
        >>> put = model.price(F0=100, K=100, T=1.0, option_type='put')
        >>> print(f"ATM Call: {call:.4f}, ATM Put: {put:.4f}")
        ATM Call: 7.9788, ATM Put: 7.9788
        """
        # Input validation
        if F0 <= 0:
            raise ValueError(f"Forward price F0 must be positive, got {F0}")
        if K <= 0:
            raise ValueError(f"Strike K must be positive, got {K}")
        if T <= 0:
            raise ValueError(f"Time to maturity T must be positive, got {T}")
        if option_type not in ['call', 'put']:
            raise ValueError(f"option_type must be 'call' or 'put', got {option_type}")
        
        # Handle edge case: T very close to 0
        if T < 1e-10:
            if option_type == 'call':
                return max(F0 - K, 0.0)
            else:
                return max(K - F0, 0.0)
        
        # Calculate d parameter
        sigma_sqrt_T = self.params.sigma * np.sqrt(T)
        d = (F0 - K) / sigma_sqrt_T
        
        # Calculate option price
        if option_type == 'call':
            # C = (F - K)×Φ(d) + σ√T×φ(d)
            price = (F0 - K) * norm.cdf(d) + sigma_sqrt_T * norm.pdf(d)
        else:  # put
            # P = (K - F)×Φ(-d) + σ√T×φ(d)
            # Note: φ(d) = φ(-d) (symmetric)
            price = (K - F0) * norm.cdf(-d) + sigma_sqrt_T * norm.pdf(d)
        
        return float(price)
    
    def delta(
        self,
        F0: float,
        K: float,
        T: float,
        option_type: Literal['call', 'put'] = 'call'
    ) -> float:
        """
        Calculate option delta (∂C/∂F).
        
        For Bachelier model:
        - Call delta: Δ_C = Φ(d)
        - Put delta: Δ_P = Φ(d) - 1
        
        Parameters
        ----------
        F0 : float
            Current forward price.
        K : float
            Strike price.
        T : float
            Time to maturity in years.
        option_type : {'call', 'put'}, default='call'
            Type of option.
        
        Returns
        -------
        float
            Option delta.
        """
        if T <= 0:
            raise ValueError(f"Time to maturity T must be positive, got {T}")
        
        sigma_sqrt_T = self.params.sigma * np.sqrt(T)
        d = (F0 - K) / sigma_sqrt_T
        
        if option_type == 'call':
            return float(norm.cdf(d))
        else:  # put
            return float(norm.cdf(d) - 1.0)
    
    def gamma(self, F0: float, K: float, T: float) -> float:
        """
        Calculate option gamma (∂²C/∂F²).
        
        For Bachelier model:
        - Γ = φ(d) / (σ√T)
        - Same for both calls and puts
        
        Parameters
        ----------
        F0 : float
            Current forward price.
        K : float
            Strike price.
        T : float
            Time to maturity in years.
        
        Returns
        -------
        float
            Option gamma.
        """
        if T <= 0:
            raise ValueError(f"Time to maturity T must be positive, got {T}")
        
        sigma_sqrt_T = self.params.sigma * np.sqrt(T)
        d = (F0 - K) / sigma_sqrt_T
        
        return float(norm.pdf(d) / sigma_sqrt_T)
    
    def vega(self, F0: float, K: float, T: float) -> float:
        """
        Calculate option vega (∂C/∂σ).
        
        For Bachelier model:
        - ν = √T × φ(d)
        - Same for both calls and puts
        
        Parameters
        ----------
        F0 : float
            Current forward price.
        K : float
            Strike price.
        T : float
            Time to maturity in years.
        
        Returns
        -------
        float
            Option vega (per unit of absolute volatility).
        """
        if T <= 0:
            raise ValueError(f"Time to maturity T must be positive, got {T}")
        
        sqrt_T = np.sqrt(T)
        d = (F0 - K) / (self.params.sigma * sqrt_T)
        
        return float(sqrt_T * norm.pdf(d))
    
    def theta(
        self,
        F0: float,
        K: float,
        T: float,
        option_type: Literal['call', 'put'] = 'call'
    ) -> float:
        """
        Calculate option theta (∂C/∂T).
        
        For Bachelier model:
        - Θ = -σ×φ(d) / (2√T)
        - Same for both calls and puts (no drift term)
        
        Parameters
        ----------
        F0 : float
            Current forward price.
        K : float
            Strike price.
        T : float
            Time to maturity in years.
        option_type : {'call', 'put'}, default='call'
            Type of option.
        
        Returns
        -------
        float
            Option theta (per year).
        """
        if T <= 0:
            raise ValueError(f"Time to maturity T must be positive, got {T}")
        
        sqrt_T = np.sqrt(T)
        d = (F0 - K) / (self.params.sigma * sqrt_T)
        
        # Theta is negative (time decay)
        return float(-self.params.sigma * norm.pdf(d) / (2 * sqrt_T))
    
    def implied_volatility(
        self,
        price: float,
        F0: float,
        K: float,
        T: float,
        option_type: Literal['call', 'put'] = 'call',
        tol: float = 1e-6,
        max_iter: int = 100
    ) -> float:
        """
        Calculate implied volatility from option price using Newton-Raphson.
        
        Parameters
        ----------
        price : float
            Observed option price.
        F0 : float
            Current forward price.
        K : float
            Strike price.
        T : float
            Time to maturity.
        option_type : {'call', 'put'}, default='call'
            Type of option.
        tol : float, default=1e-6
            Convergence tolerance.
        max_iter : int, default=100
            Maximum iterations.
        
        Returns
        -------
        float
            Implied absolute volatility.
        
        Raises
        ------
        ValueError
            If Newton-Raphson fails to converge.
        """
        from scipy.optimize import newton
        
        def objective(sigma):
            temp_model = BachelierModel(sigma=sigma)
            return temp_model.price(F0, K, T, option_type) - price
        
        def derivative(sigma):
            temp_model = BachelierModel(sigma=sigma)
            return temp_model.vega(F0, K, T)
        
        # Initial guess: use intrinsic value relationship
        intrinsic = max(F0 - K, 0) if option_type == 'call' else max(K - F0, 0)
        time_value = price - intrinsic
        initial_guess = max(time_value / np.sqrt(T * 2 * np.pi), 0.1)
        
        try:
            result = newton(
                objective,
                x0=initial_guess,
                fprime=derivative,
                tol=tol,
                maxiter=max_iter
            )
            return float(result)
        except RuntimeError as e:
            raise ValueError(f"Failed to converge: {e}")
    
    def simulate(
        self,
        F0: float,
        n_paths: int,
        n_steps: int,
        T: float,
        seed: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        Simulate price paths using arithmetic Brownian motion.
        
        Discretization:
            F_{t+dt} = F_t + σ×√dt×Z
        
        Where Z ~ N(0,1)
        
        Parameters
        ----------
        F0 : float
            Initial forward price.
        n_paths : int
            Number of paths to simulate.
        n_steps : int
            Number of time steps per path.
        T : float
            Time to maturity in years.
        seed : int, optional
            Random seed for reproducibility.
        
        Returns
        -------
        List[np.ndarray]
            List of simulated price paths, each of length (n_steps + 1).
        
        Examples
        --------
        >>> model = BachelierModel(sigma=20.0)
        >>> paths = model.simulate(F0=100, n_paths=1000, n_steps=252, T=1.0, seed=42)
        >>> terminal_prices = [path[-1] for path in paths]
        >>> print(f"Mean: {np.mean(terminal_prices):.2f}, Std: {np.std(terminal_prices):.2f}")
        Mean: 100.12, Std: 20.04
        """
        if F0 <= 0:
            raise ValueError(f"Initial price F0 must be positive, got {F0}")
        if n_paths <= 0:
            raise ValueError(f"Number of paths must be positive, got {n_paths}")
        if n_steps <= 0:
            raise ValueError(f"Number of steps must be positive, got {n_steps}")
        if T <= 0:
            raise ValueError(f"Time to maturity T must be positive, got {T}")
        
        # Set random seed for reproducibility
        if seed is not None:
            np.random.seed(seed)
        
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        
        paths = []
        for _ in range(n_paths):
            path = np.zeros(n_steps + 1)
            path[0] = F0
            
            for t in range(n_steps):
                dW = np.random.standard_normal()
                path[t + 1] = path[t] + self.params.sigma * sqrt_dt * dW
            
            paths.append(path)
        
        return paths
    
    def simulate_vectorized(
        self,
        F0: float,
        n_paths: int,
        n_steps: int,
        T: float,
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Simulate price paths using vectorized operations (faster).
        
        Parameters
        ----------
        F0 : float
            Initial forward price.
        n_paths : int
            Number of paths to simulate.
        n_steps : int
            Number of time steps per path.
        T : float
            Time to maturity in years.
        seed : int, optional
            Random seed for reproducibility.
        
        Returns
        -------
        np.ndarray
            Array of shape (n_paths, n_steps + 1) containing simulated paths.
        
        Examples
        --------
        >>> model = BachelierModel(sigma=20.0)
        >>> paths = model.simulate_vectorized(F0=100, n_paths=10000, n_steps=252, T=1.0)
        >>> print(f"Shape: {paths.shape}")
        Shape: (10000, 253)
        """
        if seed is not None:
            np.random.seed(seed)
        
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        
        # Generate all random numbers at once
        dW = np.random.standard_normal((n_paths, n_steps))
        
        # Calculate increments
        increments = self.params.sigma * sqrt_dt * dW
        
        # Cumulative sum to get paths
        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = F0
        paths[:, 1:] = F0 + np.cumsum(increments, axis=1)
        
        return paths
    
    def __repr__(self) -> str:
        return f"BachelierModel(sigma={self.params.sigma})"
    
    def __str__(self) -> str:
        return (
            f"Bachelier Model (Arithmetic Brownian Motion)\n"
            f"  Absolute Volatility (σ): {self.params.sigma:.4f}\n"
            f"  Model Type: European Options Pricing\n"
            f"  Underlying Process: dF = σ dW"
        )


# Convenience functions for quick pricing without instantiating model

def bachelier_call(F0: float, K: float, T: float, sigma: float) -> float:
    """
    Quick Bachelier call option pricing.
    
    Parameters
    ----------
    F0 : float
        Forward price.
    K : float
        Strike price.
    T : float
        Time to maturity.
    sigma : float
        Absolute volatility.
    
    Returns
    -------
    float
        Call option price.
    """
    model = BachelierModel(sigma=sigma)
    return model.price(F0, K, T, 'call')


def bachelier_put(F0: float, K: float, T: float, sigma: float) -> float:
    """
    Quick Bachelier put option pricing.
    
    Parameters
    ----------
    F0 : float
        Forward price.
    K : float
        Strike price.
    T : float
        Time to maturity.
    sigma : float
        Absolute volatility.
    
    Returns
    -------
    float
        Put option price.
    """
    model = BachelierModel(sigma=sigma)
    return model.price(F0, K, T, 'put')


if __name__ == "__main__":
    # Example usage and verification
    print("Bachelier Option Pricing Model")
    print("=" * 50)
    
    # Create model
    model = BachelierModel(sigma=20.0)
    print(model)
    print()
    
    # Price options
    F0, K, T = 100, 100, 1.0
    call_price = model.price(F0, K, T, 'call')
    put_price = model.price(F0, K, T, 'put')
    
    print(f"ATM Option Pricing (F0={F0}, K={K}, T={T}):")
    print(f"  Call Price: {call_price:.6f}")
    print(f"  Put Price:  {put_price:.6f}")
    print(f"  Put-Call Parity Check: {abs(call_price - put_price):.2e}")
    print()
    
    # Calculate Greeks
    print("Greeks:")
    print(f"  Delta (Call): {model.delta(F0, K, T, 'call'):.6f}")
    print(f"  Delta (Put):  {model.delta(F0, K, T, 'put'):.6f}")
    print(f"  Gamma:        {model.gamma(F0, K, T):.6f}")
    print(f"  Vega:         {model.vega(F0, K, T):.6f}")
    print(f"  Theta:        {model.theta(F0, K, T):.6f}")
    print()
    
    # Simulate paths
    print("Monte Carlo Simulation (1000 paths, 252 steps):")
    paths = model.simulate_vectorized(F0, 1000, 252, T, seed=42)
    terminal = paths[:, -1]
    print(f"  Mean Terminal Price: {np.mean(terminal):.2f} (Expected: {F0:.2f})")
    print(f"  Std Dev:             {np.std(terminal):.2f} (Expected: {model.sigma:.2f})")
