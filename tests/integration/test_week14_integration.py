"""
Integration tests for Week 14 features.

Tests cross-module integration:
- Backtesting with data providers
- Compliance reporting with audit trail
- Policy engine with approval workflow
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

# Backtesting and data
from quantlib_pro.execution.backtesting import (
    BacktestEngine,
    MovingAverageCrossover,
    MomentumStrategy,
)
from quantlib_pro.data.providers import (
    DataProviderFactory,
    SimulatedProvider,
)

# Compliance
from quantlib_pro.compliance.reporting import (
    ComplianceReporter,
    RiskLimitRule,
    PositionLimitRule,
)
from quantlib_pro.compliance.audit_trail import AuditTrail

# Governance
from quantlib_pro.governance.policies import (
    PolicyEngine,
    RiskLimitPolicy,
    TradingRestrictionPolicy,
)


def test_backtesting_with_simulated_data():
    """Test backtesting framework with simulated data provider."""
    # Create simulated data provider
    provider = DataProviderFactory.create('simulated', seed=42)
    
    # Fetch historical data
    data = provider.fetch_historical(
        symbol='TEST',
        start_date='2023-01-01',
        end_date='2023-12-31',
        interval='1d'
    )
    
    assert not data.empty
    assert 'Close' in data.columns
    assert len(data) > 200  # Should have ~252 trading days
    
    # Create backtest engine
    engine = BacktestEngine(
        data=data,
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005,
    )
    
    # Test with MA crossover strategy
    strategy = MovingAverageCrossover(short_window=20, long_window=50)
    results = engine.run(strategy)
    
    # Verify results
    assert results.strategy_name == "MA Crossover (20/50)"
    assert results.total_trades >= 0
    assert len(results.equity_curve) == len(data)
    assert results.sharpe_ratio is not None
    
    print(results.summary())


def test_backtesting_with_momentum_strategy():
    """Test momentum strategy backtesting."""
    # Create simulated data
    provider = SimulatedProvider(config={'seed': 123})
    data = provider.fetch_historical('MOMENTUM_TEST', '2023-01-01', '2023-12-31')
    
    # Create backtest engine
    engine = BacktestEngine(data=data, initial_capital=100000)
    
    # Test momentum strategy
    strategy = MomentumStrategy(period=14, oversold=30, overbought=70)
    results = engine.run(strategy)
    
    # Verify
    assert results.total_trades >= 0
    assert -1.0 <= results.total_return <= 5.0  # Reasonable return range
    assert 0 <= results.win_rate <= 1.0
    
    print(f"Total Return: {results.total_return:.2%}")
    print(f"Win Rate: {results.win_rate:.2%}")
    print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")


def test_compliance_with_audit_trail():
    """Test compliance reporting integrated with audit trail."""
    # Create audit trail
    audit = AuditTrail()
    
    # Log some events
    audit.log_event('user1', 'login', 'User logged in', severity='info')
    audit.log_data_access('user1', 'portfolio_data', 'READ')
    audit.log_trade('user1', 'AAPL', 'BUY', 100, 150.00)
    audit.log_trade('user1', 'TSLA', 'SELL', 50, 250.00)
    
    # Create compliance reporter
    reporter = ComplianceReporter()
    
    # Prepare portfolio data
    portfolio_data = {
        'var': 0.03,
        'volatility': 0.20,
        'max_drawdown': -0.15,
        'largest_position': 500000,
        'max_concentration': 0.20,
        'num_positions': 10,
    }
    
    # Prepare transactions
    transactions = [
        {'trade_id': 'T001', 'value': 15000, 'cost_bps': 25},
        {'trade_id': 'T002', 'value': 12500, 'cost_bps': 30},
    ]
    
    # Generate compliance report
    report = reporter.generate_daily_report(portfolio_data, transactions)
    
    # Verify
    assert report.report_type == 'DAILY'
    assert report.is_compliant  # Should pass with these values
    assert len(report.violations) == 0
    
    # Verify audit trail
    events = audit.query_events(user_id='user1')
    assert len(events) == 4  # login + data access + 2 trades
    
    # Verify integrity
    integrity = audit.verify_integrity()
    assert integrity['tampered'] == 0
    assert integrity['integrity_rate'] == 1.0
    
    print(report.summary())


def test_policy_engine_with_approval_workflow():
    """Test policy engine integrated with approval workflow."""
    # Create policy engine
    engine = PolicyEngine()
    
    # Add policies
    risk_policy = RiskLimitPolicy(
        max_var=0.05,
        max_volatility=0.30,
        max_drawdown=0.20,
        max_leverage=2.0,
    )
    
    trading_policy = TradingRestrictionPolicy(
        blacklisted_symbols=['FRAUD_STOCK'],
        min_trade_value=1000,
    )
    
    engine.add_policy(risk_policy)
    engine.add_policy(trading_policy)
    
    # Test 1: Compliant trade
    compliant_trade = {
        'symbol': 'AAPL',
        'trade_value': 10000,
        'var': 0.03,
        'volatility': 0.20,
        'max_drawdown': -0.10,
        'leverage': 1.5,
    }
    
    result = engine.evaluate_trade(compliant_trade)
    assert result.approved
    print(f"Compliant trade: {result}")
    
    # Test 2: Non-compliant trade (blacklisted symbol)
    blacklisted_trade = {
        'symbol': 'FRAUD_STOCK',
        'trade_value': 10000,
        'var': 0.03,
        'volatility': 0.20,
    }
    
    result = engine.evaluate_trade(blacklisted_trade)
    assert not result.approved
    assert 'blacklisted' in result.rejection_reason.lower()
    print(f"Blacklisted trade: {result}")
    
    # Test 3: Non-compliant trade (excessive risk)
    risky_trade = {
        'symbol': 'RISKY',
        'trade_value': 10000,
        'var': 0.08,  # Exceeds limit
        'volatility': 0.20,
    }
    
    result = engine.evaluate_trade(risky_trade)
    assert not result.approved
    assert 'VaR' in result.rejection_reason
    print(f"Risky trade: {result}")
    
    # Test approval workflow
    request = engine.workflow.submit_request(
        requestor='trader1',
        request_type='HIGH_RISK_TRADE',
        description='Requesting approval for high VaR trade',
        data=risky_trade,
    )
    
    assert request.status.value == 'pending'
    
    # Approve the request
    engine.workflow.process_request(
        request_id=request.request_id,
        approver='risk_manager',
        action='approve',
        notes='Approved due to special circumstances',
    )
    
    assert request.status.value == 'approved'
    assert request.approver == 'risk_manager'


def test_full_workflow_integration():
    """Test full workflow: data -> backtest -> compliance -> governance."""
    # 1. Get data
    provider = DataProviderFactory.create('simulated', seed=42)
    data = provider.fetch_historical('FULL_TEST', '2023-01-01', '2023-12-31')
    
    # 2. Run backtest
    engine = BacktestEngine(data=data, initial_capital=100000)
    strategy = MovingAverageCrossover(short_window=10, long_window=30)
    backtest_results = engine.run(strategy)
    
    # 3. Create audit trail
    audit = AuditTrail()
    audit.log_event('system', 'backtesting', f'Executed backtest: {strategy.name}')
    
    # Log trades from backtest
    for trade in backtest_results.trades[:5]:  # Log first 5 trades
        audit.log_trade(
            user_id='backtest_system',
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price,
        )
    
    # 4. Compliance check
    portfolio_data = {
        'var': abs(backtest_results.var_95),
        'volatility': backtest_results.volatility,
        'max_drawdown': abs(backtest_results.max_drawdown),
    }
    
    reporter = ComplianceReporter()
    compliance_report = reporter.generate_daily_report(portfolio_data, [])
    
    # 5. Policy evaluation
    policy_engine = PolicyEngine()
    policy_engine.add_policy(RiskLimitPolicy(
        max_var=0.10,
        max_volatility=0.40,
        max_drawdown=0.30,
    ))
    
    policy_result = policy_engine.evaluate_trade(portfolio_data)
    
    # Verify all components
    print("\n" + "=" * 60)
    print("FULL WORKFLOW INTEGRATION TEST")
    print("=" * 60)
    
    print(f"\n1. DATA: Fetched {len(data)} bars")
    
    print(f"\n2. BACKTEST:")
    print(f"   Strategy: {backtest_results.strategy_name}")
    print(f"   Total Return: {backtest_results.total_return:.2%}")
    print(f"   Sharpe Ratio: {backtest_results.sharpe_ratio:.2f}")
    print(f"   Total Trades: {backtest_results.total_trades}")
    
    print(f"\n3. AUDIT:")
    print(f"   Total Events: {len(audit.events)}")
    print(f"   Integrity: {audit.verify_integrity()['integrity_rate']:.0%}")
    
    print(f"\n4. COMPLIANCE:")
    print(f"   Status: {'✓ COMPLIANT' if compliance_report.is_compliant else '✗ NON-COMPLIANT'}")
    print(f"   Violations: {len(compliance_report.violations)}")
    
    print(f"\n5. GOVERNANCE:")
    print(f"   Policy Result: {'✓ APPROVED' if policy_result.approved else '✗ REJECTED'}")
    print(f"   Warnings: {len(policy_result.warnings)}")
    
    assert len(data) > 0
    assert backtest_results.total_trades >= 0
    assert len(audit.events) > 0
    assert policy_result is not None


if __name__ == '__main__':
    # Run tests
    test_backtesting_with_simulated_data()
    test_backtesting_with_momentum_strategy()
    test_compliance_with_audit_trail()
    test_policy_engine_with_approval_workflow()
    test_full_workflow_integration()
    
    print("\n✓ All integration tests passed!")
