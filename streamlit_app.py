"""
QuantLib Pro - Streamlit Dashboard

Week 12: UI Layer - Main application entry point for Streamlit multi-page app.
"""

import streamlit as st

# Configure page
st.set_page_config(
    page_title="QuantLib Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main content
st.markdown('<div class="main-header">📊 QuantLib Pro</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Quantitative Finance Platform - Portfolio Optimization, '
    'Risk Analysis & Derivatives Pricing</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# Welcome section
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 Portfolio Analysis")
    st.markdown(
        """
        - Mean-variance optimization
        - Efficient frontier visualization
        - Risk parity allocation
        - Performance analytics
        """
    )
    if st.button("Open Portfolio Dashboard", key="portfolio"):
        st.switch_page("pages/1_📈_Portfolio.py")

with col2:
    st.markdown("### ⚠️ Risk Management")
    st.markdown(
        """
        - Value-at-Risk (VaR) calculation
        - Stress testing & scenarios
        - Tail risk analysis
        - Real-time monitoring
        """
    )
    if st.button("Open Risk Dashboard", key="risk"):
        st.switch_page("pages/2_⚠️_Risk.py")

with col3:
    st.markdown("### 📊 Options Pricing")
    st.markdown(
        """
        - Black-Scholes pricing
        - Monte Carlo simulation
        - Greeks analysis
        - Volatility surface
        """
    )
    if st.button("Open Options Dashboard", key="options"):
        st.switch_page("pages/3_📊_Options.py")

st.markdown("---")

# Additional features
st.markdown("### 🔧 Additional Features")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container():
        st.markdown("#### 🎯 Market Regime")
        st.markdown("Detect market states using HMM")
        if st.button("View", key="regime"):
            st.switch_page("pages/4_🎯_Market_Regime.py")

with col2:
    with st.container():
        st.markdown("#### 📉 Macro Analysis")
        st.markdown("Economic indicators & sentiment")
        if st.button("View", key="macro"):
            st.switch_page("pages/5_📉_Macro.py")

with col3:
    with st.container():
        st.markdown("#### 🌊 Vol Surface")
        st.markdown("Implied volatility analysis")
        if st.button("View", key="vol_surface"):
            st.switch_page("pages/6_🌊_Volatility_Surface.py")

with col4:
    with st.container():
        st.markdown("#### � Backtesting")
        st.markdown("Test trading strategies")
        if st.button("View", key="backtest"):
            st.switch_page("pages/7_📊_Backtesting.py")

# Second row of additional features
col5, col6, col7, col8 = st.columns(4)

with col5:
    with st.container():
        st.markdown("#### �📖 Documentation")
        st.markdown("API docs & user guide")
        if st.button("View Docs", key="docs"):
            st.markdown("[API Documentation](/docs)")
with col6:
    with st.container():
        st.markdown("#### 📊 Analytics")
        st.markdown("Performance & correlation")
        if st.button("View", key="analytics"):
            st.switch_page("pages/8_📊_Advanced_Analytics.py")
# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    st.markdown("### Data Source")
    data_source = st.selectbox(
        "Choose data provider",
        ["Yahoo Finance", "Alpha Vantage"],
        index=0,
    )
    
    st.markdown("### Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=None)
    with col2:
        end_date = st.date_input("End Date", value=None)
    
    st.markdown("### Risk Preferences")
    risk_free_rate = st.slider(
        "Risk-free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.1,
    ) / 100
    
    confidence_level = st.slider(
        "VaR Confidence Level (%)",
        min_value=90,
        max_value=99,
        value=95,
        step=1,
    ) / 100
    
    # Store in session state
    st.session_state.data_source = data_source
    st.session_state.risk_free_rate = risk_free_rate
    st.session_state.confidence_level = confidence_level
    if start_date:
        st.session_state.start_date = start_date
    if end_date:
        st.session_state.end_date = end_date
    
    st.markdown("---")
    
    st.markdown("### About")
    st.info(
        """
        **QuantLib Pro v1.0.0**
        
        A comprehensive quantitative finance platform built with:
        - FastAPI for REST API
        - Streamlit for UI
        - NumPy/SciPy for analytics
        - Plotly for visualization
        
        Week 12: UI Layer
        """
    )
    
    st.markdown("---")
    
    # System status
    st.markdown("### 🔍 System Status")
    
    import requests
    
    try:
        # Try to ping the API health endpoint
        response = requests.get("http://localhost:8000/health/", timeout=2)
        if response.status_code == 200:
            st.success("✅ API: Online")
        else:
            st.warning("⚠️ API: Degraded")
    except:
        st.error("❌ API: Offline")
    
    st.success("✅ UI: Online")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    QuantLib Pro © 2026 | Built with Streamlit | 
    <a href="https://github.com/gdukens/quant-simulator" target="_blank">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
