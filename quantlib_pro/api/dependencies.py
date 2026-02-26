"""
FastAPI dependencies for request handling, authentication, and common services.

Week 11: API Layer - Enhanced dependency injection with JWT authentication,
                     role-based access control, and tiered rate limiting.
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Annotated, Optional, Dict, Any

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address

from quantlib_pro.observability import (
    check_health,
    get_performance_monitor,
    track_api_request,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

# JWT Configuration
JWT_SECRET_KEY = "your-secret-key-here"  # In production: use environment variable
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Rate Limiting Configuration
RATE_LIMITS = {
    "free": "60/hour",
    "pro": "1000/hour", 
    "enterprise": "10000/hour",
    "admin": "unlimited"
}

# =============================================================================
# Rate Limiting
# =============================================================================

limiter = Limiter(key_func=get_remote_address)


def get_user_rate_limit(user_tier: str) -> str:
    """Get rate limit based on user tier."""
    return RATE_LIMITS.get(user_tier, "60/hour")


# =============================================================================
# JWT Authentication
# =============================================================================

class AuthenticationService:
    """JWT Authentication service."""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


# Global authentication service
auth_service = AuthenticationService()
security = HTTPBearer(auto_error=False)


# =============================================================================
# User Models
# =============================================================================

class User:
    """User model for API authentication."""
    
    def __init__(self, user_id: str, email: str, tier: str, permissions: list):
        self.user_id = user_id
        self.email = email
        self.tier = tier
        self.permissions = permissions
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions or "admin" in self.permissions


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_api_key(
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> Optional[str]:
    """Extract API key from header."""
    return x_api_key


async def verify_api_key(
    api_key: Annotated[Optional[str], Depends(get_api_key)],
) -> str:
    """
    Verify API key (production implementation should use database).
    
    Raises:
        HTTPException: If API key is invalid or missing.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In production: validate against database/cache
    # For demo: simple validation
    if len(api_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return api_key


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ] = None,
) -> Optional[User]:
    """
    Get current user from JWT Bearer token.
    
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Verify JWT token
        payload = auth_service.verify_token(credentials.credentials)
        
        # In production: fetch user from database using payload['user_id']
        # For demo: create user from token payload
        user = User(
            user_id=payload.get("user_id", "demo_user"),
            email=payload.get("email", "demo@quantlibpro.com"),
            tier=payload.get("tier", "free"),
            permissions=payload.get("permissions", ["basic"])
        )
        
        return user
        
    except HTTPException:
        # Token validation failed - return None for optional auth
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


async def require_authentication(
    user: Annotated[Optional[User], Depends(get_current_user)],
) -> User:
    """
    Require authentication for endpoint.
    
    Raises:
        HTTPException: If not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_permission(permission: str):
    """Decorator to require specific permission."""
    async def permission_checker(
        user: Annotated[User, Depends(require_authentication)]
    ) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user
    
    return permission_checker


# =============================================================================
# Rate Limiting Dependencies
# =============================================================================

async def check_rate_limit(
    request: Request,
    user: Annotated[Optional[User], Depends(get_current_user)] = None,
) -> None:
    """
    Check rate limits based on user tier.
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Get user tier for rate limiting
    user_tier = user.tier if user else "free"
    
    # Skip rate limiting for admin and enterprise users in demo
    if user_tier in ["admin", "enterprise"]:
        return
    
    # Apply rate limiting based on tier
    rate_limit = get_user_rate_limit(user_tier)
    
    # In production: implement proper rate limiting with Redis
    # For demo: simplified rate limiting
    try:
        # This would use slowapi limiter in production
        # limiter.limit(rate_limit)(request)
        pass
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {user_tier} tier. Limit: {rate_limit}"
        )


# =============================================================================
# Service Dependencies
# =============================================================================

@lru_cache()
def get_settings():
    """Get application settings (cached)."""
    return {
        "app_name": "QuantLib Pro API",
        "version": "1.0.0",
        "debug": True,  # In production: from environment
    }


async def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    monitor = get_performance_monitor()
    return {
        "active_requests": monitor.active_requests,
        "total_requests": monitor.total_requests,
        "average_response_time": monitor.average_response_time,
        "error_rate": monitor.error_rate
    }


async def health_check_dependency() -> Dict[str, str]:
    """Health check dependency for endpoints."""
    health = check_health()
    if health["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
    return health


# =============================================================================
# Rate Limiting Dependencies
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    In production: use Redis-backed rate limiter like slowapi.
    """
    
    def __init__(self, requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests: Max requests per window
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self._requests: dict[str, list[datetime]] = {}
    
    def _clean_old_requests(self, client_id: str) -> None:
        """Remove requests outside current window."""
        if client_id not in self._requests:
            return
        
        cutoff = datetime.utcnow() - timedelta(seconds=self.window)
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if req_time > cutoff
        ]
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        self._clean_old_requests(client_id)
        
        if client_id not in self._requests:
            self._requests[client_id] = []
        
        if len(self._requests[client_id]) >= self.requests:
            return False
        
        self._requests[client_id].append(datetime.utcnow())
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        self._clean_old_requests(client_id)
        
        if client_id not in self._requests:
            return self.requests
        
        return max(0, self.requests - len(self._requests[client_id]))


# Global rate limiter instance
_rate_limiter = RateLimiter(requests=100, window=60)


async def check_rate_limit(
    request: Request,
    api_key: Annotated[Optional[str], Depends(get_api_key)] = None,
) -> None:
    """
    Check rate limit for request.
    
    Raises:
        HTTPException: If rate limit exceeded.
    """
    # Use API key or IP as client identifier
    client_id = api_key if api_key else request.client.host
    
    if not _rate_limiter.is_allowed(client_id):
        remaining = _rate_limiter.get_remaining(client_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(_rate_limiter.requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(_rate_limiter.window),
            },
        )


# =============================================================================
# Service Dependencies
# =============================================================================

@lru_cache()
def get_settings():
    """
    Get application settings (cached).
    
    In production: load from environment variables or config service.
    """
    return {
        "app_name": "QuantLib Pro API",
        "version": "1.0.0",
        "environment": "development",
        "max_request_size": 10 * 1024 * 1024,  # 10 MB
        "default_page_size": 50,
        "max_page_size": 1000,
    }


async def get_db():
    """
    Get database connection (placeholder).
    
    In production: yield database session from connection pool.
    """
    # Placeholder for database dependency
    # In production:
    # try:
    #     db = SessionLocal()
    #     yield db
    # finally:
    #     db.close()
    
    yield None


async def get_cache():
    """
    Get cache connection (placeholder).
    
    In production: yield Redis connection from pool.
    """
    # Placeholder for cache dependency
    # In production:
    # try:
    #     cache = redis.Redis(...)
    #     yield cache
    # finally:
    #     cache.close()
    
    yield None


# =============================================================================
# Request Tracking Dependencies
# =============================================================================

async def track_request(
    request: Request,
) -> None:
    """
    Track API request for monitoring.
    
    Integrates with observability layer to track request metrics.
    """
    endpoint = request.url.path
    method = request.method
    
    # Track in performance monitor
    monitor = get_performance_monitor()
    monitor.record(
        name=f"{method} {endpoint}",
        duration=0.0,  # Will be updated by middleware
        error=False,
    )


# =============================================================================
# Pagination Dependencies
# =============================================================================

async def get_pagination(
    skip: int = 0,
    limit: int = 50,
    settings: dict = Depends(get_settings),
) -> dict[str, int]:
    """
    Get pagination parameters.
    
    Args:
        skip: Number of records to skip
        limit: Max number of records to return
        settings: Application settings
    
    Returns:
        Dictionary with skip and limit values
    
    Raises:
        HTTPException: If pagination parameters invalid
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip must be non-negative",
        )
    
    max_limit = settings["max_page_size"]
    if limit < 1 or limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit must be between 1 and {max_limit}",
        )
    
    return {"skip": skip, "limit": limit}


# =============================================================================
# Health Check Dependencies
# =============================================================================

async def verify_system_health() -> bool:
    """
    Verify system health before processing requests.
    
    Returns:
        True if system is healthy
    
    Raises:
        HTTPException: If system is unhealthy
    """
    health = check_health()
    
    if health.overall_status.name == "UNHEALTHY":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is unhealthy",
        )
    
    return True


# =============================================================================
# Input Validation Dependencies
# =============================================================================

async def validate_date_range(
    start_date: str,
    end_date: str,
) -> tuple[str, str]:
    """
    Validate date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Validated date range
    
    Raises:
        HTTPException: If date range is invalid
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}",
        )
    
    if start >= end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date",
        )
    
    # Check date range is not too large (e.g., max 10 years)
    max_days = 365 * 10
    if (end - start).days > max_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Date range too large (max {max_days} days)",
        )
    
    return start_date, end_date


async def validate_tickers(
    tickers: list[str],
    max_tickers: int = 50,
) -> list[str]:
    """
    Validate ticker list.
    
    Args:
        tickers: List of ticker symbols
        max_tickers: Maximum number of tickers allowed
    
    Returns:
        Validated ticker list
    
    Raises:
        HTTPException: If tickers are invalid
    """
    if not tickers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one ticker required",
        )
    
    if len(tickers) > max_tickers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {max_tickers} tickers allowed",
        )
    
    # Validate ticker format (simple check)
    for ticker in tickers:
        if not ticker or not ticker.replace(".", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ticker format: {ticker}",
            )
    
    return tickers
