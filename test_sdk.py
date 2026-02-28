#!/usr/bin/env python3
"""
Quick SDK Test

This script performs a basic test of the QuantLib Pro SDK to verify
that all components are working correctly.
"""

import sys
import traceback
from datetime import datetime

def test_sdk_imports():
    """Test that SDK can be imported successfully."""
    print("🧪 Testing SDK imports...")
    
    try:
        from quantlib_pro import QuantLibSDK, SDKConfig, create_sdk
        print("✅ Main SDK imports successful")
        
        # Test individual modules
        from quantlib_pro.portfolio import PortfolioManager
        from quantlib_pro.risk import RiskManager
        from quantlib_pro.options import OptionsManager
        from quantlib_pro.data import DataManager
        print("✅ Manager imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_sdk_initialization():
    """Test SDK initialization."""
    print("\n🧪 Testing SDK initialization...")
    
    try:
        from quantlib_pro import QuantLibSDK, SDKConfig
        
        # Test with default config
        sdk = QuantLibSDK()
        print("✅ Default configuration successful")
        
        # Test with custom config
        config = SDKConfig(
            enable_caching=False,
            log_level="ERROR",
            default_confidence_level=0.01
        )
        sdk_custom = QuantLibSDK(config)
        print("✅ Custom configuration successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_health_check():
    """Test SDK health check."""
    print("\n🧪 Testing health check...")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        health = sdk.health_check()
        
        print(f"✅ Health check completed: {health.get('sdk_version', 'Unknown version')}")
        
        # Check components
        components = health.get("components", {})
        for component, status in components.items():
            status_icon = "✅" if status.get("status") == "healthy" else "⚠️"
            print(f"   {status_icon} {component}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_basic_functionality():
    """Test basic SDK functionality."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        
        # Test portfolio creation
        portfolio = sdk.portfolio.create_portfolio(['AAPL', 'MSFT'])
        print(f"✅ Portfolio creation: {portfolio['portfolio_id']}")
        
        # Test data retrieval (mock data)
        data = sdk.data.get_price_data(['AAPL'], period='1m')
        print(f"✅ Data retrieval: {data.shape}")
        
        # Test options pricing
        call_price = sdk.options.black_scholes(100, 105, 0.25, 0.05, 0.2)
        print(f"✅ Options pricing: ${call_price:.4f}")
        
        # Test risk calculation
        returns = sdk.portfolio.calculate_returns(data)
        var = sdk.risk.calculate_var(returns)
        print(f"✅ Risk calculation: VaR = {var:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        traceback.print_exc()
        return False

def test_module_managers():
    """Test individual module managers."""
    print("\n🧪 Testing module managers...")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        
        # Test each manager's health check
        managers = [
            ('portfolio', sdk.portfolio),
            ('risk', sdk.risk),
            ('options', sdk.options),
            ('data', sdk.data),
            ('volatility', sdk.volatility),
            ('macro', sdk.macro),
            ('market_regime', sdk.market_regime),
            ('analytics', sdk.analytics),
            ('execution', sdk.execution)
        ]
        
        for name, manager in managers:
            health = manager.health_check()
            status = health.get('status', 'unknown')
            status_icon = "✅" if status == "healthy" else "⚠️"
            print(f"   {status_icon} {name}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Manager testing failed: {e}")
        return False

def test_error_handling():
    """Test error handling."""
    print("\n🧪 Testing error handling...")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        
        # Test invalid inputs
        try:
            # Should handle empty data gracefully
            empty_data = sdk.data.get_price_data([])
            print("⚠️  Empty symbols handled")
        except:
            print("✅ Empty symbols rejected properly")
        
        try:
            # Should handle invalid option parameters
            invalid_price = sdk.options.black_scholes(-100, 105, -0.25, 0.05, 0.2)
            print("⚠️  Invalid option parameters handled")
        except:
            print("✅ Invalid option parameters rejected properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("QuantLib Pro SDK Test Suite")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        test_sdk_imports,
        test_sdk_initialization,
        test_health_check,
        test_basic_functionality,
        test_module_managers,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! SDK is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())