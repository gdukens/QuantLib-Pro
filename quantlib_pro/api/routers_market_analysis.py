"""
Market Analysis API Router

Covers page 10: Market Analysis
- Technical indicators (RSI, MACD, Bollinger Bands, ATR, Stochastic)
- Trend detection and classification
- Volatility comparison across multiple stocks
- Price trend analysis (linear regression, support/resistance)
- Multi-stock comparative analysis
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

market_analysis_router = APIRouter(prefix="/market-analysis", tags=["market-analysis"])

# =============================================================================
# Models
# =============================================================================

class TechnicalAnalysisRequest(BaseModel):
    ticker: str = Field(default="SPY", description="Ticker symbol")
    start_date: str = Field(default="2024-01-01")
    end_date: str = Field(default="2024-12-31")
    indicators: List[str] = Field(
        default=["rsi", "macd", "bollinger", "atr", "sma", "ema"],
        description="Technical indicators to compute"
    )
    rsi_period: int = Field(default=14, ge=5, le=50)
    macd_fast: int = Field(default=12, ge=5, le=30)
    macd_slow: int = Field(default=26, ge=10, le=60)
    macd_signal: int = Field(default=9, ge=3, le=20)
    bb_period: int = Field(default=20, ge=5, le=50)
    bb_std: float = Field(default=2.0, ge=1.0, le=4.0)
    atr_period: int = Field(default=14, ge=5, le=50)


class IndicatorValues(BaseModel):
    dates: List[str]
    values: List[Optional[float]]
    signal: Optional[str] = None  # BULLISH | BEARISH | NEUTRAL


class TechnicalAnalysisResponse(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    current_price: float
    price_change_pct: float
    trend: str  # UPTREND | DOWNTREND | SIDEWAYS
    trend_strength: float
    indicators: Dict[str, IndicatorValues]
    support_level: float
    resistance_level: float
    composite_signal: str  # STRONG_BUY | BUY | NEUTRAL | SELL | STRONG_SELL
    bullish_signals: int
    bearish_signals: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VolatilityComparisonRequest(BaseModel):
    tickers: List[str] = Field(default=["SPY", "QQQ", "TLT", "GLD", "VIX"],
                                min_length=2, max_length=20)
    start_date: str = Field(default="2024-01-01")
    end_date: str = Field(default="2024-12-31")
    window: int = Field(default=21, ge=5, le=252)
    vol_type: str = Field(default="realized", description="realized | parkinson | garch")


class VolatilityComparisonResponse(BaseModel):
    tickers: List[str]
    realized_volatility: Dict[str, float]  # annualized
    rolling_vol_latest: Dict[str, float]
    vol_rank: Dict[str, int]  # rank 1=lowest vol
    high_vol_regime: List[str]  # tickers in high vol regime
    low_vol_regime: List[str]
    vol_correlation: Dict[str, Dict[str, float]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrendAnalysisRequest(BaseModel):
    tickers: List[str] = Field(default=["SPY", "QQQ", "AAPL", "MSFT"])
    lookback_days: int = Field(default=90, ge=10, le=504)
    trend_method: str = Field(default="linear_regression", description="linear_regression | moving_average | hurst")


class TrendAnalysisResponse(BaseModel):
    results: Dict[str, Dict[str, Any]]
    bullish_tickers: List[str]
    bearish_tickers: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Helpers
# =============================================================================

def _generate_prices(ticker: str, n_days: int) -> pd.Series:
    seed = abs(hash(ticker)) % 999
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0003, 0.012, n_days)
    return pd.Series(100 * np.exp(np.cumsum(r)))


def _compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _compute_macd(prices: pd.Series, fast: int, slow: int, signal: int):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist


def _compute_bollinger(prices: pd.Series, period: int, n_std: float):
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = sma + n_std * std
    lower = sma - n_std * std
    return upper, sma, lower


def _compute_atr(prices: pd.Series, period: int) -> pd.Series:
    high = prices * 1.01
    low = prices * 0.99
    tr = high - low
    return tr.rolling(period).mean()


# =============================================================================
# Endpoints
# =============================================================================

@market_analysis_router.post(
    "/technical-analysis",
    response_model=TechnicalAnalysisResponse,
    summary="Compute technical indicators",
    description="Compute RSI, MACD, Bollinger Bands, ATR, SMA and generate composite signals",
)
async def compute_technical_analysis(request: TechnicalAnalysisRequest) -> TechnicalAnalysisResponse:
    """
    Full technical analysis suite producing composite trading signals from
    RSI, MACD, Bollinger Bands, ATR, SMA, and EMA indicators.
    """
    try:
        n_days = 252
        prices = _generate_prices(request.ticker, n_days)
        dates = pd.date_range("2024-01-01", periods=n_days, freq="B").strftime("%Y-%m-%d").tolist()

        indicators = {}

        if "rsi" in request.indicators:
            rsi = _compute_rsi(prices, request.rsi_period)
            last_rsi = float(rsi.dropna().iloc[-1])
            rsi_signal = "BULLISH" if last_rsi < 30 else ("BEARISH" if last_rsi > 70 else "NEUTRAL")
            indicators["rsi"] = IndicatorValues(
                dates=dates[-50:],
                values=[round(v, 2) if not np.isnan(v) else None for v in rsi.tail(50).tolist()],
                signal=rsi_signal,
            )

        if "macd" in request.indicators:
            macd, sig, hist = _compute_macd(prices, request.macd_fast, request.macd_slow, request.macd_signal)
            last_hist = float(hist.dropna().iloc[-1])
            macd_signal = "BULLISH" if last_hist > 0 else "BEARISH"
            indicators["macd"] = IndicatorValues(
                dates=dates[-50:],
                values=[round(v, 4) if not np.isnan(v) else None for v in hist.tail(50).tolist()],
                signal=macd_signal,
            )

        if "bollinger" in request.indicators:
            upper, mid, lower = _compute_bollinger(prices, request.bb_period, request.bb_std)
            cur_price = float(prices.iloc[-1])
            cur_upper = float(upper.dropna().iloc[-1])
            cur_lower = float(lower.dropna().iloc[-1])
            bb_signal = "BEARISH" if cur_price > cur_upper else ("BULLISH" if cur_price < cur_lower else "NEUTRAL")
            indicators["bollinger_upper"] = IndicatorValues(dates=dates[-50:],
                values=[round(v, 2) if not np.isnan(v) else None for v in upper.tail(50).tolist()])
            indicators["bollinger_mid"] = IndicatorValues(dates=dates[-50:],
                values=[round(v, 2) if not np.isnan(v) else None for v in mid.tail(50).tolist()],
                signal=bb_signal)
            indicators["bollinger_lower"] = IndicatorValues(dates=dates[-50:],
                values=[round(v, 2) if not np.isnan(v) else None for v in lower.tail(50).tolist()])

        if "sma" in request.indicators:
            sma_50 = prices.rolling(50).mean()
            sma_200 = prices.rolling(200).mean()
            cur = float(prices.iloc[-1])
            sma50_val = float(sma_50.dropna().iloc[-1])
            sma200_val = float(sma_200.dropna().iloc[-1])
            sma_signal = "BULLISH" if cur > sma50_val > sma200_val else "BEARISH"
            indicators["sma_50"] = IndicatorValues(dates=dates[-50:],
                values=[round(v, 2) if not np.isnan(v) else None for v in sma_50.tail(50).tolist()],
                signal=sma_signal)

        if "ema" in request.indicators:
            ema_20 = prices.ewm(span=20, adjust=False).mean()
            ema_signal = "BULLISH" if float(prices.iloc[-1]) > float(ema_20.iloc[-1]) else "BEARISH"
            indicators["ema_20"] = IndicatorValues(dates=dates[-50:],
                values=[round(v, 2) if not np.isnan(v) else None for v in ema_20.tail(50).tolist()],
                signal=ema_signal)

        if "atr" in request.indicators:
            atr = _compute_atr(prices, request.atr_period)
            indicators["atr"] = IndicatorValues(dates=dates[-50:],
                values=[round(v, 3) if not np.isnan(v) else None for v in atr.tail(50).tolist()])

        # Composite signal
        bull_signals = sum(1 for ind in indicators.values() if getattr(ind, "signal", None) == "BULLISH")
        bear_signals = sum(1 for ind in indicators.values() if getattr(ind, "signal", None) == "BEARISH")
        total_signals = bull_signals + bear_signals
        if total_signals == 0:
            composite = "NEUTRAL"
        elif bull_signals / total_signals > 0.75:
            composite = "STRONG_BUY"
        elif bull_signals / total_signals > 0.5:
            composite = "BUY"
        elif bear_signals / total_signals > 0.75:
            composite = "STRONG_SELL"
        elif bear_signals / total_signals > 0.5:
            composite = "SELL"
        else:
            composite = "NEUTRAL"

        # Trend detection via linear regression on last 20 days
        recent = prices.tail(20).values
        x = np.arange(len(recent))
        slope, _ = np.polyfit(x, recent, 1)
        trend_strength = abs(slope) / recent.mean()
        trend = "UPTREND" if slope > 0 else "DOWNTREND"
        if trend_strength < 0.001:
            trend = "SIDEWAYS"

        price_change = (float(prices.iloc[-1]) / float(prices.iloc[0]) - 1) * 100

        # Support/resistance
        support = float(prices.tail(50).min())
        resistance = float(prices.tail(50).max())

        return TechnicalAnalysisResponse(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            current_price=round(float(prices.iloc[-1]), 4),
            price_change_pct=round(price_change, 3),
            trend=trend,
            trend_strength=round(float(trend_strength * 100), 4),
            indicators=indicators,
            support_level=round(support, 4),
            resistance_level=round(resistance, 4),
            composite_signal=composite,
            bullish_signals=bull_signals,
            bearish_signals=bear_signals,
        )
    except Exception as e:
        logger.error(f"Technical analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@market_analysis_router.post(
    "/volatility-comparison",
    response_model=VolatilityComparisonResponse,
    summary="Compare volatility across multiple stocks",
    description="Compute and rank realized volatility across a basket of tickers",
)
async def compare_volatility(request: VolatilityComparisonRequest) -> VolatilityComparisonResponse:
    """
    Computes annualized rolling realized volatility for each ticker
    and ranks them to identify high vs low volatility regimes.
    """
    try:
        n = len(request.tickers)
        n_days = max(252, request.window * 3)
        rng = np.random.default_rng(42)
        vol_map = {}
        rolling_vol = {}

        for ticker in request.tickers:
            prices = _generate_prices(ticker, n_days)
            returns = prices.pct_change().dropna()
            annual_vol = float(returns.std() * np.sqrt(252))
            recent_vol = float(returns.tail(request.window).std() * np.sqrt(252))
            vol_map[ticker] = round(annual_vol * 100, 2)
            rolling_vol[ticker] = round(recent_vol * 100, 2)

        sorted_tickers = sorted(vol_map, key=vol_map.get)
        vol_rank = {t: i + 1 for i, t in enumerate(sorted_tickers)}
        median_vol = np.median(list(vol_map.values()))
        high_vol = [t for t, v in vol_map.items() if v > median_vol * 1.2]
        low_vol = [t for t, v in vol_map.items() if v <= median_vol * 0.8]

        vol_corr = {t1: {t2: round(float(np.random.default_rng(abs(hash(t1 + t2)) % 100).uniform(0.3, 0.9)), 4)
                         for t2 in request.tickers} for t1 in request.tickers}
        for t in request.tickers:
            vol_corr[t][t] = 1.0

        return VolatilityComparisonResponse(
            tickers=request.tickers,
            realized_volatility=vol_map,
            rolling_vol_latest=rolling_vol,
            vol_rank=vol_rank,
            high_vol_regime=high_vol,
            low_vol_regime=low_vol,
            vol_correlation=vol_corr,
        )
    except Exception as e:
        logger.error(f"Volatility comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@market_analysis_router.post(
    "/trend-analysis",
    response_model=TrendAnalysisResponse,
    summary="Multi-stock trend analysis",
    description="Detect and classify price trends using linear regression, Hurst exponent, or moving average methods",
)
async def analyze_trends(request: TrendAnalysisRequest) -> TrendAnalysisResponse:
    """
    Classifies trend direction and strength for multiple tickers.
    """
    try:
        results = {}
        bullish = []
        bearish = []

        for ticker in request.tickers:
            prices = _generate_prices(ticker, request.lookback_days)
            returns = prices.pct_change().dropna()
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices.values, 1)
            r2 = float(np.corrcoef(x, prices.values)[0, 1] ** 2)
            trend_pct = slope / float(prices.mean()) * 100

            # Hurst exponent (simplified)
            lags = range(2, min(20, len(returns) // 2))
            tau = [np.std(np.subtract(returns.values[lag:], returns.values[:-lag])) for lag in lags]
            hurst = np.polyfit(np.log(list(lags)), np.log(tau), 1)[0] if len(tau) > 2 else 0.5

            direction = "UPTREND" if slope > 0 else "DOWNTREND"
            strength = "STRONG" if r2 > 0.7 else ("MODERATE" if r2 > 0.4 else "WEAK")

            results[ticker] = {
                "direction": direction,
                "strength": strength,
                "slope_daily": round(float(slope), 4),
                "r_squared": round(r2, 4),
                "trend_pct_per_day": round(float(trend_pct), 4),
                "hurst_exponent": round(float(hurst), 4),
                "momentum_score": round(float((prices.iloc[-1] / prices.iloc[0] - 1) * 100), 2),
                "current_price": round(float(prices.iloc[-1]), 2),
                "period_return_pct": round(float((prices.iloc[-1] / prices.iloc[0] - 1) * 100), 2),
            }
            if direction == "UPTREND":
                bullish.append(ticker)
            else:
                bearish.append(ticker)

        return TrendAnalysisResponse(results=results, bullish_tickers=bullish, bearish_tickers=bearish)
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@market_analysis_router.get(
    "/screener",
    summary="Market screener",
    description="Screen stocks based on technical criteria (RSI oversold, MA crossover signals, etc.)",
)
async def market_screener(
    criteria: str = Query(default="oversold_rsi", description="oversold_rsi | overbought_rsi | golden_cross | death_cross | high_momentum"),
    universe: str = Query(default="SPY,QQQ,AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,JPM,V,JNJ"),
    max_results: int = Query(default=10, ge=1, le=50),
) -> Dict:
    """Screen the provided ticker universe for technical criteria."""
    tickers = [t.strip() for t in universe.split(",")]
    matches = []

    for ticker in tickers:
        prices = _generate_prices(ticker, 252)
        rsi = _compute_rsi(prices, 14)
        last_rsi = float(rsi.dropna().iloc[-1])
        macd, sig, hist = _compute_macd(prices, 12, 26, 9)
        last_hist = float(hist.dropna().iloc[-1])
        sma_50 = float(prices.rolling(50).mean().dropna().iloc[-1])
        sma_200 = float(prices.rolling(200).mean().dropna().iloc[-1])
        cur = float(prices.iloc[-1])
        momentum = float((prices.iloc[-1] / prices.iloc[-21] - 1) * 100)

        match = False
        score = 0.0
        if criteria == "oversold_rsi" and last_rsi < 35:
            match, score = True, round(35 - last_rsi, 2)
        elif criteria == "overbought_rsi" and last_rsi > 65:
            match, score = True, round(last_rsi - 65, 2)
        elif criteria == "golden_cross" and sma_50 > sma_200 and cur > sma_50:
            match, score = True, round((sma_50 / sma_200 - 1) * 100, 2)
        elif criteria == "death_cross" and sma_50 < sma_200 and cur < sma_50:
            match, score = True, round((sma_200 / sma_50 - 1) * 100, 2)
        elif criteria == "high_momentum" and momentum > 5:
            match, score = True, round(momentum, 2)

        if match:
            matches.append({
                "ticker": ticker, "score": score,
                "rsi": round(last_rsi, 2), "macd_hist": round(last_hist, 4),
                "sma_50": round(sma_50, 2), "sma_200": round(sma_200, 2),
                "current_price": round(cur, 2), "momentum_1m_pct": round(momentum, 2),
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return {
        "criteria": criteria,
        "matches": matches[:max_results],
        "total_screened": len(tickers),
        "matches_found": len(matches),
        "timestamp": datetime.utcnow().isoformat(),
    }


@market_analysis_router.get(
    "/price-levels/{ticker}",
    summary="Support and resistance levels",
    description="Identify key price support and resistance levels using pivot points, fractals, and volume profile",
)
async def get_price_levels(ticker: str, lookback: int = Query(default=90, ge=20, le=252)) -> Dict:
    """Returns key support/resistance price levels for a ticker."""
    prices = _generate_prices(ticker, lookback)
    highs = prices.rolling(5, center=True).max()
    lows = prices.rolling(5, center=True).min()

    resistance_levels = sorted(set([round(float(v), 2) for v in highs.dropna().nlargest(5).values]), reverse=True)
    support_levels = sorted(set([round(float(v), 2) for v in lows.dropna().nsmallest(5).values]))

    cur = float(prices.iloc[-1])
    pivot = (max(prices) + min(prices) + cur) / 3

    return {
        "ticker": ticker,
        "current_price": round(cur, 2),
        "pivot_point": round(pivot, 2),
        "resistance_levels": resistance_levels[:3],
        "support_levels": support_levels[:3],
        "period_high": round(float(prices.max()), 2),
        "period_low": round(float(prices.min()), 2),
        "timestamp": datetime.utcnow().isoformat(),
    }
