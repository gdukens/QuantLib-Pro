"""
Endpoint list for CLI 'endpoints list' command.

This is auto-generated from the API router definitions.
"""

ENDPOINT_LIST = [
    {"domain": "Portfolio", "method": "POST", "path": "/api/v1/portfolio/optimize", "description": "Optimize portfolio weights (MPT)"},
    {"domain": "Portfolio", "method": "GET", "path": "/api/v1/portfolio/performance", "description": "Portfolio performance metrics"},
    {"domain": "Portfolio", "method": "POST", "path": "/api/v1/portfolio/efficient-frontier", "description": "Compute efficient frontier"},
    {"domain": "Portfolio", "method": "POST", "path": "/api/v1/portfolio/sharpe-analysis", "description": "Sharpe ratio analysis"},
    {"domain": "Portfolio", "method": "POST", "path": "/api/v1/portfolio/rebalance", "description": "Calculate rebalancing trades"},

    {"domain": "Risk", "method": "POST", "path": "/api/v1/risk/var", "description": "Value at Risk (VaR) and CVaR"},
    {"domain": "Risk", "method": "POST", "path": "/api/v1/risk/stress-test", "description": "Stress test scenarios"},
    {"domain": "Risk", "method": "POST", "path": "/api/v1/risk/tail-risk", "description": "Tail risk analysis"},
    {"domain": "Risk", "method": "GET", "path": "/api/v1/risk/drawdown", "description": "Maximum drawdown"},
    {"domain": "Risk", "method": "POST", "path": "/api/v1/risk/correlation-stress", "description": "Correlation stress analysis"},

    {"domain": "Options", "method": "POST", "path": "/api/v1/options/price", "description": "Option pricing (BS/Binomial/MC)"},
    {"domain": "Options", "method": "POST", "path": "/api/v1/options/greeks", "description": "Option Greeks"},
    {"domain": "Options", "method": "POST", "path": "/api/v1/options/monte-carlo", "description": "Monte Carlo pricing"},
    {"domain": "Options", "method": "POST", "path": "/api/v1/options/implied-volatility", "description": "Implied volatility"},

    {"domain": "Regime", "method": "POST", "path": "/api/v1/regime/detect", "description": "Detect market regime (HMM)"},
    {"domain": "Regime", "method": "GET", "path": "/api/v1/regime/current/{ticker}", "description": "Current regime for ticker"},
    {"domain": "Regime", "method": "GET", "path": "/api/v1/regime/history", "description": "Regime history"},
    {"domain": "Regime", "method": "POST", "path": "/api/v1/regime/probabilities", "description": "Transition probabilities"},

    {"domain": "Volatility", "method": "POST", "path": "/api/v1/volatility/surface", "description": "IV surface construction"},
    {"domain": "Volatility", "method": "POST", "path": "/api/v1/volatility/term-structure", "description": "ATM term structure"},
    {"domain": "Volatility", "method": "POST", "path": "/api/v1/volatility/smile", "description": "Volatility smile"},
    {"domain": "Volatility", "method": "POST", "path": "/api/v1/volatility/garch", "description": "GARCH forecast"},

    {"domain": "Macro", "method": "POST", "path": "/api/v1/macro/indicators", "description": "Economic indicators"},
    {"domain": "Macro", "method": "POST", "path": "/api/v1/macro/correlation-regime", "description": "Macro correlation regime"},
    {"domain": "Macro", "method": "GET", "path": "/api/v1/macro/sentiment", "description": "Market sentiment"},

    {"domain": "Backtesting", "method": "GET", "path": "/api/v1/backtesting/strategies", "description": "List strategies"},
    {"domain": "Backtesting", "method": "POST", "path": "/api/v1/backtesting/run", "description": "Run backtest"},
    {"domain": "Backtesting", "method": "GET", "path": "/api/v1/backtesting/performance/{id}", "description": "Backtest performance"},
    {"domain": "Backtesting", "method": "POST", "path": "/api/v1/backtesting/compare", "description": "Compare backtests"},

    {"domain": "Analytics", "method": "POST", "path": "/api/v1/analytics/correlation", "description": "Correlation matrix"},
    {"domain": "Analytics", "method": "POST", "path": "/api/v1/analytics/pca", "description": "PCA analysis"},
    {"domain": "Analytics", "method": "POST", "path": "/api/v1/analytics/factor-analysis", "description": "Factor analysis"},
    {"domain": "Analytics", "method": "POST", "path": "/api/v1/analytics/return-attribution", "description": "Return attribution"},

    {"domain": "Data", "method": "GET", "path": "/api/v1/data/market-status", "description": "Market status"},
    {"domain": "Data", "method": "GET", "path": "/api/v1/data/quote/{ticker}", "description": "Real-time quote"},
    {"domain": "Data", "method": "POST", "path": "/api/v1/data/historical", "description": "Historical data"},
    {"domain": "Data", "method": "GET", "path": "/api/v1/data/quality-check", "description": "Data quality check"},

    {"domain": "Market Analysis", "method": "POST", "path": "/api/v1/market-analysis/technical-analysis", "description": "Technical indicators"},
    {"domain": "Market Analysis", "method": "POST", "path": "/api/v1/market-analysis/volatility-comparison", "description": "Volatility comparison"},
    {"domain": "Market Analysis", "method": "POST", "path": "/api/v1/market-analysis/trend-analysis", "description": "Trend analysis"},
    {"domain": "Market Analysis", "method": "GET", "path": "/api/v1/market-analysis/screener", "description": "Technical screener"},
    {"domain": "Market Analysis", "method": "GET", "path": "/api/v1/market-analysis/price-levels/{ticker}", "description": "Support/resistance"},

    {"domain": "Signals", "method": "POST", "path": "/api/v1/signals/generate", "description": "Generate signals"},
    {"domain": "Signals", "method": "GET", "path": "/api/v1/signals/current/{ticker}", "description": "Current signals"},
    {"domain": "Signals", "method": "POST", "path": "/api/v1/signals/backtest", "description": "Backtest signals"},
    {"domain": "Signals", "method": "POST", "path": "/api/v1/signals/screen", "description": "Screen universe"},

    {"domain": "Liquidity", "method": "POST", "path": "/api/v1/liquidity/order-book", "description": "Order book simulation"},
    {"domain": "Liquidity", "method": "POST", "path": "/api/v1/liquidity/metrics", "description": "Liquidity metrics"},
    {"domain": "Liquidity", "method": "POST", "path": "/api/v1/liquidity/market-impact", "description": "Market impact"},
    {"domain": "Liquidity", "method": "POST", "path": "/api/v1/liquidity/flash-crash", "description": "Flash crash simulation"},
    {"domain": "Liquidity", "method": "GET", "path": "/api/v1/liquidity/heatmap/{ticker}", "description": "Intraday heatmap"},

    {"domain": "Systemic Risk", "method": "POST", "path": "/api/v1/systemic-risk/network-analysis", "description": "Network analysis"},
    {"domain": "Systemic Risk", "method": "POST", "path": "/api/v1/systemic-risk/covar", "description": "CoVaR, SRISK"},
    {"domain": "Systemic Risk", "method": "POST", "path": "/api/v1/systemic-risk/fragility-index", "description": "Fragility index"},
    {"domain": "Systemic Risk", "method": "POST", "path": "/api/v1/systemic-risk/contagion", "description": "Contagion cascade"},
    {"domain": "Systemic Risk", "method": "GET", "path": "/api/v1/systemic-risk/too-big-to-fail", "description": "TBTF scoring"},

    {"domain": "Execution", "method": "POST", "path": "/api/v1/execution/market-impact", "description": "Market impact models"},
    {"domain": "Execution", "method": "POST", "path": "/api/v1/execution/vwap-schedule", "description": "VWAP schedule"},
    {"domain": "Execution", "method": "POST", "path": "/api/v1/execution/twap-schedule", "description": "TWAP schedule"},
    {"domain": "Execution", "method": "POST", "path": "/api/v1/execution/optimal-trajectory", "description": "Optimal trajectory"},
    {"domain": "Execution", "method": "POST", "path": "/api/v1/execution/cost-analysis", "description": "Execution cost analysis"},

    {"domain": "Compliance", "method": "POST", "path": "/api/v1/compliance/trade-check", "description": "Pre-trade compliance"},
    {"domain": "Compliance", "method": "GET", "path": "/api/v1/compliance/audit-log", "description": "Audit log"},
    {"domain": "Compliance", "method": "POST", "path": "/api/v1/compliance/policy/evaluate", "description": "Policy evaluation"},
    {"domain": "Compliance", "method": "POST", "path": "/api/v1/compliance/regulatory-report", "description": "Regulatory reports"},
    {"domain": "Compliance", "method": "GET", "path": "/api/v1/compliance/gdpr/status", "description": "GDPR status"},
    {"domain": "Compliance", "method": "GET", "path": "/api/v1/compliance/position-limits", "description": "Position limits"},

    {"domain": "UAT", "method": "POST", "path": "/api/v1/uat/scenarios/run", "description": "Run UAT scenarios"},
    {"domain": "UAT", "method": "GET", "path": "/api/v1/uat/bugs", "description": "Bug reports"},
    {"domain": "UAT", "method": "POST", "path": "/api/v1/uat/feedback", "description": "Submit feedback"},
    {"domain": "UAT", "method": "GET", "path": "/api/v1/uat/performance-validation", "description": "Performance validation"},
    {"domain": "UAT", "method": "POST", "path": "/api/v1/uat/stress-monitor/analyze", "description": "Trader stress analysis"},
    {"domain": "UAT", "method": "GET", "path": "/api/v1/uat/ab-tests", "description": "A/B test results"},

    {"domain": "Health", "method": "GET", "path": "/health", "description": "API health check"},
    {"domain": "Health", "method": "GET", "path": "/health/detailed", "description": "Detailed health"},
    {"domain": "Health", "method": "GET", "path": "/health/readiness", "description": "Readiness probe"},
    {"domain": "Health", "method": "GET", "path": "/health/liveness", "description": "Liveness probe"},
]
