"""
Performance monitoring and profiling.

Provides:
  - Function execution timing
  - Performance profiling
  - Slow query detection
  - Resource usage tracking
  - Performance reports
"""

from __future__ import annotations

import functools
import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a function or operation."""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    errors: int = 0
    
    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0
    
    def record(self, duration: float, error: bool = False):
        """
        Record a new measurement.
        
        Parameters
        ----------
        duration : float
            Execution duration (seconds)
        error : bool
            Whether an error occurred
        """
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        
        if error:
            self.errors += 1
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'call_count': self.call_count,
            'total_time': self.total_time,
            'avg_time': self.avg_time,
            'min_time': self.min_time if self.min_time != float('inf') else 0.0,
            'max_time': self.max_time,
            'errors': self.errors,
        }


class PerformanceMonitor:
    """Global performance monitor."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self._metrics: dict[str, PerformanceMetrics] = defaultdict(
            lambda: PerformanceMetrics(name="unknown")
        )
        self._slow_threshold: float = 1.0  # seconds
        self._slow_operations: list[dict] = []
    
    def record(self, name: str, duration: float, error: bool = False):
        """
        Record performance metric.
        
        Parameters
        ----------
        name : str
            Operation name
        duration : float
            Duration (seconds)
        error : bool
            Whether an error occurred
        """
        if name not in self._metrics:
            self._metrics[name] = PerformanceMetrics(name=name)
        
        self._metrics[name].record(duration, error)
        
        # Track slow operations
        if duration > self._slow_threshold:
            self._slow_operations.append({
                'name': name,
                'duration': duration,
                'timestamp': time.time(),
            })
            
            # Keep only last 100 slow operations
            if len(self._slow_operations) > 100:
                self._slow_operations = self._slow_operations[-100:]
            
            log.warning(f"Slow operation detected: {name} took {duration:.3f}s")
    
    def get_metrics(self, name: Optional[str] = None) -> dict[str, PerformanceMetrics] | PerformanceMetrics:
        """
        Get performance metrics.
        
        Parameters
        ----------
        name : str, optional
            Specific metric name, or None for all metrics
        
        Returns
        -------
        dict or PerformanceMetrics
            Requested metrics
        """
        if name is not None:
            return self._metrics.get(name, PerformanceMetrics(name=name))
        return dict(self._metrics)
    
    def get_slow_operations(self) -> list[dict]:
        """Get recent slow operations."""
        return self._slow_operations.copy()
    
    def reset(self):
        """Reset all metrics."""
        self._metrics.clear()
        self._slow_operations.clear()
    
    def set_slow_threshold(self, seconds: float):
        """Set slow operation threshold."""
        self._slow_threshold = seconds
    
    def generate_report(self) -> dict[str, Any]:
        """
        Generate performance report.
        
        Returns
        -------
        dict
            Performance report
        """
        sorted_metrics = sorted(
            self._metrics.values(),
            key=lambda m: m.total_time,
            reverse=True
        )
        
        return {
            'total_operations': sum(m.call_count for m in self._metrics.values()),
            'total_time': sum(m.total_time for m in self._metrics.values()),
            'total_errors': sum(m.errors for m in self._metrics.values()),
            'top_time_consumers': [m.to_dict() for m in sorted_metrics[:10]],
            'slow_operations_count': len(self._slow_operations),
            'recent_slow_operations': self._slow_operations[-10:],
        }


# === Global Monitor ===

_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return _performance_monitor


# === Decorators ===

def monitor_performance(name: Optional[str] = None):
    """
    Decorator to monitor function performance.
    
    Usage:
        @monitor_performance('my_function')
        def my_function():
            ...
    
    Parameters
    ----------
    name : str, optional
        Custom name for the operation (default: function name)
    """
    def decorator(func: Callable) -> Callable:
        operation_name = name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            error = False
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                error = True
                raise
            finally:
                duration = time.perf_counter() - start
                _performance_monitor.record(operation_name, duration, error)
        
        return wrapper
    return decorator


@contextmanager
def track_performance(name: str):
    """
    Context manager to track performance.
    
    Usage:
        with track_performance('database_query'):
            results = db.query(...)
    
    Parameters
    ----------
    name : str
        Operation name
    """
    start = time.perf_counter()
    error = False
    
    try:
        yield
    except Exception:
        error = True
        raise
    finally:
        duration = time.perf_counter() - start
        _performance_monitor.record(name, duration, error)


@contextmanager
def profile_section(label: str):
    """
    Context manager to profile a code section.
    
    Logs timing information for the section.
    
    Parameters
    ----------
    label : str
        Section label
    """
    start = time.perf_counter()
    log.debug(f"Starting: {label}")
    
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        log.info(f"Completed: {label} in {duration:.3f}s")


class PerformanceTimer:
    """Manual performance timer."""
    
    def __init__(self, name: str, auto_record: bool = True):
        """
        Initialize timer.
        
        Parameters
        ----------
        name : str
            Timer name
        auto_record : bool
            Automatically record to global monitor on stop
        """
        self.name = name
        self.auto_record = auto_record
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None
    
    def start(self):
        """Start the timer."""
        self.start_time = time.perf_counter()
        return self
    
    def stop(self) -> float:
        """
        Stop the timer.
        
        Returns
        -------
        float
            Duration in seconds
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        self.duration = time.perf_counter() - self.start_time
        
        if self.auto_record:
            _performance_monitor.record(self.name, self.duration)
        
        return self.duration
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def time_function(func: Callable) -> float:
    """
    Time a function call (single execution).
    
    Parameters
    ----------
    func : Callable
        Function to time
    
    Returns
    -------
    float
        Execution time in seconds
    """
    start = time.perf_counter()
    func()
    return time.perf_counter() - start


def benchmark(func: Callable, iterations: int = 100) -> dict[str, float]:
    """
    Benchmark a function over multiple iterations.
    
    Parameters
    ----------
    func : Callable
        Function to benchmark
    iterations : int
        Number of iterations
    
    Returns
    -------
    dict
        Benchmark results (mean, min, max, total)
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append(time.perf_counter() - start)
    
    return {
        'iterations': iterations,
        'mean': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'total': sum(times),
    }
