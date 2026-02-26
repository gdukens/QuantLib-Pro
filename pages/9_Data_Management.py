"""
Data Management Dashboard - QuantLib Pro

User-friendly interface for managing market data, cache, and data sources.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Data Management", page_icon="", layout="wide")

st.title("Data Management")
st.markdown("Manage market data sources, cache, and data quality.")

# ─── Tabs ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    " Fetch Data",
    " Cache Management",
    " Data Quality",
    " Data Sources"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: FETCH DATA
# ─────────────────────────────────────────────────────────────────────────────

with tab1:
    st.subheader("Fetch Market Data")
    st.markdown("Download and preview market data for stocks, options, and indices.")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        tickers_input = st.text_input(
            "Ticker Symbols",
            value="AAPL, MSFT, GOOGL",
            help="Enter comma-separated ticker symbols (e.g., AAPL, SPY, ^GSPC)"
        )
        tickers = [t.strip().upper() for t in tickers_input.split(",")]
    
    with col2:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365)
        )
    
    with col3:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )
    
    col_fetch, col_clear = st.columns([1, 1])
    
    with col_fetch:
        fetch_button = st.button(" Fetch Data", type="primary", use_container_width=True)
    
    with col_clear:
        clear_cache = st.button(" Clear Cache", use_container_width=True)
    
    if fetch_button:
        st.markdown("---")
        
        try:
            from quantlib_pro.data.market_data import MarketDataProvider
            from quantlib_pro.data.fetcher import DataFetchError
            
            provider = MarketDataProvider()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            data_collection = {}
            
            for idx, ticker in enumerate(tickers):
                status_text.text(f"Fetching {ticker}... ({idx+1}/{len(tickers)})")
                
                try:
                    data = provider.get_stock_data(
                        ticker,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d")
                    )
                    data_collection[ticker] = data
                    st.success(f" {ticker}: {len(data)} rows fetched")
                
                except DataFetchError as e:
                    st.error(f" {ticker}: Failed - {str(e)}")
                
                progress_bar.progress((idx + 1) / len(tickers))
            
            status_text.text(" Fetch complete!")
            
            # Display summary
            if data_collection:
                st.subheader("Data Summary")
                
                summary_data = []
                for ticker, df in data_collection.items():
                    summary_data.append({
                        "Ticker": ticker,
                        "Rows": len(df),
                        "Start": df.index[0].strftime("%Y-%m-%d"),
                        "End": df.index[-1].strftime("%Y-%m-%d"),
                        "Latest Close": f"${df['Close'].iloc[-1]:.2f}",
                        "Avg Volume": f"{df['Volume'].mean():,.0f}"
                    })
                
                st.dataframe(
                    pd.DataFrame(summary_data),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Preview first ticker
                if data_collection:
                    first_ticker = list(data_collection.keys())[0]
                    st.subheader(f" Preview: {first_ticker}")
                    
                    # Create price chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=data_collection[first_ticker].index,
                        y=data_collection[first_ticker]['Close'],
                        name='Close Price',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    fig.update_layout(
                        title=f"{first_ticker} Price History",
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        hovermode='x unified',
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show data table
                    st.dataframe(
                        data_collection[first_ticker].tail(10),
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f" Unexpected error: {str(e)}")
    
    if clear_cache:
        try:
            from quantlib_pro.data.cache import l1_clear
            l1_clear()
            st.success(" Memory cache cleared!")
        except Exception as e:
            st.error(f" Failed to clear cache: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: CACHE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

with tab2:
    st.subheader("Cache Management")
    st.markdown("View and manage the multi-tier caching system.")
    
    # Cache tiers info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(" L1: Memory", "Sub-millisecond", "Hot data")
        st.caption("Process-local dictionary cache")
    
    with col2:
        st.metric(" L2: Redis", "1-5 ms", "Warm data")
        st.caption("Distributed cache with persistence")
    
    with col3:
        st.metric(" L3: File System", "10-50 ms", "Cold data")
        st.caption("Parquet files for long-term storage")
    
    st.markdown("---")
    
    # Cache stats
    try:
        import os
        from quantlib_pro.data import cache
        
        # L1 stats
        st.subheader("Cache Statistics")
        
        l1_count = len(cache._L1)
        st.write(f"**L1 (Memory) Entries:** {l1_count}")
        
        if l1_count > 0:
            # Show L1 keys
            with st.expander("View L1 Cache Keys"):
                for key in list(cache._L1.keys())[:20]:  # Show first 20
                    st.code(key, language=None)
                if l1_count > 20:
                    st.caption(f"... and {l1_count - 20} more")
        
        # L3 stats (file cache)
        cache_dir = cache._CACHE_DIR
        if os.path.exists(cache_dir):
            files = [f for f in os.listdir(cache_dir) if f.endswith('.parquet')]
            total_size = sum(
                os.path.getsize(os.path.join(cache_dir, f))
                for f in files
            )
            st.write(f"**L3 (File) Entries:** {len(files)}")
            st.write(f"**Total Size:** {total_size / 1024 / 1024:.2f} MB")
        else:
            st.info(" File cache directory not created yet")
        
        # Clear buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(" Clear L1 (Memory)", use_container_width=True):
                cache.l1_clear()
                st.success(" L1 cache cleared!")
                st.rerun()
        
        with col2:
            if st.button(" Clear L2 (Redis)", use_container_width=True, disabled=True):
                st.info("Redis cache clearing requires connection")
        
        with col3:
            if st.button(" Clear L3 (Files)", use_container_width=True):
                if os.path.exists(cache_dir):
                    import shutil
                    shutil.rmtree(cache_dir)
                    os.makedirs(cache_dir)
                    st.success(" File cache cleared!")
                    st.rerun()
    
    except Exception as e:
        st.error(f" Error loading cache stats: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: DATA QUALITY
# ─────────────────────────────────────────────────────────────────────────────

with tab3:
    st.subheader("Data Quality Validation")
    st.markdown("Check data quality for market data using built-in contracts.")
    
    ticker_quality = st.text_input("Ticker to Validate", value="AAPL")
    
    if st.button(" Run Quality Check", type="primary"):
        try:
            from quantlib_pro.data.market_data import MarketDataProvider
            from quantlib_pro.data.quality import DataValidator, QualityContract
            
            st.info(f"Validating {ticker_quality}...")
            
            provider = MarketDataProvider()
            data = provider.get_stock_data(ticker_quality, period="1y")
            
            # Run validation
            validator = DataValidator()
            contract = QualityContract(
                required_columns=['Open', 'High', 'Low', 'Close', 'Volume'],
                min_rows=1
            )
            report = validator.validate(data, contract)
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_icon = "" if report.is_valid else ""
                st.metric("Status", f"{status_icon} {'Valid' if report.is_valid else 'Invalid'}")
            
            with col2:
                st.metric("Rows", report.row_count)
            
            with col3:
                st.metric("Completeness", f"{report.completeness * 100:.1f}%")
            
            # Violations
            if report.violations:
                st.error("** Violations Found:**")
                for violation in report.violations:
                    st.write(f"- {violation}")
            
            # Warnings
            if report.warnings:
                st.warning("** Warnings:**")
                for warning in report.warnings:
                    st.write(f"- {warning}")
            
            if not report.violations and not report.warnings:
                st.success(" No issues found! Data quality is excellent.")
            
            # Data preview
            st.subheader("Data Preview")
            st.dataframe(data.head(10), use_container_width=True)
            
            # Quality visualizations
            st.subheader("Data Quality Metrics")
            
            # Missing data heatmap
            missing_pct = data.isnull().sum() / len(data) * 100
            if missing_pct.sum() > 0:
                fig = px.bar(
                    x=missing_pct.index,
                    y=missing_pct.values,
                    labels={'x': 'Column', 'y': 'Missing (%)'},
                    title='Missing Data by Column'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success(" No missing data!")
            
            # Price consistency check
            high_low_issues = (data['High'] < data['Low']).sum()
            high_close_issues = (data['High'] < data['Close']).sum()
            low_close_issues = (data['Low'] > data['Close']).sum()
            
            consistency_data = pd.DataFrame({
                'Check': ['High < Low', 'High < Close', 'Low > Close'],
                'Issues': [high_low_issues, high_close_issues, low_close_issues]
            })
            
            st.subheader("Price Consistency")
            st.dataframe(consistency_data, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f" Validation failed: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: DATA SOURCES
# ─────────────────────────────────────────────────────────────────────────────

with tab4:
    st.subheader("Data Sources Configuration")
    st.markdown("Configure data providers and fallback chain.")
    
    # Data source info
    st.info("""
    **6-Level Fallback Chain:**
    1.  **Memory Cache** - Sub-millisecond (in-process dict)
    2.  **Redis Cache** - 1-5 ms (distributed cache)
    3.  **File Cache** - 10-50 ms (Parquet files)
    4.  **Yahoo Finance** - 300-2000 ms (primary API)
    5.  **Alternative API** - Configurable secondary source
    6.  **Synthetic Data** - Geometric Brownian Motion (last resort, flagged)
    """)
    
    st.markdown("---")
    
    # Yahoo Finance config
    st.subheader("Yahoo Finance (yfinance)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Status", " Active", "Primary source")
        st.metric("Rate Limit", "~2000/hour", "Approximate")
    
    with col2:
        st.metric("Retry Strategy", "Exponential backoff", "3 retries, 5s delay")
        st.metric("Coverage", "Global equities, options, ETFs", delta=None)
    
    # Test connection
    if st.button(" Test Yahoo Finance Connection"):
        try:
            from quantlib_pro.data.market_data import MarketDataProvider
            
            with st.spinner("Testing connection..."):
                provider = MarketDataProvider()
                data = provider.get_stock_data("SPY", period="5d")
                
                if len(data) > 0:
                    st.success(f" Connection successful! Retrieved {len(data)} rows for SPY")
                    st.dataframe(data.tail(3), use_container_width=True)
                else:
                    st.warning(" Connection successful but no data returned")
        
        except Exception as e:
            st.error(f" Connection test failed: {str(e)}")
    
    st.markdown("---")
    
    # Alternative providers (placeholder for future)
    st.subheader("Alternative Data Providers")
    
    st.info("""
    **Available Providers:** (Future Enhancement)
    - Alpha Vantage (Free tier: 5 calls/min)
    - IEX Cloud (Real-time market data)
    - Quandl (Financial & economic datasets)
    - CSV/Parquet Upload (Local files)
    """)
    
    # Upload local data
    st.subheader("Upload Local Data")
    
    uploaded_file = st.file_uploader(
        "Upload CSV or Parquet file",
        type=['csv', 'parquet'],
        help="File should have OHLCV columns and a date index"
    )
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file,  index_col=0, parse_dates=True)
            else:
                df = pd.read_parquet(uploaded_file)
            
            st.success(f" Loaded {len(df)} rows")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Validate uploaded data
            from quantlib_pro.data.quality import DataValidator, QualityContract
            
            validator = DataValidator() 
            contract = QualityContract(
                required_columns=['Open', 'High', 'Low', 'Close', 'Volume'],
                min_rows=1
            )
            report = validator.validate(df, contract)
            
            if report.is_valid:
                st.success(" Data passes quality checks")
            else:
                st.warning(f" Data quality issues: {report.violations}")
        
        except Exception as e:
            st.error(f" Failed to load file: {str(e)}")

# ─── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(" **Tip:** Use cache management to optimize performance. Clear cache when you need fresh data.")
