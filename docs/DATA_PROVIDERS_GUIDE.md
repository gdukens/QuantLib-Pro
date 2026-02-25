# Data Providers Integration Guide

Complete guide for integrating additional market data sources into QuantLib Pro.

## Overview

QuantLib Pro supports multiple data providers with automatic failover:

| Provider | Status | Free Tier | API Key Required | Best For |
|----------|--------|-----------|------------------|----------|
| **Yahoo Finance** | ✅ Active | Yes (unlimited) | No | Historical data, quick prototyping |
| **Alpha Vantage** | ✅ Ready | Yes (500/day) | Yes | Backup source, intraday data |
| **FactSet** | ✅ Ready | No | Yes | Enterprise data, fundamentals |
| **Capital IQ** | ⏳ Placeholder | No | Yes | Coming soon - enterprise analytics |

---

## Quick Start

### 1. Alpha Vantage (Free Tier Available)

**Get API Key:**
1. Visit https://www.alphavantage.co/support/#api-key
2. Register for free (5 calls/min, 500 calls/day)
3. Premium plans available for higher limits

**Setup:**

```bash
# Add to .env file
ALPHA_VANTAGE_API_KEY=your_key_here
ALPHA_VANTAGE_ENABLED=true
```

**Usage:**

```python
from quantlib_pro.data.providers import create_alpha_vantage_fetcher
from quantlib_pro.data.fetcher import ResilientDataFetcher

# Option 1: Use Alpha Vantage as fallback
alt_fn = create_alpha_vantage_fetcher()
fetcher = ResilientDataFetcher(alt_api_fn=alt_fn)

data = fetcher.fetch("AAPL", period="1y")
# Tries: Cache → Yahoo Finance → Alpha Vantage → Synthetic

# Option 2: Use Alpha Vantage directly
from quantlib_pro.data.providers import AlphaVantageProvider

provider = AlphaVantageProvider(api_key="YOUR_KEY")
data = provider.fetch("AAPL", start="2024-01-01", end="2024-12-31")

# Get intraday data (5-minute intervals)
intraday = provider.fetch_intraday("AAPL", interval="5min")

# Get real-time quote
quote = provider.get_quote("AAPL")
print(f"Price: ${quote['price']}, Change: {quote['change_percent']}")
```

---

### 2. FactSet (Enterprise)

**Get Credentials:**
1. Contact FactSet sales: https://www.factset.com/contact-us
2. Obtain username and API key (serial)
3. Verify API entitlements for pricing data

**Setup:**

```bash
# Add to .env file
FACTSET_USERNAME=your-username
FACTSET_API_KEY=your-serial-key
FACTSET_ENABLED=true
```

**Usage:**

```python
from quantlib_pro.data.providers import create_factset_fetcher
from quantlib_pro.data.fetcher import ResilientDataFetcher

# Use FactSet as fallback
alt_fn = create_factset_fetcher()
fetcher = ResilientDataFetcher(alt_api_fn=alt_fn)

# FactSet requires region suffix (auto-appended for US stocks)
data = fetcher.fetch("AAPL")  # Auto-converts to "AAPL-US"

# Direct usage
from quantlib_pro.data.providers import FactsetProvider

provider = FactsetProvider(
    username="your-username",
    api_key="your-serial-key"
)

# Fetch pricing data
data = provider.fetch("AAPL-US", start="2024-01-01", end="2024-12-31")

# Get company information
info = provider.get_company_info("AAPL-US")

# Get fundamentals
fundamentals = provider.get_fundamentals(
    "AAPL-US",
    metrics=["FF_SALES", "FF_ASSETS", "FF_EPS_BASIC"],
    start="2020-01-01"
)
```

**FactSet Ticker Formats:**
- US stocks: `AAPL-US`, `MSFT-US`
- UK stocks: `VOD-GB`, `BP/-GB`
- European: `BMW-DE`, `TOT-FR`
- See: https://developer.factset.com/api-catalog/factset-symbology-api

---

### 3. Capital IQ (Coming Soon)

**Status:** Placeholder implementation - awaiting API access.

**Planned Features:**
- Company fundamentals and financials
- Market data and pricing
- Estimates and consensus
- Ownership data
- Credit ratings

**When Available:**

```python
# This will be enabled once API documentation is obtained
from quantlib_pro.data.providers import create_capital_iq_fetcher

alt_fn = create_capital_iq_fetcher(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
```

---

## Multi-Provider Setup (Recommended)

Use `MultiProviderDataFetcher` to automatically try multiple sources:

```python
from quantlib_pro.data.providers import MultiProviderDataFetcher

# Configure with multiple fallbacks
fetcher = MultiProviderDataFetcher(
    enable_alpha_vantage=True,
    enable_factset=True,
    alpha_vantage_key="YOUR_AV_KEY",
    factset_username="YOUR_FS_USERNAME",
    factset_api_key="YOUR_FS_KEY",
)

# Check provider status
status = fetcher.get_provider_status()
print(status)
# {
#   'configured_providers': 2,
#   'providers': ['Alpha Vantage', 'FactSet'],
#   'fallback_chain': [
#     'L1: Memory Cache',
#     'L2: Redis Cache',
#     'L3: File Cache',
#     'L4: Yahoo Finance',
#     'L5: Alpha Vantage',
#     'L6: FactSet',
#     'L7: Synthetic Data (GBM)'
#   ]
# }

# Fetch with full failover
data = fetcher.fetch("AAPL", period="1y")
print(f"Data source: {data.source}")
```

---

## Provider Comparison

### Alpha Vantage

**Pros:**
- ✅ Free tier available (500 calls/day)
- ✅ Easy to get started
- ✅ Intraday data (1min, 5min, 15min, 30min, 60min)
- ✅ Global coverage
- ✅ No credit card required for free tier

**Cons:**
- ⚠️ Rate limits on free tier (5 calls/min)
- ⚠️ Limited fundamental data
- ⚠️ Occasional API downtime

**Best For:** Development, testing, backup data source

### FactSet

**Pros:**
- ✅ Enterprise-grade data quality
- ✅ Comprehensive fundamentals
- ✅ Global coverage (200+ exchanges)
- ✅ Corporate actions, estimates, ownership data
- ✅ Excellent uptime SLA

**Cons:**
- ⚠️ Expensive (enterprise pricing)
- ⚠️ Requires sales contact
- ⚠️ Complex ticker format (region suffixes)

**Best For:** Production systems, institutional use, comprehensive analysis

### Capital IQ

**Pros:**
- ✅ Deep fundamental data
- ✅ Private company coverage
- ✅ Corporate structure mapping
- ✅ Credit ratings integration

**Cons:**
- ⚠️ Enterprise-only (no free tier)
- ⚠️ Not yet implemented in QuantLib Pro
- ⚠️ Requires OAuth 2.0 setup

**Best For:** Credit analysis, M&A research, private markets (when available)

---

## Environment Variables Reference

```bash
# Alpha Vantage
ALPHA_VANTAGE_API_KEY=your_api_key_here
ALPHA_VANTAGE_ENABLED=true

# FactSet
FACTSET_USERNAME=your-username
FACTSET_API_KEY=your-serial-key
FACTSET_ENABLED=true

# Capital IQ (future)
CAPITAL_IQ_CLIENT_ID=your-client-id
CAPITAL_IQ_CLIENT_SECRET=your-client-secret
CAPITAL_IQ_ENABLED=false
```

---

## Error Handling

All providers include comprehensive error handling:

```python
from quantlib_pro.data.providers import AlphaVantageProvider, AlphaVantageError

provider = AlphaVantageProvider(api_key="YOUR_KEY")

try:
    data = provider.fetch("AAPL")
except AlphaVantageError as e:
    if "rate limit" in str(e).lower():
        print("⚠️ Rate limit exceeded - wait 60 seconds")
    elif "api error" in str(e).lower():
        print("❌ Invalid ticker or API issue")
    else:
        print(f"❌ Unexpected error: {e}")
```

Circuit breakers prevent hammering failing services:
- Failure threshold: 3 consecutive failures
- Recovery timeout: 5 minutes
- Automatic retry when circuit closes

---

## Integration with Streamlit App

Update your data management page to show provider status:

```python
# In pages/9_📚_Data_Management.py

from quantlib_pro.data.providers import MultiProviderDataFetcher

st.subheader("📡 Active Data Providers")

fetcher = MultiProviderDataFetcher(
    enable_alpha_vantage=os.getenv("ALPHA_VANTAGE_ENABLED") == "true",
    enable_factset=os.getenv("FACTSET_ENABLED") == "true",
)

status = fetcher.get_provider_status()

for provider in status['providers']:
    st.success(f"✅ {provider} - Active")

# Show fallback chain
with st.expander("View Fallback Chain"):
    for level in status['fallback_chain']:
        st.write(f"→ {level}")
```

---

## Rate Limits & Best Practices

### Alpha Vantage (Free Tier)
- **Limit:** 5 calls/min, 500 calls/day
- **Strategy:** Cache aggressively, use `output_size="compact"` for recent data
- **Upgrade:** Premium tiers: $49.99/mo (75 calls/min), $149.99/mo (300 calls/min)

### FactSet
- **Limit:** Based on subscription tier
- **Strategy:** Batch requests, use date filters
- **Cost:** Contact sales for pricing

### General Best Practices

1. **Enable caching:**
   ```python
   fetcher = MultiProviderDataFetcher(cache_ttl=3600)  # 1 hour cache
   ```

2. **Use appropriate date ranges:**
   ```python
   # Good: Request only needed data
   data = provider.fetch("AAPL", start="2024-01-01", end="2024-12-31")
   
   # Bad: Request full history every time
   data = provider.fetch("AAPL", output_size="full")
   ```

3. **Handle errors gracefully:**
   ```python
   try:
       data = fetcher.fetch("AAPL")
   except Exception as e:
       st.warning(f"Using cached data due to: {e}")
       data = load_from_cache("AAPL")
   ```

---

## Troubleshooting

### Alpha Vantage Issues

**"Note: Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute..."**
- You've hit the rate limit
- Solution: Wait 60 seconds or upgrade to premium

**"Invalid API call. Please retry or visit the documentation..."**
- Invalid ticker or malformed request
- Check ticker format (should be plain symbols: "AAPL", not "AAPL-US")

### FactSet Issues

**401 Unauthorized**
- Check username and API key format
- Verify credentials: `username-serial` format

**403 Forbidden**
- Subscription doesn't include requested data type
- Contact FactSet to verify entitlements

**Ticker Format Errors**
- Remember to use region suffixes: "AAPL-US", not "AAPL"
- Use `provider.fetch("AAPL")` - auto-appends "-US"

---

## Next Steps

1. **Get API keys:**
   - Alpha Vantage: https://www.alphavantage.co/support/#api-key
   - FactSet: Contact sales team

2. **Update `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Test integration:**
   ```bash
   python -c "
   from quantlib_pro.data.providers import AlphaVantageProvider
   provider = AlphaVantageProvider()
   data = provider.fetch('AAPL', output_size='compact')
   print(f'✅ Retrieved {len(data)} rows')
   "
   ```

4. **Update Streamlit app** to use `MultiProviderDataFetcher`

5. **Monitor usage** to avoid rate limits

---

## Support

**Alpha Vantage:**
- Documentation: https://www.alphavantage.co/documentation/
- Support: support@alphavantage.co

**FactSet:**
- Developer Portal: https://developer.factset.com/
- Support: Contact your account manager

**Capital IQ:**
- Support: https://www.spglobal.com/marketintelligence/en/support
- Contact: Your S&P Global representative

**QuantLib Pro:**
- GitHub Issues: https://github.com/your-repo/issues
- Internal docs: See `docs/` directory
