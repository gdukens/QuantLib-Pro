"""
QuantLib Pro SDK — Main Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The primary interface for interacting with the QuantLib Pro API.

Usage::

    from quantlib_api import QuantLibClient

    client = QuantLibClient(auto_login=True)
    result = client.portfolio.optimize(tickers=["AAPL", "GOOGL"], budget=100000)
    print(result)
"""

import os
from typing import Optional

from quantlib_api._http import HTTPSession, AsyncHTTPSession
from quantlib_api.auth import AuthManager
from quantlib_api.exceptions import QuantLibAuthError


class QuantLibClient:
    """
    Synchronous client for the QuantLib Pro API.

    All domain resources are lazily initialized and accessible as properties.

    Parameters
    ----------
    base_url : str
        API base URL (default: from QUANTLIB_URL env var or localhost:8000)
    username : str, optional
        Username for JWT auth (or QUANTLIB_USERNAME env var)
    password : str, optional
        Password for JWT auth (or QUANTLIB_PASSWORD env var)
    api_key : str, optional
        API key for auth (alternative to username/password)
    auto_login : bool
        If True, automatically authenticate on client creation
    timeout : float
        Request timeout in seconds (default: 30)
    verbose : bool
        Enable debug logging of HTTP requests/responses
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        auto_login: bool = False,
        timeout: float = 30.0,
        verbose: bool = False,
    ):
        self.base_url = base_url or os.getenv("QUANTLIB_URL", "http://localhost:8000")
        self._username = username or os.getenv("QUANTLIB_USERNAME")
        self._password = password or os.getenv("QUANTLIB_PASSWORD")
        self._api_key = api_key or os.getenv("QUANTLIB_API_KEY")

        # HTTP session
        self._http = HTTPSession(
            base_url=self.base_url,
            timeout=timeout,
            verbose=verbose,
        )

        # Auth manager
        self._auth = AuthManager(self._http)

        # Lazy-initialized resources
        self._portfolio = None
        self._risk = None
        self._options = None
        self._regime = None
        self._volatility = None
        self._macro = None
        self._backtesting = None
        self._analytics = None
        self._data = None
        self._market_analysis = None
        self._signals = None
        self._liquidity = None
        self._systemic_risk = None
        self._execution = None
        self._compliance = None
        self._uat = None
        self._health = None

        if auto_login:
            self.login()

    # ─────────────────────────────────────────────────────────────────────────
    # Authentication
    # ─────────────────────────────────────────────────────────────────────────

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> str:
        """
        Authenticate with username/password and obtain JWT token.

        Returns the JWT token string.
        """
        user = username or self._username
        pwd = password or self._password

        if not user or not pwd:
            raise QuantLibAuthError(
                "Username and password required. Set via constructor or "
                "QUANTLIB_USERNAME / QUANTLIB_PASSWORD environment variables."
            )

        token = self._auth.login(user, pwd)
        self._http.set_token(token)
        return token

    def set_api_key(self, api_key: str):
        """Use API key authentication instead of JWT."""
        self._http.set_api_key(api_key)

    @property
    def is_authenticated(self) -> bool:
        """Check if client has an active auth token."""
        return self._http._token is not None or self._http._api_key is not None

    # ─────────────────────────────────────────────────────────────────────────
    # Resource Properties (lazy initialization)
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def portfolio(self):
        """Portfolio optimization and management."""
        if self._portfolio is None:
            from quantlib_api.resources.portfolio import PortfolioResource
            self._portfolio = PortfolioResource(self._http)
        return self._portfolio

    @property
    def risk(self):
        """Risk analysis: VaR, CVaR, stress testing."""
        if self._risk is None:
            from quantlib_api.resources.risk import RiskResource
            self._risk = RiskResource(self._http)
        return self._risk

    @property
    def options(self):
        """Options pricing and Greeks calculation."""
        if self._options is None:
            from quantlib_api.resources.options import OptionsResource
            self._options = OptionsResource(self._http)
        return self._options

    @property
    def regime(self):
        """Market regime detection and analysis."""
        if self._regime is None:
            from quantlib_api.resources.regime import RegimeResource
            self._regime = RegimeResource(self._http)
        return self._regime

    @property
    def volatility(self):
        """Volatility surface construction and analysis."""
        if self._volatility is None:
            from quantlib_api.resources.volatility import VolatilityResource
            self._volatility = VolatilityResource(self._http)
        return self._volatility

    @property
    def macro(self):
        """Macro analysis and economic indicators."""
        if self._macro is None:
            from quantlib_api.resources.macro import MacroResource
            self._macro = MacroResource(self._http)
        return self._macro

    @property
    def backtesting(self):
        """Strategy backtesting and performance analysis."""
        if self._backtesting is None:
            from quantlib_api.resources.backtesting import BacktestingResource
            self._backtesting = BacktestingResource(self._http)
        return self._backtesting

    @property
    def analytics(self):
        """Advanced analytics: correlation, PCA, factor analysis."""
        if self._analytics is None:
            from quantlib_api.resources.analytics import AnalyticsResource
            self._analytics = AnalyticsResource(self._http)
        return self._analytics

    @property
    def data(self):
        """Market data access and management."""
        if self._data is None:
            from quantlib_api.resources.data import DataResource
            self._data = DataResource(self._http)
        return self._data

    @property
    def market_analysis(self):
        """Technical indicators and market analysis."""
        if self._market_analysis is None:
            from quantlib_api.resources.market_analysis import MarketAnalysisResource
            self._market_analysis = MarketAnalysisResource(self._http)
        return self._market_analysis

    @property
    def signals(self):
        """Trading signal generation and backtesting."""
        if self._signals is None:
            from quantlib_api.resources.signals import SignalsResource
            self._signals = SignalsResource(self._http)
        return self._signals

    @property
    def liquidity(self):
        """Liquidity analysis and market microstructure."""
        if self._liquidity is None:
            from quantlib_api.resources.liquidity import LiquidityResource
            self._liquidity = LiquidityResource(self._http)
        return self._liquidity

    @property
    def systemic_risk(self):
        """Systemic risk and contagion analysis."""
        if self._systemic_risk is None:
            from quantlib_api.resources.systemic_risk import SystemicRiskResource
            self._systemic_risk = SystemicRiskResource(self._http)
        return self._systemic_risk

    @property
    def execution(self):
        """Execution optimization: VWAP, TWAP, market impact."""
        if self._execution is None:
            from quantlib_api.resources.execution import ExecutionResource
            self._execution = ExecutionResource(self._http)
        return self._execution

    @property
    def compliance(self):
        """Compliance checks and regulatory reporting."""
        if self._compliance is None:
            from quantlib_api.resources.compliance import ComplianceResource
            self._compliance = ComplianceResource(self._http)
        return self._compliance

    @property
    def uat(self):
        """UAT scenarios and stress monitoring."""
        if self._uat is None:
            from quantlib_api.resources.uat import UATResource
            self._uat = UATResource(self._http)
        return self._uat

    @property
    def health(self):
        """API health checks."""
        if self._health is None:
            from quantlib_api.resources.health import HealthResource
            self._health = HealthResource(self._http)
        return self._health

    # ─────────────────────────────────────────────────────────────────────────
    # Context Manager
    # ─────────────────────────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close HTTP session and release resources."""
        self._http.close()


class AsyncQuantLibClient:
    """
    Async client for the QuantLib Pro API.

    Usage::

        async with AsyncQuantLibClient(auto_login=True) as client:
            result = await client.portfolio.aoptimize(tickers=["AAPL"], budget=100000)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        auto_login: bool = False,
        timeout: float = 30.0,
        verbose: bool = False,
    ):
        self.base_url = base_url or os.getenv("QUANTLIB_URL", "http://localhost:8000")
        self._username = username or os.getenv("QUANTLIB_USERNAME")
        self._password = password or os.getenv("QUANTLIB_PASSWORD")
        self._api_key = api_key or os.getenv("QUANTLIB_API_KEY")
        self._auto_login = auto_login

        self._http = AsyncHTTPSession(
            base_url=self.base_url,
            timeout=timeout,
            verbose=verbose,
        )

        # Lazy resources (async versions)
        self._portfolio = None
        self._risk = None
        # ... (other resources would be added)

    async def __aenter__(self):
        if self._auto_login:
            await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http.close()

    async def login(self, username: Optional[str] = None, password: Optional[str] = None) -> str:
        user = username or self._username
        pwd = password or self._password

        if not user or not pwd:
            raise QuantLibAuthError("Username and password required for async login.")

        response = await self._http.post(
            "/auth/login",
            json={"username": user, "password": pwd}
        )
        token = response.get("access_token")
        if not token:
            raise QuantLibAuthError("No access_token in login response")
        self._http.set_token(token)
        return token

    @property
    def portfolio(self):
        if self._portfolio is None:
            from quantlib_api.resources.portfolio import AsyncPortfolioResource
            self._portfolio = AsyncPortfolioResource(self._http)
        return self._portfolio
