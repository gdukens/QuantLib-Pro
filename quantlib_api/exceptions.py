"""
QuantLib Pro SDK — Typed Exception Hierarchy

Exception Design:
    QuantLibError (base)
    ├── QuantLibAPIError        # 4xx/5xx API responses
    │   ├── QuantLibAuthError   # 401/403
    │   ├── QuantLibNotFoundError  # 404
    │   └── QuantLibRateLimitError # 429
    ├── QuantLibNetworkError    # Connection/timeout errors
    └── QuantLibValidationError # Request validation failures
"""


class QuantLibError(Exception):
    """Base exception for all QuantLib SDK errors."""

    def __init__(self, message: str, *, status_code: int = 0, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}

    def __repr__(self):
        return f"{self.__class__.__name__}(status={self.status_code}, message={str(self)})"


class QuantLibAPIError(QuantLibError):
    """Raised when the API returns a 4xx or 5xx status code."""
    pass


class QuantLibAuthError(QuantLibAPIError):
    """Raised on 401 Unauthorized or 403 Forbidden responses."""

    def __init__(self, message: str = "Authentication failed. Check credentials or token expiry."):
        super().__init__(message, status_code=401)


class QuantLibNotFoundError(QuantLibAPIError):
    """Raised when the requested resource returns 404."""

    def __init__(self, resource: str = "resource"):
        super().__init__(f"Not found: {resource}", status_code=404)


class QuantLibRateLimitError(QuantLibAPIError):
    """Raised on 429 Too Many Requests. Contains retry_after seconds."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds.",
            status_code=429,
        )
        self.retry_after = retry_after


class QuantLibNetworkError(QuantLibError):
    """Raised when the HTTP request fails due to network issues (timeout, DNS, etc.)."""

    def __init__(self, message: str = "Network error. Check that the API server is running."):
        super().__init__(message, status_code=0)


class QuantLibValidationError(QuantLibError):
    """Raised when request parameters fail Pydantic validation before sending."""

    def __init__(self, field: str, message: str):
        super().__init__(f"Validation error on field '{field}': {message}")
        self.field = field
