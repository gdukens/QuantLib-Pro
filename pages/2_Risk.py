"""
Risk Analytics Dashboard

Week 12: Streamlit page for Value-at-Risk, stress testing, and tail risk analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

from quantlib_pro.ui import components
from quantlib_pro.risk.var import calculate_var
from quantlib_pro.risk.stress import StressTester
from quantlib_pro.data.market_data import MarketDataProvider

# Page config
st.set_page_config(
    page_title="Risk Analytics - QuantLib Pro",
    page_icon="",
    layout="wide",
)

st.title("Risk Analytics")
st.markdown("Comprehensive risk analysis including VaR, CVaR, stress testing, and tail risk metrics.")

# Initialize session state
if "risk_results" not in st.session_state:
    st.session_state.risk_results = None

# Sidebar controls
with st.sidebar:
    st.header("Configuration")
    
    # Portfolio setup
    st.subheader("Portfolio")
    
    ticker_input = st.text_area(
        "Tickers (one per line)",
        value="AAPL\nMSFT\nGOOG\nAMZN",
        height=120,
    )
    tickers = [t.strip().upper() for t in ticker_input.split("\n") if t.strip()]
    
    weights_input = st.text_area(
        "Weights (one per line, must sum to 1)",
        value="0.25\n0.25\n0.25\n0.25",
        height=120,
    )
    
    try:
        weights = [float(w.strip()) for w in weights_input.split("\n") if w.strip()]
        if len(weights) != len(tickers):
            st.error(f" Mismatch: {len(tickers)} tickers but {len(weights)} weights")
        elif abs(sum(weights) - 1.0) > 0.01:
            st.warning(f" Weights sum to {sum(weights):.2f}, should be 1.0")
        else:
            st.success(f" {len(tickers)} assets, weights sum to {sum(weights):.2f}")
    except ValueError:
        st.error(" Invalid weight format")
        weights = []
    
    portfolio_value = st.number_input(
        "Portfolio Value ($)",
        min_value=1000,
        max_value=100_000_000,
        value=1_000_000,
        step=10000,
    )
    
    # Date range
    st.subheader("Date Range")
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)
    
    # Risk parameters
    st.subheader("Risk Parameters")
    
    confidence_level = st.slider(
        "VaR Confidence Level (%)",
        min_value=90,
        max_value=99,
        value=95,
        step=1,
    ) / 100
    
    var_method = st.selectbox(
        "VaR Method",
        ["historical", "parametric", "monte_carlo"],
        index=0,
    )
    
    time_horizon = st.slider(
        "Time Horizon (days)",
        min_value=1,
        max_value=30,
        value=1,
        step=1,
    )
    
    # Run analysis
    analyze_button = st.button(" Analyze Risk", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3 = st.tabs([" VaR Analysis", " Stress Testing", " Tail Risk"])

with tab1:
    st.header("Value-at-Risk (VaR) Analysis")
    
    if analyze_button:
        if len(tickers) != len(weights) or abs(sum(weights) - 1.0) > 0.01:
            components.error_message("Invalid portfolio configuration. Check tickers and weights.")
        else:
            with st.spinner("Calculating VaR..."):
                try:
                    # Simulate returns data
                    dates = pd.date_range(start=start_date, end=end_date, freq="D")
                    returns_data = {}
                    
                    for ticker in tickers:
                        np.random.seed(hash(ticker) % 2**32)
                        daily_returns = np.random.normal(0.0005, 0.02, len(dates))
                        returns_data[ticker] = daily_returns
                    
                    returns_df = pd.DataFrame(returns_data, index=dates)
                    
                    # Calculate portfolio returns
                    portfolio_returns = (returns_df * weights).sum(axis=1)
                    
                    # Calculate VaR
                    var_result = calculate_var(
                        returns=portfolio_returns.values,
                        confidence_level=confidence_level,
                        method=var_method,
                        portfolio_value=portfolio_value,
                    )
                    
                    # Store results
                    st.session_state.risk_results = {
                        "var": var_result.var,
                        "cvar": var_result.cvar,
                        "confidence_level": confidence_level,
                        "method": var_method,
                        "portfolio_returns": portfolio_returns,
                        "portfolio_value": portfolio_value,
                        "returns_df": returns_df,
                        "weights": weights,
                        "tickers": tickers,
                    }
                    
                    components.success_message("VaR calculation complete!")
                    
                except Exception as e:
                    components.error_message(f"Risk analysis failed: {str(e)}")
                    st.session_state.risk_results = None
    
    # Display VaR results
    if st.session_state.risk_results:
        results = st.session_state.risk_results
        
        # Metrics
        var_dollar = results["var"] * results["portfolio_value"]
        cvar_dollar = results["cvar"] * results["portfolio_value"]
        
        components.multi_metric_row([
            {
                "title": f"VaR ({results['confidence_level']*100:.0f}%)",
                "value": f"${abs(var_dollar):,.0f}",
                "delta": f"{results['var']*100:.2f}%",
                "help": f"Maximum expected loss at {results['confidence_level']*100:.0f}% confidence",
            },
            {
                "title": f"CVaR ({results['confidence_level']*100:.0f}%)",
                "value": f"${abs(cvar_dollar):,.0f}",
                "delta": f"{results['cvar']*100:.2f}%",
                "help": "Expected loss given VaR is breached (tail risk)",
            },
            {
                "title": "Method",
                "value": results["method"].title(),
                "help": "VaR calculation methodology",
            },
            {
                "title": "Portfolio Value",
                "value": f"${results['portfolio_value']:,.0f}",
                "help": "Total portfolio value",
            },
        ])
        
        st.markdown("---")
        
        # Plot distribution
        fig = components.plot_var_distribution(
            returns=results["portfolio_returns"].values,
            var_value=results["var"],
            cvar_value=results["cvar"],
            confidence_level=results["confidence_level"],
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretation
        st.subheader("Interpretation")
        st.markdown(
            f"""
            - **VaR ({results['confidence_level']*100:.0f}%)**: With {results['confidence_level']*100:.0f}% confidence, 
              the portfolio will not lose more than **${abs(var_dollar):,.0f}** 
              ({abs(results['var'])*100:.2f}%) in a single day.
            
            - **CVaR ({results['confidence_level']*100:.0f}%)**: If losses exceed the VaR threshold, 
              the expected loss is **${abs(cvar_dollar):,.0f}** 
              ({abs(results['cvar'])*100:.2f}%).
            
            - **Method**: {results['method'].title()} VaR uses 
              {'historical return distribution' if results['method'] == 'historical' else 
               'normal distribution assumption' if results['method'] == 'parametric' else
               'Monte Carlo simulation'}.
            """
        )
        
    else:
        components.info_message("Click 'Analyze Risk' to calculate VaR and CVaR.")

with tab2:
    st.header("Stress Testing")
    
    if st.session_state.risk_results:
        results = st.session_state.risk_results
        
        st.subheader("Scenario Analysis")
        st.markdown("Simulate portfolio performance under extreme market conditions.")
        
        # Define stress scenarios
        scenarios = {
            "Market Crash (-20%)": -0.20,
            "Volatility Spike (+50%)": 0.15,
            "2008 Financial Crisis": -0.35,
            "COVID-19 Crash": -0.30,
            "Black Monday 1987": -0.22,
            "Moderate Correction (-10%)": -0.10,
        }
        
        # Calculate impacts
        scenario_impacts = {}
        
        for scenario_name, market_shock in scenarios.items():
            # Simple stress test: apply shock to portfolio
            # In reality, would use correlation structure and asset-specific betas
            portfolio_impact = market_shock * 1.2  # Assume 1.2 beta to market
            scenario_impacts[scenario_name] = portfolio_impact * 100
        
        # Plot scenarios
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = components.plot_stress_test(scenario_impacts, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Scenario Details")
            for scenario_name, impact_pct in scenario_impacts.items():
                impact_dollar = (impact_pct / 100) * results["portfolio_value"]
                st.markdown(
                    f"**{scenario_name}**  \n"
                    f"Impact: ${impact_dollar:,.0f} ({impact_pct:.1f}%)"
                )
        
        # Custom scenario
        st.subheader("Custom Scenario")
        
        col1, col2 = st.columns(2)
        
        with col1:
            custom_shock = st.slider(
                "Market Shock (%)",
                min_value=-50,
                max_value=50,
                value=-15,
                step=1,
            )
        
        with col2:
            portfolio_beta = st.slider(
                "Portfolio Beta",
                min_value=0.5,
                max_value=2.0,
                value=1.2,
                step=0.1,
            )
        
        custom_impact = (custom_shock / 100) * portfolio_beta
        custom_impact_dollar = custom_impact * results["portfolio_value"]
        
        st.metric(
            "Custom Scenario Impact",
            f"${custom_impact_dollar:,.0f}",
            delta=f"{custom_impact*100:.2f}%",
        )
        
    else:
        components.info_message("Run VaR analysis first to enable stress testing.")

with tab3:
    st.header("Tail Risk Metrics")
    
    if st.session_state.risk_results:
        results = st.session_state.risk_results
        portfolio_returns = results["portfolio_returns"]
        
        # Calculate tail risk metrics
        from scipy import stats
        
        # Skewness and kurtosis
        skewness = stats.skew(portfolio_returns)
        kurtosis = stats.kurtosis(portfolio_returns)
        
        # Extreme returns
        extreme_losses = portfolio_returns[portfolio_returns < results["var"]]
        avg_extreme_loss = extreme_losses.mean() if len(extreme_losses) > 0 else 0
        max_loss = portfolio_returns.min()
        max_gain = portfolio_returns.max()
        
        # Metrics display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Skewness",
                f"{skewness:.3f}",
                help="Negative skew indicates more frequent large losses",
            )
            st.metric(
                "Kurtosis",
                f"{kurtosis:.3f}",
                help="Higher kurtosis indicates fatter tails (more extreme events)",
            )
        
        with col2:
            st.metric(
                "Max Drawdown",
                f"{max_loss*100:.2f}%",
                help="Largest single-day loss in the period",
            )
            st.metric(
                "Max Gain",
                f"{max_gain*100:.2f}%",
                help="Largest single-day gain in the period",
            )
        
        with col3:
            st.metric(
                "Avg Extreme Loss",
                f"{avg_extreme_loss*100:.2f}%",
                help=f"Average loss when VaR ({results['confidence_level']*100:.0f}%) is breached",
            )
            st.metric(
                "# Extreme Events",
                len(extreme_losses),
                help=f"Number of days exceeding VaR threshold",
            )
        
        # Tail analysis
        st.subheader("Distribution Analysis")
        
        interpretation = []
        
        if skewness < -0.5:
            interpretation.append(" **Negative skew**: Portfolio has asymmetric downside risk (fat left tail)")
        elif skewness > 0.5:
            interpretation.append(" **Positive skew**: Portfolio has asymmetric upside potential")
        else:
            interpretation.append("ℹ **Near-symmetric**: Distribution is relatively balanced")
        
        if kurtosis > 3:
            interpretation.append(f" **High kurtosis ({kurtosis:.1f})**: More extreme events than normal distribution predicts")
        elif kurtosis < -1:
            interpretation.append(f"ℹ **Low kurtosis ({kurtosis:.1f})**: Fewer extreme events than normal distribution")
        else:
            interpretation.append(f"ℹ **Normal kurtosis ({kurtosis:.1f})**: Similar to normal distribution")
        
        for item in interpretation:
            st.markdown(item)
        
        # Q-Q plot comparison with normal distribution
        st.subheader("Return Distribution vs. Normal")
        
        normal_quantiles = np.random.normal(
            portfolio_returns.mean(),
            portfolio_returns.std(),
            len(portfolio_returns)
        )
        
        comparison_df = pd.DataFrame({
            "Portfolio Returns": sorted(portfolio_returns.values),
            "Normal Distribution": sorted(normal_quantiles),
        })
        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=comparison_df["Normal Distribution"] * 100,
            y=comparison_df["Portfolio Returns"] * 100,
            mode="markers",
            marker=dict(size=4, color="steelblue", opacity=0.6),
            name="Actual Returns",
        ))
        
        # Add diagonal line (perfect normal)
        min_val = min(comparison_df.min()) * 100
        max_val = max(comparison_df.max()) * 100
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode="lines",
            line=dict(color="red", dash="dash"),
            name="Perfect Normal",
        ))
        
        fig.update_layout(
            title="Q-Q Plot: Portfolio Returns vs. Normal Distribution",
            xaxis_title="Normal Distribution Quantiles (%)",
            yaxis_title="Portfolio Return Quantiles (%)",
            height=400,
            template="plotly_white",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(
            """
            **Interpretation**: Points that deviate from the diagonal line indicate departures from normality.
            - Points below the line in the left tail = more extreme negative returns than normal
            - Points above the line in the right tail = more extreme positive returns than normal
            """
        )
        
    else:
        components.info_message("Run VaR analysis to see tail risk metrics.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Risk Analytics powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
