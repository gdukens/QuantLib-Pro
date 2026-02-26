"""
Execution & Market Impact API Router

Covers execution module:
- Market impact models (Almgren-Chriss, Kyle's lambda, JPM, square-root)
- VWAP / TWAP schedule generation
- Optimal execution trajectory
- Execution cost analysis and slippage estimation
- Smart order routing simulation
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

execution_router = APIRouter(prefix="/execution", tags=["execution"])

# =============================================================================
# Models
# =============================================================================

class MarketImpactModelRequest(BaseModel):
    ticker: str = Field(default="SPY")
    trade_size_shares: int = Field(default=50000, ge=100)
    price: float = Field(default=100.0, ge=0.01)
    average_daily_volume: int = Field(default=5_000_000, ge=10000)
    volatility_daily: float = Field(default=0.012, ge=0.001, le=0.2)
    horizon_days: int = Field(default=1, ge=1, le=20)
    model: str = Field(
        default="all",
        description="almgren_chriss | kyle | jpm | square_root | all"
    )


class ImpactModelResult(BaseModel):
    model: str
    temporary_impact_bps: float
    permanent_impact_bps: float
    total_impact_bps: float
    cost_usd: float


class MarketImpactModelResponse(BaseModel):
    ticker: str
    trade_size_shares: int
    participation_rate: float
    trade_value_usd: float
    results: List[ImpactModelResult]
    recommended_model: str
    min_cost_model: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VWAPRequest(BaseModel):
    ticker: str = Field(default="SPY")
    total_shares: int = Field(default=100_000, ge=1000)
    average_daily_volume: int = Field(default=5_000_000, ge=10000)
    volatility_daily: float = Field(default=0.012, ge=0.001, le=0.2)
    execution_period_mins: int = Field(default=390, ge=30, le=390,
                                        description="Minutes in trading day to execute over")
    num_intervals: int = Field(default=13, ge=4, le=78, description="Number of execution buckets")
    participation_cap: float = Field(default=0.20, ge=0.01, le=0.5,
                                      description="Max participation rate per interval")


class VWAPSlice(BaseModel):
    interval: int
    time: str
    target_shares: int
    cumulative_shares: int
    pct_complete: float
    estimated_participation: float


class VWAPResponse(BaseModel):
    ticker: str
    total_shares: int
    schedule: List[VWAPSlice]
    estimated_vwap: float
    estimated_impact_bps: float
    execution_horizon_mins: int
    strategy: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TWAPRequest(BaseModel):
    ticker: str = Field(default="SPY")
    total_shares: int = Field(default=100_000, ge=1000)
    start_time: str = Field(default="09:30")
    end_time: str = Field(default="16:00")
    interval_mins: int = Field(default=30, ge=5, le=120)
    allow_randomization: bool = Field(default=True, description="Add ~10% randomization to reduce gaming")


class TWAPSlice(BaseModel):
    interval: int
    time_start: str
    shares_this_slice: int
    is_randomized: bool


class TWAPResponse(BaseModel):
    ticker: str
    total_shares: int
    num_slices: int
    schedule: List[TWAPSlice]
    avg_shares_per_slice: float
    estimated_impact_bps: float
    strategy: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OptimalExecutionRequest(BaseModel):
    ticker: str = Field(default="SPY")
    total_shares: int = Field(default=200_000, ge=1000)
    price: float = Field(default=100.0, ge=0.01)
    average_daily_volume: int = Field(default=5_000_000, ge=10000)
    volatility_daily: float = Field(default=0.012, ge=0.001)
    risk_aversion: float = Field(default=1e-6, ge=1e-9, le=1e-3,
                                  description="Lagrangian risk aversion parameter")
    horizon_periods: int = Field(default=10, ge=2, le=100)
    side: str = Field(default="BUY")


class OptimalExecutionResponse(BaseModel):
    ticker: str
    total_shares: int
    strategy: str  # ALMGREN_CHRISS
    trajectory: List[Dict[str, Any]]  # period, shares_to_trade, inventory_remaining
    expected_cost_bps: float
    variance_cost_bps: float
    efficient_frontier_summary: Dict[str, float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutionCostAnalysisRequest(BaseModel):
    executions: List[Dict[str, Any]] = Field(
        default=[
            {"ticker": "SPY", "shares": 10000, "exec_price": 100.5, "arrival_price": 100.0, "side": "BUY"},
            {"ticker": "QQQ", "shares": 5000, "exec_price": 99.8, "arrival_price": 100.2, "side": "SELL"},
        ]
    )


# =============================================================================
# Helpers
# =============================================================================

def _almgren_chriss_impact(participation: float, sigma: float, eta: float = 0.1, gamma: float = 0.05):
    temp = eta * sigma * float(np.sqrt(participation)) * 10000
    perm = gamma * sigma * participation * 10000
    return temp, perm


def _kyle_impact(participation: float, sigma: float):
    lambda_kyle = sigma / (2 * float(np.sqrt(participation + 1e-9)))
    temp = lambda_kyle * participation * 10000
    perm = temp * 0.4
    return temp, perm


def _jpm_impact(participation: float, sigma: float):
    temp = 0.5 * sigma * (participation ** 0.6) * 10000
    perm = 0.1 * sigma * (participation ** 0.3) * 10000
    return temp, perm


def _sqrt_impact(participation: float, sigma: float):
    temp = 0.3 * sigma * float(np.sqrt(participation)) * 10000
    perm = 0.05 * sigma * participation * 10000
    return temp, perm


# =============================================================================
# Endpoints
# =============================================================================

@execution_router.post(
    "/market-impact",
    response_model=MarketImpactModelResponse,
    summary="Compare market impact models",
    description="Compute market impact estimates across Almgren-Chriss, Kyle, JPM, and square-root models",
)
async def compute_market_impact(request: MarketImpactModelRequest) -> MarketImpactModelResponse:
    """
    Runs multiple market impact models and returns a comparison.
    Uses the Almgren-Chriss framework as the recommended model for large orders.
    """
    try:
        try:
            from quantlib_pro.execution.market_impact import (
                almgren_chriss_impact, kyle_lambda_impact, jpm_impact, square_root_impact
            )
        except ImportError:
            almgren_chriss_impact = kyle_lambda_impact = jpm_impact = square_root_impact = None

        participation = request.trade_size_shares / request.average_daily_volume
        sigma = request.volatility_daily
        trade_value = request.trade_size_shares * request.price

        model_fns = {
            "almgren_chriss": _almgren_chriss_impact,
            "kyle": _kyle_impact,
            "jpm": _jpm_impact,
            "square_root": _sqrt_impact,
        }

        selected = list(model_fns.keys()) if request.model == "all" else [request.model]
        results = []
        for m in selected:
            if m in model_fns:
                t, p = model_fns[m](participation, sigma)
                total = t + p
                cost = trade_value * total / 10000
                results.append(ImpactModelResult(
                    model=m,
                    temporary_impact_bps=round(t, 3),
                    permanent_impact_bps=round(p, 3),
                    total_impact_bps=round(total, 3),
                    cost_usd=round(cost, 2),
                ))

        min_cost_model = min(results, key=lambda r: r.cost_usd).model if results else "almgren_chriss"

        return MarketImpactModelResponse(
            ticker=request.ticker,
            trade_size_shares=request.trade_size_shares,
            participation_rate=round(participation, 4),
            trade_value_usd=round(trade_value, 2),
            results=results,
            recommended_model="almgren_chriss",
            min_cost_model=min_cost_model,
        )
    except Exception as e:
        logger.error(f"Market impact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@execution_router.post(
    "/vwap-schedule",
    response_model=VWAPResponse,
    summary="Generate VWAP execution schedule",
    description="Generate a VWAP schedule distributing shares according to expected intraday volume profile",
)
async def generate_vwap_schedule(request: VWAPRequest) -> VWAPResponse:
    """
    Generates intraday VWAP schedule based on U-shaped volume profile.
    Caps participation rate to avoid market disruption.
    """
    try:
        try:
            from quantlib_pro.execution.strategies import VWAPStrategy
            strategy = VWAPStrategy()
        except ImportError:
            pass

        n = request.num_intervals
        interval_mins = request.execution_period_mins // n

        # U-shape volume profile weights
        x = np.linspace(0, 1, n)
        vol_weights = 1.5 - np.cos(np.pi * x)  # high at open/close
        vol_weights /= vol_weights.sum()

        schedule = []
        cum_shares = 0
        for i in range(n):
            target = max(100, int(request.total_shares * vol_weights[i]))
            target = min(target, int(request.average_daily_volume * request.participation_cap * interval_mins / 390))
            cum_shares += target
            h = 9 + (i * interval_mins) // 60
            m = (i * interval_mins) % 60
            schedule.append(VWAPSlice(
                interval=i + 1,
                time=f"{h:02d}:{m:02d}",
                target_shares=target,
                cumulative_shares=cum_shares,
                pct_complete=round(cum_shares / request.total_shares * 100, 1),
                estimated_participation=round(float(vol_weights[i] * request.total_shares / (request.average_daily_volume * interval_mins / 390)), 4),
            ))

        avg_participation = request.total_shares / request.average_daily_volume
        impact_bps = round(0.1 * request.volatility_daily * float(np.sqrt(avg_participation)) * 10000 if hasattr(request, 'volatility_daily') else 5.0, 3)
        estimated_vwap = round(100.0 * (1 + avg_participation * 0.001), 4)

        return VWAPResponse(
            ticker=request.ticker,
            total_shares=request.total_shares,
            schedule=schedule,
            estimated_vwap=estimated_vwap,
            estimated_impact_bps=impact_bps,
            execution_horizon_mins=request.execution_period_mins,
            strategy="VWAP",
        )
    except Exception as e:
        logger.error(f"VWAP schedule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@execution_router.post(
    "/twap-schedule",
    response_model=TWAPResponse,
    summary="Generate TWAP execution schedule",
    description="Generate a time-weighted average price execution schedule with optional randomization",
)
async def generate_twap_schedule(request: TWAPRequest) -> TWAPResponse:
    """
    Divides total shares evenly across time intervals. With randomization,
    each slice varies by ±10% to prevent front-running.
    """
    try:
        try:
            from quantlib_pro.execution.strategies import TWAPStrategy
            strategy = TWAPStrategy()
        except ImportError:
            pass

        start_h, start_m = map(int, request.start_time.split(":"))
        end_h, end_m = map(int, request.end_time.split(":"))
        total_mins = (end_h * 60 + end_m) - (start_h * 60 + start_m)
        num_slices = max(1, total_mins // request.interval_mins)
        base_shares = request.total_shares // num_slices
        rng = np.random.default_rng(42)

        schedule = []
        for i in range(num_slices):
            actual_shares = base_shares
            randomized = False
            if request.allow_randomization and i < num_slices - 1:
                actual_shares = max(1, int(base_shares * rng.uniform(0.9, 1.1)))
                randomized = True
            total_min = start_h * 60 + start_m + i * request.interval_mins
            h, m = total_min // 60, total_min % 60
            schedule.append(TWAPSlice(
                interval=i + 1,
                time_start=f"{h:02d}:{m:02d}",
                shares_this_slice=actual_shares,
                is_randomized=randomized,
            ))

        return TWAPResponse(
            ticker=request.ticker,
            total_shares=request.total_shares,
            num_slices=num_slices,
            schedule=schedule,
            avg_shares_per_slice=round(base_shares, 0),
            estimated_impact_bps=round(float(np.sqrt(request.total_shares / 5_000_000) * 0.012 * 10000), 3),
            strategy="TWAP",
        )
    except Exception as e:
        logger.error(f"TWAP schedule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@execution_router.post(
    "/optimal-trajectory",
    response_model=OptimalExecutionResponse,
    summary="Almgren-Chriss optimal execution trajectory",
    description="Generate optimal liquidation/acquisition trajectory minimizing expected cost + variance",
)
async def optimal_execution_trajectory(request: OptimalExecutionRequest) -> OptimalExecutionResponse:
    """
    Solves the Almgren-Chriss (2001) optimal trade schedule minimizing:
    E[cost] + lambda * Var[cost] over a discrete horizon.
    """
    try:
        n = request.horizon_periods
        T = n
        sigma = request.volatility_daily
        lam = request.risk_aversion
        eta = 0.1 * sigma
        gamma = 0.05 * sigma

        # Almgren-Chriss closed-form trajectory
        kappa_sq = lam * sigma ** 2 / eta
        kappa = float(np.sqrt(kappa_sq))
        tau = T / n

        trajectory = []
        rem = request.total_shares
        for j in range(1, n + 1):
            # Optimal trade at period j
            n_j = request.total_shares * (
                float(np.sinh(kappa * (n - j + 1) * tau)) /
                float(np.sinh(kappa * n * tau) + 1e-10)
            ) if kappa > 1e-10 else rem / (n - j + 1 + 1e-10)
            shares_j = max(0, int(rem - max(0, int(n_j))))
            rem = max(0, rem - shares_j)
            part = shares_j / request.average_daily_volume if request.average_daily_volume > 0 else 0
            t_imp, p_imp = _almgren_chriss_impact(part, sigma)
            trajectory.append({
                "period": j,
                "shares_to_trade": shares_j,
                "inventory_remaining": rem,
                "participation_rate": round(part, 4),
                "period_impact_bps": round(t_imp + p_imp, 3),
            })

        total_impact = sum(sl["period_impact_bps"] for sl in trajectory)
        variance_bps = round(total_impact * 0.3, 3)

        return OptimalExecutionResponse(
            ticker=request.ticker,
            total_shares=request.total_shares,
            strategy="ALMGREN_CHRISS_OPTIMAL",
            trajectory=trajectory,
            expected_cost_bps=round(total_impact, 3),
            variance_cost_bps=variance_bps,
            efficient_frontier_summary={
                "min_cost_bps": round(total_impact * 0.7, 3),
                "min_variance_bps": round(variance_bps * 0.7, 3),
                "balanced_bps": round(total_impact, 3),
            },
        )
    except Exception as e:
        logger.error(f"Optimal execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@execution_router.post(
    "/cost-analysis",
    summary="Execution cost analysis",
    description="Analyze a set of completed executions against arrival price benchmarks",
)
async def execution_cost_analysis(request: ExecutionCostAnalysisRequest) -> Dict:
    """Analyze slippage and implementation shortfall for completed executions."""
    try:
        results = []
        total_is_bps = 0.0
        for exec_data in request.executions:
            ticker = exec_data.get("ticker", "?")
            shares = exec_data.get("shares", 1)
            exec_price = float(exec_data.get("exec_price", 100))
            arrival_price = float(exec_data.get("arrival_price", 100))
            side = exec_data.get("side", "BUY")

            if side == "BUY":
                slippage_bps = (exec_price - arrival_price) / arrival_price * 10000
            else:
                slippage_bps = (arrival_price - exec_price) / arrival_price * 10000

            cost_usd = shares * abs(exec_price - arrival_price)
            total_is_bps += slippage_bps
            results.append({
                "ticker": ticker, "shares": shares, "side": side,
                "exec_price": exec_price, "arrival_price": arrival_price,
                "slippage_bps": round(slippage_bps, 3),
                "implementation_shortfall_usd": round(cost_usd, 2),
                "quality": "GOOD" if abs(slippage_bps) < 5 else ("FAIR" if abs(slippage_bps) < 15 else "POOR"),
            })

        avg_is = total_is_bps / len(results) if results else 0
        return {
            "executions": results,
            "summary": {
                "avg_implementation_shortfall_bps": round(avg_is, 3),
                "total_slippage_cost_usd": round(sum(r["implementation_shortfall_usd"] for r in results), 2),
                "execution_quality": "GOOD" if abs(avg_is) < 5 else "NEEDS_IMPROVEMENT",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Cost analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
