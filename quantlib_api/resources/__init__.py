"""
QuantLib Pro SDK — Resource classes for all API domains.

Each resource provides typed methods for interacting with a specific API domain.
"""

from quantlib_api.resources.portfolio import PortfolioResource
from quantlib_api.resources.risk import RiskResource
from quantlib_api.resources.options import OptionsResource
from quantlib_api.resources.regime import RegimeResource
from quantlib_api.resources.volatility import VolatilityResource
from quantlib_api.resources.macro import MacroResource
from quantlib_api.resources.backtesting import BacktestingResource
from quantlib_api.resources.analytics import AnalyticsResource
from quantlib_api.resources.data import DataResource
from quantlib_api.resources.market_analysis import MarketAnalysisResource
from quantlib_api.resources.signals import SignalsResource
from quantlib_api.resources.liquidity import LiquidityResource
from quantlib_api.resources.systemic_risk import SystemicRiskResource
from quantlib_api.resources.execution import ExecutionResource
from quantlib_api.resources.compliance import ComplianceResource
from quantlib_api.resources.uat import UATResource
from quantlib_api.resources.health import HealthResource

__all__ = [
    "PortfolioResource",
    "RiskResource",
    "OptionsResource",
    "RegimeResource",
    "VolatilityResource",
    "MacroResource",
    "BacktestingResource",
    "AnalyticsResource",
    "DataResource",
    "MarketAnalysisResource",
    "SignalsResource",
    "LiquidityResource",
    "SystemicRiskResource",
    "ExecutionResource",
    "ComplianceResource",
    "UATResource",
    "HealthResource",
]
