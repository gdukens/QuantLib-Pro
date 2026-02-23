"""Smoke test for quantlib_pro.portfolio module."""

import numpy as np
import pandas as pd

from quantlib_pro.portfolio import (
    max_sharpe_portfolio,
    min_volatility_portfolio,
    target_return_portfolio,
    efficient_frontier,
    risk_parity_portfolio,
    risk_budgeting_portfolio,
    black_litterman,
    create_absolute_view,
    create_relative_view,
)


def test_portfolio_optimization():
    """Test mean-variance optimization."""
    print("\n=== Portfolio Optimization Tests ===\n")
    
    # Sample data: 3 assets
    tickers = ["AAPL", "MSFT", "GOOGL"]
    expected_returns = pd.Series([0.12, 0.10, 0.14], index=tickers)
    
    cov_matrix = pd.DataFrame(
        [
            [0.04, 0.01, 0.02],
            [0.01, 0.03, 0.015],
            [0.02, 0.015, 0.05],
        ],
        index=tickers,
        columns=tickers,
    )
    
    # Test 1: Max Sharpe portfolio
    print("1. Max Sharpe Portfolio")
    max_sharpe = max_sharpe_portfolio(
        expected_returns, cov_matrix, risk_free_rate=0.02
    )
    print(max_sharpe.summary())
    assert max_sharpe.weights.sum() == 1.0, "Weights must sum to 1"
    assert np.all(max_sharpe.weights >= 0), "No short selling by default"
    print("✓ Max Sharpe portfolio computed\n")
    
    # Test 2: Min Volatility portfolio
    print("2. Min Volatility Portfolio")
    min_vol = min_volatility_portfolio(expected_returns, cov_matrix)
    print(min_vol.summary())
    assert min_vol.weights.sum() == 1.0
    assert min_vol.volatility <= max_sharpe.volatility, "Min vol should have lower volatility"
    print("✓ Min volatility portfolio computed\n")
    
    # Test 3: Target return portfolio
    print("3. Target Return Portfolio (11%)")
    target = target_return_portfolio(expected_returns, cov_matrix, target_return=0.11)
    print(target.summary())
    assert np.isclose(target.expected_return, 0.11, atol=1e-3)
    print("✓ Target return portfolio computed\n")
    
    # Test 4: Efficient frontier
    print("4. Efficient Frontier (20 portfolios)")
    frontier = efficient_frontier(expected_returns, cov_matrix, n_points=20)
    print(f"Constructed {len(frontier)} portfolios on efficient frontier")
    assert len(frontier) > 0, "Frontier should have at least 1 portfolio"
    # Verify frontier is sorted by return
    returns = [p.expected_return for p in frontier]
    assert returns == sorted(returns), "Frontier should be sorted by return"
    print("✓ Efficient frontier constructed\n")


def test_risk_parity():
    """Test risk parity allocation."""
    print("\n=== Risk Parity Tests ===\n")
    
    tickers = ["Stocks", "Bonds", "Commodities"]
    cov_matrix = pd.DataFrame(
        [
            [0.04, 0.01, 0.005],
            [0.01, 0.01, 0.002],
            [0.005, 0.002, 0.03],
        ],
        index=tickers,
        columns=tickers,
    )
    
    # Test 1: Equal risk contribution
    print("1. Risk Parity Portfolio")
    rp = risk_parity_portfolio(cov_matrix, tickers=tickers)
    print(f"Risk Parity Weights: {rp.to_dict()}")
    print(f"Volatility: {rp.volatility:.4f}")
    assert rp.weights.sum() == 1.0
    assert np.all(rp.weights > 0), "All weights should be positive"
    print("✓ Risk parity portfolio computed\n")
    
    # Test 2: Custom risk budgeting (60/30/10)
    print("2. Risk Budgeting Portfolio (60/30/10)")
    budgets = np.array([0.6, 0.3, 0.1])
    rb = risk_budgeting_portfolio(cov_matrix, budgets, tickers=tickers)
    print(f"Risk Budget Weights: {rb.to_dict()}")
    print(f"Volatility: {rb.volatility:.4f}")
    assert rb.weights.sum() == 1.0
    print("✓ Risk budgeting portfolio computed\n")


def test_black_litterman():
    """Test Black-Litterman model."""
    print("\n=== Black-Litterman Tests ===\n")
    
    # Market data
    tickers = ["AAPL", "MSFT", "GOOGL"]
    market_weights = pd.Series([0.4, 0.35, 0.25], index=tickers)
    
    cov_matrix = pd.DataFrame(
        [
            [0.04, 0.01, 0.02],
            [0.01, 0.03, 0.015],
            [0.02, 0.015, 0.05],
        ],
        index=tickers,
        columns=tickers,
    )
    
    # Test 1: No views (equilibrium)
    print("1. Black-Litterman with No Views")
    posterior_ret, posterior_cov = black_litterman(
        cov_matrix, market_weights, views=[], risk_aversion=2.5
    )
    print(f"Implied equilibrium returns: {posterior_ret}")
    assert len(posterior_ret) == 3
    print("✓ Equilibrium returns computed\n")
    
    # Test 2: Absolute view on AAPL
    print("2. Black-Litterman with Absolute View (AAPL = 15%)")
    view1 = create_absolute_view(0, expected_return=0.15, confidence=0.8)
    posterior_ret_v1, _ = black_litterman(
        cov_matrix, market_weights, views=[view1], risk_aversion=2.5
    )
    print(f"Posterior returns with view: {posterior_ret_v1}")
    assert posterior_ret_v1[0] > posterior_ret[0], "AAPL return should increase"
    print("✓ Absolute view incorporated\n")
    
    # Test 3: Relative view (AAPL outperforms MSFT by 5%)
    print("3. Black-Litterman with Relative View (AAPL > MSFT by 5%)")
    view2 = create_relative_view(0, 1, outperformance=0.05, confidence=0.6)
    posterior_ret_v2, _ = black_litterman(
        cov_matrix, market_weights, views=[view2], risk_aversion=2.5
    )
    print(f"Posterior returns with relative view: {posterior_ret_v2}")
    assert (posterior_ret_v2[0] - posterior_ret_v2[1]) > (posterior_ret[0] - posterior_ret[1])
    print("✓ Relative view incorporated\n")


def main():
    """Run all smoke tests."""
    print("\n" + "="*60)
    print("PORTFOLIO OPTIMIZATION SUITE — SMOKE TESTS")
    print("="*60)
    
    try:
        test_portfolio_optimization()
        test_risk_parity()
        test_black_litterman()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise


if __name__ == "__main__":
    main()
