"""
Market impact models for execution cost estimation.

Implements academic and practitioner models:
  - Almgren-Chriss (2000) — square-root impact
  - Kyle's lambda (1985) — linear price impact
  - JPM model — temporary + permanent impact decomposition
  - Obizhaeva-Wang (2013) — propagator model

Market impact is the price deviation caused by trading,
decomposed into:
  - Temporary impact: immediate, mean-reverting
  - Permanent impact: persistent information leakage
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import numpy as np

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


class ImpactModel(Enum):
    """Market impact model types."""
    ALMGREN_CHRISS = "almgren_chriss"
    KYLE_LAMBDA = "kyle_lambda"
    JPM = "jpm"
    LINEAR = "linear"
    SQUARE_ROOT = "square_root"


@dataclass
class MarketImpactResult:
    """Results from market impact calculation."""
    temporary_impact: float  # Temporary price impact (bps)
    permanent_impact: float  # Permanent price impact (bps)
    total_impact: float  # Total impact (bps)
    execution_cost: float  # Dollar cost
    arrival_price: float  # Reference price
    average_price: float  # VWAP including impact
    
    def summary(self) -> str:
        return (
            f"Market Impact Summary:\n"
            f"  Temporary Impact: {self.temporary_impact:.2f} bps\n"
            f"  Permanent Impact: {self.permanent_impact:.2f} bps\n"
            f"  Total Impact: {self.total_impact:.2f} bps\n"
            f"  Execution Cost: ${self.execution_cost:,.2f}\n"
            f"  Arrival Price: ${self.arrival_price:.2f}\n"
            f"  Average Price: ${self.average_price:.2f}"
        )


def almgren_chriss_impact(
    order_size: float,
    daily_volume: float,
    volatility: float,
    participation_rate: float = 0.1,
    gamma: float = 0.1,
    eta: float = 2.5e-7,
) -> MarketImpactResult:
    """
    Almgren-Chriss (2000) market impact model.

    Models temporary and permanent impact with square-root scaling.
    
    Temporary impact: η * σ * (v / V)^(1/2)
    Permanent impact: γ * σ * (x / V)
    
    Parameters
    ----------
    order_size : float
        Total order size (shares)
    daily_volume : float
        Average daily volume (shares)
    volatility : float
        Daily volatility (e.g., 0.02 for 2%)
    participation_rate : float
        Trade participation in daily volume (e.g., 0.1 = 10%)
    gamma : float
        Permanent impact coefficient
    eta : float
        Temporary impact coefficient
    
    Returns
    -------
    MarketImpactResult
        Impact estimates in basis points
    """
    require_positive(order_size, "order_size")
    require_positive(daily_volume, "daily_volume")
    require_positive(volatility, "volatility")
    
    # Volume fraction
    volume_fraction = order_size / daily_volume
    
    # Temporary impact (in price units)
    # η * σ * sqrt(v/V) where v is trade rate
    temp_impact = eta * volatility * np.sqrt(participation_rate)
    
    # Permanent impact (in price units)
    # γ * (x / V) where x is total shares
    perm_impact = gamma * volume_fraction
    
    # Convert to basis points (assuming arrival_price = 1 for simplicity)
    temp_impact_bps = temp_impact * 10000
    perm_impact_bps = perm_impact * 10000
    total_impact_bps = temp_impact_bps + perm_impact_bps
    
    # Assume arrival price = $100 for cost calculation
    arrival_price = 100.0
    execution_cost = (temp_impact + perm_impact) * arrival_price * order_size
    average_price = arrival_price * (1 + temp_impact + perm_impact)
    
    return MarketImpactResult(
        temporary_impact=temp_impact_bps,
        permanent_impact=perm_impact_bps,
        total_impact=total_impact_bps,
        execution_cost=execution_cost,
        arrival_price=arrival_price,
        average_price=average_price,
    )


def kyle_lambda_impact(
    order_size: float,
    kyle_lambda: float,
    arrival_price: float = 100.0,
) -> MarketImpactResult:
    """
    Kyle's lambda (1985) linear impact model.

    Price impact = λ * order_size
    
    Kyle's lambda measures the price impact per unit volume,
    typically estimated from regression of price changes on volume.
    
    Parameters
    ----------
    order_size : float
        Order size (shares)
    kyle_lambda : float
        Kyle's lambda coefficient ($/share)
    arrival_price : float
        Arrival price
    
    Returns
    -------
    MarketImpactResult
        Linear impact estimate
    """
    require_positive(order_size, "order_size")
    
    # Linear impact: ΔP = λ * Q
    impact_dollars = kyle_lambda * order_size
    impact_pct = impact_dollars / arrival_price
    impact_bps = impact_pct * 10000
    
    # Assume all impact is permanent (Kyle model is about information)
    execution_cost = impact_dollars * order_size / 2  # Average impact
    average_price = arrival_price + impact_dollars / 2
    
    return MarketImpactResult(
        temporary_impact=0.0,
        permanent_impact=impact_bps,
        total_impact=impact_bps,
        execution_cost=execution_cost,
        arrival_price=arrival_price,
        average_price=average_price,
    )


def jpm_impact(
    order_size: float,
    daily_volume: float,
    volatility: float,
    arrival_price: float = 100.0,
    beta_temp: float = 0.5,
    beta_perm: float = 0.1,
) -> MarketImpactResult:
    """
    JPM (J.P. Morgan) market impact model.

    Decomposes impact into temporary and permanent components
    with square-root scaling.
    
    Temporary: β_temp * σ * (Q / ADV)^0.5
    Permanent: β_perm * σ * (Q / ADV)
    
    Parameters
    ----------
    order_size : float
        Order size (shares)
    daily_volume : float
        Average daily volume (shares)
    volatility : float
        Daily volatility
    arrival_price : float
        Arrival price ($)
    beta_temp : float
        Temporary impact coefficient
    beta_perm : float
        Permanent impact coefficient
    
    Returns
    -------
    MarketImpactResult
        JPM impact estimate
    """
    require_positive(order_size, "order_size")
    require_positive(daily_volume, "daily_volume")
    require_positive(volatility, "volatility")
    
    volume_fraction = order_size / daily_volume
    
    # Temporary impact (square-root)
    temp_impact_pct = beta_temp * volatility * np.sqrt(volume_fraction)
    
    # Permanent impact (linear)
    perm_impact_pct = beta_perm * volatility * volume_fraction
    
    temp_impact_bps = temp_impact_pct * 10000
    perm_impact_bps = perm_impact_pct * 10000
    total_impact_bps = temp_impact_bps + perm_impact_bps
    
    # Cost calculation
    temp_cost = temp_impact_pct * arrival_price * order_size
    perm_cost = perm_impact_pct * arrival_price * order_size
    execution_cost = temp_cost + perm_cost
    
    average_price = arrival_price * (1 + temp_impact_pct + perm_impact_pct)
    
    return MarketImpactResult(
        temporary_impact=temp_impact_bps,
        permanent_impact=perm_impact_bps,
        total_impact=total_impact_bps,
        execution_cost=execution_cost,
        arrival_price=arrival_price,
        average_price=average_price,
    )


def square_root_impact(
    order_size: float,
    daily_volume: float,
    volatility: float,
    arrival_price: float = 100.0,
    coefficient: float = 0.5,
) -> MarketImpactResult:
    """
    Simple square-root impact model (industry standard).

    Impact = c * σ * (Q / ADV)^0.5
    
    This is the most commonly used functional form in practice.
    
    Parameters
    ----------
    coefficient : float
        Impact coefficient (typical range: 0.3 - 1.0)
    
    Returns
    -------
    MarketImpactResult
        Square-root impact estimate
    """
    require_positive(order_size, "order_size")
    require_positive(daily_volume, "daily_volume")
    require_positive(volatility, "volatility")
    
    volume_fraction = order_size / daily_volume
    
    # Square-root scaling
    impact_pct = coefficient * volatility * np.sqrt(volume_fraction)
    impact_bps = impact_pct * 10000
    
    execution_cost = impact_pct * arrival_price * order_size
    average_price = arrival_price * (1 + impact_pct)
    
    # Assume 70% temporary, 30% permanent (typical split)
    temp_impact_bps = impact_bps * 0.7
    perm_impact_bps = impact_bps * 0.3
    
    return MarketImpactResult(
        temporary_impact=temp_impact_bps,
        permanent_impact=perm_impact_bps,
        total_impact=impact_bps,
        execution_cost=execution_cost,
        arrival_price=arrival_price,
        average_price=average_price,
    )


def estimate_slippage(
    order_size: float,
    spread: float,
    arrival_price: float = 100.0,
) -> float:
    """
    Estimate simple slippage from bid-ask spread.

    Slippage = spread / 2 (assumes crossing half the spread)
    
    Parameters
    ----------
    order_size : float
        Order size (shares)
    spread : float
        Bid-ask spread ($)
    arrival_price : float
        Arrival price ($)
    
    Returns
    -------
    float
        Slippage cost ($)
    """
    slippage_per_share = spread / 2
    return slippage_per_share * order_size
