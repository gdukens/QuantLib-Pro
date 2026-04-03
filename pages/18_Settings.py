"""
Settings & Configuration - API Keys and System Preferences
"""

import streamlit as st
import os
import requests
from pathlib import Path
from dotenv import load_dotenv, set_key, find_dotenv
import re

# Load environment variables
load_dotenv()

# Helper function: get session or env/secret value for provider keys

def get_provider_api_key(provider_name: str) -> str:
    session_val = st.session_state.get(f"{provider_name}_API_KEY")
    if session_val:
        return session_val.strip()

    if hasattr(st, "secrets") and st.secrets is not None:
        secret_val = st.secrets.get(f"{provider_name}_API_KEY")
        if secret_val:
            return str(secret_val).strip()

    return os.getenv(f"{provider_name}_API_KEY", "").strip()


def get_provider_enabled_flag(provider_name: str) -> bool:
    session_val = st.session_state.get(f"{provider_name}_ENABLED")
    if isinstance(session_val, bool):
        return session_val

    if hasattr(st, "secrets") and st.secrets is not None:
        secret_val = st.secrets.get(f"{provider_name}_ENABLED")
        if isinstance(secret_val, str):
            return secret_val.strip().lower() == "true"

    return os.getenv(f"{provider_name}_ENABLED", "false").lower() == "true"


st.title("Settings & Configuration")
st.markdown("Configure API keys, data providers, and system preferences")

# Tabs for different settings sections
tab1, tab2, tab3 = st.tabs(["API Keys", "Data Providers", "System Info"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: API KEYS CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

with tab1:
    st.header("API Key Configuration")
    st.markdown("Secure configuration for third-party data providers")

    # Temporary session overrides (Option 1)
    st.expander("Temporary session API keys", expanded=False)
    tmp_col1, tmp_col2 = st.columns(2)
    with tmp_col1:
        temp_av_key = st.text_input(
            "Temp Alpha Vantage key",
            value=st.session_state.get("ALPHA_VANTAGE_API_KEY", ""),
            type="password",
            help="Use this key for current session only",
            key="temp_av_key",
        )
        temp_fred_key = st.text_input(
            "Temp FRED key",
            value=st.session_state.get("FRED_API_KEY", ""),
            type="password",
            help="Use this key for current session only",
            key="temp_fred_key",
        )

    with tmp_col2:
        temp_factset_user = st.text_input(
            "Temp FactSet username",
            value=st.session_state.get("FACTSET_USERNAME", ""),
            help="Use this username for current session only",
            key="temp_factset_user",
        )
        temp_factset_key = st.text_input(
            "Temp FactSet key",
            value=st.session_state.get("FACTSET_API_KEY", ""),
            type="password",
            help="Use this key for current session only",
            key="temp_factset_key",
        )

    if st.button("Apply temporary session keys", key="apply_temporary_keys"):
        if temp_av_key:
            st.session_state["ALPHA_VANTAGE_API_KEY"] = temp_av_key.strip()
        if temp_fred_key:
            st.session_state["FRED_API_KEY"] = temp_fred_key.strip()
        if temp_factset_user:
            st.session_state["FACTSET_USERNAME"] = temp_factset_user.strip()
        if temp_factset_key:
            st.session_state["FACTSET_API_KEY"] = temp_factset_key.strip()

        st.success("Temporary session credentials applied.")
        st.experimental_rerun()

    # Find .env file
    env_path = find_dotenv()
    if not env_path:
        env_path = os.path.join(os.getcwd(), ".env")
        st.warning(f"No .env file found. Will create at: `{env_path}`")
    
    st.divider()
    
    # ═════════════════════════════════════════════════════════════════════════
    # ALPHA VANTAGE CONFIGURATION
    # ═════════════════════════════════════════════════════════════════════════
    
    st.subheader("Alpha Vantage")
    st.markdown("**Premium financial data API** - Real-time quotes, historical data, technical indicators")
    
    # Current status
    current_av_key = get_provider_api_key("ALPHA_VANTAGE")
    av_enabled = get_provider_enabled_flag("ALPHA_VANTAGE")
    
    # Check if key is configured and valid format
    av_configured = current_av_key and current_av_key != "REPLACE_WITH_ALPHA_VANTAGE_KEY" and len(current_av_key) > 10
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if av_configured:
            st.success(f"**Status:** Configured (`***{current_av_key[-4:]}`)")
        else:
            st.error("**Status:** Not configured")
    
    with col2:
        if av_configured:
            st.metric("Enabled", "Yes" if av_enabled else "No")
    
    # Rate limit info
    st.info("""
    **Free Tier Limits:**
    - 5 API calls per minute
    - 500 API calls per day
    - No credit card required
    
    **Premium Options:** $49.99/mo (75 calls/min) | $149.99/mo (300 calls/min)
    """)
    
    # Configuration section
    with st.expander("Configure Alpha Vantage API Key", expanded=not av_configured):
        st.markdown("### Step 1: Get Your Free API Key")
        st.markdown("""
        1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
        2. Enter your email address
        3. Copy the API key (arrives instantly, no verification needed)
        4. Paste it below
        """)
        
        # API key input
        new_av_key = st.text_input(
            "Alpha Vantage API Key",
            value=current_av_key if av_configured else "",
            type="password",
            placeholder="e.g., MK01VGPAXTBXDL3V",
            help="Your personal Alpha Vantage API key",
            key="av_key_input"
        )
        
        # Enable/disable toggle
        new_av_enabled = st.checkbox(
            "Enable Alpha Vantage provider",
            value=av_enabled,
            help="When enabled, Alpha Vantage will be used for real-time data",
            key="av_enabled_input"
        )
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if st.button("Save Configuration", type="primary", use_container_width=True):
                if new_av_key and len(new_av_key) > 10:
                    try:
                        # Create .env file if it doesn't exist
                        if not os.path.exists(env_path):
                            Path(env_path).touch()
                        
                        # Update .env file
                        set_key(env_path, "ALPHA_VANTAGE_API_KEY", new_av_key)
                        set_key(env_path, "ALPHA_VANTAGE_ENABLED", str(new_av_enabled).lower())
                        
                        # Reload environment
                        load_dotenv(override=True)
                        
                        st.success("Configuration saved! Restart the app to apply changes.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
                else:
                    st.error("Please enter a valid API key")
        
        with col2:
            if st.button("Test Connection", use_container_width=True):
                if new_av_key and len(new_av_key) > 10:
                    with st.spinner("Testing connection..."):
                        try:
                            # Test API key with a simple quote request
                            test_url = "https://www.alphavantage.co/query"
                            test_params = {
                                "function": "GLOBAL_QUOTE",
                                "symbol": "AAPL",
                                "apikey": new_av_key
                            }
                            response = requests.get(test_url, params=test_params, timeout=10)
                            data = response.json()
                            
                            if "Global Quote" in data:
                                st.success("Connection successful! API key is valid.")
                                st.json(data["Global Quote"])
                            elif "Note" in data:
                                st.warning("API key works but rate limit reached (5 calls/min)")
                            elif "Error Message" in data:
                                st.error(f"API Error: {data['Error Message']}")
                            else:
                                st.error(f"Invalid API key or unknown error")
                                st.json(data)
                        except requests.exceptions.Timeout:
                            st.error("Connection timeout - check your internet connection")
                        except Exception as e:
                            st.error(f"Test failed: {e}")
                else:
                    st.error("Please enter an API key first")
        
        with col3:
            if st.button("Clear Configuration", use_container_width=True):
                try:
                    set_key(env_path, "ALPHA_VANTAGE_API_KEY", "REPLACE_WITH_ALPHA_VANTAGE_KEY")
                    set_key(env_path, "ALPHA_VANTAGE_ENABLED", "false")
                    load_dotenv(override=True)
                    st.success("Configuration cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear: {e}")
    
    st.divider()
    
    # ═════════════════════════════════════════════════════════════════════════
    # FACTSET CONFIGURATION
    # ═════════════════════════════════════════════════════════════════════════
    
    st.subheader("FactSet")
    st.markdown("**Enterprise financial data** - Premium institutional-grade market data")
    
    # Current status
    current_factset_username = os.getenv("FACTSET_USERNAME", "")
    current_factset_key = os.getenv("FACTSET_API_KEY", "")
    factset_enabled = os.getenv("FACTSET_ENABLED", "false").lower() == "true"
    
    factset_configured = (
        current_factset_username and 
        current_factset_key and 
        current_factset_key != "REPLACE_WITH_FACTSET_SERIAL_KEY" and
        len(current_factset_key) > 20
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if factset_configured:
            st.success(f"**Status:** Configured (`{current_factset_username}`)")
        else:
            st.error("**Status:** Not configured")
    
    with col2:
        if factset_configured:
            st.metric("Enabled", "Yes" if factset_enabled else "No")
    
    st.warning("**Enterprise License Required** - Contact [FactSet Sales](https://www.factset.com/contact-us) for access")
    
    with st.expander("Configure FactSet API Credentials", expanded=False):
        st.markdown("""
        ### Requirements
        1. Active FactSet subscription
        2. API credentials from [FactSet Developer Portal](https://developer.factset.com/)
        3. IP whitelist configuration
        """)
        
        # Username input
        new_factset_username = st.text_input(
            "FactSet Username",
            value=current_factset_username,
            placeholder="YOURCOMPANY-serial",
            help="Your FactSet username or serial number",
            key="factset_username_input"
        )
        
        # API key input
        new_factset_key = st.text_input(
            "FactSet API Key (Serial)",
            value=current_factset_key if factset_configured else "",
            type="password",
            placeholder="Your FactSet serial key",
            help="Long alphanumeric string from FactSet Developer Portal",
            key="factset_key_input"
        )
        
        # Enable toggle
        new_factset_enabled = st.checkbox(
            "Enable FactSet provider",
            value=factset_enabled,
            help="When enabled, FactSet will be used for premium data",
            key="factset_enabled_input"
        )
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save FactSet Config", type="primary", use_container_width=True):
                if new_factset_username and new_factset_key and len(new_factset_key) > 20:
                    try:
                        if not os.path.exists(env_path):
                            Path(env_path).touch()
                        
                        set_key(env_path, "FACTSET_USERNAME", new_factset_username)
                        set_key(env_path, "FACTSET_API_KEY", new_factset_key)
                        set_key(env_path, "FACTSET_ENABLED", str(new_factset_enabled).lower())
                        
                        load_dotenv(override=True)
                        st.success("FactSet configuration saved!")
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
                else:
                    st.error("Please enter valid credentials")
        
        with col2:
            if st.button("Clear FactSet Config", use_container_width=True):
                try:
                    set_key(env_path, "FACTSET_USERNAME", "REPLACE_WITH_FACTSET_USERNAME")
                    set_key(env_path, "FACTSET_API_KEY", "REPLACE_WITH_FACTSET_SERIAL_KEY")
                    set_key(env_path, "FACTSET_ENABLED", "false")
                    load_dotenv(override=True)
                    st.success("FactSet configuration cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear: {e}")
    
    st.divider()
    
    # ═════════════════════════════════════════════════════════════════════════
    # FRED CONFIGURATION
    # ═════════════════════════════════════════════════════════════════════════
    
    st.subheader("FRED - Federal Reserve Economic Data")
    st.markdown("**Macroeconomic data from the Federal Reserve** - Free access to 800,000+ economic time series")
    
    # Current status
    current_fred_key = get_provider_api_key("FRED")
    fred_enabled = get_provider_enabled_flag("FRED")
    
    # Check if key is configured and valid format
    fred_configured = current_fred_key and current_fred_key != "REPLACE_WITH_FRED_API_KEY" and len(current_fred_key) > 10
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if fred_configured:
            st.success(f"**Status:** Configured (`***{current_fred_key[-4:]}`)")
        else:
            st.error("**Status:** Not configured")
    
    with col2:
        if fred_configured:
            st.metric("Enabled", "Yes" if fred_enabled else "No")
    
    # Info about FRED
    st.info("""
    **FRED API Benefits:**
    -  **Completely FREE** - No rate limits for reasonable use
    -  Access to 800,000+ economic data series
    -  Official data from the Federal Reserve
    -  US and international economic indicators
    -  GDP, inflation, unemployment, interest rates, and more
    
    **Use Cases:**
    - Macro analysis and regime detection
    - Economic indicator tracking
    - Correlation with market regimes
    - Fundamental analysis inputs
    """)
    
    # Configuration section
    with st.expander("Configure FRED API Key", expanded=not fred_configured):
        st.markdown("### Step 1: Get Your Free FRED API Key")
        st.markdown("""
        1. Visit [FRED API Key Request](https://fred.stlouisfed.org/docs/api/api_key.html)
        2. Click "Request API Key"
        3. Sign in or create a free account
        4. Fill out the simple form (just name and email)
        5. Receive your API key instantly via email
        6. Paste it below
        """)
        
        # API key input
        new_fred_key = st.text_input(
            "FRED API Key",
            value=current_fred_key if fred_configured else "",
            type="password",
            placeholder="e.g., 5f5dcf2ef53c496228fa2935b71d9d40",
            help="Your personal FRED API key from St. Louis Fed",
            key="fred_key_input"
        )
        
        # Enable/disable toggle
        new_fred_enabled = st.checkbox(
            "Enable FRED provider",
            value=fred_enabled,
            help="When enabled, FRED will be used for macroeconomic data",
            key="fred_enabled_input"
        )
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if st.button("Save FRED Config", type="primary", use_container_width=True, key="save_fred"):
                if new_fred_key and len(new_fred_key) > 10:
                    try:
                        # Create .env file if it doesn't exist
                        if not os.path.exists(env_path):
                            Path(env_path).touch()
                        
                        # Update .env file
                        set_key(env_path, "FRED_API_KEY", new_fred_key)
                        set_key(env_path, "FRED_ENABLED", str(new_fred_enabled).lower())
                        
                        # Reload environment
                        load_dotenv(override=True)
                        
                        st.success("FRED configuration saved! Restart the app to apply changes.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
                else:
                    st.error("Please enter a valid API key")
        
        with col2:
            if st.button("Test FRED Connection", use_container_width=True, key="test_fred"):
                if new_fred_key and len(new_fred_key) > 10:
                    with st.spinner("Testing FRED connection..."):
                        try:
                            # Test API key with GDP series request
                            test_url = "https://api.stlouisfed.org/fred/series/observations"
                            test_params = {
                                "series_id": "GDP",
                                "api_key": new_fred_key,
                                "file_type": "json",
                                "limit": 5
                            }
                            response = requests.get(test_url, params=test_params, timeout=10)
                            data = response.json()
                            
                            if "observations" in data:
                                st.success(" Connection successful! FRED API key is valid.")
                                latest = data["observations"][-1]
                                st.info(f"**Latest GDP data:** {latest['date']} = ${latest['value']} billion")
                            elif "error_message" in data:
                                st.error(f"API Error: {data['error_message']}")
                            else:
                                st.error(f"Invalid API key or unknown error")
                                st.json(data)
                        except requests.exceptions.Timeout:
                            st.error("Connection timeout - check your internet connection")
                        except Exception as e:
                            st.error(f"Test failed: {e}")
                else:
                    st.error("Please enter an API key first")
        
        with col3:
            if st.button("Clear FRED Config", use_container_width=True, key="clear_fred"):
                try:
                    set_key(env_path, "FRED_API_KEY", "REPLACE_WITH_FRED_API_KEY")
                    set_key(env_path, "FRED_ENABLED", "false")
                    load_dotenv(override=True)
                    st.success("FRED configuration cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: DATA PROVIDERS PRIORITY
# ─────────────────────────────────────────────────────────────────────────────

with tab2:
    st.header("Data Provider Priority")
    st.markdown("Configure fallback hierarchy for data retrieval")
    
    st.info("""
    **Automatic Fallback Chain:**
    
    The system automatically tries providers in this order:
    
    **For Market Data (Stocks, ETFs):**
    1.  **Alpha Vantage** (if configured & enabled)
       - Premium data quality
       - Rate limited (5 calls/min free tier)
    
    2.  **Yahoo Finance** (always available)
       - Free and unlimited
       - Good data quality
       - No API key required
    
    3.  **FactSet** (if configured & enabled)
       - Enterprise-grade data
       - Requires paid subscription
    
    4.  **Simulated Data** (final fallback)
       - Synthetic data for testing
       - Always available
    
    **For Macroeconomic Data:**
    1.  **FRED - Federal Reserve** (if configured & enabled)
       - Official US economic data
       - 800,000+ time series
       - Free and unlimited
    
    2.  **Simulated Data** (final fallback)
       - Synthetic macro data for testing
    """)
    
    st.divider()
    
    st.subheader("Current Configuration")
    
    # Provider status table
    providers_status = []
    
    # Alpha Vantage
    av_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    av_status = "Ready" if (av_key and av_key != "REPLACE_WITH_ALPHA_VANTAGE_KEY") else "Not Configured"
    providers_status.append({
        "Provider": "Alpha Vantage",
        "Type": "Market Data",
        "Status": av_status,
        "Enabled": "Yes" if os.getenv("ALPHA_VANTAGE_ENABLED", "false").lower() == "true" else "No",
        "Priority": "1"
    })
    
    # Yahoo Finance
    providers_status.append({
        "Provider": "Yahoo Finance",
        "Type": "Market Data",
        "Status": "Ready",
        "Enabled": "Yes (Always)",
        "Priority": "2"
    })
    
    # FactSet
    fs_username = get_provider_api_key("FACTSET_USERNAME") if hasattr(st, 'session_state') else os.getenv("FACTSET_USERNAME", "")
    fs_key = get_provider_api_key("FACTSET")
    fs_status = "Ready" if (fs_username and fs_key and fs_key != "REPLACE_WITH_FACTSET_SERIAL_KEY") else "Not Configured"
    providers_status.append({
        "Provider": "FactSet",
        "Type": "Market Data",
        "Status": fs_status,
        "Enabled": "Yes" if os.getenv("FACTSET_ENABLED", "false").lower() == "true" else "No",
        "Priority": "3"
    })
    
    # FRED
    fred_key = os.getenv("FRED_API_KEY", "")
    fred_status = "Ready" if (fred_key and fred_key != "REPLACE_WITH_FRED_API_KEY") else "Not Configured"
    providers_status.append({
        "Provider": "FRED (Federal Reserve)",
        "Type": "Macro Data",
        "Status": fred_status,
        "Enabled": "Yes" if os.getenv("FRED_ENABLED", "false").lower() == "true" else "No",
        "Priority": "1 (Macro)"
    })
    
    # Simulated
    providers_status.append({
        "Provider": "Simulated Data",
        "Type": "All Types",
        "Status": "Ready",
        "Enabled": "Yes (Fallback)",
        "Priority": "4"
    })
    
    st.table(providers_status)
    
    st.divider()
    
    st.subheader("Usage Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Development/Testing:**
        - Yahoo Finance (free, unlimited)
        - Simulated data (instant)
        - Alpha Vantage (save quotas)
        """)
    
    with col2:
        st.markdown("""
        **Production:**
        - Alpha Vantage (reliable)
        - Yahoo Finance (fallback)
        - FactSet (enterprise)
        """)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: SYSTEM INFORMATION
# ─────────────────────────────────────────────────────────────────────────────

with tab3:
    st.header("System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Environment")
        st.code(f"""
Python: {os.sys.version.split()[0]}
OS: {os.name}
Working Directory: {os.getcwd()}
Env File: {env_path or 'Not found'}
        """.strip())
    
    with col2:
        st.subheader("API Status")
        
        # Check API server
        try:
            response = requests.get("http://localhost:8001/health", timeout=2)
            if response.status_code == 200:
                st.success("FastAPI Server: Online (port 8001)")
                data = response.json()
                st.caption(f"Service: {data.get('service', 'unknown')}")
            else:
                st.warning(f"FastAPI Server: Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("FastAPI Server: Offline")
        except Exception as e:
            st.error(f"FastAPI Server: Error ({e})")
        
        # Check Streamlit
        st.success("Streamlit UI: Online")
    
    st.divider()
    
    st.subheader("Environment Variables")
    
    # Display relevant environment variables (masked)
    env_vars = {
        "ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY", "Not set"),
        "ALPHA_VANTAGE_ENABLED": os.getenv("ALPHA_VANTAGE_ENABLED", "false"),
        "FACTSET_USERNAME": os.getenv("FACTSET_USERNAME", "Not set"),
        "FACTSET_API_KEY": os.getenv("FACTSET_API_KEY", "Not set"),
        "FACTSET_ENABLED": os.getenv("FACTSET_ENABLED", "false"),
    }
    
    # Mask sensitive values
    masked_vars = {}
    for key, value in env_vars.items():
        if "API_KEY" in key or "SERIAL" in key:
            if value and value not in ["Not set", "REPLACE_WITH_ALPHA_VANTAGE_KEY", "REPLACE_WITH_FACTSET_SERIAL_KEY"]:
                masked_vars[key] = f"***{value[-4:]}" if len(value) > 4 else "***"
            else:
                masked_vars[key] = value
        else:
            masked_vars[key] = value
    
    st.json(masked_vars)
    
    st.divider()
    
    st.subheader("Help & Documentation")
    
    st.markdown("""
    **Quick Links:**
    - [Alpha Vantage Docs](https://www.alphavantage.co/documentation/)
    - [FactSet Developer Portal](https://developer.factset.com/)
    - [Yahoo Finance Docs](https://github.com/ranaroussi/yfinance)
    
    **Need Help?**
    - Check [PROVIDERS_STATUS.md](../PROVIDERS_STATUS.md) for setup guides
    - Review [DATA_PROVIDERS_GUIDE.md](../docs/DATA_PROVIDERS_GUIDE.md) for detailed instructions
    - Test your configuration in the API Explorer page
    """)

# Footer
st.divider()
st.caption("**Tip:** API keys are stored in `.env` file and never displayed in logs or UI. Restart the application after changing configuration.")
