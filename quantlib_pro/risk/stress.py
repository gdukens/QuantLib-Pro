"""
Stress testing - convenience wrapper module.

This module re-exports the stress testing functionality for cleaner imports.
"""

from quantlib_pro.risk.stress_testing import (
    StressTestEngine,
    StressTestResult,
)

# Provide backward compatibility aliases
StressTester = StressTestEngine
StressResult = StressTestResult

__all__ = [
    "StressTestEngine",
    "StressTestResult",
    "StressTester",  # Alias for backward compatibility
    "StressResult",   # Alias for backward compatibility
]
