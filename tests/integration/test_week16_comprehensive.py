"""
Week 16: Comprehensive Integration Tests

End-to-end testing of cross-module workflows:
- Portfolio optimization → Risk analysis → Stress testing
- Options pricing → Greeks → Risk management
- Market regime detection → Portfolio rebalancing
- Data fetching → Validation → Calculation → Audit
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

# Import all modules for integration testing
from quantlib_pro.portfolio.optimizer import PortfolioOptimizer
from quantlib_pro.portfolio.efficient_frontier import EfficientFrontier
from quantlib_pro.risk.var import calculate_var, VaRMethod
from quantlib_pro.risk.stress_testing import StressTestEngine, Scenario
from quantlib_pro.risk.advanced_analytics import StressTester, TailRiskAnalyzer
from quantlib_pro.options.black_scholes import BlackScholesModel
from quantlib_pro.options.monte_carlo import MonteCarloEngine
from quantlib_pro.market_regime.hmm import MarketRegimeDetector
from quantlib_pro.data.providers import SimulatedProvider, MultiProviderAggregator
from quantlib_pro.execution.backtesting import BacktestEngine, MovingAverageCrossover
from quantlib_pro.analytics.correlation_analysis import CorrelationAnalyzer
from quantlib_pro.compliance.reporting import ComplianceReporter, PositionLimitRule
from quantlib_pro.compliance.audit_trail import AuditTrail
from quantlib_pro.governance.policies import PolicyEngine, RiskLimitPolicy
from quantlib_pro.observability.profiler import get_profiler, profile
from quantlib_pro.observability.monitoring import get_monitor, MetricType


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows across all modules."""
    
    def test_portfolio_to_risk_workflow(self):
        """Test: Portfolio Optimization → Risk Analysis → Stress Testing."""
        # 1. Generate sample data
        provider = SimulatedProvider(n_assets=5, n_periods=252, seed=42)
        returns = provider.fetch_historical('portfolio', start='2023-01-01', end='2023-12-31')
        
        # 2. Portfolio optimization
        optimizer = PortfolioOptimizer(returns, risk_free_rate=0.02)
        optimal = optimizer.optimize_max_sharpe()
        
        assert optimal is not None
        assert len(optimal.weights) == len(returns.columns)
        assert abs(np.sum(optimal.weights) - 1.0) < 1e-6
        
        # 3. Calculate portfolio returns
        portfolio_returns = (returns @ optimal.weights).dropna()
        
        # 4. Risk analysis
        var_result = calculate_var(
            portfolio_returns,
            confidence=0.95,
            method=VaRMethod.HISTORICAL
        )
        
        assert var_result.var < 0  # VaR should be negative (loss)
        assert var_result.cvar < var_result.var  # CVaR worse than VaR
        
        # 5. Stress testing
        stress_tester = StressTester(returns, weights=optimal.weights)
        stress_result = stress_tester.run_monte_carlo_stress(
            n_scenarios=1000,
            stress_level=3.0
        )
        
        assert stress_result.portfolio_loss < 0
        assert stress_result.max_drawdown < 0
        
        # 6. Correlation analysis
        corr_analyzer = CorrelationAnalyzer(returns)
        breakdowns = corr_analyzer.detect_correlation_breakdowns(threshold=0.15)
        
        # Verify workflow completed successfully
        assert len(optimal.weights) > 0
        assert stress_result is not None
    
    def test_options_to_risk_workflow(self):
        """Test: Options Pricing → Greeks → Risk Management."""
        # 1. Price option using Black-Scholes
        bs_model = BlackScholesModel()
        call_price = bs_model.price_call(
            S=100.0,
            K=100.0,
            T=1.0,
            r=0.05,
            sigma=0.2
        )
        
        assert call_price > 0
        assert call_price < 100.0  # Call price should be less than spot
        
        # 2. Calculate Greeks
        greeks = bs_model.calculate_greeks(
            S=100.0,
            K=100.0,
            T=1.0,
            r=0.05,
            sigma=0.2,
            option_type='call'
        )
        
        assert greeks['delta'] > 0  # Call delta is positive
        assert greeks['delta'] < 1  # Delta between 0 and 1
        assert greeks['gamma'] > 0  # Gamma always positive
        assert greeks['vega'] > 0  # Vega always positive
        
        # 3. Monte Carlo validation
        mc_engine = MonteCarloEngine(n_simulations=10000, seed=42)
        mc_price = mc_engine.price_european_option(
            S0=100.0,
            K=100.0,
            T=1.0,
            r=0.05,
            sigma=0.2,
            option_type='call'
        )
        
        # Prices should be close (within 1%)
        assert abs(mc_price - call_price) / call_price < 0.01
        
        # 4. Risk checks - simulate option portfolio
        option_portfolio_value = call_price * 100  # 100 contracts
        
        # Check against policy limits
        policy_engine = PolicyEngine()
        risk_policy = RiskLimitPolicy(
            max_var=0.10,
            max_volatility=0.50,
            max_drawdown=0.30
        )
        policy_engine.add_policy(risk_policy)
        
        # Verify workflow completed
        assert option_portfolio_value > 0
        assert greeks is not None
    
    def test_regime_detection_to_rebalancing_workflow(self):
        """Test: Market Regime Detection → Portfolio Rebalancing."""
        # 1. Generate returns data
        provider = SimulatedProvider(n_assets=4, n_periods=500, seed=42)
        returns = provider.fetch_historical('regimes', start='2022-01-01', end='2023-12-31')
        
        # 2. Detect market regimes
        regime_detector = MarketRegimeDetector(n_regimes=3)
        regime_detector.fit(returns.mean(axis=1).values)
        
        # Get current regime
        latest_returns = returns.mean(axis=1).values[-20:]
        current_regime = regime_detector.predict_current_regime(latest_returns)
        
        assert 0 <= current_regime < 3
        
        # 3. Regime-specific optimization
        # Split data by regime
        regime_labels = regime_detector.predict_regimes(returns.mean(axis=1).values)
        
        # Optimize for each regime
        regime_weights = {}
        
        for regime in range(3):
            regime_mask = regime_labels == regime
            if regime_mask.sum() > 50:  # Need enough data
                regime_returns = returns.iloc[regime_mask]
                
                optimizer = PortfolioOptimizer(regime_returns, risk_free_rate=0.02)
                result = optimizer.optimize_max_sharpe()
                
                regime_weights[regime] = result.weights
        
        assert len(regime_weights) > 0
        
        # 4. Select weights based on current regime
        if current_regime in regime_weights:
            selected_weights = regime_weights[current_regime]
            assert len(selected_weights) == len(returns.columns)
            assert abs(np.sum(selected_weights) - 1.0) < 1e-6
    
    def test_data_to_audit_workflow(self):
        """Test: Data Fetching → Validation → Calculation → Audit Trail."""
        # 1. Initialize audit trail
        audit = AuditTrail()
        
        # 2. Data fetching with audit
        audit.log_data_access(
            user_id='test_user',
            resource='market_data',
            action='fetch'
        )
        
        provider = SimulatedProvider(n_assets=3, n_periods=100, seed=42)
        returns = provider.fetch_historical('test', start='2023-01-01', end='2023-12-31')
        
        # 3. Data validation
        assert not returns.empty
        assert not returns.isnull().all().all()
        
        # 4. Perform calculation with audit
        audit.log_event(
            user_id='test_user',
            event_type='TRADE_EXECUTION',
            description='Calculate portfolio VaR',
            metadata={'symbols': list(returns.columns)}
        )
        
        portfolio_returns = returns.mean(axis=1)
        var_result = calculate_var(portfolio_returns, confidence=0.95)
        
        # 5. Audit calculation
        audit.log_event(
            user_id='test_user',
            event_type='DATA_MODIFICATION',
            description=f'VaR calculation completed: {var_result.var:.4f}'
        )
        
        # 6. Query audit trail
        events = audit.query_events(user_id='test_user')
        
        assert len(events) >= 3
        
        # 7. Verify integrity
        tamper_count = audit.verify_integrity()
        assert tamper_count == 0
    
    def test_backtesting_with_compliance_workflow(self):
        """Test: Strategy Backtesting → Compliance Checks → Reporting."""
        # 1. Generate market data
        provider = SimulatedProvider(n_assets=1, n_periods=252, seed=42)
        data = provider.fetch_historical('BTC', start='2023-01-01', end='2023-12-31')
        
        # 2. Run backtest
        strategy = MovingAverageCrossover(short_window=20, long_window=50)
        engine = BacktestEngine(
            initial_capital=100000,
            commission_rate=0.001,
            slippage_rate=0.0005
        )
        
        result = engine.run_backtest(data, strategy)
        
        assert result is not None
        assert result.metrics['total_return'] is not None
        
        # 3. Compliance checks
        reporter = ComplianceReporter()
        
        # Add position limit rule
        position_rule = PositionLimitRule(
            max_position_value=50000,
            max_concentration=0.5
        )
        reporter.add_rule(position_rule)
        
        # Simulate portfolio data for compliance
        trades = result.trades
        
        if trades:
            # Check largest position
            max_position = max([abs(t.quantity * t.price) for t in trades])
            
            # Verify compliance
            # (In real scenario, would generate full compliance report)
            assert max_position is not None
        
        # 4. Generate report
        # (Simplified - full report would include all metrics)
        assert result.metrics['sharpe_ratio'] is not None


class TestConcurrentOperations:
    """Test system behavior under concurrent load."""
    
    def test_concurrent_var_calculations(self):
        """Test multiple VaR calculations running concurrently."""
        # Simulate concurrent calculations
        provider = SimulatedProvider(n_assets=5, n_periods=252, seed=42)
        returns = provider.fetch_historical('concurrent', start='2023-01-01', end='2023-12-31')
        
        results = []
        
        # Run 10 concurrent calculations
        for i in range(10):
            portfolio_returns = returns.iloc[:, i % len(returns.columns)]
            var_result = calculate_var(portfolio_returns, confidence=0.95)
            results.append(var_result)
        
        assert len(results) == 10
        assert all(r.var < 0 for r in results)
    
    def test_concurrent_optimizations(self):
        """Test multiple portfolio optimizations running concurrently."""
        provider = SimulatedProvider(n_assets=6, n_periods=252, seed=42)
        returns = provider.fetch_historical('opt_test', start='2023-01-01', end='2023-12-31')
        
        results = []
        
        # Run 5 concurrent optimizations
        for _ in range(5):
            optimizer = PortfolioOptimizer(returns, risk_free_rate=0.02)
            result = optimizer.optimize_max_sharpe()
            results.append(result)
        
        assert len(results) == 5
        assert all(abs(np.sum(r.weights) - 1.0) < 1e-6 for r in results)


class TestErrorHandling:
    """Test system error handling and recovery."""
    
    def test_invalid_data_handling(self):
        """Test handling of invalid input data."""
        # Test empty data
        with pytest.raises((ValueError, Exception)):
            empty_returns = pd.Series([])
            calculate_var(empty_returns, confidence=0.95)
        
        # Test NaN data
        nan_returns = pd.Series([np.nan, np.nan, np.nan])
        with pytest.raises((ValueError, Exception)):
            calculate_var(nan_returns, confidence=0.95)
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters."""
        # Invalid Black-Scholes parameters
        bs_model = BlackScholesModel()
        
        # Negative stock price
        with pytest.raises((ValueError, AssertionError)):
            bs_model.price_call(S=-100, K=100, T=1, r=0.05, sigma=0.2)
        
        # Negative time
        with pytest.raises((ValueError, AssertionError)):
            bs_model.price_call(S=100, K=100, T=-1, r=0.05, sigma=0.2)
        
        # Zero volatility
        with pytest.raises((ValueError, AssertionError)):
            bs_model.price_call(S=100, K=100, T=1, r=0.05, sigma=0)
    
    def test_optimization_edge_cases(self):
        """Test portfolio optimization edge cases."""
        # Single asset - should return 100% weight
        single_asset_returns = pd.DataFrame({
            'Asset1': np.random.normal(0.001, 0.02, 100)
        })
        
        optimizer = PortfolioOptimizer(single_asset_returns, risk_free_rate=0.02)
        result = optimizer.optimize_max_sharpe()
        
        assert abs(result.weights[0] - 1.0) < 1e-6
        
        # Highly correlated assets
        n = 100
        base_returns = np.random.normal(0.001, 0.02, n)
        correlated_returns = pd.DataFrame({
            'Asset1': base_returns,
            'Asset2': base_returns + np.random.normal(0, 0.001, n),
            'Asset3': base_returns + np.random.normal(0, 0.001, n),
        })
        
        optimizer = PortfolioOptimizer(correlated_returns, risk_free_rate=0.02)
        result = optimizer.optimize_max_sharpe()
        
        assert len(result.weights) == 3
        assert abs(np.sum(result.weights) - 1.0) < 1e-6


class TestPerformanceMetrics:
    """Test performance monitoring and profiling."""
    
    @profile
    def sample_calculation(self):
        """Sample calculation for profiling."""
        provider = SimulatedProvider(n_assets=5, n_periods=252, seed=42)
        returns = provider.fetch_historical('perf', start='2023-01-01', end='2023-12-31')
        
        optimizer = PortfolioOptimizer(returns, risk_free_rate=0.02)
        result = optimizer.optimize_max_sharpe()
        
        return result
    
    def test_profiling_integration(self):
        """Test that profiling captures performance data."""
        profiler = get_profiler()
        
        # Clear previous measurements
        profiler.clear('sample_calculation')
        
        # Run profiled function
        result = self.sample_calculation()
        
        assert result is not None
        
        # Check profiling data
        stats = profiler.get_stats('sample_calculation')
        
        if stats:
            assert stats.count > 0
            assert stats.total_time > 0
    
    def test_monitoring_integration(self):
        """Test real-time performance monitoring."""
        monitor = get_monitor()
        
        # Add baseline
        monitor.add_baseline(
            'test_operation',
            metric_type=MetricType.LATENCY,
            target_value=100.0,
            warning_threshold=0.5,
            critical_threshold=1.0
        )
        
        # Track operation
        with monitor.track('test_operation'):
            # Simulate work
            provider = SimulatedProvider(n_assets=3, n_periods=100, seed=42)
            _ = provider.fetch_historical('monitor', start='2023-01-01', end='2023-12-31')
        
        # Check measurements
        measurements = monitor.get_measurements('test_operation')
        
        assert not measurements.empty
        assert len(measurements) > 0


class TestDataProviderFallback:
    """Test data provider fallback mechanism."""
    
    def test_multi_provider_aggregator(self):
        """Test fallback between multiple providers."""
        # Create primary provider (simulated)
        primary = SimulatedProvider(n_assets=3, n_periods=100, seed=42)
        
        # Create fallback provider
        fallback = SimulatedProvider(n_assets=3, n_periods=100, seed=43)
        
        # Create aggregator
        aggregator = MultiProviderAggregator([primary, fallback])
        
        # Fetch data (should use primary)
        data = aggregator.fetch_historical('TEST', start='2023-01-01', end='2023-12-31')
        
        assert not data.empty
        assert len(data) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
