"""
Load Testing Framework for QuantLib Pro

Simulates concurrent users and measures system performance under load.

Features:
- Concurrent user simulation (50+ users)
- Request rate control
- Performance metric collection
- Bottleneck identification
- Load test scenarios

Example
-------
>>> from quantlib_pro.testing.load_testing import LoadTester, Scenario
>>>
>>> tester = LoadTester(base_url='http://localhost:8000')
>>> scenario = Scenario(name='Portfolio Optimization', endpoint='/api/portfolio/optimize')
>>> results = tester.run_load_test(scenario, users=50, duration=60)
>>> print(results.summary())
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class LoadPattern(Enum):
    """Load test patterns."""
    CONSTANT = 'constant'  # Constant user count
    RAMP_UP = 'ramp_up'  # Gradually increase users
    SPIKE = 'spike'  # Sudden traffic spike
    WAVE = 'wave'  # Oscillating load


@dataclass
class Request:
    """Single request in load test."""
    scenario_name: str
    start_time: float
    end_time: float
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    response_size: int = 0
    
    @property
    def duration(self) -> float:
        """Request duration in milliseconds."""
        return (self.end_time - self.start_time) * 1000


@dataclass
class LoadTestResult:
    """Load test results."""
    scenario_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    response_times: List[float]
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        return (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
    
    @property
    def mean_response_time(self) -> float:
        """Mean response time in milliseconds."""
        return np.mean(self.response_times) if self.response_times else 0
    
    @property
    def median_response_time(self) -> float:
        """Median response time in milliseconds."""
        return np.median(self.response_times) if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        """95th percentile response time in milliseconds."""
        return np.percentile(self.response_times, 95) if self.response_times else 0
    
    @property
    def p99_response_time(self) -> float:
        """99th percentile response time in milliseconds."""
        return np.percentile(self.response_times, 99) if self.response_times else 0
    
    def summary(self) -> str:
        """Generate summary report."""
        return f"""
Load Test Results: {self.scenario_name}
{'=' * 70}
Total Requests:        {self.total_requests:,}
Successful:            {self.successful_requests:,} ({self.success_rate:.1f}%)
Failed:                {self.failed_requests:,}
Duration:              {self.duration_seconds:.2f}s
Throughput:            {self.requests_per_second:.2f} req/s

Response Times (ms):
  Mean:                {self.mean_response_time:.2f}
  Median:              {self.median_response_time:.2f}
  95th Percentile:     {self.p95_response_time:.2f}
  99th Percentile:     {self.p99_response_time:.2f}
  Min:                 {min(self.response_times) if self.response_times else 0:.2f}
  Max:                 {max(self.response_times) if self.response_times else 0:.2f}

Status:                {'✅ PASS' if self.success_rate > 95 and self.p95_response_time < 1000 else '❌ FAIL'}
"""


@dataclass
class LoadTestScenario:
    """Load test scenario definition."""
    name: str
    test_function: Callable
    weight: float = 1.0  # Probability weight
    think_time: float = 0.0  # Seconds between requests


class LoadTester:
    """
    Load testing framework.
    
    Simulates concurrent users executing scenarios and measures performance.
    
    Parameters
    ----------
    max_workers : int
        Maximum concurrent users
    ramp_up_time : float
        Time to ramp up to max users (seconds)
    
    Example
    -------
    >>> def portfolio_optimization():
    >>>     # Your test logic here
    >>>     time.sleep(0.1)  # Simulate work
    >>>     return True
    >>>
    >>> tester = LoadTester()
    >>> scenario = LoadTestScenario('Portfolio Opt', portfolio_optimization)
    >>> results = tester.run_load_test([scenario], users=50, duration=60)
    """
    
    def __init__(
        self,
        max_workers: int = 100,
        ramp_up_time: float = 10.0,
    ):
        self.max_workers = max_workers
        self.ramp_up_time = ramp_up_time
        self.requests: List[Request] = []
        
        log.info(f"Initialized LoadTester: max_workers={max_workers}")
    
    def run_load_test(
        self,
        scenarios: List[LoadTestScenario],
        users: int = 50,
        duration: float = 60.0,
        pattern: LoadPattern = LoadPattern.RAMP_UP,
    ) -> Dict[str, LoadTestResult]:
        """
        Run load test with specified scenarios.
        
        Parameters
        ----------
        scenarios : list of LoadTestScenario
            Test scenarios to execute
        users : int
            Number of concurrent users
        duration : float
            Test duration in seconds
        pattern : LoadPattern
            Load pattern
        
        Returns
        -------
        dict
            Results for each scenario
        """
        log.info(f"Starting load test: {users} users, {duration}s, pattern={pattern.value}")
        
        self.requests = []
        start_time = time.time()
        end_time = start_time + duration
        
        # Calculate user schedule based on pattern
        user_schedule = self._generate_user_schedule(users, duration, pattern)
        
        # Execute load test
        with ThreadPoolExecutor(max_workers=min(users, self.max_workers)) as executor:
            futures = []
            
            for user_id, spawn_time in enumerate(user_schedule):
                # Wait until spawn time
                wait_time = spawn_time - (time.time() - start_time)
                if wait_time > 0:
                    time.sleep(wait_time)
                
                # Submit user task
                future = executor.submit(
                    self._user_session,
                    user_id,
                    scenarios,
                    end_time
                )
                futures.append(future)
            
            # Wait for all users to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    log.error(f"User session error: {e}")
        
        # Process results
        actual_duration = time.time() - start_time
        
        return self._generate_results(scenarios, actual_duration)
    
    def _generate_user_schedule(
        self,
        users: int,
        duration: float,
        pattern: LoadPattern,
    ) -> List[float]:
        """Generate user spawn schedule based on load pattern."""
        if pattern == LoadPattern.CONSTANT:
            # Spawn all users immediately
            return [0.0] * users
        
        elif pattern == LoadPattern.RAMP_UP:
            # Linear ramp up
            ramp_duration = min(self.ramp_up_time, duration / 2)
            return [i * ramp_duration / users for i in range(users)]
        
        elif pattern == LoadPattern.SPIKE:
            # Spawn half at start, spike rest at midpoint
            half = users // 2
            return ([0.0] * half) + ([duration / 2] * (users - half))
        
        elif pattern == LoadPattern.WAVE:
            # Sinusoidal spawn pattern
            return [
                abs(np.sin(2 * np.pi * i / users)) * duration / 2
                for i in range(users)
            ]
        
        return [0.0] * users
    
    def _user_session(
        self,
        user_id: int,
        scenarios: List[LoadTestScenario],
        end_time: float,
    ) -> None:
        """Simulate single user session."""
        # Calculate scenario probabilities
        total_weight = sum(s.weight for s in scenarios)
        probabilities = [s.weight / total_weight for s in scenarios]
        
        while time.time() < end_time:
            # Select scenario based on weights
            scenario = np.random.choice(scenarios, p=probabilities)
            
            # Execute request
            request = self._execute_request(scenario)
            self.requests.append(request)
            
            # Think time
            if scenario.think_time > 0:
                time.sleep(scenario.think_time)
    
    def _execute_request(self, scenario: LoadTestScenario) -> Request:
        """Execute single request."""
        start_time = time.time()
        success = False
        error = None
        
        try:
            # Execute test function
            result = scenario.test_function()
            success = bool(result)
        
        except Exception as e:
            error = str(e)
            log.debug(f"Request failed: {e}")
        
        end_time = time.time()
        
        return Request(
            scenario_name=scenario.name,
            start_time=start_time,
            end_time=end_time,
            success=success,
            error=error,
        )
    
    def _generate_results(
        self,
        scenarios: List[LoadTestScenario],
        duration: float,
    ) -> Dict[str, LoadTestResult]:
        """Generate results for each scenario."""
        results = {}
        
        for scenario in scenarios:
            # Filter requests for this scenario
            scenario_requests = [
                r for r in self.requests
                if r.scenario_name == scenario.name
            ]
            
            total = len(scenario_requests)
            successful = sum(1 for r in scenario_requests if r.success)
            failed = total - successful
            
            response_times = [r.duration for r in scenario_requests]
            errors = [r.error for r in scenario_requests if r.error]
            
            rps = total / duration if duration > 0 else 0
            
            results[scenario.name] = LoadTestResult(
                scenario_name=scenario.name,
                total_requests=total,
                successful_requests=successful,
                failed_requests=failed,
                duration_seconds=duration,
                requests_per_second=rps,
                response_times=response_times,
                errors=errors[:10],  # Keep first 10 errors
            )
        
        return results
    
    def generate_report(self, results: Dict[str, LoadTestResult]) -> pd.DataFrame:
        """Generate DataFrame report."""
        data = []
        
        for name, result in results.items():
            data.append({
                'Scenario': name,
                'Total Requests': result.total_requests,
                'Success Rate (%)': result.success_rate,
                'RPS': result.requests_per_second,
                'Mean (ms)': result.mean_response_time,
                'Median (ms)': result.median_response_time,
                'P95 (ms)': result.p95_response_time,
                'P99 (ms)': result.p99_response_time,
            })
        
        return pd.DataFrame(data)


class PerformanceBenchmark:
    """
    Performance benchmarking suite.
    
    Defines performance targets and validates against them.
    """
    
    def __init__(self):
        self.benchmarks: Dict[str, Dict[str, float]] = {
            'portfolio_optimization': {
                'max_p95_ms': 500,  # 95th percentile < 500ms
                'max_p99_ms': 1000,  # 99th percentile < 1s
                'min_rps': 10,  # At least 10 req/s
                'min_success_rate': 99.0,  # 99% success
            },
            'var_calculation': {
                'max_p95_ms': 100,
                'max_p99_ms': 200,
                'min_rps': 50,
                'min_success_rate': 99.5,
            },
            'options_pricing': {
                'max_p95_ms': 50,
                'max_p99_ms': 100,
                'min_rps': 100,
                'min_success_rate': 99.9,
            },
            'regime_detection': {
                'max_p95_ms': 200,
                'max_p99_ms': 500,
                'min_rps': 20,
                'min_success_rate': 98.0,
            },
        }
    
    def validate(
        self,
        scenario_name: str,
        result: LoadTestResult,
    ) -> Dict[str, bool]:
        """
        Validate results against benchmark.
        
        Parameters
        ----------
        scenario_name : str
            Scenario name
        result : LoadTestResult
            Test results
        
        Returns
        -------
        dict
            Validation results for each metric
        """
        if scenario_name not in self.benchmarks:
            log.warning(f"No benchmark defined for {scenario_name}")
            return {}
        
        benchmark = self.benchmarks[scenario_name]
        validation = {}
        
        # Check P95 latency
        if 'max_p95_ms' in benchmark:
            validation['p95_latency'] = result.p95_response_time <= benchmark['max_p95_ms']
        
        # Check P99 latency
        if 'max_p99_ms' in benchmark:
            validation['p99_latency'] = result.p99_response_time <= benchmark['max_p99_ms']
        
        # Check throughput
        if 'min_rps' in benchmark:
            validation['throughput'] = result.requests_per_second >= benchmark['min_rps']
        
        # Check success rate
        if 'min_success_rate' in benchmark:
            validation['success_rate'] = result.success_rate >= benchmark['min_success_rate']
        
        return validation
    
    def generate_validation_report(
        self,
        scenario_name: str,
        result: LoadTestResult,
    ) -> str:
        """Generate validation report."""
        validation = self.validate(scenario_name, result)
        
        if not validation:
            return "No benchmark defined"
        
        lines = [
            f"Benchmark Validation: {scenario_name}",
            "=" * 50,
        ]
        
        benchmark = self.benchmarks[scenario_name]
        
        for metric, passed in validation.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            
            if metric == 'p95_latency':
                lines.append(f"P95 Latency: {result.p95_response_time:.2f}ms / {benchmark['max_p95_ms']}ms {status}")
            elif metric == 'p99_latency':
                lines.append(f"P99 Latency: {result.p99_response_time:.2f}ms / {benchmark['max_p99_ms']}ms {status}")
            elif metric == 'throughput':
                lines.append(f"Throughput: {result.requests_per_second:.2f} / {benchmark['min_rps']} req/s {status}")
            elif metric == 'success_rate':
                lines.append(f"Success Rate: {result.success_rate:.1f}% / {benchmark['min_success_rate']}% {status}")
        
        overall = "✅ ALL PASSED" if all(validation.values()) else "❌ SOME FAILED"
        lines.append(f"\nOverall: {overall}")
        
        return '\n'.join(lines)
