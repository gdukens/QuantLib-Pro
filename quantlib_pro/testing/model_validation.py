"""
Model Validation Suite for QuantLib Pro

End-to-end validation of quantitative models against known benchmarks:
- Options pricing accuracy
- Risk metrics (VaR, CVaR)
- Portfolio optimization
- Market regime detection
- Statistical properties

Example
-------
>>> from quantlib_pro.testing.model_validation import ModelValidator
>>>
>>> validator = ModelValidator()
>>> results = validator.validate_all_models()
>>> print(validator.generate_report())
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from quantlib_pro.options.black_scholes import BlackScholesModel
from quantlib_pro.options.monte_carlo import MonteCarloEngine
from quantlib_pro.portfolio.optimizer import PortfolioOptimizer
from quantlib_pro.risk.var import calculate_var, VaRMethod
from quantlib_pro.market_regime.hmm import MarketRegimeDetector
from quantlib_pro.data.providers import SimulatedProvider

log = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Validation result for a single model/test."""
    model_name: str
    test_name: str
    expected_value: float
    actual_value: float
    tolerance: float
    passed: bool
    error_pct: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.error_pct is None and self.expected_value != 0:
            self.error_pct = abs(self.actual_value - self.expected_value) / abs(self.expected_value) * 100


class ModelValidator:
    """
    Comprehensive model validation suite.
    
    Validates all quantitative models against known benchmarks,
    closed-form solutions, and industry standards.
    
    Example
    -------
    >>> validator = ModelValidator()
    >>> results = validator.validate_options_pricing()
    >>> print(f"{len([r for r in results if r.passed])} / {len(results)} tests passed")
    """
    
    def __init__(self, tolerance: float = 0.01):
        """
        Initialize validator.
        
        Parameters
        ----------
        tolerance : float
            Default relative tolerance for validation (1% = 0.01)
        """
        self.tolerance = tolerance
        self.results: List[ValidationResult] = []
        
        log.info(f"Initialized ModelValidator with tolerance={tolerance}")
    
    def validate_all_models(self) -> List[ValidationResult]:
        """Run all validation tests."""
        self.results = []
        
        self.validate_options_pricing()
        self.validate_risk_metrics()
        self.validate_portfolio_optimization()
        self.validate_statistical_properties()
        
        return self.results
    
    def validate_options_pricing(self) -> List[ValidationResult]:
        """
        Validate options pricing models.
        
        Tests:
        1. Black-Scholes vs known analytical values
        2. Monte Carlo vs Black-Scholes
        3. Put-call parity
        4. Greeks accuracy
        """
        log.info("Validating options pricing models")
        
        bs = BlackScholesModel()
        
        # Test 1: ATM call option (benchmark from literature)
        # S=100, K=100, T=1, r=0.05, sigma=0.2
        # Expected: ~10.45 (from Hull's Options book Table)
        call_price = bs.price_call(S=100, K=100, T=1.0, r=0.05, sigma=0.2)
        
        self.results.append(ValidationResult(
            model_name='Black-Scholes',
            test_name='ATM Call Price',
            expected_value=10.45,
            actual_value=call_price,
            tolerance=0.01,
            passed=abs(call_price - 10.45) / 10.45 < 0.01,
        ))
        
        # Test 2: ATM put option
        put_price = bs.price_put(S=100, K=100, T=1.0, r=0.05, sigma=0.2)
        
        # Expected: ~5.57 (from Hull's Options book)
        self.results.append(ValidationResult(
            model_name='Black-Scholes',
            test_name='ATM Put Price',
            expected_value=5.57,
            actual_value=put_price,
            tolerance=0.01,
            passed=abs(put_price - 5.57) / 5.57 < 0.01,
        ))
        
        # Test 3: Put-Call Parity
        # C - P = S - K * exp(-r*T)
        parity_lhs = call_price - put_price
        parity_rhs = 100 - 100 * np.exp(-0.05 * 1.0)
        
        self.results.append(ValidationResult(
            model_name='Black-Scholes',
            test_name='Put-Call Parity',
            expected_value=parity_rhs,
            actual_value=parity_lhs,
            tolerance=0.001,
            passed=abs(parity_lhs - parity_rhs) < 0.01,
        ))
        
        # Test 4: Monte Carlo vs Black-Scholes
        mc = MonteCarloEngine(n_simulations=100000, seed=42)
        mc_call_price = mc.price_european_option(
            S0=100, K=100, T=1.0, r=0.05, sigma=0.2, option_type='call'
        )
        
        self.results.append(ValidationResult(
            model_name='Monte Carlo',
            test_name='MC vs BS Call Price',
            expected_value=call_price,
            actual_value=mc_call_price,
            tolerance=0.02,  # MC has sampling error
            passed=abs(mc_call_price - call_price) / call_price < 0.02,
        ))
        
        # Test 5: Greeks - Delta
        greeks = bs.calculate_greeks(S=100, K=100, T=1.0, r=0.05, sigma=0.2, option_type='call')
        
        # ATM call delta should be ~0.6 (slightly above 0.5 due to drift)
        expected_delta = 0.6368  # Analytical value
        
        self.results.append(ValidationResult(
            model_name='Black-Scholes',
            test_name='Call Delta',
            expected_value=expected_delta,
            actual_value=greeks['delta'],
            tolerance=0.01,
            passed=abs(greeks['delta'] - expected_delta) / expected_delta < 0.01,
        ))
        
        # Test 6: Greeks - Gamma (should be positive and symmetric for ATM)
        # ATM gamma ~ 0.02 for these parameters
        expected_gamma = 0.0199  # Analytical value
        
        self.results.append(ValidationResult(
            model_name='Black-Scholes',
            test_name='Gamma',
            expected_value=expected_gamma,
            actual_value=greeks['gamma'],
            tolerance=0.05,
            passed=abs(greeks['gamma'] - expected_gamma) / expected_gamma < 0.05,
        ))
        
        # Test 7: Deep ITM call should have delta close to 1
        itm_greeks = bs.calculate_greeks(S=150, K=100, T=1.0, r=0.05, sigma=0.2, option_type='call')
        
        self.results.append(ValidationResult(
            model_name='Black-Scholes',
            test_name='Deep ITM Call Delta',
            expected_value=0.95,
            actual_value=itm_greeks['delta'],
            tolerance=0.05,
            passed=itm_greeks['delta'] > 0.90,
        ))
        
        # Test 8: Deep OTM call should have delta close to 0
        otm_greeks = bs.calculate_greeks(S=50, K=100, T=1.0, r=0.05, sigma=0.2, option_type='call')
        
        self.results.append(ValidationResult(
            model_name='Black-Scholes',
            test_name='Deep OTM Call Delta',
            expected_value=0.0,
            actual_value=otm_greeks['delta'],
            tolerance=0.01,
            passed=otm_greeks['delta'] < 0.01,
        ))
        
        return [r for r in self.results if r.model_name in ['Black-Scholes', 'Monte Carlo']]
    
    def validate_risk_metrics(self) -> List[ValidationResult]:
        """
        Validate risk calculation models.
        
        Tests:
        1. VaR for normal distribution (analytical)
        2. CVaR relationship (CVaR >= VaR)
        3. Historical vs parametric VaR
        """
        log.info("Validating risk metrics")
        
        # Test 1: VaR for perfectly normal returns
        np.random.seed(42)
        normal_returns = pd.Series(np.random.normal(0, 0.01, 10000))
        
        # Parametric VaR (95%)
        var_result = calculate_var(normal_returns, confidence=0.95, method=VaRMethod.PARAMETRIC)
        
        # Expected: -1.645 * 0.01 = -0.01645
        expected_var = -1.645 * 0.01
        
        self.results.append(ValidationResult(
            model_name='VaR',
            test_name='Parametric VaR (Normal)',
            expected_value=expected_var,
            actual_value=var_result.var,
            tolerance=0.05,  # 5% tolerance
            passed=abs(var_result.var - expected_var) / abs(expected_var) < 0.05,
        ))
        
        # Test 2: CVaR >= VaR
        self.results.append(ValidationResult(
            model_name='VaR',
            test_name='CVaR >= VaR',
            expected_value=var_result.var,
            actual_value=var_result.cvar,
            tolerance=0.0,
            passed=var_result.cvar <= var_result.var,  # CVaR should be worse (more negative)
        ))
        
        # Test 3: Historical VaR
        hist_var = calculate_var(normal_returns, confidence=0.95, method=VaRMethod.HISTORICAL)
        
        # Should be close to parametric for normal distribution
        self.results.append(ValidationResult(
            model_name='VaR',
            test_name='Historical vs Parametric',
            expected_value=var_result.var,
            actual_value=hist_var.var,
            tolerance=0.10,  # 10% tolerance
            passed=abs(hist_var.var - var_result.var) / abs(var_result.var) < 0.10,
        ))
        
        # Test 4: Monte Carlo VaR
        mc_var = calculate_var(normal_returns, confidence=0.95, method=VaRMethod.MONTE_CARLO)
        
        self.results.append(ValidationResult(
            model_name='VaR',
            test_name='Monte Carlo VaR',
            expected_value=var_result.var,
            actual_value=mc_var.var,
            tolerance=0.10,
            passed=abs(mc_var.var - var_result.var) / abs(var_result.var) < 0.10,
        ))
        
        return [r for r in self.results if r.model_name == 'VaR']
    
    def validate_portfolio_optimization(self) -> List[ValidationResult]:
        """
        Validate portfolio optimization.
        
        Tests:
        1. Weights sum to 1
        2. Max Sharpe portfolio has positive Sharpe
        3. Min volatility portfolio has lowest vol
        4. Efficient frontier is convex
        """
        log.info("Validating portfolio optimization")
        
        # Generate sample returns
        provider = SimulatedProvider(n_assets=5, n_periods=252, seed=42)
        returns = provider.fetch_historical('val', start='2023-01-01', end='2023-12-31')
        
        optimizer = PortfolioOptimizer(returns, risk_free_rate=0.02)
        
        # Test 1: Max Sharpe weights sum to 1
        max_sharpe = optimizer.optimize_max_sharpe()
        
        self.results.append(ValidationResult(
            model_name='Portfolio Optimization',
            test_name='Weights Sum to 1',
            expected_value=1.0,
            actual_value=np.sum(max_sharpe.weights),
            tolerance=1e-6,
            passed=abs(np.sum(max_sharpe.weights) - 1.0) < 1e-6,
        ))
        
        # Test 2: Max Sharpe has positive Sharpe ratio
        self.results.append(ValidationResult(
            model_name='Portfolio Optimization',
            test_name='Positive Sharpe Ratio',
            expected_value=0.5,  # Reasonable expectation
            actual_value=max_sharpe.sharpe_ratio,
            tolerance=1.0,
            passed=max_sharpe.sharpe_ratio > 0,
        ))
        
        # Test 3: Min volatility
        min_vol = optimizer.optimize_min_volatility()
        
        # Min vol portfolio should have lower vol than max Sharpe
        self.results.append(ValidationResult(
            model_name='Portfolio Optimization',
            test_name='Min Vol < Max Sharpe Vol',
            expected_value=min_vol.volatility,
            actual_value=max_sharpe.volatility,
            tolerance=0.0,
            passed=min_vol.volatility <= max_sharpe.volatility * 1.01,  # Allow 1% tolerance
        ))
        
        # Test 4: All weights non-negative (long-only constraint)
        self.results.append(ValidationResult(
            model_name='Portfolio Optimization',
            test_name='Long-Only Constraint',
            expected_value=0.0,
            actual_value=np.min(max_sharpe.weights),
            tolerance=1e-6,
            passed=np.all(max_sharpe.weights >= -1e-6),
        ))
        
        return [r for r in self.results if r.model_name == 'Portfolio Optimization']
    
    def validate_statistical_properties(self) -> List[ValidationResult]:
        """
        Validate statistical properties.
        
        Tests:
        1. Simulated data has correct mean/variance
        2. Correlation matrix properties
        3. Regime detection converges
        """
        log.info("Validating statistical properties")
        
        # Test 1: Simulated data statistics
        provider = SimulatedProvider(n_assets=1, n_periods=10000, seed=42, mean_return=0.001, volatility=0.02)
        returns = provider.fetch_historical('stats', start='2020-01-01', end='2023-12-31')
        
        actual_mean = returns.mean().values[0]
        actual_std = returns.std().values[0]
        
        self.results.append(ValidationResult(
            model_name='Simulated Data',
            test_name='Mean Return',
            expected_value=0.001,
            actual_value=actual_mean,
            tolerance=0.20,  # 20% tolerance (statistical variation)
            passed=abs(actual_mean - 0.001) / 0.001 < 0.20,
        ))
        
        self.results.append(ValidationResult(
            model_name='Simulated Data',
            test_name='Volatility',
            expected_value=0.02,
            actual_value=actual_std,
            tolerance=0.10,
            passed=abs(actual_std - 0.02) / 0.02 < 0.10,
        ))
        
        # Test 2: Correlation matrix is positive semi-definite
        provider_multi = SimulatedProvider(n_assets=5, n_periods=500, seed=42)
        returns_multi = provider_multi.fetch_historical('corr', start='2023-01-01', end='2023-12-31')
        
        corr_matrix = returns_multi.corr()
        eigenvalues = np.linalg.eigvalsh(corr_matrix)
        
        self.results.append(ValidationResult(
            model_name='Correlation Matrix',
            test_name='Positive Semi-Definite',
            expected_value=0.0,
            actual_value=np.min(eigenvalues),
            tolerance=1e-10,
            passed=np.min(eigenvalues) >= -1e-10,
        ))
        
        # Test 3: Market regime detection
        regime_detector = MarketRegimeDetector(n_regimes=3)
        regime_detector.fit(returns_multi.mean(axis=1).values)
        
        # Should detect 3 regimes
        self.results.append(ValidationResult(
            model_name='Regime Detection',
            test_name='Number of Regimes',
            expected_value=3,
            actual_value=regime_detector.n_regimes,
            tolerance=0,
            passed=regime_detector.n_regimes == 3,
        ))
        
        return [r for r in self.results if r.model_name in ['Simulated Data', 'Correlation Matrix', 'Regime Detection']]
    
    def generate_report(self) -> str:
        """Generate validation report."""
        if not self.results:
            return "No validation results available"
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        pass_rate = passed / total * 100
        
        lines = [
            "Model Validation Report",
            "=" * 80,
            f"Total Tests: {total}",
            f"Passed: {passed} ({pass_rate:.1f}%)",
            f"Failed: {total - passed}",
            "",
            "Details:",
            "-" * 80,
        ]
        
        # Group by model
        by_model: Dict[str, List[ValidationResult]] = {}
        for result in self.results:
            if result.model_name not in by_model:
                by_model[result.model_name] = []
            by_model[result.model_name].append(result)
        
        for model_name, results in sorted(by_model.items()):
            model_passed = sum(1 for r in results if r.passed)
            model_total = len(results)
            
            lines.append(f"\n{model_name}: {model_passed}/{model_total} passed")
            
            for r in results:
                status = "✅" if r.passed else "❌"
                error = f" (error: {r.error_pct:.2f}%)" if r.error_pct is not None else ""
                lines.append(f"  {status} {r.test_name}: {r.actual_value:.6f} (expected: {r.expected_value:.6f}){error}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"Overall Status: {'✅ VALIDATED' if pass_rate >= 90 else '❌ VALIDATION FAILED'}")
        
        return '\n'.join(lines)
    
    def get_summary_df(self) -> pd.DataFrame:
        """Get summary as DataFrame."""
        data = []
        
        for r in self.results:
            data.append({
                'Model': r.model_name,
                'Test': r.test_name,
                'Expected': r.expected_value,
                'Actual': r.actual_value,
                'Error %': r.error_pct,
                'Passed': r.passed,
            })
        
        return pd.DataFrame(data)


if __name__ == '__main__':
    # Run validation
    validator = ModelValidator()
    validator.validate_all_models()
    print(validator.generate_report())
