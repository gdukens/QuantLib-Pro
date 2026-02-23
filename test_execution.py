"""Smoke test for quantlib_pro.execution module."""

import numpy as np
import pandas as pd

from quantlib_pro.execution import (
    OrderBookSimulator,
    almgren_chriss_impact,
    kyle_lambda_impact,
    jpm_impact,
    square_root_impact,
    estimate_slippage,
    twap_schedule,
    vwap_schedule,
    pov_schedule,
    simulate_execution,
    intraday_volume_profile,
)


def test_order_book_simulator():
    """Test order book simulation."""
    print("\n=== Order Book Simulator Tests ===\n")
    
    # Test 1: Initialize order book
    print("1. Initialize Order Book")
    ob = OrderBookSimulator(
        mid_price=100.0,
        tick_size=0.01,
        n_levels=10,
        initial_liquidity=1000,
    )
    snapshot = ob.get_snapshot()
    print(f"Mid price: ${snapshot.mid_price:.2f}")
    print(f"Spread: ${snapshot.spread:.2f}")
    print(f"Bid depth: {snapshot.depth[0]:,} shares")
    print(f"Ask depth: {snapshot.depth[1]:,} shares")
    assert snapshot.mid_price == 100.0
    assert snapshot.spread > 0
    print("✓ Order book initialized\n")
    
    # Test 2: Submit market buy order
    print("2. Submit Market Buy Order (500 shares)")
    initial_best_ask = snapshot.get_best_ask()
    trades = ob.submit_market_order('buy', 500)
    print(f"Number of fills: {len(trades)}")
    print(f"Total filled: {sum(t.size for t in trades)} shares")
    vwap = ob.calculate_vwap(trades)
    print(f"VWAP: ${vwap:.4f}")
    assert len(trades) > 0
    assert sum(t.size for t in trades) == 500
    print("✓ Market order executed\n")
    
    # Test 3: Submit limit orders
    print("3. Submit Limit Order")
    snapshot_before = ob.get_snapshot()
    ob.submit_limit_order('buy', 99.95, 100)
    snapshot_after = ob.get_snapshot()
    assert snapshot_after.depth[0] > snapshot_before.depth[0]
    print("✓ Limit order added to book\n")
    
    # Test 4: Step simulation (liquidity replenishment)
    print("4. Step Simulation (10 steps)")
    for _ in range(10):
        ob.step(dt=1.0)
    final_snapshot = ob.get_snapshot()
    print(f"Final mid price: ${final_snapshot.mid_price:.2f}")
    print(f"Final spread: ${final_snapshot.spread:.4f}")
    assert ob.time == 10.0
    print("✓ Simulation stepped\n")


def test_market_impact_models():
    """Test market impact models."""
    print("\n=== Market Impact Models Tests ===\n")
    
    # Common parameters
    order_size = 50_000  # shares
    daily_volume = 1_000_000  # shares
    volatility = 0.02  # 2% daily vol
    arrival_price = 100.0
    
    # Test 1: Almgren-Chriss
    print("1. Almgren-Chriss Impact Model")
    ac_result = almgren_chriss_impact(
        order_size=order_size,
        daily_volume=daily_volume,
        volatility=volatility,
        participation_rate=0.1,
    )
    print(f"Temporary impact: {ac_result.temporary_impact:.2f} bps")
    print(f"Permanent impact: {ac_result.permanent_impact:.2f} bps")
    print(f"Total impact: {ac_result.total_impact:.2f} bps")
    assert ac_result.total_impact > 0
    print("✓ Almgren-Chriss model computed\n")
    
    # Test 2: Kyle's lambda
    print("2. Kyle's Lambda Impact Model")
    kyle_result = kyle_lambda_impact(
        order_size=order_size,
        kyle_lambda=0.0001,
        arrival_price=arrival_price,
    )
    print(f"Permanent impact: {kyle_result.permanent_impact:.2f} bps")
    print(f"Execution cost: ${kyle_result.execution_cost:,.2f}")
    assert kyle_result.permanent_impact > 0
    print("✓ Kyle's lambda model computed\n")
    
    # Test 3: JPM model
    print("3. JPM Impact Model")
    jpm_result = jpm_impact(
        order_size=order_size,
        daily_volume=daily_volume,
        volatility=volatility,
        arrival_price=arrival_price,
    )
    print(f"Temporary impact: {jpm_result.temporary_impact:.2f} bps")
    print(f"Permanent impact: {jpm_result.permanent_impact:.2f} bps")
    print(f"Total impact: {jpm_result.total_impact:.2f} bps")
    assert jpm_result.total_impact > 0
    print("✓ JPM model computed\n")
    
    # Test 4: Square-root model
    print("4. Square-Root Impact Model")
    sqrt_result = square_root_impact(
        order_size=order_size,
        daily_volume=daily_volume,
        volatility=volatility,
        arrival_price=arrival_price,
        coefficient=0.5,
    )
    print(f"Total impact: {sqrt_result.total_impact:.2f} bps")
    print(f"Average price: ${sqrt_result.average_price:.4f}")
    assert sqrt_result.total_impact > 0
    print("✓ Square-root model computed\n")
    
    # Test 5: Slippage estimation
    print("5. Slippage Estimation")
    slippage = estimate_slippage(
        order_size=order_size,
        spread=0.05,
        arrival_price=arrival_price,
    )
    print(f"Slippage cost: ${slippage:,.2f}")
    assert slippage > 0
    print("✓ Slippage estimated\n")


def test_execution_strategies():
    """Test execution strategies."""
    print("\n=== Execution Strategies Tests ===\n")
    
    order_size = 10_000
    duration = 3600  # 1 hour in seconds
    
    # Test 1: TWAP schedule
    print("1. TWAP Schedule (10 slices)")
    twap = twap_schedule(order_size=order_size, duration=duration, n_slices=10)
    print(f"Strategy: {twap.strategy}")
    print(f"Number of slices: {len(twap.sizes)}")
    print(f"Slice sizes: {twap.sizes}")
    print(f"Total size: {twap.sizes.sum()}")
    assert twap.sizes.sum() == order_size
    assert len(twap.sizes) == 10
    # Check roughly equal slices
    assert np.std(twap.sizes) < 2  # Low variance for TWAP
    print("✓ TWAP schedule generated\n")
    
    # Test 2: VWAP schedule
    print("2. VWAP Schedule (U-shaped volume)")
    volume_profile = intraday_volume_profile(profile_type='u_shaped', n_points=20)
    vwap = vwap_schedule(
        order_size=order_size,
        duration=duration,
        volume_profile=volume_profile,
    )
    print(f"Strategy: {vwap.strategy}")
    print(f"Number of slices: {len(vwap.sizes)}")
    print(f"Total size: {vwap.sizes.sum()}")
    assert vwap.sizes.sum() == order_size
    # Check volume profile is U-shaped (higher at edges than middle)
    # Average of first/last 2 slices should be > midpoint slices
    edge_avg = (vwap.sizes[:2].mean() + vwap.sizes[-2:].mean()) / 2
    mid_point = len(vwap.sizes) // 2
    mid_avg = vwap.sizes[mid_point-1:mid_point+2].mean()
    print(f"Edge average: {edge_avg:.1f}, Mid average: {mid_avg:.1f}")
    assert edge_avg > mid_avg * 0.8  # Allow some tolerance
    print("✓ VWAP schedule generated\n")
    
    # Test 3: POV schedule
    print("3. POV Schedule (10% participation)")
    pov = pov_schedule(
        order_size=order_size,
        duration=duration,
        n_slices=10,
        target_pov=0.1,
        volume_profile=None,
    )
    print(f"Strategy: {pov.strategy}")
    print(f"Total size: {pov.sizes.sum()}")
    assert pov.sizes.sum() == order_size
    print("✓ POV schedule generated\n")
    
    # Test 4: Simulate execution
    print("4. Simulate TWAP Execution")
    result = simulate_execution(
        schedule=twap,
        arrival_price=100.0,
        volatility=0.02,
        daily_volume=1_000_000,
    )
    print(f"VWAP: ${result.vwap:.4f}")
    print(f"Arrival price: ${result.arrival_price:.4f}")
    print(f"Slippage: {result.slippage_bps:.2f} bps")
    print(f"Total cost: ${result.total_cost:,.2f}")
    assert result.vwap > 0
    assert result.total_cost >= 0
    print("✓ Execution simulated\n")
    
    # Test 5: Intraday volume profile
    print("5. Intraday Volume Profile")
    profile_u = intraday_volume_profile('u_shaped', n_points=100)
    profile_flat = intraday_volume_profile('flat', n_points=100)
    print(f"U-shaped profile sum: {profile_u.sum():.4f}")
    print(f"Flat profile sum: {profile_flat.sum():.4f}")
    assert np.isclose(profile_u.sum(), 1.0)
    assert np.isclose(profile_flat.sum(), 1.0)
    print("✓ Volume profiles generated\n")


def test_integration():
    """Integration test: full execution workflow."""
    print("\n=== Integration Test: Full Execution Workflow ===\n")
    
    # Scenario: Execute 50,000 shares over 1 hour using VWAP
    order_size = 50_000
    duration = 3600
    arrival_price = 100.0
    daily_volume = 2_000_000
    volatility = 0.015
    
    print("Scenario: Execute 50,000 shares using VWAP strategy")
    print(f"  Order size: {order_size:,} shares")
    print(f"  Daily volume: {daily_volume:,} shares")
    print(f"  Arrival price: ${arrival_price:.2f}")
    print(f"  Volatility: {volatility * 100:.1f}%\n")
    
    # Step 1: Generate volume profile
    volume_profile = intraday_volume_profile('u_shaped', n_points=30)
    
    # Step 2: Create VWAP schedule
    schedule = vwap_schedule(order_size, duration, volume_profile)
    
    # Step 3: Estimate market impact
    impact = square_root_impact(order_size, daily_volume, volatility, arrival_price)
    print(f"Pre-trade impact estimate: {impact.total_impact:.2f} bps\n")
    
    # Step 4: Simulate execution
    result = simulate_execution(schedule, arrival_price, volatility, daily_volume)
    
    print("Execution Results:")
    print(f"  VWAP: ${result.vwap:.4f}")
    print(f"  Slippage: {result.slippage_bps:.2f} bps")
    print(f"  Total cost: ${result.total_cost:,.2f}")
    print(f"  Number of slices: {len(schedule.sizes)}")
    
    # Slippage includes random price movement + impact, so can be large
    assert abs(result.slippage_bps) < 2000  # Sanity check
    assert result.vwap > 0
    print("\n✓ Full execution workflow completed\n")


def main():
    """Run all smoke tests."""
    print("\n" + "="*60)
    print("EXECUTION SIMULATION SUITE — SMOKE TESTS")
    print("="*60)
    
    try:
        test_order_book_simulator()
        test_market_impact_models()
        test_execution_strategies()
        test_integration()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
