"""
 Advanced Analytics Dashboard

Performance profiling, stress testing, and correlation analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Advanced Analytics",
    page_icon="",
    layout="wide",
)

st.title("Advanced Analytics")
st.markdown("Performance profiling, stress testing, and correlation analysis")

# Tabs for different analytics
tab1, tab2, tab3, tab4 = st.tabs([
    " Performance Profiling",
    " Stress Testing",
    " Correlation Analysis",
    " Tail Risk"
])

# ============================================================================
# Tab 1: Performance Profiling
# ============================================================================
with tab1:
    st.header("Performance Profiling")
    
    try:
        from quantlib_pro.observability.profiler import get_profiler, print_bottlenecks
        
        profiler = get_profiler()
        
        # Generate report
        report_df = profiler.generate_report()
        
        if not report_df.empty:
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_time = report_df['total_time'].sum()
                st.metric("Total Time", f"{total_time:.2f}s")
            
            with col2:
                total_calls = report_df['count'].sum()
                st.metric("Total Calls", f"{int(total_calls):,}")
            
            with col3:
                avg_time = report_df['mean_time'].mean()
                st.metric("Avg Time/Call", f"{avg_time*1000:.2f}ms")
            
            with col4:
                slowest_func = report_df.loc[report_df['total_time'].idxmax(), 'function']
                st.metric("Slowest Function", slowest_func)
            
            # Performance table
            st.subheader("Function Performance")
            
            display_df = report_df.copy()
            display_df['total_time'] = display_df['total_time'].apply(lambda x: f"{x:.3f}s")
            display_df['mean_time'] = display_df['mean_time'].apply(lambda x: f"{x*1000:.2f}ms")
            display_df['median_time'] = display_df['median_time'].apply(lambda x: f"{x*1000:.2f}ms")
            display_df['p95_time'] = display_df['p95_time'].apply(lambda x: f"{x*1000:.2f}ms")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )
            
            # Visualization: Bottlenecks
            st.subheader("Performance Bottlenecks")
            
            bottlenecks_df = profiler.generate_report().nlargest(10, 'total_time')
            
            if not bottlenecks_df.empty:
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=bottlenecks_df['total_time'],
                    y=bottlenecks_df['function'],
                    orientation='h',
                    marker=dict(
                        color=bottlenecks_df['total_time'],
                        colorscale='Reds',
                    ),
                    text=bottlenecks_df['total_time'].apply(lambda x: f"{x:.2f}s"),
                    textposition='auto',
                ))
                
                fig.update_layout(
                    title="Top 10 Slowest Functions (Total Time)",
                    xaxis_title="Total Time (seconds)",
                    yaxis_title="Function",
                    height=400,
                    template='plotly_dark',
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Call distribution
                fig2 = go.Figure()
                
                fig2.add_trace(go.Bar(
                    x=bottlenecks_df['count'],
                    y=bottlenecks_df['function'],
                    orientation='h',
                    marker=dict(color='#1f77b4'),
                    text=bottlenecks_df['count'].apply(lambda x: f"{int(x):,}"),
                    textposition='auto',
                ))
                
                fig2.update_layout(
                    title="Function Call Counts",
                    xaxis_title="Number of Calls",
                    yaxis_title="Function",
                    height=400,
                    template='plotly_dark',
                )
                
                st.plotly_chart(fig2, use_container_width=True)
        
        else:
            st.info("No profiling data available. Run some operations to collect performance data.")
    
    except Exception as e:
        st.error(f"Error loading profiler: {e}")

# ============================================================================
# Tab 2: Stress Testing
# ============================================================================
with tab2:
    st.header("Stress Testing")
    
    # Sidebar controls
    with st.sidebar:
        st.subheader("Stress Test Configuration")
        
        test_type = st.selectbox(
            "Test Type",
            ["Monte Carlo", "Historical Scenario", "Hypothetical Scenario"]
        )
        
        if test_type == "Monte Carlo":
            n_scenarios = st.slider("Number of Scenarios", 1000, 50000, 10000, 1000)
            stress_level = st.slider("Stress Level (σ)", 1.0, 5.0, 2.0, 0.5)
            correlation_breakdown = st.checkbox("Simulate Correlation Breakdown", value=True)
        
        elif test_type == "Historical Scenario":
            scenario_name = st.selectbox(
                "Historical Scenario",
                ["2008 Financial Crisis", "2020 COVID Crash", "2022 Rate Hikes", "Custom"]
            )
            
            if scenario_name == "Custom":
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
        
        else:  # Hypothetical
            st.markdown("**Market Shocks**")
            equity_shock = st.slider("Equity Shock (%)", -50, 50, -20, 5)
            bond_shock = st.slider("Bond Shock (%)", -30, 30, 10, 5)
            vol_multiplier = st.slider("Volatility Multiplier", 1.0, 5.0, 2.0, 0.5)
    
    # Generate sample stress test results
    st.subheader("Stress Test Results")
    
    # Simulate results
    np.random.seed(42)
    n_sim = 1000
    
    # Portfolio returns under stress
    if test_type == "Monte Carlo":
        stress_returns = np.random.normal(-0.02 * stress_level, 0.05 * stress_level, n_sim)
    elif test_type == "Historical Scenario":
        stress_returns = np.random.normal(-0.15, 0.08, n_sim)
    else:
        stress_returns = np.random.normal(equity_shock/100, 0.06, n_sim)
    
    # Metrics
    portfolio_loss = np.min(stress_returns)
    var_95 = np.percentile(stress_returns, 5)
    cvar_95 = stress_returns[stress_returns <= var_95].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Worst Loss", f"{portfolio_loss:.2%}")
    
    with col2:
        st.metric("VaR (95%)", f"{var_95:.2%}")
    
    with col3:
        st.metric("CVaR (95%)", f"{cvar_95:.2%}")
    
    with col4:
        st.metric("Max Drawdown", f"{portfolio_loss:.2%}")
    
    # Distribution chart
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=stress_returns * 100,
        nbinsx=50,
        name="Scenario Returns",
        marker=dict(color='#1f77b4'),
    ))
    
    # Add VaR line
    fig.add_vline(
        x=var_95 * 100,
        line_dash="dash",
        line_color="red",
        annotation_text=f"VaR 95%: {var_95:.2%}",
    )
    
    # Add CVaR line
    fig.add_vline(
        x=cvar_95 * 100,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"CVaR 95%: {cvar_95:.2%}",
    )
    
    fig.update_layout(
        title="Stress Test Return Distribution",
        xaxis_title="Portfolio Return (%)",
        yaxis_title="Frequency",
        template='plotly_dark',
        height=400,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Asset contributions
    st.subheader("Asset Risk Contributions")
    
    # Sample asset contributions
    assets = ['Equities', 'Bonds', 'Real Estate', 'Commodities', 'Cash']
    contributions = np.random.dirichlet(np.ones(5)) * portfolio_loss
    
    contrib_df = pd.DataFrame({
        'Asset': assets,
        'Contribution': contributions,
    }).sort_values('Contribution')
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=contrib_df['Contribution'] * 100,
        y=contrib_df['Asset'],
        orientation='h',
        marker=dict(
            color=contrib_df['Contribution'],
            colorscale='RdYlGn_r',
        ),
        text=contrib_df['Contribution'].apply(lambda x: f"{x:.2%}"),
        textposition='auto',
    ))
    
    fig2.update_layout(
        title="Risk Contribution by Asset Class",
        xaxis_title="Contribution to Portfolio Loss (%)",
        yaxis_title="Asset Class",
        template='plotly_dark',
        height=300,
    )
    
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================================
# Tab 3: Correlation Analysis
# ============================================================================
with tab3:
    st.header("Correlation Analysis")
    
    # Generate sample correlation data
    np.random.seed(42)
    n_assets = 10
    assets = [f"Asset_{i+1}" for i in range(n_assets)]
    
    # Generate correlation matrix
    random_corr = np.random.rand(n_assets, n_assets)
    corr_matrix = (random_corr + random_corr.T) / 2
    np.fill_diagonal(corr_matrix, 1.0)
    
    # Ensure valid correlation matrix
    eigenvalues = np.linalg.eigvalsh(corr_matrix)
    if np.min(eigenvalues) < 0:
        corr_matrix = corr_matrix + np.eye(n_assets) * abs(np.min(eigenvalues)) * 1.1
        corr_matrix = corr_matrix / np.outer(np.sqrt(np.diag(corr_matrix)), np.sqrt(np.diag(corr_matrix)))
    
    corr_df = pd.DataFrame(corr_matrix, index=assets, columns=assets)
    
    # Correlation heatmap
    st.subheader("Correlation Matrix")
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns,
        y=corr_df.index,
        colorscale='RdBu_r',
        zmid=0,
        text=corr_df.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlation"),
    ))
    
    fig.update_layout(
        title="Asset Correlation Heatmap",
        height=600,
        template='plotly_dark',
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Rolling correlation
    st.subheader("Rolling Correlation Over Time")
    
    # Generate time series
    n_periods = 252
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n_periods, freq='D')
    
    # Simulate rolling correlation
    base_corr = 0.5
    corr_volatility = 0.2
    rolling_corr = base_corr + np.random.randn(n_periods) * corr_volatility
    rolling_corr = np.clip(rolling_corr, -1, 1)
    
    # Add regime changes
    rolling_corr[100:150] = rolling_corr[100:150] + 0.3  # High correlation regime
    rolling_corr = np.clip(rolling_corr, -1, 1)
    
    rolling_df = pd.DataFrame({
        'Date': dates,
        'Correlation': rolling_corr,
    })
    
    # Calculate average
    avg_corr = rolling_corr.mean()
    
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
        annotation_text=f"Average: {avg_corr:.2f}",
    )
    
    # Highlight high correlation regime
    fig2.add_vrect(
        x0=dates[100],
        x1=dates[150],
        fillcolor="red",
        opacity=0.2,
        annotation_text="High Correlation Regime",
        annotation_position="top left",
    )
    
    fig2.update_layout(
        title="Average Pairwise Correlation (60-day rolling)",
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
    upper_tri = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
    
    with col1:
        st.metric("Mean Correlation", f"{upper_tri.mean():.3f}")
    
    with col2:
        st.metric("Median Correlation", f"{np.median(upper_tri):.3f}")
    
    with col3:
        st.metric("Max Correlation", f"{upper_tri.max():.3f}")
    
    with col4:
        st.metric("Min Correlation", f"{upper_tri.min():.3f}")

# ============================================================================
# Tab 4: Tail Risk
# ============================================================================
with tab4:
    st.header("Tail Risk Analysis")
    
    st.markdown("""
    Extreme Value Theory (EVT) analysis for tail risk assessment.
    """)
    
    # Generate sample returns
    np.random.seed(42)
    n_samples = 1000
    
    # Normal returns with fat tails
    returns = np.concatenate([
        np.random.standard_t(df=3, size=int(n_samples * 0.9)),
        np.random.standard_t(df=2, size=int(n_samples * 0.1)),
    ])
    returns = returns / 10  # Scale
    
    # Calculate tail metrics
    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)
    cvar_95 = returns[returns <= var_95].mean()
    cvar_99 = returns[returns <= var_99].mean()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("VaR 95%", f"{var_95:.2%}")
    
    with col2:
        st.metric("VaR 99%", f"{var_99:.2%}")
    
    with col3:
        st.metric("CVaR 95%", f"{cvar_95:.2%}")
    
    with col4:
        st.metric("CVaR 99%", f"{cvar_99:.2%}")
    
    # Return distribution with tail highlights
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=returns * 100,
        nbinsx=100,
        name="Returns",
        marker=dict(color='#1f77b4'),
    ))
    
    # Add VaR lines
    fig.add_vline(
        x=var_95 * 100,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"VaR 95%",
    )
    
    fig.add_vline(
        x=var_99 * 100,
        line_dash="dash",
        line_color="red",
        annotation_text=f"VaR 99%",
    )
    
    fig.update_layout(
        title="Return Distribution with Tail Risk Measures",
        xaxis_title="Return (%)",
        yaxis_title="Frequency",
        template='plotly_dark',
        height=400,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Q-Q plot
    st.subheader("Q-Q Plot (Normal Distribution)")
    
    from scipy import stats as sp_stats
    
    # Generate Q-Q data
    sorted_returns = np.sort(returns)
    theoretical_quantiles = sp_stats.norm.ppf(np.linspace(0.01, 0.99, len(sorted_returns)))
    
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
        y=theoretical_quantiles * returns.std() + returns.mean(),
        mode='lines',
        name='Normal Reference',
        line=dict(color='red', dash='dash'),
    ))
    
    fig2.update_layout(
        title="Q-Q Plot: Actual vs Normal Distribution",
        xaxis_title="Theoretical Quantiles",
        yaxis_title="Sample Quantiles",
        template='plotly_dark',
        height=400,
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Tail statistics
    st.subheader("Tail Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Left Tail (Losses)**")
        left_tail = returns[returns < var_95]
        st.metric("Mean Tail Loss", f"{left_tail.mean():.2%}")
        st.metric("Worst Loss", f"{returns.min():.2%}")
        st.metric("Tail Observations", f"{len(left_tail)} ({len(left_tail)/len(returns):.1%})")
    
    with col2:
        st.markdown("**Right Tail (Gains)**")
        var_95_right = np.percentile(returns, 95)
        right_tail = returns[returns > var_95_right]
        st.metric("Mean Tail Gain", f"{right_tail.mean():.2%}")
        st.metric("Best Gain", f"{returns.max():.2%}")
        st.metric("Tail Observations", f"{len(right_tail)} ({len(right_tail)/len(returns):.1%})")
