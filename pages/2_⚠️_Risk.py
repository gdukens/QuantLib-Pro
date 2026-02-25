"""
Risk Analytics Dashboard

Week 12: Streamlit page for Value-at-Risk, stress testing, and tail risk analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict

from quantlib_pro.ui import components
from quantlib_pro.risk.var import calculate_var
from quantlib_pro.risk.stress import StressTester
from quantlib_pro.data.market_data import MarketDataProvider

# Page config
st.set_page_config(
    page_title="Risk Analytics - QuantLib Pro",
    page_icon="⚠️",
    layout="wide",
)

st.title("⚠️ Risk Analytics")
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
            st.error(f"⚠️ Mismatch: {len(tickers)} tickers but {len(weights)} weights")
        elif abs(sum(weights) - 1.0) > 0.01:
            st.warning(f"⚠️ Weights sum to {sum(weights):.2f}, should be 1.0")
        else:
            st.success(f"✅ {len(tickers)} assets, weights sum to {sum(weights):.2f}")
    except ValueError:
        st.error("❌ Invalid weight format")
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
    analyze_button = st.button("📊 Analyze Risk", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "📉 VaR Analysis",
    "💥 Stress Testing",
    "📊 Tail Risk",
    "🧠 Trader Stress Monitor"
])

with tab1:
    st.header("Value-at-Risk (VaR) Analysis")
    
    if analyze_button:
        if len(tickers) != len(weights) or abs(sum(weights) - 1.0) > 0.01:
            components.error_message("Invalid portfolio configuration. Check tickers and weights.")
        else:
            with st.spinner("Calculating VaR..."):
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
                    
                    # Calculate portfolio returns
                    portfolio_returns = (returns_df * weights).sum(axis=1)
                    
                    # Calculate VaR with user-specified time horizon
                    var_result = calculate_var(
                        returns=portfolio_returns.values,
                        confidence_level=confidence_level,
                        time_horizon=time_horizon,  # Use user-specified time horizon
                        method=var_method,
                        portfolio_value=portfolio_value,
                    )
                    
                    # Store results
                    st.session_state.risk_results = {
                        "var": var_result.var,
                        "cvar": var_result.cvar,
                        "confidence_level": confidence_level,
                        "method": var_method,
                        "time_horizon": time_horizon,  # Store time horizon for display
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
        time_period = f"{results['time_horizon']} day{'s' if results['time_horizon'] > 1 else ''}"
        st.markdown(
            f"""
            - **VaR ({results['confidence_level']*100:.0f}%)**: With {results['confidence_level']*100:.0f}% confidence, 
              the portfolio will not lose more than **${abs(var_dollar):,.0f}** 
              ({abs(results['var'])*100:.2f}%) over **{time_period}**.
            
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
        
        # Calculate actual portfolio beta from real market data
        try:
            with st.spinner("Calculating portfolio beta..."):
                data_provider = MarketDataProvider()
                
                # Fetch S&P 500 as market benchmark
                market_df = data_provider.get_stock_data(
                    ticker="^GSPC",  # S&P 500
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                if not market_df.empty:
                    market_returns = market_df['Close'].pct_change().dropna()
                    
                    # Align portfolio and market returns
                    min_length = min(len(results["portfolio_returns"]), len(market_returns))
                    portfolio_rets = results["portfolio_returns"].values[:min_length]
                    market_rets = market_returns.values[:min_length]
                    
                    # Calculate beta: cov(portfolio, market) / var(market)
                    covariance = np.cov(portfolio_rets, market_rets)[0, 1]
                    market_variance = np.var(market_rets)
                    calculated_beta = covariance / market_variance if market_variance > 0 else 1.0
                else:
                    calculated_beta = 1.0  # Fallback if market data unavailable
        except Exception:
            calculated_beta = 1.0  # Fallback on error
        
        # Display calculated beta
        st.info(f"📊 **Portfolio Beta**: {calculated_beta:.2f} (calculated from S&P 500 correlation)")
        
        # Define stress scenarios
        scenarios = {
            "Market Crash (-20%)": -0.20,
            "Volatility Spike (+50%)": 0.15,
            "2008 Financial Crisis": -0.35,
            "COVID-19 Crash": -0.30,
            "Black Monday 1987": -0.22,
            "Moderate Correction (-10%)": -0.10,
        }
        
        # Calculate impacts using actual portfolio beta
        scenario_impacts = {}
        
        for scenario_name, market_shock in scenarios.items():
            # Use calculated beta from real portfolio data
            portfolio_impact = market_shock * calculated_beta
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
                value=float(np.clip(calculated_beta, 0.5, 2.0)),  # Use calculated beta as default
                step=0.1,
                help=f"Calculated beta: {calculated_beta:.2f}",
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
            interpretation.append("⚠️ **Negative skew**: Portfolio has asymmetric downside risk (fat left tail)")
        elif skewness > 0.5:
            interpretation.append("✅ **Positive skew**: Portfolio has asymmetric upside potential")
        else:
            interpretation.append("ℹ️ **Near-symmetric**: Distribution is relatively balanced")
        
        if kurtosis > 3:
            interpretation.append(f"⚠️ **High kurtosis ({kurtosis:.1f})**: More extreme events than normal distribution predicts")
        elif kurtosis < -1:
            interpretation.append(f"ℹ️ **Low kurtosis ({kurtosis:.1f})**: Fewer extreme events than normal distribution")
        else:
            interpretation.append(f"ℹ️ **Normal kurtosis ({kurtosis:.1f})**: Similar to normal distribution")
        
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

# ============================================================================
# Tab 4: Real-Time Trader Stress Monitoring
# ============================================================================
with tab4:
    st.header("🧠 Real-Time Trader Stress Monitoring")
    
    st.warning("""
    ⚠️ **NON-FINANCE TOOL** - This is a personal wellness monitoring feature.
    
    This tool uses computer vision to detect stress levels based on facial expressions 
    and micro-movements. It is **NOT** a market stress indicator.
    
    **Use Case**: Monitor your own stress levels during trading sessions to maintain 
    emotional discipline and prevent stress-driven decision making.
    
    **Requirements**: Webcam access and proper lighting.
    """)
    
    st.markdown("""
    ### How It Works
    
    The stress detection algorithm analyzes:
    - **Facial Landmarks**: Eyebrow position, lip tension, facial symmetry
    - **Micro-expressions**: Rapid involuntary expressions indicating stress
    - **Blink Rate**: Elevated blinking often correlates with cognitive load
    - **Head Movement**: Frequent nodding/shaking can indicate anxiety
    
    ### Stress Levels
    - 🟢 **Calm** (Score < 0.08): Relaxed state, optimal for decision-making
    - 🟡 **Mild** (Score 0.08-0.15): Slightly elevated, maintain awareness
    - 🔴 **High** (Score > 0.15): Significant stress, consider taking a break
    """)
    
    st.markdown("---")
    
    st.info("""
    🚧 **Implementation Note**
    
    This feature requires:
    1. **MediaPipe Face Landmarker** - Computer vision model for facial tracking
    2. **OpenCV** - Video capture and processing
    3. **Webcam Access** - Browser permissions required
    4. **face_landmarker.task** model file
    
    Due to browser security restrictions and model dependencies, this feature 
    is best run as a standalone application rather than in Streamlit.
    
    **To use this feature:**
    ```bash
    cd Real-Time-Stress-Detection-main/app
    python main.py
    ```
    
    The standalone app provides:
    - Real-time video feed with stress overlay
    - Stress score meter (0-1 scale)
    - Individual metric breakdowns (eyebrow raise, lip tension, etc.)
    - Stress level classification with color coding
    - Continuous monitoring during trading sessions
    """)
    
    # Simulated stress metrics for demonstration
    st.markdown("---")
    st.subheader("📊 Simulated Stress Metrics (Demo)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        demo_stress = st.slider(
            "Demo Stress Score",
            min_value=0.0,
            max_value=1.0,
            value=0.12,
            step=0.01,
            help="Adjust to see how stress levels would be classified"
        )
    
    with col2:
        if demo_stress < 0.08:
            stress_level = "Calm"
            stress_color = "green"
            emoji = "🟢"
        elif demo_stress < 0.15:
            stress_level = "Mild"
            stress_color = "orange"
            emoji = "🟡"
        else:
            stress_level = "High"
            stress_color = "red"
            emoji = "🔴"
        
        st.metric(
            "Stress Level",
            f"{emoji} {stress_level}",
            delta=f"Score: {demo_stress:.3f}"
        )
    
    with col3:
        # Calculate recommendation
        if demo_stress < 0.08:
            recommendation = "👍 Optimal trading state"
        elif demo_stress < 0.15:
            recommendation = "⚠️ Monitor closely"
        else:
            recommendation = "🛑 Consider a break"
        
        st.info(f"**Recommendation**: {recommendation}")
    
    # Simulated component metrics
    st.subheader("📊 Component Metrics (Demo)")
    
    # Generate simulated values based on overall stress
    import random
    random.seed(int(demo_stress * 1000))
    
    eyebrow_raise = demo_stress * 0.6 + random.uniform(0, 0.1)
    lip_tension = demo_stress * 0.8 + random.uniform(0, 0.1)
    head_movement = demo_stress * 0.4 + random.uniform(0, 0.05)
    facial_symmetry = demo_stress * 0.2 + random.uniform(0, 0.05)
    blink_rate = int((demo_stress * 30) + random.randint(10, 25))  # blinks per minute
    
    col1a, col2a, col3a, col4a, col5a = st.columns(5)
    
    with col1a:
        st.metric("Eyebrow Raise", f"{eyebrow_raise:.3f}")
    
    with col2a:
        st.metric("Lip Tension", f"{lip_tension:.3f}")
    
    with col3a:
        st.metric("Head Movement", f"{head_movement:.3f}")
    
    with col4a:
        st.metric("Asymmetry", f"{facial_symmetry:.3f}")
    
    with col5a:
        st.metric("Blink Rate", f"{blink_rate}/min")
    
    # Visualization
    st.subheader("📊 Stress Components Breakdown")
    
    components_data = pd.DataFrame({
        'Metric': ['Eyebrow Raise', 'Lip Tension', 'Head Movement', 'Asymmetry', 'Blink Rate (norm)'],
        'Value': [eyebrow_raise, lip_tension, head_movement, facial_symmetry, blink_rate / 60]
    })
    
    fig_components = go.Figure(data=[
        go.Bar(
            x=components_data['Metric'],
            y=components_data['Value'],
            marker_color=['#00f2fe', '#f6416c', '#43e97b', '#ffbd39', '#f7971e']
        )
    ])
    
    fig_components.update_layout(
        template='plotly_dark',
        height=300,
        yaxis_title='Stress Contribution',
        xaxis_title='Component',
        showlegend=False
    )
    
    st.plotly_chart(fig_components, use_container_width=True)
    
    # Tips for stress management
    st.markdown("---")
    st.subheader("🧘 Stress Management Tips for Traders")
    
    col1b, col2b = st.columns(2)
    
    with col1b:
        st.markdown("""
        **During Trading:**
        - 🚨 Take breaks every 60-90 minutes
        - 💧 Stay hydrated
        - 🧘 Practice deep breathing
        - 👁️ Look away from screen (20-20-20 rule)
        - 🚫 Avoid revenge trading when stressed
        """)
    
    with col2b:
        st.markdown("""
        **Long-term Strategies:**
        - 🏋️ Regular exercise
        - 😴 Adequate sleep (7-8 hours)
        - 🧘 Meditation or mindfulness practice
        - 📝 Trading journal to track emotional state
        - 🔄 Stick to trading plan regardless of emotions
        """)

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
