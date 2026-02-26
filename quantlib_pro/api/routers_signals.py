"""
Trading Signals API Router

Covers page 11: Buy/Sell Signal Generator
- MA crossover signals
- RSI momentum signals
- MACD crossover signals
- Bollinger Band breakout signals
- Combined multi-indicator signals with confidence scoring
- Signal screener across universe
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

signals_router = APIRouter(prefix="/signals", tags=["signals"])

# =============================================================================
# Models
# =============================================================================

class Signal(BaseModel):
    indicator: str
    signal_type: str  # BUY | SELL | NEUTRAL
    value: float
    threshold: Optional[float] = None
    confidence: float  # 0-1


class SignalGenerateRequest(BaseModel):
    ticker: str = Field(default="SPY")
    lookback_days: int = Field(default=252, ge=60, le=1260)
    strategies: List[str] = Field(
        default=["ma_crossover", "rsi", "macd", "bollinger_bands", "momentum"],
        description="Strategies to evaluate"
    )
    rsi_oversold: float = Field(default=30.0, ge=10, le=40)
    rsi_overbought: float = Field(default=70.0, ge=60, le=90)
    ma_short: int = Field(default=20, ge=5, le=50)
    ma_long: int = Field(default=50, ge=20, le=200)


class SignalGenerateResponse(BaseModel):
    ticker: str
    current_price: float
    signals: List[Signal]
    combined_signal: str  # STRONG_BUY | BUY | NEUTRAL | SELL | STRONG_SELL
    combined_confidence: float
    buy_count: int
    sell_count: int
    neutral_count: int
    recommendation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SignalBacktestRequest(BaseModel):
    ticker: str = Field(default="SPY")
    strategy: str = Field(default="ma_crossover", description="Strategy name to backtest")
    lookback_days: int = Field(default=504, ge=120, le=2520)
    initial_capital: float = Field(default=10000.0, ge=1000)
    transaction_cost_bps: float = Field(default=5.0, ge=0, le=100)


class SignalBacktestResponse(BaseModel):
    ticker: str
    strategy: str
    total_return_pct: float
    annualized_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    final_portfolio_value: float
    buy_and_hold_return_pct: float
    alpha_vs_bh: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScreenRequest(BaseModel):
    universe: List[str] = Field(
        default=["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM"]
    )
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    signal_filter: str = Field(default="BUY", description="BUY | SELL | ALL")


class ScreenResponse(BaseModel):
    results: List[Dict[str, Any]]
    buy_signals: int
    sell_signals: int
    neutral_signals: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Helpers
# =============================================================================

def _sim_prices(ticker: str, n: int) -> pd.Series:
    seed = abs(hash(ticker)) % 9999
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0003, 0.012, n)
    return pd.Series(100.0 * np.exp(np.cumsum(r)))


def _ma_crossover_signal(prices: pd.Series, short: int = 20, long: int = 50) -> Signal:
    sma_s = prices.rolling(short).mean()
    sma_l = prices.rolling(long).mean()
    diff_now = float(sma_s.iloc[-1] - sma_l.iloc[-1])
    diff_prev = float(sma_s.iloc[-2] - sma_l.iloc[-2])
    if diff_prev <= 0 and diff_now > 0:
        sig, conf = "BUY", 0.85
    elif diff_prev >= 0 and diff_now < 0:
        sig, conf = "SELL", 0.85
    elif diff_now > 0:
        sig, conf = "BUY", 0.6
    else:
        sig, conf = "SELL", 0.6
    return Signal(indicator="ma_crossover", signal_type=sig, value=round(diff_now, 4), confidence=conf)


def _rsi_signal(prices: pd.Series, period: int = 14, oversold: float = 30, overbought: float = 70) -> Signal:
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = float(rsi.dropna().iloc[-1])
    if val < oversold:
        return Signal(indicator="rsi", signal_type="BUY", value=round(val, 2), threshold=oversold, confidence=0.8)
    elif val > overbought:
        return Signal(indicator="rsi", signal_type="SELL", value=round(val, 2), threshold=overbought, confidence=0.8)
    else:
        return Signal(indicator="rsi", signal_type="NEUTRAL", value=round(val, 2), confidence=0.5)


def _macd_signal(prices: pd.Series, fast: int = 12, slow: int = 26, sig_p: int = 9) -> Signal:
    ema_f = prices.ewm(span=fast, adjust=False).mean()
    ema_s = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_f - ema_s
    signal_line = macd.ewm(span=sig_p, adjust=False).mean()
    hist = macd - signal_line
    last_hist = float(hist.dropna().iloc[-1])
    prev_hist = float(hist.dropna().iloc[-2])
    if prev_hist <= 0 and last_hist > 0:
        return Signal(indicator="macd", signal_type="BUY", value=round(last_hist, 5), confidence=0.82)
    elif prev_hist >= 0 and last_hist < 0:
        return Signal(indicator="macd", signal_type="SELL", value=round(last_hist, 5), confidence=0.82)
    elif last_hist > 0:
        return Signal(indicator="macd", signal_type="BUY", value=round(last_hist, 5), confidence=0.58)
    else:
        return Signal(indicator="macd", signal_type="SELL", value=round(last_hist, 5), confidence=0.58)


def _bollinger_signal(prices: pd.Series, period: int = 20, n_std: float = 2.0) -> Signal:
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = sma + n_std * std
    lower = sma - n_std * std
    cur = float(prices.iloc[-1])
    up = float(upper.dropna().iloc[-1])
    lo = float(lower.dropna().iloc[-1])
    if cur < lo:
        return Signal(indicator="bollinger_bands", signal_type="BUY", value=round(cur, 4), threshold=round(lo, 4), confidence=0.75)
    elif cur > up:
        return Signal(indicator="bollinger_bands", signal_type="SELL", value=round(cur, 4), threshold=round(up, 4), confidence=0.75)
    else:
        pct_b = (cur - lo) / (up - lo)
        return Signal(indicator="bollinger_bands", signal_type="NEUTRAL", value=round(pct_b, 4), confidence=0.5)


def _momentum_signal(prices: pd.Series, period: int = 21) -> Signal:
    mom = float((prices.iloc[-1] / prices.iloc[-period - 1] - 1) * 100)
    if mom > 5:
        return Signal(indicator="momentum", signal_type="BUY", value=round(mom, 3), confidence=min(0.9, 0.5 + mom / 20))
    elif mom < -5:
        return Signal(indicator="momentum", signal_type="SELL", value=round(mom, 3), confidence=min(0.9, 0.5 + abs(mom) / 20))
    else:
        return Signal(indicator="momentum", signal_type="NEUTRAL", value=round(mom, 3), confidence=0.45)


# =============================================================================
# Endpoints
# =============================================================================

@signals_router.post(
    "/generate",
    response_model=SignalGenerateResponse,
    summary="Generate trading signals for a ticker",
    description="Compute buy/sell signals from multiple indicators and combine into a composite recommendation",
)
async def generate_signals(request: SignalGenerateRequest) -> SignalGenerateResponse:
    """
    Runs MA crossover, RSI, MACD, Bollinger Band and momentum analyses
    and produces a combined confidence-weighted signal.
    """
    try:
        prices = _sim_prices(request.ticker, request.lookback_days)
        sigs: List[Signal] = []

        strat_map = {
            "ma_crossover": lambda: _ma_crossover_signal(prices, request.ma_short, request.ma_long),
            "rsi": lambda: _rsi_signal(prices, 14, request.rsi_oversold, request.rsi_overbought),
            "macd": lambda: _macd_signal(prices),
            "bollinger_bands": lambda: _bollinger_signal(prices),
            "momentum": lambda: _momentum_signal(prices),
        }

        for strat in request.strategies:
            if strat in strat_map:
                sigs.append(strat_map[strat]())

        buy_conf = sum(s.confidence for s in sigs if s.signal_type == "BUY")
        sell_conf = sum(s.confidence for s in sigs if s.signal_type == "SELL")
        buy_count = sum(1 for s in sigs if s.signal_type == "BUY")
        sell_count = sum(1 for s in sigs if s.signal_type == "SELL")
        neutral_count = len(sigs) - buy_count - sell_count
        total_conf = sum(s.confidence for s in sigs) or 1

        if buy_conf > sell_conf * 1.5:
            combined = "STRONG_BUY" if buy_conf / total_conf > 0.7 else "BUY"
            combined_conf = round(buy_conf / total_conf, 3)
        elif sell_conf > buy_conf * 1.5:
            combined = "STRONG_SELL" if sell_conf / total_conf > 0.7 else "SELL"
            combined_conf = round(sell_conf / total_conf, 3)
        else:
            combined = "NEUTRAL"
            combined_conf = 0.5

        recommendation = {
            "STRONG_BUY": "Strong accumulation opportunity. Multiple indicators aligned bullish.",
            "BUY": "Moderate buy signal. Majority of indicators suggest upward momentum.",
            "NEUTRAL": "No clear directional edge. Wait for confirmation.",
            "SELL": "Moderate sell signal. Majority of indicators suggest downward pressure.",
            "STRONG_SELL": "Strong sell signal. Multiple indicators aligned bearish.",
        }.get(combined, "Monitor for confirmation.")

        return SignalGenerateResponse(
            ticker=request.ticker,
            current_price=round(float(prices.iloc[-1]), 4),
            signals=sigs,
            combined_signal=combined,
            combined_confidence=combined_conf,
            buy_count=buy_count,
            sell_count=sell_count,
            neutral_count=neutral_count,
            recommendation=recommendation,
        )
    except Exception as e:
        logger.error(f"Signal generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@signals_router.post(
    "/backtest",
    response_model=SignalBacktestResponse,
    summary="Backtest a signal strategy",
    description="Run historical backtest for a given signal strategy and compute performance metrics",
)
async def backtest_signal(request: SignalBacktestRequest) -> SignalBacktestResponse:
    """
    Backtests a signal-based trading strategy computing Sharpe, drawdown, win rate.
    """
    try:
        prices = _sim_prices(request.ticker, request.lookback_days)
        cost = request.transaction_cost_bps / 10000

        strat_map = {
            "ma_crossover": lambda p: _ma_crossover_signal(p, 20, 50),
            "rsi": lambda p: _rsi_signal(p, 14, 30, 70),
            "macd": lambda p: _macd_signal(p),
            "bollinger_bands": lambda p: _bollinger_signal(p),
            "momentum": lambda p: _momentum_signal(p),
        }

        positions = []
        for i in range(60, len(prices)):
            sig_fn = strat_map.get(request.strategy, strat_map["ma_crossover"])
            s = sig_fn(prices.iloc[:i+1])
            positions.append(1 if s.signal_type == "BUY" else (-1 if s.signal_type == "SELL" else 0))

        positions = pd.Series(positions)
        rets = prices.pct_change().iloc[60:].reset_index(drop=True)
        strat_rets = positions.shift(1).fillna(0) * rets - abs(positions.diff().fillna(0)) * cost
        cum = (1 + strat_rets).cumprod()
        total_ret = float(cum.iloc[-1] - 1) * 100
        annual_ret = ((1 + total_ret / 100) ** (252 / len(strat_rets)) - 1) * 100
        roll_max = cum.cummax()
        dd = (cum / roll_max - 1).min() * 100
        sharpe = float(strat_rets.mean() / strat_rets.std() * np.sqrt(252)) if strat_rets.std() > 0 else 0.0
        trades_idx = positions[positions.diff().abs() > 0].index
        n_trades = len(trades_idx)
        wins = sum(strat_rets.iloc[i] > 0 for i in trades_idx if i < len(strat_rets))
        win_rate = (wins / n_trades * 100) if n_trades > 0 else 50.0
        gross_profit = strat_rets[strat_rets > 0].sum()
        gross_loss = abs(strat_rets[strat_rets < 0].sum())
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else float("inf")
        bh_ret = float((prices.iloc[-1] / prices.iloc[60] - 1) * 100)

        return SignalBacktestResponse(
            ticker=request.ticker,
            strategy=request.strategy,
            total_return_pct=round(total_ret, 2),
            annualized_return_pct=round(float(annual_ret), 2),
            max_drawdown_pct=round(float(dd), 2),
            sharpe_ratio=round(sharpe, 3),
            total_trades=n_trades,
            win_rate_pct=round(win_rate, 2),
            profit_factor=round(min(profit_factor, 99.0), 3),
            final_portfolio_value=round(request.initial_capital * (1 + total_ret / 100), 2),
            buy_and_hold_return_pct=round(bh_ret, 2),
            alpha_vs_bh=round(total_ret - bh_ret, 2),
        )
    except Exception as e:
        logger.error(f"Signal backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@signals_router.post(
    "/screen",
    response_model=ScreenResponse,
    summary="Screen universe for signals",
    description="Scan a list of tickers and return those with qualifying buy/sell signals",
)
async def screen_signals(request: ScreenRequest) -> ScreenResponse:
    """Screens a ticker universe and returns combined signals."""
    try:
        results = []
        buy_count = sell_count = neutral_count = 0

        for ticker in request.universe:
            prices = _sim_prices(ticker, 252)
            sigs = [
                _ma_crossover_signal(prices),
                _rsi_signal(prices),
                _macd_signal(prices),
                _bollinger_signal(prices),
                _momentum_signal(prices),
            ]
            buy_c = sum(1 for s in sigs if s.signal_type == "BUY")
            sell_c = sum(1 for s in sigs if s.signal_type == "SELL")
            conf_buy = sum(s.confidence for s in sigs if s.signal_type == "BUY")
            conf_sell = sum(s.confidence for s in sigs if s.signal_type == "SELL")
            total = sum(s.confidence for s in sigs) or 1

            if conf_buy > conf_sell:
                combined, conf = "BUY", round(conf_buy / total, 3)
            elif conf_sell > conf_buy:
                combined, conf = "SELL", round(conf_sell / total, 3)
            else:
                combined, conf = "NEUTRAL", 0.5

            if conf < request.min_confidence:
                continue
            if request.signal_filter != "ALL" and combined != request.signal_filter:
                continue

            if combined == "BUY":
                buy_count += 1
            elif combined == "SELL":
                sell_count += 1
            else:
                neutral_count += 1

            results.append({
                "ticker": ticker,
                "signal": combined,
                "confidence": conf,
                "buy_indicators": buy_c,
                "sell_indicators": sell_c,
                "current_price": round(float(prices.iloc[-1]), 2),
            })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return ScreenResponse(
            results=results,
            buy_signals=buy_count,
            sell_signals=sell_count,
            neutral_signals=neutral_count,
        )
    except Exception as e:
        logger.error(f"Signal screen error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@signals_router.get(
    "/current/{ticker}",
    summary="Get current signals for a ticker",
    description="Returns real-time (simulated) signal status for a single ticker across all strategies",
)
async def get_current_signals(ticker: str) -> Dict:
    """Returns current signal state for all strategies on a single ticker."""
    prices = _sim_prices(ticker, 252)
    sigs = {
        "ma_crossover": _ma_crossover_signal(prices),
        "rsi": _rsi_signal(prices),
        "macd": _macd_signal(prices),
        "bollinger_bands": _bollinger_signal(prices),
        "momentum": _momentum_signal(prices),
    }
    return {
        "ticker": ticker,
        "current_price": round(float(prices.iloc[-1]), 4),
        "signals": {k: {"signal": v.signal_type, "value": v.value, "confidence": v.confidence}
                    for k, v in sigs.items()},
        "timestamp": datetime.utcnow().isoformat(),
    }
