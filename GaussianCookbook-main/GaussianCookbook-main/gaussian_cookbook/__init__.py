"""
Gaussian Cookbook: A rigorous library for Gaussian stochastic processes.

This library provides mathematically rigorous implementations of:
- Brownian Motion (standard and fractional)
- Brownian Bridge
- Parameter estimation methods
- Hypothesis testing frameworks
- Statistical validation tools
"""

__version__ = "0.2.0"
__author__ = "Gaussian Cookbook Contributors"

from .processes import (
    BrownianMotion,
    FractionalBrownianMotion,
    BrownianBridge,
    FBMMethod
)

from .estimation import (
    HurstEstimator,
    MaximumLikelihoodEstimator
)

from .testing import (
    HypothesisTests
)

__all__ = [
    "BrownianMotion",
    "FractionalBrownianMotion", 
    "BrownianBridge",
    "FBMMethod",
    "HurstEstimator",
    "MaximumLikelihoodEstimator",
    "HypothesisTests"
]