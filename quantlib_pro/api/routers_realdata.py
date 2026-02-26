"""
Real Data API Router - Uses Alpha Vantage + Yahoo Finance

New endpoints that integrate with the Sprint 1-2 data infrastructure:
- Real-time quotes from Alpha Vantage/Yahoo Finance
- Historical data with automatic fallback
- Redis caching with smart TTL
- Database persistence (PostgreSQL + TimescaleDB)
- Provider health monitoring
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from quantlib_pro.data.data_router import DataProviderRouter
from quantlib_pro.data.cache_manager import CacheManager
from quantlib_pro.data.database import get_postgres_session, get_timescale_session
from quantlib_pro.data.models import User, Portfolio, Holding, Price

logger = logging.getLogger(__name__)

realdata_router = APIRouter(prefix="/realdata", tags=["real-data"])

# Initialize global data router and cache (reuse connections)
_data_router: Optional[DataProviderRouter] = None
_cache_manager: Optional[CacheManager] = None


def get_data_router() -> DataProviderRouter:
    """Dependency for data router."""
    global _data_router
    if _data_router is None:
        _data_router = DataProviderRouter()
    return _data_router


def get_cache() -> CacheManager:
    """Dependency for cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# =============================================================================
# Models
# =============================================================================

class QuoteResponse(BaseModel):
    symbol: str
    price: float
    volume: int
    timestamp: str
    change: float
    change_percent: float
    provider: str
    cached: bool


class HistoricalDataRequest(BaseModel):
    symbol: str
    period: str = Field(default="1y", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max")
    adjusted: bool = Field(default=True, description="Adjust for dividends and splits")


class HistoricalDataResponse(BaseModel):
    symbol: str
    period: str
    data_points: int
    data: List[Dict[str, Any]]
    provider: str
    cached: bool


class BatchQuoteRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1, max_length=50)


class BatchQuoteResponse(BaseModel):
    quotes: Dict[str, QuoteResponse]
    failed_symbols: List[str]
    total_time_ms: float


class ProviderHealthResponse(BaseModel):
    alpha_vantage: str
    yahoo_finance: str
    cache_connected: bool
    cache_keys: int
    cache_hit_rate: float


class CacheStatsResponse(BaseModel):
    connected: bool
    keys: int
    memory_used: str
    hit_rate: float
    uptime_seconds: int


# =============================================================================
# Endpoints: Real-Time Quotes
# =============================================================================

@realdata_router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_real_quote(
    symbol: str,
    use_cache: bool = Query(True, description="Use Redis cache"),
    router: DataProviderRouter = Depends(get_data_router),
    cache: CacheManager = Depends(get_cache)
):
    """
    Get real-time quote for a symbol.
    
    - Tries cache first (TTL: 60s)
    - Falls back to Alpha Vantage → Yahoo Finance
    - Returns provider name and cache status
    """
    try:
        cached = False
        
        # Try cache first
        if use_cache:
            cached_quote = cache.get("quote", symbol)
            if cached_quote:
                cached_quote["cached"] = True
                return QuoteResponse(**cached_quote)
        
        # Fetch from API
        quote = router.get_quote(symbol)
        
        # Cache it
        if use_cache:
            cache.set("quote", quote, symbol)
        
        return QuoteResponse(
            symbol=quote["symbol"],
            price=quote["price"],
            volume=quote["volume"],
            timestamp=quote["timestamp"],
            change=quote.get("change", 0),
            change_percent=float(quote.get("change_percent", 0)),
            provider=quote["_provider"],
            cached=cached
        )
    
    except Exception as e:
        logger.error(f"Failed to get quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {str(e)}")


@realdata_router.post("/quote/batch", response_model=BatchQuoteResponse)
async def get_batch_quotes(
    request: BatchQuoteRequest,
    use_cache: bool = Query(True),
    router: DataProviderRouter = Depends(get_data_router),
    cache: CacheManager = Depends(get_cache)
):
    """
    Get real-time quotes for multiple symbols.
    
    - Processes symbols in parallel
    - Returns partial results if some symbols fail
    """
    import time
    start_time = time.time()
    
    try:
        quotes = {}
        failed = []
        
        for symbol in request.symbols:
            try:
                # Try cache first
                cached_quote = None
                if use_cache:
                    cached_quote = cache.get("quote", symbol)
                
                if cached_quote:
                    quotes[symbol] = QuoteResponse(**{**cached_quote, "cached": True})
                else:
                    # Fetch from API
                    quote = router.get_quote(symbol)
                    
                    # Cache it
                    if use_cache:
                        cache.set("quote", quote, symbol)
                    
                    quotes[symbol] = QuoteResponse(
                        symbol=quote["symbol"],
                        price=quote["price"],
                        volume=quote["volume"],
                        timestamp=quote["timestamp"],
                        change=quote.get("change", 0),
                        change_percent=float(quote.get("change_percent", 0)),
                        provider=quote["_provider"],
                        cached=False
                    )
            except Exception as e:
                logger.warning(f"Failed to get quote for {symbol}: {e}")
                failed.append(symbol)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return BatchQuoteResponse(
            quotes=quotes,
            failed_symbols=failed,
            total_time_ms=elapsed_ms
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch quote failed: {str(e)}")


# =============================================================================
# Endpoints: Historical Data
# =============================================================================

@realdata_router.post("/historical", response_model=HistoricalDataResponse)
async def get_historical_data(
    request: HistoricalDataRequest,
    use_cache: bool = Query(True),
    store_db: bool = Query(False, description="Store data in TimescaleDB"),
    router: DataProviderRouter = Depends(get_data_router),
    cache: CacheManager = Depends(get_cache)
):
    """
    Get historical OHLCV data for a symbol.
    
    - Tries cache first (TTL: 24h)
    - Falls back to Alpha Vantage → Yahoo Finance
    - Optionally stores data in TimescaleDB hypertable
    """
    try:
        cached = False
        
        # Try cache first
        if use_cache:
            cached_data = cache.get("historical", request.symbol, request.period)
            if cached_data:
                return HistoricalDataResponse(
                    symbol=cached_data["symbol"],
                    period=request.period,
                    data_points=len(cached_data["data"]),
                    data=cached_data["data"],
                    provider=cached_data.get("_provider", "cache"),
                    cached=True
                )
        
        # Fetch from API
        historical = router.get_historical(
            request.symbol,
            period=request.period,
            adjusted=request.adjusted
        )
        
        # Cache it
        if use_cache:
            cache.set("historical", historical, request.symbol, request.period)
        
        # Store in TimescaleDB
        if store_db:
            try:
                with get_timescale_session() as session:
                    for day in historical["data"]:
                        price = Price(
                            time=day["date"],
                            ticker=request.symbol,
                            open=day["open"],
                            high=day["high"],
                            low=day["low"],
                            close=day["close"],
                            volume=day["volume"],
                            adjusted_close=day.get("adjusted_close", day["close"])
                        )
                        session.merge(price)  # Update if exists
                    session.commit()
                    logger.info(f"Stored {len(historical['data'])} price records for {request.symbol}")
            except Exception as e:
                logger.warning(f"Failed to store in TimescaleDB: {e}")
        
        return HistoricalDataResponse(
            symbol=historical["symbol"],
            period=request.period,
            data_points=len(historical["data"]),
            data=historical["data"],
            provider=historical["_provider"],
            cached=False
        )
    
    except Exception as e:
        logger.error(f"Failed to get historical data for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")


# =============================================================================
# Endpoints: System Status
# =============================================================================

@realdata_router.get("/health", response_model=ProviderHealthResponse)
async def get_provider_health(
    router: DataProviderRouter = Depends(get_data_router),
    cache: CacheManager = Depends(get_cache)
):
    """
    Check health of data providers and cache.
    
    - Provider status (active, rate_limited, failed, unavailable)
    - Cache connection status
    - Cache hit rate
    """
    try:
        provider_status = router.get_provider_status()
        cache_stats = cache.get_stats()
        
        return ProviderHealthResponse(
            alpha_vantage=provider_status.get("alpha_vantage", "unavailable"),
            yahoo_finance=provider_status.get("yahoo_finance", "active"),
            cache_connected=cache_stats.get("connected", False),
            cache_keys=cache_stats.get("keys", 0),
            cache_hit_rate=cache_stats.get("hit_rate", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@realdata_router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(cache: CacheManager = Depends(get_cache)):
    """
    Get detailed cache statistics.
    
    - Total keys
    - Memory usage
    - Hit rate
    - Uptime
    """
    try:
        stats = cache.get_stats()
        return CacheStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@realdata_router.post("/cache/clear/{pattern}")
async def clear_cache_pattern(
    pattern: str,
    cache: CacheManager = Depends(get_cache)
):
    """
    Clear cache keys matching a pattern.
    
    Examples:
    - /cache/clear/quote:* → Clear all quotes
    - /cache/clear/*:AAPL* → Clear all AAPL data
    - /cache/clear/historical:* → Clear all historical data
    """
    try:
        deleted = cache.invalidate_pattern(pattern)
        return {
            "pattern": pattern,
            "deleted_keys": deleted,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@realdata_router.post("/cache/clear-symbol/{symbol}")
async def clear_symbol_cache(
    symbol: str,
    cache: CacheManager = Depends(get_cache)
):
    """
    Clear all cached data for a specific symbol.
    """
    try:
        deleted = cache.invalidate_symbol(symbol)
        return {
            "symbol": symbol,
            "deleted_keys": deleted,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear symbol cache: {str(e)}")
