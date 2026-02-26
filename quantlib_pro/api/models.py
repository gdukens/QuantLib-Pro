"""
Pydantic models for API request/response validation.

Week 11: API Layer - Data models for all quantitative finance endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Common Models
# =============================================================================

class AssetClass(str, Enum):
    """Asset class enumeration."""
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    COMMODITY = "commodity"
    FX = "fx"
    CRYPTO = "crypto"


class OptionType(str, Enum):
    """Option type enumeration."""
    CALL = "call"
    PUT = "put"


class Status(BaseModel):
    """Generic status response."""
    status: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Portfolio Models
# =============================================================================

class PortfolioWeights(BaseModel):
    """Portfolio asset weights."""
    weights: Dict[str, float] = Field(..., description="Asset weights (ticker -> weight)")
    
    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate weights sum to 1.0."""
        total = sum(v.values())
        if not 0.99 <= total <= 1.01:  # Allow small numerical errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class OptimizationRequest(BaseModel):
    """Portfolio optimization request."""
    tickers: List[str] = Field(..., min_length=2, description="List of asset tickers")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    risk_free_rate: float = Field(default=0.02, ge=0, le=1, description="Risk-free rate")
    target_return: Optional[float] = Field(None, ge=0, description="Target return for optimization")
    constraints: Optional[Dict[str, float]] = Field(None, description="Weight constraints")


class OptimizationResponse(BaseModel):
    """Portfolio optimization result."""
    optimal_weights: Dict[str, float] = Field(..., description="Optimal asset weights")
    expected_return: float = Field(..., description="Expected portfolio return")
    volatility: float = Field(..., description="Portfolio volatility (std dev)")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EfficientFrontierRequest(BaseModel):
    """Efficient frontier calculation request."""
    tickers: List[str] = Field(..., min_length=2, description="List of asset tickers")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    risk_free_rate: float = Field(default=0.02, ge=0, le=1)
    num_points: int = Field(default=50, ge=10, le=200, description="Number of frontier points")


class EfficientFrontierResponse(BaseModel):
    """Efficient frontier result."""
    returns: List[float] = Field(..., description="Portfolio returns")
    volatilities: List[float] = Field(..., description="Portfolio volatilities")
    sharpe_ratios: List[float] = Field(..., description="Sharpe ratios")
    weights: List[Dict[str, float]] = Field(..., description="Optimal weights for each point")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Options Pricing Models
# =============================================================================

class BlackScholesRequest(BaseModel):
    """Black-Scholes pricing request."""
    spot_price: float = Field(..., gt=0, description="Current spot price")
    strike_price: float = Field(..., gt=0, description="Strike price")
    time_to_expiry: float = Field(..., gt=0, description="Time to expiry in years")
    risk_free_rate: float = Field(..., ge=-0.1, le=1.0, description="Risk-free rate (annual)")
    volatility: float = Field(..., gt=0, le=5.0, description="Volatility (annual)")
    option_type: OptionType = Field(..., description="Call or put option")


class BlackScholesResponse(BaseModel):
    """Black-Scholes pricing result."""
    option_price: float = Field(..., description="Option price")
    delta: float = Field(..., description="Price sensitivity to spot (Delta)")
    gamma: float = Field(..., description="Delta sensitivity to spot (Gamma)")
    vega: float = Field(..., description="Price sensitivity to volatility (Vega)")
    theta: float = Field(..., description="Price decay over time (Theta)")
    rho: float = Field(..., description="Price sensitivity to interest rate (Rho)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ImpliedVolatilityRequest(BaseModel):
    """Implied volatility calculation request."""
    market_price: float = Field(..., gt=0, description="Observed market price")
    spot_price: float = Field(..., gt=0, description="Current spot price")
    strike_price: float = Field(..., gt=0, description="Strike price")
    time_to_expiry: float = Field(..., gt=0, description="Time to expiry in years")
    risk_free_rate: float = Field(..., ge=-0.1, le=1.0, description="Risk-free rate")
    option_type: OptionType = Field(..., description="Call or put option")



# =============================================================================
# Risk Analytics Models
# =============================================================================

class VaRMethod(str, Enum):
    """Value at Risk calculation methods."""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


class VaRRequest(BaseModel):
    """Value at Risk calculation request."""
    tickers: List[str] = Field(..., min_length=1, description="Portfolio asset tickers")
    weights: Dict[str, float] = Field(..., description="Portfolio weights (ticker -> weight)")
    portfolio_value: float = Field(..., gt=0, description="Total portfolio value")
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.999, description="VaR confidence level")
    holding_period_days: int = Field(default=1, ge=1, le=30, description="Holding period in days")
    method: VaRMethod = Field(default=VaRMethod.HISTORICAL, description="VaR calculation method")
    
    @field_validator("weights")
    @classmethod
    def validate_weights_sum(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate weights sum approximately to 1.0."""
        total = sum(v.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class VaRResponse(BaseModel):
    """Value at Risk calculation result."""
    var_amount: float = Field(..., description="VaR in portfolio currency units")
    var_percentage: float = Field(..., description="VaR as percentage of portfolio")
    cvar_amount: float = Field(..., description="Conditional VaR (Expected Shortfall)")
    cvar_percentage: float = Field(..., description="CVaR as percentage of portfolio")
    confidence_level: float = Field(..., description="Confidence level used")
    method: str = Field(..., description="Calculation method used")
    holding_period_days: int = Field(..., description="Holding period in days")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StressTestRequest(BaseModel):
    """Portfolio stress test request."""
    tickers: List[str] = Field(..., min_length=1, description="Portfolio asset tickers")
    weights: Dict[str, float] = Field(..., description="Portfolio weights")
    portfolio_value: float = Field(..., gt=0, description="Total portfolio value")
    scenarios: List[str] = Field(
        default=["market_crash_2008", "covid_2020", "interest_rate_spike"],
        description="Stress scenarios to test"
    )


class StressTestResponse(BaseModel):
    """Portfolio stress test result."""
    scenario_results: List[Dict[str, Any]] = Field(..., description="Individual scenario results")
    worst_case_loss: float = Field(..., description="Maximum potential loss")
    worst_case_percentage: float = Field(..., description="Worst case as percentage")
    best_case_impact: float = Field(..., description="Best case scenario impact")
    average_impact: float = Field(..., description="Average impact across scenarios")
    scenarios_tested: int = Field(..., description="Number of scenarios tested")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    strike_price: float = Field(..., gt=0, description="Strike price")
    time_to_maturity: float = Field(..., gt=0, le=30, description="Time to maturity (years)")
    risk_free_rate: float = Field(..., ge=-0.1, le=1, description="Risk-free rate")
    volatility: float = Field(..., gt=0, le=5, description="Volatility (annualized)")
    option_type: OptionType = Field(..., description="Option type (call/put)")
    dividend_yield: float = Field(default=0.0, ge=0, le=1, description="Dividend yield")


class BlackScholesResponse(BaseModel):
    """Black-Scholes pricing result."""
    option_price: float = Field(..., description="Option price")
    delta: float = Field(..., description="Delta (price sensitivity)")
    gamma: float = Field(..., description="Gamma (delta sensitivity)")
    vega: float = Field(..., description="Vega (volatility sensitivity)")
    theta: float = Field(..., description="Theta (time decay)")
    rho: float = Field(..., description="Rho (rate sensitivity)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MonteCarloOptionRequest(BaseModel):
    """Monte Carlo option pricing request."""
    spot_price: float = Field(..., gt=0)
    strike_price: float = Field(..., gt=0)
    time_to_maturity: float = Field(..., gt=0, le=30)
    risk_free_rate: float = Field(..., ge=-0.1, le=1)
    volatility: float = Field(..., gt=0, le=5)
    option_type: OptionType
    num_simulations: int = Field(default=10000, ge=1000, le=1000000)
    num_steps: int = Field(default=252, ge=10, le=1000)
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")


class MonteCarloOptionResponse(BaseModel):
    """Monte Carlo option pricing result."""
    option_price: float
    confidence_interval_95: tuple[float, float] = Field(..., description="95% confidence interval")
    standard_error: float
    num_simulations: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Risk Analysis Models
# =============================================================================

class VaRRequest(BaseModel):
    """Value-at-Risk calculation request."""
    returns: List[float] = Field(..., min_length=30, description="Historical returns")
    confidence_level: float = Field(default=0.95, ge=0.9, le=0.99, description="Confidence level")
    method: str = Field(default="historical", pattern="^(historical|parametric|monte_carlo)$")
    holding_period: int = Field(default=1, ge=1, le=252, description="Holding period (days)")
    portfolio_value: Optional[float] = Field(None, gt=0, description="Portfolio value")


class VaRResponse(BaseModel):
    """VaR calculation result."""
    var: float = Field(..., description="Value-at-Risk")
    cvar: float = Field(..., description="Conditional VaR (Expected Shortfall)")
    confidence_level: float
    method: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StressTestRequest(BaseModel):
    """Stress test request."""
    portfolio_weights: Dict[str, float] = Field(..., description="Portfolio weights")
    tickers: List[str] = Field(..., min_length=1)
    shock_magnitude: float = Field(..., ge=-1, le=1, description="Shock magnitude (-1 to 1)")
    shock_type: str = Field(default="market_crash", pattern="^(market_crash|volatility_spike|correlation_shock|liquidity_crisis)$")


class StressTestResponse(BaseModel):
    """Stress test result."""
    baseline_value: float = Field(..., description="Pre-shock portfolio value")
    stressed_value: float = Field(..., description="Post-shock portfolio value")
    loss_amount: float = Field(..., description="Loss amount")
    loss_percentage: float = Field(..., description="Loss percentage")
    shock_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Market Regime Models
# =============================================================================

class MarketRegimeRequest(BaseModel):
    """Market regime detection request."""
    returns: List[float] = Field(..., min_length=100, description="Historical returns")
    num_regimes: int = Field(default=3, ge=2, le=5, description="Number of regimes")
    method: str = Field(default="hmm", pattern="^(hmm|clustering|volatility)$")


class MarketRegimeResponse(BaseModel):
    """Market regime detection result."""
    current_regime: int = Field(..., description="Current regime (0-indexed)")
    regime_probabilities: List[float] = Field(..., description="Probabilities for each regime")
    regime_characteristics: Dict[str, Dict[str, float]] = Field(..., description="Regime properties")
    transitions: List[List[float]] = Field(..., description="Transition matrix")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Volatility Surface Models
# =============================================================================

class VolatilitySurfaceRequest(BaseModel):
    """Volatility surface construction request."""
    ticker: str = Field(..., min_length=1, description="Underlying ticker")
    maturities: List[float] = Field(..., min_length=3, description="Option maturities (years)")
    strikes: List[float] = Field(..., min_length=5, description="Strike prices")
    spot_price: float = Field(..., gt=0, description="Current spot price")


class VolatilitySurfaceResponse(BaseModel):
    """Volatility surface result."""
    surface: List[List[float]] = Field(..., description="Volatility surface (maturities x strikes)")
    maturities: List[float]
    strikes: List[float]
    atm_volatilities: List[float] = Field(..., description="ATM vols for each maturity")
    skew: Dict[str, float] = Field(..., description="Skew metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ImpliedVolatilityRequest(BaseModel):
    """Implied volatility calculation request."""
    option_price: float = Field(..., gt=0, description="Observed option price")
    spot_price: float = Field(..., gt=0)
    strike_price: float = Field(..., gt=0)
    time_to_maturity: float = Field(..., gt=0, le=30)
    risk_free_rate: float = Field(..., ge=-0.1, le=1)
    option_type: OptionType
    initial_guess: float = Field(default=0.2, gt=0, le=5)


class ImpliedVolatilityResponse(BaseModel):
    """Implied volatility result."""
    implied_volatility: float = Field(..., description="Implied volatility")
    iterations: int = Field(..., description="Solver iterations")
    convergence_error: float = Field(..., description="Final convergence error")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Macro Analysis Models
# =============================================================================

class MacroRegimeRequest(BaseModel):
    """Macro regime detection request."""
    gdp_growth: Optional[List[float]] = Field(None, description="GDP growth rates")
    unemployment_rate: Optional[List[float]] = Field(None, description="Unemployment rates")
    pmi: Optional[List[float]] = Field(None, description="PMI readings")
    inflation: Optional[List[float]] = Field(None, description="Inflation rates")


class MacroRegimeResponse(BaseModel):
    """Macro regime detection result."""
    current_regime: str = Field(..., description="Current macro regime")
    regime_score: float = Field(..., description="Regime confidence score")
    indicators: Dict[str, float] = Field(..., description="Key indicator values")
    recession_probability: float = Field(..., description="Recession probability (0-1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CorrelationAnalysisRequest(BaseModel):
    """Correlation analysis request."""
    returns_data: Dict[str, List[float]] = Field(..., description="Returns for multiple assets")
    window: int = Field(default=60, ge=20, le=500, description="Rolling window size")
    method: str = Field(default="pearson", pattern="^(pearson|spearman|kendall)$")


class CorrelationAnalysisResponse(BaseModel):
    """Correlation analysis result."""
    correlation_matrix: List[List[float]] = Field(..., description="Current correlation matrix")
    regime: str = Field(..., description="Correlation regime (calm/stress/crisis)")
    avg_correlation: float = Field(..., description="Average pairwise correlation")
    eigenvalue_concentration: float = Field(..., description="First eigenvalue concentration")
    diversification_ratio: float = Field(..., description="Diversification ratio")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SentimentAnalysisRequest(BaseModel):
    """Market sentiment analysis request."""
    vix_level: Optional[float] = Field(None, ge=0, le=100, description="VIX level")
    put_call_ratio: Optional[float] = Field(None, ge=0, description="Put/call ratio")
    advance_decline: Optional[int] = Field(None, description="Advancing - declining stocks")
    new_highs: Optional[int] = Field(None, ge=0, description="52-week new highs")
    new_lows: Optional[int] = Field(None, ge=0, description="52-week new lows")


class SentimentAnalysisResponse(BaseModel):
    """Market sentiment analysis result."""
    sentiment_regime: str = Field(..., description="Sentiment regime")
    fear_greed_index: float = Field(..., description="Fear/greed index (0-100)")
    contrarian_signal: str = Field(..., description="Contrarian signal (buy/sell/neutral)")
    components: Dict[str, float] = Field(..., description="Sentiment component scores")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Execution Simulation Models
# =============================================================================

class ExecutionRequest(BaseModel):
    """Order execution simulation request."""
    ticker: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0, description="Order quantity")
    side: str = Field(..., pattern="^(buy|sell)$")
    execution_style: str = Field(default="VWAP", pattern="^(VWAP|TWAP|POV|market)$")
    time_horizon_minutes: int = Field(default=60, ge=1, le=1440)
    participation_rate: float = Field(default=0.1, ge=0.01, le=0.5, description="Max % of volume")


class ExecutionResponse(BaseModel):
    """Execution simulation result."""
    average_price: float = Field(..., description="Average execution price")
    total_cost: float = Field(..., description="Total execution cost")
    slippage_bps: float = Field(..., description="Slippage in basis points")
    market_impact_bps: float = Field(..., description="Market impact in bps")
    execution_shortfall: float = Field(..., description="Implementation shortfall")
    num_trades: int = Field(..., description="Number of child orders")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Data Models
# =============================================================================

class DataRequest(BaseModel):
    """Market data request."""
    tickers: List[str] = Field(..., min_length=1, max_length=50)
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    fields: List[str] = Field(default=["close"], description="Data fields")
    frequency: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")


class DataResponse(BaseModel):
    """Market data response."""
    data: Dict[str, List[float]] = Field(..., description="Time series data")
    dates: List[str] = Field(..., description="Date index")
    metadata: Dict[str, str] = Field(..., description="Data metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Error Models
# =============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type")
    detail: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationError(BaseModel):
    """Validation error detail."""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    invalid_value: Optional[Any] = Field(None, description="Invalid value")
