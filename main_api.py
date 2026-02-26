#!/usr/bin/env python3
"""
QuantLib Pro - FastAPI Application Entry Point

Production-ready REST API server for quantitative finance platform.
Consolidates 30+ specialized applications into a unified API.

Usage:
    python main_api.py                    # Development server
    uvicorn main_api:app --host 0.0.0.0   # Production server

Author: tubakhxn
Date: February 2026
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from quantlib_pro.api.health import router as health_router
from quantlib_pro.api.auth import auth_router
from quantlib_pro.api.routers import (
    macro_router,
    options_router,
    portfolio_router,
    regime_router,
    risk_router,
    volatility_router,
)
from quantlib_pro.api.routers_backtesting import backtesting_router
from quantlib_pro.api.routers_analytics import analytics_router
from quantlib_pro.api.routers_data import data_router
from quantlib_pro.api.routers_realdata import realdata_router
from quantlib_pro.api.routers_market_analysis import market_analysis_router
from quantlib_pro.api.routers_signals import signals_router
from quantlib_pro.api.routers_liquidity import liquidity_router
from quantlib_pro.api.routers_systemic_risk import systemic_risk_router
from quantlib_pro.api.routers_execution import execution_router
from quantlib_pro.api.routers_compliance import compliance_router
from quantlib_pro.api.routers_uat import uat_router
from quantlib_pro.observability import track_api_request

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Handles startup and shutdown procedures.
    """
    # Startup
    logging.info("🚀 QuantLib Pro API starting up...")
    
    # Initialize services (Redis, monitoring, etc.)
    # In production: connect to databases, caches, external services
    
    logging.info("✅ QuantLib Pro API ready to serve requests")
    
    yield  # Application is running
    
    # Shutdown
    logging.info("⚠️  QuantLib Pro API shutting down...")
    # Cleanup: close database connections, flush metrics, etc.
    logging.info("✅ Shutdown complete")


# =============================================================================
# Rate Limiting
# =============================================================================

# Global rate limiter using client IP
limiter = Limiter(key_func=get_remote_address)

# Custom rate limit exceeded handler
def rate_limit_handler(request, exc):
    """Custom handler for rate limit exceeded."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Retry after {exc.retry_after} seconds.",
            "retry_after": exc.retry_after,
            "timestamp": "2026-02-25T00:00:00Z"  # In production: use datetime.utcnow()
        }
    )


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="QuantLib Pro API",
    description="""
    **Enterprise Quantitative Finance Platform**
    
    Production-ready REST API consolidating 30+ specialized quantitative 
    finance applications into a unified, scalable suite.
    
    ## Features
    
    * **Portfolio Optimization**: Modern Portfolio Theory, efficient frontier
    * **Options Pricing**: Black-Scholes, Monte Carlo, Greeks calculations  
    * **Risk Analytics**: VaR, CVaR, stress testing, tail risk
    * **Market Regime Detection**: HMM models, regime switching
    * **Volatility Analytics**: Surface construction, implied volatility
    * **Macro Analysis**: Economic indicators, correlation regimes
    
    ## Authentication
    
    - API Key: Include `X-API-Key` header
    - JWT Bearer: Include `Authorization: Bearer <token>` header
    
    ## Rate Limits
    
    - **Free Tier**: 60 requests/hour
    - **Pro Tier**: 1000 requests/hour  
    - **Enterprise**: Unlimited
    
    ## Support
    
    - Documentation: `/docs`
    - Health Status: `/health`
    - Metrics: `/health/detailed`
    """,
    version="1.0.0",
    contact={
        "name": "QuantLib Pro Support",
        "email": "support@quantlibpro.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc", 
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# =============================================================================
# Middleware Stack
# =============================================================================

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Security: Trusted host middleware (prevent Host header attacks)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"],  # In production: restrict to specific domains
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit app
        "http://localhost:3000",  # React development
        "https://quantlibpro.com",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# =============================================================================
# API Routers
# =============================================================================

# Health and monitoring endpoints
app.include_router(health_router)

# Authentication endpoints
app.include_router(auth_router)

# Core quantitative finance endpoints
app.include_router(
    portfolio_router,
    prefix="/api/v1",
    dependencies=[]  # Add auth dependencies in production
)

app.include_router(
    options_router,
    prefix="/api/v1", 
    dependencies=[]
)

app.include_router(
    risk_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    regime_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    volatility_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    macro_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    backtesting_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    data_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    realdata_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    market_analysis_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    signals_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    liquidity_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    systemic_risk_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    execution_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    compliance_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    uat_router,
    prefix="/api/v1",
    dependencies=[]
)

# =============================================================================
# Root Endpoints
# =============================================================================

@app.get(
    "/",
    summary="API Root", 
    description="Get API information and available endpoints"
)
async def root():
    """API root endpoint with service information."""
    with track_api_request("/", "GET"):
        return {
            "service": "QuantLib Pro API",
            "version": "1.0.0",
            "status": "operational",
            "documentation": "/docs",
            "health": "/health",
            "total_endpoints": 60,
            "endpoints": {
                "authentication": "/auth/*",
                "portfolio": "/api/v1/portfolio/*",
                "options": "/api/v1/options/*",
                "risk": "/api/v1/risk/*",
                "regime": "/api/v1/regime/*",
                "volatility": "/api/v1/volatility/*",
                "macro": "/api/v1/macro/*",
                "backtesting": "/api/v1/backtesting/*",
                "analytics": "/api/v1/analytics/*",
                "data": "/api/v1/data/*",
                "market_analysis": "/api/v1/market-analysis/*",
                "signals": "/api/v1/signals/*",
                "liquidity": "/api/v1/liquidity/*",
                "systemic_risk": "/api/v1/systemic-risk/*",
                "execution": "/api/v1/execution/*",
                "compliance": "/api/v1/compliance/*",
                "uat": "/api/v1/uat/*",
                "health": "/health/*",
            }
        }


@app.get("/api", summary="API Version Info")
async def api_info():
    """Get API version and capabilities."""
    return {
        "api_version": "v1",
        "capabilities": [
            "portfolio_optimization",
            "options_pricing",
            "risk_analysis",
            "market_regime_detection",
            "volatility_analysis",
            "macro_analysis",
            "backtesting",
            "advanced_analytics",
            "data_management",
            "market_analysis",
            "trading_signals",
            "liquidity_microstructure",
            "systemic_risk_contagion",
            "execution_optimization",
            "compliance_governance",
            "uat_stress_monitoring",
        ],
        "rate_limits": {
            "free_tier": "60/hour",
            "pro_tier": "1000/hour", 
            "enterprise": "unlimited"
        }
    }


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    """Run development server."""
    
    # Configure logging for development
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    print("🚀 Starting QuantLib Pro API Server...")
    print("📊 Quantitative Finance Platform")
    print("🌐 Access API documentation at: http://localhost:8000/docs")
    print("❤️  Health checks at: http://localhost:8000/health")
    
    # Run with uvicorn
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
        access_log=True,
    )