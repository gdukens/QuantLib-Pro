"""
QuantLib Pro SDK — HTTP Session Wrapper

Handles:
- httpx session with connection pooling
- Automatic retry with exponential backoff (3 attempts)
- JWT Bearer token injection
- Timeout configuration (connect: 5s, read: 30s)
- Verbose mode for debugging (masks auth headers)
- Async support via httpx.AsyncClient
"""

import logging
import time
from typing import Any

import httpx

from quantlib_api.exceptions import (
    QuantLibAPIError,
    QuantLibAuthError,
    QuantLibNetworkError,
    QuantLibNotFoundError,
    QuantLibRateLimitError,
)

logger = logging.getLogger(__name__)

# Default timeouts
CONNECT_TIMEOUT = 5.0   # seconds
READ_TIMEOUT = 30.0     # seconds
MAX_RETRIES = 3
BACKOFF_BASE = 0.5      # seconds


class HTTPSession:
    """
    Synchronous HTTP session wrapping httpx.Client with retry logic.

    Automatically injects Authorization header and handles
    4xx/5xx responses by raising typed exceptions.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = READ_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        verbose: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose
        self._token: str | None = None
        self._api_key: str | None = None
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=self.timeout, write=10.0, pool=5.0),
            follow_redirects=True,
        )

    def set_token(self, token: str):
        """Update the Bearer token used for all requests."""
        self._token = token

    def set_api_key(self, api_key: str):
        """Update the API key used for all requests."""
        self._api_key = api_key

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        elif self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    def _log_request(self, method: str, url: str, body: Any = None):
        if self.verbose:
            safe_headers = self._headers()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "Bearer ***"
            logger.debug(f"→ {method} {url}  headers={safe_headers}  body={body}")

    def _handle_response(self, response: httpx.Response) -> dict:
        status = response.status_code
        if self.verbose:
            logger.debug(f"← {status} ({len(response.content)} bytes)")

        if status == 200 or status == 201:
            try:
                return response.json()
            except Exception:
                return {"raw": response.text}

        # Error handling
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text

        if status in (401, 403):
            raise QuantLibAuthError(f"HTTP {status}: {detail}")
        if status == 404:
            raise QuantLibNotFoundError(detail)
        if status == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise QuantLibRateLimitError(retry_after)
        raise QuantLibAPIError(f"HTTP {status}: {detail}", status_code=status, response={"detail": detail})

    def _request_with_retry(self, method: str, path: str, **kwargs) -> dict:
        url = path if path.startswith("http") else self.base_url + path
        self._log_request(method, url, kwargs.get("json"))

        last_exc = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.request(method, url, headers=self._headers(), **kwargs)
                return self._handle_response(response)
            except (QuantLibAuthError, QuantLibNotFoundError):
                raise  # Don't retry auth/404 errors
            except QuantLibRateLimitError as e:
                wait = e.retry_after
                logger.warning(f"Rate limited. Waiting {wait}s before retry {attempt + 1}/{self.max_retries}")
                time.sleep(min(wait, 60))
                last_exc = e
            except QuantLibAPIError as e:
                if e.status_code < 500:
                    raise  # Don't retry 4xx
                wait = BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"Server error {e.status_code}. Retrying in {wait:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait)
                last_exc = e
            except httpx.TimeoutException as e:
                wait = BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"Timeout. Retrying in {wait:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait)
                last_exc = QuantLibNetworkError(f"Request timed out after {self.timeout}s")
            except httpx.ConnectError as e:
                raise QuantLibNetworkError(f"Cannot connect to {self.base_url}. Is the server running?") from e
            except httpx.RequestError as e:
                raise QuantLibNetworkError(str(e)) from e

        raise last_exc or QuantLibNetworkError("Max retries exceeded")

    def get(self, path: str, params: dict = None) -> dict:
        return self._request_with_retry("GET", path, params=params)

    def post(self, path: str, json: dict = None) -> dict:
        return self._request_with_retry("POST", path, json=json or {})

    def put(self, path: str, json: dict = None) -> dict:
        return self._request_with_retry("PUT", path, json=json or {})

    def delete(self, path: str) -> dict:
        return self._request_with_retry("DELETE", path)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncHTTPSession:
    """
    Async HTTP session (httpx.AsyncClient) for use with asyncio.

    Usage::

        async with AsyncHTTPSession("http://localhost:8000") as session:
            session.set_token(token)
            result = await session.get("/api/v1/portfolio/performance")
    """

    def __init__(self, base_url: str, *, timeout: float = READ_TIMEOUT, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self._token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=timeout, write=10.0, pool=5.0),
            follow_redirects=True,
        )

    def set_token(self, token: str):
        self._token = token

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    async def _handle_response_async(self, response: httpx.Response) -> dict:
        status = response.status_code
        if status in (200, 201):
            try:
                return response.json()
            except Exception:
                return {"raw": response.text}
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        if status in (401, 403):
            raise QuantLibAuthError(f"HTTP {status}: {detail}")
        if status == 404:
            raise QuantLibNotFoundError(detail)
        if status == 429:
            raise QuantLibRateLimitError(int(response.headers.get("Retry-After", 60)))
        raise QuantLibAPIError(f"HTTP {status}: {detail}", status_code=status)

    async def get(self, path: str, params: dict = None) -> dict:
        url = self.base_url + path
        try:
            r = await self._client.get(url, headers=self._headers(), params=params)
            return await self._handle_response_async(r)
        except httpx.ConnectError as e:
            raise QuantLibNetworkError(str(e)) from e

    async def post(self, path: str, json: dict = None) -> dict:
        url = self.base_url + path
        try:
            r = await self._client.post(url, headers=self._headers(), json=json or {})
            return await self._handle_response_async(r)
        except httpx.ConnectError as e:
            raise QuantLibNetworkError(str(e)) from e

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
