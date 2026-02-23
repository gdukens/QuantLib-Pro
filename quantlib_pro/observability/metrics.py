"""
Metrics collection and Prometheus integration.

Provides:
  - Counter, Gauge, Histogram, Summary metrics
  - Custom business metrics (trades, calculations, errors)
  - Prometheus exposition
  - Metric labels and aggregation
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

log = logging.getLogger(__name__)


# === Global Registry ===

# Custom registry to avoid conflicts with default
METRICS_REGISTRY = CollectorRegistry()


# === Core Business Metrics ===

# Calculation counters
calculations_total = Counter(
    'quantlib_calculations_total',
    'Total number of calculations performed',
    ['calculation_type', 'status'],
    registry=METRICS_REGISTRY,
)

calculation_duration = Histogram(
    'quantlib_calculation_duration_seconds',
    'Calculation duration in seconds',
    ['calculation_type'],
    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0],
    registry=METRICS_REGISTRY,
)

# Portfolio metrics
portfolio_value = Gauge(
    'quantlib_portfolio_value_usd',
    'Current portfolio value in USD',
    ['portfolio_id'],
    registry=METRICS_REGISTRY,
)

portfolio_var = Gauge(
    'quantlib_portfolio_var_usd',
    'Portfolio Value-at-Risk in USD',
    ['portfolio_id', 'confidence'],
    registry=METRICS_REGISTRY,
)

# Trade metrics
trades_executed = Counter(
    'quantlib_trades_executed_total',
    'Total number of trades executed',
    ['asset_class', 'side'],
    registry=METRICS_REGISTRY,
)

trade_slippage = Summary(
    'quantlib_trade_slippage_bps',
    'Trade slippage in basis points',
    ['asset_class'],
    registry=METRICS_REGISTRY,
)

# Data quality metrics
data_quality_score = Gauge(
    'quantlib_data_quality_score',
    'Data quality score [0, 1]',
    ['source', 'asset'],
    registry=METRICS_REGISTRY,
)

missing_data_points = Counter(
    'quantlib_missing_data_points_total',
    'Total missing data points detected',
    ['source', 'asset'],
    registry=METRICS_REGISTRY,
)

# Cache metrics
cache_hits = Counter(
    'quantlib_cache_hits_total',
    'Total cache hits',
    ['cache_name'],
    registry=METRICS_REGISTRY,
)

cache_misses = Counter(
    'quantlib_cache_misses_total',
    'Total cache misses',
    ['cache_name'],
    registry=METRICS_REGISTRY,
)

# Error metrics
errors_total = Counter(
    'quantlib_errors_total',
    'Total errors encountered',
    ['error_type', 'module'],
    registry=METRICS_REGISTRY,
)

# API metrics
api_requests = Counter(
    'quantlib_api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status'],
    registry=METRICS_REGISTRY,
)

api_latency = Histogram(
    'quantlib_api_latency_seconds',
    'API request latency',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=METRICS_REGISTRY,
)


# === Metric Helpers ===

@contextmanager
def track_calculation(calc_type: str):
    """
    Context manager to track calculation metrics.
    
    Usage:
        with track_calculation('black_scholes'):
            result = price_option(...)
    """
    start = time.perf_counter()
    status = 'success'
    
    try:
        yield
    except Exception as e:
        status = 'error'
        errors_total.labels(error_type=type(e).__name__, module='calculation').inc()
        raise
    finally:
        duration = time.perf_counter() - start
        calculations_total.labels(calculation_type=calc_type, status=status).inc()
        calculation_duration.labels(calculation_type=calc_type).observe(duration)


@contextmanager
def track_api_request(endpoint: str, method: str = 'GET'):
    """
    Context manager to track API request metrics.
    
    Usage:
        with track_api_request('/api/portfolio', 'GET'):
            response = handle_request()
    """
    start = time.perf_counter()
    status = '200'
    
    try:
        yield
    except Exception as e:
        status = '500'
        errors_total.labels(error_type=type(e).__name__, module='api').inc()
        raise
    finally:
        duration = time.perf_counter() - start
        api_requests.labels(endpoint=endpoint, method=method, status=status).inc()
        api_latency.labels(endpoint=endpoint).observe(duration)


def record_trade(asset_class: str, side: str, slippage_bps: float):
    """
    Record trade execution metrics.
    
    Parameters
    ----------
    asset_class : str
        Asset class ('equity', 'bond', 'option', etc.)
    side : str
        Trade side ('buy' or 'sell')
    slippage_bps : float
        Slippage in basis points
    """
    trades_executed.labels(asset_class=asset_class, side=side).inc()
    trade_slippage.labels(asset_class=asset_class).observe(slippage_bps)


def record_cache_access(cache_name: str, hit: bool):
    """
    Record cache access.
    
    Parameters
    ----------
    cache_name : str
        Name of cache
    hit : bool
        True if cache hit, False if miss
    """
    if hit:
        cache_hits.labels(cache_name=cache_name).inc()
    else:
        cache_misses.labels(cache_name=cache_name).inc()


def update_portfolio_metrics(portfolio_id: str, value: float, var_95: float, var_99: float):
    """
    Update portfolio metrics.
    
    Parameters
    ----------
    portfolio_id : str
        Portfolio identifier
    value : float
        Portfolio value (USD)
    var_95 : float
        95% VaR (USD)
    var_99 : float
        99% VaR (USD)
    """
    portfolio_value.labels(portfolio_id=portfolio_id).set(value)
    portfolio_var.labels(portfolio_id=portfolio_id, confidence='95').set(var_95)
    portfolio_var.labels(portfolio_id=portfolio_id, confidence='99').set(var_99)


def record_data_quality(source: str, asset: str, quality_score: float, missing_count: int = 0):
    """
    Record data quality metrics.
    
    Parameters
    ----------
    source : str
        Data source
    asset : str
        Asset identifier
    quality_score : float
        Quality score [0, 1]
    missing_count : int
        Number of missing data points
    """
    data_quality_score.labels(source=source, asset=asset).set(quality_score)
    
    if missing_count > 0:
        missing_data_points.labels(source=source, asset=asset).inc(missing_count)


def export_metrics() -> tuple[bytes, str]:
    """
    Export metrics in Prometheus format.
    
    Returns
    -------
    tuple[bytes, str]
        (metrics_data, content_type)
    """
    return generate_latest(METRICS_REGISTRY), CONTENT_TYPE_LATEST


@dataclass
class MetricSnapshot:
    """Snapshot of current metrics."""
    timestamp: float
    calculations_total: int = 0
    trades_total: int = 0
    errors_total: int = 0
    cache_hit_rate: float = 0.0
    avg_calculation_duration: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'calculations_total': self.calculations_total,
            'trades_total': self.trades_total,
            'errors_total': self.errors_total,
            'cache_hit_rate': self.cache_hit_rate,
            'avg_calculation_duration': self.avg_calculation_duration,
        }


def get_metrics_snapshot() -> MetricSnapshot:
    """
    Get current metrics snapshot.
    
    Returns
    -------
    MetricSnapshot
        Current metrics
    """
    # This is a simplified snapshot - in production would query actual metrics
    return MetricSnapshot(
        timestamp=time.time(),
        calculations_total=0,
        trades_total=0,
        errors_total=0,
        cache_hit_rate=0.0,
        avg_calculation_duration=0.0,
    )


# === Custom Metric Decorator ===

def measure_time(metric_name: str, labels: Optional[dict[str, str]] = None):
    """
    Decorator to measure function execution time.
    
    Usage:
        @measure_time('my_function', labels={'module': 'portfolio'})
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                log.debug(f"{metric_name} took {duration:.4f}s")
                # Could also record to a metric here
        return wrapper
    return decorator
