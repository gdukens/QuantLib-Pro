"""Smoke test for quantlib_pro.market_regime module."""

import numpy as np
import pandas as pd

from quantlib_pro.market_regime import (
    detect_regimes_hmm,
    detect_regimes_fast,
    detect_volatility_regimes_percentile,
    detect_volatility_regimes_adaptive,
    detect_volatility_breakout,
    detect_trend_regimes_ma,
    detect_trend_regimes_adx,
    detect_trend_regimes_momentum,
)


def generate_synthetic_prices(n: int = 500, trend: str = 'mixed') -> pd.Series:
    """Generate synthetic price data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=n, freq='D')
    
    if trend == 'bull':
        drift = 0.0005
        volatility = 0.015
    elif trend == 'bear':
        drift = -0.0005
        volatility = 0.015
    elif trend == 'sideways':
        drift = 0.0
        volatility = 0.01
    else:  # mixed
        # Create regime-switching data
        regime_1 = np.random.normal(0.001, 0.01, n // 3)
        regime_2 = np.random.normal(-0.001, 0.02, n // 3)
        regime_3 = np.random.normal(0.0, 0.01, n - 2 * (n // 3))
        returns = np.concatenate([regime_1, regime_2, regime_3])
        prices = 100 * np.exp(np.cumsum(returns))
        return pd.Series(prices, index=dates)
    
    returns = np.random.normal(drift, volatility, n)
    prices = 100 * np.exp(np.cumsum(returns))
    return pd.Series(prices, index=dates)


def generate_ohlc_data(n: int = 500) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Generate synthetic OHLC data."""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=n, freq='D')
    
    close = generate_synthetic_prices(n)
    high = close * (1 + np.abs(np.random.normal(0, 0.01, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, n)))
    
    return pd.Series(high.values, index=dates), pd.Series(low.values, index=dates), close


def test_hmm_regime_detection():
    """Test HMM-based regime detection."""
    print("\n=== HMM Regime Detection Tests ===\n")
    
    prices = generate_synthetic_prices(n=500, trend='mixed')
    
    # Test 1: HMM with 3 regimes (Bull/Sideways/Bear)
    print("1. HMM Regime Detection (3 regimes)")
    result = detect_regimes_hmm(prices, n_regimes=3, random_state=42)
    print(f"Detected regimes: {result.regime_names}")
    print(f"Current regime: {result.get_current_regime()}")
    print(f"Transition matrix shape: {result.transition_matrix.shape}")
    print(f"Number of observations: {len(result.regimes)}")
    assert len(result.regimes) > 0, "Should detect regimes"
    assert len(result.regime_names) == 3, "Should have 3 regime names"
    assert result.transition_matrix.shape == (3, 3), "3x3 transition matrix"
    print("✓ HMM regime detection successful\n")
    
    # Test 2: Fast regime detection (threshold-based)
    print("2. Fast Regime Detection (3 regimes)")
    result_fast = detect_regimes_fast(prices, n_regimes=3)
    print(f"Detected regimes: {result_fast.regime_names}")
    print(f"Current regime: {result_fast.get_current_regime()}")
    print(f"Number of observations: {len(result_fast.regimes)}")
    assert len(result_fast.regimes) > 0
    print("✓ Fast regime detection successful\n")
    
    # Test 3: Convert to DataFrame
    print("3. Convert to DataFrame")
    df = result.to_dataframe()
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    assert 'regime' in df.columns
    assert 'regime_id' in df.columns
    print("✓ DataFrame conversion successful\n")


def test_volatility_regime_detection():
    """Test volatility regime detection."""
    print("\n=== Volatility Regime Detection Tests ===\n")
    
    prices = generate_synthetic_prices(n=500)
    
    # Test 1: Percentile-based (3 regimes)
    print("1. Percentile-Based Volatility Regimes (3 regimes)")
    result = detect_volatility_regimes_percentile(prices, n_regimes=3, method='realized')
    print(f"Detected regimes: {result.regime_names}")
    print(f"Current regime: {result.get_current_regime()}")
    print(f"Thresholds: {result.thresholds}")
    print(f"Mean realized vol: {result.realized_vol.mean():.4f}")
    assert len(result.regimes) > 0
    assert len(result.regime_names) == 3
    print("✓ Percentile-based detection successful\n")
    
    # Test 2: EWMA method
    print("2. EWMA Volatility Regimes")
    result_ewma = detect_volatility_regimes_percentile(prices, n_regimes=3, method='ewma')
    print(f"Current regime: {result_ewma.get_current_regime()}")
    assert len(result_ewma.regimes) > 0
    print("✓ EWMA-based detection successful\n")
    
    # Test 3: Adaptive (z-score based)
    print("3. Adaptive Volatility Regimes (z-score)")
    result_adaptive = detect_volatility_regimes_adaptive(prices, lookback=252, z_threshold=1.5)
    print(f"Detected regimes: {result_adaptive.regime_names}")
    print(f"Current regime: {result_adaptive.get_current_regime()}")
    print(f"Thresholds: {result_adaptive.thresholds}")
    assert len(result_adaptive.regimes) > 0
    print("✓ Adaptive detection successful\n")
    
    # Test 4: Volatility breakout
    print("4. Volatility Breakout Detection")
    breakout = detect_volatility_breakout(prices, window=21, multiplier=2.0)
    n_breakouts = breakout.sum()
    print(f"Number of breakouts: {n_breakouts}")
    print(f"Breakout percentage: {100 * n_breakouts / len(breakout):.2f}%")
    assert len(breakout) > 0
    print("✓ Breakout detection successful\n")


def test_trend_regime_detection():
    """Test trend regime detection."""
    print("\n=== Trend Regime Detection Tests ===\n")
    
    prices = generate_synthetic_prices(n=500)
    high, low, close = generate_ohlc_data(n=500)
    
    # Test 1: Moving average crossover
    print("1. MA-Based Trend Detection (50/200)")
    result_ma = detect_trend_regimes_ma(prices, short_window=50, long_window=200)
    print(f"Detected regimes: {result_ma.regime_names}")
    print(f"Current regime: {result_ma.get_current_regime()}")
    print(f"Indicators shape: {result_ma.indicators.shape}")
    regime_counts = pd.Series(result_ma.regimes).value_counts()
    print(f"Regime distribution:\n{regime_counts}")
    assert len(result_ma.regimes) > 0
    print("✓ MA-based detection successful\n")
    
    # Test 2: ADX-based
    print("2. ADX-Based Trend Detection")
    result_adx = detect_trend_regimes_adx(high, low, close, adx_window=14, adx_threshold=25.0)
    print(f"Current regime: {result_adx.get_current_regime()}")
    print(f"Indicators: {result_adx.indicators.columns.tolist()}")
    assert len(result_adx.regimes) > 0
    assert 'adx' in result_adx.indicators.columns
    print("✓ ADX-based detection successful\n")
    
    # Test 3: Momentum-based
    print("3. Momentum-Based Trend Detection")
    result_momentum = detect_trend_regimes_momentum(prices, momentum_window=20, threshold_pct=0.02)
    print(f"Current regime: {result_momentum.get_current_regime()}")
    regime_counts = pd.Series(result_momentum.regimes).value_counts()
    print(f"Regime distribution:\n{regime_counts}")
    assert len(result_momentum.regimes) > 0
    print("✓ Momentum-based detection successful\n")


def main():
    """Run all smoke tests."""
    print("\n" + "="*60)
    print("MARKET REGIME DETECTION SUITE — SMOKE TESTS")
    print("="*60)
    
    try:
        test_hmm_regime_detection()
        test_volatility_regime_detection()
        test_trend_regime_detection()
        
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
