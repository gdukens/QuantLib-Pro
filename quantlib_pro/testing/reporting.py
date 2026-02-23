"""
Test Reporting and Metrics

Track test execution history, performance trends, and coverage metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import os
import pandas as pd
import numpy as np


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(Enum):
    """Type of test."""
    UNIT = "unit"
    INTEGRATION = "integration"
    LOAD = "load"
    CHAOS = "chaos"
    VALIDATION = "validation"


@dataclass
class TestResult:
    """Single test execution result."""
    test_name: str
    test_type: TestType
    status: TestStatus
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'test_name': self.test_name,
            'test_type': self.test_type.value,
            'status': self.status.value,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create from dictionary."""
        return cls(
            test_name=data['test_name'],
            test_type=TestType(data['test_type']),
            status=TestStatus(data['status']),
            duration_ms=data['duration_ms'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            error_message=data.get('error_message'),
            metadata=data.get('metadata', {}),
        )


@dataclass
class TestRun:
    """Complete test run with multiple results."""
    run_id: str
    run_type: TestType
    start_time: datetime
    end_time: datetime
    results: List[TestResult]
    environment: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Total run duration."""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def total_tests(self) -> int:
        """Total number of tests."""
        return len(self.results)
    
    @property
    def passed_tests(self) -> int:
        """Number of passed tests."""
        return sum(1 for r in self.results if r.status == TestStatus.PASSED)
    
    @property
    def failed_tests(self) -> int:
        """Number of failed tests."""
        return sum(1 for r in self.results if r.status == TestStatus.FAILED)
    
    @property
    def pass_rate(self) -> float:
        """Pass rate percentage."""
        return (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0.0
    
    @property
    def avg_duration_ms(self) -> float:
        """Average test duration."""
        if not self.results:
            return 0.0
        return np.mean([r.duration_ms for r in self.results])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'run_id': self.run_id,
            'run_type': self.run_type.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'results': [r.to_dict() for r in self.results],
            'environment': self.environment,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestRun':
        """Create from dictionary."""
        return cls(
            run_id=data['run_id'],
            run_type=TestType(data['run_type']),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            results=[TestResult.from_dict(r) for r in data['results']],
            environment=data.get('environment', {}),
        )


class TestReporter:
    """Test execution reporter and history tracker."""
    
    def __init__(self, storage_path: str = "test_reports"):
        """
        Initialize test reporter.
        
        Args:
            storage_path: Directory for storing test reports
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def save_run(self, run: TestRun) -> None:
        """
        Save test run to storage.
        
        Args:
            run: Test run to save
        """
        filepath = os.path.join(self.storage_path, f"{run.run_id}.json")
        
        with open(filepath, 'w') as f:
            json.dump(run.to_dict(), f, indent=2)
    
    def load_run(self, run_id: str) -> Optional[TestRun]:
        """
        Load test run from storage.
        
        Args:
            run_id: Test run identifier
            
        Returns:
            Test run or None if not found
        """
        filepath = os.path.join(self.storage_path, f"{run_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return TestRun.from_dict(data)
    
    def list_runs(self, 
                  test_type: Optional[TestType] = None,
                  since: Optional[datetime] = None,
                  limit: Optional[int] = None) -> List[TestRun]:
        """
        List test runs.
        
        Args:
            test_type: Filter by test type
            since: Filter runs after this datetime
            limit: Maximum number of runs to return
            
        Returns:
            List of test runs
        """
        runs = []
        
        for filename in os.listdir(self.storage_path):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.storage_path, filename)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
                run = TestRun.from_dict(data)
                
                # Apply filters
                if test_type and run.run_type != test_type:
                    continue
                
                if since and run.start_time < since:
                    continue
                
                runs.append(run)
        
        # Sort by start time (newest first)
        runs.sort(key=lambda r: r.start_time, reverse=True)
        
        # Apply limit
        if limit:
            runs = runs[:limit]
        
        return runs
    
    def get_summary(self, test_type: Optional[TestType] = None) -> pd.DataFrame:
        """
        Get summary of test runs.
        
        Args:
            test_type: Filter by test type
            
        Returns:
            DataFrame with run summaries
        """
        runs = self.list_runs(test_type=test_type)
        
        if not runs:
            return pd.DataFrame()
        
        data = []
        
        for run in runs:
            data.append({
                'Run ID': run.run_id,
                'Type': run.run_type.value,
                'Start Time': run.start_time,
                'Duration (s)': run.duration_seconds,
                'Total Tests': run.total_tests,
                'Passed': run.passed_tests,
                'Failed': run.failed_tests,
                'Pass Rate (%)': run.pass_rate,
                'Avg Duration (ms)': run.avg_duration_ms,
            })
        
        return pd.DataFrame(data)
    
    def generate_report(self, run_id: str) -> str:
        """
        Generate detailed test report.
        
        Args:
            run_id: Test run identifier
            
        Returns:
            Formatted report string
        """
        run = self.load_run(run_id)
        
        if not run:
            return f"Test run {run_id} not found"
        
        report = []
        report.append("=" * 80)
        report.append(f"TEST REPORT: {run.run_id}")
        report.append("=" * 80)
        report.append(f"Type: {run.run_type.value}")
        report.append(f"Start Time: {run.start_time}")
        report.append(f"End Time: {run.end_time}")
        report.append(f"Duration: {run.duration_seconds:.2f}s")
        report.append("")
        
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Tests: {run.total_tests}")
        report.append(f"Passed: {run.passed_tests}")
        report.append(f"Failed: {run.failed_tests}")
        report.append(f"Pass Rate: {run.pass_rate:.1f}%")
        report.append(f"Avg Duration: {run.avg_duration_ms:.1f}ms")
        report.append("")
        
        # Failed tests
        failed = [r for r in run.results if r.status == TestStatus.FAILED]
        
        if failed:
            report.append("FAILED TESTS")
            report.append("-" * 80)
            
            for result in failed:
                report.append(f"❌ {result.test_name}")
                report.append(f"   Duration: {result.duration_ms:.1f}ms")
                
                if result.error_message:
                    report.append(f"   Error: {result.error_message}")
                
                report.append("")
        
        # Environment info
        if run.environment:
            report.append("ENVIRONMENT")
            report.append("-" * 80)
            
            for key, value in run.environment.items():
                report.append(f"{key}: {value}")
            
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


class TrendAnalyzer:
    """Analyze test trends over time."""
    
    def __init__(self, reporter: TestReporter):
        """
        Initialize trend analyzer.
        
        Args:
            reporter: Test reporter instance
        """
        self.reporter = reporter
    
    def get_pass_rate_trend(self, 
                           test_type: Optional[TestType] = None,
                           days: int = 30) -> pd.DataFrame:
        """
        Get pass rate trend over time.
        
        Args:
            test_type: Filter by test type
            days: Number of days to analyze
            
        Returns:
            DataFrame with daily pass rates
        """
        since = datetime.now() - timedelta(days=days)
        runs = self.reporter.list_runs(test_type=test_type, since=since)
        
        if not runs:
            return pd.DataFrame()
        
        data = []
        
        for run in runs:
            data.append({
                'date': run.start_time.date(),
                'pass_rate': run.pass_rate,
                'total_tests': run.total_tests,
            })
        
        df = pd.DataFrame(data)
        
        # Group by date and average
        return df.groupby('date').agg({
            'pass_rate': 'mean',
            'total_tests': 'sum',
        }).reset_index()
    
    def get_duration_trend(self,
                          test_type: Optional[TestType] = None,
                          days: int = 30) -> pd.DataFrame:
        """
        Get test duration trend over time.
        
        Args:
            test_type: Filter by test type
            days: Number of days to analyze
            
        Returns:
            DataFrame with daily average durations
        """
        since = datetime.now() - timedelta(days=days)
        runs = self.reporter.list_runs(test_type=test_type, since=since)
        
        if not runs:
            return pd.DataFrame()
        
        data = []
        
        for run in runs:
            data.append({
                'date': run.start_time.date(),
                'avg_duration_ms': run.avg_duration_ms,
            })
        
        df = pd.DataFrame(data)
        
        # Group by date and average
        return df.groupby('date').agg({
            'avg_duration_ms': 'mean',
        }).reset_index()
    
    def detect_regressions(self,
                          test_type: Optional[TestType] = None,
                          threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Detect performance regressions.
        
        Args:
            test_type: Filter by test type
            threshold: Regression threshold (10% by default)
            
        Returns:
            List of detected regressions
        """
        runs = self.reporter.list_runs(test_type=test_type, limit=10)
        
        if len(runs) < 2:
            return []
        
        regressions = []
        
        # Compare latest run with baseline (average of previous runs)
        latest = runs[0]
        baseline_runs = runs[1:]
        
        # Calculate baseline metrics
        baseline_duration = np.mean([r.avg_duration_ms for r in baseline_runs])
        baseline_pass_rate = np.mean([r.pass_rate for r in baseline_runs])
        
        # Check for duration regression
        duration_change = (latest.avg_duration_ms - baseline_duration) / baseline_duration
        
        if duration_change > threshold:
            regressions.append({
                'type': 'duration',
                'metric': 'avg_duration_ms',
                'baseline': baseline_duration,
                'current': latest.avg_duration_ms,
                'change_pct': duration_change * 100,
                'run_id': latest.run_id,
            })
        
        # Check for pass rate regression
        pass_rate_change = (baseline_pass_rate - latest.pass_rate) / 100
        
        if pass_rate_change > threshold:
            regressions.append({
                'type': 'pass_rate',
                'metric': 'pass_rate',
                'baseline': baseline_pass_rate,
                'current': latest.pass_rate,
                'change_pct': -pass_rate_change * 100,
                'run_id': latest.run_id,
            })
        
        return regressions


class CoverageTracker:
    """Track test coverage metrics."""
    
    def __init__(self):
        """Initialize coverage tracker."""
        self.modules_covered: set = set()
        self.functions_covered: set = set()
        self.total_modules: int = 0
        self.total_functions: int = 0
    
    def record_coverage(self,
                       module: str,
                       function: str) -> None:
        """
        Record coverage for a module/function.
        
        Args:
            module: Module name
            function: Function name
        """
        self.modules_covered.add(module)
        self.functions_covered.add(f"{module}.{function}")
    
    def set_totals(self,
                  total_modules: int,
                  total_functions: int) -> None:
        """
        Set total counts for coverage calculation.
        
        Args:
            total_modules: Total number of modules
            total_functions: Total number of functions
        """
        self.total_modules = total_modules
        self.total_functions = total_functions
    
    @property
    def module_coverage(self) -> float:
        """Module coverage percentage."""
        if self.total_modules == 0:
            return 0.0
        return len(self.modules_covered) / self.total_modules * 100
    
    @property
    def function_coverage(self) -> float:
        """Function coverage percentage."""
        if self.total_functions == 0:
            return 0.0
        return len(self.functions_covered) / self.total_functions * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get coverage summary.
        
        Returns:
            Coverage metrics
        """
        return {
            'modules_covered': len(self.modules_covered),
            'total_modules': self.total_modules,
            'module_coverage_pct': self.module_coverage,
            'functions_covered': len(self.functions_covered),
            'total_functions': self.total_functions,
            'function_coverage_pct': self.function_coverage,
        }
    
    def generate_report(self) -> str:
        """
        Generate coverage report.
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("TEST COVERAGE REPORT")
        report.append("=" * 60)
        report.append(f"Modules: {len(self.modules_covered)}/{self.total_modules} ({self.module_coverage:.1f}%)")
        report.append(f"Functions: {len(self.functions_covered)}/{self.total_functions} ({self.function_coverage:.1f}%)")
        report.append("")
        
        if self.modules_covered:
            report.append("COVERED MODULES")
            report.append("-" * 60)
            
            for module in sorted(self.modules_covered):
                report.append(f"✓ {module}")
            
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
