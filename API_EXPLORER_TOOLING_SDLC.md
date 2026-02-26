# **API DEVELOPER TOOLING SUITE — COMPLETE SDLC DOCUMENTATION**

## **PROJECT OVERVIEW**

**Project Name:** QuantLib Pro — API Developer Tooling Suite  
**Sub-Projects:**
1. Streamlit API Explorer (Interactive UI)
2. Python SDK / Client Library
3. CLI Tool (Command-Line Interface)
4. Postman / OpenAPI Collection  

**Parent Project:** QuantLib Pro — Unified Quantitative Finance Suite  
**Document Version:** 1.0  
**Date:** February 25, 2026  
**Developer:** tubakhxn  
**Methodology:** Agile SDLC with DevOps Integration  
**Base API Version Targeted:** QuantLib Pro API v1.0.0 (`http://localhost:8000`)  
**API Domain Count:** 17 domains | 60+ endpoints  
**Streamlit App Version:** Pages 0–16 (17 pages)

---

## **EXECUTIVE SUMMARY**

The QuantLib Pro API currently exposes 60+ REST endpoints across 17 quantitative finance domains. While the API is fully functional with Swagger UI at `/docs`, non-technical users and quantitative analysts lack ergonomic, purpose-built access tools.

This SDLC defines the design, implementation, testing, and deployment of four complementary developer-facing tools:

| Tool | Audience | Interface | Priority |
|------|----------|-----------|----------|
| **Streamlit API Explorer** | Analysts, traders, all app users | Web UI (in-app) | P0 — Critical |
| **Python SDK** | Developers, quants integrating programmatically | Python library | P1 — High |
| **CLI Tool** | DevOps, power users, CI/CD pipelines | Terminal | P1 — High |
| **Postman Collection** | API testers, QA engineers | Postman/OpenAPI | P2 — Medium |

---

## **PHASE 1: REQUIREMENTS ANALYSIS**

### **1.1 PROBLEM STATEMENT**

#### **Current Pain Points**
| Pain Point | Impact | Affected Users |
|-----------|--------|---------------|
| Swagger UI (`/docs`) is generic, not domain-optimized | Low discoverability of domain-specific endpoints | All users |
| No code generation for common workflows | Developer friction; repeated boilerplate | Developers |
| No terminal access to API | Cannot integrate into scripts, CI/CD | DevOps / Power users |
| No pre-configured test collections | Manual setup for every new tester | QA / Testers |
| API auth (JWT) is manual copy-paste in Swagger | Poor UX; sessions expire unnoticed | All users |
| No response visualization beyond raw JSON | Numeric data hard to interpret | Analysts / Traders |
| No request history or replay | Investigations require manual re-entry | Analysts |

#### **Business Justification**
- **Time Saved**: Pre-filled forms and auto-auth reduce API testing from 5 min → 30 seconds per endpoint
- **Adoption**: Streamlit Explorer increases API usage by estimated 3–5x (embedded in existing app)
- **Developer Experience**: SDK + CLI reduce integration effort from days to hours
- **Reproducibility**: Postman collection ensures consistent test coverage across QA cycles

---

### **1.2 STAKEHOLDER ANALYSIS**

| Stakeholder | Role | Primary Need | Success Metric |
|------------|------|-------------|----------------|
| **Quantitative Analysts** | Primary users | Explore portfolio/risk APIs visually | <30s to get first result |
| **Portfolio Managers** | Secondary users | Run ad-hoc optimization + risk checks | Self-service without dev help |
| **Developers / Quants** | Integrators | SDK for scripted workflows | Import and call in <5 lines |
| **DevOps Engineers** | Automation | CLI for CI/CD pipelines | Bash scriptable |
| **QA Engineers** | Testers | Postman collection for regression | All 60+ endpoints coverable |
| **Compliance Officers** | Auditors | Compliance endpoint explorer | Audit log accessible via UI |

---

### **1.3 FUNCTIONAL REQUIREMENTS**

#### **FR-1: Streamlit API Explorer**

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Display all 17 API domain categories in a collapsible sidebar | P0 |
| FR-1.2 | Show all endpoints per domain with HTTP method badges (GET/POST) | P0 |
| FR-1.3 | Auto-generate dynamic input forms from endpoint parameter schemas | P0 |
| FR-1.4 | Execute API requests directly from the UI with one click | P0 |
| FR-1.5 | Display raw JSON response with syntax highlighting | P0 |
| FR-1.6 | Detect numeric arrays in responses and auto-render charts | P1 |
| FR-1.7 | Detect tabular data in responses and render as `st.dataframe` | P1 |
| FR-1.8 | Persist JWT token across Streamlit session state | P0 |
| FR-1.9 | Provide one-click login form that stores auth token | P0 |
| FR-1.10 | Generate Python SDK code snippet for any executed request | P1 |
| FR-1.11 | Generate `curl` command snippet for any executed request | P1 |
| FR-1.12 | Maintain request history (last 20 calls) per session | P2 |
| FR-1.13 | Allow users to bookmark/favorite endpoints | P2 |
| FR-1.14 | Export response data as CSV or JSON download | P2 |
| FR-1.15 | Show endpoint latency (response time in ms) after each call | P1 |
| FR-1.16 | Pre-fill forms with realistic example values for all endpoints | P1 |
| FR-1.17 | Group endpoints by domain with search/filter bar | P2 |
| FR-1.18 | Display API health status indicator (live `/health` check) | P1 |

#### **FR-2: Python SDK**

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Provide one top-level `QuantLibClient` class | P0 |
| FR-2.2 | Expose one property per domain (e.g., `client.portfolio`, `client.risk`) | P0 |
| FR-2.3 | Each domain class exposes typed methods per endpoint | P0 |
| FR-2.4 | Methods accept Python-native types (lists, dicts, floats) | P0 |
| FR-2.5 | Responses return Pydantic models or pandas DataFrames automatically | P1 |
| FR-2.6 | Handle JWT auth transparently (auto-refresh on expiry) | P0 |
| FR-2.7 | Support both sync and async invocation (`asyncio`) | P1 |
| FR-2.8 | Support API key auth as alternative to JWT | P1 |
| FR-2.9 | Configurable base URL (local dev / staging / production) | P0 |
| FR-2.10 | Built-in retry logic (3 attempts with exponential backoff) | P1 |
| FR-2.11 | Raise typed exceptions (`QuantLibAPIError`, `AuthError`, `RateLimitError`) | P1 |
| FR-2.12 | Installable via `pip install quantlib-pro-client` | P0 |
| FR-2.13 | Full type hints (py.typed marker) for IDE autocomplete | P1 |
| FR-2.14 | Bundled Jupyter notebook examples (one per domain) | P2 |

#### **FR-3: CLI Tool**

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Provide `quantlib` top-level command | P0 |
| FR-3.2 | Sub-commands mirror API domains (e.g., `quantlib portfolio optimize`) | P0 |
| FR-3.3 | Support `--json` flag to output raw JSON | P0 |
| FR-3.4 | Support `--table` flag to output formatted table (rich/tabulate) | P1 |
| FR-3.5 | `quantlib login` stores JWT token in `~/.quantlib/credentials` | P0 |
| FR-3.6 | `quantlib logout` clears stored credentials | P0 |
| FR-3.7 | `quantlib endpoints list` prints all available endpoint paths | P1 |
| FR-3.8 | `quantlib endpoints list --domain portfolio` filters by domain | P1 |
| FR-3.9 | Support reading request body from JSON file (`--file request.json`) | P1 |
| FR-3.10 | Support piping JSON input (`echo '{}' | quantlib risk var`) | P2 |
| FR-3.11 | `quantlib health` returns live health check result | P0 |
| FR-3.12 | Shell completion for Bash, Zsh, Fish | P2 |
| FR-3.13 | `--verbose` flag for HTTP request/response details | P1 |
| FR-3.14 | Exit codes: 0 (success), 1 (API error), 2 (auth error), 3 (network error) | P1 |

#### **FR-4: Postman Collection**

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Collection covers all 60+ endpoints | P0 |
| FR-4.2 | Organized into folders matching 17 API domains | P0 |
| FR-4.3 | All requests include valid example request bodies | P0 |
| FR-4.4 | Pre-request script auto-injects JWT token | P0 |
| FR-4.5 | Login request stores token to collection variable | P0 |
| FR-4.6 | Test scripts validate status code 200 on all GET endpoints | P1 |
| FR-4.7 | Test scripts validate required response fields exist | P1 |
| FR-4.8 | Environment files: Local, Staging, Production | P1 |
| FR-4.9 | Export as `quantlib-pro-api.postman_collection.json` | P0 |
| FR-4.10 | Postman monitor configuration for scheduled health checks | P2 |

---

### **1.4 NON-FUNCTIONAL REQUIREMENTS**

| Category | Requirement | Target Value |
|----------|-------------|-------------|
| **Performance** | API Explorer page loads in under | <2 seconds |
| **Performance** | API request round-trip (Explorer → API → response rendered) | <5 seconds |
| **Performance** | SDK method call overhead vs raw HTTP | <50ms |
| **Reliability** | SDK retry success rate on 5xx errors | >95% |
| **Usability** | First successful API call without documentation | <3 minutes |
| **Compatibility** | Python SDK versions supported | Python 3.10+ |
| **Compatibility** | CLI OS support | Windows, macOS, Linux |
| **Security** | Credentials stored in local keyring (not plaintext) | Required |
| **Security** | No secrets logged in verbose mode | Required |
| **Maintainability** | New endpoint added to Explorer with | <15 min effort |
| **Accessibility** | Streamlit Explorer WCAG 2.1 AA | Target |

---

## **PHASE 2: SYSTEM DESIGN & ARCHITECTURE**

### **2.1 HIGH-LEVEL ARCHITECTURE**

```
┌──────────────────────────────────────────────────────────────────┐
│                    ACCESS LAYER (Developer Tools)                 │
├─────────────────┬─────────────────┬──────────────┬───────────────┤
│  Streamlit      │  Python SDK     │  CLI Tool    │  Postman      │
│  API Explorer   │  (pip package)  │  (quantlib)  │  Collection   │
│  pages/17_      │  quantlib_api/  │  quantlib_   │  postman/     │
│  API_Explorer   │  client.py      │  cli/cli.py  │  collection   │
│  .py            │                 │              │  .json        │
└────────┬────────┴────────┬────────┴──────┬───────┴───────────────┘
         │                 │               │
         └────────────────►│◄──────────────┘
                           ▼
         ┌─────────────────────────────────────┐
         │         HTTP Layer (httpx/requests) │
         │         Base URL: localhost:8000     │
         │         Auth: Bearer JWT / API Key   │
         └─────────────────┬───────────────────┘
                           ▼
         ┌─────────────────────────────────────┐
         │        QuantLib Pro FastAPI          │
         │           main_api.py               │
         │    17 Router Domains / 60+ endpoints │
         │         /api/v1/{domain}/...         │
         └─────────────────┬───────────────────┘
                           ▼
         ┌─────────────────────────────────────┐
         │           quantlib_pro/             │
         │     Python modules + numpy          │
         │     scipy + pandas computation      │
         └─────────────────────────────────────┘
```

---

### **2.2 STREAMLIT API EXPLORER — DETAILED DESIGN**

#### **File Location**
```
pages/17_API_Explorer.py
```

#### **Component Architecture**

```
17_API_Explorer.py
│
├── SIDEBAR
│   ├── 🔑 Authentication Widget
│   │   ├── username/password input
│   │   ├── [Login] button → POST /auth/login → stores token in st.session_state
│   │   └── status badge: 🟢 Authenticated / 🔴 Not Authenticated
│   │
│   ├── 🌐 API Status Badge (live ping to /health)
│   │
│   ├── 🔍 Endpoint Search Box
│   │
│   └── 📁 Domain Tree (17 domains)
│       ├── 📊 Portfolio (5 endpoints)
│       ├── ⚙️  Options (4 endpoints)
│       ├── 🛡️  Risk (5 endpoints)
│       ├── 🎯 Market Regime (4 endpoints)
│       ├── 📉 Volatility (4 endpoints)
│       ├── 🌍 Macro (3 endpoints)
│       ├── 📈 Backtesting (4 endpoints)
│       ├── 🔬 Analytics (4 endpoints)
│       ├── 💾 Data (4 endpoints)
│       ├── 📊 Market Analysis (5 endpoints)
│       ├── 🔔 Trading Signals (4 endpoints)
│       ├── 💧 Liquidity (5 endpoints)
│       ├── 🌐 Systemic Risk (5 endpoints)
│       ├── ⚡ Execution (5 endpoints)
│       ├── ✅ Compliance (6 endpoints)
│       ├── 🧪 UAT (6 endpoints)
│       └── ❤️  Health (2 endpoints)
│
└── MAIN PANEL
    ├── Endpoint Header
    │   ├── [POST] or [GET] badge (colored)
    │   ├── Path: /api/v1/portfolio/optimize
    │   └── Description text
    │
    ├── 📝 Request Configuration
    │   ├── Dynamic form (st.text_input / st.number_input / st.multiselect)
    │   ├── Fields auto-generated from ENDPOINT_CATALOG schema definitions
    │   └── [Send Request 🚀] button
    │
    ├── 📊 Response Panel
    │   ├── Status badge: 200 OK | latency: 143ms
    │   ├── Auto-viz: chart if array detected / dataframe if table detected
    │   └── Raw JSON (st.json / st.code)
    │
    ├── </> Code Generator Tabs
    │   ├── [🐍 Python SDK]
    │   ├── [⚡ curl]
    │   └── [📋 Copy]
    │
    └── 🕐 Request History (collapsible, last 20 requests)
```

#### **Endpoint Catalog Data Structure**

The Explorer is driven by a declarative `ENDPOINT_CATALOG` dictionary, making it trivial to add new endpoints without changing UI code:

```python
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
                "description": "Compute optimal portfolio weights using Modern Portfolio Theory",
                "fields": [
                    {"name": "tickers", "type": "list_str", "label": "Tickers", 
                     "example": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
                     "help": "Comma-separated list of stock tickers"},
                    {"name": "budget", "type": "float", "label": "Budget ($)", 
                     "example": 100000.0, "min": 1000.0, "max": 10000000.0},
                    {"name": "risk_free_rate", "type": "float", "label": "Risk-free Rate",
                     "example": 0.045, "min": 0.0, "max": 0.20},
                    {"name": "optimization_target", "type": "select", 
                     "options": ["sharpe", "min_volatility", "max_return"],
                     "example": "sharpe"},
                ],
                "response_viz": "weights_pie_chart"
            },
            # ... more endpoints
        ]
    },
    "Risk": {
        "icon": "🛡️",
        "prefix": "/api/v1/risk",
        "endpoints": [
            {
                "id": "risk_var",
                "label": "Value at Risk",
                "method": "POST",
                "path": "/var",
                "description": "Compute VaR and CVaR using historical, parametric, or Monte Carlo methods",
                "fields": [
                    {"name": "portfolio_id", "type": "str", "example": "DEMO_PORT"},
                    {"name": "confidence_level", "type": "float", "example": 0.95,
                     "min": 0.90, "max": 0.999},
                    {"name": "method", "type": "select",
                     "options": ["historical", "parametric", "monte_carlo"],
                     "example": "historical"},
                    {"name": "horizon_days", "type": "int", "example": 10},
                ],
                "response_viz": "histogram"
            },
        ]
    },
    # ... all 17 domains
}
```

#### **Response Visualization Engine**

Auto-detect and render response content based on shapes:

| Response Shape | Detected By | Rendered As |
|---------------|-------------|-------------|
| `{"weights": {...}}` | dict of ticker → float | Pie chart (plotly) |
| `{"returns": [0.01, -0.02, ...]}` | key ending in `s`, value is array | Line chart |
| `{"correlation_matrix": [[...]]}` | 2D array | Heatmap |
| `{"positions": [{"ticker":..., "value":...}]}` | list of objects | `st.dataframe` |
| `{"var_95": 0.032, "cvar_95": 0.041, ...}` | flat numeric dict | Bar chart or metric cards |
| Any other JSON | fallback | `st.json` with expand |

---

### **2.3 PYTHON SDK — DETAILED DESIGN**

#### **Package Structure**

```
quantlib_api/
├── __init__.py              # Exports QuantLibClient
├── client.py                # Main QuantLibClient class
├── auth.py                  # JWT/API key auth manager
├── exceptions.py            # Typed exception hierarchy
├── models.py                # Pydantic request/response models
├── _http.py                 # httpx session wrapper with retry
├── resources/
│   ├── __init__.py
│   ├── portfolio.py         # PortfolioResource
│   ├── options.py           # OptionsResource
│   ├── risk.py              # RiskResource
│   ├── regime.py            # RegimeResource
│   ├── volatility.py        # VolatilityResource
│   ├── macro.py             # MacroResource
│   ├── backtesting.py       # BacktestingResource
│   ├── analytics.py         # AnalyticsResource
│   ├── data.py              # DataResource
│   ├── market_analysis.py   # MarketAnalysisResource
│   ├── signals.py           # SignalsResource
│   ├── liquidity.py         # LiquidityResource
│   ├── systemic_risk.py     # SystemicRiskResource
│   ├── execution.py         # ExecutionResource
│   ├── compliance.py        # ComplianceResource
│   └── uat.py               # UATResource
├── py.typed                 # PEP 561 marker
└── examples/
    ├── portfolio_workflow.ipynb
    ├── risk_analysis.ipynb
    ├── options_pricing.ipynb
    ├── market_regime.ipynb
    └── execution_analysis.ipynb
```

#### **Client Interface Design**

```python
# Usage example — full workflow
from quantlib_api import QuantLibClient

client = QuantLibClient(
    base_url="http://localhost:8000",   # or set QUANTLIB_URL env var
    username="demo",                     # or use api_key=
    password="demo123",
    auto_login=True                      # fetch token immediately
)

# Portfolio optimization
result = client.portfolio.optimize(
    tickers=["AAPL", "GOOGL", "MSFT"],
    budget=100_000,
    optimization_target="sharpe"
)
print(result.weights)          # {"AAPL": 0.45, "GOOGL": 0.30, "MSFT": 0.25}
print(result.sharpe_ratio)     # 1.82
print(result.as_dataframe())   # pandas DataFrame

# Risk analysis
var = client.risk.var(
    portfolio=result.weights,
    confidence_level=0.95,
    method="monte_carlo"
)
print(f"VaR 95%: {var.var_95:.2%}")

# Market regime detection
regime = client.regime.detect(tickers=["SPY"], lookback_days=252)
print(regime.current_regime)   # "BULL"

# Execution optimization
schedule = client.execution.vwap_schedule(
    ticker="AAPL",
    shares=50_000,
    time_horizon_hours=4
)
print(schedule.as_dataframe())  # pandas DataFrame with slices

# Async support
import asyncio
async def run():
    result = await client.portfolio.aoptimize(tickers=["AAPL", "GOOGL"])
    return result
asyncio.run(run())
```

#### **Exception Hierarchy**

```python
QuantLibError (base)
├── QuantLibAPIError        # 4xx/5xx API responses
│   ├── QuantLibAuthError   # 401/403
│   ├── QuantLibNotFoundError  # 404
│   └── QuantLibRateLimitError # 429 (includes .retry_after)
├── QuantLibNetworkError    # httpx connection errors
└── QuantLibValidationError # Pydantic validation failures
```

---

### **2.4 CLI TOOL — DETAILED DESIGN**

#### **Package Structure**

```
quantlib_cli/
├── __init__.py
├── cli.py               # Click root group + all commands
├── auth_store.py        # Credential persistence (~/.quantlib/credentials)
├── formatters.py        # JSON / table / rich output formatters
└── completions/
    ├── quantlib.bash
    ├── quantlib.zsh
    └── quantlib.fish
```

#### **Command Tree**

```
quantlib
├── login                     # Authenticate and store credentials
│   --url, --username, --password
├── logout                    # Clear stored credentials
├── health                    # Check API health
│   --url
│   --watch                   # Continuous polling mode
│
├── endpoints
│   ├── list                  # List all endpoints
│   │   --domain [portfolio|risk|options|...]
│   │   --format [table|json]
│   └── describe <path>       # Show endpoint schema/docs
│
├── portfolio
│   ├── optimize              # POST /api/v1/portfolio/optimize
│   │   --tickers AAPL,GOOGL,MSFT
│   │   --budget 100000
│   │   --target sharpe
│   ├── performance           # GET /api/v1/portfolio/performance
│   └── efficient-frontier    # POST /api/v1/portfolio/efficient-frontier
│
├── risk
│   ├── var                   # POST /api/v1/risk/var
│   │   --portfolio-id <id>
│   │   --confidence 0.95
│   │   --method historical
│   ├── stress-test           # POST /api/v1/risk/stress-test
│   └── tail-risk             # POST /api/v1/risk/tail-risk
│
├── options
│   ├── price                 # POST /api/v1/options/price
│   │   --ticker AAPL --strike 175 --expiry 2026-06-20 --type call
│   └── greeks                # POST /api/v1/options/greeks
│
├── regime
│   ├── detect                # POST /api/v1/regime/detect
│   └── current               # GET  /api/v1/regime/current
│
├── volatility
│   └── surface               # POST /api/v1/volatility/surface
│
├── signals
│   ├── generate              # POST /api/v1/signals/generate
│   ├── current               # GET  /api/v1/signals/current/{ticker}
│   └── backtest              # POST /api/v1/signals/backtest
│
├── liquidity
│   ├── metrics               # POST /api/v1/liquidity/metrics
│   └── market-impact         # POST /api/v1/liquidity/market-impact
│
├── execution
│   ├── vwap                  # POST /api/v1/execution/vwap-schedule
│   ├── twap                  # POST /api/v1/execution/twap-schedule
│   └── optimal-trajectory    # POST /api/v1/execution/optimal-trajectory
│
├── compliance
│   ├── trade-check           # POST /api/v1/compliance/trade-check
│   ├── position-limits       # GET  /api/v1/compliance/position-limits
│   └── gdpr-status           # GET  /api/v1/compliance/gdpr/status
│
├── systemic-risk
│   ├── network               # POST /api/v1/systemic-risk/network-analysis
│   └── too-big-to-fail       # GET  /api/v1/systemic-risk/too-big-to-fail
│
└── data
    ├── market-status         # GET  /api/v1/data/market-status
    └── quote                 # GET  /api/v1/data/quote/{ticker}
```

#### **Usage Examples**

```bash
# Authenticate
quantlib login --username demo --password demo123

# Portfolio optimization
quantlib portfolio optimize --tickers AAPL,GOOGL,MSFT --budget 100000 --target sharpe

# Options pricing
quantlib options price --ticker AAPL --strike 175.0 --expiry 2026-06-20 --type call

# Risk with table output
quantlib risk var --confidence 0.95 --method monte_carlo --table

# Execute signals screen
quantlib signals generate --ticker TSLA --strategies RSI,MACD,Bollinger --json

# Read from file
quantlib portfolio optimize --file portfolio_request.json

# Watch API health
quantlib health --watch --interval 30
```

---

### **2.5 POSTMAN COLLECTION STRUCTURE**

```
QuantLib Pro API.postman_collection.json
├── 🔑 Authentication
│   ├── Login (POST /auth/login) → saves {{token}}
│   └── Validate Token (GET /auth/validate)
│
├── ❤️  Health & Status
│   ├── Health Check (GET /health)
│   └── Detailed Health (GET /health/detailed)
│
├── 📊 Portfolio
│   ├── Optimize Portfolio
│   ├── Portfolio Performance
│   ├── Efficient Frontier
│   ├── Sharpe Analysis
│   └── Portfolio Rebalance
│
├── ⚙️  Options & Derivatives
│   ├── Price Option (BS)
│   ├── Calculate Greeks
│   ├── Monte Carlo Pricing
│   └── Volatility Surface
│
├── 🛡️  Risk Analysis
│   ├── Value at Risk (VaR)
│   ├── CVaR Calculation
│   ├── Stress Testing
│   ├── Tail Risk Analysis
│   └── Drawdown Analysis
│
├── 🎯 Market Regime
│   ├── Detect Regime
│   ├── Regime History
│   ├── Current Regime (GET)
│   └── Regime Probabilities
│
├── 📉 Volatility
│   ├── Volatility Surface
│   ├── GARCH Analysis
│   ├── Realized Volatility
│   └── Volatility Term Structure
│
├── 🌍 Macro Analysis
│   ├── Macro Indicators
│   ├── Correlation Regime
│   └── Economic Calendar
│
├── 📈 Backtesting
│   ├── List Strategies
│   ├── Run Backtest
│   ├── Strategy Performance
│   └── Compare Strategies
│
├── 🔬 Advanced Analytics
│   ├── Correlation Analysis
│   ├── PCA Analysis
│   ├── Factor Analysis
│   └── Return Attribution
│
├── 💾 Data Management
│   ├── Market Status (GET)
│   ├── Stock Quote (GET)
│   ├── Historical Data
│   └── Data Quality Check
│
├── 📊 Market Analysis
│   ├── Technical Analysis
│   ├── Volatility Comparison
│   ├── Trend Analysis
│   ├── Market Screener
│   └── Price Levels (GET)
│
├── 🔔 Trading Signals
│   ├── Generate Signals
│   ├── Backtest Signal
│   ├── Screen Universe
│   └── Current Signals (GET)
│
├── 💧 Liquidity
│   ├── Order Book Simulation
│   ├── Liquidity Metrics
│   ├── Market Impact
│   ├── Flash Crash Simulation
│   └── Intraday Heatmap (GET)
│
├── 🌐 Systemic Risk
│   ├── Network Analysis
│   ├── CoVaR & SRISK
│   ├── Fragility Index
│   ├── Contagion Cascade
│   └── Too-Big-to-Fail (GET)
│
├── ⚡ Execution
│   ├── Market Impact Models
│   ├── VWAP Schedule
│   ├── TWAP Schedule
│   ├── Optimal Trajectory
│   └── Cost Analysis
│
├── ✅ Compliance
│   ├── Trade Check
│   ├── Audit Log (GET)
│   ├── Policy Evaluate
│   ├── Regulatory Report
│   ├── GDPR Status (GET)
│   └── Position Limits (GET)
│
└── 🧪 UAT & Testing
    ├── Run UAT Scenarios
    ├── Bug Reports (GET)
    ├── Submit Feedback
    ├── Performance Validation (GET)
    ├── Stress Monitor Analyze
    └── A/B Tests (GET)
```

#### **Postman Environment Variables**

```json
// environments/local.postman_environment.json
{
  "name": "QuantLib Pro - Local",
  "values": [
    {"key": "base_url",  "value": "http://localhost:8000"},
    {"key": "username",  "value": "demo"},
    {"key": "password",  "value": "demo123"},
    {"key": "token",     "value": ""},
    {"key": "api_key",   "value": ""}
  ]
}

// environments/production.postman_environment.json  
{
  "name": "QuantLib Pro - Production",
  "values": [
    {"key": "base_url",  "value": "https://api.quantlibpro.com"},
    {"key": "username",  "value": ""},
    {"key": "password",  "value": ""},
    {"key": "token",     "value": ""},
    {"key": "api_key",   "value": ""}
  ]
}
```

---

## **PHASE 3: IMPLEMENTATION PLAN**

### **3.1 SPRINT BREAKDOWN**

#### **Sprint 1 (Week 1) — Streamlit API Explorer Core**

| Task | File | Estimate |
|------|------|----------|
| Define `ENDPOINT_CATALOG` dict for all 17 domains | `pages/17_API_Explorer.py` | 3h |
| Build sidebar: domain tree, auth widget, health badge | `pages/17_API_Explorer.py` | 2h |
| Build dynamic form generator (field type dispatcher) | `pages/17_API_Explorer.py` | 4h |
| Build request executor (httpx POST/GET with session JWT) | `pages/17_API_Explorer.py` | 2h |
| Build raw JSON + `st.json` response panel | `pages/17_API_Explorer.py` | 1h |
| Add request latency measurement | `pages/17_API_Explorer.py` | 1h |
| **Sprint 1 Total** | | **13h** |

#### **Sprint 2 (Week 2) — Response Visualization + Code Generation**

| Task | File | Estimate |
|------|------|----------|
| Auto-viz engine: detect + render charts (plotly) | `pages/17_API_Explorer.py` | 4h |
| Auto-viz: dataframe detection + `st.dataframe` | `pages/17_API_Explorer.py` | 2h |
| Python SDK code snippet generator | `pages/17_API_Explorer.py` | 2h |
| curl command generator | `pages/17_API_Explorer.py` | 1h |
| Copy-to-clipboard button | `pages/17_API_Explorer.py` | 1h |
| Request history (session state, last 20) | `pages/17_API_Explorer.py` | 2h |
| Endpoint search/filter bar | `pages/17_API_Explorer.py` | 2h |
| **Sprint 2 Total** | | **14h** |

#### **Sprint 3 (Week 3) — Python SDK**

| Task | File | Estimate |
|------|------|----------|
| `_http.py`: httpx session wrapper with retry + timeout | `quantlib_api/_http.py` | 3h |
| `auth.py`: JWT token manager with auto-refresh | `quantlib_api/auth.py` | 3h |
| `exceptions.py`: typed exception hierarchy | `quantlib_api/exceptions.py` | 1h |
| `client.py`: `QuantLibClient` main class | `quantlib_api/client.py` | 2h |
| 17 resource classes (domain.py files) | `quantlib_api/resources/*.py` | 8h |
| `models.py`: Pydantic request/response models | `quantlib_api/models.py` | 4h |
| Async support (`aiohttp` or `httpx` async client) | `quantlib_api/_http.py` | 3h |
| `pyproject.toml`: package config, `pip install` | `pyproject.toml` | 1h |
| **Sprint 3 Total** | | **25h** |

#### **Sprint 4 (Week 4) — CLI Tool**

| Task | File | Estimate |
|------|------|----------|
| `cli.py`: Click root + `login`/`logout`/`health` commands | `quantlib_cli/cli.py` | 4h |
| `auth_store.py`: credential persistence | `quantlib_cli/auth_store.py` | 2h |
| `formatters.py`: JSON + rich table output | `quantlib_cli/formatters.py` | 3h |
| Domain sub-commands for all 17 domains | `quantlib_cli/cli.py` | 8h |
| Exit code conventions + error handling | `quantlib_cli/cli.py` | 2h |
| `endpoints list`/`describe` commands | `quantlib_cli/cli.py` | 2h |
| Shell completion scripts (bash/zsh/fish) | `quantlib_cli/completions/` | 2h |
| `--file` flag for JSON body input | `quantlib_cli/cli.py` | 1h |
| **Sprint 4 Total** | | **24h** |

#### **Sprint 5 (Week 5) — Postman Collection + Polish**

| Task | File | Estimate |
|------|------|----------|
| Build Postman collection JSON (all 60+ requests) | `postman/collection.json` | 6h |
| Pre-request auth scripts + token variable | `postman/collection.json` | 2h |
| Test scripts (status 200, field validation) | `postman/collection.json` | 3h |
| Environment files: Local, Staging, Production | `postman/environments/` | 1h |
| SDK Jupyter notebook examples (5 notebooks) | `quantlib_api/examples/` | 4h |
| Explorer: CSV/JSON export download button | `pages/17_API_Explorer.py` | 2h |
| Explorer: favorites / bookmark feature | `pages/17_API_Explorer.py` | 2h |
| Documentation + README for all tools | `quantlib_api/README.md` + `quantlib_cli/README.md` | 3h |
| **Sprint 5 Total** | | **23h** |

---

### **3.2 FILE STRUCTURE (DELIVERABLES)**

```
advanced quant/
│
├── pages/
│   └── 17_API_Explorer.py          ← NEW: Streamlit API Explorer
│
├── quantlib_api/                   ← NEW: Python SDK package
│   ├── __init__.py
│   ├── client.py
│   ├── auth.py
│   ├── exceptions.py
│   ├── models.py
│   ├── _http.py
│   ├── py.typed
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── portfolio.py
│   │   ├── options.py
│   │   ├── risk.py
│   │   ├── regime.py
│   │   ├── volatility.py
│   │   ├── macro.py
│   │   ├── backtesting.py
│   │   ├── analytics.py
│   │   ├── data.py
│   │   ├── market_analysis.py
│   │   ├── signals.py
│   │   ├── liquidity.py
│   │   ├── systemic_risk.py
│   │   ├── execution.py
│   │   ├── compliance.py
│   │   └── uat.py
│   └── examples/
│       ├── portfolio_workflow.ipynb
│       ├── risk_analysis.ipynb
│       ├── options_pricing.ipynb
│       ├── market_regime.ipynb
│       └── execution_analysis.ipynb
│
├── quantlib_cli/                   ← NEW: CLI Tool
│   ├── __init__.py
│   ├── cli.py
│   ├── auth_store.py
│   ├── formatters.py
│   └── completions/
│       ├── quantlib.bash
│       ├── quantlib.zsh
│       └── quantlib.fish
│
└── postman/                        ← NEW: Postman Collection
    ├── quantlib-pro-api.postman_collection.json
    └── environments/
        ├── local.postman_environment.json
        ├── staging.postman_environment.json
        └── production.postman_environment.json
```

---

## **PHASE 4: UI/UX DESIGN SPECIFICATION**

### **4.1 STREAMLIT API EXPLORER — VISUAL WIREFRAME**

```
┌───────────────────────────────────────────────────────────────────────┐
│  🔌 QuantLib Pro — API Explorer                              v1.0.0   │
├─────────────────────┬─────────────────────────────────────────────────┤
│  SIDEBAR            │  MAIN AREA                                      │
│                     │                                                  │
│  🔑 Authentication  │  ┌────────────────────────────────────────────┐ │
│  ┌───────────────┐  │  │  [POST]  /api/v1/portfolio/optimize        │ │
│  │ user: demo    │  │  │  Compute optimal portfolio weights (MPT)   │ │
│  │ pass: ••••••• │  │  └────────────────────────────────────────────┘ │
│  │ [Login 🔓]    │  │                                                  │
│  │ 🟢 Logged In  │  │  ⚙️ REQUEST CONFIGURATION                       │
│  └───────────────┘  │  ──────────────────────────────────────────────  │
│                     │  Tickers:  [AAPL] [GOOGL] [MSFT] [+ Add]       │
│  🌐 API: 🟢 Online  │  Budget:   $  100,000                           │
│                     │  Target:   [Sharpe ▾]                           │
│  🔍 [Search...]     │  Risk-free Rate: 0.045                          │
│                     │                                                  │
│  📁 Portfolio  ▶    │              [ 🚀 Send Request ]                │
│  📁 Risk       ▶    │                                                  │
│  📁 Options    ▶    │  ✅ 200 OK  •  143ms                             │
│  📁 Regime     ▶    │  ──────────────────────────────────────────────  │
│  📁 Volatility ▶    │  📊 Portfolio Weights                            │
│  📁 Macro      ▶    │  ┌──────────────────────────────────┐           │
│  📁 Backtesting▶    │  │  🍰 Pie Chart: AAPL 45%          │           │
│  📁 Analytics  ▶    │  │               GOOGL 30%          │           │
│  📁 Data       ▶    │  │               MSFT  25%          │           │
│  📁 Mkt Anal.  ▶    │  └──────────────────────────────────┘           │
│  📁 Signals    ▶    │                                                  │
│  📁 Liquidity  ▶    │  📋 Raw JSON                                     │
│  📁 Sys. Risk  ▶    │  { "optimal_weights": {"AAPL": 0.45, ...}       │
│  📁 Execution  ▶    │    "sharpe_ratio": 1.82,                         │
│  📁 Compliance ▶    │    "expected_return": 0.156,                     │
│  📁 UAT        ▶    │    "volatility": 0.189 }                         │
│  📁 Health     ▶    │                                                  │
│                     │  </> CODE GENERATOR                              │
│  ⭐ Favorites   ▶   │  [🐍 Python SDK] [⚡ curl] [📋 Copy]            │
│  🕐 History    ▶    │  ┌──────────────────────────────────────────┐   │
│                     │  │ from quantlib_api import QuantLibClient   │   │
│                     │  │ client = QuantLibClient(auto_login=True)  │   │
│                     │  │ result = client.portfolio.optimize(       │   │
│                     │  │     tickers=["AAPL","GOOGL","MSFT"],      │   │
│                     │  │     budget=100000,                        │   │
│                     │  │     optimization_target="sharpe"          │   │
│                     │  │ )                                         │   │
│                     │  └──────────────────────────────────────────┘   │
│                     │                                                  │
└─────────────────────┴─────────────────────────────────────────────────┘
```

### **4.2 COLOR SCHEME & HTTP METHOD BADGES**

| HTTP Method | Badge Color | Streamlit CSS |
|------------|-------------|---------------|
| `GET` | 🟢 Green `#2ECC71` | Success |
| `POST` | 🔵 Blue `#3498DB` | Info |
| `PUT` | 🟠 Orange `#E67E22` | Warning |
| `DELETE` | 🔴 Red `#E74C3C` | Error |

### **4.3 FIELD TYPE → STREAMLIT WIDGET MAPPING**

| Field Type | Streamlit Widget | Notes |
|-----------|-----------------|-------|
| `str` | `st.text_input` | — |
| `float` | `st.number_input` | With min/max/step |
| `int` | `st.number_input(step=1)` | — |
| `bool` | `st.checkbox` | — |
| `list_str` | `st.multiselect` or `st.text_input` (comma-sep) | With common options |
| `select` | `st.selectbox` | From `options` list |
| `multi_select` | `st.multiselect` | From `options` list |
| `date` | `st.date_input` | — |
| `datetime` | `st.date_input` + time | — |
| `json` | `st.text_area` | Validated on submit |

---

## **PHASE 5: TESTING STRATEGY**

### **5.1 TEST PLAN**

#### **Unit Tests**

| Component | Test File | Coverage Target |
|-----------|----------|-----------------|
| SDK `_http.py` retry logic | `tests/test_sdk_http.py` | 90% |
| SDK auth token refresh | `tests/test_sdk_auth.py` | 95% |
| SDK resource method serialization | `tests/test_sdk_resources.py` | 85% |
| CLI command parsing | `tests/test_cli.py` | 90% |
| Explorer form field generator | `tests/test_explorer_forms.py` | 80% |
| Explorer code snippet generator | `tests/test_explorer_codegen.py` | 80% |

#### **Integration Tests**

| Scenario | Test | Tool |
|----------|------|------|
| SDK full portfolio workflow | Login → optimize → VaR → backtest | pytest + live API |
| CLI login + portfolio optimize | `quantlib login && quantlib portfolio optimize` | subprocess pytest |
| Explorer all 17 domains submit | Selenium / Playwright headless | E2E |
| Postman collection run all | Newman CLI runner | CI/CD |

#### **Test Scenarios**

```
SCENARIO: SDK portfolio optimization round-trip
  GIVEN: API is running at localhost:8000
  WHEN: QuantLibClient().portfolio.optimize(tickers=["AAPL", "GOOGL"], budget=100000)
  THEN: response.sharpe_ratio > 0
  AND:  sum(response.weights.values()) == pytest.approx(1.0, abs=0.01)
  AND:  all(w >= 0 for w in response.weights.values())

SCENARIO: SDK auto-retry on 503
  GIVEN: API returns 503 twice then 200
  WHEN: client.risk.var(...)
  THEN: method succeeds without raising
  AND:  retry count == 2

SCENARIO: CLI exit code on auth failure
  GIVEN: invalid credentials in ~/.quantlib/credentials
  WHEN: quantlib portfolio optimize --tickers AAPL
  THEN: exit code == 2 (auth error)

SCENARIO: Explorer form renders all fields for portfolio/optimize
  GIVEN: API Explorer page is loaded
  WHEN: user selects "Portfolio" → "Optimize Portfolio"
  THEN: form shows tickers, budget, target, risk_free_rate fields
  AND:  Send Request button is enabled

SCENARIO: Explorer auto-visualizes portfolio weights
  GIVEN: portfolio/optimize request succeeds
  WHEN: response contains optimal_weights dict
  THEN: pie chart is rendered with plotly

SCENARIO: Postman collection Newman runner
  GIVEN: Newman runs quantlib-pro-api.postman_collection.json
  WHEN: all requests execute against local environment
  THEN: 0 test failures
  AND:  all requests return 2xx
```

### **5.2 PERFORMANCE BENCHMARKS**

| Test | Target | Measurement Method |
|------|--------|--------------------|
| SDK `portfolio.optimize()` overhead | <50ms over raw HTTP | Timer decorator |
| CLI startup time | <200ms | `time quantlib health` |
| Explorer page first render | <2s | Streamlit profiler |
| Explorer request → render cycle | <5s | Manual stopwatch |
| Postman collection full run | <60s | Newman `--reporter-cli` |

---

## **PHASE 6: SECURITY DESIGN**

### **6.1 AUTHENTICATION FLOW**

```
Streamlit Explorer:
  User enters username/password → POST /auth/login
  → JWT token stored in st.session_state["token"]
  → Token prepended to all subsequent requests
  → Token expires? → Re-prompt login (session_state cleared)

Python SDK:
  QuantLibClient(auto_login=True) → POST /auth/login on init
  → Token stored in memory (instance variable)
  → On 401 response → auto-refresh via re-login
  → Token never written to disk unless explicitly requested

CLI Tool:
  `quantlib login` → POST /auth/login
  → Token written to ~/.quantlib/credentials (mode 600)
  → On Windows: DPAPI-encrypted via keyring library
  → `quantlib logout` → deletes file
  → --verbose mode: never prints token to stdout (masked as ***)
```

### **6.2 SECRETS MANAGEMENT**

| Scenario | Approach |
|---------|---------|
| SDK: API key in environment | `QUANTLIB_API_KEY` env var |
| CLI: Credentials on disk | `keyring` library (OS keychain integration) |
| Explorer: Token in browser | `st.session_state` (in-memory, server-side) |
| CI/CD Postman: Credentials | Environment variable injection (GitHub Secrets) |

### **6.3 SECURITY REQUIREMENTS**

| Requirement | Implementation |
|-------------|---------------|
| No credentials in logs | SDK/CLI filter auth headers from verbose output |
| No credentials in code | Example config uses placeholder strings only |
| HTTPS enforcement (production) | SDK warns if base_url is not `https://` |
| Token expiry handling | SDK auto-refreshes; Explorer prompts; CLI re-runs login |

---

## **PHASE 7: DEPLOYMENT & DISTRIBUTION**

### **7.1 PYTHON SDK DISTRIBUTION**

```toml
# pyproject.toml additions
[project]
name = "quantlib-pro-client"
version = "1.0.0"
description = "Python SDK for QuantLib Pro quantitative finance API"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "pandas>=2.0",
]

[project.optional-dependencies]
async = ["anyio>=4.0"]
jupyter = ["jupyter>=1.0", "matplotlib>=3.7"]
```

**Distribution Steps:**
1. `python -m build` → generates `dist/quantlib_pro_client-1.0.0-py3-none-any.whl`
2. Local install: `pip install dist/quantlib_pro_client-1.0.0.whl`
3. Future: `pip install quantlib-pro-client` via PyPI

### **7.2 CLI DISTRIBUTION**

```toml
[project.scripts]
quantlib = "quantlib_cli.cli:main"
```

**Installation:**
```bash
pip install -e ".[cli]"   # Development
pip install quantlib-pro-client[cli]  # Production (future PyPI)
```

After install, `quantlib` is available globally in the terminal.

### **7.3 STREAMLIT EXPLORER DEPLOYMENT**

The Explorer page is part of the existing Streamlit multi-page app:

```
# Already handled by virtue of placing in pages/ directory
streamlit run streamlit_app.py
# → Page "17 API Explorer" appears automatically in sidebar
```

No additional deployment steps beyond adding the file.

### **7.4 POSTMAN COLLECTION DISTRIBUTION**

- Committed to `postman/` directory in repository
- Importable via Postman desktop: **File → Import → Upload Files**
- Shareable via Postman Workspace (team cloud sync)
- Runnable via Newman for CI/CD:
  ```bash
  npm install -g newman
  newman run postman/quantlib-pro-api.postman_collection.json \
    --environment postman/environments/local.postman_environment.json \
    --reporters cli,json \
    --reporter-json-export results/postman-results.json
  ```

---

## **PHASE 8: MAINTENANCE & GOVERNANCE**

### **8.1 ADDING A NEW ENDPOINT**

When a new endpoint is added to the FastAPI (e.g., `/api/v1/portfolio/tax-harvest`):

#### **Explorer (pages/17_API_Explorer.py)**
```python
# Add one dict entry to ENDPOINT_CATALOG["Portfolio"]["endpoints"]:
{
    "id": "portfolio_tax_harvest",
    "label": "Tax-Loss Harvesting",
    "method": "POST",
    "path": "/tax-harvest",
    "description": "Identify tax-loss harvesting opportunities",
    "fields": [
        {"name": "portfolio_id", "type": "str", "example": "PORT_001"},
        {"name": "threshold_pct", "type": "float", "example": -0.05},
    ],
    "response_viz": "table"
}
# ← ~10 minutes effort, zero UI code changes needed
```

#### **Python SDK (quantlib_api/resources/portfolio.py)**
```python
def tax_harvest(self, portfolio_id: str, threshold_pct: float = -0.05):
    """Identify tax-loss harvesting opportunities."""
    return self._http.post(
        "/api/v1/portfolio/tax-harvest",
        json={"portfolio_id": portfolio_id, "threshold_pct": threshold_pct}
    )
```

#### **CLI (quantlib_cli/cli.py)**
```python
@portfolio.command("tax-harvest")
@click.option("--portfolio-id", required=True)
@click.option("--threshold", default=-0.05)
@pass_client
def tax_harvest(client, portfolio_id, threshold):
    result = client.portfolio.tax_harvest(portfolio_id, threshold)
    click.echo(format_result(result))
```

#### **Postman**
- Duplicate any existing Portfolio request
- Update method, URL, body JSON

**Estimated maintenance effort per new endpoint:** ~30 minutes total across all tools.

---

### **8.2 VERSIONING STRATEGY**

| Component | Version Strategy |
|-----------|-----------------|
| SDK | Semantic versioning (1.0.0 → 1.1.0 on new endpoints) |
| CLI | Follows SDK version |
| Explorer | No versioning (always reflects current `ENDPOINT_CATALOG`) |
| Postman | Collection schema_version in JSON header |
| API | `/api/v1/` prefix allows future `/api/v2/` without breaking |

---

### **8.3 MONITORING & OBSERVABILITY**

| Metric | Source | Where Visible |
|--------|--------|---------------|
| API Explorer usage (endpoint calls) | Streamlit session events | Server logs |
| SDK call frequency by endpoint | httpx request log | observability module |
| CLI usage patterns | Shell history / OS analytics | N/A |
| API health (live) | `GET /health` | Explorer sidebar badge |
| API error rates from SDK | Exception counts per method | Could feed `/metrics` |

---

## **PHASE 9: COMPLETE IMPLEMENTATION CHECKLIST**

### **9.1 STREAMLIT API EXPLORER**

- [ ] `ENDPOINT_CATALOG` defined for all 17 domains (60+ endpoints)
- [ ] Authentication widget (login form → JWT → session_state)
- [ ] Live API health indicator (sidebar)
- [ ] Domain sidebar with collapsible categories
- [ ] Endpoint search/filter
- [ ] Dynamic form generator (all field types: str, float, int, bool, select, list, date)
- [ ] Request executor (JWT-authenticated httpx POST/GET)
- [ ] Latency display after each request
- [ ] Raw JSON response (`st.json`)
- [ ] Auto-viz: numeric dict → bar chart / metric cards
- [ ] Auto-viz: float array → line chart
- [ ] Auto-viz: dict of floats → pie chart (for weights)
- [ ] Auto-viz: list of dicts → `st.dataframe`
- [ ] Auto-viz: 2D array → heatmap (for correlation)
- [ ] Python SDK code snippet generator
- [ ] curl command generator
- [ ] Copy-to-clipboard button
- [ ] Request history (last 20 in session)
- [ ] CSV/JSON export button
- [ ] Favorites / bookmark persistence

### **9.2 PYTHON SDK**

- [ ] `quantlib_api/_http.py` — httpx session + retry
- [ ] `quantlib_api/auth.py` — JWT token lifecycle
- [ ] `quantlib_api/exceptions.py` — exception hierarchy
- [ ] `quantlib_api/models.py` — Pydantic models
- [ ] `quantlib_api/client.py` — `QuantLibClient` main class
- [ ] 17 resource files in `quantlib_api/resources/`
- [ ] Async support (`aoptimize`, `avar`, etc.)
- [ ] `py.typed` marker (PEP 561)
- [ ] `pyproject.toml` install config
- [ ] 5 Jupyter example notebooks
- [ ] Unit tests (90%+ coverage on `_http.py`, `auth.py`)

### **9.3 CLI TOOL**

- [ ] `quantlib_cli/cli.py` — Click root + all sub-commands
- [ ] `quantlib login` / `quantlib logout`
- [ ] `quantlib health` + `--watch`
- [ ] `quantlib endpoints list` / `describe`
- [ ] 17 domain command groups (all methods)
- [ ] `--json` and `--table` output flags
- [ ] `--file` JSON body flag
- [ ] `auth_store.py` — keyring-based credential storage
- [ ] `formatters.py` — rich table rendering
- [ ] Shell completions (bash, zsh, fish)
- [ ] Exit code conventions (0/1/2/3)
- [ ] `pip install` entrypoint in `pyproject.toml`

### **9.4 POSTMAN COLLECTION**

- [ ] 60+ requests covering all endpoints
- [ ] 17 domain folders
- [ ] Pre-request script: inject `{{token}}`
- [ ] Login request: saves token to collection variable
- [ ] Test scripts: status 200, field validation
- [ ] 3 environment files (local, staging, production)
- [ ] Newman CI/CD run instructions documented

---

## **PHASE 10: API DOMAIN COVERAGE MATRIX**

### **Complete Endpoint × Tool Coverage**

| Domain | Base Path | Endpoints | Explorer | SDK | CLI | Postman |
|--------|-----------|-----------|----------|-----|-----|---------|
| Portfolio | `/api/v1/portfolio` | 5 | ✅ | ✅ | ✅ | ✅ |
| Options | `/api/v1/options` | 4 | ✅ | ✅ | ✅ | ✅ |
| Risk | `/api/v1/risk` | 5 | ✅ | ✅ | ✅ | ✅ |
| Market Regime | `/api/v1/regime` | 4 | ✅ | ✅ | ✅ | ✅ |
| Volatility | `/api/v1/volatility` | 4 | ✅ | ✅ | ✅ | ✅ |
| Macro | `/api/v1/macro` | 3 | ✅ | ✅ | ✅ | ✅ |
| Backtesting | `/api/v1/backtesting` | 4 | ✅ | ✅ | ✅ | ✅ |
| Analytics | `/api/v1/analytics` | 4 | ✅ | ✅ | ✅ | ✅ |
| Data | `/api/v1/data` | 4 | ✅ | ✅ | ✅ | ✅ |
| Market Analysis | `/api/v1/market-analysis` | 5 | ✅ | ✅ | ✅ | ✅ |
| Trading Signals | `/api/v1/signals` | 4 | ✅ | ✅ | ✅ | ✅ |
| Liquidity | `/api/v1/liquidity` | 5 | ✅ | ✅ | ✅ | ✅ |
| Systemic Risk | `/api/v1/systemic-risk` | 5 | ✅ | ✅ | ✅ | ✅ |
| Execution | `/api/v1/execution` | 5 | ✅ | ✅ | ✅ | ✅ |
| Compliance | `/api/v1/compliance` | 6 | ✅ | ✅ | ✅ | ✅ |
| UAT / Stress | `/api/v1/uat` | 6 | ✅ | ✅ | ✅ | ✅ |
| Health | `/health` | 2 | ✅ | ✅ | ✅ | ✅ |
| **TOTAL** | | **75** | **75** | **75** | **75** | **75** |

---

## **PHASE 11: RISK REGISTER**

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| API URL change breaks Explorer | Medium | High | `BASE_URL` config in one place (`config/api_config.py`) |
| JWT token format changes | Low | High | SDK token parser abstracted in `auth.py` |
| Streamlit version breaks UI | Low | Medium | Pin `streamlit>=1.30` in requirements |
| httpx not installed | Low | High | Listed in `requirements.txt` + `pyproject.toml` |
| Rate limit hits during Explorer testing | Medium | Low | SDK auto-handles 429 with `retry_after` |
| New endpoint not added to Explorer | High | Medium | Quarterly audit of `ENDPOINT_CATALOG` vs FastAPI routes |
| Credentials stored incorrectly (CLI) | Low | Critical | Use `keyring` library; never store plaintext |
| SDK breaking change with API v2 | Low | High | Versioned resource classes (`ResourceV1`, `ResourceV2`) |

---

## **SUMMARY**

| Component | Files | Lines of Code (Est.) | Priority | Status |
|-----------|-------|---------------------|----------|--------|
| Streamlit API Explorer | 1 (`pages/17_API_Explorer.py`) | ~900 | P0 | 🔲 To Build |
| Python SDK | 20 files in `quantlib_api/` | ~2,500 | P1 | 🔲 To Build |
| CLI Tool | 5 files in `quantlib_cli/` | ~800 | P1 | 🔲 To Build |
| Postman Collection | 4 JSON files in `postman/` | ~3,000 (JSON) | P2 | 🔲 To Build |
| **Total** | **30 files** | **~7,200** | | |

**Parent Project:** QuantLib Pro Unified Quantitative Finance Suite  
**Parent SDLC:** [QUANTITATIVE_FINANCE_MEGA_PROJECT_SDLC.md](QUANTITATIVE_FINANCE_MEGA_PROJECT_SDLC.md)  
**API Reference:** `http://localhost:8000/docs` (Swagger UI)  
**Base SDLC Version:** 4.0 → **This document extends to v5.0**
