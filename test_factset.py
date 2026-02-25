"""
Quick test for FactSet provider.
Run this after you've configured FactSet OAuth2 credentials.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("  FactSet OAuth2 Quick Test")
print("=" * 70)

client_id = os.getenv("FACTSET_CLIENT_ID")
jwk_path = os.getenv("FACTSET_JWK_PATH")

print(f"\n✓ Client ID: {client_id[:16] if client_id else 'NOT_SET'}...")
print(f"✓ JWK Path: {jwk_path}")

if not client_id or not jwk_path:
    print("\n" + "="*70)
    print("❌ OAUTH2 CREDENTIALS NOT CONFIGURED")
    print("="*70)
    print("\nYou need to configure FactSet OAuth2 credentials.")
    print("Follow the instructions in FACTSET_SETUP.md")
    print("\nQuick steps:")
    print("1. Create factset_jwk.json with your OAuth2 credentials")
    print("2. Update .env:")
    print("   FACTSET_CLIENT_ID=your_client_id_here")
    print("   FACTSET_JWK_PATH=factset_jwk.json")
    print("   FACTSET_ENABLED=true")
    exit(1)

# Check JWK file exists
if jwk_path and not os.path.exists(jwk_path):
    print(f"\n❌ JWK file not found: {jwk_path}")
    print("Create the file with your FactSet OAuth2 credentials.")
    exit(1)

print(f"✓ JWK file exists: {jwk_path}")

# Check IP address
try:
    import requests
    current_ip = requests.get("https://api.ipify.org", timeout=5).text
    expected_ip = "173.206.223.186"
    
    print(f"\n✓ Current IP: {current_ip}")
    print(f"✓ Whitelisted IP: {expected_ip}")
    
    if current_ip != expected_ip:
        print(f"\n⚠️  WARNING: IP MISMATCH")
        print(f"   Your current IP ({current_ip}) is not whitelisted!")
        print(f"   FactSet will reject requests.")
        print(f"   Contact FactSet support to add {current_ip} to whitelist.")
except Exception as e:
    print(f"\n⚠️  Could not check IP: {e}")
    current_ip = "unknown"

try:
    from quantlib_pro.data.providers import FactsetProvider
    
    provider = FactsetProvider(client_id=client_id, jwk_path=jwk_path)
    print("\n✓ Provider initialized")
    print("✓ OAuth2 configuration loaded")
    
    # Test: Fetch historical data
    print("\nTest: Fetching historical data for AAPL-US...")
    print("(FactSet requires region suffix: AAPL-US, MSFT-US, etc.)")
    
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    try:
        data = provider.fetch(
            ticker="AAPL",  # Will auto-append -US
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d")
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"   Rows: {len(data)}")
        print(f"   Date range: {data.index[0]} to {data.index[-1]}")
        print(f"   Latest close: ${data['Close'].iloc[-1]:.2f}")
        print(f"\nData preview:")
        print(data.tail(3))
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ FAILED: {e}")
        
        # Print detailed traceback for debugging
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()
        
        if "401" in error_msg:
            print("\n🔒 HTTP 401: Unauthorized")
            print("   → Your API key or username is incorrect")
            print("   → Double-check FACTSET_API_KEY in .env")
            print("   → Verify username format: UOTTAWA_CA-2235705")
        
        elif "403" in error_msg:
            print("\n🚫 HTTP 403: Forbidden")
            print("   → Your IP address is not whitelisted")
            print(f"   → Current IP: {current_ip}")
            print("   → Contact FactSet to whitelist this IP")
        
        elif "429" in error_msg:
            print("\n⏱️  HTTP 429: Rate Limit Exceeded")
            print("   → You've hit your API rate limit")
            print("   → Wait and try again")
            print("   → Contact FactSet to increase limits")
        
        elif "500" in error_msg:
            print("\n⚠️  HTTP 500: Server Error")
            print("   → FactSet API is experiencing issues")
            print("   → Or your API key is invalid")
            print("   → Check https://status.factset.com/")
    
    print("\n" + "=" * 70)
    print("  Test Complete")
    print("=" * 70)
    print("\nNext steps:")
    print("✅ Alpha Vantage: Working!")
    if 'data' in locals() and len(data) > 0:
        print("✅ FactSet: Working!")
        print("\nYou now have multi-provider failover:")
        print("   Cache → Yahoo → Alpha Vantage → FactSet → Synthetic")
    else:
        print("⏳ FactSet: Fix the errors above")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
