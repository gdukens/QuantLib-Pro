# QuantLib Pro User Guide

Complete guide to using QuantLib Pro for quantitative finance analysis.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Portfolio Management](#portfolio-management)
3. [Risk Analysis](#risk-analysis)
4. [Options & Derivatives](#options--derivatives)
5. [Backtesting Strategies](#backtesting-strategies)
6. [Performance Optimization](#performance-optimization)
7. [Best Practices](#best-practices)

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/gdukens/quant-simulator.git
cd quant-simulator

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run Home.py
```

### Quick Start

```python
import quantlib_pro as qlp
import pandas as pd

# Load market data
data = qlp.data.get_historical_data(['AAPL', 'MSFT', 'GOOGL'])

# Calculate returns
returns = data.pct_change().dropna()

# Optimize portfolio
optimizer = qlp.portfolio.PortfolioOptimizer(
    expected_returns=returns.mean() * 252,
    cov_matrix=returns.cov() * 252
)

optimal_weights = optimizer.max_sharpe_ratio()
print(optimal_weights)
```

---

## Portfolio Management

### Building a Portfolio

**Step 1: Data Collection**

```python
from quantlib_pro.data import MarketDataProvider

# Initialize data provider
provider = MarketDataProvider(source='yfinance')

# Define your universe
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

# Fetch historical data
data = provider.get_historical_data(
    tickers=tickers,
    start_date='2020-01-01',
    end_date='2024-01-01'
)

# Calculate returns
returns = data['Close'].pct_change().dropna()
```

**Step 2: Portfolio Optimization**

```python
from quantlib_pro.portfolio import PortfolioOptimizer

# Annualized inputs
expected_returns = returns.mean() * 252
cov_matrix = returns.cov() * 252

# Create optimizer
optimizer = PortfolioOptimizer(
    expected_returns=expected_returns,
    cov_matrix=cov_matrix,
    risk_free_rate=0.03  # 3% risk-free rate
)

# Find optimal portfolio
optimal_weights = optimizer.max_sharpe_ratio()

# Display results
portfolio_metrics = optimizer.portfolio_performance(optimal_weights)
print(f"Expected Annual Return: {portfolio_metrics['return']:.2%}")
print(f"Annual Volatility: {portfolio_metrics['volatility']:.2%}")
print(f"Sharpe Ratio: {portfolio_metrics['sharpe']:.2f}")
```

**Step 3: Constraints**

```python
# Long-only constraint (no short selling)
constraints = {
    'type': 'ineq',
    'fun': lambda w: w  # All weights >= 0
}

# Sector exposure limits
# Limit tech stocks to 40%
tech_stocks = ['AAPL', 'MSFT', 'GOOGL']
tech_indices = [tickers.index(t) for t in tech_stocks]

def tech_constraint(weights):
    tech_weight = sum(weights[i] for i in tech_indices)
    return 0.4 - tech_weight  # Tech weight <= 40%

constraints_list = [
    {'type': 'ineq', 'fun': lambda w: w},  # Long-only
    {'type': 'ineq', 'fun': tech_constraint}  # Sector limit
]

optimal_weights = optimizer.max_sharpe_ratio(constraints=constraints_list)
```

### Rebalancing

```python
from quantlib_pro.portfolio import PortfolioRebalancer

rebalancer = PortfolioRebalancer(
    target_weights=optimal_weights,
    current_weights=current_portfolio,
    transaction_cost=0.001  # 0.1% per trade
)

# Get rebalancing trades
trades = rebalancer.get_trades()

# Execute rebalancing
rebalanced_portfolio = rebalancer.rebalance()
```

---

## Risk Analysis

### Value at Risk (VaR)

VaR estimates the maximum potential loss over a given time horizon at a specified confidence level.

**Example: Calculate 1-day 95% VaR**

```python
from quantlib_pro.risk import RiskCalculator

calculator = RiskCalculator()

# Historical VaR (non-parametric)
var_95 = calculator.historical_var(
    returns=portfolio_returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

print(f"There is a 5% chance of losing more than ${-var_95:,.0f} tomorrow")
```

**Comparison of VaR Methods:**

```python
# 1. Parametric VaR (assumes normal distribution)
parametric_var = calculator.parametric_var(returns, 0.95, 1_000_000)

# 2. Historical VaR (uses actual historical distribution)
historical_var = calculator.historical_var(returns, 0.95, 1_000_000)

# 3. Monte Carlo VaR (simulates future scenarios)
mc_var = calculator.monte_carlo_var(returns, 0.95, 1_000_000, n_simulations=10_000)

print(f"Parametric VaR: ${-parametric_var:,.0f}")
print(f"Historical VaR: ${-historical_var:,.0f}")
print(f"Monte Carlo VaR: ${-mc_var:,.0f}")
```

### Conditional VaR (CVaR)

CVaR measures the expected loss given that VaR has been exceeded.

```python
# Calculate CVaR (Expected Shortfall)
cvar_95 = calculator.cvar(
    returns=portfolio_returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

print(f"Expected loss if VaR is exceeded: ${-cvar_95:,.0f}")
```

### Stress Testing

```python
from quantlib_pro.risk import StressTester

tester = StressTester(portfolio_returns)

# Historical stress test (2008 financial crisis)
crisis_scenario = tester.historical_stress_test(
    scenario_start='2008-09-01',
    scenario_end='2009-03-31'
)

# Hypothetical stress test
hypothetical = tester.hypothetical_stress_test(
    shocks={
        'AAPL': -0.30,  # 30% drop
        'MSFT': -0.25,  # 25% drop
    }
)

# Monte Carlo stress test
mc_stress = tester.monte_carlo_stress_test(
    n_scenarios=1000,
    worst_percentile=0.05  # Worst 5% of scenarios
)
```

---

## Options & Derivatives

### European Options

**Black-Scholes Pricing:**

```python
from quantlib_pro.derivatives import BlackScholesPricer

# Price a call option
pricer = BlackScholesPricer(
    spot=100.0,        # Current stock price
    strike=105.0,      # Strike price
    time_to_maturity=0.25,  # 3 months
    risk_free_rate=0.05,    # 5% annual rate
    volatility=0.25,        # 25% annual volatility
    dividend_yield=0.02     # 2% dividend yield
)

call_price = pricer.call_price()
put_price = pricer.put_price()

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# Verify put-call parity
parity_check = call_price - put_price
expected = pricer.spot * np.exp(-pricer.dividend_yield * pricer.time_to_maturity) - \
           pricer.strike * np.exp(-pricer.risk_free_rate * pricer.time_to_maturity)
print(f"Put-Call Parity: {np.isclose(parity_check, expected)}")
```

**Greeks:**

```python
# Calculate option Greeks
delta_call = pricer.delta('call')  # ~0.50 for ATM
gamma = pricer.gamma()              # Same for calls and puts
vega = pricer.vega()                # Volatility sensitivity
theta_call = pricer.theta('call')  # Time decay
rho_call = pricer.rho('call')      # Interest rate sensitivity

print(f"Delta: {delta_call:.4f}")
print(f"Gamma: {gamma:.4f}")
print(f"Vega: {vega:.4f}")
print(f"Theta: {theta_call:.4f}")
print(f"Rho: {rho_call:.4f}")
```

### Monte Carlo Pricing

For complex or path-dependent derivatives:

```python
from quantlib_pro.derivatives import MonteCarloEngine

engine = MonteCarloEngine(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    n_simulations=100_000,
    seed=42  # For reproducibility
)

# European options (benchmark against Black-Scholes)
european_call = engine.price_european_call()
print(f"European Call (MC): ${european_call:.2f}")

# Asian option (average price)
asian_call = engine.price_asian_call()
print(f"Asian Call: ${asian_call:.2f}")

# Barrier option
barrier_call = engine.price_barrier_call(barrier=110.0, barrier_type='up-and-out')
print(f"Barrier Call: ${barrier_call:.2f}")
```

---

## Backtesting Strategies

### Creating a Strategy

```python
from quantlib_pro.backtesting import Strategy, Backtester
import pandas as pd

class MovingAverageCrossover(Strategy):
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data):
        """Generate trading signals."""
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        
        # Calculate moving averages
        signals['short_ma'] = data['Close'].rolling(window=self.short_window).mean()
        signals['long_ma'] = data['Close'].rolling(window=self.long_window).mean()
        
        # Generate signals
        signals['signal'][self.short_window:] = np.where(
            signals['short_ma'][self.short_window:] > signals['long_ma'][self.short_window:],
            1.0,  # Long
            0.0   # Flat
        )
        
        # Generate trading orders (position changes)
        signals['positions'] = signals['signal'].diff()
        
        return signals

# Load data
data = provider.get_historical_data(['AAPL'], '2020-01-01', '2024-01-01')

# Create and run backtest
strategy = MovingAverageCrossover(short_window=50, long_window=200)
backtester = Backtester(
    strategy=strategy,
    data=data,
    initial_capital=100_000,
    commission=0.001  # 0.1% commission
)

results = backtester.run()

# Analyze results
print(results.summary())
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
print(f"Win Rate: {results.win_rate:.2%}")
```

### Performance Metrics

```python
# Detailed performance analysis
metrics = results.get_metrics()

print("Performance Metrics:")
print(f"  CAGR: {metrics['cagr']:.2%}")
print(f"  Volatility: {metrics['volatility']:.2%}")
print(f"  Sharpe Ratio: {metrics['sharpe']:.2f}")
print(f"  Sortino Ratio: {metrics['sortino']:.2f}")
print(f"  Calmar Ratio: {metrics['calmar']:.2f}")
print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")

# Trade analysis
print(f"\nTrade Statistics:")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Win Rate: {metrics['win_rate']:.2%}")
print(f"  Avg Win: {metrics['avg_win']:.2%}")
print(f"  Avg Loss: {metrics['avg_loss']:.2%}")
print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
```

---

## Performance Optimization

### Profiling

```python
from quantlib_pro.observability import profile, PerformanceProfiler

# Decorator profiling
@profile
def expensive_calculation():
    # Your code here
    return optimizer.max_sharpe_ratio()

result = expensive_calculation()

# Get profiling statistics
profiler = PerformanceProfiler()
stats = profiler.get_stats('expensive_calculation')
print(f"Average execution time: {stats['mean']:.2f}ms")
print(f"P95 latency: {stats['p95']:.2f}ms")
```

### Monitoring

```python
from quantlib_pro.observability import RealTimeMonitor

monitor = RealTimeMonitor()

# Track operations
with monitor.track('portfolio_optimization'):
    optimal_weights = optimizer.max_sharpe_ratio()

# Check performance
metrics = monitor.get_metrics('portfolio_optimization')
if metrics['avg_duration_ms'] > 1000:
    print("⚠️ Performance degradation detected!")
```

---

## Best Practices

### 1. Data Quality

```python
# Always validate data before analysis
from quantlib_pro.data import DataValidator

validator = DataValidator()

# Check for missing data
missing = validator.check_missing_data(data)
if missing:
    print(f"Warning: {len(missing)} missing data points")
    data = data.fillna(method='ffill')  # Forward fill

# Check for outliers
outliers = validator.detect_outliers(returns, n_std=4)
```

### 2. Risk Management

```python
# Always set position limits
max_position_size = 0.10  # 10% max per position
max_sector_exposure = 0.40  # 40% max per sector

# Use stop losses
stop_loss_pct = 0.05  # 5% stop loss

# Monitor leverage
max_leverage = 1.5  # 1.5x maximum leverage
```

### 3. Testing

```python
# Always validate models before production
from quantlib_pro.testing import ModelValidator

validator = ModelValidator(tolerance=0.01)
results = validator.validate_all_models()

if not results['all_passed']:
    print("❌ Model validation failed!")
    print(results.generate_report())
```

### 4. Transaction Costs

```python
# Include realistic transaction costs
optimizer = PortfolioOptimizer(
    expected_returns=returns,
    cov_matrix=cov_matrix,
    transaction_cost=0.001,  # 10 bps
    turnover_limit=0.30      # 30% max turnover
)
```

### 5. Backtesting

```python
# Avoid lookahead bias
# Never use future data in historical analysis

# Use walk-forward analysis
# Train on in-sample, test on out-of-sample

# Account for market impact
# Use realistic fill prices for large orders
```

---

## See Also

- [API Reference](../api/README.md)
- [Tutorials](../tutorials/)
- [Architecture](../architecture.md)
- [Examples](../../examples/)
