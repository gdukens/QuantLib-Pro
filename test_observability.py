"""
Week 10: Observability smoke tests.
"""

import time
import pytest

from quantlib_pro.observability import (
    # Metrics
    track_calculation,
    track_api_request,
    record_trade,
    record_cache_access,
    update_portfolio_metrics,
    record_data_quality,
    export_metrics,
    get_metrics_snapshot,
    monitor_performance,
    # Health
    HealthStatus,
    HealthCheckResult,
    SystemHealth,
    HealthChecker,
    register_health_check,
    check_health,
    check_memory,
    check_disk,
    check_cpu,
    liveness_probe,
    readiness_probe,
    # Performance
    PerformanceMetrics,
    get_performance_monitor,
    track_performance,
    profile_section,
    PerformanceTimer,
    time_function,
    benchmark,
)


# === Metrics Tests ===

def test_track_calculation():
    """Test calculation tracking context manager."""
    with track_calculation('test_calc'):
        time.sleep(0.01)
    
    # Should complete without error
    assert True


def test_track_calculation_error():
    """Test calculation tracking with error."""
    try:
        with track_calculation('test_calc_error'):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Should track the error
    assert True


def test_track_api_request():
    """Test API request tracking."""
    with track_api_request('/api/test', 'GET'):
        time.sleep(0.01)
    
    assert True


def test_record_trade():
    """Test trade recording."""
    record_trade(
        asset_class='equity',
        side='buy',
        slippage_bps=2.5,
    )
    
    assert True


def test_record_cache_access():
    """Test cache access recording."""
    record_cache_access('test_cache', hit=True)
    record_cache_access('test_cache', hit=False)
    
    assert True


def test_update_portfolio_metrics():
    """Test portfolio metrics update."""
    update_portfolio_metrics(
        portfolio_id='test_portfolio',
        value=1000000.0,
        var_95=50000.0,
        var_99=75000.0,
    )
    
    assert True


def test_record_data_quality():
    """Test data quality recording."""
    record_data_quality(
        source='test_source',
        asset='TEST',
        quality_score=0.95,
        missing_count=5,
    )
    
    assert True


def test_export_metrics():
    """Test metrics export."""
    data, content_type = export_metrics()
    
    assert isinstance(data, bytes)
    assert 'text/plain' in content_type


def test_get_metrics_snapshot():
    """Test metrics snapshot."""
    snapshot = get_metrics_snapshot()
    
    assert snapshot.timestamp > 0
    assert isinstance(snapshot.to_dict(), dict)


# === Health Tests ===

def test_health_check_result():
    """Test HealthCheckResult."""
    result = HealthCheckResult(
        component='test',
        status=HealthStatus.HEALTHY,
        message='OK',
    )
    
    assert result.is_healthy()
    assert result.component == 'test'
    
    result_dict = result.to_dict()
    assert result_dict['status'] == 'healthy'


def test_health_checker_registration():
    """Test health check registration."""
    checker = HealthChecker()
    
    def test_check() -> HealthCheckResult:
        return HealthCheckResult(
            component='test',
            status=HealthStatus.HEALTHY,
            message='Test OK',
        )
    
    checker.register_check('test', test_check)
    
    result = checker.run_check('test')
    assert result.is_healthy()


def test_health_checker_run_all():
    """Test running all health checks."""
    checker = HealthChecker()
    
    checker.register_check('check1', lambda: HealthCheckResult(
        component='check1',
        status=HealthStatus.HEALTHY,
    ))
    
    checker.register_check('check2', lambda: HealthCheckResult(
        component='check2',
        status=HealthStatus.HEALTHY,
    ))
    
    health = checker.run_all_checks()
    
    assert health.status == HealthStatus.HEALTHY
    assert len(health.checks) == 2


def test_health_checker_degraded():
    """Test degraded health status."""
    checker = HealthChecker()
    
    checker.register_check('healthy', lambda: HealthCheckResult(
        component='healthy',
        status=HealthStatus.HEALTHY,
    ))
    
    checker.register_check('degraded', lambda: HealthCheckResult(
        component='degraded',
        status=HealthStatus.DEGRADED,
    ))
    
    health = checker.run_all_checks()
    
    # Overall should be degraded
    assert health.status == HealthStatus.DEGRADED


def test_check_memory():
    """Test memory health check."""
    result = check_memory()
    
    assert result.component == 'memory'
    assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]


def test_check_disk():
    """Test disk health check."""
    result = check_disk()
    
    assert result.component == 'disk'
    assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]


def test_check_cpu():
    """Test CPU health check."""
    result = check_cpu()
    
    assert result.component == 'cpu'
    assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]


def test_liveness_probe():
    """Test liveness probe."""
    assert liveness_probe() == True


def test_readiness_probe():
    """Test readiness probe."""
    # Should return bool
    result = readiness_probe()
    assert isinstance(result, bool)


def test_system_health_to_dict():
    """Test SystemHealth serialization."""
    health = SystemHealth(
        status=HealthStatus.HEALTHY,
        checks=[
            HealthCheckResult(
                component='test',
                status=HealthStatus.HEALTHY,
            )
        ],
    )
    
    health_dict = health.to_dict()
    assert health_dict['status'] == 'healthy'
    assert len(health_dict['checks']) == 1


# === Performance Tests ===

def test_performance_metrics():
    """Test PerformanceMetrics."""
    metrics = PerformanceMetrics(name='test')
    
    metrics.record(0.1, error=False)
    metrics.record(0.2, error=False)
    metrics.record(0.3, error=True)
    
    assert metrics.call_count == 3
    assert metrics.errors == 1
    assert metrics.avg_time > 0
    assert metrics.min_time == 0.1
    assert metrics.max_time == 0.3


def test_performance_monitor():
    """Test PerformanceMonitor."""
    monitor = get_performance_monitor()
    monitor.reset()
    
    monitor.record('test_op', 0.5)
    monitor.record('test_op', 0.3)
    
    metrics = monitor.get_metrics('test_op')
    assert metrics.call_count == 2


def test_monitor_performance_decorator():
    """Test monitor_performance decorator."""
    @monitor_performance('test_function')
    def slow_function():
        time.sleep(0.01)
        return 42
    
    result = slow_function()
    assert result == 42
    
    # Should have recorded metrics
    monitor = get_performance_monitor()
    metrics = monitor.get_metrics('test_function')
    assert metrics.call_count >= 1


def test_monitor_performance_error():
    """Test monitor_performance with error."""
    @monitor_performance('test_error_function')
    def error_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        error_function()
    
    # Should have recorded error
    monitor = get_performance_monitor()
    metrics = monitor.get_metrics('test_error_function')
    assert metrics.errors >= 1


def test_track_performance_context():
    """Test track_performance context manager."""
    with track_performance('test_operation'):
        time.sleep(0.01)
    
    monitor = get_performance_monitor()
    metrics = monitor.get_metrics('test_operation')
    assert metrics.call_count >= 1


def test_profile_section():
    """Test profile_section context manager."""
    with profile_section('test_section'):
        time.sleep(0.01)
    
    # Should complete without error
    assert True


def test_performance_timer():
    """Test PerformanceTimer."""
    timer = PerformanceTimer('manual_timer', auto_record=False)
    timer.start()
    time.sleep(0.01)
    duration = timer.stop()
    
    assert duration > 0.01


def test_performance_timer_context():
    """Test PerformanceTimer as context manager."""
    with PerformanceTimer('context_timer', auto_record=False) as timer:
        time.sleep(0.01)
    
    assert timer.duration > 0.01


def test_time_function():
    """Test time_function utility."""
    def test_func():
        time.sleep(0.01)
    
    duration = time_function(test_func)
    assert duration > 0.01


def test_benchmark():
    """Test benchmark utility."""
    def test_func():
        x = sum(range(1000))
    
    results = benchmark(test_func, iterations=10)
    
    assert results['iterations'] == 10
    assert results['mean'] > 0
    assert results['min'] > 0
    assert results['max'] >= results['min']


def test_performance_report():
    """Test performance report generation."""
    monitor = get_performance_monitor()
    monitor.reset()
    
    monitor.record('op1', 0.5)
    monitor.record('op2', 0.3)
    monitor.record('op1', 0.4)
    
    report = monitor.generate_report()
    
    assert report['total_operations'] == 3
    assert report['total_time'] > 0
    assert len(report['top_time_consumers']) <= 10


def test_slow_operation_detection():
    """Test slow operation detection."""
    monitor = get_performance_monitor()
    monitor.reset()
    monitor.set_slow_threshold(0.05)
    
    # Normal operation
    monitor.record('fast_op', 0.01)
    
    # Slow operation
    monitor.record('slow_op', 0.1)
    
    slow_ops = monitor.get_slow_operations()
    assert len(slow_ops) >= 1
    assert slow_ops[-1]['name'] == 'slow_op'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
