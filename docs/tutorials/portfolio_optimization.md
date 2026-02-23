# Tutorial: Building Your First Quantitative Portfolio

This tutorial walks you through building, analyzing, and optimizing a quantitative portfolio from scratch.

## What You'll Learn

- Fetching and preparing market data
- Calculating expected returns and risk
- Portfolio optimization techniques
- Risk analysis (VaR, CVaR, stress testing)
- Performance monitoring

**Time:** 30-45 minutes  
**Level:** Beginner to Intermediate

---

## Prerequisites

```bash
# Ensure QuantLib Pro is installed
pip install -r requirements.txt

# Start the application
streamlit run Home.py
```

---

## Step 1: Define Your Investment Universe

Let's build a diversified portfolio across different sectors:

```python
import quantlib_pro as qlp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Define tickers
tech_stocks = ['AAPL', 'MSFT', 'GOOGL']
finance_stocks = ['JPM', 'BAC', 'GS']
healthcare_stocks = ['JNJ', 'UNH', 'PFE']
consumer_stocks = ['AMZN', 'WMT', 'HD']

all_tickers = tech_stocks + finance_stocks + healthcare_stocks + consumer_stocks

print(f"Portfolio Universe: {len(all_tickers)} stocks")
print(f"Tech: {len(tech_stocks)} | Finance: {len(finance_stocks)} | "
      f"Healthcare: {len(healthcare_stocks)} | Consumer: {len(consumer_stocks)}")
```

**Output:**
```
Portfolio Universe: 12 stocks
Tech: 3 | Finance: 3 | Healthcare: 3 | Consumer: 3
```

---

## Step 2: Fetch Historical Data

```python
from quantlib_pro.data import MarketDataProvider

# Initialize data provider
provider = MarketDataProvider(source='yfinance')

# Define time period (3 years of historical data)
end_date = datetime.now()
start_date = end_date - timedelta(days=3*365)

# Fetch data
print("Fetching historical data...")
data = provider.get_historical_data(
    tickers=all_tickers,
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d')
)

# Extract closing prices
prices = data['Close']
print(f"Data shape: {prices.shape}")
print(f"Date range: {prices.index[0]} to {prices.index[-1]}")
```

**Output:**
```
Fetching historical data...
Data shape: (755, 12)
Date range: 2021-02-23 to 2024-02-23
```

---

## Step 3: Calculate Returns and Statistics

```python
# Calculate daily returns
returns = prices.pct_change().dropna()

# Basic statistics
print("\nReturns Statistics:")
print(f"Mean daily return: {returns.mean().mean():.4%}")
print(f"Median daily return: {returns.median().median():.4%}")
print(f"Daily volatility: {returns.std().mean():.4%}")

# Annualized metrics (assuming 252 trading days)
ann_returns = returns.mean() * 252
ann_volatility = returns.std() * np.sqrt(252)

print("\nAnnualized Metrics:")
for ticker in all_tickers:
    print(f"{ticker:6s} | Return: {ann_returns[ticker]:7.2%} | "
          f"Volatility: {ann_volatility[ticker]:6.2%}")
```

**Output:**
```
Returns Statistics:
Mean daily return: 0.0615%
Median daily return: 0.1201%
Daily volatility: 1.8542%

Annualized Metrics:
AAPL   | Return: 15.23% | Volatility: 28.45%
MSFT   | Return: 18.67% | Volatility: 25.32%
GOOGL  | Return: 12.45% | Volatility: 30.12%
...
```

---

## Step 4: Visualize Correlations

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Calculate correlation matrix
correlation_matrix = returns.corr()

# Plot heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0)
plt.title('Stock Return Correlations')
plt.tight_layout()
plt.savefig('correlation_matrix.png')
plt.show()

# Sector correlations
tech_corr = returns[tech_stocks].corr().values[np.triu_indices_from(correlation_matrix, k=1)].mean()
print(f"\nAverage intra-sector correlation:")
print(f"Tech stocks: {tech_corr:.2f}")
```

---

## Step 5: Portfolio Optimization

### 5a. Maximum Sharpe Ratio Portfolio

```python
from quantlib_pro.portfolio import PortfolioOptimizer

# Prepare inputs
expected_returns = returns.mean() * 252
cov_matrix = returns.cov() * 252
risk_free_rate = 0.03  # 3% risk-free rate

# Create optimizer
optimizer = PortfolioOptimizer(
    expected_returns=expected_returns,
    cov_matrix=cov_matrix,
    risk_free_rate=risk_free_rate
)

# Find maximum Sharpe ratio portfolio
print("Optimizing for maximum Sharpe ratio...")
optimal_weights = optimizer.max_sharpe_ratio()

# Display results
print("\nOptimal Portfolio Weights:")
for ticker, weight in zip(all_tickers, optimal_weights):
    if weight > 0.01:  # Only show positions > 1%
        print(f"{ticker:6s}: {weight:6.2%}")

# Portfolio performance
performance = optimizer.portfolio_performance(optimal_weights)
print(f"\nPortfolio Metrics:")
print(f"Expected Return: {performance['return']:.2%}")
print(f"Volatility: {performance['volatility']:.2%}")
print(f"Sharpe Ratio: {performance['sharpe']:.2f}")
```

**Output:**
```
Optimizing for maximum Sharpe ratio...

Optimal Portfolio Weights:
AAPL  : 15.23%
MSFT  : 22.45%
GOOGL :  8.12%
JPM   : 12.34%
JNJ   : 18.76%
UNH   : 10.45%
AMZN  :  9.67%
WMT   :  2.98%

Portfolio Metrics:
Expected Return: 14.56%
Volatility: 18.23%
Sharpe Ratio: 0.63
```

### 5b. Minimum Volatility Portfolio

```python
# Find minimum volatility portfolio
min_vol_weights = optimizer.min_volatility()

min_vol_performance = optimizer.portfolio_performance(min_vol_weights)
print(f"\nMinimum Volatility Portfolio:")
print(f"Expected Return: {min_vol_performance['return']:.2%}")
print(f"Volatility: {min_vol_performance['volatility']:.2%}")
print(f"Sharpe Ratio: {min_vol_performance['sharpe']:.2f}")
```

### 5c. Efficient Frontier

```python
# Generate efficient frontier
print("Generating efficient frontier...")
frontier = optimizer.efficient_frontier(n_points=50)

# Plot efficient frontier
plt.figure(figsize=(10, 6))
plt.scatter(frontier['volatility'], frontier['return'], c=frontier['sharpe'], cmap='viridis')
plt.colorbar(label='Sharpe Ratio')
plt.xlabel('Volatility (Annual)')
plt.ylabel('Expected Return (Annual)')
plt.title('Efficient Frontier')

# Mark optimal portfolio
plt.scatter(performance['volatility'], performance['return'], 
           marker='*', s=500, c='red', label='Max Sharpe')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('efficient_frontier.png')
plt.show()
```

---

## Step 6: Risk Analysis

### 6a. Value at Risk (VaR)

```python
from quantlib_pro.risk import RiskCalculator

calculator = RiskCalculator()

# Calculate portfolio returns
portfolio_returns = (returns * optimal_weights).sum(axis=1)

# Portfolio value
portfolio_value = 1_000_000  # $1 million

# Calculate VaR at different confidence levels
var_90 = calculator.historical_var(portfolio_returns, 0.90, portfolio_value)
var_95 = calculator.historical_var(portfolio_returns, 0.95, portfolio_value)
var_99 = calculator.historical_var(portfolio_returns, 0.99, portfolio_value)

print(f"\nValue at Risk (1-day):")
print(f"90% VaR: ${-var_90:,.0f}")
print(f"95% VaR: ${-var_95:,.0f}")
print(f"99% VaR: ${-var_99:,.0f}")

# CVaR (Expected Shortfall)
cvar_95 = calculator.cvar(portfolio_returns, 0.95, portfolio_value)
print(f"\n95% CVaR: ${-cvar_95:,.0f}")
print(f"(Expected loss if VaR is exceeded)")
```

**Output:**
```
Value at Risk (1-day):
90% VaR: $23,450
95% VaR: $31,230
99% VaR: $47,890

95% CVaR: $42,560
(Expected loss if VaR is exceeded)
```

### 6b. Stress Testing

```python
from quantlib_pro.risk import StressTester

tester = StressTester(portfolio_returns)

# Historical stress test: COVID-19 crash (Feb-Mar 2020)
print("\nStress Test: COVID-19 Crash (Feb-Mar 2020)")
covid_stress = tester.historical_stress_test(
    scenario_start='2020-02-20',
    scenario_end='2020-03-23'
)
print(f"Portfolio Loss: {covid_stress['portfolio_loss']:.2%}")

# Hypothetical stress scenario
print("\nHypothetical Stress: Tech Crash")
tech_crash = tester.hypothetical_stress_test(
    shocks={
        'AAPL': -0.30,
        'MSFT': -0.25,
        'GOOGL': -0.35,
        'AMZN': -0.28,
    }
)
print(f"Portfolio Loss: {tech_crash['portfolio_loss']:.2%}")

# Monte Carlo stress test
print("\nMonte Carlo Stress Test (1000 scenarios)")
mc_stress = tester.monte_carlo_stress_test(
    n_scenarios=1000,
    worst_percentile=0.05  # Worst 5% of scenarios
)
print(f"Average loss in worst 5%: {mc_stress['avg_loss']:.2%}")
print(f"Maximum loss: {mc_stress['max_loss']:.2%}")
```

---

## Step 7: Implement Portfolio with Constraints

Real-world portfolios often have constraints. Let's add some:

```python
# Constraints:
# 1. Long-only (no short selling)
# 2. Max 25% in any single stock
# 3. Max 40% in any sector
# 4. Min 2% position size (or 0)

from scipy.optimize import LinearConstraint, NonlinearConstraint

# Sector mappings
sectors = {
    'Tech': [0, 1, 2],      # AAPL, MSFT, GOOGL
    'Finance': [3, 4, 5],    # JPM, BAC, GS
    'Healthcare': [6, 7, 8], # JNJ, UNH, PFE
    'Consumer': [9, 10, 11]  # AMZN, WMT, HD
}

# Build constraints
constraints_list = []

# 1. Long-only
constraints_list.append({'type': 'ineq', 'fun': lambda w: w})

# 2. Max 25% per stock
constraints_list.append({'type': 'ineq', 'fun': lambda w: 0.25 - w})

# 3. Max 40% per sector
for sector_name, indices in sectors.items():
    def sector_constraint(w, idx=indices):
        return 0.40 - sum(w[i] for i in idx)
    constraints_list.append({'type': 'ineq', 'fun': sector_constraint})

# Optimize with constraints
constrained_weights = optimizer.max_sharpe_ratio(constraints=constraints_list)

print("\nConstrained Portfolio Weights:")
for ticker, weight in zip(all_tickers, constrained_weights):
    if weight > 0.01:
        print(f"{ticker:6s}: {weight:6.2%}")

# Verify sector exposures
print("\nSector Exposures:")
for sector_name, indices in sectors.items():
    exposure = sum(constrained_weights[i] for i in indices)
    print(f"{sector_name:12s}: {exposure:6.2%}")

# Performance
constrained_perf = optimizer.portfolio_performance(constrained_weights)
print(f"\nConstrained Portfolio:")
print(f"Expected Return: {constrained_perf['return']:.2%}")
print(f"Volatility: {constrained_perf['volatility']:.2%}")
print(f"Sharpe Ratio: {constrained_perf['sharpe']:.2f}")
```

---

## Step 8: Monitor Performance

```python
from quantlib_pro.observability import RealTimeMonitor

monitor = RealTimeMonitor()

# Set baseline performance
monitor.set_baseline('portfolio_optimization', 
                    avg_duration_ms=250, 
                    p95_duration_ms=400)

# Track optimization
with monitor.track('portfolio_optimization'):
    weights = optimizer.max_sharpe_ratio()

# Check for performance issues
metrics = monitor.get_metrics('portfolio_optimization')
print(f"\nOptimization Performance:")
print(f"Duration: {metrics['avg_duration_ms']:.0f}ms")
print(f"Status: {'✅ Normal' if metrics['is_healthy'] else '⚠️ Degraded'}")
```

---

## Next Steps

Congratulations! You've built and analyzed your first quantitative portfolio. Here's what to explore next:

1. **Backtesting**: Test your portfolio strategy on historical data
   - See [Backtesting Tutorial](backtesting_tutorial.md)

2. **Advanced Risk**: Explore correlation regimes and tail risk
   - See [Risk Analytics Tutorial](risk_analytics_tutorial.md)

3. **Options Strategies**: Add derivatives to your portfolio
   - See [Options Tutorial](options_tutorial.md)

4. **Rebalancing**: Implement dynamic rebalancing strategies
   - See [Rebalancing Tutorial](rebalancing_tutorial.md)

---

## Full Code

Complete working example:

```python
# portfolio_builder.py
import quantlib_pro as qlp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'JPM', 'BAC', 'GS', 
           'JNJ', 'UNH', 'PFE', 'AMZN', 'WMT', 'HD']
LOOKBACK_DAYS = 3 * 365
RISK_FREE_RATE = 0.03
PORTFOLIO_VALUE = 1_000_000

def main():
    # 1. Fetch data
    provider = qlp.data.MarketDataProvider(source='yfinance')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    data = provider.get_historical_data(
        tickers=TICKERS,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    # 2. Calculate returns
    prices = data['Close']
    returns = prices.pct_change().dropna()
    
    # 3. Optimize portfolio
    optimizer = qlp.portfolio.PortfolioOptimizer(
        expected_returns=returns.mean() * 252,
        cov_matrix=returns.cov() * 252,
        risk_free_rate=RISK_FREE_RATE
    )
    
    weights = optimizer.max_sharpe_ratio()
    performance = optimizer.portfolio_performance(weights)
    
    # 4. Risk analysis
    calculator = qlp.risk.RiskCalculator()
    portfolio_returns = (returns * weights).sum(axis=1)
    
    var_95 = calculator.historical_var(portfolio_returns, 0.95, PORTFOLIO_VALUE)
    cvar_95 = calculator.cvar(portfolio_returns, 0.95, PORTFOLIO_VALUE)
    
    # 5. Results
    print("=" * 60)
    print("PORTFOLIO OPTIMIZATION RESULTS")
    print("=" * 60)
    print(f"\nExpected Return: {performance['return']:.2%}")
    print(f"Volatility: {performance['volatility']:.2%}")
    print(f"Sharpe Ratio: {performance['sharpe']:.2f}")
    print(f"\n95% VaR (1-day): ${-var_95:,.0f}")
    print(f"95% CVaR (1-day): ${-cvar_95:,.0f}")
    print("\nWeights:")
    for ticker, weight in zip(TICKERS, weights):
        if weight > 0.01:
            print(f"  {ticker:6s}: {weight:6.2%}")

if __name__ == '__main__':
    main()
```

Run with:
```bash
python portfolio_builder.py
```

---

## Troubleshooting

**Issue: Data fetch fails**
```python
# Solution: Check internet connection and API limits
# Try alternative data source
provider = MarketDataProvider(source='alpha_vantage', api_key='YOUR_KEY')
```

**Issue: Optimization doesn't converge**
```python
# Solution: Relax constraints or use different solver
weights = optimizer.max_sharpe_ratio(method='SLSQP', options={'maxiter': 1000})
```

**Issue: Negative Sharpe ratios**
```python
# Solution: Check if risk-free rate is too high or returns too low
# Adjust risk-free rate
optimizer.risk_free_rate = 0.01  # Lower risk-free rate
```

---

## See Also

- [User Guide](../guides/user_guide.md)
- [API Reference](../api/README.md)
- [More Tutorials](README.md)
