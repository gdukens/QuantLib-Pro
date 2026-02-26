"""
QuantLib Pro SDK — Options Resource
"""
from typing import Any, Dict, Optional
from quantlib_api.resources.base import BaseResource


class OptionsResource(BaseResource):
    """Options pricing and Greeks calculation."""

    PREFIX = "/api/v1/options"

    def price(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        risk_free_rate: float = 0.045,
        volatility: float = 0.25,
        option_type: str = "call",
        model: str = "black_scholes",
    ) -> Dict[str, Any]:
        """
        Price an option using specified model.

        Parameters
        ----------
        spot : float
            Current underlying price
        strike : float
            Option strike price
        expiry_days : int
            Days to expiration
        risk_free_rate : float
            Risk-free interest rate
        volatility : float
            Implied or historical volatility
        option_type : str
            "call" or "put"
        model : str
            "black_scholes", "binomial", "monte_carlo"

        Returns
        -------
        dict
            Option price and Greeks
        """
        return self._http.post(
            self._url("/price"),
            json={
                "spot": spot,
                "strike": strike,
                "expiry_days": expiry_days,
                "risk_free_rate": risk_free_rate,
                "volatility": volatility,
                "option_type": option_type,
                "model": model,
            },
        )

    def greeks(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        risk_free_rate: float = 0.045,
        volatility: float = 0.25,
        option_type: str = "call",
    ) -> Dict[str, Any]:
        """Calculate all option Greeks (Delta, Gamma, Theta, Vega, Rho)."""
        return self._http.post(
            self._url("/greeks"),
            json={
                "spot": spot,
                "strike": strike,
                "expiry_days": expiry_days,
                "risk_free_rate": risk_free_rate,
                "volatility": volatility,
                "option_type": option_type,
            },
        )

    def monte_carlo(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        volatility: float = 0.25,
        simulations: int = 10000,
        option_type: str = "call",
    ) -> Dict[str, Any]:
        """Price option using Monte Carlo simulation."""
        return self._http.post(
            self._url("/monte-carlo"),
            json={
                "spot": spot,
                "strike": strike,
                "expiry_days": expiry_days,
                "volatility": volatility,
                "simulations": simulations,
                "option_type": option_type,
            },
        )

    def implied_volatility(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        market_price: float,
        option_type: str = "call",
    ) -> Dict[str, Any]:
        """Calculate implied volatility from market price."""
        return self._http.post(
            self._url("/implied-volatility"),
            json={
                "spot": spot,
                "strike": strike,
                "expiry_days": expiry_days,
                "market_price": market_price,
                "option_type": option_type,
            },
        )
