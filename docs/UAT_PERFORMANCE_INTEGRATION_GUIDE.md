# UAT Dashboard & Performance Profiling Integration Guide

## Overview

This guide explains how the **UAT Dashboard** and **Performance Profiling** systems are fully integrated with the QuantLib Pro project, including real-world usage examples and how to leverage these features for quality assurance.

---

# 🧪 UAT Dashboard - Complete Integration

## Architecture

The UAT (User Acceptance Testing) Dashboard is fully connected through the `quantlib_pro.uat` module, which provides comprehensive testing infrastructure.

### Module Structure

```
quantlib_pro/uat/
├── __init__.py               # Module exports
├── scenarios.py              # Test scenario definitions and execution
├── feedback.py               # User feedback collection and analysis
├── bug_tracker.py            # Bug tracking and management
└── performance_validation.py # Performance benchmarking
```

---

## 1. Test Scenarios System

### UATScenarioLibrary

Pre-defined test scenarios covering all major features:

```python
from quantlib_pro.uat import UATScenarioLibrary, UATExecutor

# Get all test scenarios
scenarios = UATScenarioLibrary.get_all_scenarios()

# Scenarios are organized by:
# - User Role (Quant, Trader, Risk Manager, Portfolio Manager)
# - Priority (Critical, High, Medium, Low)
# - Category (Portfolio, Risk, Options, etc.)

# Example scenario structure:
{
    'scenario_id': 'UAT-PORT-001',
    'title': 'Portfolio Creation and Analysis',
    'description': 'Test complete portfolio workflow',
    'user_role': UserRole.PORTFOLIO_MANAGER,
    'priority': Priority.CRITICAL,
    'category': 'Portfolio',
    'preconditions': ['Market data available', 'No existing portfolio'],
    'steps': [
        {
            'step_number': 1,
            'description': 'Navigate to Portfolio page',
            'expected_result': 'Portfolio page loads successfully',
            'actual_result': None,
            'status': TestStatus.NOT_STARTED
        },
        # Additional steps...
    ],
    'acceptance_criteria': [
        'Portfolio is created with correct weights',
        'Performance metrics are calculated accurately',
        'Risk metrics match expected values'
    ]
}
```

### Built-in Test Scenarios

#### **Portfolio Testing (7 scenarios)**
- UAT-PORT-001: Portfolio Creation and Analysis
- UAT-PORT-002: Portfolio Optimization
- UAT-PORT-003: Rebalancing Workflow
- UAT-PORT-004: Performance Attribution
- UAT-PORT-005: Multi-Period Analysis
- UAT-PORT-006: Benchmark Comparison
- UAT-PORT-007: Export Functionality

#### **Risk Testing (6 scenarios)**
- UAT-RISK-001: VaR Calculation
- UAT-RISK-002: Stress Testing
- UAT-RISK-003: Scenario Analysis
- UAT-RISK-004: Risk Decomposition
- UAT-RISK-005: Correlation Analysis
- UAT-RISK-006: Tail Risk Analysis

#### **Options Testing (5 scenarios)**
- UAT-OPT-001: Black-Scholes Pricing
- UAT-OPT-002: Greeks Calculation
- UAT-OPT-003: Implied Volatility
- UAT-OPT-004: Monte Carlo Pricing
- UAT-OPT-005: Option Strategies

#### **Market Regime Testing (4 scenarios)**
- UAT-REG-001: Regime Detection
- UAT-REG-002: Volatility Clustering
- UAT-REG-003: Regime Transitions
- UAT-REG-004: Real-time Monitoring

#### **Backtesting (5 scenarios)**
- UAT-BACK-001: Strategy Creation
- UAT-BACK-002: Historical Backtest
- UAT-BACK-003: Performance Metrics
- UAT-BACK-004: Risk Analysis
- UAT-BACK-005: Optimization

### Running UAT Scenarios

```python
from quantlib_pro.uat import UATExecutor, TestStatus

executor = UATExecutor()
executor.load_scenarios(UATScenarioLibrary.get_all_scenarios())

# Execute a specific scenario
scenario_id = 'UAT-PORT-001'
result = executor.execute_scenario(scenario_id)

# Update scenario status
executor.update_scenario_status(scenario_id, TestStatus.PASSED)

# Add notes/comments
executor.add_scenario_note(
    scenario_id,
    "Successfully created portfolio with 5 ETFs. Performance metrics accurate."
)

# Get execution summary
summary = executor.get_summary()
print(f"Total: {summary['total_scenarios']}")
print(f"Passed: {summary['passed']}")
print(f"Failed: {summary['failed']}")
print(f"Pass Rate: {summary['pass_rate']:.1f}%")
```

---

## 2. Feedback Collection System

### FeedbackCollector

Collects and manages user feedback across all pages:

```python
from quantlib_pro.uat import FeedbackCollector, FeedbackType, Severity

collector = FeedbackCollector()

# Submit feedback
feedback = collector.submit_feedback(
    feedback_type=FeedbackType.BUG,          # BUG, FEATURE_REQUEST, IMPROVEMENT, QUESTION
    title="Portfolio weights not summing to 1.0",
    description="When entering manual weights, total is 0.999 instead of 1.0",
    severity=Severity.HIGH,                   # CRITICAL, HIGH, MEDIUM, LOW
    page="Portfolio",
    user_name="John Doe",
    user_role="Portfolio Manager",
    expected_behavior="Weights should sum exactly to 1.0",
    actual_behavior="Sum is 0.999 due to rounding",
    steps_to_reproduce=[
        "Enter 3 tickers: SPY, QQQ, IWM",
        "Set weights: 0.333, 0.333, 0.334",
        "Click 'Analyze Portfolio'",
        "Notice total = 0.999"
    ]
)

print(f"Feedback ID: {feedback.feedback_id}")
# Output: FEED-20260224-001
```

### Feedback Analysis

```python
from quantlib_pro.uat import FeedbackAnalyzer

analyzer = FeedbackAnalyzer(collector)

# Get sentiment analysis
sentiment = analyzer.analyze_sentiment()
print(f"Positive: {sentiment['positive_rate']:.1f}%")
print(f"Negative: {sentiment['negative_rate']:.1f}%")

# Get trending issues
trending = analyzer.get_trending_issues(days=7)
for issue in trending:
    print(f"{issue['title']}: {issue['count']} occurrences")

# Common pain points
pain_points = analyzer.identify_pain_points()
for pain_point in pain_points:
    print(f"Page: {pain_point['page']}")
    print(f"Issue: {pain_point['issue']}")
    print(f"Frequency: {pain_point['frequency']}")

# Feature requests (most requested)
features = analyzer.get_feature_requests(top_n=10)
for feature in features:
    print(f"{feature['title']}: {feature['votes']} votes")
```

---

## 3. Bug Tracking System

### BugTracker

Comprehensive bug tracking integrated with feedback:

```python
from quantlib_pro.uat import BugTracker, BugPriority, BugCategory

tracker = BugTracker()

# Report bug
bug = tracker.report_bug(
    title="VaR calculation incorrect for negative returns",
    category=BugCategory.CALCULATION,       # UI, CALCULATION, PERFORMANCE, DATA, etc.
    severity=Severity.CRITICAL,
    priority=BugPriority.P1,                # P1 (Critical) to P4 (Low)
    description="Historical VaR returning positive values when should be negative",
    reporter="Jane Smith",
    page="Risk Dashboard",
    steps_to_reproduce=[
        "Load portfolio with AAPL, MSFT, GOOGL",
        "Set date range to 2022-01-01 to 2022-12-31",
        "Calculate 95% VaR",
        "Observe: VaR = +2.5% (should be -2.5%)"
    ],
    expected_behavior="VaR should be negative (loss)",
    actual_behavior="VaR is positive",
    affected_users="All users calculating VaR",
    workaround="Manually negate the value"
)

print(f"Bug ID: {bug.bug_id}")
# Output: BUG-20260224-001

# Assign bug
tracker.assign_bug(bug.bug_id, assignee="Dev Team")

# Update bug status
tracker.update_bug_status(bug.bug_id, "In Progress")

# Resolve bug
tracker.resolve_bug(
    bug.bug_id,
    resolution="Fixed sign error in VaR calculation. Now returns negative values correctly.",
    fixed_by="Developer A",
    fix_version="v1.2.1"
)
```

### Bug Metrics

```python
metrics = tracker.get_bug_metrics()

print(f"Total Bugs: {metrics['total']}")
print(f"Open: {metrics['open']}")
print(f"Resolved: {metrics['resolved']}")
print(f"Resolution Rate: {metrics['resolution_rate']:.1f}%")
print(f"Avg Resolution Time: {metrics['avg_resolution_time_hours']:.1f} hours")

# By priority
for priority, counts in metrics['by_priority'].items():
    print(f"{priority}: {counts['open']} open, {counts['resolved']} resolved")

# By category
for category, count in metrics['by_category'].items():
    print(f"{category}: {count} bugs")

# Critical bugs
critical_bugs = tracker.get_critical_bugs()
print(f"Critical bugs requiring immediate attention: {len(critical_bugs)}")
```

---

## 4. Performance Validation System

### PerformanceValidator

Automated performance benchmarking to detect regressions:

```python
from quantlib_pro.uat import PerformanceValidator

validator = PerformanceValidator()

# Run all benchmarks
results = validator.run_all_benchmarks(executions=10)

# Run specific category
results = validator.run_all_benchmarks(category='portfolio', executions=20)

# Get summary
summary = validator.get_summary()
print(f"Total Tests: {summary['total']}")
print(f"Passed: {summary['passed']}")
print(f"Failed: {summary['failed']}")
print(f"Pass Rate: {summary['pass_rate']:.1f}%")

# Check for regressions
regressions = validator.get_regressions()
if regressions:
    print(f"⚠️ {len(regressions)} performance regressions detected!")
    for reg in regressions:
        print(f"  {reg.benchmark_name}: {reg.regression_pct:.1f}% slower")
        print(f"    Current: {reg.mean_ms:.2f}ms vs Baseline: {reg.baseline_ms:.2f}ms")
```

### Built-in Benchmarks

```python
# Portfolio benchmarks
- benchmark_portfolio_metrics: Portfolio calculations
- benchmark_portfolio_optimization: Optimization algorithms
- benchmark_portfolio_rebalancing: Rebalancing logic

# Risk benchmarks
- benchmark_var_calculation: VaR computation
- benchmark_stress_testing: Stress test scenarios
- benchmark_correlation_matrix: Correlation calculations

# Options benchmarks
- benchmark_black_scholes: Analytical pricing
- benchmark_monte_carlo: MC simulation
- benchmark_greeks_calculation: Greeks computation
- benchmark_implied_volatility: IV solver

# Market regime benchmarks
- benchmark_regime_detection: HMM/clustering
- benchmark_volatility_estimation: GARCH/EWMA

# Backtest benchmarks
- benchmark_strategy_backtest: Full backtest
- benchmark_performance_metrics: Metric calculations
```

### Custom Benchmarks

```python
from quantlib_pro.uat import PerformanceBenchmark

# Define custom benchmark
custom_benchmark = PerformanceBenchmark(
    name="custom_calculation",
    category="custom",
    baseline_ms=100.0,          # Expected time in milliseconds
    max_regression_pct=20.0,    # Allow 20% regression before failure
    description="Custom heavy calculation",
    function=my_custom_function,
    function_args={'param1': 100, 'param2': 'test'}
)

# Add to validator
validator.add_benchmark(custom_benchmark)

# Run it
result = validator.run_benchmark(custom_benchmark, executions=10)
```

---

## 5. UAT Dashboard UI Integration

### Navigation Flow

```
streamlit_app.py → pages/9_UAT_Dashboard.py
                   │
                   ├── Tab 1: UAT Scenarios
                   │   ├── Filter by role/priority/status
                   │   ├── Execute scenarios
                   │   └── Update results
                   │
                   ├── Tab 2: Feedback
                   │   ├── Submit new feedback
                   │   ├── View recent feedback
                   │   └── Statistics
                   │
                   ├── Tab 3: Bug Tracking
                   │   ├── View critical bugs
                   │   ├── Bug distribution charts
                   │   └── Bug metrics
                   │
                   ├── Tab 4: Performance
                   │   ├── Run benchmarks
                   │   ├── View results
                   │   └── Detect regressions
                   │
                   ├── Tab 5: Reports
                   │   ├── Export feedback CSV
                   │   ├── Export bug report JSON
                   │   └── Export performance report
                   │
                   └── Tab 6: Overall Metrics
                       ├── Test execution status
                       ├── Feedback by type
                       ├── Quality score
                       └── Trending issues
```

### Real-World Usage Example

```python
# Step 1: Tester navigates to UAT Dashboard
# → Opens "UAT Scenarios" tab

# Step 2: Select and execute scenario
scenario_id = 'UAT-PORT-001'  # Portfolio Creation
executor.execute_scenario(scenario_id)

# Step 3: Test each step manually
for step in scenario.steps:
    # Perform action (e.g., create portfolio)
    # Verify expected result
    # Update step status
    executor.update_step_status(scenario_id, step.step_number, TestStatus.PASSED)

# Step 4: If issue found → Submit feedback
if issue_found:
    feedback = collector.submit_feedback(
        feedback_type=FeedbackType.BUG,
        title="Portfolio weights validation error",
        severity=Severity.HIGH,
        page="Portfolio",
        # ... details
    )
    
    # Also report as bug if critical
    if severity == Severity.CRITICAL:
        bug = tracker.report_bug(
            title=feedback.title,
            # ... bug details
        )

# Step 5: Review performance
# → Navigate to "Performance" tab
# → Run portfolio benchmarks
validator.run_all_benchmarks(category='portfolio')

# Step 6: Check for regressions
regressions = validator.get_regressions()
if regressions:
    # Report as bug
    tracker.report_bug(
        title=f"Performance regression in {reg.benchmark_name}",
        category=BugCategory.PERFORMANCE,
        severity=Severity.MEDIUM,
        #... details
    )

# Step 7: Generate report
# → Navigate to "Reports" tab
# → Export feedback CSV for analysis
# → Export bug report for developers
collector.export_csv("uat_report_20260224.csv")
tracker.export_bug_report("bugs_20260224.json")
```

---

# 🎯 Performance Profiling - Complete Integration

## Architecture

Performance profiling is fully integrated through the `quantlib_pro.observability` module.

### Module Structure

```
quantlib_pro/observability/
├── __init__.py          # Module exports
├── profiler.py          # Performance profiler (main)
├── performance.py       # Performance decorators and utilities
├── monitoring.py        # Real-time monitoring
├── metrics.py          # Custom metrics collection
└── health.py           # System health checks
```

---

## 1. PerformanceProfiler

### Core Profiler Class

```python
from quantlib_pro.observability.profiler import PerformanceProfiler, profile

# Global profiler instance
profiler = PerformanceProfiler()

# Decorator usage
@profile
def expensive_calculation(n):
    """Calculate something expensive."""
    result = sum(i**2 for i in range(n))
    return result

# Call function normally
result = expensive_calculation(1000000)

# Check profiler data
report = profiler.generate_report()
print(report)
```

### Context Manager Usage

```python
from quantlib_pro.observability.profiler import get_profiler

profiler = get_profiler()

# Measure code block
with profiler.measure("portfolio_optimization"):
    # ... portfolio optimization code
    weights = optimize_portfolio(returns, cov_matrix)

# Measure with metadata
with profiler.measure("var_calculation", metadata={'method': 'historical', 'confidence': 0.95}):
    var = calculate_var(returns, confidence=0.95)
```

### Automatic Instrumentation

The profiler automatically tracks:
- **All decorated functions** in quantlib_pro modules
- **Major operations**: Portfolio calculations, risk metrics, option pricing
- **Data operations**: Market data fetching, caching
- **UI rendering**: Streamlit page loads, chart generation

### Tracked Operations

```python
# Portfolio operations
- calculate_portfolio_metrics()
- optimize_portfolio()
- rebalance_portfolio()
- calculate_performance_attribution()

# Risk operations
- calculate_var()
- calculate_cvar()
- run_stress_test()
- calculate_correlation_matrix()

# Options operations
- price_option_black_scholes()
- price_option_monte_carlo()
- calculate_greeks()
- calculate_implied_volatility()

# Market regime operations
- detect_regimes()
- estimate_volatility()
- identify_clusters()

# Backtesting operations
- run_backtest()
- calculate_strategy_metrics()
- analyze_trades()
```

---

## 2. Performance Metrics

### PerformanceMeasurement

Each measurement contains:

```python
@dataclass
class PerformanceMeasurement:
    name: str                    # Function/operation name
    start_time: float           # Unix timestamp
    end_time: float             # Unix timestamp
    duration: float             # Seconds
    memory_start: Optional[float]  # MB (if psutil available)
    memory_end: Optional[float]    # MB
    memory_delta: Optional[float]  # MB change
    metadata: Dict[str, Any]    # Custom metadata
    
    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        return self.duration * 1000
    
    @property
    def memory_mb(self) -> Optional[float]:
        """Memory delta in MB."""
        if self.memory_delta:
            return self.memory_delta / (1024 * 1024)
        return None
```

### PerformanceStats

Aggregated statistics:

```python
@dataclass
class PerformanceStats:
    name: str          # Function name
    count: int         # Number of calls
    total_time: float  # Total execution time (s)
    min_time: float    # Minimum time (s)
    max_time: float    # Maximum time (s)
    mean_time: float   # Average time (s)
    std_time: float    # Standard deviation (s)
    median_time: float # Median time (s)
    p95_time: float    # 95th percentile (s)
    p99_time: float    # 99th percentile (s)
```

---

## 3. Profiler Report Generation

### Generate Performance Report

```python
profiler = get_profiler()

# Generate DataFrame report
report_df = profiler.generate_report()

# Report includes:
# - Function: Name of function/operation
# - Count: Number of executions
# - Total (ms): Total time spent
# - Mean (ms): Average execution time
# - Std (ms): Standard deviation
# - Min (ms): Fastest execution
# - Max (ms): Slowest execution
# - Median (ms): Median time
# - P95 (ms): 95th percentile
# - P99 (ms): 99th percentile

print(report_df.to_string())
```

### Example Report Output

```
Function                          Count  Total (ms)  Mean (ms)  Std (ms)  Min (ms)  Max (ms)  Median (ms)  P95 (ms)  P99 (ms)
portfolio_optimization               42    5,234.56     124.63     32.15     89.23    198.45       119.87    172.34    189.12
calculate_var                       156      876.23       5.62      1.23      3.45      12.34         5.23      8.45     10.23
price_option_black_scholes        1,234       98.45       0.08      0.02      0.05       0.15         0.07      0.11      0.13
fetch_market_data                    23    1,234.56      53.68     12.34     35.67      89.23        51.23     72.45     82.34
generate_volatility_surface          12    2,345.67     195.47     45.23    123.45     278.90       189.34    256.78    271.23
```

---

## 4. Performance Dashboard Integration

### Navigation Flow

```
streamlit_app.py → pages/8_📊_Advanced_Analytics.py
                   │
                   └── Tab 1: Performance Profiling
                       ├── Overview metrics (total time, calls, avg time)
                       ├── Performance table (all functions)
                       ├── Bottleneck visualization (top 10 slowest)
                       ├── Call distribution chart
                       └── Instructions for generating data
```

### UI Components

#### **Overview Metrics**
```python
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Execution Time", f"{total_time:.2f}s")

with col2:
    st.metric("Total Function Calls", f"{total_calls:,}")

with col3:
    st.metric("Average Time per Call", f"{avg_time*1000:.2f}ms")

with col4:
    st.metric("Slowest Function", slowest_function_name)
```

#### **Performance Table**
```python
# Full metrics table
st.dataframe(report_df, use_container_width=True, height=400)
```

#### **Bottleneck Visualization**
```python
# Top 10 slowest functions
fig = go.Figure(data=[
    go.Bar(
        x=top_funcs["Function"],
        y=top_funcs["Total_Time_Numeric"],
        marker_color='#ff7f0e',
        text=top_funcs["Total_Time_Numeric"].round(3),
        textposition='outside',
    )
])

fig.update_layout(
    title="Top 10 Slowest Functions",
    xaxis_title="Function",
    yaxis_title="Total Time (s)",
    template='plotly_dark',
    height=400,
)

st.plotly_chart(fig, use_container_width=True)
```

#### **Call Distribution**
```python
# Most frequently called functions
fig2 = go.Figure(data=[
    go.Bar(
        x=top_funcs["Function"],
        y=top_funcs["Count"],
        marker_color='#1f77b4',
        text=top_funcs["Count"],
        textposition='outside',
    )
])

fig2.update_layout(
    title="Top 10 Most Called Functions",
    xaxis_title="Function",
    yaxis_title="Number of Calls",
)

st.plotly_chart(fig2, use_container_width=True)
```

---

## 5. Generating Performance Data

### Workflow for Users

1. **Navigate to any dashboard and perform operations:**
   - 📈 Portfolio: Load portfolio, optimize, rebalance
   - ⚠️ Risk: Calculate VaR, run stress tests
   - 📊 Options: Price options, calculate Greeks
   - 🎯 Market Regime: Detect regimes, estimate volatility
   - 🌊 Volatility Surface: Generate surfaces
   - 📊 Backtesting: Run strategy backtests

2. **Operations are automatically profiled:**
   - Function calls are intercepted by `@profile` decorator
   - Execution time and memory usage recorded
   - Stored in global profiler instance

3. **View profiling data:**
   - Navigate to Advanced Analytics → Performance Profiling
   - See aggregated metrics
   - Identify bottlenecks
   - Export report for optimization

### Example Profiling Session

```python
# User navigates to Portfolio page
# → Enters tickers: AAPL, MSFT, GOOGL, AMZN, TSLA
# → Clicks "Analyze Portfolio"

# Behind the scenes:
@profile  # <-- Decorator captures this
def calculate_portfolio_metrics(tickers, weights):
    # Fetch data (profiled)
    data = fetch_market_data(tickers)
    
    # Calculate returns (profiled)
    returns = calculate_returns(data)
    
    # Calculate metrics (profiled)
    metrics = {
        'return': calculate_portfolio_return(returns, weights),
        'volatility': calculate_portfolio_volatility(returns, weights),
        'sharpe': calculate_sharpe_ratio(returns, weights),
    }
    
    return metrics

# User then navigates to Advanced Analytics → Performance Profiling
# → Sees all the profiled function calls
# → Top functions by time:
#     1. fetch_market_data: 234.5ms (5 calls)
#     2. calculate_portfolio_volatility: 45.6ms (1 call)
#     3. calculate_returns: 12.3ms (1 call)
```

---

## 6. Performance Optimization Workflow

### Identify Bottlenecks

```python
# 1. Review profiler report
report = profiler.generate_report()

# 2. Find slowest functions
slowest = report.nlargest(10, 'Total (ms)')

# 3. Analyze why they're slow
for idx, row in slowest.iterrows():
    print(f"{row['Function']}:")
    print(f"  Called {row['Count']} times")
    print(f"  Average: {row['Mean (ms)']}ms")
    print(f"  Total: {row['Total (ms)']}ms")
    print(f"  P95: {row['P95 (ms)']}ms")  # 95% of calls faster than this
    
    # If high call count with moderate time → caching opportunity
    # If low call count with high time → algorithm optimization needed
    # If high std dev → inconsistent performance, investigate outliers
```

### Optimization Strategies

#### **Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
@profile
def fetch_market_data(ticker, start_date, end_date):
    # Expensive data fetch
    data = api.get_data(ticker, start_date, end_date)
    return data

# Result: 10x speedup on repeated calls
```

#### **Vectorization**
```python
# Before (slow)
@profile
def calculate_returns_slow(prices):
    returns = []
    for i in range(1, len(prices)):
        returns.append((prices[i] - prices[i-1]) / prices[i-1])
    return returns

# After (fast)
@profile
def calculate_returns_fast(prices):
    return prices.pct_change().dropna()

# Result: 100x speedup
```

#### **Parallel Processing**
```python
from concurrent.futures import ThreadPoolExecutor

@profile
def fetch_multiple_tickers_parallel(tickers):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_market_data, ticker): ticker 
                   for ticker in tickers}
        results = {futures[future]: future.result() 
                   for future in futures}
    return results

# Result: 5x speedup (with 5 workers)
```

---

## 7. Integration with CI/CD

### Performance Regression Testing

```python
# In CI pipeline
def test_performance_regression():
    """Fail CI if performance regresses > 20%."""
    validator = PerformanceValidator()
    results = validator.run_all_benchmarks(executions=20)
    
    regressions = validator.get_regressions()
    
    if regressions:
        print("Performance regressions detected:")
        for reg in regressions:
            print(f"  {reg.benchmark_name}: {reg.regression_pct:.1f}% slower")
        
        # Fail CI
        assert False, f"{len(regressions)} performance regressions detected"
```

### Automated Profiling Reports

```python
# Generate daily profiling reports
import schedule

def generate_daily_profiling_report():
    profiler = get_profiler()
    report = profiler.generate_report()
    
    # Export to CSV
    report.to_csv(f"profiling_reports/report_{datetime.now():%Y%m%d}.csv")
    
    # Send email if bottlenecks detected
    slowest = report.nlargest(5, 'Total (ms)')
    if slowest['Total (ms)'].iloc[0] > 5000:  # > 5 seconds
        send_alert_email(slowest)

# Schedule
schedule.every().day.at("23:00").do(generate_daily_profiling_report)
```

---

## 8. Real-World Usage Examples

### Example 1: Portfolio Optimization Bottleneck

**Problem**: Portfolio optimization taking 30+ seconds

```python
# Before optimization
@profile
def optimize_portfolio(returns, constraints):
    # Using scipy.optimize.minimize
    result = minimize(
        objective_function,
        x0= =[1/n] * n,
        method='SLSQP',
        constraints=constraints,
        options={'maxiter': 1000}
    )
    return result.x

# Profiler shows:
# optimize_portfolio: Mean 32,456ms, P95 45,678ms
```

**Solution**: Switch to CVXPY convex optimization

```python
# After optimization
import cvxpy as cp

@profile
def optimize_portfolio_fast(returns, constraints):
    # Use convex optimization
    w = cp.Variable(n)
    ret = returns.mean() @ w
    risk = cp.quad_form(w, returns.cov())
    
    objective = cp.Maximize(ret - risk_aversion * risk)
    constraints = [cp.sum(w) == 1, w >= 0]
    
    problem = cp.Problem(objective, constraints)
    problem.solve()
    
    return w.value

# Profiler shows:
# optimize_portfolio_fast: Mean 234ms, P95 345ms
# Result: 140x speedup!
```

### Example 2: Market Data Fetching

**Problem**: Repeated API calls for same data

```python
# Before caching
@profile
def get_portfolio_data(tickers, start_date):
    data = {}
    for ticker in tickers:
        # API call every time
        data[ticker] = yfinance.download(ticker, start=start_date)
    return data

# Profiler shows:
# get_portfolio_data: Called 25 times, Total 125,000ms
```

**Solution**: Implement caching layer

```python
from functools import lru_cache
import pickle

# Persistent cache
class MarketDataCache:
    def __init__(self, cache_file='data/cache/market_data.pkl'):
        self.cache_file = cache_file
        self.load_cache()
    
    def load_cache(self):
        try:
            with open(self.cache_file, 'rb') as f:
                self.cache = pickle.load(f)
        except FileNotFoundError:
            self.cache = {}
    
    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
    
    @profile
    def get(self, ticker, start_date):
        key = f"{ticker}_{start_date}"
        
        if key in self.cache:
            # Cache hit
            return self.cache[key]
        
        # Cache miss - fetch from API
        data = yfinance.download(ticker, start=start_date)
        self.cache[key] = data
        self.save_cache()
        
        return data

# Profiler shows:
# MarketDataCache.get: Called 25 times, Total 5,000ms (cache hits)
# Result: 25x speedup!
```

---

## 9. Best Practices

### Profiling Best Practices

1. **Profile in production-like environment**
   - Same data volumes
   - Same number of concurrent users
   - Realistic network latency

2. **Run multiple iterations**
   - Minimum 10 executions per function
   - Calculate mean, median, P95, P99
   - Watch for outliers

3. **Profile before and after changes**
   - Baseline before optimization
   - Measure after optimization
   - Ensure no regressions in other functions

4. **Focus on bottlenecks**
   - 80/20 rule: 20% of functions use 80% of time
   - Optimize high-impact functions first
   - Don't micro-optimize fast functions

5. **Monitor in production**
   - Continuous profiling
   - Alert on regressions
   - Track performance over time

### UAT Best Practices

1. **Test early and often**
   - Run UAT scenarios before each release
   - Regression testing on all critical paths
   - Edge case testing

2. **Involve real users**
   - Portfolio managers test portfolio features
   - Traders test trading workflows
   - Risk managers test risk calculations

3. **Document everything**
   - Clear reproducible steps
   - Screenshots for UI issues
   - Expected vs. actual results

4. **Prioritize bugs correctly**
   - P1: Complete blocker (fix immediately)
   - P2: Major feature broken (fix this sprint)
   - P3: Minor issue (fix next sprint)
   - P4: Nice to have (backlog)

5. **Track metrics**
   - Test pass rate (target: > 95%)
   - Bug resolution time (target: < 24h for P1)
   - User satisfaction (target: > 4/5)

---

## 10. Troubleshooting

### Common Issues

#### **"No profiling data available"**
**Problem**: Profiler report is empty

**Solution**:
1. Ensure you've performed operations (not just opened pages)
2. Check that functions have `@profile` decorator
3. Verify global profiler instance is being used:
   ```python
   from quantlib_pro.observability.profiler import get_profiler
   profiler = get_profiler()
   print(f"Measurements: {len(profiler.measurements)}")
   ```

#### **"Performance metrics seem wrong"**
**Problem**: Times are unexpectedly high/low

**Solution**:
1. **Check execution count**: High counts inflate total time
2. **Check for caching**: First call slow, subsequent calls fast
3. **Check system load**: High CPU usage affects measurements
4. **Use median/P95**: More robust than mean (avoids outliers)

#### **"Feedback not saving"**
**Problem**: Submitted feedback not showing up

**Solution**:
1. Check file permissions for `data/uat/` directory
2. Verify FeedbackCollector initialization:
   ```python
   collector = FeedbackCollector()
   stats = collector.get_statistics()
   print(f"Total feedback: {stats['total']}")
   ```
3. Check feedback ID format: `FEED-YYYYMMDD-nnn`

---

## Summary

### UAT Dashboard Integration

✅ **Fully Connected**:
- `quantlib_pro.uat` module with 4 submodules
- 30+ pre-defined test scenarios across all features
- Complete feedback collection and analysis system
- Comprehensive bug tracking with metrics
- Automated performance validation with benchmarks

✅ **Usage**:
- Navigate to 9_UAT_Dashboard.py in Streamlit
- Execute test scenarios
- Submit feedback on any page
- Track bugs with priority/severity
- Run performance benchmarks
- Generate reports

### Performance Profiling Integration

✅ **Fully Connected**:
- `quantlib_pro.observability.profiler` module
- Automatic instrumentation of major operations
- Real-time performance tracking
- Statistical analysis (mean, median, P95, P99)
- Bottleneck identification

✅ **Usage**:
- Use any feature in QuantLib Pro
- Navigate to Advanced Analytics → Performance Profiling
- View aggregated metrics
- Identify slow functions
- Optimize based on data

---

*Last Updated: February 24, 2026*
*Version: 2.0.0*
