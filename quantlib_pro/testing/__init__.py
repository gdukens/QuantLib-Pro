"""Testing infrastructure for QuantLib Pro.

Advanced testing tools:
- Load testing framework
- Chaos engineering / fault injection
- Model validation suite
- Test reporting and metrics
"""

from quantlib_pro.testing.load_testing import (
    LoadPattern,
    LoadTestResult,
    LoadTestScenario,
    LoadTester,
    PerformanceBenchmark,
    Request,
)
from quantlib_pro.testing.chaos import (
    ChaosEngineer,
    ChaosExperiment,
    FaultInjection,
    FaultType,
    ResilienceValidator,
)
from quantlib_pro.testing.model_validation import (
    ModelValidator,
    ValidationResult,
)
from quantlib_pro.testing.reporting import (
    TestReporter,
    TrendAnalyzer,
    CoverageTracker,
    TestResult,
    TestRun,
    TestStatus,
    TestType,
)

__all__ = [
    # Load Testing
    "LoadPattern",
    "LoadTestResult",
    "LoadTestScenario",
    "LoadTester",
    "PerformanceBenchmark",
    "Request",
    # Chaos Engineering
    "ChaosEngineer",
    "ChaosExperiment",
    "FaultInjection",
    "FaultType",
    "ResilienceValidator",
    # Model Validation
    "ModelValidator",
    "ValidationResult",
    # Test Reporting
    "TestReporter",
    "TrendAnalyzer",
    "CoverageTracker",
    "TestResult",
    "TestRun",
    "TestStatus",
    "TestType",
]
