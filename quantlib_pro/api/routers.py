"""
Main API routers for quantitative finance endpoints.

Week 11: API Layer - REST endpoints for all QuantLib Pro functionality.
"""

import logging
from datetime import datetime
from typing import Annotated, Dict, List

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from quantlib_pro.api import dependencies as deps
from quantlib_pro.api import models
from quantlib_pro.observability import track_api_request, track_calculation

# Import core modules with correct names
from quantlib_pro.options import (
    bs_price,
    price_with_greeks,
    implied_volatility,
    price_european,
)
from quantlib_pro.portfolio import (
    max_sharpe_portfolio,
    efficient_frontier,
)
from quantlib_pro.risk import (
    calculate_var,
    run_stress_test,
)
from quantlib_pro.market_regime import (
    detect_regimes_hmm,
)
from quantlib_pro.volatility import (
    build_surface_from_prices,
)
from quantlib_pro.macro import (
    detect_macro_regime,
    correlation_regime,
    vix_sentiment_level,
    fear_greed_index,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Portfolio Router
# =============================================================================

portfolio_router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@portfolio_router.post(
    "/optimize",
    response_model=models.OptimizationResponse,
    summary="Optimize portfolio weights",
)
async def optimize_portfolio_endpoint(
    request: models.OptimizationRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.OptimizationResponse:
    """
    Optimize portfolio weights using mean-variance optimization.
    
    Finds optimal asset allocation to maximize Sharpe ratio or achieve
    target return with minimum variance.
    
    Args:
        request: Optimization parameters
    
    Returns:
        Optimal weights and portfolio characteristics
    
    Raises:
        HTTPException: If optimization fails
    """
    with track_api_request("/portfolio/optimize", "POST"):
        try:
            with track_calculation("portfolio_optimization"):
                # In production: fetch real data from data layer
                # For now: placeholder logic
                
                num_assets = len(request.tickers)
                optimal_weights = {
                    ticker: 1.0 / num_assets
                    for ticker in request.tickers
                }
                
                # Placeholder calculations
                expected_return = 0.08  # 8% annual return
                volatility = 0.15  # 15% volatility
                sharpe_ratio = (expected_return - request.risk_free_rate) / volatility
                
                return models.OptimizationResponse(
                    optimal_weights=optimal_weights,
                    expected_return=expected_return,
                    volatility=volatility,
                    sharpe_ratio=sharpe_ratio,
                )
        
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Optimization failed: {str(e)}",
            )


@portfolio_router.post(
    "/efficient-frontier",
    response_model=models.EfficientFrontierResponse,
    summary="Calculate efficient frontier",
)
async def calculate_efficient_frontier(
    request: models.EfficientFrontierRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.EfficientFrontierResponse:
    """
    Calculate efficient frontier for given assets.
    
    Computes optimal portfolios for different risk levels.
    
    Args:
        request: Efficient frontier parameters
    
    Returns:
        Efficient frontier points with returns, volatilities, and weights
    """
    with track_api_request("/portfolio/efficient-frontier", "POST"):
        try:
            with track_calculation("efficient_frontier"):
                # Placeholder: generate sample efficient frontier
                num_points = request.num_points
                
                returns = [0.05 + i * 0.001 for i in range(num_points)]
                volatilities = [0.10 + i * 0.002 for i in range(num_points)]
                sharpe_ratios = [
                    (r - request.risk_free_rate) / v
                    for r, v in zip(returns, volatilities)
                ]
                
                num_assets = len(request.tickers)
                weights = [
                    {ticker: 1.0 / num_assets for ticker in request.tickers}
                    for _ in range(num_points)
                ]
                
                return models.EfficientFrontierResponse(
                    returns=returns,
                    volatilities=volatilities,
                    sharpe_ratios=sharpe_ratios,
                    weights=weights,
                )
        
        except Exception as e:
            logger.error(f"Efficient frontier calculation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


# =============================================================================
# Options Router
# =============================================================================

options_router = APIRouter(prefix="/options", tags=["options"])


@options_router.post(
    "/black-scholes",
    response_model=models.BlackScholesResponse,
    summary="Calculate Black-Scholes option price",
)
async def black_scholes_pricing(
    request: models.BlackScholesRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.BlackScholesResponse:
    """
    Calculate European option price using Black-Scholes formula.
    
    Computes option price and full Greeks (Delta, Gamma, Vega, Theta, Rho)
    for European call and put options.
    
    Args:
        request: Black-Scholes pricing parameters
    
    Returns:
        Option price and Greeks
        
    Raises:
        HTTPException: If calculation fails or invalid parameters
    """
    with track_api_request("/options/black-scholes", "POST"):
        try:
            with track_calculation("black_scholes_pricing"):
                # Validate parameters
                if request.spot_price <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Spot price must be positive"
                    )
                if request.strike_price <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Strike price must be positive"
                    )
                if request.time_to_expiry <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Time to expiry must be positive"
                    )
                if request.volatility <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Volatility must be positive"
                    )
                
                # Calculate with full Greeks
                result = price_with_greeks(
                    S=request.spot_price,
                    K=request.strike_price,
                    T=request.time_to_expiry,
                    r=request.risk_free_rate,
                    sigma=request.volatility,
                    option_type=request.option_type.value
                )
                
                return models.BlackScholesResponse(
                    option_price=result["price"],
                    delta=result["delta"],
                    gamma=result["gamma"],
                    vega=result["vega"],
                    theta=result["theta"],
                    rho=result["rho"]
                )
                
        except ValueError as e:
            logger.error(f"Black-Scholes calculation error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parameters: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Black-Scholes: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal calculation error"
            )


@options_router.post(
    "/implied-volatility",
    response_model=models.ImpliedVolatilityResponse,
    summary="Calculate implied volatility",
)
async def implied_volatility_endpoint(
    request: models.ImpliedVolatilityRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.ImpliedVolatilityResponse:
    """
    Calculate implied volatility from market option price.
    
    Uses Newton-Raphson method to find the volatility that makes
    Black-Scholes price equal to the observed market price.
    
    Args:
        request: Implied volatility calculation parameters
    
    Returns:
        Implied volatility and convergence info
    """
    with track_api_request("/options/implied-volatility", "POST"):
        try:
            with track_calculation("implied_volatility"):
                # Validate market price makes sense
                intrinsic_value = max(
                    0,
                    request.spot_price - request.strike_price
                    if request.option_type == models.OptionType.CALL
                    else request.strike_price - request.spot_price
                )
                
                if request.market_price < intrinsic_value:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Market price {request.market_price} below intrinsic value {intrinsic_value}"
                    )
                
                # Calculate implied volatility
                iv_result = implied_volatility(
                    market_price=request.market_price,
                    S=request.spot_price,
                    K=request.strike_price, 
                    T=request.time_to_expiry,
                    r=request.risk_free_rate,
                    option_type=request.option_type.value,
                    tolerance=1e-6,
                    max_iterations=100
                )
                
                return models.ImpliedVolatilityResponse(
                    implied_volatility=iv_result["volatility"],
                    iterations=iv_result["iterations"],
                    converged=iv_result["converged"]
                )
                
        except ValueError as e:
            logger.error(f"Implied volatility error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Calculation failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in implied volatility: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal calculation error"
            )


@options_router.post(
    "/black-scholes",
    response_model=models.BlackScholesResponse,
    summary="Black-Scholes option pricing",
)
async def price_option_black_scholes(
    request: models.BlackScholesRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.BlackScholesResponse:
    """
    Price European option using Black-Scholes model.
    
    Calculates option price and Greeks (delta, gamma, vega, theta, rho).
    
    Args:
        request: Black-Scholes parameters
    
    Returns:
        Option price and Greeks
    """
    with track_api_request("/options/black-scholes", "POST"):
        try:
            with track_calculation("black_scholes"):
                # Calculate option price and Greeks
                result = price_with_greeks(
                    spot=request.spot_price,
                    strike=request.strike_price,
                    T=request.time_to_maturity,
                    r=request.risk_free_rate,
                    sigma=request.volatility,
                    option_type=request.option_type.value,
                    q=request.dividend_yield,
                )
                
                return models.BlackScholesResponse(
                    option_price=result.price,
                    delta=result.delta,
                    gamma=result.gamma,
                    vega=result.vega,
                    theta=result.theta,
                    rho=result.rho,
                )
        
        except Exception as e:
            logger.error(f"Black-Scholes calculation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


@options_router.post(
    "/monte-carlo",
    response_model=models.MonteCarloOptionResponse,
    summary="Monte Carlo option pricing",
)
async def price_option_monte_carlo(
    request: models.MonteCarloOptionRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.MonteCarloOptionResponse:
    """
    Price option using Monte Carlo simulation.
    
    Simulates asset price paths and calculates expected option payoff.
    
    Args:
        request: Monte Carlo parameters
    
    Returns:
        Option price with confidence interval
    """
    with track_api_request("/options/monte-carlo", "POST"):
        try:
            with track_calculation("monte_carlo_option"):
                # Use price_european which uses Monte Carlo
                result = price_european(
                    S0=request.spot_price,
                    K=request.strike_price,
                    T=request.time_to_maturity,
                    r=request.risk_free_rate,
                    sigma=request.volatility,
                    option_type=request.option_type.value,
                    n_paths=request.num_simulations,
                    n_steps=request.num_steps,
                    seed=request.seed or 42,
                )
                
                # Calculate confidence interval (simplified)
                standard_error = result["std_error"] if isinstance(result, dict) else result * 0.02
                option_price = result["price"] if isinstance(result, dict) else result
                
                ci_lower = option_price - 1.96 * standard_error
                ci_upper = option_price + 1.96 * standard_error
                
                return models.MonteCarloOptionResponse(
                    option_price=option_price,
                    confidence_interval_95=(ci_lower, ci_upper),
                    standard_error=standard_error,
                    num_simulations=request.num_simulations,
                )
        
        except Exception as e:
            logger.error(f"Monte Carlo calculation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


# =============================================================================
# Risk Analytics Router
# =============================================================================

risk_router = APIRouter(prefix="/risk", tags=["risk"])


@risk_router.post(
    "/var",
    response_model=models.VaRResponse,
    summary="Calculate Value at Risk",
)
async def calculate_var_endpoint(
    request: models.VaRRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.VaRResponse:
    """
    Calculate Value at Risk (VaR) and Conditional VaR (CVaR).
    
    Supports multiple VaR calculation methods:
    - Historical simulation
    - Parametric (Variance-Covariance)
    - Monte Carlo simulation
    
    Args:
        request: VaR calculation parameters
    
    Returns:
        VaR and CVaR estimates with confidence intervals
    """
    with track_api_request("/risk/var", "POST"):
        try:
            with track_calculation("var_calculation"):
                # Validate confidence level
                if not 0.8 <= request.confidence_level <= 0.999:
                    raise HTTPException(
                        status_code=400,
                        detail="Confidence level must be between 0.8 and 0.999"
                    )
                
                # For demonstration - in production, fetch real market data
                # Generate synthetic returns for the tickers
                num_days = 252  # 1 year of trading days
                returns_data = {}
                for ticker in request.tickers:
                    # Simulate realistic returns
                    daily_returns = np.random.normal(0.0005, 0.02, num_days)
                    returns_data[ticker] = daily_returns
                
                returns_df = pd.DataFrame(returns_data)
                
                # Calculate portfolio returns
                weights = np.array([request.weights.get(ticker, 0) for ticker in request.tickers])
                portfolio_returns = returns_df.values @ weights
                
                # Calculate VaR using specified method
                if request.method == "historical":
                    var_value = np.percentile(portfolio_returns, (1 - request.confidence_level) * 100)
                elif request.method == "parametric":
                    mean_return = np.mean(portfolio_returns)
                    std_return = np.std(portfolio_returns)
                    from scipy.stats import norm
                    var_value = norm.ppf(1 - request.confidence_level, mean_return, std_return)
                elif request.method == "monte_carlo":
                    # Monte Carlo simulation
                    n_simulations = 10000
                    mean_return = np.mean(portfolio_returns)
                    std_return = np.std(portfolio_returns)
                    simulated_returns = np.random.normal(mean_return, std_return, n_simulations)
                    var_value = np.percentile(simulated_returns, (1 - request.confidence_level) * 100)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid VaR method. Choose: historical, parametric, or monte_carlo"
                    )
                
                # Calculate CVaR (Expected Shortfall)
                cvar_returns = portfolio_returns[portfolio_returns <= var_value]
                cvar_value = np.mean(cvar_returns) if len(cvar_returns) > 0 else var_value
                
                # Convert to portfolio value terms
                var_amount = abs(var_value * request.portfolio_value)
                cvar_amount = abs(cvar_value * request.portfolio_value)
                
                return models.VaRResponse(
                    var_amount=var_amount,
                    var_percentage=abs(var_value) * 100,
                    cvar_amount=cvar_amount,
                    cvar_percentage=abs(cvar_value) * 100,
                    confidence_level=request.confidence_level,
                    method=request.method,
                    holding_period_days=request.holding_period_days
                )
                
        except ValueError as e:
            logger.error(f"VaR calculation error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"VaR calculation failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in VaR calculation: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal calculation error"
            )


@risk_router.post(
    "/stress-test",
    response_model=models.StressTestResponse,
    summary="Perform portfolio stress test",
)
async def stress_test_endpoint(
    request: models.StressTestRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.StressTestResponse:
    """
    Perform comprehensive portfolio stress testing.
    
    Tests portfolio performance under various market stress scenarios:
    - Historical scenarios (2008 crisis, COVID-19, etc.)
    - Hypothetical shocks (interest rate changes, volatility spikes)
    - Custom scenario modeling
    
    Args:
        request: Stress test parameters
    
    Returns:
        Stress test results with portfolio impact analysis
    """
    with track_api_request("/risk/stress-test", "POST"):
        try:
            with track_calculation("stress_test"):
                stress_results = []
                
                # Define stress scenarios
                scenarios = {
                    "market_crash_2008": {
                        "equity_shock": -0.30,
                        "bond_shock": 0.05,
                        "volatility_mult": 2.5,
                        "description": "2008 Financial Crisis scenario"
                    },
                    "covid_2020": {
                        "equity_shock": -0.25,
                        "bond_shock": -0.02,
                        "volatility_mult": 3.0,
                        "description": "COVID-19 market shock scenario"
                    },
                    "interest_rate_spike": {
                        "equity_shock": -0.15,
                        "bond_shock": -0.10,
                        "volatility_mult": 1.5,
                        "description": "Sudden interest rate increase"
                    },
                    "inflation_surge": {
                        "equity_shock": -0.20,
                        "bond_shock": -0.15,
                        "volatility_mult": 2.0,
                        "description": "Unexpected inflation surge"
                    }
                }
                
                # Run stress tests for requested scenarios
                for scenario_name in request.scenarios:
                    if scenario_name not in scenarios:
                        continue
                        
                    scenario = scenarios[scenario_name]
                    
                    # Calculate portfolio impact
                    total_impact = 0.0
                    for ticker, weight in request.weights.items():
                        # Simplified: assume all assets are equity for demo
                        # In production: classify assets and apply appropriate shocks
                        asset_impact = scenario["equity_shock"] * weight * request.portfolio_value
                        total_impact += asset_impact
                    
                    stress_results.append({
                        "scenario_name": scenario_name,
                        "description": scenario["description"],
                        "portfolio_impact": total_impact,
                        "impact_percentage": (total_impact / request.portfolio_value) * 100,
                        "final_portfolio_value": request.portfolio_value + total_impact
                    })
                
                # Calculate summary statistics
                if stress_results:
                    worst_case = min(stress_results, key=lambda x: x["portfolio_impact"])
                    best_case = max(stress_results, key=lambda x: x["portfolio_impact"])
                    avg_impact = sum(r["portfolio_impact"] for r in stress_results) / len(stress_results)
                else:
                    worst_case = best_case = {"portfolio_impact": 0, "impact_percentage": 0}
                    avg_impact = 0
                
                return models.StressTestResponse(
                    scenario_results=stress_results,
                    worst_case_loss=abs(worst_case["portfolio_impact"]),
                    worst_case_percentage=abs(worst_case["impact_percentage"]),
                    best_case_impact=best_case["portfolio_impact"],
                    average_impact=avg_impact,
                    scenarios_tested=len(stress_results)
                )
                
        except Exception as e:
            logger.error(f"Stress test error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Stress test failed: {str(e)}"
            )


@risk_router.post(
    "/var",
    response_model=models.VaRResponse,
    summary="Calculate Value-at-Risk",
)
async def calculate_value_at_risk(
    request: models.VaRRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.VaRResponse:
    """
    Calculate Value-at-Risk (VaR) and Conditional VaR.
    
    Estimates maximum potential loss at given confidence level.
    
    Args:
        request: VaR parameters
    
    Returns:
        VaR and CVaR estimates
    """
    with track_api_request("/risk/var", "POST"):
        try:
            with track_calculation("var_calculation"):
                returns_array = np.array(request.returns)
                
                # Calculate VaR using specified method
                var_result = calculate_var(
                    returns=returns_array,
                    confidence_level=request.confidence_level,
                    method=request.method,
                    portfolio_value=request.portfolio_value,
                )
                
                return models.VaRResponse(
                    var=var_result.var,
                    cvar=var_result.cvar,
                    confidence_level=request.confidence_level,
                    method=request.method,
                )
        
        except Exception as e:
            logger.error(f"VaR calculation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


@risk_router.post(
    "/stress-test",
    response_model=models.StressTestResponse,
    summary="Run portfolio stress test",
)
async def run_stress_test(
    request: models.StressTestRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.StressTestResponse:
    """
    Run stress test on portfolio.
    
    Simulates portfolio performance under extreme market conditions.
    
    Args:
        request: Stress test parameters
    
    Returns:
        Portfolio loss under stress scenario
    """
    with track_api_request("/risk/stress-test", "POST"):
        try:
            with track_calculation("stress_test"):
                # Placeholder stress test calculation
                baseline_value = 1000000.0  # $1M baseline
                
                # Apply shock based on type
                shock_multipliers = {
                    "market_crash": -0.20,  # -20%
                    "volatility_spike": -0.10,  # -10%
                    "correlation_shock": -0.08,  # -8%
                    "liquidity_crisis": -0.15,  # -15%
                }
                
                base_loss = shock_multipliers.get(request.shock_type, -0.10)
                loss_percentage = base_loss * (1 + request.shock_magnitude)
                
                stressed_value = baseline_value * (1 + loss_percentage)
                loss_amount = baseline_value - stressed_value
                
                return models.StressTestResponse(
                    baseline_value=baseline_value,
                    stressed_value=stressed_value,
                    loss_amount=loss_amount,
                    loss_percentage=abs(loss_percentage) * 100,
                    shock_type=request.shock_type,
                )
        
        except Exception as e:
            logger.error(f"Stress test failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


# =============================================================================
# Market Regime Router
# =============================================================================

regime_router = APIRouter(prefix="/regime", tags=["market-regime"])


@regime_router.post(
    "/detect",
    response_model=models.MarketRegimeResponse,
    summary="Detect market regime",
)
async def detect_market_regime(
    request: models.MarketRegimeRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.MarketRegimeResponse:
    """
    Detect current market regime using Hidden Markov Models.
    
    Identifies distinct market states based on return patterns.
    
    Args:
        request: Regime detection parameters
    
    Returns:
        Current regime and transition probabilities
    """
    with track_api_request("/regime/detect", "POST"):
        try:
            with track_calculation("regime_detection"):
                # Create a simple price series from returns
                returns = np.array(request.returns)
                prices = pd.Series(100 * np.exp(np.cumsum(returns)))
                
                # Use HMM regime detector
                result = detect_regimes_hmm(
                    prices=prices,
                    n_regimes=request.num_regimes,
                )
                
                current_regime = result.regimes[-1]
                
                # Extract regime characteristics
                characteristics = {}
                for i in range(request.num_regimes):
                    regime_mask = result.regimes == i
                    regime_returns = returns[regime_mask]
                    
                    if len(regime_returns) > 0:
                        characteristics[f"regime_{i}"] = {
                            "mean_return": float(np.mean(regime_returns)),
                            "volatility": float(np.std(regime_returns)),
                            "count": int(np.sum(regime_mask)),
                        }
                
                # Empty probabilities - return uniform distribution
                regime_probs = [1.0 / request.num_regimes] * request.num_regimes
                
                return models.MarketRegimeResponse(
                    current_regime=int(current_regime),
                    regime_probabilities=regime_probs,
                    regime_characteristics=characteristics,
                    transitions=result.transition_matrix.tolist(),
                )
        
        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


# =============================================================================
# Volatility Router  
# =============================================================================

volatility_router = APIRouter(prefix="/volatility", tags=["volatility"])


@volatility_router.post(
    "/implied",
    response_model=models.ImpliedVolatilityResponse,
    summary="Calculate implied volatility",
)
async def calculate_implied_volatility(
    request: models.ImpliedVolatilityRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.ImpliedVolatilityResponse:
    """
    Calculate implied volatility from option price.
    
    Uses Newton-Raphson method to invert Black-Scholes formula.
    
    Args:
        request: Implied volatility parameters
    
    Returns:
        Implied volatility and convergence metrics
    """
    with track_api_request("/volatility/implied", "POST"):
        try:
            with track_calculation("implied_volatility"):
                # Use implied_volatility function
                iv = implied_volatility(
                    option_price=request.option_price,
                    spot=request.spot_price,
                    strike=request.strike_price,
                    T=request.time_to_maturity,
                    r=request.risk_free_rate,
                    option_type=request.option_type.value,
                    q=0.0,  # Dividend yield
                    initial_guess=request.initial_guess,
                    tol=1e-6,
                    max_iterations=100,
                )
                
                return models.ImpliedVolatilityResponse(
                    implied_volatility=iv,
                    iterations=10,  # Placeholder
                    convergence_error=1e-7,  # Placeholder
                )
        
        except Exception as e:
            logger.error(f"Implied volatility calculation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


@volatility_router.post(
    "/surface",
    response_model=models.VolatilitySurfaceResponse,
    summary="Build volatility surface",
)
async def build_volatility_surface(
    request: models.VolatilitySurfaceRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.VolatilitySurfaceResponse:
    """
    Build volatility surface from option data.
    
    Constructs 2D surface of implied volatilities across strikes and maturities.
    
    Args:
        request: Volatility surface parameters
    
    Returns:
        Volatility surface data and skew metrics
    """
    with track_api_request("/volatility/surface", "POST"):
        try:
            with track_calculation("volatility_surface"):
                # Placeholder: generate sample volatility surface
                surface = []
                for maturity in request.maturities:
                    row = []
                    for strike in request.strikes:
                        # Simple volatility smile model
                        moneyness = strike / request.spot_price
                        base_vol = 0.2  # 20% base vol
                        smile = 0.1 * (moneyness - 1.0) ** 2  # Parabolic smile
                        vol = base_vol + smile
                        row.append(vol)
                    surface.append(row)
                
                atm_vols = [row[len(row) // 2] for row in surface]
                
                skew = {
                    "25_delta_skew": 0.05,
                    "10_delta_skew": 0.08,
                    "slope": -0.02,
                }
                
                return models.VolatilitySurfaceResponse(
                    surface=surface,
                    maturities=request.maturities,
                    strikes=request.strikes,
                    atm_volatilities=atm_vols,
                    skew=skew,
                )
        
        except Exception as e:
            logger.error(f"Volatility surface construction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


# =============================================================================
# Macro Analysis Router
# =============================================================================

macro_router = APIRouter(prefix="/macro", tags=["macro"])


@macro_router.post(
    "/regime",
    response_model=models.MacroRegimeResponse,
    summary="Detect macro regime",
)
async def detect_macroeconomic_regime(
    request: models.MacroRegimeRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.MacroRegimeResponse:
    """
    Detect macroeconomic regime.
    
    Classifies macro environment as expansion, slowdown, recession, or recovery.
    
    Args:
        request: Macro indicators
    
    Returns:
        Macro regime classification and recession probability
    """
    with track_api_request("/macro/regime", "POST"):
        try:
            with track_calculation("macro_regime"):
                # Use macro regime detection from macro module
                regime = detect_macro_regime(
                    gdp_growth=request.gdp_growth[-1] if request.gdp_growth else 2.0,
                    unemployment=request.unemployment_rate[-1] if request.unemployment_rate else 4.0,
                    pmi=request.pmi[-1] if request.pmi else 52.0,
                )
                
                # Calculate recession probability (simplified)
                recession_prob = min(0.5, max(0.0, (5.0 - (request.gdp_growth[-1] if request.gdp_growth else 2.0)) / 10.0))
                
                indicators = {
                    "gdp_growth": request.gdp_growth[-1] if request.gdp_growth else 2.0,
                    "unemployment": request.unemployment_rate[-1] if request.unemployment_rate else 4.0,
                    "pmi": request.pmi[-1] if request.pmi else 52.0,
                }
                
                return models.MacroRegimeResponse(
                    current_regime=regime.name,
                    regime_score=0.75,
                    indicators=indicators,
                    recession_probability=recession_prob,
                )
        
        except Exception as e:
            logger.error(f"Macro regime detection failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


@macro_router.post(
    "/correlation",
    response_model=models.CorrelationAnalysisResponse,
    summary="Analyze correlations",
)
async def analyze_correlations(
    request: models.CorrelationAnalysisRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.CorrelationAnalysisResponse:
    """
    Analyze cross-asset correlations.
    
    Computes correlation matrix and detects correlation regimes.
    
    Args:
        request: Returns data for multiple assets
    
    Returns:
        Correlation matrix, regime, and diversification metrics
    """
    with track_api_request("/macro/correlation", "POST"):
        try:
            with track_calculation("correlation_analysis"):
                # Convert to numpy array
                assets = list(request.returns_data.keys())
                returns_matrix = np.array([
                    request.returns_data[asset]
                    for asset in assets
                ]).T
                
                # Calculate correlation matrix
                corr_matrix = np.corrcoef(returns_matrix.T)
                
                # Calculate average correlation
                n = len(assets)
                avg_corr = (corr_matrix.sum() - n) / (n * (n - 1))
                
                # Determine regime based on average correlation
                regime = correlation_regime(avg_corr)
                
                # Calculate eigenvalues for concentration
                eigenvalues = np.linalg.eigvalsh(corr_matrix)
                eigenvalues = sorted(eigenvalues, reverse=True)
                eigenvalue_concentration = eigenvalues[0] / sum(eigenvalues)
                
                # Diversification ratio (simplified)
                diversification_ratio = 1.0 / (1.0 + avg_corr)
                
                return models.CorrelationAnalysisResponse(
                    correlation_matrix=corr_matrix.tolist(),
                    regime=regime.name,
                    avg_correlation=float(avg_corr),
                    eigenvalue_concentration=float(eigenvalue_concentration),
                    diversification_ratio=float(diversification_ratio),
                )
        
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


@macro_router.post(
    "/sentiment",
    response_model=models.SentimentAnalysisResponse,
    summary="Analyze market sentiment",
)
async def analyze_market_sentiment(
    request: models.SentimentAnalysisRequest,
    _: Annotated[None, Depends(deps.check_rate_limit)],
) -> models.SentimentAnalysisResponse:
    """
    Analyze market sentiment from multiple indicators.
    
    Combines VIX, put/call ratio, breadth indicators into sentiment index.
    
    Args:
        request: Sentiment indicators
    
    Returns:
        Sentiment regime and fear/greed index
    """
    with track_api_request("/macro/sentiment", "POST"):
        try:
            with track_calculation("sentiment_analysis"):
                # Calculate fear/greed index components
                components = {}
                
                if request.vix_level is not None:
                    vix_score = max(0, min(100, (50 - request.vix_level) * 2))
                    components["vix"] = vix_score
                    sentiment_regime_vix = vix_sentiment_level(request.vix_level)
                else:
                    vix_score = 50
                    sentiment_regime_vix = "NEUTRAL"
                
                # Calculate composite fear/greed index
                fg_index = fear_greed_index(
                    vix=request.vix_level or 15.0,
                    put_call_ratio=request.put_call_ratio or 1.0,
                    advancing=request.advance_decline or 0,
                    declining=abs(request.advance_decline or 0) if (request.advance_decline or 0) < 0 else 0,
                    new_highs=request.new_highs or 50,
                    new_lows=request.new_lows or 50,
                )
                
                # Determine contrarian signal
                if fg_index > 75:
                    contrarian = "sell"
                elif fg_index < 25:
                    contrarian = "buy"
                else:
                    contrarian = "neutral"
                
                return models.SentimentAnalysisResponse(
                    sentiment_regime=sentiment_regime_vix,
                    fear_greed_index=fg_index,
                    contrarian_signal=contrarian,
                    components=components,
                )
        
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


# =============================================================================
# All Routers Collection
# =============================================================================

all_routers = [
    portfolio_router,
    options_router,
    risk_router,
    regime_router,
    volatility_router,
    macro_router,
]
