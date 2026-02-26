"""
QuantLib Pro SDK — JWT Authentication Manager

Handles:
- Login via POST /auth/login
- Token storage in memory (never to disk)
- Auto-refresh on 401 responses
- Token expiry detection via JWT decode
- API key auth as alternative
"""

import base64
import json
import logging
import os
import time
from typing import Optional

import httpx

from quantlib_api.exceptions import QuantLibAuthError, QuantLibNetworkError

logger = logging.getLogger(__name__)

API_BASE_URL_ENV = "QUANTLIB_URL"
API_KEY_ENV = "QUANTLIB_API_KEY"
DEFAULT_BASE_URL = "http://localhost:8000"


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verifying signature (for expiry check only)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        # Add padding
        payload += "=" * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def _token_expired(token: str, buffer_seconds: int = 60) -> bool:
    """Return True if the JWT token expires within buffer_seconds."""
    payload = _decode_jwt_payload(token)
    exp = payload.get("exp")
    if not exp:
        return False  # No expiry claim → assume valid
    return time.time() >= (exp - buffer_seconds)


class AuthManager:
    """
    Manages JWT authentication lifecycle for the QuantLib Pro API.

    Supports:
    - username/password login (POST /auth/login)
    - API key via Authorization header
    - Auto-refresh on expiry
    - Environment variable configuration (QUANTLIB_URL, QUANTLIB_API_KEY)
    """

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._api_key = api_key or os.environ.get(API_KEY_ENV)
        self._token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AuthManager":
        """Create AuthManager from environment variables."""
        base_url = os.environ.get(API_BASE_URL_ENV, DEFAULT_BASE_URL)
        api_key = os.environ.get(API_KEY_ENV)
        return cls(base_url=base_url, api_key=api_key)

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> str:
        """
        Authenticate with username/password and store the JWT token.

        Returns:
            str: The JWT access token

        Raises:
            QuantLibAuthError: If credentials are invalid
            QuantLibNetworkError: If the server is unreachable
        """
        user = username or self._username
        pwd = password or self._password

        if not user or not pwd:
            raise QuantLibAuthError("Username and password are required for login.")

        try:
            response = httpx.post(
                f"{self.base_url}/auth/login",
                json={"username": user, "password": pwd},
                timeout=10.0,
            )
        except httpx.ConnectError as e:
            raise QuantLibNetworkError(f"Cannot connect to {self.base_url}") from e
        except httpx.TimeoutException as e:
            raise QuantLibNetworkError("Login request timed out") from e

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token")
            if not token:
                raise QuantLibAuthError("Login succeeded but no token in response.")
            self._token = token
            logger.info("✅ Successfully authenticated with QuantLib Pro API")
            return token
        elif response.status_code in (401, 403):
            raise QuantLibAuthError(f"Invalid credentials: {response.json().get('detail', '')}")
        else:
            raise QuantLibAuthError(f"Login failed with status {response.status_code}")

    def get_token(self, auto_refresh: bool = True) -> Optional[str]:
        """
        Get the current valid token. Auto-refreshes if expired and credentials available.

        Returns:
            str | None: JWT token, or None if not authenticated
        """
        if self._api_key:
            return self._api_key  # API key doesn't expire

        if not self._token:
            return None

        if auto_refresh and _token_expired(self._token) and self._username and self._password:
            logger.info("Token expired. Auto-refreshing...")
            try:
                self.login()
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                return None

        return self._token

    def get_headers(self) -> dict:
        """Return Authorization headers for API requests."""
        token = self.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    @property
    def is_authenticated(self) -> bool:
        """True if a valid token is available."""
        return bool(self.get_token(auto_refresh=False))

    def logout(self):
        """Clear stored credentials."""
        self._token = None
        logger.info("Logged out from QuantLib Pro API")
