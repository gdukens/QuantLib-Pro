"""
📊 Advanced Analytics Dashboard

Performance profiling, stress testing, correlation analysis, and tail risk analysis
with real portfolio data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from scipy import stats

# Page config
st.set_page_config(
    page_title="Advanced Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Advanced Analytics")
st.markdown("Advanced portfolio analytics with real-time data: stress testing, correlation dynamics, and tail risk assessment")

# ============================================================================
# Sidebar: Portfolio Configuration
# ============================================================================
with st.sidebar:
    st.header("⚙️ Portfolio Configuration")
    
    # Portfolio tickers input
    st.subheader("Assets")
    portfolio_input = st.text_area(
        "Enter tickers (one per line)",
        value="AAPL\nMSFT\nGOOG\nAMZN\nTSLA",
        height=120,
        help="Enter stock tickers, ETFs, or indices separated by new lines"
    )
    
    tickers = [t.strip().upper() for t in portfolio_input.split('\n') if t.strip()]
    
    # Weights input (optional)
    use_custom_weights = st.checkbox("Custom Weights", value=False)
    
    if use_custom_weights:
        weights_input = st.text_area(
            "Enter weights (one per line, must sum to 100%)",
            value="\n".join([f"{100/len(tickers):.1f}" for _ in tickers]),
            height=120,
            help="Enter weights as percentages (e.g., 25.0 for 25%)"
        )
        
        try:
            weights = [float(w.strip()) for w in weights_input.split('\n') if w.strip()]
            if len(weights) != len(tickers):
                st.error(f"Expected {len(tickers)} weights, got {len(weights)}")
                weights = [100/len(tickers)] * len(tickers)
            elif abs(sum(weights) - 100) > 0.1:
                st.warning(f"Weights sum to {sum(weights):.1f}%, normalizing to 100%")
                weights = [w / sum(weights) * 100 for w in weights]
            weights = [w / 100 for w in weights]  # Convert to decimal
        except ValueError:
            st.error("Invalid weight format. Using equal weights.")
            weights = [1/len(tickers)] * len(tickers)
    else:
        weights = [1/len(tickers)] * len(tickers)
    
    # Benchmark selection
    st.subheader("Benchmark")
    benchmark = st.selectbox(
        "Select benchmark",
        ["^GSPC", "^DJI", "^IXIC", "^RUT", "SPY", "QQQ"],
        index=0,
        help="Benchmark index for comparison"
    )
    
    # Date range
    st.subheader("Analysis Period")
    
    period_option = st.selectbox(
        "Time Period",
        ["1 Year", "2 Years", "3 Years", "5 Years", "Custom"],
        index=1
    )
    
    if period_option == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=730)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now()
            )
    else:
        period_map = {"1 Year": 365, "2 Years": 730, "3 Years": 1095, "5 Years": 1825}
        days = period_map[period_option]
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
    
    # Analysis parameters
    st.subheader("Analysis Parameters")
    
    correlation_window = st.slider(
        "Correlation Window (days)",
        min_value=20,
        max_value=252,
        value=60,
        step=10,
        help="Rolling window for correlation calculation"
    )
    
    confidence_level = st.selectbox(
        "VaR Confidence Level",
        [90, 95, 99],
        index=1,
        help="Confidence level for Value at Risk calculations"
    )

# ============================================================================
# Data Fetching Functions
# ============================================================================

@st.cache_data(ttl=3600)
def fetch_portfolio_data(tickers, start_date, end_date):
    """Fetch historical data for portfolio tickers"""
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
                
                # If data index is timezone-aware, make our timestamps timezone-aware too
                if data.index.tz is not None:
                    if start_ts.tz is None:
                        start_ts = start_ts.tz_localize('UTC').tz_convert(data.index.tz)
                    if end_ts.tz is None:
                        end_ts = end_ts.tz_localize('UTC').tz_convert(data.index.tz)
                
                # Filter by date range
                data = data[(data.index >= start_ts) & (data.index <= end_ts)]
                all_data[ticker] = data['Close']
        except Exception as e:
            st.warning(f"Could not fetch data for {ticker}: {str(e)}")
    
    if not all_data:
        return None
    
    # Combine into DataFrame
    df = pd.DataFrame(all_data)
    return df.dropna()

@st.cache_data(ttl=3600)
def calculate_portfolio_metrics(prices_df, weights):
    """Calculate portfolio returns and various metrics"""
    # Calculate returns
    returns = prices_df.pct_change().dropna()
    
    # Portfolio returns
    portfolio_returns = (returns * weights).sum(axis=1)
    
    # Cumulative returns
    cumulative_returns = (1 + portfolio_returns).cumprod()
    
    return returns, portfolio_returns, cumulative_returns

# Fetch data
try:
    with st.spinner("Fetching portfolio data..."):
        prices_df = fetch_portfolio_data(tickers, start_date, end_date)
        
        if prices_df is None or prices_df.empty:
            st.error("Could not fetch portfolio data. Please check your tickers and try again.")
            st.stop()
        
        returns_df, portfolio_returns, cumulative_returns = calculate_portfolio_metrics(prices_df, weights)
        
        # Show portfolio summary in sidebar
        with st.sidebar:
            st.success(f"✅ Loaded {len(prices_df)} days of data")
            st.write(f"**Portfolio:** {len(tickers)} assets")
            
            total_return = (cumulative_returns.iloc[-1] - 1) * 100
            annualized_return = ((cumulative_returns.iloc[-1] ** (252 / len(portfolio_returns))) - 1) * 100
            volatility = portfolio_returns.std() * np.sqrt(252) * 100
            sharpe = annualized_return / volatility if volatility > 0 else 0
            
            st.metric("Total Return", f"{total_return:.2f}%")
            st.metric("Annualized Return", f"{annualized_return:.2f}%")
            st.metric("Volatility (Ann.)", f"{volatility:.2f}%")
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")

except Exception as e:
    st.error(f"Error loading portfolio data: {str(e)}")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Performance Profiling",
    "⚡ Stress Testing",
    "🔗 Correlation Analysis",
    "📉 Tail Risk"
])

# ============================================================================
# Tab 1: Performance Profiling
# ============================================================================
with tab1:
    st.header("Performance Profiling")
    
    st.markdown("""
    System performance metrics and bottleneck analysis for QuantLib Pro operations.
    """)
    
    try:
        from quantlib_pro.observability.profiler import get_profiler
        
        profiler = get_profiler()
        
        if profiler and profiler.measurements:
            # Generate performance report
            report_df = profiler.generate_report()
            
            if not report_df.empty:
                # Calculate overview metrics
                col1, col2, col3, col4 = st.columns(4)
                
                # Convert Total (ms) from string to float for calculations
                total_times = report_df['Total (ms)'].apply(lambda x: float(x.replace(',', '')) if isinstance(x, str) else x)
                counts = report_df['Count']
                
                total_time = total_times.sum() / 1000  # Convert to seconds
                total_calls = counts.sum()
                avg_time = total_time / total_calls if total_calls > 0 else 0
                slowest_func = report_df.iloc[0]['Function'] if len(report_df) > 0 else None
                
                with col1:
                    st.metric("Total Execution Time", f"{total_time:.2f}s")
                
                with col2:
                    st.metric("Total Function Calls", f"{total_calls:,}")
                
                with col3:
                    st.metric("Average Time per Call", f"{avg_time*1000:.2f}ms")
                
                with col4:
                    if slowest_func:
                        st.metric("Slowest Function", slowest_func)
                
                # Performance table
                st.subheader("Function Performance Metrics")
                
                st.dataframe(report_df, use_container_width=True, height=400)
                
                # Bottlenecks visualization
                st.subheader("Performance Bottlenecks")
                
                # Top 10 slowest functions by total time
                top_n = min(10, len(report_df))
                top_funcs = report_df.head(top_n).copy()
                
                # Convert Total (ms) to numeric for plotting
                top_funcs['Total_Time_Numeric'] = top_funcs['Total (ms)'].apply(
                    lambda x: float(x.replace(',', '')) if isinstance(x, str) else x
                ) / 1000  # Convert to seconds
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=top_funcs["Function"],
                        y=top_funcs["Total_Time_Numeric"],
                        marker_color='#ff7f0e',
                        text=top_funcs["Total_Time_Numeric"].round(3),
                        textposition='outside',
                    )
                ])
                
                fig.update_layout(
                    title=f"Top {top_n} Slowest Functions",
                    xaxis_title="Function",
                    yaxis_title="Total Time (s)",
                    template='plotly_dark',
                    height=400,
                    xaxis={'tickangle': -45}
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Call distribution
                st.subheader("Call Distribution")
                
                fig2 = go.Figure(data=[
                    go.Bar(
                        x=top_funcs["Function"],
                        y=top_funcs["Count"],
                        marker_color='#1f77b4',
                        text=top_funcs["Count"],
                        textposition='outside',
                    )
                ])
                
                fig2.update_layout(
                    title=f"Top {top_n} Most Called Functions",
                    xaxis_title="Function",
                    yaxis_title="Number of Calls",
                    template='plotly_dark',
                    height=400,
                    xaxis={'tickangle': -45}
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No profiling data available. Run some operations to generate profiling metrics.")
        
        else:
            st.info("📊 No profiling data available yet.")
            
            st.markdown("""
            ### How to Generate Profiling Data
            
            The profiler tracks execution time and performance of QuantLib Pro operations. To see metrics here:
            
            1. **Navigate to other dashboards** and perform calculations:
               - 📈 **Portfolio**: Load portfolio data and view metrics
               - ⚠️ **Risk**: Calculate VaR, CVaR, and run stress tests
               - 📊 **Options**: Price options using Black-Scholes or Monte Carlo
               - 🎯 **Market Regime**: Detect market regimes and volatility clusters
               - 🌊 **Volatility Surface**: Generate volatility surfaces
               - 📊 **Backtesting**: Run strategy backtests
            
            2. **Return to this page** to view performance metrics
            
            3. **Analyze bottlenecks** to identify slow operations and optimization opportunities
            
            ---
            
            **What you'll see:**
            - Function execution times (total, mean, min, max)
            - Call counts and distribution
            - Performance bottlenecks visualization
            - Statistical metrics (P95, P99 percentiles)
            """)
    
    except ImportError:
        st.warning("⚠️ Profiler module not available. Performance tracking is disabled.")

# ============================================================================
# Tab 2: Stress Testing
# ============================================================================
with tab2:
    st.header("Stress Testing")
    
    st.markdown("""
    Test portfolio resilience under extreme market scenarios using real historical data.
    """)
    
    # Sidebar configuration for stress tests
    with st.sidebar:
        st.markdown("---")
        st.subheader("Stress Test Configuration")
        
        test_type = st.selectbox(
            "Test Type",
            ["Monte Carlo", "Historical Scenario", "Hypothetical Scenario"],
            help="Type of stress test to run"
        )
        
        if test_type == "Monte Carlo":
            n_scenarios = st.slider("Number of Scenarios", 1000, 50000, 10000, 1000)
            stress_level = st.slider("Stress Level (σ)", 1.0, 5.0, 2.0, 0.5,
                                    help="Standard deviations from mean")
        
        elif test_type == "Historical Scenario":
            scenario_name = st.selectbox(
                "Select Scenario",
                ["2008 Financial Crisis", "2020 COVID Crash", "2022 Rate Hikes", "Custom Date Range"]
            )
            
            if scenario_name == "Custom Date Range":
                stress_start = st.date_input("Scenario Start", value=datetime(2020, 2, 1))
                stress_end = st.date_input("Scenario End", value=datetime(2020, 3, 23))
            else:
                # Predefined scenarios
                scenarios = {
                    "2008 Financial Crisis": (datetime(2008, 9, 1), datetime(2009, 3, 9)),
                    "2020 COVID Crash": (datetime(2020, 2, 19), datetime(2020, 3, 23)),
                    "2022 Rate Hikes": (datetime(2022, 1, 1), datetime(2022, 10, 13))
                }
                stress_start, stress_end = scenarios[scenario_name]
        
        else:  # Hypothetical Scenario
            equity_shock = st.slider("Equity Shock (%)", -50, 50, -20, 5)
            vol_multiplier = st.slider("Volatility Multiplier", 1.0, 5.0, 2.0, 0.5)
    
    # Run stress test
    if test_type == "Monte Carlo":
        st.subheader("Monte Carlo Stress Test")
        
        # Calculate portfolio statistics
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        
        # Generate stressed scenarios
        np.random.seed(None)  # Use real random seed
        stress_returns = np.random.normal(
            loc=mean_return - stress_level * std_return,
            scale=std_return * stress_level,
            size=n_scenarios
        )
        
        # Calculate metrics
        portfolio_loss = stress_returns.min()
        var_level = (100 - confidence_level) / 100
        var = np.percentile(stress_returns, var_level * 100)
        cvar = stress_returns[stress_returns <= var].mean()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Worst Case Loss", f"{portfolio_loss*100:.2f}%",
                     delta=f"{(portfolio_loss - mean_return)*100:.2f}%",
                     delta_color="inverse")
        with col2:
            st.metric(f"VaR {confidence_level}%", f"{var*100:.2f}%")
        with col3:
            st.metric(f"CVaR {confidence_level}%", f"{cvar*100:.2f}%")
        with col4:
            prob_large_loss = (stress_returns < -0.10).sum() / n_scenarios * 100
            st.metric("Prob(Loss > 10%)", f"{prob_large_loss:.1f}%")
        
        # Distribution plot
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=stress_returns * 100,
            nbinsx=50,
            name="Stress Returns",
            marker=dict(color='#1f77b4'),
            opacity=0.7
        ))
        
        # Add VaR and CVaR lines
        fig.add_vline(x=var * 100, line_dash="dash", line_color="orange",
                     annotation_text=f"VaR {confidence_level}%")
        fig.add_vline(x=cvar * 100, line_dash="dash", line_color="red",
                     annotation_text=f"CVaR {confidence_level}%")
        
        fig.update_layout(
            title=f"Monte Carlo Stress Test Distribution ({n_scenarios:,} scenarios)",
            xaxis_title="Portfolio Return (%)",
            yaxis_title="Frequency",
            template='plotly_dark',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif test_type == "Historical Scenario":
        st.subheader(f"Historical Scenario: {scenario_name if scenario_name != 'Custom Date Range' else 'Custom'}")
        
        # Fetch data for stress period
        try:
            stress_prices = fetch_portfolio_data(tickers, stress_start, stress_end)
            if stress_prices is not None and not stress_prices.empty:
                stress_returns_hist, stress_portfolio_returns, stress_cumulative = calculate_portfolio_metrics(
                    stress_prices, weights
                )
                
                # Calculate impact metrics
                total_scenario_return = (stress_cumulative.iloc[-1] - 1) * 100
                max_drawdown = ((stress_cumulative / stress_cumulative.cummax()) - 1).min() * 100
                scenario_vol = stress_portfolio_returns.std() * np.sqrt(252) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Scenario Return", f"{total_scenario_return:.2f}%",
                             delta_color="normal")
                with col2:
                    st.metric("Max Drawdown", f"{max_drawdown:.2f}%",
                             delta_color="inverse")
                with col3:
                    st.metric("Scenario Volatility", f"{scenario_vol:.2f}%")
                with col4:
                    worst_day = stress_portfolio_returns.min() * 100
                    st.metric("Worst Single Day", f"{worst_day:.2f}%")
                
                # Cumulative return chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=stress_cumulative.index,
                    y=(stress_cumulative - 1) * 100,
                    mode='lines',
                    name='Portfolio',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                fig.update_layout(
                    title=f"Portfolio Performance: {stress_start.strftime('%Y-%m-%d')} to {stress_end.strftime('%Y-%m-%d')}",
                    xaxis_title="Date",
                    yaxis_title="Cumulative Return (%)",
                    template='plotly_dark',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Daily returns distribution
                fig2 = go.Figure()
                
                fig2.add_trace(go.Histogram(
                    x=stress_portfolio_returns * 100,
                    nbinsx=30,
                    name="Daily Returns",
                    marker=dict(color='#ff7f0e'),
                    opacity=0.7
                ))
                
                fig2.update_layout(
                    title="Daily Returns Distribution During Stress Period",
                    xaxis_title="Daily Return (%)",
                    yaxis_title="Frequency",
                    template='plotly_dark',
                    height=400
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
            else:
                st.warning("Could not fetch data for the selected stress period.")
        
        except Exception as e:
            st.error(f"Error running historical scenario: {str(e)}")
    
    else:  # Hypothetical Scenario
        st.subheader("Hypothetical Scenario Analysis")
        
        # Apply hypothetical shock to current portfolio
        shocked_returns = portfolio_returns * vol_multiplier + (equity_shock / 100 / 252)
        
        # Calculate impact
        scenario_total_return = shocked_returns.sum() * 100
        scenario_vol = shocked_returns.std() * np.sqrt(252) * 100
        var = np.percentile(shocked_returns, (100 - confidence_level) / 100 * 100) * 100
        cvar = shocked_returns[shocked_returns <= np.percentile(shocked_returns, (100 - confidence_level) / 100 * 100)].mean() * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Hypothetical Return", f"{scenario_total_return:.2f}%")
        with col2:
            st.metric("Adjusted Volatility", f"{scenario_vol:.2f}%")
        with col3:
            st.metric(f"VaR {confidence_level}%", f"{var:.2f}%")
        with col4:
            st.metric(f"CVaR {confidence_level}%", f"{cvar:.2f}%")
        
        # Show impact distribution
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=shocked_returns * 100,
            nbinsx=50,
            name="Shocked Returns",
            marker=dict(color='#d62728'),
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Hypothetical Scenario Return Distribution",
            xaxis_title="Daily Return (%)",
            yaxis_title="Frequency", 
            template='plotly_dark',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Asset-level contributions
    st.subheader("Asset Risk Contributions")
    
    # Calculate individual asset volatilities
    asset_vols = returns_df.std() * np.sqrt(252) * 100
    asset_contributions = asset_vols * weights
    asset_contributions = asset_contributions / asset_contributions.sum() * 100
    
    # Create DataFrame
    contrib_df = pd.DataFrame({
        'Asset': tickers,
        'Weight (%)': [w * 100 for w in weights],
        'Volatility (%)': asset_vols.values,
        'Risk Contribution (%)': asset_contributions.values
    }).sort_values('Risk Contribution (%)', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(contrib_df, use_container_width=True, height=300)
    
    with col2:
        fig = go.Figure(data=[
            go.Bar(
                x=contrib_df['Asset'],
                y=contrib_df['Risk Contribution (%)'],
                marker_color='#2ca02c',
                text=contrib_df['Risk Contribution (%)'].round(1),
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Portfolio Risk Contributions by Asset",
            xaxis_title="Asset",
            yaxis_title="Risk Contribution (%)",
            template='plotly_dark',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# Tab 3: Correlation Analysis
# ============================================================================
with tab3:
    st.header("Correlation Analysis")
    
    st.markdown("""
    Dynamic correlation patterns and regime analysis using real portfolio data.
    """)
    
    # Calculate correlation matrix
    corr_matrix = returns_df.corr()
    
    # Correlation heatmap
    st.subheader("Asset Correlation Matrix")
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu_r',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlation"),
    ))
    
    fig.update_layout(
        title="Pairwise Asset Correlations",
        height=600,
        template='plotly_dark',
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Rolling correlation analysis
    st.subheader("Rolling Correlation Dynamics")
    
    # Calculate average pairwise correlation over time
    rolling_corrs = []
    dates = []
    
    for i in range(correlation_window, len(returns_df)):
        window_returns = returns_df.iloc[i-correlation_window:i]
        window_corr = window_returns.corr()
        
        # Get upper triangle (exclude diagonal)
        upper_tri = window_corr.values[np.triu_indices_from(window_corr.values, k=1)]
        avg_corr = upper_tri.mean()
        
        rolling_corrs.append(avg_corr)
        dates.append(returns_df.index[i])
    
    rolling_df = pd.DataFrame({
        'Date': dates,
        'Correlation': rolling_corrs
    })
    
    # Calculate average and std
    avg_corr = rolling_df['Correlation'].mean()
    std_corr = rolling_df['Correlation'].std()
    
    # Plot rolling correlation
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=rolling_df['Date'],
        y=rolling_df['Correlation'],
        mode='lines',
        name='Rolling Correlation',
        line=dict(color='#1f77b4', width=2),
    ))
    
    # Add average line
    fig2.add_hline(
        y=avg_corr,
        line_dash="dash",
        line_color="white",
        annotation_text=f"Average: {avg_corr:.3f}",
    )
    
    # Add high/low correlation bands
    fig2.add_hline(
        y=avg_corr + std_corr,
        line_dash="dot",
        line_color="red",
        annotation_text="High Correlation",
    )
    
    fig2.add_hline(
        y=avg_corr - std_corr,
        line_dash="dot",
        line_color="green",
        annotation_text="Low Correlation",
    )
    
    fig2.update_layout(
        title=f"Average Pairwise Correlation ({correlation_window}-day rolling window)",
        xaxis_title="Date",
        yaxis_title="Correlation",
        template='plotly_dark',
        height=400,
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Correlation statistics
    st.subheader("Correlation Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get upper triangle (exclude diagonal)
    upper_tri = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
    
    with col1:
        st.metric("Mean Correlation", f"{upper_tri.mean():.3f}")
    
    with col2:
        st.metric("Median Correlation", f"{np.median(upper_tri):.3f}")
    
    with col3:
        st.metric("Max Correlation", f"{upper_tri.max():.3f}")
    
    with col4:
        st.metric("Min Correlation", f"{upper_tri.min():.3f}")
    
    # Correlation regime detection
    st.subheader("Correlation Regime Analysis")
    
    # Identify high correlation periods (> avg + std)
    high_corr_threshold = avg_corr + std_corr
    low_corr_threshold = avg_corr - std_corr
    
    rolling_df['Regime'] = 'Normal'
    rolling_df.loc[rolling_df['Correlation'] > high_corr_threshold, 'Regime'] = 'High Correlation'
    rolling_df.loc[rolling_df['Correlation'] < low_corr_threshold, 'Regime'] = 'Low Correlation'
    
    regime_counts = rolling_df['Regime'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Regime Distribution:**")
        for regime, count in regime_counts.items():
            pct = count / len(rolling_df) * 100
            st.metric(regime, f"{count} days ({pct:.1f}%)")
    
    with col2:
        # Regime pie chart
        fig3 = go.Figure(data=[go.Pie(
            labels=regime_counts.index,
            values=regime_counts.values,
            marker=dict(colors=['#ff7f0e', '#1f77b4', '#2ca02c'])
        )])
        
        fig3.update_layout(
            title="Correlation Regime Distribution",
            template='plotly_dark',
            height=300
        )
        
        st.plotly_chart(fig3, use_container_width=True)

# ============================================================================
# Tab 4: Tail Risk
# ============================================================================
with tab4:
    st.header("Tail Risk Analysis")
    
    st.markdown("""
    Extreme Value Theory (EVT) and tail risk assessment using real portfolio returns.
    """)
    
    # Calculate tail metrics from real portfolio returns
    returns_pct = portfolio_returns.values
    
    var_95 = np.percentile(returns_pct, 5)
    var_99 = np.percentile(returns_pct, 1)
    cvar_95 = returns_pct[returns_pct <= var_95].mean()
    cvar_99 = returns_pct[returns_pct <= var_99].mean()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("VaR 95%", f"{var_95*100:.2f}%")
    
    with col2:
        st.metric("VaR 99%", f"{var_99*100:.2f}%")
    
    with col3:
        st.metric("CVaR 95%", f"{cvar_95*100:.2f}%")
    
    with col4:
        st.metric("CVaR 99%", f"{cvar_99*100:.2f}%")
    
    # Return distribution with tail highlights
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=returns_pct * 100,
        nbinsx=100,
        name="Returns",
        marker=dict(color='#1f77b4'),
    ))
    
    # Add VaR lines
    fig.add_vline(
        x=var_95 * 100,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"VaR 95%: {var_95*100:.2f}%",
    )
    
    fig.add_vline(
        x=var_99 * 100,
        line_dash="dash",
        line_color="red",
        annotation_text=f"VaR 99%: {var_99*100:.2f}%",
    )
    
    fig.update_layout(
        title="Portfolio Return Distribution with Tail Risk Measures",
        xaxis_title="Daily Return (%)",
        yaxis_title="Frequency",
        template='plotly_dark',
        height=400,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Q-Q plot
    st.subheader("Q-Q Plot (Normal Distribution)")
    
    # Generate Q-Q data
    sorted_returns = np.sort(returns_pct)
    theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(sorted_returns)))
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=theoretical_quantiles,
        y=sorted_returns,
        mode='markers',
        name='Q-Q Plot',
        marker=dict(size=3, color='#1f77b4'),
    ))
    
    # Add reference line
    fig2.add_trace(go.Scatter(
        x=theoretical_quantiles,
        y=theoretical_quantiles * returns_pct.std() + returns_pct.mean(),
        mode='lines',
        name='Normal Reference',
        line=dict(color='red', dash='dash'),
    ))
    
    fig2.update_layout(
        title="Q-Q Plot: Actual vs Normal Distribution",
        xaxis_title="Theoretical Quantiles (Normal)",
        yaxis_title="Sample Quantiles (Actual Returns)",
        template='plotly_dark',
        height=400,
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Tail statistics
    st.subheader("Tail Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Left Tail (Losses)**")
        left_tail = returns_pct[returns_pct < var_95]
        st.metric("Mean Tail Loss", f"{left_tail.mean()*100:.2f}%")
        st.metric("Worst Loss", f"{returns_pct.min()*100:.2f}%")
        st.metric("Tail Observations", f"{len(left_tail)} ({len(left_tail)/len(returns_pct)*100:.1f}%)")
        
        # Kurtosis and skewness
        from scipy.stats import kurtosis, skew
        kurt = kurtosis(returns_pct)
        skewness = skew(returns_pct)
        
        st.metric("Kurtosis (Excess)", f"{kurt:.2f}",
                 help="Excess kurtosis > 0 indicates fat tails")
        st.metric("Skewness", f"{skewness:.2f}",
                 help="Negative skewness indicates left tail risk")
    
    with col2:
        st.markdown("**Right Tail (Gains)**")
        var_95_right = np.percentile(returns_pct, 95)
        right_tail = returns_pct[returns_pct > var_95_right]
        st.metric("Mean Tail Gain", f"{right_tail.mean()*100:.2f}%")
        st.metric("Best Gain", f"{returns_pct.max()*100:.2f}%")
        st.metric("Tail Observations", f"{len(right_tail)} ({len(right_tail)/len(returns_pct)*100:.1f}%)")
        
        # Tail ratio
        tail_ratio = abs(right_tail.mean() / left_tail.mean()) if len(left_tail) > 0 else 0
        st.metric("Tail Ratio (Right/Left)", f"{tail_ratio:.2f}",
                 help="Ratio > 1 indicates asymmetric upside")
    
    # Drawdown analysis
    st.subheader("Historical Drawdown Analysis")
    
    # Calculate drawdown
    cumulative = (1 + portfolio_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative / running_max - 1) * 100
    
    # Plot drawdown over time
    fig3 = go.Figure()
    
    fig3.add_trace(go.Scatter(
        x=drawdown.index,
        y=drawdown,
        mode='lines',
        name='Drawdown',
        fill='tozeroy',
        line=dict(color='#d62728', width=1),
    ))
    
    fig3.update_layout(
        title="Portfolio Drawdown Over Time",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        template='plotly_dark',
        height=400,
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # Drawdown statistics
    max_dd = drawdown.min()
    avg_dd = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0
    
    # Find max drawdown period
    max_dd_idx = drawdown.idxmin()
    dd_start = running_max[:max_dd_idx].idxmax()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Max Drawdown", f"{max_dd:.2f}%")
    with col2:
        st.metric("Average Drawdown", f"{avg_dd:.2f}%")
    with col3:
        if max_dd_idx and dd_start:
            recovery_days = (max_dd_idx - dd_start).days
            st.metric("Max DD Duration", f"{recovery_days} days")
