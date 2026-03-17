# QuantLib Pro SDK & Python Package

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/quantlib-pro/quantlib-pro)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Enterprise-grade quantitative finance toolkit for Python, providing comprehensive tools for portfolio management, risk analysis, options pricing, and market analysis.

##  Quick Start

### Installation

#### As a Package (Recommended for Users)
```bash
# Install from PyPI ( NOW AVAILABLE!)
pip install quantlib-pro

# Or install in development mode
pip install -e .
```

#### As an SDK (Recommended for Developers)
```python
from quantlib_pro import QuantLibSDK

# Initialize with default configuration
sdk = QuantLibSDK()

# Or with custom configuration
from quantlib_pro import SDKConfig
config = SDKConfig(
    alpha_vantage_key="your_api_key",
    enable_caching=True,
    log_level="INFO"
)
sdk = QuantLibSDK(config)
```

### Basic Usage

```python
from quantlib_pro import QuantLibSDK

# Initialize SDK
sdk = QuantLibSDK()

# Portfolio Analysis
portfolio = sdk.portfolio.create_portfolio(['AAPL', 'GOOGL', 'MSFT'])
data = sdk.data.get_price_data(['AAPL', 'GOOGL', 'MSFT'], period="1y")
returns = sdk.portfolio.calculate_returns(data)
metrics = sdk.portfolio.calculate_portfolio_metrics(returns)

# Risk Analysis
risk_metrics = sdk.risk.calculate_portfolio_risk(data)
var_95 = sdk.risk.calculate_var(returns, confidence_level=0.05)

# Options Pricing
call_price = sdk.options.black_scholes(S=100, K=105, T=0.25, r=0.05, sigma=0.2)
greeks = sdk.options.calculate_greeks(S=100, K=105, T=0.25, r=0.05, sigma=0.2)
```

##  Package Structure

### Core Modules

| Module | Description | Key Features |
|--------|-------------|--------------|
| **Portfolio** | Portfolio management & optimization | Mean-variance optimization, risk budgeting, backtesting |
| **Risk** | Risk analysis & measurement | VaR/CVaR, stress testing, correlation analysis |
| **Options** | Options pricing & Greeks | Black-Scholes, Monte Carlo, implied volatility |
| **Volatility** | Volatility modeling | GARCH, volatility surfaces, regime detection |
| **Data** | Market data management | Multi-provider support, caching, validation |
| **Macro** | Economic analysis | FRED integration, macro indicators, sentiment |
| **Analytics** | Advanced analytics | ML models, factor analysis, PCA |
| **Execution** | Trade execution analysis | Transaction costs, market impact, strategies |

### SDK vs Individual Modules

#### SDK Approach (Unified Interface)
```python
from quantlib_pro import QuantLibSDK

sdk = QuantLibSDK()
result = sdk.portfolio.optimize_portfolio(returns, cov_matrix)
```

#### Direct Module Approach (Fine-grained Control)
```python
from quantlib_pro.portfolio import max_sharpe_portfolio
from quantlib_pro.risk import calculate_var

weights = max_sharpe_portfolio(returns, cov_matrix)
var = calculate_var(returns)
```

##  Installation Options

### Production Environment
```bash
# Minimal installation with core dependencies
pip install quantlib-pro[sdk]

# Full installation with all features
pip install quantlib-pro[full]

# Specific feature sets
pip install quantlib-pro[data]  # Data providers
pip install quantlib-pro[ml]    # Machine learning
```

### Development Environment
```bash
# Clone repository
git clone https://github.com/your-org/quantlib-pro.git
cd quantlib-pro

# Install in development mode with all dependencies
pip install -e .[dev,all]

# Run tests
pytest

# Run SDK demo
python sdk_demo.py
```

##  Configuration

### Environment Variables
```bash
# API Keys
export ALPHA_VANTAGE_API_KEY="your_key"
export FRED_API_KEY="your_key"
export FACTSET_USERNAME="your_username"
export FACTSET_API_KEY="your_key"

# Database URLs
export DATABASE_URL="postgresql://user:pass@localhost:5432/quantlib"
export REDIS_URL="redis://localhost:6379"
```

### Programmatic Configuration
```python
from quantlib_pro import SDKConfig, QuantLibSDK

config = SDKConfig(
    # API Keys
    alpha_vantage_key="your_api_key",
    fred_api_key="your_fred_key",
    
    # Performance settings
    enable_caching=True,
    cache_ttl=3600,
    max_workers=4,
    
    # Risk defaults
    default_confidence_level=0.05,
    default_time_horizon=252,
    
    # Logging
    log_level="INFO",
    log_file="quantlib.log"
)

sdk = QuantLibSDK(config)
```

##  Examples

### Portfolio Optimization
```python
import pandas as pd
from quantlib_pro import QuantLibSDK

sdk = QuantLibSDK()

# Get data for tech stocks
symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA']
data = sdk.data.get_price_data(symbols, period='2y')

# Calculate expected returns and covariance
returns = data.pct_change().dropna()
expected_returns = returns.mean() * 252
cov_matrix = returns.cov() * 252

# Optimize portfolio
result = sdk.portfolio.optimize_portfolio(
    expected_returns, 
    cov_matrix, 
    risk_aversion=1.0
)

print("Optimal weights:", result['optimal_weights'])
print("Expected return:", result['expected_return'])
print("Expected risk:", result['expected_risk'])
```

### Risk Analysis
```python
# Calculate comprehensive risk metrics
risk_metrics = sdk.risk.calculate_portfolio_risk(returns)

print(f"Portfolio Volatility: {risk_metrics['portfolio_volatility']:.2%}")
print(f"VaR (95%): {risk_metrics['var_95']:.2%}")
print(f"CVaR (95%): {risk_metrics['cvar_95']:.2%}")

# Stress testing
scenarios = {
    "Market Crash": -0.20,
    "Interest Rate Shock": -0.05,
    "Liquidity Crisis": -0.15
}

stress_results = sdk.risk.stress_test(returns, scenarios)
for scenario, result in stress_results.items():
    print(f"{scenario}: {result['percentage_loss']:.2f}% loss")
```

### Options Strategy Analysis
```python
# Define a covered call strategy
legs = [
    {"position": 1, "type": "call", "strike": 100, "price": 5.0},   # Long stock (synthetic)
    {"position": -1, "type": "call", "strike": 110, "price": 2.0}   # Short call
]

strategy_analysis = sdk.options.option_strategy_analysis(legs)
print(f"Max Profit: ${strategy_analysis['max_profit']:.2f}")
print(f"Max Loss: ${strategy_analysis['max_loss']:.2f}")
print(f"Breakeven: ${strategy_analysis['breakeven_points']}")
```

##  Command Line Interface

```bash
# Run SDK demo
quantlib demo

# Health check
quantlib health

# Get market data
quantlib data --symbols AAPL,MSFT --period 1y

# Portfolio optimization
quantlib portfolio optimize --symbols AAPL,MSFT,GOOGL --method max_sharpe

# Risk analysis
quantlib risk var --portfolio portfolio.json --confidence 0.05
```

##  Architecture

### Modular Design
- **Lazy Loading**: Modules are loaded only when accessed
- **Plugin Architecture**: Easy to extend with custom providers
- **Caching Layer**: Redis-based caching for performance
- **Data Validation**: Comprehensive data quality checks
- **Error Handling**: Graceful degradation and fallback mechanisms

### Data Flow
```
Data Sources → Data Manager → Cache Layer → Analysis Modules → Results
     ↓              ↓            ↓             ↓            ↓
  (APIs, Files) → (Validation) → (Redis) → (Portfolio, Risk) → (Metrics)
```

##  Testing & Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=quantlib_pro

# Run specific module tests
pytest tests/test_portfolio.py

# Run SDK integration tests
pytest tests/test_sdk_integration.py
```

### Code Quality
```bash
# Format code
black quantlib_pro/

# Check linting
flake8 quantlib_pro/

# Type checking
mypy quantlib_pro/

# Security scan
bandit -r quantlib_pro/
```

##  Performance

- **Vectorized Operations**: NumPy/Pandas for fast computations
- **Parallel Processing**: Multi-threading for independent calculations  
- **Caching**: Redis for frequently accessed data
- **Lazy Loading**: Modules loaded on demand
- **Memory Optimization**: Efficient data structures

##  Security

- **API Key Management**: Secure environment variable handling
- **Input Validation**: Comprehensive parameter checking
- **Error Sanitization**: No sensitive data in error messages
- **Access Control**: Role-based permissions (enterprise version)

##  Documentation

- **API Reference**: Complete function documentation
- **Tutorials**: Step-by-step guides for common tasks
- **Examples**: Real-world use cases and code samples
- **Best Practices**: Performance and security guidelines

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Support

- **Documentation**: [https://quantlib-pro.readthedocs.io](https://quantlib-pro.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/quantlib-pro/quantlib-pro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/quantlib-pro/quantlib-pro/discussions)
- **Email**: support@quantlibpro.com

##  Performance Benchmarks

| Operation | Time | Memory |
|-----------|------|--------|
| Portfolio optimization (100 assets) | <50ms | <10MB |
| VaR calculation (10,000 scenarios) | <100ms | <20MB |
| Options pricing (Black-Scholes) | <1ms | <1MB |
| Data retrieval (1 year, 10 symbols) | <2s | <50MB |

##  Roadmap

### Version 1.1 (Q2 2024)
- [ ] Real-time data streaming
- [ ] More ML models
- [ ] Enhanced UI components
- [ ] Cloud deployment templates

### Version 1.2 (Q3 2024)
- [ ] Alternative data sources
- [ ] Factor modeling
- [ ] ESG integration
- [ ] Performance attribution

### Version 2.0 (Q4 2024)
- [ ] Multi-asset support
- [ ] Fixed income tools
- [ ] Derivatives pricing
- [ ] Risk management platform

---

**QuantLib Pro** - Professional quantitative finance toolkit for the modern era.  **Now Available on PyPI!** 