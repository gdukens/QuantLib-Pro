"""
📈 Market Analysis Dashboard

Comprehensive stock analysis: trend detection, volatility comparison, and technical indicators.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy import stats

# Page config
st.set_page_config(
    page_title="Market Analysis",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Market Analysis")
st.markdown("Technical analysis, trend detection, and volatility comparison across multiple stocks")

# ============================================================================
# Sidebar: Configuration
# ============================================================================

# Common ticker list
COMMON_TICKERS = [
    "SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "USO", "UUP",
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
    "JPM", "V", "JNJ", "WMT", "PG", "MA", "HD", "DIS", "BAC", "XOM",
    "NFLX", "ADBE", "CRM", "CSCO", "INTC", "AMD", "QCOM", "TXN",
    "XLF", "XLE", "XLK", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB"
]

with st.sidebar:
    st.header("⚙️ Analysis Configuration")
    
    # Stock selection
    st.subheader("Stocks to Analyze")
    
    # Multi-select dropdown
    selected_tickers = st.multiselect(
        "Select Assets",
        options=COMMON_TICKERS,
        default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"],
        help="Select one or more tickers to analyze"
    )
    
    # Optional: Custom ticker input
    custom_ticker = st.text_input(
        "Add Custom Ticker (optional)",
        value="",
        help="Add any ticker not in the list"
    )
    
    if custom_ticker.strip():
        selected_tickers.append(custom_ticker.strip().upper())
    
    tickers = selected_tickers
    
    # Date range
    st.subheader("Analysis Period")
    
    period_option = st.selectbox(
        "Time Period",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "Custom"],
        index=3
    )
    
    if period_option == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=365)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now()
            )
    else:
        period_map = {"1 Month": 30, "3 Months": 90, "6 Months": 180, "1 Year": 365, "2 Years": 730}
        days = period_map[period_option]
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
    
    # Technical indicators parameters
    st.subheader("Technical Indicators")
    
    short_ma = st.slider("Short MA Period", min_value=5, max_value=50, value=20, step=5)
    long_ma = st.slider("Long MA Period", min_value=20, max_value=200, value=50, step=10)
    
    trend_threshold = st.slider(
        "Trend Slope Threshold",
        min_value=0.01,
        max_value=0.20,
        value=0.05,
        step=0.01,
        help="Minimum slope to consider uptrend/downtrend"
    )
    
    # Volatility parameters
    st.subheader("Volatility Analysis")
    
    vol_window = st.slider(
        "Volatility Window (days)",
        min_value=10,
        max_value=100,
        value=30,
        step=5,
        help="Rolling window for volatility calculation"
    )
    
    annualize_vol = st.checkbox("Annualize Volatility", value=True)

# ============================================================================
# Data Fetching
# ============================================================================

@st.cache_data(ttl=3600)
def fetch_stock_data(tickers, start_date, end_date):
    """Fetch historical data for stocks"""
    from quantlib_pro.data.market_data import MarketDataProvider
    
    provider = MarketDataProvider()
    all_data = {}
    
    for ticker in tickers:
        try:
            data = provider.get_stock_data(ticker, period='max')
            if data is not None and not data.empty:
                # Convert dates to timezone-aware if needed
                start_ts = pd.Timestamp(start_date)
                end_ts = pd.Timestamp(end_date)
                
                # If data index is timezone-aware, make timestamps timezone-aware too
                if hasattr(data.index, 'tz') and data.index.tz is not None:
                    if start_ts.tz is None:
                        start_ts = start_ts.tz_localize('UTC').tz_convert(data.index.tz)
                    if end_ts.tz is None:
                        end_ts = end_ts.tz_localize('UTC').tz_convert(data.index.tz)
                
                # Filter by date range
                data = data[(data.index >= start_ts) & (data.index <= end_ts)]
                all_data[ticker] = data
        except Exception as e:
            st.warning(f"Could not fetch data for {ticker}: {str(e)}")
    
    if not all_data:
        return None
    
    return all_data

# Fetch data
try:
    with st.spinner("Fetching market data..."):
        stock_data = fetch_stock_data(tickers, start_date, end_date)
        
        if stock_data is None or not stock_data:
            st.error("Could not fetch data for any tickers. Please check your symbols and try again.")
            st.stop()
        
        # Show summary
        with st.sidebar:
            st.success(f"✅ Loaded {len(stock_data)} stocks")
            min_days = min(len(df) for df in stock_data.values())
            st.write(f"**Data points:** {min_days} days")

except Exception as e:
    st.error(f"Error loading market data: {str(e)}")
    st.stop()

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_trend(prices, short_window=20, long_window=50, threshold=0.05):
    """Calculate trend using moving averages and slope"""
    ma_short = prices.rolling(window=short_window).mean()
    ma_long = prices.rolling(window=long_window).mean()
    
    # Calculate slope of long MA
    ma_long_clean = ma_long.dropna()
    if len(ma_long_clean) < 2:
        return "Insufficient Data", 0, ma_short, ma_long
    
    x = np.arange(len(ma_long_clean))
    slope = np.polyfit(x, ma_long_clean.values, 1)[0]
    
    # Normalize slope by price level
    avg_price = prices.mean()
    normalized_slope = slope / avg_price if avg_price > 0 else 0
    
    # Determine trend
    if normalized_slope > threshold:
        trend = "Uptrend"
    elif normalized_slope < -threshold:
        trend = "Downtrend"
    else:
        trend = "Sideways"
    
    return trend, normalized_slope, ma_short, ma_long

def calculate_volatility(returns, window=30, annualize=True):
    """Calculate rolling volatility"""
    vol = returns.rolling(window=window).std()
    if annualize:
        vol = vol * np.sqrt(252)
    return vol

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Trend Analysis",
    "📉 Volatility Comparison",
    "📈 Technical Charts",
    "🔢 Statistics"
])

# ============================================================================
# Tab 1: Trend Analysis
# ============================================================================
with tab1:
    st.header("Trend Analysis")
    
    st.markdown("""
    Identify market trends using moving average crossovers and slope analysis.
    - **Uptrend**: Long-term MA has positive slope above threshold
    - **Downtrend**: Long-term MA has negative slope below threshold
    - **Sideways**: Slope within threshold range
    """)
    
    # Calculate trends for all stocks
    trend_results = []
    
    for ticker, data in stock_data.items():
        prices = data['Close']
        trend, slope, ma_short, ma_long = calculate_trend(
            prices, short_ma, long_ma, trend_threshold
        )
        
        # Calculate additional metrics
        current_price = prices.iloc[-1]
        price_change = ((current_price / prices.iloc[0]) - 1) * 100
        
        trend_results.append({
            'Ticker': ticker,
            'Trend': trend,
            'Slope': slope,
            'Current Price': current_price,
            'Period Change': price_change,
            'Above Short MA': current_price > ma_short.iloc[-1] if not pd.isna(ma_short.iloc[-1]) else False,
            'Above Long MA': current_price > ma_long.iloc[-1] if not pd.isna(ma_long.iloc[-1]) else False
        })
    
    trend_df = pd.DataFrame(trend_results)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        uptrend_count = (trend_df['Trend'] == 'Uptrend').sum()
        st.metric("Uptrend Stocks", uptrend_count, delta=f"{uptrend_count/len(trend_df)*100:.0f}%")
    
    with col2:
        downtrend_count = (trend_df['Trend'] == 'Downtrend').sum()
        st.metric("Downtrend Stocks", downtrend_count, delta=f"{downtrend_count/len(trend_df)*100:.0f}%")
    
    with col3:
        sideways_count = (trend_df['Trend'] == 'Sideways').sum()
        st.metric("Sideways Stocks", sideways_count, delta=f"{sideways_count/len(trend_df)*100:.0f}%")
    
    with col4:
        avg_change = trend_df['Period Change'].mean()
        st.metric("Avg Period Return", f"{avg_change:.2f}%")
    
    # Trend table
    st.subheader("Trend Summary")
    
    # Color code trends
    def color_trend(val):
        if val == 'Uptrend':
            return 'background-color: #2ca02c; color: white'
        elif val == 'Downtrend':
            return 'background-color: #d62728; color: white'
        else:
            return 'background-color: #ff7f0e; color: white'
    
    styled_df = trend_df.copy()
    styled_df['Slope'] = styled_df['Slope'].apply(lambda x: f"{x:.4f}")
    styled_df['Current Price'] = styled_df['Current Price'].apply(lambda x: f"${x:.2f}")
    styled_df['Period Change'] = styled_df['Period Change'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(
        styled_df.style.applymap(color_trend, subset=['Trend']),
        use_container_width=True,
        height=400
    )
    
    # Trend distribution pie chart
    st.subheader("Trend Distribution")
    
    trend_counts = trend_df['Trend'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=trend_counts.index,
        values=trend_counts.values,
        marker=dict(colors=['#2ca02c', '#d62728', '#ff7f0e']),
        hole=0.3
    )])
    
    fig.update_layout(
        template='plotly_dark',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# Tab 2: Volatility Comparison
# ============================================================================
with tab2:
    st.header("Volatility Comparison")
    
    st.markdown("""
    Compare volatility across stocks to identify relative risk levels.
    """)
    
    # Calculate volatilities
    vol_results = []
    
    for ticker, data in stock_data.items():
        returns = data['Close'].pct_change().dropna()
        
        # Current volatility (last value of rolling)
        vol = calculate_volatility(returns, vol_window, annualize_vol)
        current_vol = vol.iloc[-1] if not pd.isna(vol.iloc[-1]) else 0
        
        # Average volatility
        avg_vol = vol.mean()
        
        # Min/Max volatility
        min_vol = vol.min()
        max_vol = vol.max()
        
        vol_results.append({
            'Ticker': ticker,
            'Current Vol': current_vol * 100,
            'Average Vol': avg_vol * 100,
            'Min Vol': min_vol * 100,
            'Max Vol': max_vol * 100,
            'Volatility Range': (max_vol - min_vol) * 100
        })
    
    vol_df = pd.DataFrame(vol_results).sort_values('Current Vol', ascending=False)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        most_volatile = vol_df.iloc[0]['Ticker']
        most_volatile_val = vol_df.iloc[0]['Current Vol']
        st.metric("Most Volatile", most_volatile, f"{most_volatile_val:.2f}%")
    
    with col2:
        least_volatile = vol_df.iloc[-1]['Ticker']
        least_volatile_val = vol_df.iloc[-1]['Current Vol']
        st.metric("Least Volatile", least_volatile, f"{least_volatile_val:.2f}%")
    
    with col3:
        avg_volatility = vol_df['Current Vol'].mean()
        st.metric("Average Volatility", f"{avg_volatility:.2f}%")
    
    with col4:
        vol_spread = most_volatile_val - least_volatile_val
        st.metric("Volatility Spread", f"{vol_spread:.2f}%")
    
    # Volatility bar chart
    st.subheader("Current Volatility Comparison")
    
    fig = go.Figure(data=[
        go.Bar(
            x=vol_df['Ticker'],
            y=vol_df['Current Vol'],
            marker_color='skyblue',
            text=vol_df['Current Vol'].round(2),
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=f"Stock Volatility Comparison ({'Annualized' if annualize_vol else 'Daily'})",
        xaxis_title="Ticker",
        yaxis_title=f"Volatility ({'Annualized %' if annualize_vol else 'Daily %'})",
        template='plotly_dark',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Volatility table
    st.subheader("Detailed Volatility Metrics")
    
    styled_vol_df = vol_df.copy()
    for col in ['Current Vol', 'Average Vol', 'Min Vol', 'Max Vol', 'Volatility Range']:
        styled_vol_df[col] = styled_vol_df[col].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(styled_vol_df, use_container_width=True, height=400)
    
    # Rolling volatility over time
    st.subheader("Rolling Volatility Over Time")
    
    fig2 = go.Figure()
    
    for ticker, data in stock_data.items():
        returns = data['Close'].pct_change().dropna()
        vol = calculate_volatility(returns, vol_window, annualize_vol) * 100
        
        fig2.add_trace(go.Scatter(
            x=vol.index,
            y=vol,
            mode='lines',
            name=ticker,
            line=dict(width=2)
        ))
    
    fig2.update_layout(
        title=f"{vol_window}-Day Rolling Volatility",
        xaxis_title="Date",
        yaxis_title=f"Volatility ({'Annualized %' if annualize_vol else 'Daily %'})",
        template='plotly_dark',
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================================
# Tab 3: Technical Charts
# ============================================================================
with tab3:
    st.header("Technical Analysis Charts")
    
    # Stock selector for detailed view
    selected_stock = st.selectbox("Select stock for detailed chart", list(stock_data.keys()))
    
    data = stock_data[selected_stock]
    prices = data['Close']
    
    # Calculate indicators
    trend, slope, ma_short_series, ma_long_series = calculate_trend(
        prices, short_ma, long_ma, trend_threshold
    )
    
    returns = prices.pct_change().dropna()
    vol = calculate_volatility(returns, vol_window, annualize_vol) * 100
    
    # Create subplot figure
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(
            f'{selected_stock} Price & Moving Averages',
            'Daily Returns',
            f'{vol_window}-Day Rolling Volatility'
        )
    )
    
    # Price and MAs
    fig.add_trace(
        go.Scatter(x=prices.index, y=prices, mode='lines', name='Price',
                  line=dict(color='#1f77b4', width=2)),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=ma_short_series.index, y=ma_short_series, mode='lines',
                  name=f'MA{short_ma}', line=dict(color='#ff7f0e', width=1.5)),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=ma_long_series.index, y=ma_long_series, mode='lines',
                  name=f'MA{long_ma}', line=dict(color='#2ca02c', width=1.5)),
        row=1, col=1
    )
    
    # Returns
    colors = ['#d62728' if x < 0 else '#2ca02c' for x in returns]
    fig.add_trace(
        go.Bar(x=returns.index, y=returns * 100, name='Daily Returns',
              marker_color=colors),
        row=2, col=1
    )
    
    # Volatility
    fig.add_trace(
        go.Scatter(x=vol.index, y=vol, mode='lines', name='Volatility',
                  line=dict(color='#9467bd', width=2), fill='tozeroy'),
        row=3, col=1
    )
    
    # Update layout
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Return (%)", row=2, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=3, col=1)
    
    fig.update_layout(
        height=900,
        template='plotly_dark',
        showlegend=True,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        trend_color = '#2ca02c' if trend == 'Uptrend' else ('#d62728' if trend == 'Downtrend' else '#ff7f0e')
        st.markdown(f"**Trend:** <span style='color:{trend_color}; font-weight:bold'>{trend}</span>", unsafe_allow_html=True)
    
    with col2:
        st.metric("Trend Slope", f"{slope:.4f}")
    
    with col3:
        current_vol = vol.iloc[-1] if not pd.isna(vol.iloc[-1]) else 0
        st.metric("Current Volatility", f"{current_vol:.2f}%")

# ============================================================================
# Tab 4: Statistics
# ============================================================================
with tab4:
    st.header("Statistical Analysis")
    
    st.markdown("""
    Comprehensive statistical metrics for all analyzed stocks.
    """)
    
    # Calculate statistics
    stats_results = []
    
    for ticker, data in stock_data.items():
        prices = data['Close']
        returns = prices.pct_change().dropna()
        
        # Calculate metrics
        total_return = ((prices.iloc[-1] / prices.iloc[0]) - 1) * 100
        annualized_return = ((1 + total_return/100) ** (252 / len(returns))) - 1
        annualized_return = annualized_return * 100 if not np.isnan(annualized_return) else 0
        
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative / running_max - 1) * 100
        max_drawdown = drawdown.min()
        
        # Skewness and kurtosis
        skewness = stats.skew(returns.dropna())
        kurtosis_val = stats.kurtosis(returns.dropna())
        
        stats_results.append({
            'Ticker': ticker,
            'Total Return': total_return,
            'Ann. Return': annualized_return,
            'Volatility': volatility,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown': max_drawdown,
            'Skewness': skewness,
            'Kurtosis': kurtosis_val
        })
    
    stats_df = pd.DataFrame(stats_results)
    
    # Display statistics table
    st.subheader("Performance Statistics")
    
    styled_stats_df = stats_df.copy()
    styled_stats_df['Total Return'] = styled_stats_df['Total Return'].apply(lambda x: f"{x:.2f}%")
    styled_stats_df['Ann. Return'] = styled_stats_df['Ann. Return'].apply(lambda x: f"{x:.2f}%")
    styled_stats_df['Volatility'] = styled_stats_df['Volatility'].apply(lambda x: f"{x:.2f}%")
    styled_stats_df['Sharpe Ratio'] = styled_stats_df['Sharpe Ratio'].apply(lambda x: f"{x:.2f}")
    styled_stats_df['Max Drawdown'] = styled_stats_df['Max Drawdown'].apply(lambda x: f"{x:.2f}%")
    styled_stats_df['Skewness'] = styled_stats_df['Skewness'].apply(lambda x: f"{x:.2f}")
    styled_stats_df['Kurtosis'] = styled_stats_df['Kurtosis'].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(styled_stats_df, use_container_width=True, height=400)
    
    # Risk-Return scatter
    st.subheader("Risk-Return Profile")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=stats_df['Volatility'],
        y=stats_df['Ann. Return'],
        mode='markers+text',
        text=stats_df['Ticker'],
        textposition='top center',
        marker=dict(
            size=stats_df['Sharpe Ratio'].abs() * 20 + 10,
            color=stats_df['Sharpe Ratio'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Sharpe Ratio"),
            line=dict(width=1, color='white')
        ),
        hovertemplate=(
            '<b>%{text}</b><br>' +
            'Volatility: %{x:.2f}%<br>' +
            'Return: %{y:.2f}%<br>' +
            '<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title="Risk-Return Scatter (Bubble Size = Sharpe Ratio)",
        xaxis_title="Annualized Volatility (%)",
        yaxis_title="Annualized Return (%)",
        template='plotly_dark',
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Distribution analysis
    st.subheader("Return Distribution Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Skewness interpretation
        st.markdown("**Skewness Analysis:**")
        for _, row in stats_df.iterrows():
            skew_val = row['Skewness']
            if skew_val > 0.5:
                interpretation = "Positive (more extreme gains)"
            elif skew_val < -0.5:
                interpretation = "Negative (more extreme losses)"
            else:
                interpretation = "Symmetric"
            st.write(f"• **{row['Ticker']}**: {skew_val:.2f} - {interpretation}")
    
    with col2:
        # Kurtosis interpretation
        st.markdown("**Kurtosis Analysis:**")
        for _, row in stats_df.iterrows():
            kurt_val = row['Kurtosis']
            if kurt_val > 3:
                interpretation="Fat tails (higher extreme risk)"
            elif kurt_val < -1:
                interpretation = "Thin tails (lower extreme risk)"
            else:
                interpretation = "Normal-like"
            st.write(f"• **{row['Ticker']}**: {kurt_val:.2f} - {interpretation}")
