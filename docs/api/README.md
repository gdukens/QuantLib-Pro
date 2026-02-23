# QuantLib Pro API Reference

Complete API documentation for QuantLib Pro - a comprehensive quantitative finance library.

## Table of Contents

- [Core Modules](#core-modules)
- [Portfolio Management](#portfolio-management)
- [Risk Analytics](#risk-analytics)
- [Options Pricing](#options-pricing)
- [Data Management](#data-management)
- [Backtesting](#backtesting)
- [Utilities](#utilities)

---

## Core Modules

### Portfolio Optimization

**Module:** `quantlib_pro.portfolio`

#### `PortfolioOptimizer`

Optimize portfolio weights using modern portfolio theory.

```python
from quantlib_pro.portfolio import PortfolioOptimizer

optimizer = PortfolioOptimizer(
    expected_returns=returns,
    cov_matrix=cov_matrix,
    risk_free_rate=0.02
)

# Maximum Sharpe ratio portfolio
weights = optimizer.max_sharpe_ratio()

# Minimum volatility portfolio
weights = optimizer.min_volatility()

# Efficient frontier
frontier = optimizer.efficient_frontier(n_points=50)
```

**Methods:**

- `max_sharpe_ratio(constraints=None) -> np.ndarray`
  - Returns optimal weights maximizing Sharpe ratio
  - Constraints: dict with 'type', 'fun', 'bounds'

- `min_volatility(target_return=None) -> np.ndarray`
  - Returns minimum variance portfolio
  - Optional target return constraint

- `efficient_frontier(n_points=50) -> pd.DataFrame`
  - Returns DataFrame with returns, volatility, weights
  - n_points: number of portfolios on frontier

- `portfolio_performance(weights) -> Dict[str, float]`
  - Returns expected return, volatility, Sharpe ratio

**Example:**

```python
import pandas as pd
import numpy as np
from quantlib_pro.portfolio import PortfolioOptimizer

# Load data
returns = pd.read_csv('returns.csv', index_col=0, parse_dates=True)

# Calculate inputs
expected_returns = returns.mean() * 252
cov_matrix = returns.cov() * 252

# Optimize
optimizer = PortfolioOptimizer(expected_returns, cov_matrix)
optimal_weights = optimizer.max_sharpe_ratio()

# Analyze
performance = optimizer.portfolio_performance(optimal_weights)
print(f"Expected Return: {performance['return']:.2%}")
print(f"Volatility: {performance['volatility']:.2%}")
print(f"Sharpe Ratio: {performance['sharpe']:.2f}")
```

---

### Risk Metrics

**Module:** `quantlib_pro.risk`

#### `RiskCalculator`

Calculate Value at Risk (VaR) and Conditional VaR (CVaR).

```python
from quantlib_pro.risk import RiskCalculator

calculator = RiskCalculator()

# Parametric VaR (assumes normal distribution)
var = calculator.parametric_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

# Historical VaR
var = calculator.historical_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

# Monte Carlo VaR
var = calculator.monte_carlo_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000,
    n_simulations=10_000
)

# CVaR (Expected Shortfall)
cvar = calculator.cvar(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)
```

**Methods:**

- `parametric_var(returns, confidence_level=0.95, portfolio_value=1.0) -> float`
  - VaR assuming normal distribution
  - Fast but may underestimate tail risk

- `historical_var(returns, confidence_level=0.95, portfolio_value=1.0) -> float`
  - VaR from historical percentiles
  - Non-parametric, no distribution assumptions

- `monte_carlo_var(returns, confidence_level=0.95, portfolio_value=1.0, n_simulations=10000) -> float`
  - VaR from Monte Carlo simulation
  - Captures non-linear risk

- `cvar(returns, confidence_level=0.95, portfolio_value=1.0, method='historical') -> float`
  - Conditional VaR (Expected Shortfall)
  - Average loss beyond VaR threshold

**Example:**

```python
from quantlib_pro.risk import RiskCalculator
import pandas as pd

# Load portfolio returns
returns = pd.read_csv('portfolio_returns.csv')['returns']

calculator = RiskCalculator()

# Calculate 1-day 95% VaR for $1M portfolio
var_95 = calculator.historical_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

# Calculate CVaR (expected loss if VaR is exceeded)
cvar_95 = calculator.cvar(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

print(f"95% VaR: ${var_95:,.0f}")
print(f"95% CVaR: ${cvar_95:,.0f}")
```

---

### Options Pricing

**Module:** `quantlib_pro.derivatives`

#### `BlackScholesPricer`

Price European options using Black-Scholes-Merton model.

```python
from quantlib_pro.derivatives import BlackScholesPricer

pricer = BlackScholesPricer(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    dividend_yield=0.0
)

# Option prices
call_price = pricer.call_price()
put_price = pricer.put_price()

# Greeks
delta = pricer.delta('call')
gamma = pricer.gamma()
vega = pricer.vega()
theta = pricer.theta('call')
rho = pricer.rho('call')
```

**Methods:**

- `call_price() -> float`
  - European call option price

- `put_price() -> float`
  - European put option price

- `delta(option_type='call') -> float`
  - Rate of change of option price w.r.t. underlying

- `gamma() -> float`
  - Rate of change of delta w.r.t. underlying

- `vega() -> float`
  - Sensitivity to volatility (per 1% change)

- `theta(option_type='call') -> float`
  - Time decay (per day)

- `rho(option_type='call') -> float`
  - Sensitivity to interest rate (per 1% change)

**Example:**

```python
from quantlib_pro.derivatives import BlackScholesPricer

# Price a call option on stock trading at $100
pricer = BlackScholesPricer(
    spot=100.0,
    strike=105.0,  # 5% out of the money
    time_to_maturity=0.25,  # 3 months
    risk_free_rate=0.05,
    volatility=0.25
)

call = pricer.call_price()
delta = pricer.delta('call')

print(f"Call Price: ${call:.2f}")
print(f"Delta: {delta:.4f}")
```

#### `MonteCarloEngine`

Price derivatives using Monte Carlo simulation.

```python
from quantlib_pro.derivatives import MonteCarloEngine

engine = MonteCarloEngine(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    n_simulations=100_000
)

# European option
call_price = engine.price_european_call()

# Path-dependent options
asian_price = engine.price_asian_call()
barrier_price = engine.price_barrier_call(barrier=110.0)
```

---

### Data Management

**Module:** `quantlib_pro.data`

#### `MarketDataProvider`

Fetch market data from multiple sources.

```python
from quantlib_pro.data import MarketDataProvider

provider = MarketDataProvider(source='yfinance')

# Get historical data
data = provider.get_historical_data(
    tickers=['AAPL', 'MSFT', 'GOOGL'],
    start_date='2020-01-01',
    end_date='2024-01-01'
)

# Get real-time quote
quote = provider.get_quote('AAPL')
```

**Supported Sources:**
- `yfinance` - Yahoo Finance
- `alpha_vantage` - Alpha Vantage API
- `iex` - IEX Cloud
- `polygon` - Polygon.io

---

### Backtesting

**Module:** `quantlib_pro.backtesting`

#### `Backtester`

Test trading strategies on historical data.

```python
from quantlib_pro.backtesting import Backtester, Strategy

class MyStrategy(Strategy):
    def generate_signals(self, data):
        # Your strategy logic
        return signals

backtester = Backtester(
    strategy=MyStrategy(),
    data=historical_data,
    initial_capital=100_000
)

results = backtester.run()
print(results.summary())
```

---

## Performance & Monitoring

### Profiling

**Module:** `quantlib_pro.observability`

```python
from quantlib_pro.observability import profile

@profile
def my_expensive_function():
    # Function will be profiled
    pass
```

### Monitoring

```python
from quantlib_pro.observability import RealTimeMonitor

monitor = RealTimeMonitor()

with monitor.track('portfolio_optimization'):
    # Code to monitor
    optimizer.max_sharpe_ratio()

# Get metrics
metrics = monitor.get_metrics('portfolio_optimization')
```

---

## Testing

### Load Testing

**Module:** `quantlib_pro.testing`

```python
from quantlib_pro.testing import LoadTester, LoadPattern

def portfolio_optimization_scenario():
    optimizer.max_sharpe_ratio()

tester = LoadTester()
results = tester.run_load_test(
    scenarios=[{'function': portfolio_optimization_scenario}],
    users=50,
    duration=60,
    pattern=LoadPattern.RAMP_UP
)
```

### Model Validation

```python
from quantlib_pro.testing import ModelValidator

validator = ModelValidator(tolerance=0.01)
results = validator.validate_all_models()
print(results.generate_report())
```

---

## See Also

- [User Guide](../guides/user_guide.md)
- [Tutorials](../tutorials/)
- [Architecture](../architecture.md)
- [Examples](../../examples/)
