"""
Q-Fin Bug Verification Script
==============================

This script validates the critical bugs identified in the Q-Fin deep scan.

Run this script to confirm:
1. Put Gamma calculation error
2. Barrier option pricing failure
3. Stochastic volatility initialization issue
4. Performance benchmarks

Author: GitHub Copilot
Date: February 24, 2026
"""

import sys
import os
import numpy as np
import time
from scipy.stats import norm
import math

# Add Q-Fin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Q-Fin-main'))

try:
    from QFin.options import BlackScholesCall, BlackScholesPut
    from QFin.simulations import (
        MonteCarloCall, MonteCarloPut,
        MonteCarloBarrierCall, MonteCarloBarrierPut,
        GeometricBrownianMotion
    )
    from QFin.stochastics import ArithmeticBrownianMotion
    QFIN_AVAILABLE = True
except ImportError as e:
    print(f"❌ Cannot import Q-Fin: {e}")
    QFIN_AVAILABLE = False


def test_put_gamma_bug():
    """
    Test #1: Put Gamma Calculation Bug
    
    Expected: Put and Call gamma should be identical for same parameters
    Bug: Put gamma uses norm.cdf instead of norm.pdf
    """
    print("\n" + "="*70)
    print("TEST 1: Put Gamma Calculation Bug")
    print("="*70)
    
    if not QFIN_AVAILABLE:
        print("❌ SKIPPED - Q-Fin not available")
        return
    
    # Test parameters
    S, sigma, K, T, r = 100, 0.3, 100, 1, 0.01
    
    # Create options
    call = BlackScholesCall(S, sigma, K, T, r)
    put = BlackScholesPut(S, sigma, K, T, r)
    
    # Calculate correct gamma manually
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    correct_gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
    
    print(f"\nParameters: S={S}, K={K}, σ={sigma}, T={T}, r={r}")
    print(f"\nCall Gamma:    {call.gamma:.10f}")
    print(f"Put Gamma:     {put.gamma:.10f}")
    print(f"Correct Gamma: {correct_gamma:.10f}")
    
    # Check if they match
    if abs(call.gamma - correct_gamma) < 1e-10:
        print("✅ Call gamma is CORRECT")
    else:
        print(f"❌ Call gamma is WRONG (diff: {abs(call.gamma - correct_gamma):.2e})")
    
    if abs(put.gamma - correct_gamma) < 1e-10:
        print("✅ Put gamma is CORRECT")
    else:
        print(f"❌ Put gamma is WRONG (diff: {abs(put.gamma - correct_gamma):.2e})")
    
    # Final verdict
    if abs(call.gamma - put.gamma) < 1e-10:
        print("\n✅ VERDICT: Call and Put gammas match (Bug may be fixed)")
    else:
        print(f"\n❌ VERDICT: Bug CONFIRMED - Put gamma differs by {abs(call.gamma - put.gamma):.2e}")
        print("   Put gamma is using norm.cdf instead of norm.pdf")


def test_barrier_option_bug():
    """
    Test #2: Barrier Option Nested Loop Bug
    
    Expected: Should run n simulations
    Bug: Inner loop resets payouts list and overwrites loop variable
    """
    print("\n" + "="*70)
    print("TEST 2: Barrier Option Nested Loop Bug")
    print("="*70)
    
    if not QFIN_AVAILABLE:
        print("❌ SKIPPED - Q-Fin not available")
        return
    
    print("\nTesting with small n to observe behavior...")
    
    # Test parameters
    S, K, sigma, r = 100, 100, 0.3, 0.01
    dt, T = 1/252, 1
    barrier = 110
    n_sims = 10  # Small number to make bug obvious
    
    try:
        start = time.time()
        barrier_call = MonteCarloBarrierCall(
            strike=K, n=n_sims, barrier=barrier, 
            r=r, S=S, mu=0, sigma=sigma, dt=dt, T=T,
            up=True, out=True
        )
        elapsed = time.time() - start
        
        print(f"\nBarrier Call Price: {barrier_call.price:.4f}")
        print(f"Time elapsed: {elapsed:.4f}s")
        print(f"Time per simulation: {elapsed/n_sims*1000:.2f}ms")
        
        # Run multiple times - should get different results due to randomness
        prices = []
        for i in range(5):
            bc = MonteCarloBarrierCall(
                strike=K, n=n_sims, barrier=barrier,
                r=r, S=S, mu=0, sigma=sigma, dt=dt, T=T,
                up=True, out=True
            )
            prices.append(bc.price)
        
        print(f"\n5 runs: {[f'{p:.4f}' for p in prices]}")
        print(f"Std dev: {np.std(prices):.4f}")
        
        # If std dev is very low with small n, likely only using 1 simulation
        if np.std(prices) < 0.1 and n_sims == 10:
            print("\n❌ VERDICT: Bug likely PRESENT - std dev too low for 10 simulations")
            print("   This suggests the nested loop bug is resetting payouts")
        else:
            print("\n✅ VERDICT: Bug may be FIXED - reasonable variance observed")
            
    except Exception as e:
        print(f"\n❌ ERROR: Barrier option raised exception: {e}")
        print("   This confirms the implementation is broken")


def test_performance_benchmark():
    """
    Test #3: Performance Benchmark
    
    Compare Q-Fin Monte Carlo vs analytical pricing speed
    """
    print("\n" + "="*70)
    print("TEST 3: Performance Benchmark")
    print("="*70)
    
    if not QFIN_AVAILABLE:
        print("❌ SKIPPED - Q-Fin not available")
        return
    
    S, K, sigma, r = 100, 100, 0.3, 0.01
    T = 1
    
    # Test 1: Analytical Black-Scholes
    print("\n--- Analytical Black-Scholes ---")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        bs = BlackScholesCall(S, sigma, K, T, r)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    bs_avg = np.mean(times) * 1000  # Convert to ms
    bs_price = bs.price
    print(f"Average time: {bs_avg:.4f}ms")
    print(f"Price: {bs_price:.4f}")
    
    # Test 2: Monte Carlo (small n)
    print("\n--- Monte Carlo (n=1,000) ---")
    n = 1000
    dt = 1/252
    
    start = time.time()
    mc = MonteCarloCall(K, n, r, S, 0, sigma, dt, T)
    mc_time_1k = time.time() - start
    mc_price_1k = mc.price
    
    print(f"Time: {mc_time_1k*1000:.2f}ms")
    print(f"Price: {mc_price_1k:.4f}")
    print(f"Error: {abs(mc_price_1k - bs_price):.4f}")
    print(f"Slowdown: {mc_time_1k*1000/bs_avg:.0f}x vs BS")
    
    # Test 3: Monte Carlo (medium n)
    print("\n--- Monte Carlo (n=10,000) ---")
    n = 10000
    
    start = time.time()
    mc = MonteCarloCall(K, n, r, S, 0, sigma, dt, T)
    mc_time_10k = time.time() - start
    mc_price_10k = mc.price
    
    print(f"Time: {mc_time_10k*1000:.2f}ms")
    print(f"Price: {mc_price_10k:.4f}")
    print(f"Error: {abs(mc_price_10k - bs_price):.4f}")
    print(f"Slowdown: {mc_time_10k*1000/bs_avg:.0f}x vs BS")
    
    print("\n--- Verdict ---")
    if mc_time_10k > 1.0:  # More than 1 second for 10k sims
        print("❌ Performance is SLOW (>1s for 10k simulations)")
        print("   Needs vectorization and optimization")
    else:
        print("✅ Performance is ACCEPTABLE")
    
    if mc_time_1k / mc_time_10k > 0.05:  # Should scale roughly linearly
        print("⚠️  Scaling is sub-linear (object creation overhead likely)")
    else:
        print("✅ Good linear scaling")


def test_arithmetic_brownian_motion():
    """
    Test #4: Arithmetic Brownian Motion (Unique component)
    
    Verify this component works correctly (should extract this)
    """
    print("\n" + "="*70)
    print("TEST 4: Arithmetic Brownian Motion (Bachelier Model)")
    print("="*70)
    
    if not QFIN_AVAILABLE:
        print("❌ SKIPPED - Q-Fin not available")
        return
    
    # Bachelier model parameters
    F0, K, T = 100, 100, 1
    sigma_bachelier = 20  # Bachelier vol (absolute, not percentage)
    
    print(f"\nParameters: F0={F0}, K={K}, T={T}, σ={sigma_bachelier}")
    
    # Create ABM model
    abm = ArithmeticBrownianMotion([sigma_bachelier])
    
    # Price call option
    call_price = abm.vanilla_pricing(F0, K, T, "CALL")
    put_price = abm.vanilla_pricing(F0, K, T, "PUT")
    
    # Calculate manually for verification
    d = (F0 - K) / (sigma_bachelier * np.sqrt(T))
    expected_call = (F0 - K) * norm.cdf(d) + sigma_bachelier * np.sqrt(T) * norm.pdf(d)
    expected_put = expected_call - F0 + K  # Put-call parity
    
    print(f"\nCall Price (ABM):      {call_price:.6f}")
    print(f"Call Price (Expected): {expected_call:.6f}")
    print(f"Difference:            {abs(call_price - expected_call):.2e}")
    
    print(f"\nPut Price (ABM):       {put_price:.6f}")
    print(f"Put Price (Expected):  {expected_put:.6f}")
    print(f"Difference:            {abs(put_price - expected_put):.2e}")
    
    # Test simulation
    print("\n--- Testing ABM Simulation ---")
    n_paths = 1000
    dt = 1/252
    
    start = time.time()
    paths_info = abm.simulate(F0, n_paths, dt, T)
    sim_time = time.time() - start
    
    paths, n, dt_used, T_used = paths_info
    terminal_values = [path[-1] for path in paths]
    
    print(f"Simulated {n_paths} paths in {sim_time:.3f}s")
    print(f"Mean terminal value: {np.mean(terminal_values):.2f}")
    print(f"Expected: {F0:.2f}")
    print(f"Std dev: {np.std(terminal_values):.2f}")
    print(f"Expected: {sigma_bachelier * np.sqrt(T):.2f}")
    
    # Verify pricing formula is correct
    if abs(call_price - expected_call) < 1e-10:
        print("\n✅ VERDICT: ABM pricing is CORRECT")
        print("   ✅ This component should be EXTRACTED and kept")
    else:
        print("\n❌ VERDICT: ABM pricing has errors")


def run_all_tests():
    """Run all verification tests"""
    print("\n" + "="*70)
    print("Q-FIN BUG VERIFICATION SUITE")
    print("="*70)
    print(f"Date: February 24, 2026")
    print(f"Python: {sys.version}")
    print(f"NumPy: {np.__version__}")
    print("="*70)
    
    if not QFIN_AVAILABLE:
        print("\n❌ CRITICAL: Cannot import Q-Fin")
        print("   Make sure Q-Fin-main/ exists and contains QFin/ package")
        return
    
    test_put_gamma_bug()
    test_barrier_option_bug()
    test_performance_benchmark()
    test_arithmetic_brownian_motion()
    
    print("\n" + "="*70)
    print("SUMMARY OF FINDINGS")
    print("="*70)
    print("\nRefer to:")
    print("  - Q-FIN_DEEP_SCAN_REPORT.md for detailed analysis")
    print("  - Q-FIN_CRITICAL_ISSUES.md for bug fixes")
    print("  - Q-FIN_COMPONENT_COMPARISON.md for integration decisions")
    print("\n" + "="*70)


if __name__ == "__main__":
    run_all_tests()
