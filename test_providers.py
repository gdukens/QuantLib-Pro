"""
Test script for data provider integrations.

Run this script to verify your provider credentials and configurations.

Usage:
    python test_providers.py
"""

import os
import sys
from datetime import datetime, timedelta

def test_alpha_vantage():
    """Test Alpha Vantage provider."""
    print("\n" + "="*60)
    print("Testing Alpha Vantage Provider")
    print("="*60)
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not set in environment")
        print("   Set it in .env file or export it:")
        print("   export ALPHA_VANTAGE_API_KEY=your_key_here")
        return False
    
    print(f"✓ API Key found: ***{api_key[-4:]}")
    
    try:
        from quantlib_pro.data.providers import AlphaVantageProvider
        
        provider = AlphaVantageProvider(api_key=api_key)
        print("✓ Provider initialized")
        
        # Test quote fetch
        print("\nFetching real-time quote for AAPL...")
        quote = provider.get_quote("AAPL")
        print(f"✅ Quote: ${quote['price']:.2f} ({quote['change_percent']})")
        
        # Test historical data fetch (compact to save API calls)
        print("\nFetching historical data (compact)...")
        data = provider.fetch("AAPL", output_size="compact")
        print(f"✅ Retrieved {len(data)} rows")
        print(f"   Date range: {data.index[0]} to {data.index[-1]}")
        print(f"   Latest close: ${data['Close'].iloc[-1]:.2f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Alpha Vantage test failed: {e}")
        return False


def test_factset():
    """Test FactSet provider."""
    print("\n" + "="*60)
    print("Testing FactSet Provider")
    print("="*60)
    
    username = os.getenv("FACTSET_USERNAME")
    api_key = os.getenv("FACTSET_API_KEY")
    
    if not username or not api_key:
        print("❌ FactSet credentials not set")
        print("   Required environment variables:")
        print("   - FACTSET_USERNAME")
        print("   - FACTSET_API_KEY")
        print("\n   This is expected if you don't have FactSet subscription.")
        return None  # Not an error, just not configured
    
    print(f"✓ Username: {username}")
    print(f"✓ API Key: ***{api_key[-4:]}")
    
    try:
        from quantlib_pro.data.providers import FactsetProvider
        
        provider = FactsetProvider(username=username, api_key=api_key)
        print("✓ Provider initialized")
        
        # Test data fetch
        print("\nFetching historical data for AAPL-US...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        data = provider.fetch("AAPL-US", start=start_date, end=end_date)
        print(f"✅ Retrieved {len(data)} rows")
        print(f"   Date range: {data.index[0]} to {data.index[-1]}")
        print(f"   Latest close: ${data['Close'].iloc[-1]:.2f}")
        
        return True
    
    except Exception as e:
        print(f"❌ FactSet test failed: {e}")
        if "401" in str(e):
            print("   → Authentication failed - check credentials")
        elif "403" in str(e):
            print("   → Access forbidden - verify subscription entitlements")
        return False


def test_multi_provider():
    """Test multi-provider failover."""
    print("\n" + "="*60)
    print("Testing Multi-Provider Failover")
    print("="*60)
    
    try:
        from quantlib_pro.data.providers import MultiProviderDataFetcher
        
        # Check which providers are configured
        av_enabled = bool(os.getenv("ALPHA_VANTAGE_API_KEY"))
        fs_enabled = bool(os.getenv("FACTSET_USERNAME") and os.getenv("FACTSET_API_KEY"))
        
        fetcher = MultiProviderDataFetcher(
            enable_alpha_vantage=av_enabled,
            enable_factset=fs_enabled,
        )
        
        print(f"✓ Multi-provider fetcher initialized")
        
        status = fetcher.get_provider_status()
        print(f"\nConfigured providers: {status['configured_providers']}")
        for provider in status['providers']:
            print(f"  - {provider}")
        
        print("\nFallback chain:")
        for level in status['fallback_chain']:
            print(f"  {level}")
        
        # Test fetch
        print("\nTesting failover with AAPL...")
        result = fetcher.fetch("AAPL", period="5d")
        print(f"✅ Data fetched from: {result.source.value}")
        print(f"   Rows: {len(result.df)}")
        
        return True
    
    except Exception as e:
        print(f"❌ Multi-provider test failed: {e}")
        return False


def test_resilient_fetcher():
    """Test basic resilient fetcher with Yahoo Finance."""
    print("\n" + "="*60)
    print("Testing Basic Resilient Fetcher (Yahoo Finance)")
    print("="*60)
    
    try:
        from quantlib_pro.data.fetcher import ResilientDataFetcher
        
        fetcher = ResilientDataFetcher()
        print("✓ Fetcher initialized")
        
        print("\nFetching AAPL from Yahoo Finance...")
        result = fetcher.fetch("AAPL", period="5d")
        
        print(f"✅ Data source: {result.source.value}")
        print(f"   Rows: {len(result.df)}")
        print(f"   Date range: {result.df.index[0]} to {result.df.index[-1]}")
        print(f"   Latest close: ${result.df['Close'].iloc[-1]:.2f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Basic fetcher test failed: {e}")
        return False


def main():
    """Run all provider tests."""
    print("\n" + "="*70)
    print("  QuantLib Pro - Data Provider Integration Tests")
    print("="*70)
    
    # Load .env if present
    try:
        from dotenv import load_dotenv
        if load_dotenv():
            print("✓ Loaded environment variables from .env file")
        else:
            print("⚠ No .env file found - using system environment variables")
    except ImportError:
        print("⚠ python-dotenv not installed - using system environment variables")
    
    results = {}
    
    # Test basic fetcher (always available)
    results['Basic (Yahoo Finance)'] = test_resilient_fetcher()
    
    # Test Alpha Vantage
    results['Alpha Vantage'] = test_alpha_vantage()
    
    # Test FactSet
    fs_result = test_factset()
    if fs_result is not None:
        results['FactSet'] = fs_result
    
    # Test multi-provider
    results['Multi-Provider'] = test_multi_provider()
    
    # Summary
    print("\n" + "="*70)
    print("  Test Results Summary")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print("\n" + "="*70)
    print(f"  Overall: {passed}/{total} tests passed")
    print("="*70)
    
    if passed < total:
        print("\n⚠️  Some tests failed. Check error messages above.")
        print("   Common issues:")
        print("   - API keys not set in .env file")
        print("   - Rate limits exceeded (wait 60 seconds for Alpha Vantage)")
        print("   - Invalid credentials")
        print("   - Network connectivity issues")
        sys.exit(1)
    else:
        print("\n✅ All configured providers are working!")
        sys.exit(0)


if __name__ == "__main__":
    main()
