"""
QuantLib Pro — API Explorer
Interactive REST API browser and tester embedded in the Streamlit app.

Features:
- Browse all 17 API domains and 75 endpoints
- Dynamic form generation from schema definitions
- One-click request execution with JWT auth
- Auto-visualization: charts, dataframes, heatmaps
- Python SDK + curl code generation
- Request history (last 20) with replay
- CSV/JSON export
- Favorites/bookmarks
- Live API health indicator
"""

import json
import time
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
st.set_page_config(
    page_title="API Explorer — QuantLib Pro",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.method-get  { background:#27AE60; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:12px; }
.method-post { background:#2980B9; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:12px; }
.method-put  { background:#E67E22; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:12px; }
.method-del  { background:#E74C3C; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:12px; }
.status-ok   { background:#27AE60; color:white; padding:2px 8px; border-radius:4px; font-size:12px; }
.status-err  { background:#E74C3C; color:white; padding:2px 8px; border-radius:4px; font-size:12px; }
.endpoint-header { background:#1E1E2E; padding:12px 16px; border-radius:8px; border-left:4px solid #7C3AED; margin-bottom:12px; }
.latency-badge { color:#94A3B8; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT CATALOG — single source of truth for all 17 domains
# ─────────────────────────────────────────────────────────────────────────────
COMMON_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM", "GS", "SPY"]

ENDPOINT_CATALOG = {
    "Portfolio": {
        "icon": "📊",
        "prefix": "/api/v1/portfolio",
        "endpoints": [
            {
                "id": "portfolio_optimize",
                "label": "Optimize Portfolio",
                "method": "POST",
                "path": "/optimize",
                "description": "Compute optimal portfolio weights using Modern Portfolio Theory (Sharpe/MinVol/MaxReturn)",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"], "options": COMMON_TICKERS},
                    {"name": "budget", "type": "float", "label": "Budget ($)", "example": 100000.0, "min": 1000.0, "max": 10000000.0, "step": 1000.0},
                    {"name": "risk_free_rate", "type": "float", "label": "Risk-Free Rate", "example": 0.045, "min": 0.0, "max": 0.20, "step": 0.001},
                    {"name": "optimization_target", "type": "select", "label": "Optimization Target", "options": ["sharpe", "min_volatility", "max_return"], "example": "sharpe"},
                    {"name": "max_position_size", "type": "float", "label": "Max Position Size", "example": 0.40, "min": 0.05, "max": 1.0, "step": 0.05},
                ],
                "response_viz": "weights_pie_chart",
            },
            {
                "id": "portfolio_performance",
                "label": "Portfolio Performance",
                "method": "GET",
                "path": "/performance",
                "description": "Get portfolio performance metrics: returns, Sharpe, Sortino, max drawdown",
                "fields": [
                    {"name": "portfolio_id", "type": "str", "label": "Portfolio ID", "example": "DEMO_PORT"},
                    {"name": "period_days", "type": "int", "label": "Period (days)", "example": 252, "min": 30, "max": 1260},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "portfolio_frontier",
                "label": "Efficient Frontier",
                "method": "POST",
                "path": "/efficient-frontier",
                "description": "Compute efficient frontier curve (risk-return tradeoff)",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["AAPL", "GOOGL", "MSFT"], "options": COMMON_TICKERS},
                    {"name": "n_portfolios", "type": "int", "label": "Portfolio Samples", "example": 1000, "min": 100, "max": 5000},
                ],
                "response_viz": "scatter",
            },
            {
                "id": "portfolio_rebalance",
                "label": "Rebalance Portfolio",
                "method": "POST",
                "path": "/rebalance",
                "description": "Calculate rebalancing trades to restore target weights",
                "fields": [
                    {"name": "portfolio_id", "type": "str", "label": "Portfolio ID", "example": "DEMO_PORT"},
                    {"name": "threshold_pct", "type": "float", "label": "Drift Threshold (%)", "example": 0.05, "min": 0.01, "max": 0.25, "step": 0.01},
                ],
                "response_viz": "table",
            },
        ],
    },
    "Risk": {
        "icon": "🛡️",
        "prefix": "/api/v1/risk",
        "endpoints": [
            {
                "id": "risk_var",
                "label": "Value at Risk (VaR)",
                "method": "POST",
                "path": "/var",
                "description": "Compute VaR and CVaR using historical, parametric, or Monte Carlo methods",
                "fields": [
                    {"name": "portfolio_id", "type": "str", "label": "Portfolio ID", "example": "DEMO_PORT"},
                    {"name": "confidence_level", "type": "float", "label": "Confidence Level", "example": 0.95, "min": 0.90, "max": 0.999, "step": 0.01},
                    {"name": "method", "type": "select", "label": "Method", "options": ["historical", "parametric", "monte_carlo"], "example": "historical"},
                    {"name": "horizon_days", "type": "int", "label": "Horizon (days)", "example": 10, "min": 1, "max": 252},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "risk_stress",
                "label": "Stress Test",
                "method": "POST",
                "path": "/stress-test",
                "description": "Run historical and hypothetical stress scenarios (2008 crisis, COVID crash, etc.)",
                "fields": [
                    {"name": "portfolio_id", "type": "str", "label": "Portfolio ID", "example": "DEMO_PORT"},
                    {"name": "scenarios", "type": "list_str", "label": "Scenarios", "example": ["2008_crisis", "covid_crash", "rate_shock"], "options": ["2008_crisis", "covid_crash", "rate_shock", "tech_bubble", "flash_crash"]},
                ],
                "response_viz": "bar_chart",
            },
            {
                "id": "risk_tail",
                "label": "Tail Risk Analysis",
                "method": "POST",
                "path": "/tail-risk",
                "description": "Analyze tail risk distribution with extreme value theory",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["SPY", "QQQ"], "options": COMMON_TICKERS},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 504, "min": 252, "max": 2520},
                ],
                "response_viz": "line_chart",
            },
        ],
    },
    "Options": {
        "icon": "⚙️",
        "prefix": "/api/v1/options",
        "endpoints": [
            {
                "id": "options_price",
                "label": "Price Option (Black-Scholes)",
                "method": "POST",
                "path": "/price",
                "description": "Price European options using Black-Scholes model with full Greeks",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "strike", "type": "float", "label": "Strike Price ($)", "example": 175.0, "min": 1.0, "max": 10000.0},
                    {"name": "expiry", "type": "str", "label": "Expiry Date (YYYY-MM-DD)", "example": "2026-06-20"},
                    {"name": "option_type", "type": "select", "label": "Option Type", "options": ["call", "put"], "example": "call"},
                    {"name": "risk_free_rate", "type": "float", "label": "Risk-Free Rate", "example": 0.045, "min": 0.0, "max": 0.15},
                    {"name": "volatility", "type": "float", "label": "Implied Volatility", "example": 0.25, "min": 0.01, "max": 2.0},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "options_greeks",
                "label": "Calculate Greeks",
                "method": "POST",
                "path": "/greeks",
                "description": "Calculate all option Greeks: Delta, Gamma, Theta, Vega, Rho",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "strike", "type": "float", "label": "Strike Price ($)", "example": 175.0, "min": 1.0, "max": 10000.0},
                    {"name": "expiry", "type": "str", "label": "Expiry Date (YYYY-MM-DD)", "example": "2026-06-20"},
                    {"name": "option_type", "type": "select", "label": "Option Type", "options": ["call", "put"], "example": "call"},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "options_mc",
                "label": "Monte Carlo Pricing",
                "method": "POST",
                "path": "/monte-carlo",
                "description": "Price options using Monte Carlo simulation with path-dependent payoffs",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "strike", "type": "float", "label": "Strike Price ($)", "example": 175.0, "min": 1.0, "max": 10000.0},
                    {"name": "expiry", "type": "str", "label": "Expiry Date (YYYY-MM-DD)", "example": "2026-06-20"},
                    {"name": "n_simulations", "type": "int", "label": "Simulations", "example": 10000, "min": 1000, "max": 100000},
                    {"name": "option_type", "type": "select", "label": "Option Type", "options": ["call", "put", "asian", "barrier"], "example": "call"},
                ],
                "response_viz": "metrics_cards",
            },
        ],
    },
    "Market Regime": {
        "icon": "🎯",
        "prefix": "/api/v1/regime",
        "endpoints": [
            {
                "id": "regime_detect",
                "label": "Detect Market Regime",
                "method": "POST",
                "path": "/detect",
                "description": "Detect market regimes using Hidden Markov Models (BULL/BEAR/SIDEWAYS)",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["SPY"], "options": COMMON_TICKERS},
                    {"name": "n_regimes", "type": "int", "label": "Number of Regimes", "example": 3, "min": 2, "max": 5},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 60, "max": 1260},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "regime_current",
                "label": "Current Regime",
                "method": "GET",
                "path": "/current",
                "description": "Get current detected market regime and probability",
                "fields": [],
                "response_viz": "metrics_cards",
            },
            {
                "id": "regime_history",
                "label": "Regime History",
                "method": "POST",
                "path": "/history",
                "description": "Get historical regime transitions over a time period",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "SPY"},
                    {"name": "start_date", "type": "str", "label": "Start Date (YYYY-MM-DD)", "example": "2020-01-01"},
                    {"name": "end_date", "type": "str", "label": "End Date (YYYY-MM-DD)", "example": "2026-02-01"},
                ],
                "response_viz": "line_chart",
            },
        ],
    },
    "Volatility": {
        "icon": "📉",
        "prefix": "/api/v1/volatility",
        "endpoints": [
            {
                "id": "vol_surface",
                "label": "Volatility Surface",
                "method": "POST",
                "path": "/surface",
                "description": "Build implied volatility surface from options market data",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "model", "type": "select", "label": "Model", "options": ["svi", "sabr", "rbf", "polynomial"], "example": "svi"},
                ],
                "response_viz": "heatmap",
            },
            {
                "id": "vol_garch",
                "label": "GARCH Analysis",
                "method": "POST",
                "path": "/garch",
                "description": "Fit GARCH(1,1) model and forecast conditional volatility",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 504, "min": 252},
                    {"name": "forecast_days", "type": "int", "label": "Forecast (days)", "example": 30, "min": 1, "max": 252},
                ],
                "response_viz": "line_chart",
            },
            {
                "id": "vol_realized",
                "label": "Realized Volatility",
                "method": "POST",
                "path": "/realized",
                "description": "Calculate realized volatility using close-to-close or Parkinson estimator",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["AAPL", "GOOGL", "MSFT"], "options": COMMON_TICKERS},
                    {"name": "window_days", "type": "int", "label": "Rolling Window (days)", "example": 21, "min": 5, "max": 252},
                    {"name": "estimator", "type": "select", "label": "Estimator", "options": ["close_to_close", "parkinson", "garman_klass", "yang_zhang"], "example": "close_to_close"},
                ],
                "response_viz": "line_chart",
            },
        ],
    },
    "Macro": {
        "icon": "🌍",
        "prefix": "/api/v1/macro",
        "endpoints": [
            {
                "id": "macro_indicators",
                "label": "Macro Indicators",
                "method": "GET",
                "path": "/indicators",
                "description": "Get current macroeconomic indicators: VIX, yield curve, credit spreads, PMI",
                "fields": [],
                "response_viz": "metrics_cards",
            },
            {
                "id": "macro_correlation",
                "label": "Correlation Regime",
                "method": "POST",
                "path": "/correlation-regime",
                "description": "Detect cross-asset correlation regime shifts",
                "fields": [
                    {"name": "assets", "type": "list_str", "label": "Asset Tickers", "example": ["SPY", "TLT", "GLD", "DXY"], "options": ["SPY", "TLT", "GLD", "DXY", "USO", "VIX", "HYG"]},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 60},
                ],
                "response_viz": "heatmap",
            },
            {
                "id": "macro_sentiment",
                "label": "Market Sentiment",
                "method": "GET",
                "path": "/sentiment",
                "description": "Compute fear/greed index and VIX-based sentiment regime",
                "fields": [],
                "response_viz": "metrics_cards",
            },
        ],
    },
    "Backtesting": {
        "icon": "📈",
        "prefix": "/api/v1/backtesting",
        "endpoints": [
            {
                "id": "backtest_list",
                "label": "List Strategies",
                "method": "GET",
                "path": "/strategies",
                "description": "List all available backtesting strategies",
                "fields": [],
                "response_viz": "table",
            },
            {
                "id": "backtest_run",
                "label": "Run Backtest",
                "method": "POST",
                "path": "/run",
                "description": "Run historical strategy backtest with performance metrics",
                "fields": [
                    {"name": "strategy", "type": "select", "label": "Strategy", "options": ["moving_average_crossover", "rsi_momentum", "mean_reversion", "pairs_trading"], "example": "moving_average_crossover"},
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "SPY"},
                    {"name": "start_date", "type": "str", "label": "Start Date (YYYY-MM-DD)", "example": "2020-01-01"},
                    {"name": "end_date", "type": "str", "label": "End Date (YYYY-MM-DD)", "example": "2026-01-01"},
                    {"name": "initial_capital", "type": "float", "label": "Initial Capital ($)", "example": 100000.0, "min": 10000.0},
                ],
                "response_viz": "line_chart",
            },
            {
                "id": "backtest_compare",
                "label": "Compare Strategies",
                "method": "POST",
                "path": "/compare",
                "description": "Compare multiple strategy backtests side by side",
                "fields": [
                    {"name": "strategies", "type": "list_str", "label": "Strategies", "example": ["moving_average_crossover", "rsi_momentum"], "options": ["moving_average_crossover", "rsi_momentum", "mean_reversion", "pairs_trading"]},
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "SPY"},
                    {"name": "start_date", "type": "str", "label": "Start Date (YYYY-MM-DD)", "example": "2020-01-01"},
                ],
                "response_viz": "bar_chart",
            },
        ],
    },
    "Analytics": {
        "icon": "🔬",
        "prefix": "/api/v1/analytics",
        "endpoints": [
            {
                "id": "analytics_correlation",
                "label": "Correlation Analysis",
                "method": "POST",
                "path": "/correlation",
                "description": "Compute Pearson, Spearman, and Kendall correlation matrices",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"], "options": COMMON_TICKERS},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 30},
                    {"name": "method", "type": "select", "label": "Method", "options": ["pearson", "spearman", "kendall"], "example": "pearson"},
                ],
                "response_viz": "heatmap",
            },
            {
                "id": "analytics_pca",
                "label": "PCA Analysis",
                "method": "POST",
                "path": "/pca",
                "description": "Principal Component Analysis to identify main return factors",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"], "options": COMMON_TICKERS},
                    {"name": "n_components", "type": "int", "label": "Components", "example": 3, "min": 2, "max": 10},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 30},
                ],
                "response_viz": "bar_chart",
            },
            {
                "id": "analytics_factor",
                "label": "Factor Analysis",
                "method": "POST",
                "path": "/factor-analysis",
                "description": "Fama-French 3/5 factor model exposure and attribution",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["AAPL", "GOOGL", "MSFT"], "options": COMMON_TICKERS},
                    {"name": "factors", "type": "list_str", "label": "Factors", "example": ["market", "size", "value"], "options": ["market", "size", "value", "momentum", "profitability", "investment"]},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 30},
                ],
                "response_viz": "bar_chart",
            },
        ],
    },
    "Data": {
        "icon": "💾",
        "prefix": "/api/v1/data",
        "endpoints": [
            {
                "id": "data_status",
                "label": "Market Status",
                "method": "GET",
                "path": "/market-status",
                "description": "Get current market open/close status for major exchanges",
                "fields": [],
                "response_viz": "metrics_cards",
            },
            {
                "id": "data_quote",
                "label": "Stock Quote",
                "method": "GET",
                "path": "/quote/{ticker}",
                "description": "Get real-time quote: price, change, volume, market cap",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                ],
                "response_viz": "metrics_cards",
                "path_params": ["ticker"],
            },
            {
                "id": "data_historical",
                "label": "Historical Data",
                "method": "POST",
                "path": "/historical",
                "description": "Fetch OHLCV historical price data for a ticker",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "start_date", "type": "str", "label": "Start Date (YYYY-MM-DD)", "example": "2024-01-01"},
                    {"name": "end_date", "type": "str", "label": "End Date (YYYY-MM-DD)", "example": "2026-02-01"},
                    {"name": "interval", "type": "select", "label": "Interval", "options": ["1d", "1wk", "1mo"], "example": "1d"},
                ],
                "response_viz": "line_chart",
            },
            {
                "id": "data_quality",
                "label": "Data Quality Check",
                "method": "POST",
                "path": "/quality-check",
                "description": "Check data integrity: gaps, anomalies, outliers",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["AAPL", "GOOGL"], "options": COMMON_TICKERS},
                ],
                "response_viz": "table",
            },
        ],
    },
    "Market Analysis": {
        "icon": "📊",
        "prefix": "/api/v1/market-analysis",
        "endpoints": [
            {
                "id": "mktanalysis_technical",
                "label": "Technical Analysis",
                "method": "POST",
                "path": "/technical-analysis",
                "description": "Compute RSI, MACD, Bollinger Bands, ATR, SMA, EMA with composite signal",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "period_days", "type": "int", "label": "Period (days)", "example": 90, "min": 30, "max": 504},
                    {"name": "indicators", "type": "list_str", "label": "Indicators", "example": ["RSI", "MACD", "BB"], "options": ["RSI", "MACD", "BB", "ATR", "SMA", "EMA"]},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "mktanalysis_screener",
                "label": "Market Screener",
                "method": "GET",
                "path": "/screener",
                "description": "Screen stocks by technical criteria: oversold, golden cross, momentum",
                "fields": [
                    {"name": "criteria", "type": "select", "label": "Criteria", "options": ["oversold", "overbought", "golden_cross", "death_cross", "momentum_bullish"], "example": "oversold"},
                ],
                "response_viz": "table",
            },
            {
                "id": "mktanalysis_trend",
                "label": "Trend Analysis",
                "method": "POST",
                "path": "/trend-analysis",
                "description": "Detect trend direction with linear regression and Hurst exponent",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "period_days", "type": "int", "label": "Period (days)", "example": 252, "min": 30},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "mktanalysis_levels",
                "label": "Price Levels",
                "method": "GET",
                "path": "/price-levels/{ticker}",
                "description": "Identify support and resistance levels via pivot points",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                ],
                "response_viz": "metrics_cards",
                "path_params": ["ticker"],
            },
        ],
    },
    "Trading Signals": {
        "icon": "🔔",
        "prefix": "/api/v1/signals",
        "endpoints": [
            {
                "id": "signals_generate",
                "label": "Generate Signals",
                "method": "POST",
                "path": "/generate",
                "description": "Generate multi-indicator trading signals (MA, RSI, MACD, Bollinger, Momentum)",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "TSLA"},
                    {"name": "strategies", "type": "list_str", "label": "Strategies", "example": ["RSI", "MACD"], "options": ["MA_Crossover", "RSI", "MACD", "Bollinger", "Momentum"]},
                    {"name": "period_days", "type": "int", "label": "Period (days)", "example": 90, "min": 30},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "signals_backtest",
                "label": "Backtest Signal Strategy",
                "method": "POST",
                "path": "/backtest",
                "description": "Backtest a signal-based strategy with Sharpe, win rate, profit factor",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "strategy", "type": "select", "label": "Strategy", "options": ["MA_Crossover", "RSI", "MACD", "Bollinger", "Momentum"], "example": "MA_Crossover"},
                    {"name": "start_date", "type": "str", "label": "Start Date (YYYY-MM-DD)", "example": "2022-01-01"},
                    {"name": "initial_capital", "type": "float", "label": "Initial Capital ($)", "example": 100000.0},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "signals_current",
                "label": "Current Signals",
                "method": "GET",
                "path": "/current/{ticker}",
                "description": "Get current real-time signal status across all strategies",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                ],
                "response_viz": "metrics_cards",
                "path_params": ["ticker"],
            },
        ],
    },
    "Liquidity": {
        "icon": "💧",
        "prefix": "/api/v1/liquidity",
        "endpoints": [
            {
                "id": "liquidity_orderbook",
                "label": "Order Book Simulation",
                "method": "POST",
                "path": "/order-book",
                "description": "Simulate L2 order book with bid/ask depth and spread dynamics",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "mid_price", "type": "float", "label": "Mid Price ($)", "example": 175.0, "min": 1.0},
                    {"name": "spread_bps", "type": "float", "label": "Spread (bps)", "example": 5.0, "min": 0.5, "max": 100.0},
                    {"name": "depth_levels", "type": "int", "label": "Depth Levels", "example": 10, "min": 5, "max": 20},
                ],
                "response_viz": "table",
            },
            {
                "id": "liquidity_metrics",
                "label": "Liquidity Metrics",
                "method": "POST",
                "path": "/metrics",
                "description": "Compute Amihud illiquidity, Kyle's lambda, Roll's spread, turnover",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 30},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "liquidity_impact",
                "label": "Market Impact",
                "method": "POST",
                "path": "/market-impact",
                "description": "Estimate market impact cost for large orders using square-root model",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "order_size_shares", "type": "int", "label": "Order Size (shares)", "example": 10000, "min": 100},
                    {"name": "side", "type": "select", "label": "Side", "options": ["buy", "sell"], "example": "buy"},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "liquidity_flashcrash",
                "label": "Flash Crash Simulation",
                "method": "POST",
                "path": "/flash-crash",
                "description": "Simulate flash crash scenario with price impact and recovery dynamics",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "shock_pct", "type": "float", "label": "Price Shock (%)", "example": -0.10, "min": -0.5, "max": -0.01},
                    {"name": "recovery_speed", "type": "select", "label": "Recovery Speed", "options": ["slow", "medium", "fast"], "example": "medium"},
                ],
                "response_viz": "line_chart",
            },
        ],
    },
    "Systemic Risk": {
        "icon": "🌐",
        "prefix": "/api/v1/systemic-risk",
        "endpoints": [
            {
                "id": "sysrisk_network",
                "label": "Network Analysis",
                "method": "POST",
                "path": "/network-analysis",
                "description": "Build correlation network graph with centrality metrics (degree, betweenness)",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", "example": ["JPM", "GS", "BAC", "C", "MS"], "options": ["JPM", "GS", "BAC", "C", "MS", "WFC", "BLK", "SCHW"]},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 60},
                    {"name": "correlation_threshold", "type": "float", "label": "Correlation Threshold", "example": 0.6, "min": 0.3, "max": 0.95},
                ],
                "response_viz": "table",
            },
            {
                "id": "sysrisk_covar",
                "label": "CoVaR & SRISK",
                "method": "POST",
                "path": "/covar",
                "description": "Compute Conditional VaR, Delta-CoVaR, SRISK, and Marginal Expected Shortfall",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Institution Ticker", "example": "JPM"},
                    {"name": "confidence_level", "type": "float", "label": "Confidence", "example": 0.95, "min": 0.90, "max": 0.999},
                    {"name": "lookback_days", "type": "int", "label": "Lookback (days)", "example": 252, "min": 60},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "sysrisk_tbtf",
                "label": "Too-Big-To-Fail Scores",
                "method": "GET",
                "path": "/too-big-to-fail",
                "description": "TBTF scoring based on size, interconnectedness, complexity, substitutability",
                "fields": [],
                "response_viz": "table",
            },
            {
                "id": "sysrisk_contagion",
                "label": "Contagion Cascade",
                "method": "POST",
                "path": "/contagion",
                "description": "Simulate multi-round contagion cascade through financial network",
                "fields": [
                    {"name": "initial_shock_ticker", "type": "str", "label": "Initial Shock Ticker", "example": "SVB"},
                    {"name": "shock_magnitude", "type": "float", "label": "Shock Magnitude", "example": -0.30, "min": -0.9, "max": -0.05},
                    {"name": "n_rounds", "type": "int", "label": "Contagion Rounds", "example": 3, "min": 1, "max": 10},
                ],
                "response_viz": "metrics_cards",
            },
        ],
    },
    "Execution": {
        "icon": "⚡",
        "prefix": "/api/v1/execution",
        "endpoints": [
            {
                "id": "exec_vwap",
                "label": "VWAP Schedule",
                "method": "POST",
                "path": "/vwap-schedule",
                "description": "Generate VWAP execution schedule with U-shaped intraday volume profile",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "total_shares", "type": "int", "label": "Total Shares", "example": 50000, "min": 1000},
                    {"name": "time_horizon_hours", "type": "float", "label": "Time Horizon (hours)", "example": 4.0, "min": 0.5, "max": 8.0},
                    {"name": "average_daily_volume", "type": "int", "label": "Avg Daily Volume", "example": 5000000, "min": 100000},
                ],
                "response_viz": "bar_chart",
            },
            {
                "id": "exec_twap",
                "label": "TWAP Schedule",
                "method": "POST",
                "path": "/twap-schedule",
                "description": "Time-weighted average price execution schedule with optional randomization",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "total_shares", "type": "int", "label": "Total Shares", "example": 50000, "min": 1000},
                    {"name": "n_slices", "type": "int", "label": "Number of Slices", "example": 8, "min": 2, "max": 50},
                    {"name": "randomize", "type": "bool", "label": "Randomize Timing", "example": True},
                ],
                "response_viz": "table",
            },
            {
                "id": "exec_optimal",
                "label": "Optimal Trajectory",
                "method": "POST",
                "path": "/optimal-trajectory",
                "description": "Almgren-Chriss optimal liquidation trajectory (urgency vs impact tradeoff)",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "total_shares", "type": "int", "label": "Total Shares", "example": 100000, "min": 1000},
                    {"name": "time_horizon_hours", "type": "float", "label": "Time Horizon (hours)", "example": 6.0, "min": 0.5, "max": 8.0},
                    {"name": "risk_aversion", "type": "float", "label": "Risk Aversion (λ)", "example": 0.001, "min": 0.0001, "max": 0.1},
                ],
                "response_viz": "line_chart",
            },
            {
                "id": "exec_impact",
                "label": "Market Impact Models",
                "method": "POST",
                "path": "/market-impact",
                "description": "Compare 4 impact models: Almgren-Chriss, Kyle, JPM, Square-Root",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "order_size_pct_adv", "type": "float", "label": "Order Size (% ADV)", "example": 0.05, "min": 0.001, "max": 0.5},
                    {"name": "participation_rate", "type": "float", "label": "Participation Rate", "example": 0.10, "min": 0.01, "max": 0.5},
                ],
                "response_viz": "bar_chart",
            },
        ],
    },
    "Compliance": {
        "icon": "✅",
        "prefix": "/api/v1/compliance",
        "endpoints": [
            {
                "id": "compliance_tradecheck",
                "label": "Pre-Trade Check",
                "method": "POST",
                "path": "/trade-check",
                "description": "Pre-trade compliance check: position limits, restricted list, wash sale, PDT rules",
                "fields": [
                    {"name": "ticker", "type": "str", "label": "Ticker", "example": "AAPL"},
                    {"name": "side", "type": "select", "label": "Side", "options": ["buy", "sell", "short"], "example": "buy"},
                    {"name": "quantity", "type": "int", "label": "Quantity (shares)", "example": 1000, "min": 1},
                    {"name": "account_id", "type": "str", "label": "Account ID", "example": "ACC_001"},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "compliance_auditlog",
                "label": "Audit Log",
                "method": "GET",
                "path": "/audit-log",
                "description": "Paginated compliance audit trail with filtering by date, user, action",
                "fields": [
                    {"name": "page", "type": "int", "label": "Page", "example": 1, "min": 1},
                    {"name": "page_size", "type": "int", "label": "Page Size", "example": 20, "min": 5, "max": 100},
                ],
                "response_viz": "table",
            },
            {
                "id": "compliance_positions",
                "label": "Position Limits",
                "method": "GET",
                "path": "/position-limits",
                "description": "Monitor current positions against limits with breach detection",
                "fields": [],
                "response_viz": "table",
            },
            {
                "id": "compliance_gdpr",
                "label": "GDPR Status",
                "method": "GET",
                "path": "/gdpr/status",
                "description": "GDPR compliance status, data retention, and data subject requests",
                "fields": [],
                "response_viz": "metrics_cards",
            },
            {
                "id": "compliance_regulatory",
                "label": "Regulatory Report",
                "method": "POST",
                "path": "/regulatory-report",
                "description": "Generate MiFID II, Dodd-Frank, Basel III, CCAR regulatory reports",
                "fields": [
                    {"name": "report_type", "type": "select", "label": "Report Type", "options": ["mifid2", "dodd_frank", "basel3", "ccar"], "example": "mifid2"},
                    {"name": "period", "type": "select", "label": "Period", "options": ["daily", "weekly", "monthly", "quarterly"], "example": "monthly"},
                ],
                "response_viz": "metrics_cards",
            },
        ],
    },
    "UAT & Stress": {
        "icon": "🧪",
        "prefix": "/api/v1/uat",
        "endpoints": [
            {
                "id": "uat_scenarios",
                "label": "Run UAT Scenarios",
                "method": "POST",
                "path": "/scenarios/run",
                "description": "Execute UAT test scenarios with pass/fail tracking across modules",
                "fields": [
                    {"name": "module", "type": "select", "label": "Module", "options": ["portfolio", "risk", "options", "execution", "compliance", "all"], "example": "all"},
                    {"name": "scenario_type", "type": "select", "label": "Scenario Type", "options": ["happy_path", "edge_cases", "stress", "regression"], "example": "happy_path"},
                ],
                "response_viz": "table",
            },
            {
                "id": "uat_performance",
                "label": "Performance Validation",
                "method": "GET",
                "path": "/performance-validation",
                "description": "Module performance benchmarks vs SLAs (latency, throughput)",
                "fields": [],
                "response_viz": "table",
            },
            {
                "id": "uat_stress",
                "label": "Trader Stress Monitor",
                "method": "POST",
                "path": "/stress-monitor/analyze",
                "description": "Analyze trader cognitive load and fatigue from trading pattern data",
                "fields": [
                    {"name": "trader_id", "type": "str", "label": "Trader ID", "example": "TRD_001"},
                    {"name": "session_duration_hours", "type": "float", "label": "Session Duration (hours)", "example": 6.0, "min": 0.5, "max": 16.0},
                    {"name": "decisions_per_hour", "type": "int", "label": "Decisions/Hour", "example": 45, "min": 1},
                ],
                "response_viz": "metrics_cards",
            },
            {
                "id": "uat_abtests",
                "label": "A/B Tests",
                "method": "GET",
                "path": "/ab-tests",
                "description": "View active A/B test configurations and results",
                "fields": [],
                "response_viz": "table",
            },
        ],
    },
    "Health": {
        "icon": "❤️",
        "prefix": "",
        "endpoints": [
            {
                "id": "health_basic",
                "label": "Health Check",
                "method": "GET",
                "path": "/health",
                "description": "Basic liveness check: API status, uptime, version",
                "fields": [],
                "response_viz": "metrics_cards",
            },
            {
                "id": "health_detailed",
                "label": "Detailed Health",
                "method": "GET",
                "path": "/health/detailed",
                "description": "Detailed subsystem health: database, cache, external APIs, memory",
                "fields": [],
                "response_viz": "metrics_cards",
            },
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "token": None,
        "history": [],
        "favorites": [],
        "selected_domain": "Portfolio",
        "selected_endpoint": None,
        "last_response": None,
        "last_latency": None,
        "last_status": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def check_api_health() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def get_auth_headers() -> dict:
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def do_login(username: str, password: str) -> bool:
    try:
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            st.session_state.token = data.get("access_token") or data.get("token")
            return True
        return False
    except Exception:
        return False


def execute_request(endpoint: dict, form_data: dict) -> tuple[int, dict, float]:
    method = endpoint["method"]
    path = endpoint["path"]
    prefix = ENDPOINT_CATALOG[st.session_state.selected_domain]["prefix"]

    # Replace path params
    for param in endpoint.get("path_params", []):
        if param in form_data:
            path = path.replace(f"{{{param}}}", str(form_data.pop(param)))

    url = BASE_URL + prefix + path
    headers = get_auth_headers()
    headers["Content-Type"] = "application/json"

    start = time.time()
    try:
        if method == "GET":
            r = requests.get(url, params=form_data, headers=headers, timeout=15)
        else:
            r = requests.post(url, json=form_data, headers=headers, timeout=15)
        latency = (time.time() - start) * 1000
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text}
        return r.status_code, body, latency
    except requests.exceptions.ConnectionError:
        return 0, {"error": "Cannot connect to API. Is the FastAPI server running on port 8000?"}, 0
    except Exception as e:
        return 0, {"error": str(e)}, 0


def add_to_history(domain: str, endpoint: dict, form_data: dict, status: int, latency: float):
    entry = {
        "ts": datetime.now().strftime("%H:%M:%S"),
        "domain": domain,
        "label": endpoint["label"],
        "method": endpoint["method"],
        "path": ENDPOINT_CATALOG[domain]["prefix"] + endpoint["path"],
        "payload": form_data,
        "status": status,
        "latency": round(latency, 1),
    }
    st.session_state.history.insert(0, entry)
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]


# ─────────────────────────────────────────────────────────────────────────────
# Response Visualization Engine
# ─────────────────────────────────────────────────────────────────────────────
def render_response(data: dict, viz_hint: str):
    if not data or not isinstance(data, dict):
        st.json(data)
        return

    # --- Detect shape and render ---
    # 1. weights dict → pie chart
    weights_key = next((k for k in data if "weight" in k.lower() and isinstance(data[k], dict)), None)
    if weights_key and viz_hint == "weights_pie_chart":
        w = data[weights_key]
        if all(isinstance(v, (int, float)) for v in w.values()):
            fig = px.pie(values=list(w.values()), names=list(w.keys()),
                         title=f"Portfolio Weights", hole=0.35,
                         template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    # 2. 2D list → heatmap
    matrix_key = next((k for k in data if "matrix" in k.lower() or "correlation" in k.lower()
                       and isinstance(data[k], list)), None)
    if matrix_key and viz_hint == "heatmap":
        arr = data[matrix_key]
        if arr and isinstance(arr[0], list):
            labels = data.get("tickers", data.get("labels", [str(i) for i in range(len(arr))]))
            fig = px.imshow(arr, x=labels, y=labels, color_continuous_scale="RdBu_r",
                            zmin=-1, zmax=1, title="Correlation Heatmap", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    # 3. list of dicts → dataframe
    list_key = next((k for k in data if isinstance(data[k], list) and data[k]
                     and isinstance(data[k][0], dict)), None)
    if list_key and viz_hint == "table":
        st.dataframe(pd.DataFrame(data[list_key]), use_container_width=True)

    # 4. flat numeric dict → metric cards
    numeric_kv = {k: v for k, v in data.items() if isinstance(v, (int, float)) and not k.startswith("_")}
    if numeric_kv and viz_hint in ("metrics_cards", "bar_chart"):
        if viz_hint == "metrics_cards":
            cols = st.columns(min(len(numeric_kv), 4))
            for i, (k, v) in enumerate(list(numeric_kv.items())[:8]):
                with cols[i % 4]:
                    display = f"{v:.4f}" if isinstance(v, float) else str(v)
                    st.metric(label=k.replace("_", " ").title(), value=display)
        else:
            fig = px.bar(x=list(numeric_kv.keys()), y=list(numeric_kv.values()),
                         title="Results", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    # 5. list of numbers → line chart
    arr_key = next((k for k in data if isinstance(data[k], list) and data[k]
                    and isinstance(data[k][0], (int, float))), None)
    if arr_key and viz_hint == "line_chart":
        fig = px.line(y=data[arr_key], title=arr_key.replace("_", " ").title(),
                      template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    # Always show raw JSON (collapsible)
    with st.expander("📋 Raw JSON Response", expanded=(viz_hint == "metrics_cards" and not numeric_kv)):
        st.json(data)


# ─────────────────────────────────────────────────────────────────────────────
# Code Generator
# ─────────────────────────────────────────────────────────────────────────────
def gen_python_snippet(domain: str, endpoint: dict, form_data: dict) -> str:
    prefix = ENDPOINT_CATALOG[domain]["prefix"]
    path = endpoint["path"]
    method = endpoint["method"].lower()
    resource = domain.lower().replace(" ", "_").replace("&", "and")
    func = endpoint["id"].replace(f"{resource.split('_')[0]}_", "")

    lines = [
        "from quantlib_api import QuantLibClient",
        "",
        "client = QuantLibClient(",
        '    base_url="http://localhost:8000",',
        '    username="demo",',
        '    password="demo123",',
        "    auto_login=True",
        ")",
        "",
        f"# {endpoint['description']}",
    ]
    if form_data:
        args = ", ".join(f"{k}={repr(v)}" for k, v in form_data.items())
        lines.append(f"result = client.{resource.split('_')[0]}.{func}({args})")
    else:
        lines.append(f"result = client.{resource.split('_')[0]}.{func}()")
    lines.append("print(result)")
    return "\n".join(lines)


def gen_curl_snippet(domain: str, endpoint: dict, form_data: dict) -> str:
    prefix = ENDPOINT_CATALOG[domain]["prefix"]
    path = endpoint["path"]
    method = endpoint["method"]
    for param in endpoint.get("path_params", []):
        if param in form_data:
            path = path.replace(f"{{{param}}}", str(form_data[param]))
    url = f"http://localhost:8000{prefix}{path}"

    lines = [f'curl -X {method} "{url}" \\']
    lines.append('  -H "Content-Type: application/json" \\')
    lines.append('  -H "Authorization: Bearer $TOKEN" \\')
    if method != "GET" and form_data:
        body = json.dumps(form_data, indent=2)
        lines.append(f"  -d '{body}'")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Form Generator
# ─────────────────────────────────────────────────────────────────────────────
def render_form(endpoint: dict) -> dict:
    form_data = {}
    for field in endpoint.get("fields", []):
        name = field["name"]
        label = field["label"]
        ftype = field["type"]
        example = field.get("example")
        help_text = field.get("help", "")

        if ftype == "str":
            form_data[name] = st.text_input(label, value=str(example or ""), help=help_text)
        elif ftype == "float":
            form_data[name] = st.number_input(
                label,
                value=float(example or 0.0),
                min_value=float(field.get("min", -1e9)),
                max_value=float(field.get("max", 1e9)),
                step=float(field.get("step", 0.01)),
                format="%.4f",
                help=help_text,
            )
        elif ftype == "int":
            form_data[name] = st.number_input(
                label,
                value=int(example or 0),
                min_value=int(field.get("min", 0)),
                max_value=int(field.get("max", 1000000)),
                step=1,
                help=help_text,
            )
        elif ftype == "bool":
            form_data[name] = st.checkbox(label, value=bool(example or False), help=help_text)
        elif ftype == "select":
            opts = field.get("options", [])
            default_idx = opts.index(example) if example in opts else 0
            form_data[name] = st.selectbox(label, options=opts, index=default_idx, help=help_text)
        elif ftype == "list_str":
            opts = field.get("options", [])
            default = example if isinstance(example, list) else []
            if opts:
                form_data[name] = st.multiselect(label, options=opts, default=default, help=help_text)
            else:
                raw = st.text_input(label, value=", ".join(default), help=help_text + " (comma-separated)")
                form_data[name] = [x.strip() for x in raw.split(",") if x.strip()]
        elif ftype == "multi_select":
            opts = field.get("options", [])
            default = example if isinstance(example, list) else []
            form_data[name] = st.multiselect(label, options=opts, default=default, help=help_text)
        elif ftype in ("date", "datetime"):
            form_data[name] = st.text_input(label, value=str(example or ""), help=help_text + " (YYYY-MM-DD)")
        elif ftype == "json":
            raw = st.text_area(label, value=json.dumps(example or {}, indent=2), help=help_text)
            try:
                form_data[name] = json.loads(raw)
            except Exception:
                form_data[name] = raw

    return form_data


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔌 API Explorer")
    st.caption("QuantLib Pro v1.0.0")

    # ── Auth ──
    st.markdown("---")
    st.subheader("🔑 Authentication")
    if st.session_state.token:
        st.success("🟢 Authenticated")
        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.rerun()
    else:
        with st.form("login_form", clear_on_submit=False):
            user = st.text_input("Username", value="demo")
            pwd = st.text_input("Password", value="demo123", type="password")
            if st.form_submit_button("Login 🔓", use_container_width=True):
                if do_login(user, pwd):
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Login failed. API may not be running.")

    # ── Health ──
    st.markdown("---")
    api_online = check_api_health()
    if api_online:
        st.markdown("🌐 **API:** 🟢 Online (`localhost:8000`)")
    else:
        st.markdown("🌐 **API:** 🔴 Offline — start: `python main_api.py`")

    # ── Search ──
    st.markdown("---")
    search_query = st.text_input("🔍 Search endpoints...", placeholder="e.g. VaR, VWAP, signals")

    # ── Domain selector ──
    st.markdown("---")
    st.subheader("📁 Domains")

    all_endpoints_flat = []
    for domain, info in ENDPOINT_CATALOG.items():
        for ep in info["endpoints"]:
            all_endpoints_flat.append((domain, ep))

    if search_query:
        matches = [
            (d, ep) for d, ep in all_endpoints_flat
            if search_query.lower() in ep["label"].lower()
            or search_query.lower() in ep["description"].lower()
            or search_query.lower() in ep["path"].lower()
        ]
        st.caption(f"{len(matches)} matches for '{search_query}'")
        for domain, ep in matches:
            icon = ENDPOINT_CATALOG[domain]["icon"]
            if st.button(f"{icon} {ep['label']}", key=f"search_{ep['id']}", use_container_width=True):
                st.session_state.selected_domain = domain
                st.session_state.selected_endpoint = ep["id"]
                st.rerun()
    else:
        for domain, info in ENDPOINT_CATALOG.items():
            count = len(info["endpoints"])
            with st.expander(f"{info['icon']} {domain} ({count})"):
                for ep in info["endpoints"]:
                    method_star = "🔵" if ep["method"] == "POST" else "🟢"
                    if st.button(
                        f"{method_star} {ep['label']}",
                        key=f"nav_{ep['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_domain = domain
                        st.session_state.selected_endpoint = ep["id"]
                        st.rerun()

    # ── Favorites ──
    if st.session_state.favorites:
        st.markdown("---")
        st.subheader("⭐ Favorites")
        for fav_id in st.session_state.favorites:
            match = next(((d, ep) for d, ep in all_endpoints_flat if ep["id"] == fav_id), None)
            if match:
                d, ep = match
                if st.button(f"★ {ep['label']}", key=f"fav_{fav_id}", use_container_width=True):
                    st.session_state.selected_domain = d
                    st.session_state.selected_endpoint = fav_id
                    st.rerun()

    # ── History ──
    if st.session_state.history:
        st.markdown("---")
        with st.expander(f"🕐 History ({len(st.session_state.history)})"):
            for h in st.session_state.history[:10]:
                color = "#27AE60" if h["status"] == 200 else "#E74C3C"
                st.markdown(
                    f"<small style='color:{color}'>{h['ts']} {h['method']} {h['label']} "
                    f"<span style='color:#94A3B8'>{h['status']} · {h['latency']}ms</span></small>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PANEL
# ─────────────────────────────────────────────────────────────────────────────
st.title("🔌 QuantLib Pro — API Explorer")

# Find active endpoint
active_domain = st.session_state.selected_domain
active_ep_id = st.session_state.selected_endpoint
domain_info = ENDPOINT_CATALOG[active_domain]

if active_ep_id:
    active_ep = next((ep for ep in domain_info["endpoints"] if ep["id"] == active_ep_id), None)
else:
    active_ep = domain_info["endpoints"][0]
    st.session_state.selected_endpoint = active_ep["id"]

if not active_ep:
    st.info("Select an endpoint from the sidebar to begin.")
    st.stop()

# ── Endpoint header ──
method_color = "#2980B9" if active_ep["method"] == "POST" else "#27AE60"
st.markdown(
    f"""<div class="endpoint-header">
    <span style="background:{method_color}; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:13px;">{active_ep['method']}</span>
    &nbsp;<code style="font-size:15px;">{domain_info['prefix']}{active_ep['path']}</code>
    </div>""",
    unsafe_allow_html=True,
)
st.markdown(f"**{active_ep['label']}** — {active_ep['description']}")

# Favorite toggle
fav_ids = st.session_state.favorites
is_fav = active_ep["id"] in fav_ids
fav_label = "★ Remove Favorite" if is_fav else "☆ Add to Favorites"
if st.button(fav_label, key="fav_toggle"):
    if is_fav:
        st.session_state.favorites = [f for f in fav_ids if f != active_ep["id"]]
    else:
        st.session_state.favorites.append(active_ep["id"])
    st.rerun()

st.markdown("---")

# ── Request form ──
left, right = st.columns([1, 1])

with left:
    st.subheader("⚙️ Request Configuration")
    if active_ep["fields"]:
        with st.form(key=f"form_{active_ep['id']}"):
            form_data = render_form(active_ep)
            submitted = st.form_submit_button("🚀 Send Request", use_container_width=True, type="primary")
    else:
        form_data = {}
        submitted = st.button("🚀 Send Request", use_container_width=True, type="primary", key=f"btn_{active_ep['id']}")

with right:
    st.subheader("📊 Response")

    if submitted:
        with st.spinner("Executing request..."):
            status, body, latency = execute_request(active_ep, dict(form_data))
            st.session_state.last_response = body
            st.session_state.last_status = status
            st.session_state.last_latency = latency
            add_to_history(active_domain, active_ep, dict(form_data), status, latency)

    if st.session_state.last_response is not None and st.session_state.selected_endpoint == active_ep["id"]:
        status = st.session_state.last_status
        latency = st.session_state.last_latency
        body = st.session_state.last_response

        status_color = "#27AE60" if status == 200 else "#E74C3C"
        st.markdown(
            f"<span style='background:{status_color}; color:white; padding:2px 8px; border-radius:4px; font-size:12px;'>{status} {'OK' if status == 200 else 'ERROR'}</span>"
            f"&nbsp;<span style='color:#94A3B8; font-size:12px;'>⏱ {latency:.0f}ms</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")
        render_response(body, active_ep.get("response_viz", "metrics_cards"))

        # Export buttons
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            st.download_button(
                "⬇️ Export JSON",
                data=json.dumps(body, indent=2),
                file_name=f"{active_ep['id']}_response.json",
                mime="application/json",
                use_container_width=True,
            )
        with exp_col2:
            # Try to create a flat CSV
            try:
                flat = {k: [v] for k, v in body.items() if isinstance(v, (str, int, float, bool))}
                if flat:
                    df_export = pd.DataFrame(flat)
                    st.download_button(
                        "⬇️ Export CSV",
                        data=df_export.to_csv(index=False),
                        file_name=f"{active_ep['id']}_response.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            except Exception:
                pass
    else:
        st.info("Fill in the form and click **Send Request** to see the response here.")

# ── Code Generator ──
st.markdown("---")
st.subheader("</> Code Generator")

tab1, tab2 = st.tabs(["🐍 Python SDK", "⚡ curl"])
with tab1:
    snippet = gen_python_snippet(active_domain, active_ep, dict(form_data))
    st.code(snippet, language="python")
with tab2:
    curl_snip = gen_curl_snippet(active_domain, active_ep, dict(form_data))
    st.code(curl_snip, language="bash")
    st.caption('Set your token: `TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d \'{"username":"demo","password":"demo123"}\' | python -c "import sys,json; print(json.load(sys.stdin)[\'access_token\'])")`')

# ── Domain Summary (footer) ──
st.markdown("---")
with st.expander("📋 Domain Overview — All Endpoints"):
    rows = []
    for domain, info in ENDPOINT_CATALOG.items():
        for ep in info["endpoints"]:
            rows.append({
                "Domain": f"{info['icon']} {domain}",
                "Method": ep["method"],
                "Endpoint": f"{info['prefix']}{ep['path']}",
                "Label": ep["label"],
            })
    df_catalog = pd.DataFrame(rows)
    st.dataframe(df_catalog, use_container_width=True, hide_index=True)
    st.caption(f"Total: {len(rows)} endpoints across {len(ENDPOINT_CATALOG)} domains")
