"""
QuantLib Pro - Streamlit application entry point.
Uses st.navigation with Material Design icons (Streamlit 1.36+).
"""

import streamlit as st

# Global page config - called ONCE here; pages must NOT call it
st.set_page_config(
    page_title="QuantLib Pro",
    page_icon=":material/candlestick_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Persistent sidebar shown on every page
with st.sidebar:
    st.markdown("## Settings")

    st.markdown("### Data Source")
    data_source = st.selectbox(
        "Choose data provider",
        ["Yahoo Finance", "Alpha Vantage"],
        index=0,
    )

    st.markdown("### Date Range")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Start", value=None)
    with c2:
        end_date = st.date_input("End", value=None)

    st.markdown("### Risk Parameters")
    risk_free_rate = st.slider(
        "Risk-free Rate (%)", 0.0, 10.0, 2.0, 0.1
    ) / 100
    confidence_level = st.slider(
        "VaR Confidence (%)", 90, 99, 95
    ) / 100

    st.session_state.data_source      = data_source
    st.session_state.risk_free_rate   = risk_free_rate
    st.session_state.confidence_level = confidence_level
    if start_date:
        st.session_state.start_date = start_date
    if end_date:
        st.session_state.end_date   = end_date

    st.divider()

    st.markdown("### System Status")
    import requests
    try:
        r = requests.get("http://localhost:8000/health/", timeout=2)
        st.success("API: Online") if r.status_code == 200 else st.warning("API: Degraded")
    except Exception:
        st.error("API: Offline")
    st.success("UI: Online")

    st.divider()
    st.caption("QuantLib Pro v1.0.0 · Streamlit · FastAPI")

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
    }
)

pg.run()
