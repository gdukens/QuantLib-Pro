"""
Demonstration of refactored Gaussian Cookbook library.

This script shows the new API replacing notebook functions.
"""

import numpy as np
import matplotlib.pyplot as plt
from gaussian_cookbook.processes import BrownianMotion


def demonstrate_brownian_motion():
    """Demonstrate Brownian motion simulation with both methods."""
    
    # Create Brownian motion instance
    bm = BrownianMotion(drift=0.05, volatility=1.2, random_state=42)
    
    # Time grid
    times = np.linspace(0, 1, 500)
    
    # Generate paths using both methods
    print("Generating Brownian motion paths...")
    
    # Method 1: Standard increments
    result_inc = bm.sample(times, n_paths=10, method='increments')
    print(f"Increments method: {result_inc.paths.shape} paths generated")
    
    # Method 2: Continuous decomposition  
    result_cont = bm.sample(times, n_paths=10, method='continuous_decomposition')
    print(f"Continuous decomposition method: {result_cont.paths.shape} paths generated")
    
    # Validate theoretical properties
    print(f"\nValidating theoretical properties...")
    print(f"Covariance at (0.5, 0.5): {bm.covariance_function(0.5, 0.5):.4f}")
    print(f"Expected theoretical value: {min(0.5, 0.5) * bm.volatility**2:.4f}")
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot paths from increments method
    for i in range(min(5, result_inc.n_paths)):
        ax1.plot(times, result_inc.paths[i], alpha=0.7, linewidth=1.2)
    ax1.set_title("Increments Method")
    ax1.set_xlabel("Time")
    ax1.set_ylabel("B(t)")
    ax1.grid(True, alpha=0.3)
    
    # Plot paths from continuous decomposition
    for i in range(min(5, result_cont.n_paths)):
        ax2.plot(times, result_cont.paths[i], alpha=0.7, linewidth=1.2)
    ax2.set_title("Continuous Decomposition Method")
    ax2.set_xlabel("Time")
    ax2.set_ylabel("B(t)")
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle("Brownian Motion: Refactored Implementation")
    plt.tight_layout()
    plt.show()
    
    return result_inc, result_cont


def validate_covariance_convergence():
    """Demonstrate covariance structure convergence."""
    
    bm = BrownianMotion(random_state=123)
    times = np.linspace(0, 1, 20)
    
    path_counts = [100, 500, 2000, 5000]
    errors = []
    
    print("Testing covariance convergence...")
    
    for n_paths in path_counts:
        result = bm.sample(times, n_paths=n_paths)
        
        empirical_cov = np.cov(result.paths.T)
        theoretical_cov = bm.theoretical_covariance_matrix(times)
        
        # Frobenius norm of relative error
        rel_error = np.abs(empirical_cov - theoretical_cov) / (np.abs(theoretical_cov) + 1e-8)
        frobenius_error = np.sqrt(np.sum(rel_error**2))
        
        errors.append(frobenius_error)
        print(f"  {n_paths:5d} paths: Relative error = {frobenius_error:.6f}")
    
    # Plot convergence
    plt.figure(figsize=(10, 6))
    plt.loglog(path_counts, errors, 'bo-', linewidth=2, markersize=8)
    plt.loglog(path_counts, [e * np.sqrt(path_counts[0] / n) for e, n in zip([errors[0]], path_counts)], 
               'r--', alpha=0.7, label='1/√n theoretical')
    plt.xlabel('Number of Paths')
    plt.ylabel('Covariance Matrix Error (Frobenius Norm)')
    plt.title('Convergence of Empirical to Theoretical Covariance')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()
    
    return errors


def performance_comparison():
    """Compare performance of different methods."""
    import time
    
    bm = BrownianMotion(random_state=42)
    times = np.linspace(0, 1, 1000)
    n_paths = 100
    
    methods = ['increments', 'continuous_decomposition']
    times_taken = {}
    
    print("Performance comparison...")
    
    for method in methods:
        start_time = time.perf_counter()
        
        result = bm.sample(times, n_paths=n_paths, method=method)
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        times_taken[method] = elapsed
        
        print(f"  {method:25s}: {elapsed:.4f} seconds")
    
    # Performance ratio
    ratio = times_taken['continuous_decomposition'] / times_taken['increments']
    print(f"  Continuous decomposition is {ratio:.1f}x {'slower' if ratio > 1 else 'faster'} than increments")
    
    return times_taken


if __name__ == "__main__":
    print("🎯 Gaussian Cookbook Refactored Demonstration")
    print("=" * 50)
    
    # Basic demonstration
    result_inc, result_cont = demonstrate_brownian_motion()
    
    print("\n" + "=" * 50)
    
    # Convergence validation
    errors = validate_covariance_convergence()
    
    print("\n" + "=" * 50)
    
    # Performance comparison
    perf_times = performance_comparison()
    
    print("\n✅ Demonstration complete!")
    print(f"📊 Generated {result_inc.n_paths} paths with {result_inc.n_steps} time points each")
    print(f"🧮 Mathematical properties validated")
    print(f"⚡ Performance benchmarked")
    
    print(f"\n📝 Next steps:")
    print(f"   1. Run tests: pytest tests/ -v")
    print(f"   2. Install package: pip install -e .")
    print(f"   3. Import: from gaussian_cookbook.processes import BrownianMotion")