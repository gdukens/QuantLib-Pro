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
    page_icon="",
    layout="wide",
)

st.title("Portfolio Optimization")
st.markdown("Optimize portfolio allocations using advanced mean-variance optimization. Get dynamic insights and context-aware analysis of your portfolio's risk-return profile.")

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
    optimize_button = st.button(" Optimize Portfolio", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3 = st.tabs([" Efficient Frontier", " Optimal Weights", " Performance"])

with tab1:
    st.header("Efficient Frontier")
    
    if optimize_button:
        with st.spinner("Fetching market data and optimizing..."):
            try:
                # Fetch market data
                data_provider = MarketDataProvider()
                
                # Use simulated data for demo
                dates = pd.date_range(start=start_date, end=end_date, freq="D")
                returns_data = {}
                
                for ticker in tickers:
                    # Simulate returns with different characteristics
                    np.random.seed(hash(ticker) % 2**32)
                    daily_returns = np.random.normal(0.0005, 0.02, len(dates))
                    returns_data[ticker] = daily_returns
                
                returns_df = pd.DataFrame(returns_data, index=dates)
                
                # Calculate expected returns and covariance matrix
                expected_returns = returns_df.mean() * 252  # Annualize
                cov_matrix = returns_df.cov() * 252  # Annualize
                
                # Calculate efficient frontier
                optimizer = PortfolioOptimizer(
                    expected_returns=expected_returns,
                    cov_matrix=cov_matrix,
                    risk_free_rate=risk_free_rate,
                    tickers=tickers
                )
                
                # Generate frontier points using the efficient_frontier method
                try:
                    frontier_portfolios = optimizer.efficient_frontier(
                        n_points=num_frontier_points,
                        allow_short=allow_short
                    )
                    
                    frontier_volatilities = [p.volatility for p in frontier_portfolios]
                    frontier_returns = [p.expected_return for p in frontier_portfolios]
                    frontier_sharpe = [p.sharpe_ratio for p in frontier_portfolios]
                    frontier_weights = [p.weights.tolist() for p in frontier_portfolios]
                    
                except Exception as e:
                    st.error(f"Efficient frontier calculation failed: {e}")
                    frontier_volatilities = []
                    frontier_returns = []
                    frontier_sharpe = []
                    frontier_weights = []
                
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
        # Ensure arrays have same length by adjusting both arrays if needed
        try:
            if hasattr(st.session_state, 'portfolio_results') and 'weights' in results and 'tickers' in results:
                n_assets = len(results["tickers"])
                
                # Convert to numpy array if not already
                if not isinstance(optimal_weights, np.ndarray):
                    optimal_weights = np.array(optimal_weights)
                
                optimal_weights_len = len(optimal_weights)
                
                # Debug information for array lengths
                if optimal_weights_len != n_assets:
                    st.warning(f"Array length mismatch detected: {optimal_weights_len} weights vs {n_assets} tickers. Adjusting arrays.")
                
                # Ensure both arrays are the same length
                if optimal_weights_len > n_assets:
                    optimal_weights = optimal_weights[:n_assets]
                elif optimal_weights_len < n_assets:
                    # Pad with zeros if needed
                    padding = np.zeros(n_assets - optimal_weights_len)
                    optimal_weights = np.concatenate([optimal_weights, padding])
                
                # Convert back to list for DataFrame creation
                optimal_weights = optimal_weights.tolist()
                tickers_list = list(results["tickers"])
                
                # Final verification
                if len(optimal_weights) == len(tickers_list):
                    weights_df = pd.DataFrame({
                        "Ticker": tickers_list,
                        "Weight": optimal_weights,
                        "Weight (%)": [w * 100 for w in optimal_weights],
                    }).sort_values("Weight", ascending=False)
                else:
                    # Emergency fallback
                    st.error(f"Critical error: Cannot align arrays - {len(optimal_weights)} weights vs {len(tickers_list)} tickers")
                    weights_df = pd.DataFrame({
                        "Ticker": ["Error"],
                        "Weight": [0.0],
                        "Weight (%)": [0.0],
                    })
            else:
                # Fallback if no results available
                weights_df = pd.DataFrame({
                    "Ticker": ["No data"],
                    "Weight": [0.0],
                    "Weight (%)": [0.0],
                })
        except Exception as e:
            st.error(f"DataFrame creation error: {str(e)}")
            # Ultimate fallback
            weights_df = pd.DataFrame({
                "Ticker": ["Error"],
                "Weight": [0.0],
                "Weight (%)": [0.0],
            })
        
        components.data_table(
            weights_df.style.format({"Weight": "{:.4f}", "Weight (%)": "{:.2f}%"}),
            title="Allocation Details",
        )
        
        # Download button
        csv = weights_df.to_csv(index=False)
        components.download_button(
            data=csv,
            filename="optimal_weights.csv",
            label=" Download Weights (CSV)",
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
        
        # Plot cumulative returns - Ensure arrays are same length
        try:
            dates = returns_df.index.tolist()
            cum_returns = cumulative_returns.values.tolist()
            
            # Verify lengths match
            if len(dates) == len(cum_returns):
                perf_df = pd.DataFrame({
                    "date": dates,
                    "Cumulative Returns": cum_returns,
                })
            else:
                # Truncate to shorter length
                min_len = min(len(dates), len(cum_returns))
                perf_df = pd.DataFrame({
                    "date": dates[:min_len],
                    "Cumulative Returns": cum_returns[:min_len],
                })
                st.warning(f"Date/returns length mismatch: {len(dates)} vs {len(cum_returns)}. Truncated to {min_len}.")
        except Exception as e:
            st.error(f"Performance data error: {str(e)}")
            # Fallback empty chart
            perf_df = pd.DataFrame({
                "date": [pd.Timestamp.now()],
                "Cumulative Returns": [1.0],
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
        
        # Context-aware Portfolio Analysis
        st.subheader("📊 Portfolio Analysis")
        
        # Get top holdings for context
        top_holding = weights_dict[max(weights_dict, key=weights_dict.get)]
        top_ticker = max(weights_dict, key=weights_dict.get)
        concentration = sum(w for w in weights_dict.values() if w > 0.1)  # Holdings > 10%
        num_significant_holdings = sum(1 for w in weights_dict.values() if w > 0.05)  # Holdings > 5%
        
        # Risk-Return Context
        if sharpe > 1.5:
            risk_assessment = "excellent risk-adjusted returns"
            risk_color = "success"
        elif sharpe > 1.0:
            risk_assessment = "good risk-adjusted returns"
            risk_color = "info"
        elif sharpe > 0.5:
            risk_assessment = "moderate risk-adjusted returns"
            risk_color = "warning"
        else:
            risk_assessment = "poor risk-adjusted returns"
            risk_color = "error"
        
        # Concentration Analysis
        if concentration > 0.7:
            concentration_msg = f"highly concentrated portfolio with {concentration:.1%} in major positions"
            concentration_color = "warning"
        elif concentration > 0.5:
            concentration_msg = f"moderately concentrated with {concentration:.1%} in top holdings"
            concentration_color = "info"
        else:
            concentration_msg = f"well-diversified portfolio with {concentration:.1%} concentration"
            concentration_color = "success"
        
        # Volatility Context
        if annualized_vol > 25:
            vol_assessment = "high volatility suggests aggressive risk profile"
        elif annualized_vol > 15:
            vol_assessment = "moderate volatility indicates balanced risk approach"
        else:
            vol_assessment = "low volatility reflects conservative positioning"
        
        # Dynamic Interpretation
        if risk_color == "success":
            st.success(f"🎯 **Strong Performance**: This portfolio delivers {risk_assessment} with a Sharpe ratio of {sharpe:.2f}. The {top_ticker} position ({top_holding:.1%}) leads the allocation in this {concentration_msg}.")
        elif risk_color == "info":
            st.info(f"📈 **Balanced Portfolio**: Achieving {risk_assessment} with {vol_assessment}. The strategy shows {concentration_msg} with {num_significant_holdings} significant holdings.")
        elif risk_color == "warning":
            st.warning(f"⚠️ **Mixed Results**: The portfolio shows {risk_assessment} despite {vol_assessment}. Consider rebalancing the {concentration_msg} for better risk management.")
        else:
            st.error(f"🚨 **Underperforming**: Current allocation delivers {risk_assessment}. The {max_drawdown:.1f}% maximum drawdown and {concentration_msg} suggest need for strategy revision.")
        
        # Drawdown Context
        if abs(max_drawdown) > 20:
            st.warning(f"🔻 **High Drawdown Alert**: Maximum drawdown of {max_drawdown:.1f}% indicates significant downside risk. This exceeds typical comfort levels for most investors.")
        elif abs(max_drawdown) > 10:
            st.info(f"📉 **Moderate Drawdown**: The {max_drawdown:.1f}% maximum drawdown is within normal ranges but worth monitoring for risk management.")
        else:
            st.success(f"✅ **Low Drawdown**: Excellent downside protection with only {max_drawdown:.1f}% maximum drawdown, indicating stable performance.")
        
        # Return Context based on risk-free rate
        risk_free_rate = risk_free_rate * 100  # Convert to percentage
        excess_return = annualized_return - risk_free_rate
        if excess_return > 5:
            st.success(f"💰 **Strong Alpha Generation**: Portfolio generates {excess_return:.1f}% excess return over the {risk_free_rate:.1f}% risk-free rate.")
        elif excess_return > 0:
            st.info(f"📊 **Positive Alpha**: Earning {excess_return:.1f}% above risk-free rate, indicating value creation.")
        else:
            st.warning(f"⚠️ **Underperforming Risk-Free Rate**: Returns lag the risk-free rate by {abs(excess_return):.1f}%.")
        
        # Correlation matrix
        st.subheader("Asset Correlation Matrix")
        corr_matrix = returns_df.corr()
        
        fig = components.plot_correlation_matrix(corr_matrix, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Run optimization to see performance analysis.")

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
