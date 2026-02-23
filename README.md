# QuantLib Pro — Enterprise Quantitative Finance Platform

> Production-grade quantitative finance platform consolidating 30+ specialized applications into a unified, scalable suite with comprehensive risk analytics, portfolio optimization, derivatives pricing, and advanced testing infrastructure.

[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**📊 70% Complete** | **16 of 22 Weeks** | **15,000+ Lines of Production Code**

---

## 🚀 Features

### Portfolio Management
- **Modern Portfolio Theory** optimization (max Sharpe, min volatility, efficient frontier)
- **Dynamic rebalancing** with transaction cost optimization
- **Multi-asset allocation** with sector/exposure constraints
- **Performance attribution** and risk decomposition

### Risk Analytics
- **Value at Risk (VaR)** - Parametric, Historical, Monte Carlo
- **Conditional VaR (CVaR)** - Expected Shortfall analysis
- **Stress testing** - Historical scenarios, hypothetical shocks, Monte Carlo
- **Tail risk analysis** - Extreme Value Theory (EVT), GPD fitting
- **Correlation regime detection** - Dynamic correlation breakdowns

### Options & Derivatives
- **Black-Scholes-Merton** pricing with full Greeks (Delta, Gamma, Vega, Theta, Rho)
- **Monte Carlo engine** for path-dependent options (Asian, Barrier, Lookback)
- **Volatility surface** construction and analysis
- **Implied volatility** calibration
- **Put-call parity** validation

### Market Regime Detection
- **Hidden Markov Models (HMM)** for regime classification
- **Regime-aware optimization** - Dynamic strategy switching
- **Transition probability analysis**
- **Regime persistence metrics**

### Backtesting
- **Event-driven backtesting** engine
- **Transaction cost modeling** - Slippage, commissions, market impact
- **Performance metrics** - Sharpe, Sortino, Calmar, max drawdown
- **Walk-forward analysis** - Out-of-sample validation

### Governance & Compliance
- **Audit trail** - Immutable calculation history
- **Position limits** enforcement
- **Risk policy** validation
- **Data lineage** tracking

### Observability & Performance
- **Real-time performance monitoring** with baselines and alerts
- **Function profiling** with @profile decorator
- **Statistical performance analysis** - Mean, P95, P99 latencies
- **Regression detection** - Automated performance drift alerts

### Testing Infrastructure
- **Load testing** - ThreadPoolExecutor with 4 load patterns (ramp-up, constant, spike, wave)
- **Chaos engineering** - 10 fault injection types, resilience validation
- **Model validation** - 21 tests against analytical benchmarks (Hull's Options book)
- **Integration testing** - End-to-end workflow validation
- **Test reporting** - Historical tracking, trend analysis, coverage metrics

---

## 📦 Quick Start

### Prerequisites
- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- 8GB+ RAM recommended
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/gdukens/quant-simulator.git
cd quant-simulator

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run Home.py
```

Application will start at `http://localhost:8501`

### Docker Deployment

```bash
# Build and run with Docker
docker build -t quantlib-pro:latest .
docker run -p 8501:8501 quantlib-pro:latest

# Or use Docker Compose
docker-compose up -d
```

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
- **yfinance** - Market data provider
- **Streamlit** - Web UI framework
- **NumPy/SciPy** - Scientific computing
- **Plotly** - Interactive visualizations

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/gdukens/quant-simulator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gdukens/quant-simulator/discussions)
- **Email**: support@quantlib-pro.com

---

## 🔗 Links

- **Repository**: https://github.com/gdukens/quant-simulator
- **Documentation**: [docs/](docs/)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

**Built with ❤️ for quantitative finance professionals**
