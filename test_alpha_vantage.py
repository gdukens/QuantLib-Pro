"""
Quick test for Alpha Vantage provider with your API key.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("  Alpha Vantage Quick Test")
print("=" * 70)

api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
print(f"\n✓ API Key loaded: ***{api_key[-4:] if api_key else 'NOT_FOUND'}")

if not api_key or api_key == "REPLACE_WITH_ALPHA_VANTAGE_KEY":
    print("❌ Please set ALPHA_VANTAGE_API_KEY in .env file")
    exit(1)

try:
    from quantlib_pro.data.providers import AlphaVantageProvider
    
    provider = AlphaVantageProvider(api_key=api_key)
    print("✓ Provider initialized\n")
    
    # Test 1: Get real-time quote (uses less API quota)
    print("Test 1: Fetching real-time quote for AAPL...")
    try:
        quote = provider.get_quote("AAPL")
        print(f"✅ SUCCESS!")
        print(f"   Price: ${quote['price']:.2f}")
        print(f"   Change: {quote['change_percent']}")
        print(f"   Volume: {quote.get('volume', 'N/A')}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        if "rate limit" in str(e).lower() or "please retry" in str(e).lower():
            print("\n⚠️  RATE LIMIT HIT")
            print("   Free tier: 5 calls/minute, 500 calls/day")
            print("   Wait 60 seconds and try again")
    
    print("\n" + "=" * 70)
    print("  Test Complete")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
