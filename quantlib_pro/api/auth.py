"""
Authentication router for user management and JWT token operations.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from quantlib_pro.api.dependencies import (
    auth_service,
    get_current_user,
    require_authentication,
    User,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Authentication Models
# =============================================================================

class LoginRequest(BaseModel):
    """User login request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """User registration request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=2, description="User full name")
    organization: str = Field(None, description="Organization name (optional)")


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user_info: Dict[str, Any] = Field(..., description="User information")


class UserProfile(BaseModel):
    """User profile information."""
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    tier: str = Field(..., description="Subscription tier")
    organization: str = Field(None, description="Organization")
    created_at: datetime = Field(..., description="Account creation date")
    last_login: datetime = Field(None, description="Last login time")
    api_calls_used: int = Field(..., description="API calls used this period")
    api_calls_limit: int = Field(..., description="API calls limit")


# =============================================================================
# Authentication Router
# =============================================================================

auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Demo user database (in production: use proper database)
DEMO_USERS = {
    "demo@quantlibpro.com": {
        "user_id": "user_demo_123",
        "email": "demo@quantlibpro.com", 
        "password_hash": "demo_hashed_password",
        "full_name": "Demo User",
        "tier": "pro",
        "organization": "QuantLib Pro",
        "permissions": ["basic", "portfolio", "options", "risk"],
        "created_at": datetime(2026, 1, 1),
        "last_login": None,
        "api_calls_used": 0,
        "api_calls_limit": 1000
    },
    "admin@quantlibpro.com": {
        "user_id": "user_admin_456",
        "email": "admin@quantlibpro.com",
        "password_hash": "admin_hashed_password", 
        "full_name": "Admin User",
        "tier": "admin",
        "organization": "QuantLib Pro",
        "permissions": ["admin"], 
        "created_at": datetime(2026, 1, 1),
        "last_login": None,
        "api_calls_used": 0,
        "api_calls_limit": 999999
    }
}


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT token."""
    try:
        user_data = DEMO_USERS.get(request.email.lower())
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # For demo: simple password check
        if request.password != "demo123456":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        user_data["last_login"] = datetime.utcnow()
        
        # Create JWT token
        token_payload = {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tier": user_data["tier"],
            "permissions": user_data["permissions"],
            "iat": datetime.utcnow()
        }
        
        access_token = auth_service.create_access_token(token_payload)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,
            user_info={
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "tier": user_data["tier"],
                "organization": user_data["organization"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error"
        )


@auth_router.get(
    "/profile",
    response_model=UserProfile,
    summary="Get user profile",
)
async def get_profile(
    current_user: User = Depends(require_authentication)
) -> UserProfile:
    """Get current user profile information."""
    try:
        user_data = None
        for email, data in DEMO_USERS.items():
            if data["user_id"] == current_user.user_id:
                user_data = data
                break
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserProfile(
            user_id=user_data["user_id"],
            email=user_data["email"], 
            full_name=user_data["full_name"],
            tier=user_data["tier"],
            organization=user_data["organization"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"],
            api_calls_used=user_data["api_calls_used"],
            api_calls_limit=user_data["api_calls_limit"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error fetching profile"
        )


@auth_router.get(
    "/verify-token",
    summary="Verify JWT token",
)
async def verify_token(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify if current JWT token is valid."""
    if current_user:
        return {
            "valid": True,
            "user_id": current_user.user_id,
            "email": current_user.email,
            "tier": current_user.tier,
            "permissions": current_user.permissions
        }
    else:
        return {
            "valid": False,
            "message": "Invalid or expired token"
        }