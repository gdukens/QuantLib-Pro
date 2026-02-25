"""
Portfolio Optimization Dashboard

Week 12: Streamlit page for portfolio optimization and efficient frontier analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import List, Dict

from quantlib_pro.ui import components
from quantlib_pro.portfolio.optimizer import PortfolioOptimizer
from quantlib_pro.data.market_data import MarketDataProvider

# Page config
st.set_page_config(
    page_title="Portfolio Optimization - QuantLib Pro",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Portfolio Optimization")
st.markdown("Optimize portfolio allocations using mean-variance optimization and visualize the efficient frontier.")

# Initialize session state
if "portfolio_results" not in st.session_state:
    st.session_state.portfolio_results = None

# Sidebar controls
with st.sidebar:
    st.header("Configuration")
    
    # Ticker selection
    st.subheader("Assets")
    ticker_input = st.text_area(
        "Enter tickers (one per line)",
        value="AAPL\nMSFT\nGOOG\nAMZN\nTSLA",
        height=150,
        help="Enter stock tickers separated by newlines",
    )
    tickers = [t.strip().upper() for t in ticker_input.split("\n") if t.strip()]
    
    st.markdown(f"**{len(tickers)} assets selected**")
    
    # Date range
    st.subheader("Date Range")
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    start_date = st.date_input(
        "Start Date",
        value=st.session_state.get("start_date", default_start),
    )
    end_date = st.date_input(
        "End Date",
        value=st.session_state.get("end_date", default_end),
    )
    
    # Optimization parameters
    st.subheader("Parameters")
    
    risk_free_rate = st.slider(
        "Risk-free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.get("risk_free_rate", 0.02) * 100,
        step=0.1,
    ) / 100
    
    target_return = st.slider(
        "Target Return (% annual)",
        min_value=0.0,
        max_value=50.0,
        value=15.0,
        step=1.0,
    ) / 100
    
    num_frontier_points = st.slider(
        "Frontier Points",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="Number of portfolios to calculate for efficient frontier",
    )
    
    allow_short = st.checkbox(
        "Allow Short Selling",
        value=False,
        help="Allow negative weights (short positions)",
    )
    
    # Run optimization
    optimize_button = st.button("🚀 Optimize Portfolio", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Efficient Frontier",
    "💼 Optimal Weights",
    "📈 Performance",
    "🌊 Dynamic Frontier",
    "💰 Wealth Simulator",
    "🎯 Diversification Analysis",
    "🧠 Monte Carlo Optimizer"
])

with tab1:
    st.header("Efficient Frontier")
    
    if optimize_button:
        with st.spinner("Fetching market data and optimizing..."):
            try:
                # Fetch real market data
                data_provider = MarketDataProvider()
                
                returns_data = {}
                
                for ticker in tickers:
                    try:
                        # Fetch historical data from real data sources
                        df = data_provider.get_stock_data(
                            ticker=ticker,
                            start_date=start_date.strftime('%Y-%m-%d'),
                            end_date=end_date.strftime('%Y-%m-%d')
                        )
                        
                        if df.empty:
                            st.error(f"No data available for {ticker}. Please check the ticker symbol.")
                            st.stop()
                        
                        # Calculate returns
                        daily_returns = df['Close'].pct_change().dropna()
                        returns_data[ticker] = daily_returns.values
                        
                    except Exception as e:
                        st.error(f"Failed to fetch data for {ticker}: {str(e)}")
                        st.stop()
                
                # Create returns DataFrame with aligned indices
                min_length = min(len(r) for r in returns_data.values())
                returns_df = pd.DataFrame({
                    ticker: returns_data[ticker][:min_length] for ticker in tickers
                })
                
                # Calculate expected returns and covariance matrix
                expected_returns = returns_df.mean() * 252  # Annualized
                cov_matrix = returns_df.cov() * 252  # Annualized
                
                # Calculate efficient frontier
                optimizer = PortfolioOptimizer(
                    expected_returns=expected_returns,
                    cov_matrix=cov_matrix,
                    risk_free_rate=risk_free_rate,
                    tickers=tickers
                )
                
                # Generate frontier points
                min_return = expected_returns.min()
                max_return = expected_returns.max()
                target_returns = np.linspace(min_return, max_return, num_frontier_points)
                
                frontier_volatilities = []
                frontier_returns = []
                frontier_sharpe = []
                frontier_weights = []
                
                for target_ret in target_returns:
                    try:
                        result = optimizer.target_return(
                            target_return=target_ret,
                            allow_short=allow_short,
                        )
                        
                        frontier_returns.append(result.expected_return)
                        frontier_volatilities.append(result.volatility)
                        frontier_sharpe.append(result.sharpe_ratio)
                        frontier_weights.append(result.weights)
                    except:
                        continue
                
                # Find optimal portfolio (max Sharpe)
                optimal_idx = np.argmax(frontier_sharpe)
                
                # Store results
                st.session_state.portfolio_results = {
                    "returns": np.array(frontier_returns),
                    "volatilities": np.array(frontier_volatilities),
                    "sharpe_ratios": np.array(frontier_sharpe),
                    "weights": frontier_weights,
                    "optimal_idx": optimal_idx,
                    "tickers": tickers,
                    "returns_df": returns_df,
                }
                
                components.success_message("Optimization complete!")
                
            except Exception as e:
                components.error_message(f"Optimization failed: {str(e)}")
                st.session_state.portfolio_results = None
    
    # Display results
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        
        # Metrics
        optimal_idx = results["optimal_idx"]
        components.multi_metric_row([
            {
                "title": "Optimal Return",
                "value": f"{results['returns'][optimal_idx]*100:.2f}%",
                "help": "Expected annual return of optimal portfolio",
            },
            {
                "title": "Optimal Volatility",
                "value": f"{results['volatilities'][optimal_idx]*100:.2f}%",
                "help": "Annual volatility of optimal portfolio",
            },
            {
                "title": "Sharpe Ratio",
                "value": f"{results['sharpe_ratios'][optimal_idx]:.2f}",
                "help": "Risk-adjusted return metric",
            },
            {
                "title": "Portfolios Analyzed",
                "value": len(results['returns']),
                "help": "Number of efficient portfolios on frontier",
            },
        ])
        
        st.markdown("---")
        
        # Plot efficient frontier
        fig = components.plot_efficient_frontier(
            returns=results["returns"],
            volatilities=results["volatilities"],
            sharpe_ratios=results["sharpe_ratios"],
            optimal_idx=optimal_idx,
            height=600,
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Click 'Optimize Portfolio' to generate the efficient frontier.")

with tab2:
    st.header("Optimal Portfolio Weights")
    
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        optimal_idx = results["optimal_idx"]
        optimal_weights = results["weights"][optimal_idx]
        
        # Create weights dict
        weights_dict = dict(zip(results["tickers"], optimal_weights))
        
        # Display as pie chart
        fig = components.plot_portfolio_weights(weights_dict, height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display as table
        weights_df = pd.DataFrame({
            "Ticker": results["tickers"],
            "Weight": optimal_weights,
            "Weight (%)": optimal_weights * 100,
        }).sort_values("Weight", ascending=False)
        
        components.data_table(
            weights_df.style.format({"Weight": "{:.4f}", "Weight (%)": "{:.2f}%"}),
            title="Allocation Details",
        )
        
        # Download button
        csv = weights_df.to_csv(index=False)
        components.download_button(
            data=csv,
            filename="optimal_weights.csv",
            label="📥 Download Weights (CSV)",
        )
        
    else:
        components.info_message("Run optimization to see optimal portfolio weights.")

with tab3:
    st.header("Performance Analysis")
    
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        returns_df = results["returns_df"]
        optimal_weights = results["weights"][results["optimal_idx"]]
        
        # Calculate portfolio returns
        portfolio_returns = (returns_df * optimal_weights).sum(axis=1)
        cumulative_returns = (1 + portfolio_returns).cumprod()
        
        # Plot cumulative returns
        perf_df = pd.DataFrame({
            "date": returns_df.index,
            "Cumulative Returns": cumulative_returns.values,
        })
        
        fig = components.plot_time_series(
            data=perf_df,
            title="Optimal Portfolio - Cumulative Returns",
            x_col="date",
            y_cols=["Cumulative Returns"],
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics
        st.subheader("Performance Metrics")
        
        total_return = (cumulative_returns.iloc[-1] - 1) * 100
        annualized_return = results["returns"][results["optimal_idx"]] * 100
        annualized_vol = results["volatilities"][results["optimal_idx"]] * 100
        sharpe = results["sharpe_ratios"][results["optimal_idx"]]
        max_drawdown = ((cumulative_returns / cumulative_returns.cummax()) - 1).min() * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Return", f"{total_return:.2f}%")
            st.metric("Annualized Return", f"{annualized_return:.2f}%")
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
        
        with col2:
            st.metric("Annualized Volatility", f"{annualized_vol:.2f}%")
            st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
            st.metric("Calendar Days", len(returns_df))
        
        # Correlation matrix
        st.subheader("Asset Correlation Matrix")
        corr_matrix = returns_df.corr()
        
        fig = components.plot_correlation_matrix(corr_matrix, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Run optimization to see performance analysis.")

# ============================================================================
# Tab 4: Dynamic Efficient Frontier
# ============================================================================
with tab4:
    st.header("Dynamic Efficient Frontier")
    
    st.markdown("""
    **Rolling Efficient Frontier Analysis** - Visualize how the efficient frontier evolves over time.
    
    This analysis shows how optimal portfolio allocations change across different market regimes.
    """)
    
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        returns_df = results["returns_df"]
        
        # Rolling frontier parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rolling_window = st.slider(
                "Rolling Window (days)",
                min_value=60,
                max_value=252,
                value=126,
                step=30,
                help="Window size for rolling frontier calculation"
            )
        
        with col2:
            num_frontiers = st.slider(
                "Number of Time Points",
                min_value=3,
                max_value=12,
                value=6,
                help="How many frontier snapshots to display"
            )
        
        with col3:
            frontier_portfolios = st.slider(
                "Portfolios per Frontier",
                min_value=20,
                max_value=100,
                value=50,
                step=10
            )
        
        if st.button("Generate Dynamic Frontier", type="primary"):
            with st.spinner("Calculating rolling efficient frontiers..."):
                try:
                    import plotly.graph_objects as go
                    
                    # Calculate time points for frontier snapshots
                    total_days = len(returns_df)
                    if total_days < rolling_window:
                        st.warning(f"Need at least {rolling_window} days of data. You have {total_days} days.")
                    else:
                        # Calculate evenly spaced time points
                        time_points = np.linspace(
                            rolling_window,
                            total_days,
                            num_frontiers,
                            dtype=int
                        )
                        
                        fig = go.Figure()
                        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                                 '#aec7e8', '#ffbb78']
                        
                        frontier_data = []
                        
                        for idx, end_point in enumerate(time_points):
                            # Get rolling window data
                            window_returns = returns_df.iloc[end_point-rolling_window:end_point]
                            
                            # Calculate statistics for this window
                            window_expected_returns = window_returns.mean() * 252
                            window_cov_matrix = window_returns.cov() * 252
                            
                            # Create optimizer
                            optimizer = PortfolioOptimizer(
                                expected_returns=window_expected_returns,
                                cov_matrix=window_cov_matrix,
                                risk_free_rate=risk_free_rate,
                                tickers=tickers
                            )
                            
                            # Generate frontier
                            min_ret = window_expected_returns.min()
                            max_ret = window_expected_returns.max()
                            target_rets = np.linspace(min_ret, max_ret, frontier_portfolios)
                            
                            vols = []
                            rets = []
                            sharpes = []
                            
                            for target_ret in target_rets:
                                try:
                                    result = optimizer.target_return(
                                        target_return=target_ret,
                                        allow_short=allow_short
                                    )
                                    rets.append(result.expected_return)
                                    vols.append(result.volatility)
                                    sharpes.append(result.sharpe_ratio)
                                except:
                                    continue
                            
                            if rets:
                                # Store frontier data
                                period_label = returns_df.index[end_point-1].strftime('%Y-%m-%d')
                                color = colors[idx % len(colors)]
                                
                                frontier_data.append({
                                    'period': period_label,
                                    'returns': rets,
                                    'volatilities': vols,
                                    'sharpes': sharpes
                                })
                                
                                # Plot this frontier
                                fig.add_trace(go.Scatter(
                                    x=np.array(vols) * 100,
                                    y=np.array(rets) * 100,
                                    mode='lines+markers',
                                    name=period_label,
                                    line=dict(width=2, color=color),
                                    marker=dict(size=4),
                                    hovertemplate=(
                                        f'<b>{period_label}</b><br>' +
                                        'Volatility: %{x:.2f}%<br>' +
                                        'Return: %{y:.2f}%<br>' +
                                        '<extra></extra>'
                                    )
                                ))
                        
                        fig.update_layout(
                            title=f"Dynamic Efficient Frontier ({rolling_window}-day rolling window)",
                            xaxis_title="Volatility (%)",
                            yaxis_title="Expected Return (%)",
                            template='plotly_dark',
                            height=700,
                            hovermode='closest',
                            legend=dict(
                                yanchor="top",
                                y=0.99,
                                xanchor="right",
                                x=0.99
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Summary table
                        st.subheader("Frontier Summary Across Time")
                        
                        summary_data = []
                        for data in frontier_data:
                            max_sharpe_idx = np.argmax(data['sharpes'])
                            summary_data.append({
                                'Period': data['period'],
                                'Optimal Return': f"{data['returns'][max_sharpe_idx]*100:.2f}%",
                                'Optimal Volatility': f"{data['volatilities'][max_sharpe_idx]*100:.2f}%",
                                'Max Sharpe': f"{data['sharpes'][max_sharpe_idx]:.2f}",
                                'Frontier Points': len(data['returns'])
                            })
                        
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True)
                        
                        # Insights
                        st.markdown("### Key Insights")
                        st.markdown("""
                        - **Frontier Evolution**: Observe how optimal portfolios shift during different market conditions
                        - **Risk-Return Trade-off**: See how the efficiency curve changes over time
                        - **Regime Detection**: Identify periods of high/low market efficiency
                        """)
                        
                except Exception as e:
                    st.error(f"Error calculating dynamic frontier: {str(e)}")
    else:
        components.info_message("Run optimization first to see dynamic frontier analysis.")

# ============================================================================
# Tab 5: Monte Carlo Wealth Simulator
# ============================================================================
with tab5:
    st.header("Monte Carlo Wealth Simulator")
    
    st.markdown("""
    **Long-term Wealth Projection** - Simulate portfolio growth over multiple years with Monte Carlo analysis.
    
    This simulation accounts for:
    - Historical return and volatility patterns
    - Periodic contributions/withdrawals
    - Compound growth effects
    - Range of possible outcomes
    """)
    
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        returns_df = results["returns_df"]
        optimal_weights = results["weights"][results["optimal_idx"]]
        
        # Simulation parameters
        st.subheader("Simulation Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            initial_investment = st.number_input(
                "Initial Investment ($)",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=10000
            )
            
            monthly_contribution = st.number_input(
                "Monthly Contribution ($)",
                min_value=0,
                max_value=100000,
                value=1000,
                step=100,
                help="Additional monthly investment"
            )
        
        with col2:
            simulation_years = st.slider(
                "Simulation Period (years)",
                min_value=5,
                max_value=40,
                value=20,
                step=5
            )
            
            num_simulations = st.slider(
                "Number of Simulations",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                help="More simulations = smoother distributions"
            )
        
        with col3:
            withdrawal_age = st.number_input(
                "Start Withdrawal at Year",
                min_value=0,
                max_value=40,
                value=simulation_years,
                step=1,
                help="Year to start withdrawing (0 = never)"
            )
            
            monthly_withdrawal = st.number_input(
                "Monthly Withdrawal ($)",
                min_value=0,
                max_value=100000,
                value=0,
                step=100,
                help="Monthly withdrawal amount"
            ) if withdrawal_age < simulation_years else 0
        
        if st.button("Run Monte Carlo Simulation", type="primary"):
            with st.spinner(f"Running {num_simulations:,} simulations..."):
                try:
                    import plotly.graph_objects as go
                    
                    # Calculate portfolio statistics
                    portfolio_returns = (returns_df * optimal_weights).sum(axis=1)
                    mean_daily_return = portfolio_returns.mean()
                    std_daily_return = portfolio_returns.std()
                    
                    # Convert to annual for simulation
                    mean_annual_return = mean_daily_return * 252
                    std_annual_return = std_daily_return * np.sqrt(252)
                    
                    # Run simulations
                    months = simulation_years * 12
                    simulation_results = np.zeros((num_simulations, months + 1))
                    simulation_results[:, 0] = initial_investment
                    
                    np.random.seed(None)  # Use real random seed
                    
                    for sim in range(num_simulations):
                        wealth = initial_investment
                        
                        for month in range(1, months + 1):
                            # Monthly return (assuming log-normal distribution)
                            monthly_return = np.random.normal(
                                mean_annual_return / 12,
                                std_annual_return / np.sqrt(12)
                            )
                            
                            # Apply return
                            wealth = wealth * (1 + monthly_return)
                            
                            # Add contribution or withdrawal
                            year = month / 12
                            if year < withdrawal_age:
                                wealth += monthly_contribution
                            else:
                                wealth -= monthly_withdrawal
                            
                            # Ensure wealth doesn't go negative
                            wealth = max(0, wealth)
                            
                            simulation_results[sim, month] = wealth
                    
                    # Calculate percentiles
                    months_array = np.arange(months + 1)
                    years_array = months_array / 12
                    
                    median_wealth = np.median(simulation_results, axis=0)
                    p10_wealth = np.percentile(simulation_results, 10, axis=0)
                    p25_wealth = np.percentile(simulation_results, 25, axis=0)
                    p75_wealth = np.percentile(simulation_results, 75, axis=0)
                    p90_wealth = np.percentile(simulation_results, 90, axis=0)
                    
                    # Plot simulation results
                    fig = go.Figure()
                    
                    # Plot sample paths (subset for clarity)
                    num_sample_paths = min(50, num_simulations)
                    for i in range(num_sample_paths):
                        fig.add_trace(go.Scatter(
                            x=years_array,
                            y=simulation_results[i],
                            mode='lines',
                            line=dict(width=0.5, color='rgba(100, 100, 100, 0.1)'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                    
                    # Plot percentile bands
                    fig.add_trace(go.Scatter(
                        x=years_array,
                        y=p90_wealth,
                        mode='lines',
                        name='90th Percentile',
                        line=dict(width=0, color='rgba(0, 255, 0, 0)'),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=years_array,
                        y=p10_wealth,
                        mode='lines',
                        name='10-90 Percentile Range',
                        line=dict(width=0, color='rgba(0, 255, 0, 0)'),
                        fill='tonexty',
                        fillcolor='rgba(0, 255, 0, 0.2)',
                        showlegend=True,
                        hovertemplate='Year: %{x:.1f}<br>10th: $%{y:,.0f}<extra></extra>'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=years_array,
                        y=p75_wealth,
                        mode='lines',
                        name='25-75 Percentile Range',
                        line=dict(width=0, color='rgba(0, 150, 255, 0)'),
                        hoverinfo='skip',
                        showlegend=False
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=years_array,
                        y=p25_wealth,
                        mode='lines',
                        name='25-75 Percentile',
                        line=dict(width=0, color='rgba(0, 150, 255, 0)'),
                        fill='tonexty',
                        fillcolor='rgba(0, 150, 255, 0.3)',
                        showlegend=True,
                        hovertemplate='Year: %{x:.1f}<br>25th: $%{y:,.0f}<extra></extra>'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=years_array,
                        y=median_wealth,
                        mode='lines',
                        name='Median',
                        line=dict(width=3, color='#ffffff'),
                        hovertemplate='Year: %{x:.1f}<br>Median: $%{y:,.0f}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=f"Monte Carlo Wealth Simulation ({num_simulations:,} paths)",
                        xaxis_title="Years",
                        yaxis_title="Portfolio Value ($)",
                        template='plotly_dark',
                        height=600,
                        hovermode='x unified',
                        yaxis=dict(tickformat='$,.0f')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Summary statistics
                    st.subheader("Projection Summary")
                    
                    final_median = median_wealth[-1]
                    final_p10 = p10_wealth[-1]
                    final_p90 = p90_wealth[-1]
                    
                    total_contributions = initial_investment + (monthly_contribution * months)
                    total_withdrawals = monthly_withdrawal * max(0, (simulation_years - withdrawal_age) * 12)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Median Final Value",
                            f"${final_median:,.0f}",
                            delta=f"+${final_median - total_contributions + total_withdrawals:,.0f}"
                        )
                    
                    with col2:
                        st.metric(
                            "10th Percentile",
                            f"${final_p10:,.0f}",
                            help="Worst 10% of outcomes"
                        )
                    
                    with col3:
                        st.metric(
                            "90th Percentile",
                            f"${final_p90:,.0f}",
                            help="Best 10% of outcomes"
                        )
                    
                    with col4:
                        prob_double = (simulation_results[:, -1] >= total_contributions * 2).mean() * 100
                        st.metric(
                            "Prob(2x Return)",
                            f"{prob_double:.1f}%"
                        )
                    
                    # Distribution at end
                    st.subheader(f"Wealth Distribution After {simulation_years} Years")
                    
                    fig2 = go.Figure()
                    
                    fig2.add_trace(go.Histogram(
                        x=simulation_results[:, -1],
                        nbinsx=50,
                        name='Final Wealth',
                        marker_color='skyblue',
                        opacity=0.7
                    ))
                    
                    fig2.add_vline(
                        x=final_median,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Median: ${final_median:,.0f}"
                    )
                    
                    fig2.update_layout(
                        title="Distribution of Final Portfolio Values",
                        xaxis_title="Final Value ($)",
                        yaxis_title="Frequency",
                        template='plotly_dark',
                        height=400,
                        xaxis=dict(tickformat='$,.0f')
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Key insights
                    st.markdown("### Key Insights")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Investment Summary:**")
                        st.write(f"• Initial Investment: ${initial_investment:,.0f}")
                        st.write(f"• Total Contributions: ${total_contributions:,.0f}")
                        if total_withdrawals > 0:
                            st.write(f"• Total Withdrawals: ${total_withdrawals:,.0f}")
                        st.write(f"• Net Invested: ${total_contributions - total_withdrawals:,.0f}")
                    
                    with col2:
                        st.markdown("**Outcome Probabilities:**")
                        prob_profitable = (simulation_results[:, -1] > total_contributions - total_withdrawals).mean() * 100
                        prob_loss = 100 - prob_profitable
                        st.write(f"• Probability of Gain: {prob_profitable:.1f}%")
                        st.write(f"• Probability of Loss: {prob_loss:.1f}%")
                        prob_million = (simulation_results[:, -1] >= 1_000_000).mean() * 100
                        st.write(f"• Probability of $1M+: {prob_million:.1f}%")
                    
                except Exception as e:
                    st.error(f"Error running simulation: {str(e)}")
    else:
        components.info_message("Run optimization first to use the wealth simulator.")

# ============================================================================
# Tab 6: Portfolio Diversification Analyzer
# ============================================================================
with tab6:
    st.header("🎯 Portfolio Diversification Analysis")
    
    st.markdown("""
    **Risk Reduction Through Diversification** - Analyze how combining uncorrelated assets reduces portfolio risk.
    Compare individual asset volatility against diversified portfolio volatility.
    """)
    
    if tickers and len(tickers) > 1:
        if st.button("🔍 Analyze Diversification", type="primary"):
            with st.spinner("Calculating correlation and risk metrics..."):
                try:
                    # Fetch data
                    market_data = MarketDataProvider()
                    data = {}
                    
                    for ticker in tickers:
                        try:
                            ticker_data = market_data.get_stock_data(
                                ticker,
                                start_date=start_date.strftime("%Y-%m-%d"),
                                end_date=end_date.strftime("%Y-%m-%d")
                            )
                            if ticker_data is not None and 'Close' in ticker_data.columns:
                                data[ticker] = ticker_data['Close']
                        except Exception as e:
                            st.warning(f"Could not fetch data for {ticker}: {str(e)}")
                            continue
                    
                    if len(data) < 2:
                        st.error("Need at least 2 valid tickers for diversification analysis")
                    else:
                        # Create DataFrame
                        prices_df = pd.DataFrame(data)
                        
                        # Calculate returns
                        returns_df = prices_df.pct_change().dropna()
                        
                        # Calculate correlation matrix
                        corr_matrix = returns_df.corr()
                        
                        # Display correlation heatmap
                        st.subheader("🔥 Correlation Heatmap")
                        
                        import plotly.figure_factory as ff
                        
                        fig_corr = ff.create_annotated_heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns.tolist(),
                            y=corr_matrix.index.tolist(),
                            annotation_text=np.around(corr_matrix.values, decimals=2),
                            colorscale='RdBu',
                            zmid=0,
                            showscale=True
                        )
                        
                        fig_corr.update_layout(
                            template='plotly_dark',
                            height=500,
                            title="Asset Return Correlations"
                        )
                        
                        st.plotly_chart(fig_corr, use_container_width=True)
                        
                        # Risk reduction analysis
                        st.subheader("🛡️ Risk Reduction Through Diversification")
                        
                        # Individual asset risks (annualized standard deviation)
                        individual_stds = returns_df.std() * np.sqrt(252)  # Annualized
                        
                        # Equal-weighted portfolio risk
                        equal_weighted_returns = returns_df.mean(axis=1)
                        portfolio_std = equal_weighted_returns.std() * np.sqrt(252)  # Annualized
                        
                        # Display risk comparison
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Individual Asset Risks (Annualized Volatility):**")
                            
                            risk_data = []
                            for ticker in individual_stds.index:
                                risk_data.append({
                                    'Asset': ticker,
                                    'Volatility (%)': f"{individual_stds[ticker] * 100:.2f}%"
                                })
                            
                            risk_df = pd.DataFrame(risk_data)
                            st.dataframe(risk_df, use_container_width=True, hide_index=True)
                            
                            avg_individual_risk = individual_stds.mean()
                            st.metric(
                                "Average Individual Risk",
                                f"{avg_individual_risk * 100:.2f}%"
                            )
                        
                        with col2:
                            st.markdown("**Equal-Weighted Portfolio:**")
                            
                            st.metric(
                                "Portfolio Risk (Volatility)",
                                f"{portfolio_std * 100:.2f}%",
                                delta=f"{(portfolio_std - avg_individual_risk) * 100:.2f}% vs avg"
                            )
                            
                            risk_reduction = (1 - portfolio_std / avg_individual_risk) * 100
                            
                            if risk_reduction > 0:
                                st.success(f"✅ **Risk Reduction: {risk_reduction:.1f}%**")
                                st.write("Diversification successfully reduces portfolio risk.")
                            else:
                                st.warning("⚠️ Assets are highly correlated, limited diversification benefit.")
                        
                        # Visualization: Risk comparison
                        st.subheader("📊 Risk Comparison: Individual vs Portfolio")
                        
                        import plotly.graph_objects as go
                        
                        fig_risk = go.Figure()
                        
                        # Individual asset risks
                        fig_risk.add_trace(go.Bar(
                            x=individual_stds.index,
                            y=individual_stds.values * 100,
                            name='Individual Asset Risk',
                            marker_color='red',
                            opacity=0.7
                        ))
                        
                        # Portfolio risk line
                        fig_risk.add_trace(go.Scatter(
                            x=individual_stds.index,
                            y=[portfolio_std * 100] * len(individual_stds),
                            name='Portfolio Risk (Equal-Weighted)',
                            mode='lines',
                            line=dict(color='lime', width=3, dash='dash')
                        ))
                        
                        fig_risk.update_layout(
                            template='plotly_dark',
                            height=400,
                            yaxis_title='Annualized Volatility (%)',
                            xaxis_title='Asset',
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig_risk, use_container_width=True)
                        
                        # Diversification insights
                        st.subheader("💡 Diversification Insights")
                        
                        # Find best and worst correlated pairs
                        corr_values = []
                        for i in range(len(corr_matrix)):
                            for j in range(i + 1, len(corr_matrix)):
                                corr_values.append((
                                    corr_matrix.index[i],
                                    corr_matrix.columns[j],
                                    corr_matrix.iloc[i, j]
                                ))
                        
                        corr_values.sort(key=lambda x: x[2])
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Least Correlated Pairs (Best Diversifiers):**")
                            for i in range(min(3, len(corr_values))):
                                asset1, asset2, corr = corr_values[i]
                                st.write(f"• {asset1} ↔ {asset2}: {corr:.3f}")
                        
                        with col2:
                            st.markdown("**Most Correlated Pairs (Limited Diversification):**")
                            for i in range(min(3, len(corr_values))):
                                asset1, asset2, corr = corr_values[-(i+1)]
                                st.write(f"• {asset1} ↔ {asset2}: {corr:.3f}")
                        
                        # Average correlation
                        avg_corr = np.mean([c[2] for c in corr_values])
                        
                        st.markdown("---")
                        st.markdown(f"**Average Pairwise Correlation:** {avg_corr:.3f}")
                        
                        if avg_corr < 0.3:
                            st.success("🌟 Excellent diversification! Low correlation between assets.")
                        elif avg_corr < 0.6:
                            st.info("👍 Good diversification. Moderate correlation between assets.")
                        else:
                            st.warning("⚠️ High correlation. Consider adding more uncorrelated assets.")
                        
                except Exception as e:
                    st.error(f"Error in diversification analysis: {str(e)}")
    else:
        st.info("📊 Add at least 2 tickers to analyze diversification benefits.")

# ============================================================================
# Tab 7: Smart Portfolio Optimizer (Monte Carlo Simulation)
# ============================================================================
with tab7:
    st.header("🧠 Smart Portfolio Optimizer")
    
    st.markdown("""
    **Monte Carlo Portfolio Optimization** - Simulate thousands of random portfolio allocations 
    to find optimal weights. Uses random sampling to explore the entire solution space.
    """)
    
    if tickers and len(tickers) >= 2:
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.subheader("⚙️ Simulation Parameters")
            
            num_simulations = st.slider(
                "Number of Simulations",
                min_value=1000,
                max_value=50000,
                value=10000,
                step=1000,
                help="More simulations = better coverage of solution space"
            )
            
            mc_risk_free = st.number_input(
                "Risk-Free Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=1.0,
                step=0.1
            ) / 100
            
            if st.button("🎲 Run Monte Carlo Optimization", type="primary"):
                with st.spinner(f"Simulating {num_simulations:,} portfolios..."):
                    try:
                        # Fetch data
                        market_data = MarketDataProvider()
                        data = {}
                        
                        for ticker in tickers:
                            try:
                                ticker_data = market_data.get_stock_data(
                                    ticker,
                                    start_date=start_date.strftime("%Y-%m-%d"),
                                    end_date=end_date.strftime("%Y-%m-%d")
                                )
                                if ticker_data is not None and 'Close' in ticker_data.columns:
                                    data[ticker] = ticker_data['Close']
                            except:
                                continue
                        
                        if len(data) < 2:
                            st.error("Need at least 2 valid tickers")
                        else:
                            prices_df = pd.DataFrame(data)
                            returns_df = prices_df.pct_change().dropna()
                            
                            expected_returns = returns_df.mean()
                            cov_matrix = returns_df.cov()
                            
                            # Monte Carlo simulation
                            simulation_results = {
                                'returns': [],
                                'volatility': [],
                                'sharpe': [],
                                'weights': []
                            }
                            
                            for _ in range(num_simulations):
                                # Random weights using Dirichlet distribution (ensures sum to 1)
                                weights = np.random.dirichlet(np.ones(len(tickers)), size=1)[0]
                                
                                # Portfolio metrics
                                port_return = np.dot(weights, expected_returns)
                                port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                                sharpe = (port_return - mc_risk_free) / port_volatility if port_volatility > 0 else 0
                                
                                simulation_results['returns'].append(port_return)
                                simulation_results['volatility'].append(port_volatility)
                                simulation_results['sharpe'].append(sharpe)
                                simulation_results['weights'].append(weights)
                            
                            # Find optimal portfolios
                            max_sharpe_idx = np.argmax(simulation_results['sharpe'])
                            min_vol_idx = np.argmin(simulation_results['volatility'])
                            
                            optimal_portfolios = {
                                'max_sharpe': {
                                    'return': simulation_results['returns'][max_sharpe_idx],
                                    'volatility': simulation_results['volatility'][max_sharpe_idx],
                                    'sharpe': simulation_results['sharpe'][max_sharpe_idx],
                                    'weights': simulation_results['weights'][max_sharpe_idx]
                                },
                                'min_volatility': {
                                    'return': simulation_results['returns'][min_vol_idx],
                                    'volatility': simulation_results['volatility'][min_vol_idx],
                                    'sharpe': simulation_results['sharpe'][min_vol_idx],
                                    'weights': simulation_results['weights'][min_vol_idx]
                                }
                            }
                            
                            st.session_state.mc_results = simulation_results
                            st.session_state.mc_optimal = optimal_portfolios
                            st.session_state.mc_tickers = tickers
                            
                    except Exception as e:
                        st.error(f"Error in Monte Carlo optimization: {str(e)}")
        
        with col1:
            if 'mc_results' in st.session_state and st.session_state.mc_tickers == tickers:
                results = st.session_state.mc_results
                optimal = st.session_state.mc_optimal
                
                # Efficient Frontier Plot
                st.subheader("📊 Monte Carlo Efficient Frontier")
                
                import plotly.graph_objects as go
                
                returns_array = np.array(results['returns']) * 252 * 100  # Annualized %
                volatility_array = np.array(results['volatility']) * np.sqrt(252) * 100  # Annualized %
                sharpe_array = np.array(results['sharpe'])
                
                fig_ef = go.Figure()
                
                # Scatter of all simulated portfolios
                fig_ef.add_trace(go.Scatter(
                    x=volatility_array,
                    y=returns_array,
                    mode='markers',
                    marker=dict(
                        size=4,
                        color=sharpe_array,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Sharpe Ratio"),
                        opacity=0.6
                    ),
                    name='Simulated Portfolios',
                    hovertemplate='<b>Vol:</b> %{x:.2f}%<br><b>Return:</b> %{y:.2f}%<extra></extra>'
                ))
                
                # Max Sharpe portfolio
                fig_ef.add_trace(go.Scatter(
                    x=[optimal['max_sharpe']['volatility'] * np.sqrt(252) * 100],
                    y=[optimal['max_sharpe']['return'] * 252 * 100],
                    mode='markers',
                    marker=dict(size=20, color='red', symbol='star'),
                    name='Max Sharpe Ratio',
                    hovertemplate='<b>Max Sharpe</b><br>Vol: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>'
                ))
                
                # Min Volatility portfolio
                fig_ef.add_trace(go.Scatter(
                    x=[optimal['min_volatility']['volatility'] * np.sqrt(252) * 100],
                    y=[optimal['min_volatility']['return'] * 252 * 100],
                    mode='markers',
                    marker=dict(size=20, color='blue', symbol='star'),
                    name='Min Volatility',
                    hovertemplate='<b>Min Vol</b><br>Vol: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>'
                ))
                
                fig_ef.update_layout(
                    template='plotly_dark',
                    height=500,
                    xaxis_title='Volatility (% annualized)',
                    yaxis_title='Expected Return (% annualized)',
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_ef, use_container_width=True)
                
                # Optimal Portfolios
                st.subheader("🏆 Optimal Portfolios")
                
                col1a, col2a = st.columns(2)
                
                with col1a:
                    st.markdown("**🔴 Max Sharpe Ratio Portfolio**")
                    
                    st.metric(
                        "Sharpe Ratio",
                        f"{optimal['max_sharpe']['sharpe']:.3f}"
                    )
                    
                    col_ret, col_vol = st.columns(2)
                    with col_ret:
                        st.metric("Return", f"{optimal['max_sharpe']['return'] * 252 * 100:.2f}%")
                    with col_vol:
                        st.metric("Volatility", f"{optimal['max_sharpe']['volatility'] * np.sqrt(252) * 100:.2f}%")
                    
                    st.markdown("**Weights:**")
                    weights_df_sharpe = pd.DataFrame({
                        'Asset': tickers,
                        'Weight (%)': optimal['max_sharpe']['weights'] * 100
                    }).sort_values('Weight (%)', ascending=False)
                    
                    st.dataframe(
                        weights_df_sharpe.style.format({'Weight (%)': '{:.2f}%'}),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2a:
                    st.markdown("**🔵 Min Volatility Portfolio**")
                    
                    st.metric(
                        "Sharpe Ratio",
                        f"{optimal['min_volatility']['sharpe']:.3f}"
                    )
                    
                    col_ret2, col_vol2 = st.columns(2)
                    with col_ret2:
                        st.metric("Return", f"{optimal['min_volatility']['return'] * 252 * 100:.2f}%")
                    with col_vol2:
                        st.metric("Volatility", f"{optimal['min_volatility']['volatility'] * np.sqrt(252) * 100:.2f}%")
                    
                    st.markdown("**Weights:**")
                    weights_df_minvol = pd.DataFrame({
                        'Asset': tickers,
                        'Weight (%)': optimal['min_volatility']['weights'] * 100
                    }).sort_values('Weight (%)', ascending=False)
                    
                    st.dataframe(
                        weights_df_minvol.style.format({'Weight (%)': '{:.2f}%'}),
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Pie charts
                st.subheader("🥧 Weight Allocation")
                
                col1b, col2b = st.columns(2)
                
                with col1b:
                    # Max Sharpe pie chart
                    fig_pie_sharpe = go.Figure(data=[go.Pie(
                        labels=tickers,
                        values=optimal['max_sharpe']['weights'],
                        hole=0.3
                    )])
                    
                    fig_pie_sharpe.update_layout(
                        title="Max Sharpe Portfolio",
                        template='plotly_dark',
                        height=400
                    )
                    
                    st.plotly_chart(fig_pie_sharpe, use_container_width=True)
                
                with col2b:
                    # Min Vol pie chart
                    fig_pie_minvol = go.Figure(data=[go.Pie(
                        labels=tickers,
                        values=optimal['min_volatility']['weights'],
                        hole=0.3
                    )])
                    
                    fig_pie_minvol.update_layout(
                        title="Min Volatility Portfolio",
                        template='plotly_dark',
                        height=400
                    )
                    
                    st.plotly_chart(fig_pie_minvol, use_container_width=True)
                
                # Simulation statistics
                st.subheader("📊 Simulation Statistics")
                
                col1c, col2c, col3c, col4c = st.columns(4)
                
                with col1c:
                    st.metric("Simulations", f"{len(results['returns']):,}")
                
                with col2c:
                    avg_return = np.mean(returns_array)
                    st.metric("Avg Return", f"{avg_return:.2f}%")
                
                with col3c:
                    avg_vol = np.mean(volatility_array)
                    st.metric("Avg Volatility", f"{avg_vol:.2f}%")
                
                with col4c:
                    avg_sharpe = np.mean(sharpe_array)
                    st.metric("Avg Sharpe", f"{avg_sharpe:.3f}")
                
            else:
                st.info("🎲 Run Monte Carlo optimization to see results")
    
    else:
        st.info("📊 Select at least 2 tickers to run Monte Carlo optimization")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Portfolio Optimization powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
