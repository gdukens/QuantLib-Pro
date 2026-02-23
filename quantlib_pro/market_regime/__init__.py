"""
Market regime detection suite.

Provides:
  - HMM-based regime detection (Bull/Bear/Sideways)
  - Volatility regime classification (Low/Medium/High)
  - Trend regime detection (Uptrend/Downtrend/Sideways)
"""

from .hmm_detector import (
    RegimeType,
    RegimeResult,
    detect_regimes_hmm,
    detect_regimes_fast,
)

from .volatility_regime import (
    VolatilityRegime,
    VolatilityRegimeResult,
    detect_volatility_regimes_percentile,
    detect_volatility_regimes_adaptive,
    detect_volatility_breakout,
)

from .trend_regime import (
    TrendRegime,
    TrendRegimeResult,
    detect_trend_regimes_ma,
    detect_trend_regimes_adx,
    detect_trend_regimes_momentum,
)

__all__ = [
    # HMM regime detection
    "RegimeType",
    "RegimeResult",
    "detect_regimes_hmm",
    "detect_regimes_fast",
    # Volatility regimes
    "VolatilityRegime",
    "VolatilityRegimeResult",
    "detect_volatility_regimes_percentile",
    "detect_volatility_regimes_adaptive",
    "detect_volatility_breakout",
    # Trend regimes
    "TrendRegime",
    "TrendRegimeResult",
    "detect_trend_regimes_ma",
    "detect_trend_regimes_adx",
    "detect_trend_regimes_momentum",
]
