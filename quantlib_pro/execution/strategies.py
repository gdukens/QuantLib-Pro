"""
Execution algorithms for optimal order placement.

Implements standard institutional execution strategies:
  - VWAP (Volume-Weighted Average Price)
  - TWAP (Time-Weighted Average Price)
  - POV (Percent of Volume)
  - Implementation Shortfall (IS)

These strategies split large orders into smaller child orders
to minimize market impact and tracking error.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from quantlib_pro.execution.market_impact import MarketImpactResult, square_root_impact
from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


@dataclass
class ExecutionSchedule:
    """Execution schedule for a parent order."""
    timestamps: np.ndarray  # Time of each child order
    sizes: np.ndarray  # Size of each child order
    strategy: str  # Strategy name
    total_size: int  # Total parent order size
    
    def __post_init__(self):
        assert len(self.timestamps) == len(self.sizes)
        assert self.sizes.sum() == self.total_size
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame."""
        return pd.DataFrame({
            'timestamp': self.timestamps,
            'size': self.sizes,
            'strategy': self.strategy,
        })


@dataclass
class ExecutionResult:
    """Results from executing a strategy."""
    schedule: ExecutionSchedule
    vwap: float  # Volume-weighted average price
    arrival_price: float  # Benchmark price at start
    slippage: float  # VWAP - arrival_price (in price units)
    slippage_bps: float  # Slippage in basis points
    total_cost: float  # Total execution cost ($)
    market_impact: Optional[MarketImpactResult] = None
    
    def summary(self) -> str:
        return (
            f"Execution Summary ({self.schedule.strategy}):\n"
            f"  VWAP: ${self.vwap:.4f}\n"
            f"  Arrival Price: ${self.arrival_price:.4f}\n"
            f"  Slippage: {self.slippage_bps:.2f} bps\n"
            f"  Total Cost: ${self.total_cost:,.2f}\n"
            f"  Number of Slices: {len(self.schedule.sizes)}"
        )


def twap_schedule(
    order_size: int,
    duration: float,
    n_slices: int,
) -> ExecutionSchedule:
    """
    Generate Time-Weighted Average Price (TWAP) schedule.

    Splits order evenly across time intervals.
    
    Parameters
    ----------
    order_size : int
        Total order size (shares)
    duration : float
        Total execution duration (seconds)
    n_slices : int
        Number of time slices
    
    Returns
    -------
    ExecutionSchedule
        Equal-sized slices at regular intervals
    """
    require_positive(order_size, "order_size")
    require_positive(duration, "duration")
    require_positive(n_slices, "n_slices")
    
    # Equal time intervals
    timestamps = np.linspace(0, duration, n_slices)
    
    # Equal sizes
    base_size = order_size // n_slices
    remainder = order_size % n_slices
    sizes = np.full(n_slices, base_size)
    sizes[:remainder] += 1  # Distribute remainder
    
    return ExecutionSchedule(
        timestamps=timestamps,
        sizes=sizes,
        strategy='TWAP',
        total_size=order_size,
    )


def vwap_schedule(
    order_size: int,
    duration: float,
    volume_profile: np.ndarray,
) -> ExecutionSchedule:
    """
    Generate Volume-Weighted Average Price (VWAP) schedule.

    Slices order proportionally to expected volume distribution.
    
    Parameters
    ----------
    order_size : int
        Total order size (shares)
    duration : float
        Total execution duration (seconds)
    volume_profile : np.ndarray
        Expected volume distribution (normalized to sum to 1)
    
    Returns
    -------
    ExecutionSchedule
        Slices weighted by volume profile
    """
    require_positive(order_size, "order_size")
    require_positive(duration, "duration")
    
    if len(volume_profile) == 0:
        raise ValidationError("volume_profile must not be empty")
    
    # Normalize volume profile
    volume_profile = np.array(volume_profile)
    volume_profile = volume_profile / volume_profile.sum()
    
    n_slices = len(volume_profile)
    timestamps = np.linspace(0, duration, n_slices)
    
    # Allocate sizes proportional to volume
    sizes_float = order_size * volume_profile
    sizes = np.round(sizes_float).astype(int)
    
    # Adjust for rounding errors
    diff = order_size - sizes.sum()
    if diff > 0:
        # Add to largest slices
        idx = np.argsort(sizes_float - sizes)[-diff:]
        sizes[idx] += 1
    elif diff < 0:
        # Remove from largest slices
        idx = np.argsort(sizes_float - sizes)[:abs(diff)]
        sizes[idx] -= 1
    
    return ExecutionSchedule(
        timestamps=timestamps,
        sizes=sizes,
        strategy='VWAP',
        total_size=order_size,
    )


def pov_schedule(
    order_size: int,
    duration: float,
    n_slices: int,
    target_pov: float = 0.1,
    volume_profile: Optional[np.ndarray] = None,
) -> ExecutionSchedule:
    """
    Generate Percent of Volume (POV) schedule.

    Trades at a constant percentage of market volume.
    
    Parameters
    ----------
    order_size : int
        Total order size (shares)
    duration : float
        Total execution duration (seconds)
    n_slices : int
        Number of time slices
    target_pov : float
        Target participation rate (e.g., 0.1 = 10% of volume)
    volume_profile : np.ndarray, optional
        Expected volume profile. If None, assumes uniform.
    
    Returns
    -------
    ExecutionSchedule
        POV-based schedule
    """
    require_positive(order_size, "order_size")
    require_positive(duration, "duration")
    require_positive(n_slices, "n_slices")
    
    if not 0 < target_pov <= 1:
        raise ValidationError(f"target_pov must be in (0, 1], got {target_pov}")
    
    timestamps = np.linspace(0, duration, n_slices)
    
    if volume_profile is None:
        # Assume uniform volume
        volume_profile = np.ones(n_slices)
    
    volume_profile = np.array(volume_profile)
    
    # Trade at target_pov of each interval's volume
    sizes_float = target_pov * volume_profile
    sizes_float = sizes_float / sizes_float.sum() * order_size
    
    sizes = np.round(sizes_float).astype(int)
    
    # Adjust for rounding
    diff = order_size - sizes.sum()
    if diff != 0:
        sizes[0] += diff
    
    return ExecutionSchedule(
        timestamps=timestamps,
        sizes=sizes,
        strategy='POV',
        total_size=order_size,
    )


def simulate_execution(
    schedule: ExecutionSchedule,
    arrival_price: float,
    volatility: float = 0.02,
    daily_volume: float = 1_000_000,
    price_path: Optional[np.ndarray] = None,
) -> ExecutionResult:
    """
    Simulate execution of a schedule and calculate costs.

    Parameters
    ----------
    schedule : ExecutionSchedule
        Execution schedule
    arrival_price : float
        Benchmark price at start
    volatility : float
        Daily volatility for impact estimation
    daily_volume : float
        Average daily volume
    price_path : np.ndarray, optional
        Simulated price path. If None, generates random walk.
    
    Returns
    -------
    ExecutionResult
        Execution metrics including VWAP and slippage
    """
    n_slices = len(schedule.sizes)
    
    # Generate price path if not provided
    if price_path is None:
        dt = schedule.timestamps[1] - schedule.timestamps[0] if n_slices > 1 else 1.0
        returns = np.random.normal(0, volatility * np.sqrt(dt / 252), n_slices)
        price_path = arrival_price * np.exp(np.cumsum(returns))
    
    # Calculate execution prices (with market impact)
    execution_prices = []
    for i, size in enumerate(schedule.sizes):
        base_price = price_path[i] if i < len(price_path) else arrival_price
        
        # Add market impact (convert numpy int to Python int)
        impact = square_root_impact(
            order_size=int(size),
            daily_volume=daily_volume,
            volatility=volatility,
            arrival_price=base_price,
        )
        
        # Execution price includes impact
        exec_price = base_price * (1 + impact.total_impact / 10000)
        execution_prices.append(exec_price)
    
    execution_prices = np.array(execution_prices)
    
    # Calculate VWAP
    vwap = np.sum(execution_prices * schedule.sizes) / schedule.total_size
    
    # Calculate slippage
    slippage = vwap - arrival_price
    slippage_bps = (slippage / arrival_price) * 10000
    
    # Total cost
    total_cost = abs(slippage) * schedule.total_size
    
    # Overall market impact
    market_impact = square_root_impact(
        order_size=schedule.total_size,
        daily_volume=daily_volume,
        volatility=volatility,
        arrival_price=arrival_price,
    )
    
    return ExecutionResult(
        schedule=schedule,
        vwap=vwap,
        arrival_price=arrival_price,
        slippage=slippage,
        slippage_bps=slippage_bps,
        total_cost=total_cost,
        market_impact=market_impact,
    )


def intraday_volume_profile(profile_type: str = 'u_shaped', n_points: int = 100) -> np.ndarray:
    """
    Generate typical intraday volume profile.

    Parameters
    ----------
    profile_type : str
        'u_shaped' (morning/afternoon peaks) or 'flat'
    n_points : int
        Number of intraday points
    
    Returns
    -------
    np.ndarray
        Normalized volume profile
    """
    if profile_type == 'u_shaped':
        # U-shaped: high volume at open/close, low at midday
        x = np.linspace(0, 1, n_points)
        # Quadratic U-shape: high at 0 and 1, low at 0.5
        profile = 2 * (x - 0.5) ** 2 + 0.5
    elif profile_type == 'flat':
        profile = np.ones(n_points)
    else:
        raise ValidationError(f"Unknown profile_type: {profile_type}")
    
    return profile / profile.sum()
