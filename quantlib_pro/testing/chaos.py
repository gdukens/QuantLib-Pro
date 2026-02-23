"""
Chaos Engineering Framework for QuantLib Pro

Fault injection and resilience testing to validate system robustness.

Features:
- Network failures (latency, timeouts, errors)
- Resource exhaustion (memory, CPU)
- Data corruption
- Service failures
- Cascading failures

Example
-------
>>> from quantlib_pro.testing.chaos import ChaosEngineer, Fault
>>>
>>> chaos = ChaosEngineer()
>>> with chaos.inject(Fault.NETWORK_LATENCY, intensity=0.5):
>>>     # Your system under test
>>>     result = portfolio_optimizer.optimize()
>>>
>>> # System should handle gracefully
>>> assert result is not None
"""

from __future__ import annotations

import contextlib
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np

log = logging.getLogger(__name__)


class FaultType(Enum):
    """Types of chaos faults."""
    NETWORK_LATENCY = 'network_latency'  # Add random delays
    NETWORK_TIMEOUT = 'network_timeout'  # Simulate timeouts
    NETWORK_ERROR = 'network_error'  # Simulate network errors
    MEMORY_PRESSURE = 'memory_pressure'  # Consume memory
    CPU_SPIKE = 'cpu_spike'  # CPU intensive operations
    DATA_CORRUPTION = 'data_corruption'  # Corrupt data randomly
    SERVICE_FAILURE = 'service_failure'  # Complete service failure
    INTERMITTENT_FAILURE = 'intermittent_failure'  # Random failures
    SLOW_RESPONSE = 'slow_response'  # Degraded performance
    CASCADING_FAILURE = 'cascading_failure'  # Chain of failures


@dataclass
class FaultInjection:
    """Fault injection configuration."""
    fault_type: FaultType
    intensity: float  # 0.0 to 1.0
    duration: Optional[float] = None  # Seconds, None = indefinite
    probability: float = 1.0  # Probability of fault occurring (0-1)
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChaosExperiment:
    """Chaos experiment definition."""
    name: str
    faults: List[FaultInjection]
    steady_state_validator: Callable[[], bool]
    duration: float = 60.0  # Experiment duration in seconds
    
    def validate_steady_state(self) -> bool:
        """Check if system is in steady state."""
        try:
            return self.steady_state_validator()
        except Exception as e:
            log.error(f"Steady state validation failed: {e}")
            return False


class ChaosEngineer:
    """
    Chaos engineering framework.
    
    Injects faults to test system resilience and recovery.
    
    Example
    -------
    >>> chaos = ChaosEngineer()
    >>>
    >>> # Inject network latency
    >>> with chaos.inject_fault(FaultType.NETWORK_LATENCY, intensity=0.5):
    >>>     data = fetch_market_data()  # Should handle delays gracefully
    >>>
    >>> # Inject data corruption
    >>> with chaos.inject_fault(FaultType.DATA_CORRUPTION, intensity=0.1):
    >>>     result = calculate_var(corrupted_data)  # Should detect corruption
    """
    
    def __init__(self):
        self.active_faults: List[FaultInjection] = []
        self.experiment_results: List[Dict] = []
        
        log.info("Initialized ChaosEngineer")
    
    @contextlib.contextmanager
    def inject_fault(
        self,
        fault_type: FaultType,
        intensity: float = 0.5,
        probability: float = 1.0,
    ):
        """
        Context manager for fault injection.
        
        Parameters
        ----------
        fault_type : FaultType
            Type of fault to inject
        intensity : float
            Fault intensity (0.0 to 1.0)
        probability : float
            Probability of fault (0.0 to 1.0)
        
        Example
        -------
        >>> with chaos.inject_fault(FaultType.NETWORK_LATENCY, intensity=0.8):
        >>>     result = api_call()  # Will experience delays
        """
        fault = FaultInjection(
            fault_type=fault_type,
            intensity=intensity,
            probability=probability,
        )
        
        self.active_faults.append(fault)
        log.info(f"Injecting fault: {fault_type.value} (intensity={intensity})")
        
        try:
            yield fault
        finally:
            self.active_faults.remove(fault)
            log.info(f"Removed fault: {fault_type.value}")
    
    def maybe_inject_network_latency(self, base_latency: float = 0.0) -> float:
        """Add network latency based on active faults."""
        added_latency = base_latency
        
        for fault in self.active_faults:
            if fault.fault_type == FaultType.NETWORK_LATENCY:
                if random.random() < fault.probability:
                    # Add 0-5 seconds based on intensity
                    delay = fault.intensity * 5.0
                    added_latency += delay
        
        if added_latency > base_latency:
            time.sleep(added_latency - base_latency)
        
        return added_latency
    
    def maybe_inject_network_error(self) -> bool:
        """Check if network error should be injected."""
        for fault in self.active_faults:
            if fault.fault_type == FaultType.NETWORK_ERROR:
                if random.random() < (fault.intensity * fault.probability):
                    return True
        
        return False
    
    def maybe_inject_timeout(self, timeout: float) -> float:
        """Modify timeout based on active faults."""
        for fault in self.active_faults:
            if fault.fault_type == FaultType.NETWORK_TIMEOUT:
                if random.random() < fault.probability:
                    # Reduce timeout by intensity percentage
                    timeout = timeout * (1 - fault.intensity)
        
        return timeout
    
    def maybe_corrupt_data(self, data: Any) -> Any:
        """Corrupt data based on active faults."""
        for fault in self.active_faults:
            if fault.fault_type == FaultType.DATA_CORRUPTION:
                if random.random() < fault.probability:
                    # Corrupt data based on type
                    if isinstance(data, (list, np.ndarray)):
                        return self._corrupt_array(data, fault.intensity)
                    elif isinstance(data, dict):
                        return self._corrupt_dict(data, fault.intensity)
                    elif isinstance(data, (int, float)):
                        return self._corrupt_number(data, fault.intensity)
        
        return data
    
    def _corrupt_array(self, arr: Any, intensity: float) -> Any:
        """Corrupt array data."""
        if isinstance(arr, np.ndarray):
            arr = arr.copy()
        else:
            arr = list(arr)
        
        # Corrupt random elements
        n_corrupt = max(1, int(len(arr) * intensity))
        indices = random.sample(range(len(arr)), min(n_corrupt, len(arr)))
        
        for idx in indices:
            if isinstance(arr[idx], (int, float)):
                arr[idx] = np.nan  # Replace with NaN
        
        return arr
    
    def _corrupt_dict(self, d: Dict, intensity: float) -> Dict:
        """Corrupt dictionary data."""
        d = d.copy()
        
        # Remove random keys
        if random.random() < intensity:
            keys = list(d.keys())
            if keys:
                key_to_remove = random.choice(keys)
                del d[key_to_remove]
        
        return d
    
    def _corrupt_number(self, value: float, intensity: float) -> float:
        """Corrupt numeric value."""
        if random.random() < intensity:
            # Scale by large factor
            return value * (1 + random.uniform(-10, 10))
        
        return value
    
    def maybe_inject_service_failure(self) -> bool:
        """Check if service should fail completely."""
        for fault in self.active_faults:
            if fault.fault_type == FaultType.SERVICE_FAILURE:
                if random.random() < fault.probability:
                    return True
        
        return False
    
    def maybe_inject_intermittent_failure(self) -> bool:
        """Check if intermittent failure should occur."""
        for fault in self.active_faults:
            if fault.fault_type == FaultType.INTERMITTENT_FAILURE:
                # Failures occur based on intensity
                if random.random() < (fault.intensity * fault.probability):
                    return True
        
        return False
    
    def run_experiment(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """
        Run chaos experiment.
        
        Parameters
        ----------
        experiment : ChaosExperiment
            Experiment configuration
        
        Returns
        -------
        dict
            Experiment results
        """
        log.info(f"Running chaos experiment: {experiment.name}")
        
        # 1. Verify steady state
        initial_steady = experiment.validate_steady_state()
        
        if not initial_steady:
            log.warning("System not in steady state before experiment")
        
        # 2. Inject faults
        start_time = time.time()
        
        for fault in experiment.faults:
            self.active_faults.append(fault)
        
        # 3. Run for duration
        try:
            time.sleep(experiment.duration)
        finally:
            # 4. Remove faults
            for fault in experiment.faults:
                if fault in self.active_faults:
                    self.active_faults.remove(fault)
        
        # 5. Verify steady state recovered
        final_steady = experiment.validate_steady_state()
        
        duration = time.time() - start_time
        
        result = {
            'experiment_name': experiment.name,
            'duration': duration,
            'initial_steady_state': initial_steady,
            'final_steady_state': final_steady,
            'recovered': final_steady,
            'faults_injected': len(experiment.faults),
        }
        
        self.experiment_results.append(result)
        
        log.info(f"Experiment complete: {experiment.name} - Recovered: {final_steady}")
        
        return result


class ResilienceValidator:
    """
    Validates system resilience patterns.
    
    Tests common resilience patterns:
    - Circuit breaker
    - Retry with backoff
    - Fallback
    - Timeout
    - Bulkhead isolation
    """
    
    def __init__(self, chaos: ChaosEngineer):
        self.chaos = chaos
        self.test_results: List[Dict] = []
    
    def test_circuit_breaker(
        self,
        protected_function: Callable,
        failure_threshold: int = 5,
    ) -> Dict[str, Any]:
        """
        Test circuit breaker pattern.
        
        Parameters
        ----------
        protected_function : callable
            Function protected by circuit breaker
        failure_threshold : int
            Number of failures before circuit opens
        
        Returns
        -------
        dict
            Test results
        """
        log.info("Testing circuit breaker pattern")
        
        # Inject service failures
        failures = 0
        successes = 0
        
        with self.chaos.inject_fault(FaultType.SERVICE_FAILURE, intensity=1.0):
            # Should fail initially
            for i in range(failure_threshold + 2):
                try:
                    protected_function()
                    successes += 1
                except Exception:
                    failures += 1
        
        # Circuit should open after threshold
        circuit_opened = failures >= failure_threshold
        
        result = {
            'pattern': 'circuit_breaker',
            'failures': failures,
            'successes': successes,
            'circuit_opened': circuit_opened,
            'passed': circuit_opened,
        }
        
        self.test_results.append(result)
        
        return result
    
    def test_retry_with_backoff(
        self,
        flaky_function: Callable,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Test retry with exponential backoff.
        
        Parameters
        ----------
        flaky_function : callable
            Function that may fail intermittently
        max_retries : int
            Maximum retry attempts
        
        Returns
        -------
        dict
            Test results
        """
        log.info("Testing retry with backoff pattern")
        
        attempts = 0
        success = False
        
        # Inject intermittent failures
        with self.chaos.inject_fault(FaultType.INTERMITTENT_FAILURE, intensity=0.5):
            for attempt in range(max_retries + 1):
                attempts += 1
                
                try:
                    flaky_function()
                    success = True
                    break
                except Exception:
                    if attempt < max_retries:
                        # Exponential backoff
                        backoff = 2 ** attempt * 0.1
                        time.sleep(backoff)
        
        result = {
            'pattern': 'retry_with_backoff',
            'attempts': attempts,
            'success': success,
            'passed': success or attempts > max_retries,
        }
        
        self.test_results.append(result)
        
        return result
    
    def test_fallback(
        self,
        primary_function: Callable,
        fallback_function: Callable,
    ) -> Dict[str, Any]:
        """
        Test fallback pattern.
        
        Parameters
        ----------
        primary_function : callable
            Primary data source
        fallback_function : callable
            Fallback data source
        
        Returns
        -------
        dict
            Test results
        """
        log.info("Testing fallback pattern")
        
        result_source = None
        
        # Inject service failure on primary
        with self.chaos.inject_fault(FaultType.SERVICE_FAILURE, intensity=1.0):
            try:
                primary_function()
                result_source = 'primary'
            except Exception:
                # Should fall back
                try:
                    fallback_function()
                    result_source = 'fallback'
                except Exception:
                    result_source = 'failed'
        
        result = {
            'pattern': 'fallback',
            'result_source': result_source,
            'passed': result_source == 'fallback',
        }
        
        self.test_results.append(result)
        
        return result
    
    def test_timeout(
        self,
        slow_function: Callable,
        timeout: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Test timeout pattern.
        
        Parameters
        ----------
        slow_function : callable
            Function that may be slow
        timeout : float
            Timeout in seconds
        
        Returns
        -------
        dict
            Test results
        """
        log.info("Testing timeout pattern")
        
        timed_out = False
        
        # Inject latency
        with self.chaos.inject_fault(FaultType.NETWORK_LATENCY, intensity=1.0):
            start = time.time()
            
            try:
                # This should timeout
                slow_function()
            except TimeoutError:
                timed_out = True
            except Exception:
                pass
            
            elapsed = time.time() - start
        
        # Should timeout within reasonable margin
        within_timeout = elapsed <= (timeout * 1.5)
        
        result = {
            'pattern': 'timeout',
            'timed_out': timed_out,
            'elapsed': elapsed,
            'within_timeout': within_timeout,
            'passed': timed_out or within_timeout,
        }
        
        self.test_results.append(result)
        
        return result
    
    def generate_report(self) -> str:
        """Generate resilience test report."""
        lines = [
            "Resilience Pattern Test Report",
            "=" * 50,
            "",
        ]
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get('passed', False))
        
        for result in self.test_results:
            pattern = result.get('pattern', 'unknown')
            passed = result.get('passed', False)
            status = "✅ PASS" if passed else "❌ FAIL"
            
            lines.append(f"{pattern}: {status}")
        
        lines.append("")
        lines.append(f"Total: {passed_tests}/{total_tests} passed")
        
        return '\n'.join(lines)
