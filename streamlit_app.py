"""
QuantLib Pro - Streamlit application entry point.
Uses st.navigation with Material Design icons (Streamlit 1.36+).
"""

import streamlit as st
import os

# Helper functions for option 1 and 3: dynamic per-session + fallback secret/env keys
def get_provider_api_key(provider_name: str):
    session_key = st.session_state.get(f"{provider_name}_API_KEY")
    if session_key:
        return session_key.strip()

    if hasattr(st, "secrets") and st.secrets is not None:
        secret_key = st.secrets.get(f"{provider_name}_API_KEY")
        if secret_key:
            return secret_key.strip()

    return os.getenv(f"{provider_name}_API_KEY", "").strip()


def get_provider_enabled_flag(provider_name: str):
    session_state_val = st.session_state.get(f"{provider_name}_ENABLED")
    if isinstance(session_state_val, bool):
        return session_state_val

    env_val = os.getenv(f"{provider_name}_ENABLED", "false").lower()
    if hasattr(st, "secrets") and st.secrets is not None:
        secret_val = st.secrets.get(f"{provider_name}_ENABLED")
        if isinstance(secret_val, str) and secret_val.strip():
            env_val = secret_val.strip().lower()
    return env_val == "true"


# Global page config - called ONCE here; pages must NOT call it
st.set_page_config(
    page_title="QuantLib Pro",
    page_icon=":material/candlestick_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def set_session_provider_keys():
    with st.sidebar.expander("Temporary API Keys (current session)", expanded=False):
        tmp_av_key = st.text_input("Alpha Vantage API Key (session)", type="password", key="tmp_av_key")
        tmp_fred_key = st.text_input("FRED API Key (session)", type="password", key="tmp_fred_key")
        tmp_factset_username = st.text_input("FactSet Username (session)", key="tmp_factset_username")
        tmp_factset_api = st.text_input("FactSet API Key (session)", type="password", key="tmp_factset_api")

        if st.button("Apply temporary keys", key="apply_temp_keys"):
            if tmp_av_key:
                st.session_state["ALPHA_VANTAGE_API_KEY"] = tmp_av_key.strip()
            if tmp_fred_key:
                st.session_state["FRED_API_KEY"] = tmp_fred_key.strip()
            if tmp_factset_username:
                st.session_state["FACTSET_USERNAME"] = tmp_factset_username.strip()
            if tmp_factset_api:
                st.session_state["FACTSET_API_KEY"] = tmp_factset_api.strip()

            st.success("Temporary session credentials have been applied. Re-run the desired action.")
            st.experimental_rerun()


# Check API credentials and show setup dialog if needed
def check_and_prompt_credentials():
    """Check for API credentials and prompt user if they're missing."""
    fred_key = get_provider_api_key("FRED")
    fred_configured = fred_key and fred_key != "REPLACE_WITH_FRED_API_KEY" and len(fred_key) > 10
    fred_enabled = get_provider_enabled_flag("FRED")
    
    av_key = get_provider_api_key("ALPHA_VANTAGE")
    av_configured = av_key and av_key != "REPLACE_WITH_ALPHA_VANTAGE_KEY" and len(av_key) > 10
    av_enabled = get_provider_enabled_flag("ALPHA_VANTAGE")
    
    # If credentials are missing, show setup instructions
    if not fred_configured or not av_configured:
        st.warning(" **API Credentials Setup Required**")
        
        with st.expander("**Click here to set up your API credentials for full functionality**", expanded=True):
            st.markdown("""
            ###  Get the Most Out of QuantLib Pro!
            
            To access all features including real-time market data, economic indicators, and enhanced analytics, 
            please configure your free API credentials:
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not fred_configured:
                    st.error(" **FRED API Key Missing**")
                    st.markdown("""
                    **Federal Reserve Economic Data (FRED)**
                    - Free API for US economic data
                    - Get your key: [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
                    - Required for: Economic indicators, yield curves, inflation data
                    """)
                else:
                    st.success(" **FRED API Key Configured**")
            
            with col2:
                if not av_configured:
                    st.error(" **Alpha Vantage API Key Missing**")
                    st.markdown("""
                    **Alpha Vantage Market Data**
                    - Free API for stock market data
                    - Get your key: [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
                    - Required for: Real-time quotes, technical indicators, forex data
                    """)
                else:
                    st.success(" **Alpha Vantage API Key Configured**")
            
            st.info("""
            ** How to Configure:**
            1. Get your free API keys from the links above
            2. Go to **Settings** (in the Developer section of the sidebar)
            3. Enter your API keys in the configuration panel
            4. Restart the application to apply changes
            
            ** Note:** You can still use QuantLib Pro without these keys, but some features will be limited to Yahoo Finance data only.
            """)
            
            if st.button(" Go to Settings", type="primary"):
                st.switch_page("pages/18_Settings.py")
        
        st.divider()

# Apply session provider key overrides (Option 1)
set_session_provider_keys()

# Show credentials prompt on app startup
check_and_prompt_credentials()

# Persistent sidebar shown on every page
with st.sidebar:
    st.markdown("## QuantLib Pro")
    st.caption("Enterprise Quantitative Finance Platform")
    
    st.divider()

    st.markdown("### Analysis Parameters")
    
    st.markdown("##### Date Range")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Start", value=None)
    with c2:
        end_date = st.date_input("End", value=None)

    st.markdown("##### Risk Parameters")
    risk_free_rate = st.slider(
        "Risk-free Rate (%)", 0.0, 10.0, 2.0, 0.1
    ) / 100
    confidence_level = st.slider(
        "VaR Confidence (%)", 90, 99, 95
    ) / 100

    st.session_state.risk_free_rate   = risk_free_rate
    st.session_state.confidence_level = confidence_level
    if start_date:
        st.session_state.start_date = start_date
    if end_date:
        st.session_state.end_date   = end_date

    st.divider()

    st.markdown("### System Status")
    
    # Import requests at module level to avoid issues
    try:
        import requests
    except ImportError:
        requests = None
    
    # Check API status (only if not in cloud environment)
    is_cloud_deployment = os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("STREAMLIT_CLOUD") or "streamlit.app" in os.getenv("HOSTNAME", "")
    
    if not is_cloud_deployment and requests:
        try:
            r = requests.get("http://localhost:8000/health/", timeout=1)
            st.success("API: Online") if r.status_code == 200 else st.warning("API: Degraded")
        except Exception:
            st.info("API: Standalone Mode")
    else:
        st.info("API: Cloud Mode")
    
    # Check data providers (with session/secret/env fallback)
    fred_key = get_provider_api_key("FRED")
    fred_ok = bool(fred_key and fred_key != "REPLACE_WITH_FRED_API_KEY" and len(fred_key) > 10)
    av_key = get_provider_api_key("ALPHA_VANTAGE")
    av_ok = bool(av_key and av_key != "REPLACE_WITH_ALPHA_VANTAGE_KEY" and len(av_key) > 10)
    
    st.success("UI: Online")
    st.success("Yahoo Finance: Ready")
    if fred_ok:
        st.success("FRED: Connected")
    else:
        st.warning("FRED: Configure in Settings or session override")
    if av_ok:
        st.success("Alpha Vantage: Connected")
    else:
        st.warning("Alpha Vantage: Configure in Settings or session override")

    st.divider()
    st.caption("v1.0.0 · Streamlit · FastAPI")

# Navigation with grouped sections and Material Design icons
pg = st.navigation(
    {
        "Core": [
            st.Page("pages/0_Home.py",               title="Home",              icon=":material/home:"),
            st.Page("pages/1_Portfolio.py",          title="Portfolio",         icon=":material/pie_chart:"),
            st.Page("pages/2_Risk.py",               title="Risk",              icon=":material/shield:"),
            st.Page("pages/3_Options.py",            title="Options",           icon=":material/calculate:"),
        ],
        "Market": [
            st.Page("pages/4_Market_Regime.py",      title="Market Regime",     icon=":material/track_changes:"),
            st.Page("pages/5_Macro.py",              title="Macro",             icon=":material/public:"),
            st.Page("pages/6_Volatility_Surface.py", title="Vol Surface",       icon=":material/show_chart:"),
            st.Page("pages/10_Market_Analysis.py",   title="Market Analysis",   icon=":material/bar_chart:"),
        ],
        "Trading": [
            st.Page("pages/7_Backtesting.py",        title="Backtesting",       icon=":material/history:"),
            st.Page("pages/11_Trading_Signals.py",   title="Trading Signals",   icon=":material/sensors:"),
            st.Page("pages/8_Advanced_Analytics.py", title="Analytics",         icon=":material/analytics:"),
        ],
        "Infrastructure": [
            st.Page("pages/12_Liquidity.py",         title="Liquidity",         icon=":material/water_drop:"),
            st.Page("pages/13_Systemic_Risk.py",     title="Systemic Risk",     icon=":material/hub:"),
            st.Page("pages/9_Data_Management.py",    title="Data Management",   icon=":material/storage:"),
        ],
        "Monitoring": [
            st.Page("pages/14_Trader_Stress_Monitor.py", title="Stress Monitor", icon=":material/psychology:"),
            st.Page("pages/16_UAT_Dashboard.py",     title="UAT Dashboard",     icon=":material/dashboard:"),
            st.Page("pages/15_Testing.py",           title="Testing",           icon=":material/science:"),
        ],
        "Developer": [
            st.Page("pages/17_API_Explorer.py",      title="API Explorer",      icon=":material/api:"),
            st.Page("pages/18_Settings.py",          title="Settings",          icon=":material/settings:"),
        ],
    }
)

pg.run()
