"""
FactSet data provider integration.

FactSet provides comprehensive financial data, analytics, and research.
Requires enterprise subscription and API credentials.

API Documentation: https://developer.factset.com/
"""

import logging
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import pandas as pd
import requests
from jose import jwt

from quantlib_pro.utils.validation import require_ticker

log = logging.getLogger(__name__)


class FactSetError(Exception):
    """Raised when FactSet API returns an error."""


class FactsetProvider:
    """
    FactSet market data provider.
    
    Features:
    - Global market coverage (200+ exchanges)
    - Real-time and historical pricing
    - Fundamentals and estimates
    - Corporate actions and events
    - Credit and fixed income data
    - Alternative data sources
    
    Authentication:
    - Uses OAuth2 Client Credentials flow with JWT
    - Requires client ID and JWK (JSON Web Key)
    - Tokens are automatically acquired and refreshed
    
    Parameters
    ----------
    client_id : str, optional
        FactSet OAuth2 client ID. If None, reads from FACTSET_CLIENT_ID env var.
    jwk_path : str, optional
        Path to JWK JSON file. If None, reads from FACTSET_JWK_PATH env var.
    base_url : str
        API base URL (default: https://api.factset.com)
    timeout : int
        Request timeout in seconds (default: 60)
    
    Examples
    --------
    >>> provider = FactsetProvider(
    ...     client_id="your-client-id",
    ...     jwk_path="factset_jwk.json"
    ... )
    >>> data = provider.fetch("AAPL-US", start="2024-01-01", end="2024-12-31")
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        jwk_path: Optional[str] = None,
        base_url: str = "https://api.factset.com",
        timeout: int = 60,
    ):
        self.client_id = client_id or os.getenv("FACTSET_CLIENT_ID")
        self.jwk_path = jwk_path or os.getenv("FACTSET_JWK_PATH")
        
        if not self.client_id or not self.jwk_path:
            raise ValueError(
                "FactSet credentials required. "
                "Set FACTSET_CLIENT_ID and FACTSET_JWK_PATH environment variables "
                "or pass client_id and jwk_path parameters."
            )
        
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Load JWK credentials
        self.jwk_data = self._load_jwk()
        
        # OAuth2 token management
        self.access_token = None
        self.token_expiry = None
        self.token_endpoint = None
        
        # Session for API requests
        self._session = requests.Session()
        
        log.info(f"FactSet provider initialized with client ID: {self.client_id[:8]}...")
    
    def _load_jwk(self) -> Dict[str, Any]:
        """Load JWK from JSON file."""
        try:
            with open(self.jwk_path, 'r') as f:
                data = json.load(f)
                # Extract just the JWK portion if wrapped in config
                if 'jwk' in data:
                    return data['jwk']
                return data
        except FileNotFoundError:
            raise ValueError(f"JWK file not found: {self.jwk_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JWK JSON: {e}")
    
    def _get_token_endpoint(self) -> str:
        """Fetch OAuth2 token endpoint from well-known configuration."""
        if self.token_endpoint:
            return self.token_endpoint
        
        try:
            well_known_url = "https://auth.factset.com/.well-known/openid-configuration"
            response = requests.get(well_known_url, timeout=10)
            response.raise_for_status()
            config = response.json()
            self.token_endpoint = config["token_endpoint"]
            log.debug(f"Token endpoint: {self.token_endpoint}")
            return self.token_endpoint
        except Exception as e:
            # Fallback to known endpoint
            log.warning(f"Could not fetch well-known config, using default: {e}")
            self.token_endpoint = "https://auth.factset.com/as/token.oauth2"
            return self.token_endpoint
    
    def _generate_jwt_assertion(self) -> str:
        """Generate JWT assertion for client credentials grant."""
        now = datetime.utcnow()
        
        # JWT claims for client credentials
        # Use issuer URL as audience (common for OAuth2)
        claims = {
            "iss": self.client_id,  # Issuer
            "sub": self.client_id,  # Subject
            "aud": "https://auth.factset.com",  # Audience (issuer URL)
            "exp": int((now + timedelta(minutes=5)).timestamp()),  # Expiration
            "iat": int(now.timestamp()),  # Issued at
        }
        
        # Sign with RS256 using JWK private key
        # python-jose expects the full JWK dict with private key components
        try:
            token = jwt.encode(
                claims,
                self.jwk_data,
                algorithm="RS256",
                headers={"kid": self.jwk_data.get("kid"), "typ": "JWT"}
            )
            log.debug(f"Generated JWT assertion for client {self.client_id[:8]}...")
            log.debug(f"JWT claims: iss={claims['iss'][:8]}..., aud={claims['aud']}")
            return token
        except Exception as e:
            log.error(f"Failed to generate JWT: {e}")
            raise FactSetError(f"JWT generation failed: {e}")
    
    def _acquire_access_token(self) -> str:
        """Acquire OAuth2 access token using client credentials flow."""
        # Check if current token is still valid
        if self.access_token and self.token_expiry:
            if datetime.utcnow() < self.token_expiry - timedelta(minutes=1):
                log.debug("Using cached access token")
                return self.access_token
        
        log.info("Acquiring new OAuth2 access token...")
        
        try:
            jwt_assertion = self._generate_jwt_assertion()
            token_endpoint = self._get_token_endpoint()
            
            # OAuth2 client credentials with JWT bearer
            payload = {
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": jwt_assertion,
                "scope": "api"
            }
            
            response = requests.post(
                token_endpoint,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            log.info(f"Access token acquired, expires in {expires_in}s")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            log.error(f"Failed to acquire access token: {e}")
            if hasattr(e.response, 'text'):
                log.error(f"Response: {e.response.text}")
            raise FactSetError(f"OAuth2 authentication failed: {e}")
    
    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with OAuth2 bearer token."""
        token = self._acquire_access_token()
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        
        return self._session.request(method, url, timeout=self.timeout, **kwargs)
    
    def fetch(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        frequency: str = "D",
        calendar: str = "FIVEDAY",
    ) -> pd.DataFrame:
        """
        Fetch historical pricing data.
        
        Parameters
        ----------
        ticker : str
            FactSet ticker symbol (e.g., "AAPL-US", "MSFT-US")
            Format: {symbol}-{region_code}
        start : str, optional
            Start date "YYYY-MM-DD"
        end : str, optional
            End date "YYYY-MM-DD"
        frequency : str
            Data frequency: "D" (daily), "W" (weekly), "M" (monthly)
        calendar : str
            Trading calendar: "FIVEDAY", "SEVENDAY"
        
        Returns
        -------
        pd.DataFrame
            OHLCV data with DatetimeIndex
        
        Raises
        ------
        FactSetError
            If API returns an error
        
        Notes
        -----
        FactSet ticker format requires region suffix:
        - US stocks: "AAPL-US"
        - UK stocks: "VOD-GB"
        - See: https://developer.factset.com/api-catalog/factset-prices-api
        """
        ticker = require_ticker(ticker)
        
        # Auto-append -US if no region suffix provided
        if "-" not in ticker and ticker.isupper():
            ticker = f"{ticker}-US"
            log.info(f"Auto-appended region suffix: {ticker}")
        
        log.info(f"Fetching {ticker} from FactSet (freq={frequency})")
        
        # FactSet Prices API endpoint
        url = f"{self.base_url}/content/factset-prices/v1/prices"
        
        payload = {
            "ids": [ticker],
            "startDate": start or "2020-01-01",
            "endDate": end or datetime.now().strftime("%Y-%m-%d"),
            "frequency": frequency,
            "calendar": calendar,
        }
        
        try:
            response = self._make_authenticated_request(
                "POST",
                url,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for errors in response
            if "errors" in data and data["errors"]:
                error_msg = data["errors"][0].get("title", "Unknown error")
                raise FactSetError(f"FactSet API error: {error_msg}")
            
            if "data" not in data or not data["data"]:
                raise FactSetError(f"No data returned for {ticker}")
            
            # Parse response data
            records = []
            for item in data["data"]:
                records.append({
                    "Date": item.get("date"),
                    "Open": item.get("open"),
                    "High": item.get("high"),
                    "Low": item.get("low"),
                    "Close": item.get("close"),
                    "Volume": item.get("volume"),
                    "Adj Close": item.get("adjClose"),
                })
            
            df = pd.DataFrame(records)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            df = df.sort_index()
            
            # Convert to numeric
            for col in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Keep only OHLCV columns (drop Adj Close for consistency)
            df = df[["Open", "High", "Low", "Close", "Volume"]]
            
            log.info(f"✅ FactSet: Retrieved {len(df)} rows for {ticker}")
            return df
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise FactSetError(
                    "Authentication failed. Check FACTSET_USERNAME and FACTSET_API_KEY."
                )
            elif e.response.status_code == 403:
                raise FactSetError(
                    "Access forbidden. Check your FactSet subscription entitlements."
                )
            elif e.response.status_code == 429:
                raise FactSetError(
                    "Rate limit exceeded. Reduce request frequency."
                )
            else:
                raise FactSetError(f"HTTP {e.response.status_code}: {e}")
        
        except requests.exceptions.RequestException as e:
            raise FactSetError(f"Request failed: {e}")
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch company profile and metadata.
        
        Parameters
        ----------
        ticker : str
            FactSet ticker symbol (e.g., "AAPL-US")
        
        Returns
        -------
        dict
            Company information
        """
        ticker = require_ticker(ticker)
        
        if "-" not in ticker:
            ticker = f"{ticker}-US"
        
        url = f"{self.base_url}/content/factset-entity/v1/entity-info"
        
        payload = {"ids": [ticker]}
        
        response = self._make_authenticated_request(
            "POST",
            url,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        if "data" in data and data["data"]:
            return data["data"][0]
        else:
            raise FactSetError(f"No company info for {ticker}")
    
    def get_fundamentals(
        self,
        ticker: str,
        metrics: list[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch fundamental data (requires FactSet Fundamentals API).
        
        Parameters
        ----------
        ticker : str
            FactSet ticker symbol
        metrics : list of str
            Fundamental metrics to retrieve
            Examples: ["FF_SALES", "FF_ASSETS", "FF_EPS_BASIC"]
        start : str, optional
            Start date "YYYY-MM-DD"
        end : str, optional
            End date "YYYY-MM-DD"
        
        Returns
        -------
        pd.DataFrame
            Fundamental data time series
        """
        ticker = require_ticker(ticker)
        
        if "-" not in ticker:
            ticker = f"{ticker}-US"
        
        log.info(f"Fetching fundamentals for {ticker}: {metrics}")
        
        url = f"{self.base_url}/content/factset-fundamentals/v2/fundamentals"
        
        payload = {
            "ids": [ticker],
            "metrics": metrics,
            "startDate": start or "2020-01-01",
            "endDate": end or datetime.now().strftime("%Y-%m-%d"),
        }
        
        response = self._make_authenticated_request(
            "POST",
            url,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        if "data" not in data:
            raise FactSetError(f"No fundamentals data for {ticker}")
        
        df = pd.DataFrame(data["data"])
        log.info(f"✅ FactSet fundamentals: {len(df)} rows for {ticker}")
        
        return df
    
    def __repr__(self):
        return f"FactsetProvider(username='{self.username}', api_key='***')"


def create_factset_fetcher(
    username: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Create a function compatible with ResilientDataFetcher's alt_api_fn.
    
    Parameters
    ----------
    username : str, optional
        FactSet username
    api_key : str, optional
        FactSet API key
    
    Returns
    -------
    callable
        Function(ticker, start, end) -> pd.DataFrame
    
    Examples
    --------
    >>> from quantlib_pro.data.fetcher import ResilientDataFetcher
    >>> from quantlib_pro.data.providers.factset import create_factset_fetcher
    >>> 
    >>> alt_fn = create_factset_fetcher()
    >>> fetcher = ResilientDataFetcher(alt_api_fn=alt_fn)
    >>> 
    >>> # FactSet expects region suffixes
    >>> data = fetcher.fetch("AAPL-US")
    """
    provider = FactsetProvider(username=username, api_key=api_key)
    
    def fetch_function(ticker: str, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
        # Auto-append -US for US stocks if no region provided
        if "-" not in ticker and ticker.isupper():
            ticker = f"{ticker}-US"
        
        return provider.fetch(ticker, start=start, end=end, frequency="D")
    
    return fetch_function
