# FactSet Integration Setup Guide

## Your FactSet Account Details

- **Account ID**: `UOTTAWA_CA-2235705`
- **API Key Name**: `quant`
- **IP Whitelist**: `173.206.223.186`

## Required API

The integration expects the **FactSet Prices API** (also called FactSet Content API - Prices v1).

**API Documentation**: https://developer.factset.com/api-catalog/factset-prices-api

### What this API provides:
- ✅ Historical end-of-day pricing (OHLCV)
- ✅ Intraday pricing data
- ✅ Corporate actions (splits, dividends)
- ✅ Multi-exchange coverage (200+ exchanges globally)
- ✅ Multiple currencies

## How to Get Your API Serial Key

### Option 1: FactSet Developer Portal (Web)

1. **Log in** to FactSet Developer Portal:
   - Go to: https://developer.factset.com/
   - Use your FactSet credentials

2. **Navigate to API Keys**:
   - Click on your profile (top right)
   - Select **"API Keys"** from the menu

3. **Find your "quant" key**:
   - You should see a key named **"quant"**
   - Click on it to view details

4. **Copy the Serial Key**:
   - Look for the **"Serial"** or **"API Key"** field
   - It should be a long alphanumeric string
   - Copy this value

5. **Update .env file**:
   ```bash
   FACTSET_API_KEY=your_serial_key_here
   FACTSET_ENABLED=true
   ```

### Option 2: FactSet Terminal

1. Open FactSet Terminal
2. Type: `FDSAPI`
3. Find API Keys section
4. Locate "quant" key
5. Copy the Serial Key

### Option 3: Contact FactSet Support

If you can't access the API keys section:

**Email**: support@factset.com  
**Subject**: Request API Serial Key for Account UOTTAWA_CA-2235705

**Message template**:
```
Hello,

I need to retrieve the API Serial Key for my account.

Account ID: UOTTAWA_CA-2235705
API Key Name: quant
Purpose: Integrating with FactSet Prices API

Could you please provide the serial key or guide me on how to access it?

Thank you.
```

## Verifying Your IP Address

The API key is restricted to IP: **173.206.223.186**

**Check your current IP**:
```powershell
# Windows
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

If your IP doesn't match `173.206.223.186`, you'll need to:
1. Contact FactSet support to update the IP whitelist
2. Or connect from the whitelisted IP address

## Testing the Integration

Once you have the serial key:

1. **Update .env**:
   ```bash
   FACTSET_API_KEY=your_actual_serial_key_here
   FACTSET_ENABLED=true
   ```

2. **Test the connection**:
   ```powershell
   python test_factset.py
   ```

3. **Or run the full test suite**:
   ```powershell
   python test_providers.py
   ```

## Troubleshooting

### Error: HTTP 401 (Unauthorized)
- ❌ Serial key is incorrect
- ❌ Username format is wrong (should be: UOTTAWA_CA-2235705)
- ✅ **Fix**: Double-check the serial key from FactSet portal

### Error: HTTP 403 (Forbidden)
- ❌ Your IP address is not whitelisted
- ✅ **Fix**: Check your IP with `(Invoke-WebRequest -Uri "https://api.ipify.org").Content`
- ✅ Contact FactSet to add your current IP to the whitelist

### Error: HTTP 500 (Internal Server Error)
- ❌ API key is still set to placeholder value
- ✅ **Fix**: Replace `REPLACE_WITH_YOUR_FACTSET_SERIAL_KEY` with actual key

### Error: "Rate limit exceeded"
- FactSet rate limits depend on your subscription tier
- Wait and retry, or contact FactSet to increase limits

## API Pricing & Limits

FactSet is an **enterprise subscription service**. Your rate limits and access depend on your University of Ottawa subscription.

**Contact your FactSet account manager** if you need:
- Higher rate limits
- Additional APIs (Fundamentals, Estimates, etc.)
- More IP addresses whitelisted

## Next Steps

✅ **Alpha Vantage**: Already working!  
⏳ **FactSet**: Get the serial key and update .env  
❌ **Capital IQ**: Not yet implemented (coming soon)

Once FactSet is configured, you'll have enterprise-grade multi-provider failover:
```
Your Data → Cache → Yahoo Finance → Alpha Vantage → FactSet → Synthetic Data
```

Need help? Check [docs/DATA_PROVIDERS_GUIDE.md](docs/DATA_PROVIDERS_GUIDE.md)
