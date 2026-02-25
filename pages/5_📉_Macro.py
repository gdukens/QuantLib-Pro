"""
Macro Analysis Dashboard

Real-time macroeconomic indicators, market sentiment, and correlation analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

from quantlib_pro.ui import components
from quantlib_pro.data.market_data import MarketDataProvider

# Page config
st.set_page_config(
    page_title="Macro Analysis - QuantLib Pro",
    page_icon="📉",
    layout="wide",
)

st.title("📉 Macro Analysis")
st.markdown("Real-time macroeconomic indicators and market sentiment analysis using live market data.")

# Initialize session state
if "macro_vix_data" not in st.session_state:
    st.session_state.macro_vix_data = None
if "macro_treasury_data" not in st.session_state:
    st.session_state.macro_treasury_data = None

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    st.subheader("Analysis Period")
    lookback_period = st.selectbox(
        "Timeframe",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "5 Years"],
        index=3,
    )
    
    # Convert to days
    period_days = {
        "1 Month": 30,
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365,
        "2 Years": 730,
        "5 Years": 1825,
    }
    
    days = period_days[lookback_period]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    st.info(f"📅 **{start_date.strftime('%Y-%m-%d')}** to **{end_date.strftime('%Y-%m-%d')}**")
    
    st.markdown("---")
    
    st.subheader("Market Indicators")
    
    # VIX Thresholds
    show_vix_thresholds = st.checkbox("Show VIX Thresholds", value=True, help="Display fear/greed threshold lines")
    
    # Commodities Selection
    st.markdown("**Commodities to Display**")
    show_gold = st.checkbox("Gold (GC=F)", value=True)
    show_oil = st.checkbox("Crude Oil (CL=F)", value=True)
    show_copper = st.checkbox("Copper (HG=F)", value=True)
    
    st.markdown("---")
    
    st.subheader("Advanced Options")
    
    # Correlation window
    correlation_window = st.slider(
        "Correlation Window (days)",
        min_value=20,
        max_value=252,
        value=60,
        step=10,
        help="Rolling window for correlation calculations"
    )
    
    # VIX percentile calculation
    vix_percentile_window = st.selectbox(
        "VIX Percentile Window",
        ["Full Period", "1 Year", "2 Years", "5 Years"],
        index=0,
        help="Period for VIX percentile calculation"
    )
    
    st.markdown("---")
    
    refresh_button = st.button("🔄 Refresh Data", type="primary", use_container_width=True)

# Fetch data on refresh or first load
if refresh_button or st.session_state.macro_vix_data is None:
    with st.spinner("Fetching market data..."):
        data_provider = MarketDataProvider()
        
        # Fetch VIX (volatility/fear gauge)
        try:
            vix_df = data_provider.get_stock_data(
                ticker="^VIX",
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            st.session_state.macro_vix_data = vix_df
        except Exception as e:
            st.error(f"VIX data fetch failed: {str(e)}")
        
        # Fetch Treasury yields
        try:
            tnx_df = data_provider.get_stock_data(
                ticker="^TNX",  # 10-year Treasury
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            st.session_state.macro_treasury_data = tnx_df
        except Exception as e:
            st.error(f"Treasury data fetch failed: {str(e)}")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Sentiment", "📈 Economic Indicators", "🔗 Yield Curve", "📉 Volatility Analysis"])

with tab1:
    st.header("Market Sentiment Dashboard")
    
    # Add last update timestamp
    from datetime import datetime
    col_time, col_refresh = st.columns([3, 1])
    with col_time:
        if st.session_state.macro_vix_data is not None and not st.session_state.macro_vix_data.empty:
            last_update = st.session_state.macro_vix_data.index[-1]
            st.caption(f"📅 Data as of: {last_update.strftime('%Y-%m-%d %H:%M') if hasattr(last_update, 'strftime') else last_update}")
    with col_refresh:
        if st.button("🔄 Refresh Now", key="sentiment_refresh"):
            st.rerun()
    
    if st.session_state.macro_vix_data is not None and not st.session_state.macro_vix_data.empty:
        vix_df = st.session_state.macro_vix_data
        current_vix = vix_df['Close'].iloc[-1]
        
        # Determine lookback period based on user selection
        window_map = {
            "Full Period": len(vix_df),
            "1 Year": min(252, len(vix_df)),
            "2 Years": min(504, len(vix_df)),
            "5 Years": min(1260, len(vix_df))
        }
        lookback_days = window_map.get(vix_percentile_window, len(vix_df))
        
        # Calculate sentiment using PERCENTILE RANK (time-contextualized)
        # This is theoretically grounded: sentiment is RELATIVE to the selected period
        vix_window = vix_df['Close'].tail(lookback_days)
        
        # Percentile rank: where does current VIX fall in historical distribution?
        # Lower VIX = higher percentile = more greed (complacency)
        # Higher VIX = lower percentile = more fear (panic)
        percentile_rank = (vix_window < current_vix).sum() / len(vix_window) * 100
        
        # Invert: we want high score = greed (low VIX), low score = fear (high VIX)
        fear_greed_score = 100 - percentile_rank
        
        # Calculate statistics for context
        vix_mean = vix_window.mean()
        vix_std = vix_window.std()
        vix_min = vix_window.min()
        vix_max = vix_window.max()
        z_score = (current_vix - vix_mean) / vix_std if vix_std > 0 else 0
        
        # Determine sentiment level
        if fear_greed_score < 25:
            sentiment_label = "EXTREME FEAR"
            sentiment_color = "darkred"
            interpretation = "VIX is in the top 25% of its range - heightened volatility and risk aversion"
        elif fear_greed_score < 45:
            sentiment_label = "FEAR"
            sentiment_color = "orange"
            interpretation = "VIX is above average - elevated uncertainty and caution"
        elif fear_greed_score < 55:
            sentiment_label = "NEUTRAL"
            sentiment_color = "gray"
            interpretation = "VIX is near its historical average for this period"
        elif fear_greed_score < 75:
            sentiment_label = "GREED"
            sentiment_color = "lightgreen"
            interpretation = "VIX is below average - market complacency and confidence"
        else:
            sentiment_label = "EXTREME GREED"
            sentiment_color = "darkgreen"
            interpretation = "VIX is in the bottom 25% of its range - very low volatility and complacency"
        
        # Display context banner
        st.info(f"""
        **📊 Time-Contextualized Sentiment Analysis**  
        Current VIX: **{current_vix:.2f}** | Period: **{vix_percentile_window}** | Percentile Rank: **{100 - fear_greed_score:.1f}th**
        
        This score is **relative** to the selected time period. The same VIX value can indicate different sentiment 
        depending on context (e.g., VIX=15 after a calm year = greed, but VIX=15 after a crisis = extreme greed).
        
        **Period Statistics:** Min={vix_min:.2f} | Mean={vix_mean:.2f} | Max={vix_max:.2f} | Z-Score={z_score:.2f}
        """)

        
        # Create two columns: gauge and historical trend
        col_gauge, col_trend = st.columns([1, 1])
        
        with col_gauge:
            # Fear & Greed Gauge (Enhanced with animation)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=fear_greed_score,
                delta={'reference': 50, 'position': "bottom"},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={
                    'text': f"<b>Market Sentiment</b><br><span style='font-size:16px; color:{sentiment_color}'>{sentiment_label}</span>", 
                    'font': {'size': 20}
                },
                number={'font': {'size': 48}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white"},
                    'bar': {'color': sentiment_color, 'thickness': 0.5},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': sentiment_color,
                    'steps': [
                        {'range': [0, 25], 'color': "rgba(139, 0, 0, 0.3)", 'name': 'Extreme Fear'},
                        {'range': [25, 45], 'color': "rgba(255, 165, 0, 0.3)", 'name': 'Fear'},
                        {'range': [45, 55], 'color': "rgba(128, 128, 128, 0.3)", 'name': 'Neutral'},
                        {'range': [55, 75], 'color': "rgba(144, 238, 144, 0.3)", 'name': 'Greed'},
                        {'range': [75, 100], 'color': "rgba(0, 100, 0, 0.3)", 'name': 'Extreme Greed'}
                    ],
                    'threshold': {
                        'line': {'color': sentiment_color, 'width': 4},
                        'thickness': 0.85,
                        'value': fear_greed_score
                    }
                }
            ))
            
            fig_gauge.update_layout(
                height=350, 
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                font={'color': "white", 'family': "Arial"}
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col_trend:
            # Historical Sentiment Trend
            st.markdown(f"**📈 Sentiment Trend (Last 30 Days)**")
            st.caption(f"_Relative to {vix_percentile_window} baseline_")
            
            # Calculate historical sentiment scores using rolling percentiles
            vix_recent = vix_df['Close'].tail(30)
            sentiment_history = []
            dates_history = []
            
            # For each recent day, calculate its percentile rank within the full lookback window
            for i, (date, vix_val) in enumerate(vix_recent.items()):
                # Get the lookback window ending at this date
                end_idx = vix_df.index.get_loc(date)
                start_idx = max(0, end_idx - lookback_days + 1)
                historical_window = vix_df['Close'].iloc[start_idx:end_idx+1]
                
                if len(historical_window) > 10:  # Need minimum data points
                    percentile = (historical_window < vix_val).sum() / len(historical_window) * 100
                    score = 100 - percentile
                else:
                    score = 50  # Neutral if insufficient data
                
                sentiment_history.append(score)
                dates_history.append(date)
            
            # Create trend chart
            fig_trend = go.Figure()
            
            # Add sentiment line
            fig_trend.add_trace(go.Scatter(
                x=dates_history,
                y=sentiment_history,
                mode='lines+markers',
                name='Sentiment',
                line=dict(color=sentiment_color, width=3),
                marker=dict(size=6, color=sentiment_color),
                fill='tozeroy',
                fillcolor=f'rgba({255 if "GREED" in sentiment_label else 139}, {165 if "FEAR" in sentiment_label else (238 if "GREED" in sentiment_label else 0)}, {0}, 0.1)'
            ))
            
            # Add threshold zones
            fig_trend.add_hline(y=25, line_dash="dash", line_color="darkred", annotation_text="Extreme Fear", opacity=0.3)
            fig_trend.add_hline(y=75, line_dash="dash", line_color="darkgreen", annotation_text="Extreme Greed", opacity=0.3)
            fig_trend.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="Neutral", opacity=0.3)
            
            fig_trend.update_layout(
                height=350,
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Sentiment Score",
                yaxis=dict(range=[0, 100]),
                showlegend=False,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # VIX metrics  
        vix_20d_avg = vix_df['Close'].tail(20).mean()
        vix_change = current_vix - vix_df['Close'].iloc[-2]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Current VIX", f"{current_vix:.2f}", f"{vix_change:.2f}")
        with col2:
            st.metric(f"{vix_percentile_window} Mean", f"{vix_mean:.2f}")
        with col3:
            st.metric(f"{vix_percentile_window} Range", f"{vix_min:.2f} - {vix_max:.2f}")
        with col4:
            st.metric("Percentile Rank", f"{100 - fear_greed_score:.1f}th", 
                     help="Where current VIX ranks in the selected period (higher = more fear)")
        with col5:
            st.metric("Z-Score", f"{z_score:.2f}", 
                     help="Standard deviations from mean (higher = more fear)")
        
        st.markdown("---")
        
        # VIX interpretation with theoretical grounding
        st.subheader("📚 Methodology & Interpretation")
        
        st.markdown(f"""
        **Time-Contextualized Sentiment (Percentile-Based)**
        
        This implementation uses a **percentile rank** approach, which is theoretically grounded in:
        
        - **Regime-Dependent Volatility** (Ang & Bekaert, 2002): Market volatility exhibits time-varying regimes
        - **Relative Value Theory**: Sentiment should be assessed relative to recent conditions, not absolute levels
        - **Practitioner Standard**: VIX percentile ranks are used by institutional investors (CBOE White Papers)
        
        **Current Assessment ({vix_percentile_window} context):**
        - Current VIX (**{current_vix:.2f}**) ranks at the **{100-fear_greed_score:.1f}th percentile** of the past {vix_percentile_window.lower()}
        - {interpretation}
        - **Z-Score: {z_score:.2f}σ** - {abs(z_score):.1f} standard deviations {"above" if z_score > 0 else "below"} the mean
        
        **Why Percentiles Matter:**
        - VIX=15 in 2017 (low-vol regime) → ~70th percentile → Fear
        - VIX=15 in 2020 (post-COVID) → ~20th percentile → Extreme Greed
        - Same value, different context, different interpretation ✓
        """)
        
        st.markdown("---")
        
        # Percentile-based interpretation
        st.subheader("💡 Trading Implications")
        
        if fear_greed_score >= 75:
            st.success(f"""
            🟢 **EXTREME GREED - VIX at {100-fear_greed_score:.1f}th Percentile ({vix_percentile_window})**
            - Current VIX ({current_vix:.2f}) is near historical lows for this period
            - Market complacency at {abs(z_score):.1f}σ below average volatility
            - ⚠️ **Mean Reversion Risk**: Extended low volatility often precedes spikes
            - **Strategy**: Consider tail risk hedges (OTM puts), monitor VIX term structure
            - **Academic Note**: Volatility clustering (Mandelbrot, 1963) - calm periods don't last forever
            """)
        elif fear_greed_score >= 55:
            st.info(f"""
            🟢 **GREED - VIX at {100-fear_greed_score:.1f}th Percentile ({vix_percentile_window})**
            - Current VIX ({current_vix:.2f}) is below historical average for this period
            - Market confidence, but not extreme complacency
            - **Strategy**: Standard risk, consider cheap volatility protection
            """)
        elif fear_greed_score >= 45:
            st.info(f"""
            ⚪ **NEUTRAL - VIX at {100-fear_greed_score:.1f}th Percentile ({vix_percentile_window})**
            - Current VIX ({current_vix:.2f}) is near historical median for this period
            - Balanced market conditions
            - **Strategy**: Normal risk management, no extreme positioning
            """)
        elif fear_greed_score >= 25:
            st.warning(f"""
            🟠 **FEAR - VIX at {100-fear_greed_score:.1f}th Percentile ({vix_percentile_window})**
            - Current VIX ({current_vix:.2f}) is above historical average for this period
            - Elevated uncertainty at {abs(z_score):.1f}σ above average volatility
            - **Strategy**: Reduce leverage, defensive positioning, quality over growth
            """)
        else:
            st.error(f"""
            🔴 **EXTREME FEAR - VIX at {100-fear_greed_score:.1f}th Percentile ({vix_percentile_window})**
            - Current VIX ({current_vix:.2f}) is near historical highs for this period
            - Panic conditions at {abs(z_score):.1f}σ above average volatility
            - **Opportunity**: Historically, extreme fear creates buying opportunities (Shefrin & Statman, 1985)
            - **Strategy**: Contrarian positioning for long-term investors, but respect momentum
            - **Caution**: "Catching falling knives" - ensure proper risk management
            """)
        
        st.markdown("---")
        
        # VIX historical chart
        st.subheader("VIX Historical Evolution")
        
        fig_vix = go.Figure()
        
        fig_vix.add_trace(go.Scatter(
            x=vix_df.index,
            y=vix_df['Close'],
            mode='lines',
            name='VIX',
            line=dict(color='steelblue', width=2),
            fill='tozeroy',
            fillcolor='rgba(70, 130, 180, 0.2)'
        ))
        
        # Add threshold lines conditionally
        if show_vix_thresholds:
            fig_vix.add_hline(y=15, line_dash="dash", line_color="green", annotation_text="Low Volatility")
            fig_vix.add_hline(y=20, line_dash="dash", line_color="gray", annotation_text="Normal")
            fig_vix.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="High Stress")
        
        fig_vix.update_layout(
            title=f"CBOE Volatility Index (VIX) - {lookback_period}",
            xaxis_title="Date",
            yaxis_title="VIX Level",
            height=400,
            template="plotly_white",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_vix, use_container_width=True)
        
    else:
        st.warning("📊 VIX data unavailable. Click 'Refresh Data' to fetch market sentiment indicators.")

with tab2:
    st.header("Economic Indicators")
    
    # Fetch major market indices as economic proxies
    if refresh_button or True:  # Always show this section
        with st.spinner("Loading economic proxies..."):
            data_provider = MarketDataProvider()
            
            col1, col2 = st.columns(2)
            
            # S&P 500 (market health)
            with col1:
                try:
                    sp500_df = data_provider.get_stock_data(
                        ticker="^GSPC",
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d')
                    )
                    
                    if not sp500_df.empty:
                        current_sp = sp500_df['Close'].iloc[-1]
                        sp_change = ((sp500_df['Close'].iloc[-1] / sp500_df['Close'].iloc[0]) - 1) * 100
                        
                        st.metric("S&P 500", f"{current_sp:,.2f}", f"{sp_change:+.2f}%", help="Broad market performance")
                        
                        fig_sp = px.line(sp500_df, y='Close', title=f"S&P 500 - {lookback_period}")
                        fig_sp.update_layout(height=250, showlegend=False, template="plotly_white")
                        st.plotly_chart(fig_sp, use_container_width=True)
                except Exception as e:
                    st.error(f"S&P 500 data unavailable: {str(e)}")
            
            # Dollar Index (currency strength)
            with col2:
                try:
                    dxy_df = data_provider.get_stock_data(
                        ticker="DX-Y.NYB",
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d')
                    )
                    
                    if not dxy_df.empty:
                        current_dxy = dxy_df['Close'].iloc[-1]
                        dxy_change = ((dxy_df['Close'].iloc[-1] / dxy_df['Close'].iloc[0]) - 1) * 100
                        
                        st.metric("Dollar Index (DXY)", f"{current_dxy:.2f}", f"{dxy_change:+.2f}%", help="USD strength vs basket of currencies")
                        
                        fig_dxy = px.line(dxy_df, y='Close', title=f"US Dollar Index - {lookback_period}")
                        fig_dxy.update_layout(height=250, showlegend=False, template="plotly_white")
                        st.plotly_chart(fig_dxy, use_container_width=True)
                except Exception as e:
                    st.info(f"Dollar Index data unavailable (common limitation)")
        
        st.markdown("---")
        
        # Commodities as inflation/growth proxies
        st.subheader("Commodity Indicators")
        
        # Build columns based on selected commodities
        selected_commodities = []
        if show_gold:
            selected_commodities.append(("Gold", "GC=F", "$"))
        if show_oil:
            selected_commodities.append(("Crude Oil", "CL=F", "$"))
        if show_copper:
            selected_commodities.append(("Copper", "HG=F", "$"))
        
        if selected_commodities:
            cols = st.columns(len(selected_commodities))
            
            for idx, (name, ticker, symbol) in enumerate(selected_commodities):
                with cols[idx]:
                    try:
                        commodity_df = data_provider.get_stock_data(
                            ticker=ticker,
                            start_date=start_date.strftime('%Y-%m-%d'),
                            end_date=end_date.strftime('%Y-%m-%d')
                        )
                        if not commodity_df.empty:
                            current = commodity_df['Close'].iloc[-1]
                            change = ((commodity_df['Close'].iloc[-1] / commodity_df['Close'].iloc[0]) - 1) * 100
                            
                            if name == "Gold":
                                help_text = "Safe haven / inflation hedge"
                            elif name == "Crude Oil":
                                help_text = "Economic activity / inflation"
                            else:  # Copper
                                help_text = "Dr. Copper: economic growth proxy"
                            
                            if name == "Copper":
                                st.metric(name, f"{symbol}{current:.4f}", f"{change:+.2f}%", help=help_text)
                            else:
                                st.metric(name, f"{symbol}{current:,.2f}", f"{change:+.2f}%", help=help_text)
                    except Exception:
                        st.info(f"{name} data unavailable")
        else:
            st.info("No commodities selected. Enable filters in the sidebar.")

with tab3:
    st.header("Treasury Yield Curve")
    
    if st.session_state.macro_treasury_data is not None and not st.session_state.macro_treasury_data.empty:
        tnx_df = st.session_state.macro_treasury_data
        current_10y = tnx_df['Close'].iloc[-1]
        
        st.metric("10-Year Treasury Yield", f"{current_10y:.2f}%", help="Benchmark risk-free rate")
        
        # 10-year yield chart
        fig_tnx = go.Figure()
        
        fig_tnx.add_trace(go.Scatter(
            x=tnx_df.index,
            y=tnx_df['Close'],
            mode='lines',
            name='10Y Yield',
            line=dict(color='darkgreen', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 100, 0, 0.1)'
        ))
        
        fig_tnx.update_layout(
            title=f"10-Year Treasury Yield - {lookback_period}",
            xaxis_title="Date",
            yaxis_title="Yield (%)",
            height=400,
            template="plotly_white",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_tnx, use_container_width=True)
        
        st.markdown("---")
        
        # Yield interpretation
        st.subheader("Yield Analysis")
        
        yield_change = current_10y - tnx_df['Close'].iloc[0]
        
        if yield_change > 0.5:
            st.warning(f"""
            📈 **Rising Rates Environment** (+{yield_change:.2f}% since start of period)
            - Higher borrowing costs
            - Pressure on growth stocks and bonds
            - Potential economic slowdown ahead
            - **Strategy**: Short duration bonds, value stocks, financials
            """)
        elif yield_change < -0.5:
            st.info(f"""
            📉 **Falling Rates Environment** ({yield_change:.2f}% since start of period)
            - Lower borrowing costs
            - Supportive for growth assets
            - Potential recessionary concerns
            - **Strategy**: Long duration bonds, growth stocks, REITs
            """)
        else:
            st.success("""
            ➡️ **Stable Rates**
            - Range-bound yields
            - Balanced economic outlook
            - **Strategy**: Maintain diversified allocation
            """)
        
    else:
        st.warning("📊 Treasury data unavailable. Click 'Refresh Data' to fetch yield information.")

with tab4:
    st.header("Volatility Regime Analysis")
    
    if st.session_state.macro_vix_data is not None and not st.session_state.macro_vix_data.empty:
        vix_df = st.session_state.macro_vix_data
        
        # Calculate volatility metrics
        vix_current = vix_df['Close'].iloc[-1]
        vix_mean = vix_df['Close'].mean()
        vix_std = vix_df['Close'].std()
        vix_percentile = (vix_df['Close'] < vix_current).sum() / len(vix_df) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current VIX", f"{vix_current:.2f}")
        with col2:
            st.metric("Mean VIX", f"{vix_mean:.2f}")
        with col3:
            st.metric("Std Dev", f"{vix_std:.2f}")
        with col4:
            st.metric("Percentile", f"{vix_percentile:.0f}%", help="Current VIX vs historical distribution")
        
        st.markdown("---")
        
        # VIX vs S&P 500 correlation
        st.subheader("VIX vs Market Performance")
        
        try:
            data_provider = MarketDataProvider()
            sp500_df = data_provider.get_stock_data(
                ticker="^GSPC",
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if not sp500_df.empty and len(sp500_df) > 1:
                # Properly align data by date index
                vix_aligned = vix_df[['Close']].copy()
                vix_aligned.columns = ['VIX']
                
                sp500_aligned = sp500_df[['Close']].copy()
                sp500_aligned.columns = ['SP500']
                
                # Merge on date index
                combined_df = vix_aligned.join(sp500_aligned, how='inner')
                
                # Calculate S&P 500 returns
                combined_df['SP500_Returns'] = combined_df['SP500'].pct_change() * 100
                
                # Drop NaN values
                combined_df = combined_df.dropna()
                
                if len(combined_df) > 10:  # Need at least 10 data points
                    correlation = combined_df['VIX'].corr(combined_df['SP500_Returns'])
                    
                    st.info(f"""
                    📊 **VIX vs S&P 500 Correlation**: {correlation:.2f}
                    
                    Typical behavior: VIX rises when S&P 500 falls (negative correlation).
                    Current correlation: {'Strong negative' if correlation < -0.5 else 'Moderate negative' if correlation < -0.2 else 'Weak or positive (unusual)'}
                    
                    Data points: {len(combined_df)}
                    """)
                    
                    # Scatter plot
                    fig_scatter = px.scatter(
                        combined_df,
                        x='SP500_Returns',
                        y='VIX',
                        title="VIX vs S&P 500 Daily Returns",
                        labels={'SP500_Returns': 'S&P 500 Daily Return (%)', 'VIX': 'VIX Level'},
                        trendline="ols",
                        opacity=0.6
                    )
                    fig_scatter.update_layout(height=400, template="plotly_white")
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    # Rolling correlation
                    if len(combined_df) >= correlation_window:
                        st.subheader(f"Rolling Correlation ({correlation_window}-day window)")
                        
                        rolling_corr = combined_df['VIX'].rolling(window=correlation_window).corr(
                            combined_df['SP500_Returns']
                        )
                        
                        fig_rolling = go.Figure()
                        fig_rolling.add_trace(go.Scatter(
                            x=combined_df.index,
                            y=rolling_corr,
                            mode='lines',
                            name=f'{correlation_window}-day Correlation',
                            line=dict(color='purple', width=2)
                        ))
                        
                        fig_rolling.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Zero Correlation")
                        fig_rolling.add_hline(y=-0.5, line_dash="dot", line_color="green", annotation_text="Strong Negative")
                        
                        fig_rolling.update_layout(
                            title=f"Rolling VIX-SPY Correlation - {correlation_window} Days",
                            xaxis_title="Date",
                            yaxis_title="Correlation",
                            height=350,
                            template="plotly_white",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig_rolling, use_container_width=True)
                else:
                    st.warning("Insufficient data points for correlation analysis. Try a longer time period.")
                
        except Exception as e:
            st.warning(f"S&P 500 correlation analysis unavailable: {str(e)}")
        
        st.markdown("---")
        
        # Volatility distribution
        st.subheader("VIX Distribution")
        
        fig_hist = go.Figure()
        
        fig_hist.add_trace(go.Histogram(
            x=vix_df['Close'],
            nbinsx=30,
            name='VIX Frequency',
            marker_color='steelblue',
            opacity=0.7
        ))
        
        fig_hist.add_vline(x=vix_current, line_dash="dash", line_color="red", annotation_text=f"Current: {vix_current:.1f}")
        fig_hist.add_vline(x=vix_mean, line_dash="dot", line_color="green", annotation_text=f"Mean: {vix_mean:.1f}")
        
        fig_hist.update_layout(
            title=f"VIX Distribution - {lookback_period}",
            xaxis_title="VIX Level",
            yaxis_title="Frequency",
            height=400,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
        
    else:
        st.warning("📊 VIX data unavailable. Click 'Refresh Data' to fetch volatility metrics.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Macro Analysis powered by QuantLib Pro | Data: Yahoo Finance (VIX, Treasury, Indices, Commodities)
    </div>
    """,
    unsafe_allow_html=True,
)
