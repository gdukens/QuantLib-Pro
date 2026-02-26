"""
Real Data API Endpoints - Quick Reference

NEW ENDPOINTS using Sprint 1-2 data infrastructure:
- Alpha Vantage + Yahoo Finance data providers
- Redis caching with smart TTL
- PostgreSQL + TimescaleDB storage
- Automatic provider fallback

Base URL: http://localhost:8000/api/v1/realdata
"""

# =============================================================================
# 1. REAL-TIME QUOTES
# =============================================================================

## GET /realdata/quote/{symbol}
"""
Get real-time quote for a symbol

Example Request:
  GET /api/v1/realdata/quote/AAPL?use_cache=true

Example Response:
{
  "symbol": "AAPL",
  "price": 150.25,
  "volume": 75000000,
  "timestamp": "2026-02-26 16:00:00",
  "change": 2.50,
  "change_percent": 1.69,
  "provider": "Yahoo Finance",
  "cached": false
}

Query Parameters:
  - use_cache: bool (default: true) - Use Redis cache
"""

## POST /realdata/quote/batch
"""
Get real-time quotes for multiple symbols

Example Request:
  POST /api/v1/realdata/quote/batch?use_cache=true
  {
    "symbols": ["AAPL", "MSFT", "GOOGL"]
  }

Example Response:
{
  "quotes": {
    "AAPL": {
      "symbol": "AAPL",
      "price": 150.25,
      "volume": 75000000,
      "timestamp": "2026-02-26 16:00:00",
      "change": 2.50,
      "change_percent": 1.69,
      "provider": "Alpha Vantage",
      "cached": true
    },
    "MSFT": { ... },
    "GOOGL": { ... }
  },
  "failed_symbols": [],
  "total_time_ms": 245.3
}
"""

# =============================================================================
# 2. HISTORICAL DATA
# =============================================================================

## POST /realdata/historical
"""
Get historical OHLCV data for a symbol

Example Request:
  POST /api/v1/realdata/historical?use_cache=true&store_db=false
  {
    "symbol": "AAPL",
    "period": "1y",
    "adjusted": true
  }

Example Response:
{
  "symbol": "AAPL",
  "period": "1y",
  "data_points": 252,
  "data": [
    {
      "date": "2025-02-26",
      "timestamp": "2025-02-26 00:00:00",
      "open": 148.50,
      "high": 151.20,
      "low": 147.80,
      "close": 150.25,
      "volume": 75000000,
      "adjusted_close": 150.25,
      "dividend": 0.0,
      "split": 1.0
    },
    ...
  ],
  "provider": "Yahoo Finance",
  "cached": false
}

Query Parameters:
  - use_cache: bool (default: true) - Use Redis cache (24h TTL)
  - store_db: bool (default: false) - Store in TimescaleDB hypertable

Valid periods:
  - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max
"""

# =============================================================================
# 3. SYSTEM HEALTH & MONITORING
# =============================================================================

## GET /realdata/health
"""
Check health of data providers and cache

Example Request:
  GET /api/v1/realdata/health

Example Response:
{
  "alpha_vantage": "active",
  "yahoo_finance": "active",
  "cache_connected": true,
  "cache_keys": 1234,
  "cache_hit_rate": 0.85
}

Provider Status Values:
  - active: Working normally
  - rate_limited: Rate limit exceeded (circuit breaker active)
  - failed: Multiple failures (circuit breaker open)
  - unavailable: Not configured or unreachable
"""

## GET /realdata/cache/stats
"""
Get detailed cache statistics

Example Request:
  GET /api/v1/realdata/cache/stats

Example Response:
{
  "connected": true,
  "keys": 1234,
  "memory_used": "10.5 MB",
  "hit_rate": 0.85,
  "uptime_seconds": 86400
}
"""

# =============================================================================
# 4. CACHE MANAGEMENT
# =============================================================================

## POST /realdata/cache/clear/{pattern}
"""
Clear cache keys matching a pattern

Example Request:
  POST /api/v1/realdata/cache/clear/quote:*

Example Response:
{
  "pattern": "quote:*",
  "deleted_keys": 156,
  "timestamp": "2026-02-26T16:00:00Z"
}

Common Patterns:
  - quote:* → Clear all quotes
  - historical:* → Clear all historical data
  - *:AAPL* → Clear all AAPL data
  - correlation_matrix:* → Clear all correlation matrices
"""

## POST /realdata/cache/clear-symbol/{symbol}
"""
Clear all cached data for a specific symbol

Example Request:
  POST /api/v1/realdata/cache/clear-symbol/AAPL

Example Response:
{
  "symbol": "AAPL",
  "deleted_keys": 12,
  "timestamp": "2026-02-26T16:00:00Z"
}
"""

# =============================================================================
# TESTING EXAMPLES
# =============================================================================

"""
1. Test real-time quote:
   curl http://localhost:8000/api/v1/realdata/quote/AAPL

2. Test batch quotes:
   curl -X POST http://localhost:8000/api/v1/realdata/quote/batch \\
     -H "Content-Type: application/json" \\
     -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'

3. Test historical data:
   curl -X POST http://localhost:8000/api/v1/realdata/historical \\
     -H "Content-Type: application/json" \\
     -d '{"symbol": "AAPL", "period": "1mo", "adjusted": true}'

4. Check provider health:
   curl http://localhost:8000/api/v1/realdata/health

5. Get cache stats:
   curl http://localhost:8000/api/v1/realdata/cache/stats

6. Clear quote cache:
   curl -X POST http://localhost:8000/api/v1/realdata/cache/clear/quote:*
"""

# =============================================================================
# CACHE TTL BY DATA TYPE
# =============================================================================

"""
Data Type              TTL      Reason
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
quote                  60s      Real-time data changes frequently
historical             24h      Historical data rarely changes
intraday               5min     Intraday updates every 1-5 minutes
correlation_matrix     1h       Expensive computation
vol_surface            1h       Options data updates hourly
portfolio              5min     User portfolios change infrequently
backtest               2h       Backtest results are stable
regime_state           30min    Market regimes shift slowly
"""

# =============================================================================
# PROVIDER FALLBACK BEHAVIOR
# =============================================================================

"""
1. Primary: Alpha Vantage (if API key configured)
   - High quality data
   - Rate limited: 5/30/75 calls/min (free/basic/premium)
   - Circuit breaker: Opens after 5 failures, recovers after 60s

2. Fallback: Yahoo Finance (always available)
   - Unlimited free tier
   - No API key required
   - Slightly delayed data (~15 minutes)

Automatic Fallback Triggers:
  - Alpha Vantage rate limit exceeded
  - Circuit breaker open
  - API error or timeout
  - No API key configured

Provider Selection:
  - Prefer Alpha Vantage if available and not rate limited
  - Fall back to Yahoo Finance on any error
  - Return "_provider" field in response to show which was used
"""

# =============================================================================
# DATABASE STORAGE
# =============================================================================

"""
TimescaleDB Storage (optional):

When store_db=true is passed to /historical endpoint:
  - Data is stored in TimescaleDB hypertable
  - Partitioned by time (1-day chunks)
  - Indexed by ticker and time
  - Supports fast time-series queries
  - Continuous aggregates for daily/weekly/monthly views

Query stored data directly:
  SELECT * FROM prices 
  WHERE ticker = 'AAPL' 
    AND time >= '2025-01-01' 
  ORDER BY time DESC;

Benefits:
  - Fast historical analysis
  - Time-based aggregations
  - Data compression (50-90% space savings)
  - Automatic retention policies (optional)
"""

# =============================================================================
# INTEGRATION WITH EXISTING ENDPOINTS
# =============================================================================

"""
Existing /api/v1/data endpoints (simulated data):
  ✓ Still available for testing
  ✓ Use for development without API keys
  ✓ Fast (no external API calls)

New /api/v1/realdata endpoints (real data):
  ✓ Use for production
  ✓ Real market data
  ✓ Cached for performance
  ✓ Persistent storage option

Migration Path:
  1. Test with /data endpoints (simulated)
  2. Switch to /realdata endpoints (real data)
  3. Configure Alpha Vantage API key (optional)
  4. Enable Redis caching (recommended)
  5. Enable TimescaleDB storage (optional)
"""

# =============================================================================
# ERROR HANDLING
# =============================================================================

"""
HTTP Status Codes:
  200 OK                 - Success
  400 Bad Request        - Invalid parameters
  404 Not Found          - Symbol not found
  429 Too Many Requests  - Rate limit exceeded
  500 Internal Error     - Server error
  503 Service Unavailable - All providers failed

Error Response Format:
{
  "error": "Failed to fetch quote",
  "detail": "All providers failed for AAPL: Alpha Vantage: rate limit; Yahoo Finance: symbol not found",
  "timestamp": "2026-02-26T16:00:00Z"
}

Rate Limit Response:
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Retry after 60 seconds.",
  "retry_after": 60,
  "timestamp": "2026-02-26T16:00:00Z"
}
"""
