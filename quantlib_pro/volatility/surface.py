"""
Volatility surface construction from market option prices.

Builds implied volatility surfaces from:
  - Market option prices (calls and puts)
  - Strike-maturity grid
  - Arbitrage-free constraints

The surface maps (strike, maturity) → implied volatility σ(K, T).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy.interpolate import RBFInterpolator, griddata

from quantlib_pro.options import implied_volatility
from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


@dataclass
class SurfacePoint:
    """Single point on volatility surface."""
    strike: float
    maturity: float  # Years
    implied_vol: float
    market_price: float
    option_type: str  # 'call' or 'put'
    moneyness: float  # K/S


@dataclass
class VolatilitySurface:
    """Implied volatility surface."""
    points: list[SurfacePoint]
    spot_price: float
    risk_free_rate: float
    timestamp: float
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert surface points to DataFrame."""
        return pd.DataFrame([
            {
                'strike': p.strike,
                'maturity': p.maturity,
                'implied_vol': p.implied_vol,
                'moneyness': p.moneyness,
                'option_type': p.option_type,
            }
            for p in self.points
        ])
    
    def get_strikes(self) -> np.ndarray:
        """Get unique strike prices."""
        return np.unique([p.strike for p in self.points])
    
    def get_maturities(self) -> np.ndarray:
        """Get unique maturities."""
        return np.unique([p.maturity for p in self.points])
    
    def get_atm_vol(self, maturity: float) -> Optional[float]:
        """
        Get at-the-money volatility for a given maturity.
        
        Parameters
        ----------
        maturity : float
            Time to maturity (years)
        
        Returns
        -------
        float or None
            ATM implied vol, or None if not found
        """
        # Find points close to ATM (moneyness ≈ 1.0)
        atm_points = [
            p for p in self.points
            if abs(p.maturity - maturity) < 0.01 and abs(p.moneyness - 1.0) < 0.05
        ]
        
        if not atm_points:
            return None
        
        return np.mean([p.implied_vol for p in atm_points])


def build_surface_from_prices(
    option_prices: pd.DataFrame,
    spot_price: float,
    risk_free_rate: float = 0.02,
) -> VolatilitySurface:
    """
    Build volatility surface from market option prices.
    
    Parameters
    ----------
    option_prices : pd.DataFrame
        Columns: ['strike', 'maturity', 'price', 'option_type']
    spot_price : float
        Current spot price
    risk_free_rate : float
        Risk-free rate
    
    Returns
    -------
    VolatilitySurface
        Constructed volatility surface
    """
    require_positive(spot_price, "spot_price")
    
    required_cols = ['strike', 'maturity', 'price', 'option_type']
    missing = set(required_cols) - set(option_prices.columns)
    if missing:
        raise ValidationError(f"option_prices missing columns: {missing}")
    
    points = []
    
    for _, row in option_prices.iterrows():
        strike = row['strike']
        maturity = row['maturity']
        market_price = row['price']
        option_type = row['option_type']
        
        if maturity <= 0:
            log.warning(f"Skipping expired option: K={strike}, T={maturity}")
            continue
        
        # Calculate implied volatility
        try:
            iv = implied_volatility(
                market_price=market_price,
                S=spot_price,
                K=strike,
                T=maturity,
                r=risk_free_rate,
                option_type=option_type,
            )
            
            if iv is None or iv <= 0:
                log.warning(f"Invalid IV for K={strike}, T={maturity}: {iv}")
                continue
            
            moneyness = strike / spot_price
            
            points.append(SurfacePoint(
                strike=strike,
                maturity=maturity,
                implied_vol=iv,
                market_price=market_price,
                option_type=option_type,
                moneyness=moneyness,
            ))
        
        except Exception as e:
            log.warning(f"Failed to calculate IV for K={strike}, T={maturity}: {e}")
            continue
    
    if not points:
        raise ValidationError("No valid surface points computed")
    
    return VolatilitySurface(
        points=points,
        spot_price=spot_price,
        risk_free_rate=risk_free_rate,
        timestamp=0.0,
    )


def interpolate_surface(
    surface: VolatilitySurface,
    method: str = 'rbf',
) -> callable:
    """
    Create interpolation function for volatility surface.
    
    Parameters
    ----------
    surface : VolatilitySurface
        Volatility surface
    method : str
        Interpolation method: 'rbf', 'linear', 'cubic'
    
    Returns
    -------
    callable
        Function that takes (strike, maturity) and returns implied vol
    """
    df = surface.to_dataframe()
    
    strikes = df['strike'].values
    maturities = df['maturity'].values
    vols = df['implied_vol'].values
    
    points = np.column_stack([strikes, maturities])
    
    if method == 'rbf':
        # Radial basis function interpolation (smooth)
        interpolator = RBFInterpolator(points, vols, kernel='thin_plate_spline')
        
        def interp_func(K: float, T: float) -> float:
            result = interpolator([[K, T]])
            return float(result[0])
        
        return interp_func
    
    elif method in ['linear', 'cubic']:
        # Grid-based interpolation
        def interp_func(K: float, T: float) -> float:
            result = griddata(points, vols, (K, T), method=method)
            return float(result) if not np.isnan(result) else surface.get_atm_vol(T) or 0.2
        
        return interp_func
    
    else:
        raise ValidationError(f"Unknown interpolation method: {method}")


def extract_volatility_slice(
    surface: VolatilitySurface,
    maturity: float,
    tolerance: float = 0.01,
) -> pd.DataFrame:
    """
    Extract volatility smile for a specific maturity.
    
    Parameters
    ----------
    surface : VolatilitySurface
        Volatility surface
    maturity : float
        Target maturity (years)
    tolerance : float
        Tolerance for maturity matching
    
    Returns
    -------
    pd.DataFrame
        Smile: columns ['strike', 'implied_vol', 'moneyness']
    """
    matching_points = [
        p for p in surface.points
        if abs(p.maturity - maturity) < tolerance
    ]
    
    if not matching_points:
        raise ValidationError(f"No points found near maturity {maturity}")
    
    df = pd.DataFrame([
        {
            'strike': p.strike,
            'implied_vol': p.implied_vol,
            'moneyness': p.moneyness,
        }
        for p in matching_points
    ])
    
    return df.sort_values('strike')


def compute_volatility_skew(smile: pd.DataFrame) -> float:
    """
    Compute volatility skew from a smile.
    
    Skew = (IV_put - IV_call) for OTM options at symmetric strikes.
    Approximated as slope of IV vs moneyness.
    
    Parameters
    ----------
    smile : pd.DataFrame
        Volatility smile with ['moneyness', 'implied_vol']
    
    Returns
    -------
    float
        Skew coefficient (negative = put skew)
    """
    if len(smile) < 2:
        return 0.0
    
    # Fit linear regression: IV = a + b * log(K/S)
    log_moneyness = np.log(smile['moneyness'].values)
    iv = smile['implied_vol'].values
    
    # Slope coefficient
    coeffs = np.polyfit(log_moneyness, iv, deg=1)
    skew = coeffs[0]  # Slope
    
    return skew


def compute_volatility_smile_curvature(smile: pd.DataFrame) -> float:
    """
    Compute smile curvature (convexity).
    
    Measures how much the smile deviates from flat.
    Positive curvature = U-shaped (typical).
    
    Parameters
    ----------
    smile : pd.DataFrame
        Volatility smile
    
    Returns
    -------
    float
        Curvature coefficient
    """
    if len(smile) < 3:
        return 0.0
    
    # Fit quadratic: IV = a + b*x + c*x^2
    log_moneyness = np.log(smile['moneyness'].values)
    iv = smile['implied_vol'].values
    
    coeffs = np.polyfit(log_moneyness, iv, deg=2)
    curvature = coeffs[0]  # Quadratic term
    
    return curvature


# ─── Convenience Aliases ──────────────────────────────────────────────────────

def construct_volatility_surface(*args, **kwargs):
    """
    Alias for build_surface_from_prices.
    
    This function provides backward compatibility for UI components
    that use the construct_volatility_surface naming convention.
    """
    return build_surface_from_prices(*args, **kwargs)
