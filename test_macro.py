"""
Week 9: Macro analysis smoke tests.
"""

import numpy as np
import pandas as pd
import pytest

from quantlib_pro.macro import (
    # Correlation
    rolling_correlation,
    correlation_regime,
    compute_correlation_metrics,
    detect_correlation_breakdowns,
    correlation_contagion_score,
    eigenvalue_concentration,
    make_psd,
    simulate_correlation_shock,
    cross_asset_correlation,
    # Economic
    MacroRegime,
    detect_macro_regime,
    growth_momentum,
    inflation_gap,
    real_interest_rate,
    yield_curve_slope,
    sahm_rule_indicator,
    leading_economic_index,
    diffusion_index,
    taylor_rule_rate,
    recession_probability,
    normalize_indicator,
    # Sentiment
    SentimentRegime,
    vix_sentiment_level,
    put_call_ratio_sentiment,
    aaii_sentiment_score,
    fear_greed_index,
    contrarian_signal,
    advance_decline_line,
    mcclellan_oscillator,
    new_high_low_ratio,
    skew_sentiment,
    vix_term_structure_slope,
    sentiment_divergence,
    aggregate_sentiment_score,
)


# === Correlation Tests ===

def test_rolling_correlation():
    """Test rolling correlation computation."""
    np.random.seed(42)
    returns = pd.DataFrame(
        np.random.randn(100, 3),
        columns=['A', 'B', 'C']
    )
    
    corr_matrices = rolling_correlation(returns, window=30)
    
    assert len(corr_matrices) == 71  # 100 - 30 + 1
    assert corr_matrices[0].shape == (3, 3)
    # Check diagonal is 1
    assert np.allclose(np.diag(corr_matrices[0]), 1.0)


def test_correlation_regime():
    """Test correlation regime classification."""
    assert correlation_regime(0.2) == 'calm'
    assert correlation_regime(0.5) == 'stress'
    assert correlation_regime(0.8) == 'crisis'


def test_compute_correlation_metrics():
    """Test correlation metrics extraction."""
    corr = pd.DataFrame([
        [1.0, 0.3, 0.4],
        [0.3, 1.0, 0.5],
        [0.4, 0.5, 1.0],
    ], columns=['A', 'B', 'C'], index=['A', 'B', 'C'])
    
    metrics = compute_correlation_metrics(corr, timestamp=100.0)
    
    assert abs(metrics.avg_correlation - 0.4) < 0.01
    assert metrics.regime in ['calm', 'stress', 'crisis']
    assert len(metrics.eigenvalues) == 3
    assert 0 < metrics.diversification_ratio < 1


def test_detect_correlation_breakdowns():
    """Test correlation breakdown detection."""
    # Create synthetic correlation history with a jump
    np.random.seed(42)
    corr_matrices = []
    
    for i in range(50):
        if i < 30:
            base_corr = 0.3
        else:
            base_corr = 0.8  # Breakdown event
        
        corr = pd.DataFrame(
            np.full((3, 3), base_corr),
            columns=['A', 'B', 'C']
        )
        np.fill_diagonal(corr.values, 1.0)
        corr_matrices.append(corr)
    
    breakdowns = detect_correlation_breakdowns(corr_matrices, threshold=0.3)
    
    # Should detect breakdown around index 30
    assert len(breakdowns) > 0
    assert 28 < breakdowns[0] < 32


def test_correlation_contagion_score():
    """Test contagion score calculation."""
    high_corr = pd.DataFrame(
        np.full((5, 5), 0.9),
        columns=list('ABCDE')
    )
    np.fill_diagonal(high_corr.values, 1.0)
    
    score = correlation_contagion_score(high_corr, baseline_corr=0.3)
    
    # High correlation should give high contagion score
    assert score > 0.7


def test_eigenvalue_concentration():
    """Test eigenvalue concentration metric."""
    # Highly concentrated eigenvalues
    eigvals = np.array([8.0, 1.0, 0.5, 0.3, 0.2])
    
    concentration = eigenvalue_concentration(eigvals, top_k=1)
    
    # First eigenvalue dominates
    assert concentration > 0.7


def test_make_psd():
    """Test PSD correction."""
    # Create non-PSD matrix
    A = np.array([
        [1.0, 0.9, 0.9],
        [0.9, 1.0, 0.9],
        [0.9, 0.9, 1.0],
    ])
    # Make it non-PSD by subtracting a bit
    A[0, 1] = 1.5  # Violates PSD
    
    psd = make_psd(A)
    
    # Check eigenvalues are positive
    eigvals = np.linalg.eigvalsh(psd)
    assert np.all(eigvals >= 0)


def test_simulate_correlation_shock():
    """Test correlation shock simulation."""
    shocked = simulate_correlation_shock(
        base_corr=0.3,
        shock_intensity=0.8,
        n_assets=5,
    )
    
    assert shocked.shape == (5, 5)
    assert np.allclose(np.diag(shocked), 1.0)
    # Shocked correlations should be higher
    off_diag = shocked[0, 1]
    assert off_diag > 0.3


def test_cross_asset_correlation():
    """Test cross-asset correlation."""
    np.random.seed(42)
    returns = pd.DataFrame(
        np.random.randn(100, 3),
        columns=['A', 'B', 'C']
    )
    
    corr_series = cross_asset_correlation(returns, 'A', 'B', window=20)
    
    assert len(corr_series) == 100
    # First 19 should be NaN
    assert pd.isna(corr_series[0])
    # Rest should be valid
    assert not pd.isna(corr_series[30])


# === Economic Tests ===

def test_detect_macro_regime():
    """Test macro regime detection."""
    # Expansion
    regime = detect_macro_regime(gdp_growth=3.0, unemployment_change=-0.2, pmi=55)
    assert regime == MacroRegime.EXPANSION
    
    # Recession
    regime = detect_macro_regime(gdp_growth=-1.0, unemployment_change=0.5, pmi=45)
    assert regime == MacroRegime.RECESSION


def test_growth_momentum():
    """Test growth momentum calculation."""
    gdp = pd.Series([2.0, 2.2, 2.5, 2.8, 3.0, 2.9, 2.7])
    
    momentum = growth_momentum(gdp, window=2)
    
    assert len(momentum) == len(gdp)
    # First values should be NaN
    assert pd.isna(momentum[0])


def test_inflation_gap():
    """Test inflation gap."""
    gap = inflation_gap(actual_inflation=3.5, target_inflation=2.0)
    assert gap == 1.5


def test_real_interest_rate():
    """Test real rate calculation."""
    real_rate = real_interest_rate(nominal_rate=5.0, inflation=2.0)
    assert real_rate == 3.0


def test_yield_curve_slope():
    """Test yield curve slope."""
    slope = yield_curve_slope(long_rate=4.0, short_rate=3.5)
    assert slope == 0.5
    
    # Inverted
    slope_inv = yield_curve_slope(long_rate=3.0, short_rate=3.5)
    assert slope_inv < 0


def test_sahm_rule_indicator():
    """Test Sahm Rule recession indicator."""
    # Stable unemployment
    stable = pd.Series([4.0] * 20)
    assert sahm_rule_indicator(stable, window=3, threshold=0.5) == False
    
    # Rising unemployment (potential recession signal)
    rising = pd.Series([4.0] * 12 + [4.1, 4.3, 4.5, 4.7, 4.9, 5.0, 5.1, 5.2])
    result = sahm_rule_indicator(rising, window=3, threshold=0.5)
    # Should trigger given the rise > 0.5pp
    assert result == True


def test_leading_economic_index():
    """Test LEI calculation."""
    indicators = {
        'pmi': 0.5,
        'building_permits': 0.3,
        'jobless_claims': -0.4,
    }
    
    lei = leading_economic_index(indicators)
    
    assert -1 < lei < 1


def test_diffusion_index():
    """Test diffusion index."""
    indicators = pd.DataFrame({
        'A': [1, 2, 3, 2, 1],
        'B': [-1, 0, 1, 2, 3],
        'C': [0, 1, 2, 3, 4],
    })
    
    diffusion = diffusion_index(indicators, threshold=1.0)
    
    assert len(diffusion) == 5
    assert 0 <= diffusion.iloc[-1] <= 100


def test_taylor_rule_rate():
    """Test Taylor Rule."""
    rate = taylor_rule_rate(
        neutral_rate=2.0,
        inflation=3.0,
        target_inflation=2.0,
        output_gap=1.0,
        alpha=0.5,
        beta=0.5,
    )
    
    # Should be positive and reasonable
    assert 0 < rate < 10


def test_recession_probability():
    """Test recession probability."""
    # Low risk
    prob_low = recession_probability(
        yield_spread=100,
        unemployment_change=-0.1,
        pmi=55,
    )
    assert prob_low < 0.3
    
    # High risk
    prob_high = recession_probability(
        yield_spread=-50,
        unemployment_change=0.6,
        pmi=42,
    )
    assert prob_high > 0.5


def test_normalize_indicator():
    """Test indicator normalization."""
    series = pd.Series([1, 2, 3, 4, 5])
    
    # Z-score
    zscore = normalize_indicator(series, method='zscore')
    assert abs(zscore.mean()) < 0.01
    assert abs(zscore.std() - 1.0) < 0.01
    
    # Min-max
    minmax = normalize_indicator(series, method='minmax')
    assert minmax.min() == 0.0
    assert minmax.max() == 1.0


# === Sentiment Tests ===

def test_vix_sentiment_level():
    """Test VIX sentiment classification."""
    assert vix_sentiment_level(10) == SentimentRegime.EXTREME_GREED
    assert vix_sentiment_level(15) == SentimentRegime.GREED
    assert vix_sentiment_level(18) == SentimentRegime.NEUTRAL
    assert vix_sentiment_level(25) == SentimentRegime.FEAR
    assert vix_sentiment_level(35) == SentimentRegime.EXTREME_FEAR


def test_put_call_ratio_sentiment():
    """Test put/call ratio sentiment."""
    assert put_call_ratio_sentiment(0.5) == SentimentRegime.EXTREME_GREED
    assert put_call_ratio_sentiment(0.9) == SentimentRegime.NEUTRAL
    assert put_call_ratio_sentiment(1.3) == SentimentRegime.EXTREME_FEAR


def test_aaii_sentiment_score():
    """Test AAII score."""
    score = aaii_sentiment_score(bull_pct=50, bear_pct=30)
    assert score == 0.2


def test_fear_greed_index():
    """Test fear/greed index."""
    # Fearful market
    index_fear = fear_greed_index(
        vix=30,
        put_call_ratio=1.2,
        advance_decline=0.8,
        new_high_low=0.3,
    )
    assert index_fear < 50
    
    # Greedy market
    index_greed = fear_greed_index(
        vix=12,
        put_call_ratio=0.7,
        advance_decline=1.5,
        new_high_low=3.0,
    )
    assert index_greed > 50


def test_contrarian_signal():
    """Test contrarian signals."""
    # Extreme greed → sell
    assert contrarian_signal(0.9, extreme_threshold=0.8) == 'sell'
    
    # Extreme fear → buy
    assert contrarian_signal(0.1, extreme_threshold=0.8) == 'buy'
    
    # Neutral
    assert contrarian_signal(0.5, extreme_threshold=0.8) == 'neutral'


def test_advance_decline_line():
    """Test A/D line."""
    advances = pd.Series([100, 120, 110, 130, 125])
    declines = pd.Series([50, 60, 70, 55, 65])
    
    ad_line = advance_decline_line(advances, declines)
    
    assert len(ad_line) == 5
    # Should be cumulative
    assert ad_line.iloc[-1] > ad_line.iloc[0]


def test_mcclellan_oscillator():
    """Test McClellan Oscillator."""
    np.random.seed(42)
    advances = pd.Series(100 + 10 * np.random.randn(50))
    declines = pd.Series(80 + 10 * np.random.randn(50))
    
    osc = mcclellan_oscillator(advances, declines, fast=10, slow=20)
    
    assert len(osc) == 50


def test_new_high_low_ratio():
    """Test new high/low ratio."""
    highs = pd.Series([10, 12, 15, 20, 18])
    lows = pd.Series([5, 4, 3, 2, 3])
    
    ratio = new_high_low_ratio(highs, lows, smooth=2)
    
    assert len(ratio) == 5
    # Ratio should be > 1 (more highs than lows)
    assert ratio.iloc[-1] > 1


def test_skew_sentiment():
    """Test skew-based sentiment."""
    assert skew_sentiment(-6) == SentimentRegime.EXTREME_GREED
    assert skew_sentiment(0) == SentimentRegime.NEUTRAL
    assert skew_sentiment(6) == SentimentRegime.EXTREME_FEAR


def test_vix_term_structure_slope():
    """Test VIX term structure."""
    assert vix_term_structure_slope(vix_spot=20, vix_3m=15) == 'backwardation'
    assert vix_term_structure_slope(vix_spot=15, vix_3m=20) == 'contango'


def test_sentiment_divergence():
    """Test sentiment divergence."""
    price = pd.Series([100, 105, 110, 115, 120])
    sentiment = pd.Series([50, 52, 48, 45, 42])  # Falling while price rises
    
    div = sentiment_divergence(price, sentiment, window=2)
    
    # Bearish divergence (positive)
    assert div.iloc[-1] > 0


def test_aggregate_sentiment_score():
    """Test aggregate sentiment."""
    indicators = {
        'vix': 0.3,  # Fearful
        'pc_ratio': 0.4,  # Fearful
        'ad_line': 0.6,  # Bullish
    }
    
    score = aggregate_sentiment_score(indicators)
    
    assert 0 <= score <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
