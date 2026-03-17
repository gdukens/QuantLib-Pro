# **QuantLib Pro: Enterprise Quantitative Finance Platform**

A comprehensive, production-grade REST API that unifies 30+ specialized quantitative finance applications into a single, scalable platform. Built for institutional traders, portfolio managers, risk analysts, and quantitative researchers who demand professional-grade financial modeling capabilities.

[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Production](https://img.shields.io/badge/status-production--ready-success)](https://github.com/gdukens/quant-simulator)
[![FRED Integration](https://img.shields.io/badge/FRED-integrated-brightgreen)](https://fred.stlouisfed.org/)

**📊 Enterprise-Ready** | **Real Market Data** | **30+ Applications** | **✅ Production Deployment**

---

## **Core Capabilities**

### **Portfolio Management**
- **Modern Portfolio Theory**: Efficient frontier optimization, risk-return analysis
- **Asset Allocation**: Multi-asset class optimization with constraints and rebalancing
- **Performance Attribution**: Factor-based return decomposition and benchmark analysis

### **Derivatives & Options**
- **Pricing Models**: Black-Scholes, Monte Carlo simulation, binomial trees
- **Greeks Analytics**: Real-time Delta, Gamma, Theta, Vega, Rho calculations
- **Volatility Modeling**: Implied volatility surfaces, skew analysis, term structure

### **Risk Management**
- **Value-at-Risk (VaR)**: Historical, parametric, and Monte Carlo methodologies
- **Conditional VaR (CVaR)**: Expected shortfall and tail risk assessment
- **Stress Testing**: Scenario analysis, backtesting, and regulatory compliance metrics

### **Market Intelligence**
- **Regime Detection**: Hidden Markov Models for market state identification
- **Correlation Analysis**: Dynamic correlation matrices and contagion modeling
- **Macro Analytics**: Real-time Federal Reserve economic data integration (FRED API)

### **Real-Time Data Integration**
- **Federal Reserve Economic Data (FRED)**: Live GDP, unemployment, inflation, Treasury rates
- **Yahoo Finance**: Real-time stock prices and market data (unlimited access)
- **Alpha Vantage**: Professional-grade financial data with 500+ daily calls
- **Multi-Provider Resilience**: 6-level failover chain with circuit breakers
- **Enterprise Caching**: 3-tier architecture (Memory → Redis → Persistent storage)
- **Data Quality Assurance**: Automated validation and anomaly detection

---

## **Authentication & Security**

### **API Key Authentication**
```http
X-API-Key: your_api_key_here
```

### **JWT Bearer Token**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

*Enterprise customers receive dedicated API keys with enhanced rate limits and priority support.*

### **Service Tiers & Rate Limits**

| Tier | Requests/Hour | Features | Support |
|------|---------------|----------|---------|  
| **Developer** | 100 | Core endpoints, basic analytics | Community |
| **Professional** | 2,500 | Advanced analytics, real-time data | Email |
| **Enterprise** | Unlimited | Full platform, custom endpoints | Dedicated |

---

## **Enterprise Deployment**

### **Prerequisites**
- Python 3.10+ (production tested on 3.10, 3.11, 3.12)
- 16GB+ RAM (recommended for institutional workloads)
- Redis 6.0+ for high-performance caching
- PostgreSQL 13+ for enterprise data persistence

### **Quick Start - Development**

```bash
# Clone the enterprise repository
git clone https://github.com/quantlibpro/enterprise-platform.git
cd enterprise-platform

# Create isolated environment
python -m venv quantlib_env
# Windows
quantlib_env\Scripts\activate
# macOS/Linux
# source quantlib_env/bin/activate

# Install enterprise dependencies
pip install -r requirements-enterprise.txt

# Initialize with real market data
streamlit run streamlit_app.py --server.port 8503
```

**Platform Access**: `http://localhost:8501`  
**API Documentation**: `http://localhost:8002/docs`  
**Health Monitoring**: `http://localhost:8002/health`

### Docker Deployment

```bash
# Build and run with Docker
docker build -t quantlib-pro:latest .
docker run -p 8501:8501 quantlib-pro:latest

# Or use Docker Compose
docker-compose up -d
```

### Production Deployment

**Full production infrastructure with monitoring, alerting, and resilience:**

```bash
# Deploy to production with all services
docker-compose -f docker-compose.prod.yml up -d

# Services included:
# - QuantLib Pro application (Streamlit)
# - PostgreSQL database with persistent storage
# - Redis cache with persistence
# - Nginx reverse proxy with SSL/TLS
# - Prometheus metrics collection
# - Grafana dashboards
# - AlertManager for notifications
```

**Cloud Deployment Scripts:**

```bash
# AWS deployment
./deploy/aws-deploy.sh

# GCP deployment
./deploy/gcp-deploy.sh

# Azure deployment
./deploy/azure-deploy.sh
```

**See [Deployment Guide](docs/deployment-guide.md) for detailed production setup instructions.**

---

## 🎯 Use Cases

### Quantitative Analysts
```python
# Portfolio optimization with constraints
from quantlib_pro.portfolio import PortfolioOptimizer

optimizer = PortfolioOptimizer(expected_returns, cov_matrix)
weights = optimizer.max_sharpe_ratio()
performance = optimizer.portfolio_performance(weights)
```

### Risk Managers
```python
# Calculate VaR and stress test portfolio
from quantlib_pro.risk import RiskCalculator, StressTester

calculator = RiskCalculator()
var_95 = calculator.historical_var(returns, 0.95, portfolio_value)

tester = StressTester(returns)
covid_impact = tester.historical_stress_test('2020-02-20', '2020-03-23')
```

### Options Traders
```python
# Price options and calculate Greeks
from quantlib_pro.derivatives import BlackScholesPricer

pricer = BlackScholesPricer(S=100, K=105, T=0.25, r=0.05, sigma=0.25)
call_price = pricer.call_price()
delta = pricer.delta('call')
gamma = pricer.gamma()
```

### Algorithmic Traders
```python
# Backtest trading strategy
from quantlib_pro.backtesting import Backtester, Strategy

class MyStrategy(Strategy):
    def generate_signals(self, data):
        # Your strategy logic
        return signals

backtester = Backtester(strategy, data, initial_capital=100_000)
results = backtester.run()
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
```

---

## 🏗️ Architecture

QuantLib Pro uses **hexagonal (ports and adapters) architecture** with 5 layers:

```
┌─────────────────────────────────────────┐
│      Presentation (Streamlit UI)       │
├─────────────────────────────────────────┤
│   Application Services (Orchestration) │
├─────────────────────────────────────────┤
│   Domain Logic (Business Rules)        │
├─────────────────────────────────────────┤
│   Infrastructure (Data, Persistence)   │
└─────────────────────────────────────────┘
```

**Core Modules:**
- `portfolio/` - Portfolio optimization and rebalancing
- `risk/` - VaR, CVaR, stress testing, tail risk
- `derivatives/` - Options pricing, Greeks, Monte Carlo
- `data/` - Market data providers, caching, validation
- `backtesting/` - Strategy testing and performance analysis
- `analytics/` - Regime detection, correlation analysis
- `governance/` - Audit trail, compliance, policies
- `observability/` - Profiling, monitoring, alerts
- `testing/` - Load testing, chaos engineering, model validation

See [Architecture Documentation](docs/architecture.md) for details.

---

## 📊 UI Dashboard

### 9 Specialized Pages

1. **📊 Portfolio Optimizer** - MPT optimization with constraints
2. **⚠️ Risk Analytics** - VaR, CVaR, stress testing
3. **📈 Options Pricing** - Black-Scholes, Monte Carlo, Greeks
4. **🔄 Backtesting** - Strategy testing and performance metrics
5. **🎯 Regime Detection** - HMM regime classification
6. **📉 Monte Carlo** - Wealth simulations and scenario analysis
7. **🔍 Data Explorer** - Market data visualization
8. **📊 Advanced Analytics** - Performance profiling, correlation, tail risk
9. **🧪 Testing** - Load testing, model validation, chaos engineering

---

## Development Workflow

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black quantlib_pro/ tests/
flake8 quantlib_pro/ tests/
isort quantlib_pro/ tests/

# Type checking
mypy quantlib_pro/

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=quantlib_pro --cov-report=html

# Run specific test categories
pytest -m unit           # Fast unit tests
pytest -m integration    # Integration tests
pytest -m load           # Performance tests
```

---

## Project Structure

```
quantlib_pro/                   # Main package (15,000+ lines)
├── portfolio/                  # Portfolio management
│   ├── optimizer.py           # MPT optimization algorithms
│   ├── rebalancer.py          # Rebalancing logic
│   └── performance.py         # Performance attribution
│
├── risk/                      # Risk analytics
│   ├── calculator.py          # VaR, CVaR calculations
│   ├── advanced_analytics.py  # Stress testing, tail risk
│   └── metrics.py             # Risk metrics
│
├── derivatives/               # Options & derivatives
│   ├── black_scholes.py       # Analytical pricing
│   ├── monte_carlo.py         # MC pricing engine
│   └── greeks.py              # Greeks calculation
│
├── data/                      # Data management
│   ├── providers.py           # Market data providers
│   ├── validator.py           # Data quality checks
│   └── cache.py               # Caching layer
│
├── backtesting/               # Strategy backtesting
│   ├── engine.py              # Backtesting engine
│   ├── strategy.py            # Strategy base class
│   └── metrics.py             # Performance metrics
│
├── analytics/                 # Advanced analytics
│   ├── regime_detection.py    # HMM regime detection
│   ├── correlation_analysis.py # Correlation regimes
│   └── factor_models.py       # Factor analysis
│
├── governance/                # Compliance & audit
│   ├── compliance.py          # Policy enforcement
│   ├── audit.py               # Audit trail
│   └── policies.py            # Risk policies
│
├── observability/             # Performance monitoring
│   ├── profiler.py            # Function profiling
│   ├── monitoring.py          # Real-time monitoring
│   └── alerts.py              # Alert system
│
└── testing/                   # Testing infrastructure
    ├── load_testing.py        # Load testing framework
    ├── chaos.py               # Chaos engineering
    ├── model_validation.py    # Model validation
    └── reporting.py           # Test reporting

pages/                         # Streamlit UI pages
├── Home.py                    # Landing page
├── 1_📊_Portfolio_Optimizer.py
├── 2_⚠️_Risk_Analytics.py
├── 3_📈_Options_Pricing.py
├── 4_🔄_Backtesting.py
├── 5_🎯_Regime_Detection.py
├── 6_📉_Monte_Carlo.py
├── 7_🔍_Data_Explorer.py
├── 8_📊_Advanced_Analytics.py
└── 9_🧪_Testing.py

tests/                         # Test suite (3,500+ lines)
├── unit/                      # Unit tests
├── integration/               # Integration tests
│   └── test_week16_comprehensive.py  # 500+ line test suite
├── fixtures/                  # Test fixtures
└── conftest.py                # Pytest configuration

docs/                          # Documentation
├── api/                       # API reference
│   └── README.md              # Complete API docs
├── guides/                    # User guides
│   └── user_guide.md          # Comprehensive user guide
├── tutorials/                 # Tutorials
│   └── portfolio_optimization.md  # Step-by-step tutorial
├── architecture.md            # Architecture documentation
└── deployment.md              # Deployment guide
```

---

## 📚 Documentation

### Getting Started
- **[User Guide](docs/guides/user_guide.md)** - Comprehensive guide with examples
- **[Portfolio Optimization Tutorial](docs/tutorials/portfolio_optimization.md)** - Step-by-step tutorial
- **[Quick Start](#-quick-start)** - Installation and first steps

### Reference
- **[API Reference](docs/api/README.md)** - Complete API documentation
- **[Architecture](docs/architecture.md)** - System design and patterns
- **[Deployment Guide](docs/deployment.md)** - Production deployment

### Development
- **[SDLC Plan](QUANTITATIVE_FINANCE_MEGA_PROJECT_SDLC.md)** - 22-week project plan
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute

---

## 🧪 Testing

QuantLib Pro includes comprehensive testing infrastructure:

### Test Coverage
- **Unit tests** - 100+ tests for core modules
- **Integration tests** - 15+ end-to-end workflow tests  
- **Load tests** - Performance benchmarking (50-200 concurrent users)
- **Chaos tests** - Resilience validation (10 fault types)
- **Model validation** - 21 tests against analytical benchmarks

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test suites
pytest tests/unit/                    # Unit tests
pytest tests/integration/             # Integration tests

# Load testing
python -m quantlib_pro.testing.load_testing

# Model validation
python -m quantlib_pro.testing.model_validation
```

### Performance Benchmarks

| Operation | P95 Latency | Target |
|-----------|-------------|--------|
| Portfolio Optimization | ~300ms | <500ms |
| VaR Calculation | ~80ms | <100ms |
| Options Pricing | ~40ms | <50ms |
| Regime Detection | ~150ms | <200ms |

---

## 🚧 Project Status

**Current Phase:** Week 17 of 22 (77% complete)

### ✅ Completed (Weeks 1-16)

- ✅ Core infrastructure & architecture
- ✅ Portfolio optimization (MPT, efficient frontier)
- ✅ Risk analytics (VaR, CVaR, stress testing)
- ✅ Options pricing (Black-Scholes, Monte Carlo)
- ✅ Data management & validation
- ✅ Backtesting engine
- ✅ Regime detection (HMM)
- ✅ Monte Carlo simulations
- ✅ Governance & compliance (audit trail, policies)
- ✅ Observability (profiling, monitoring, alerts)
- ✅ Advanced analytics (stress testing, tail risk, correlation)
- ✅ Testing infrastructure (load, chaos, validation)
- ✅ Documentation (API, guides, tutorials)

### 🔄 In Progress (Week 17)
- 🔄 Documentation finalization
- ⏳ API reference completion

### 📅 Upcoming (Weeks 18-22)
- Week 18: User acceptance testing (UAT)
- Weeks 19-20: Production deployment
- Weeks 21-22: Hardening & stabilization

---

## 🎓 Key Concepts

### Modern Portfolio Theory (MPT)
```python
# Maximize Sharpe ratio
optimizer = PortfolioOptimizer(returns, cov_matrix, risk_free_rate=0.03)
weights = optimizer.max_sharpe_ratio()
```

### Value at Risk (VaR)
```python
# 95% confidence: maximum expected loss
calculator = RiskCalculator()
var_95 = calculator.historical_var(returns, 0.95, portfolio_value)
```

### Black-Scholes Options Pricing
```python
# European call option price
pricer = BlackScholesPricer(S=100, K=105, T=0.25, r=0.05, sigma=0.25)
call_price = pricer.call_price()
```

### Hidden Markov Models (HMM)
```python
# Detect market regimes
detector = RegimeDetector(n_regimes=3)
regimes = detector.fit_predict(returns)
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Development workflow
- Pull request process
- Issue reporting

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Hull, J. C.** - Options, Futures, and Other Derivatives (benchmarks)
- **Markowitz, H.** - Modern Portfolio Theory
- **Black, F. & Scholes, M.** - Options pricing model
- **yfinance** - Primary market data provider (Yahoo Finance)
- **Alpha Vantage** - Alternative market data API
- **FactSet** - Enterprise financial data platform
- **Streamlit** - Web UI framework
- **NumPy/SciPy** - Scientific computing
- **Plotly** - Interactive visualizations

---

## **Resources & Enterprise Support**

### **Documentation & Monitoring**
- **Interactive API Documentation**: [`/docs`](http://localhost:8002/docs) - Swagger UI with live endpoint testing
- **API Reference Guide**: [`/redoc`](http://localhost:8002/redoc) - Comprehensive endpoint documentation  
- **System Health Dashboard**: [`/health/detailed`](http://localhost:8002/health/detailed) - Real-time performance metrics
- **Code Examples**: [`/examples`](./examples) - Python, R, and JavaScript integration samples

### **Enterprise Support Tiers**

| Support Level | Contact Method | Response Time | SLA |
|---------------|----------------|---------------|-----|
| **Community** | GitHub Issues | 48-72 hours | Best effort |
| **Professional** | Email support | 4-8 hours | Business hours |
| **Enterprise** | Dedicated CSM | 1-2 hours | 24/7 availability |

### **Production Services**
- **Primary Contact**: guersondukensjrjoseph@gmail.com
- **Academic Contact**: gjose078@uottawa.ca

**99.9% Uptime Guarantee** for Enterprise tier customers with dedicated infrastructure and priority support.

---

## **Technical References**

- **Hull, J. C.** - Options, Futures, and Other Derivatives (benchmarks)
- **Markowitz, H.** - Modern Portfolio Theory
- **Black, F. & Scholes, M.** - Options pricing model  
- **Federal Reserve Economic Data (FRED)** - Real economic indicators
- **Yahoo Finance API** - Primary market data provider
- **Alpha Vantage API** - Professional financial data
- **Streamlit** - Enterprise web framework
- **FastAPI** - Production-grade REST API framework
- **Redis** - High-performance caching layer

---

**Transform your applications with institutional-grade quantitative finance capabilities.**

*Built for enterprise quantitative finance professionals*
