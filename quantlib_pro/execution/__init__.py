"""
Execution simulation suite.

Provides:
  - Order book simulation with realistic microstructure
  - Market impact models (Almgren-Chriss, Kyle, JPM, square-root)
  - Execution strategies (VWAP, TWAP, POV)
  - Slippage and execution cost analysis
  - Backtesting framework for strategy evaluation
"""

from .order_book import (
    Order,
    Trade,
    OrderBookSnapshot,
    OrderBookSimulator,
)

from .market_impact import (
    ImpactModel,
    MarketImpactResult,
    almgren_chriss_impact,
    kyle_lambda_impact,
    jpm_impact,
    square_root_impact,
    estimate_slippage,
)

from .strategies import (
    ExecutionSchedule,
    ExecutionResult,
    twap_schedule,
    vwap_schedule,
    pov_schedule,
    simulate_execution,
    intraday_volume_profile,
)

from .backtesting import (
    Trade as BacktestTrade,
    Position,
    BacktestResult,
    Strategy,
    BacktestEngine,
    MovingAverageCrossover,
    MeanReversionStrategy,
    MomentumStrategy,
)

__all__ = [
    # Order book
    "Order",
    "Trade",
    "OrderBookSnapshot",
    "OrderBookSimulator",
    # Market impact
    "ImpactModel",
    "MarketImpactResult",
    "almgren_chriss_impact",
    "kyle_lambda_impact",
    "jpm_impact",
    "square_root_impact",
    "estimate_slippage",
    # Strategies
    "ExecutionSchedule",
    "ExecutionResult",
    "twap_schedule",
    "vwap_schedule",
    "pov_schedule",
    "simulate_execution",
    "intraday_volume_profile",
    # Backtesting
    "BacktestTrade",
    "Position",
    "BacktestResult",
    "Strategy",
    "BacktestEngine",
    "MovingAverageCrossover",
    "MeanReversionStrategy",
    "MomentumStrategy",
]
