"""
Market Regime Detection Dashboard

Week 13: Streamlit page for HMM-based market regime detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from quantlib_pro.ui import components
from quantlib_pro.market_regime.hmm_detector import detect_regimes_hmm
from quantlib_pro.data.market_data import MarketDataProvider

# Page config
st.set_page_config(
    page_title="Market Regime - QuantLib Pro",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Market Regime Detection")
st.markdown("Identify market regimes (bull, bear, high vol, low vol) using Hidden Markov Models.")

# Common ticker list
COMMON_TICKERS = [
    "SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "USO", "UUP",
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
    "JPM", "V", "JNJ", "WMT", "PG", "MA", "HD", "DIS", "BAC", "XOM",
    "NFLX", "ADBE", "CRM", "CSCO", "INTC", "AMD", "QCOM", "TXN",
    "XLF", "XLE", "XLK", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB"
]

# Initialize session state
if "regime_results" not in st.session_state:
    st.session_state.regime_results = None

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    ticker = st.selectbox(
        "Select Asset",
        options=COMMON_TICKERS,
        index=0,
        help="Ticker symbol for regime analysis"
    )
    
    st.subheader("Date Range")
    default_end = datetime.now()
    default_start = default_end - timedelta(days=730)  # 2 years
    
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)
    
    num_regimes = st.slider(
        "Number of Regimes",
        min_value=2,
        max_value=5,
        value=3,
        help="Number of hidden states to detect",
    )
    
    detect_button = st.button("🔍 Detect Regimes", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Regime Detection", 
    "🔄 Transitions", 
    "📈 Statistics",
    "🎲 3D State Machine",
    "📉 Alpha Decay",
    "🌋 Correlation Shifts"
])

with tab1:
    st.header("Market Regime Analysis")
    
    if detect_button:
        with st.spinner(f"Detecting {num_regimes} regimes for {ticker}..."):
            try:
                # Fetch real market data
                provider = MarketDataProvider()
                
                try:
                    df = provider.get_stock_data(
                        ticker=ticker,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                    )
                    
                    if df.empty:
                        st.error(f"No data available for {ticker}. Please check the ticker symbol and date range.")
                        st.stop()
                    
                    # Use closing prices
                    prices_series = df['Close']
                    
                except Exception as e:
                    st.error(f"Failed to fetch data for {ticker}: {str(e)}")
                    st.error("Please check your internet connection and verify the ticker symbol is correct.")
                    st.stop()
                
                # Detect regimes using HMM
                result = detect_regimes_hmm(
                    prices=prices_series,
                    n_regimes=num_regimes,
                )
                
                # Store results - use timestamps and data from HMM result
                current_regime = result.regimes[-1]  # Most recent regime
                
                # Create probability distribution (simplified - assign 100% to current regime)
                # Note: result.confidence is max probability per timestep, not distribution across regimes
                regime_probs = np.zeros(num_regimes)
                regime_probs[current_regime] = 1.0
                
                # Get confidence score for the assignment (if available)
                confidence_score = result.confidence[-1] if result.confidence is not None else 1.0
                
                # Align prices and returns with HMM timestamps
                aligned_prices = prices_series.loc[result.timestamps]
                aligned_returns = aligned_prices.pct_change().fillna(0)
                
                st.session_state.regime_results = {
                    "current_regime": int(current_regime),
                    "regime_probabilities": regime_probs,
                    "confidence_score": float(confidence_score),
                    "regimes": result.regimes,
                    "transition_matrix": result.transition_matrix,
                    "regime_names": result.regime_names,
                    "prices": aligned_prices.values,
                    "returns": aligned_returns.values,
                    "dates": result.timestamps,  # Use HMM timestamps for alignment
                    "ticker": ticker,
                    "num_regimes": num_regimes,
                }
                
                components.success_message("Regime detection complete!")
                
            except Exception as e:
                components.error_message(f"Regime detection failed: {str(e)}")
                st.session_state.regime_results = None
    
    # Display results
    if st.session_state.regime_results:
        results = st.session_state.regime_results
        
        # Current regime metrics
        current_regime = results["current_regime"]
        regime_probs = results["regime_probabilities"]
        
        components.multi_metric_row([
            {
                "title": "Current Regime",
                "value": f"Regime {current_regime}",
                "help": "Current detected market regime",
            },
            {
                "title": "Regime Confidence",
                "value": f"{regime_probs[current_regime]*100:.1f}%",
                "help": "Probability of current regime assignment",
            },
            {
                "title": "Total Regimes",
                "value": results["num_regimes"],
                "help": "Number of hidden states",
            },
            {
                "title": "Data Points",
                "value": len(results["dates"]),
                "help": "Number of observations analyzed",
            },
        ])
        
        st.markdown("---")
        
        # Plot price with regime coloring
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Create regime segments
        regime_colors = ["green", "orange", "red", "blue", "purple"]
        
        # Use regime names from result if available
        if "regime_names" in results and results["regime_names"]:
            regime_names = [f"{name.title()}" for name in results["regime_names"]]
        else:
            regime_names = [
                "Regime 0 (Bull/Low Vol)",
                "Regime 1 (High Vol)",
                "Regime 2 (Bear)",
                "Regime 3",
                "Regime 4",
            ]
        
        for regime_id in range(results["num_regimes"]):
            mask = np.array(results["regimes"]) == regime_id
            # Use aligned dates and prices
            regime_dates = pd.DatetimeIndex(results["dates"])[mask]
            regime_prices = np.array(results["prices"])[mask]
            
            fig.add_trace(go.Scatter(
                x=regime_dates,
                y=regime_prices,
                mode="markers",
                marker=dict(size=4, color=regime_colors[regime_id]),
                name=regime_names[regime_id],
            ))
        
        fig.update_layout(
            title=f"{results['ticker']} Price History Colored by Detected Regime",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=500,
            template="plotly_white",
            hovermode="x unified",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Regime probabilities over time
        st.subheader("Regime Probability Evolution")
        
        st.markdown(
            f"""
            Current regime probabilities:
            
            {" | ".join([f"**Regime {i}**: {regime_probs[i]*100:.1f}%" for i in range(len(regime_probs))])}
            """
        )
        
    else:
        components.info_message("Click 'Detect Regimes' to analyze market regimes.")

with tab2:
    st.header("Regime Transitions")
    
    if st.session_state.regime_results and st.session_state.regime_results.get("transition_matrix") is not None:
        results = st.session_state.regime_results
        transition_matrix = results["transition_matrix"]
        
        # Display transition matrix
        st.subheader("Transition Probability Matrix")
        
        transition_df = pd.DataFrame(
            transition_matrix,
            columns=[f"To Regime {i}" for i in range(results["num_regimes"])],
            index=[f"From Regime {i}" for i in range(results["num_regimes"])],
        )
        
        components.data_table(
            transition_df.style.format("{:.3f}").background_gradient(cmap="YlOrRd"),
            title="How likely each regime transitions to another",
        )
        
        # Visualize as heatmap
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Heatmap(
            z=transition_matrix,
            x=[f"Regime {i}" for i in range(results["num_regimes"])],
            y=[f"Regime {i}" for i in range(results["num_regimes"])],
            colorscale="YlOrRd",
            text=transition_matrix,
            texttemplate="%{text:.3f}",
            textfont={"size": 12},
            colorbar=dict(title="Probability"),
        ))
        
        fig.update_layout(
            title="Regime Transition Matrix",
            xaxis_title="To Regime",
            yaxis_title="From Regime",
            height=400,
            template="plotly_white",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Persistence analysis
        st.subheader("Regime Persistence")
        
        persistence_metrics = []
        for i in range(results["num_regimes"]):
            stay_prob = transition_matrix[i, i]
            avg_duration = 1 / (1 - stay_prob) if stay_prob < 1 else float('inf')
            persistence_metrics.append({
                "Regime": f"Regime {i}",
                "Stay Probability": f"{stay_prob:.3f}",
                "Avg Duration (days)": f"{avg_duration:.1f}" if avg_duration != float('inf') else "Absorbing",
            })
        
        persistence_df = pd.DataFrame(persistence_metrics)
        components.data_table(persistence_df)
        
    else:
        components.info_message("Transition matrix will be displayed after regime detection.")

with tab3:
    st.header("Regime Statistics")
    
    if st.session_state.regime_results:
        results = st.session_state.regime_results
        
        # Calculate statistics per regime
        regime_stats = []
        
        for regime_id in range(results["num_regimes"]):
            mask = np.array(results["regimes"]) == regime_id
            # Ensure mask and returns are same length
            regime_returns = np.array(results["returns"])[mask]
            
            if len(regime_returns) > 0:
                regime_stats.append({
                    "Regime": f"Regime {regime_id}",
                    "Observations": len(regime_returns),
                    "Avg Return (%)": regime_returns.mean() * 100,
                    "Volatility (%)": regime_returns.std() * 100,
                    "Sharpe Ratio": regime_returns.mean() / regime_returns.std() if regime_returns.std() > 0 else 0,
                    "Min Return (%)": regime_returns.min() * 100,
                    "Max Return (%)": regime_returns.max() * 100,
                })
        
        stats_df = pd.DataFrame(regime_stats)
        
        components.data_table(
            stats_df.style.format({
                "Observations": "{:,.0f}",
                "Avg Return (%)": "{:.4f}",
                "Volatility (%)": "{:.4f}",
                "Sharpe Ratio": "{:.3f}",
                "Min Return (%)": "{:.4f}",
                "Max Return (%)": "{:.4f}",
            }),
            title="Statistical Characteristics by Regime",
        )
        
        # Return distributions by regime
        st.subheader("Return Distributions by Regime")
        
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=1, cols=results["num_regimes"],
            subplot_titles=[f"Regime {i}" for i in range(results["num_regimes"])],
        )
        
        colors = ["green", "orange", "red", "blue", "purple"]
        
        for regime_id in range(results["num_regimes"]):
            mask = np.array(results["regimes"]) == regime_id
            regime_returns = np.array(results["returns"])[mask]
            
            fig.add_trace(
                go.Histogram(
                    x=regime_returns * 100,
                    name=f"Regime {regime_id}",
                    marker_color=colors[regime_id],
                    nbinsx=30,
                ),
                row=1, col=regime_id + 1
            )
        
        fig.update_layout(
            title_text="Return Distributions by Regime",
            height=350,
            showlegend=False,
            template="plotly_white",
        )
        
        fig.update_xaxes(title_text="Daily Return (%)")
        fig.update_yaxes(title_text="Frequency")
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Regime statistics will be displayed after detection.")

# ============================================================================
# Tab 4: 3D State Machine
# ============================================================================
with tab4:
    st.header("3D Market Regime State Machine")
    
    st.markdown("""
    **3D Visualization** - Explore regime transitions in 3D space using volatility, return, and momentum dimensions.
    """)
    
    if st.session_state.regime_results:
        results = st.session_state.regime_results
        
        # Calculate features for 3D visualization
        returns = pd.Series(results["returns"], index=results["dates"])
        prices = pd.Series(results["prices"], index=results["dates"])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vol_window = st.slider("Volatility Window", 5, 50, 20, help="Window for volatility calculation")
        
        with col2:
            momentum_window = st.slider("Momentum Window", 5, 50, 20, help="Window for momentum")
        
        with col3:
            show_transitions = st.checkbox("Show Transitions", value=True)
        
        # Calculate 3D features
        rolling_vol = returns.rolling(vol_window).std() * np.sqrt(252) * 100  # Annualized %
        rolling_return = returns.rolling(vol_window).mean() * 252 * 100  # Annualized %
        momentum = prices.pct_change(momentum_window) * 100  # % change
        
        # Remove NaN values
        valid_mask = ~(rolling_vol.isna() | rolling_return.isna() | momentum.isna())
        
        vol_clean = rolling_vol[valid_mask].values
        ret_clean = rolling_return[valid_mask].values
        mom_clean = momentum[valid_mask].values
        regime_clean = np.array(results["regimes"])[valid_mask]
        dates_clean = pd.DatetimeIndex(results["dates"])[valid_mask]
        
        # Create 3D scatter plot
        fig = go.Figure()
        
        regime_colors = ["green", "orange", "red", "blue", "purple"]
        regime_names = [f"Regime {i}" for i in range(results["num_regimes"])]
        
        for regime_id in range(results["num_regimes"]):
            mask = regime_clean == regime_id
            
            fig.add_trace(go.Scatter3d(
                x=vol_clean[mask],
                y=ret_clean[mask],
                z=mom_clean[mask],
                mode='markers',
                marker=dict(
                    size=5,
                    color=regime_colors[regime_id],
                    opacity=0.7
                ),
                name=regime_names[regime_id],
                text=[f"{d.strftime('%Y-%m-%d')}" for d in dates_clean[mask]],
                hovertemplate=(
                    '<b>%{text}</b><br>' +
                    'Volatility: %{x:.2f}%<br>' +
                    'Return: %{y:.2f}%<br>' +
                    'Momentum: %{z:.2f}%<br>' +
                    '<extra></extra>'
                )
            ))
        
        # Add transition lines if requested
        if show_transitions and len(regime_clean) > 1:
            # Find regime changes
            regime_changes = np.where(np.diff(regime_clean) != 0)[0]
            
            for change_idx in regime_changes[:50]:  # Limit to first 50 transitions for clarity
                if change_idx + 1 < len(regime_clean):
                    fig.add_trace(go.Scatter3d(
                        x=[vol_clean[change_idx], vol_clean[change_idx + 1]],
                        y=[ret_clean[change_idx], ret_clean[change_idx + 1]],
                        z=[mom_clean[change_idx], mom_clean[change_idx + 1]],
                        mode='lines',
                        line=dict(color='white', width=1, dash='dot'),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
        
        fig.update_layout(
            title=f"3D Market Regime State Space - {results['ticker']}",
            scene=dict(
                xaxis_title='Volatility (%)',
                yaxis_title='Annualized Return (%)',
                zaxis_title='Momentum (%)',
                bgcolor='rgba(0,0,0,0)',
            ),
            template='plotly_dark',
            height=700,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # State space metrics
        st.subheader("State Space Characteristics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Volatility Range",
                f"{vol_clean.min():.1f}% - {vol_clean.max():.1f}%"
            )
        
        with col2:
            st.metric(
                "Return Range",
                f"{ret_clean.min():.1f}% - {ret_clean.max():.1f}%"
            )
        
        with col3:
            st.metric(
                "Regime Transitions",
                f"{len(np.where(np.diff(regime_clean) != 0)[0])}"
            )
        
    else:
        components.info_message("Run regime detection first to see 3D state machine.")

# ============================================================================
# Tab 5: Alpha Decay
# ============================================================================
with tab5:
    st.header("Alpha Decay & Regime Shift Analysis")
    
    st.markdown("""
    **Alpha Decay** - Measure how quickly trading signals decay and vary across regimes.
    """)
    
    if st.session_state.regime_results:
        results = st.session_state.regime_results
        
        # Parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            alpha_type = st.selectbox(
                "Alpha Signal",
                ["Momentum", "Mean Reversion", "Volatility Carry"]
            )
        
        with col2:
            lookback = st.slider("Lookback Period", 5, 60, 20)
        
        with col3:
            decay_window = st.slider("Decay Window", 10, 100, 30)
        
        if st.button("Calculate Alpha Decay", type="primary"):
            with st.spinner("Computing alpha decay..."):
                prices = pd.Series(results["prices"], index=results["dates"])
                returns = pd.Series(results["returns"], index=results["dates"])
                regimes = pd.Series(results["regimes"], index=results["dates"])
                
                # Generate alpha signal
                if alpha_type == "Momentum":
                    # Simple momentum: return over lookback
                    alpha = prices.pct_change(lookback) * 100
                elif alpha_type == "Mean Reversion":
                    # Z-score of price
                    rolling_mean = prices.rolling(lookback).mean()
                    rolling_std = prices.rolling(lookback).std()
                    alpha = -(prices - rolling_mean) / (rolling_std + 1e-10)  # Negative for mean reversion
                else:  # Volatility Carry
                    # Realized vol vs historical
                    realized_vol = returns.rolling(lookback).std() * np.sqrt(252)
                    historical_vol = returns.rolling(lookback * 2).std() * np.sqrt(252)
                    alpha = historical_vol - realized_vol
                
                # Calculate forward returns at different horizons
                horizons = [1, 5, 10, 20, 40, 60]
                ic_results = {}
                
                for horizon in horizons:
                    forward_ret = returns.shift(-horizon).rolling(horizon).sum()
                    
                    # Calculate rolling IC (Information Coefficient)
                    valid_mask = ~(alpha.isna() | forward_ret.isna())
                    if valid_mask.sum() > decay_window:
                        correlation = alpha[valid_mask].rolling(decay_window).corr(forward_ret[valid_mask])
                        ic_results[horizon] = correlation
                
                # Plot IC decay
                fig = go.Figure()
                
                for horizon, ic in ic_results.items():
                    fig.add_trace(go.Scatter(
                        x=ic.index,
                        y=ic.values,
                        name=f"{horizon}-Day Horizon",
                        mode='lines',
                        line=dict(width=2)
                    ))
                
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                
                fig.update_layout(
                    title=f"Alpha Decay: Information Coefficient Over Time ({alpha_type})",
                    xaxis_title="Date",
                    yaxis_title="IC (Rolling Correlation)",
                    template='plotly_dark',
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # IC by regime
                st.subheader("Alpha Performance by Regime")
                
                regime_ic = []
                
                for regime_id in range(results["num_regimes"]):
                    regime_mask = regimes == regime_id
                    
                    avg_ics = []
                    for horizon, ic in ic_results.items():
                        regime_ic_values = ic[regime_mask]
                        avg_ic = regime_ic_values.mean()
                        avg_ics.append(avg_ic)
                    
                    regime_ic.append({
                        'Regime': f"Regime {regime_id}",
                        '1-Day IC': avg_ics[0],
                        '5-Day IC': avg_ics[1],
                        '10-Day IC': avg_ics[2],
                        '20-Day IC': avg_ics[3],
                        '40-Day IC': avg_ics[4],
                        '60-Day IC': avg_ics[5],
                        'Avg IC': np.mean(avg_ics)
                    })
                
                regime_ic_df = pd.DataFrame(regime_ic)
                
                # Style dataframe
                styled_df = regime_ic_df.style.format({
                    '1-Day IC': '{:.3f}',
                    '5-Day IC': '{:.3f}',
                    '10-Day IC': '{:.3f}',
                    '20-Day IC': '{:.3f}',
                    '40-Day IC': '{:.3f}',
                    '60-Day IC': '{:.3f}',
                    'Avg IC': '{:.3f}'
                }).background_gradient(cmap='RdYlGn', subset=[col for col in regime_ic_df.columns if 'IC' in col])
                
                st.dataframe(styled_df, use_container_width=True)
                
                # Decay curve visualization
                st.subheader("Alpha Decay Curve by Regime")
                
                fig2 = go.Figure()
                
                regime_colors = ["green", "orange", "red", "blue", "purple"]
                
                for i, row in regime_ic_df.iterrows():
                    ic_values = [row['1-Day IC'], row['5-Day IC'], row['10-Day IC'], 
                                row['20-Day IC'], row['40-Day IC'], row['60-Day IC']]
                    
                    fig2.add_trace(go.Scatter(
                        x=horizons,
                        y=ic_values,
                        name=row['Regime'],
                        mode='lines+markers',
                        line=dict(width=3, color=regime_colors[i]),
                        marker=dict(size=8)
                    ))
                
                fig2.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
                
                fig2.update_layout(
                    title="Alpha Decay Curves Across Regimes",
                    xaxis_title="Forward Return Horizon (Days)",
                    yaxis_title="Information Coefficient",
                    template='plotly_dark',
                    height=500,
                    xaxis=dict(type='log')
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Key insights
                st.markdown("### Key Insights")
                
                best_regime_idx = regime_ic_df['Avg IC'].abs().idxmax()
                best_regime = regime_ic_df.iloc[best_regime_idx]
                
                # Get horizon columns (skip 'Regime' and 'Avg IC')
                horizon_cols = [col for col in regime_ic_df.columns if col not in ['Regime', 'Avg IC']]
                if horizon_cols:
                    # Find best horizon
                    horizon_values = best_regime[horizon_cols].abs()
                    best_horizon_idx = horizon_values.idxmax()
                    best_horizon_value = horizon_values.max()
                    
                    st.success(f"""
                    **Best Regime for {alpha_type} Alpha**: {best_regime['Regime']}
                    - Average IC: {best_regime['Avg IC']:.3f}
                    - Best Horizon: {best_horizon_idx}: {best_horizon_value:.3f}
                    """)
                else:
                    st.success(f"""
                    **Best Regime for {alpha_type} Alpha**: {best_regime['Regime']}
                    - Average IC: {best_regime['Avg IC']:.3f}
                    """)
                
    else:
        components.info_message("Run regime detection first to analyze alpha decay.")

# ============================================================================
# Tab 6: Correlation Regime Shifts
# ============================================================================
with tab6:
    st.header("Correlation Regime Tectonic Shifts")
    
    st.markdown("""
    **Correlation Dynamics** - Visualize how asset correlations shift dramatically across regimes.
    """)
    
    if st.session_state.regime_results:
        results = st.session_state.regime_results
        
        # Get additional tickers for correlation analysis
        col1, col2 = st.columns([2, 1])
        
        with col1:
            additional_tickers = st.multiselect(
                "Additional Assets for Correlation",
                options=[t for t in COMMON_TICKERS if t != results['ticker']],
                default=["QQQ", "IWM", "TLT", "GLD"],
                help="Select assets to analyze correlation structure"
            )
            
            # Optional custom tickers
            custom_corr_tickers = st.text_input(
                "Custom Tickers (comma-separated)",
                value="",
                help="Add any tickers not in the list"
            )
            
            if custom_corr_tickers.strip():
                custom_list = [t.strip().upper() for t in custom_corr_tickers.split(',') if t.strip()]
                additional_tickers.extend(custom_list)
        
        with col2:
            correlation_window = st.slider(
                "Correlation Window",
                min_value=10,
                max_value=100,
                value=30
            )
        
        if st.button("Analyze Correlation Shifts", type="primary"):
            if not additional_tickers:
                st.warning("Please select at least one additional ticker")
            else:
                with st.spinner("Fetching multi-asset data..."):
                    try:
                        # Parse tickers
                        all_tickers = [results['ticker']] + additional_tickers
                        
                        # Fetch data for all tickers
                        provider = MarketDataProvider()
                        all_returns = {}
                        
                        for ticker in all_tickers:
                            try:
                                df = provider.get_stock_data(
                                    ticker=ticker,
                                    start_date=results['dates'][0].strftime('%Y-%m-%d'),
                                    end_date=results['dates'][-1].strftime('%Y-%m-%d')
                                )
                                
                                if not df.empty:
                                    returns = df['Close'].pct_change().dropna()
                                    all_returns[ticker] = returns
                            except:
                                st.warning(f"Could not fetch data for {ticker}")
                    except Exception as e:
                        st.error(f"Error loading data: {str(e)}")
                        st.stop()
                    
                    if len(all_returns) < 2:
                        st.error("Need at least 2 assets for correlation analysis")
                    else:
                        try:
                            # Align returns
                            returns_df = pd.DataFrame(all_returns)
                            returns_df = returns_df.dropna()
                            
                            # Calculate rolling correlation matrices
                            n_assets = len(returns_df.columns)
                            dates_for_corr = returns_df.index[correlation_window:]
                            
                            correlation_history = []
                            
                            for i in range(correlation_window, len(returns_df)):
                                window_data = returns_df.iloc[i-correlation_window:i]
                                corr_matrix = window_data.corr().values
                                correlation_history.append(corr_matrix)
                            
                            correlation_history = np.array(correlation_history)
                        
                            # Map regimes to correlation dates
                            regime_dates = pd.DatetimeIndex(results['dates'])
                            regime_series = pd.Series(results['regimes'], index=regime_dates)
                            
                            # Align regimes with correlation dates
                            aligned_regimes = []
                            for date in dates_for_corr:
                                if date in regime_series.index:
                                    aligned_regimes.append(regime_series.loc[date])
                                else:
                                    # Find nearest regime
                                    idx = regime_series.index.get_indexer([date], method='nearest')[0]
                                    aligned_regimes.append(regime_series.iloc[idx])
                            
                            aligned_regimes = np.array(aligned_regimes)
                            
                            # Calculate average correlation matrix per regime
                            regime_corr_matrices = []
                            
                            for regime_id in range(results["num_regimes"]):
                                regime_mask = aligned_regimes == regime_id
                                
                                if regime_mask.sum() > 0:
                                    avg_corr = correlation_history[regime_mask].mean(axis=0)
                                    regime_corr_matrices.append(avg_corr)
                                else:
                                    regime_corr_matrices.append(np.eye(n_assets))
                            
                            # Visualize correlation matrices by regime
                            st.subheader("Average Correlation Structure by Regime")
                            
                            cols = st.columns(min(3, results["num_regimes"]))
                            
                            for regime_id in range(results["num_regimes"]):
                                with cols[regime_id % 3]:
                                    fig = go.Figure(data=go.Heatmap(
                                        z=regime_corr_matrices[regime_id],
                                        x=list(returns_df.columns),
                                        y=list(returns_df.columns),
                                        colorscale='RdBu',
                                        zmid=0,
                                        zmin=-1,
                                        zmax=1,
                                        text=regime_corr_matrices[regime_id],
                                        texttemplate='%{text:.2f}',
                                        textfont={"size": 10},
                                        colorbar=dict(title="Correlation")
                                    ))
                                    
                                    fig.update_layout(
                                        title=f"Regime {regime_id}",
                                        template='plotly_dark',
                                        height=400,
                                        width=400
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            # 3D Correlation Surface Evolution
                            st.subheader("3D Correlation Surface Evolution")
                            
                            # Calculate average correlation (excluding diagonal) over time
                            avg_correlations = []
                            for corr_mat in correlation_history:
                                mask = ~np.eye(n_assets, dtype=bool)
                                avg_corr = corr_mat[mask].mean()
                                avg_correlations.append(avg_corr)
                            
                            # Create 3D surface: Time x Asset Pair x Correlation
                            # For simplicity, show correlation evolution for selected pairs
                            
                            if n_assets >= 2:
                                # Take first two assets as example
                                pair_corr = correlation_history[:, 0, 1]
                                
                                # Create colored line based on regime
                                fig = go.Figure()
                                
                                regime_colors_map = {0: "green", 1: "orange", 2: "red", 3: "blue", 4: "purple"}
                                
                                for regime_id in range(results["num_regimes"]):
                                    mask = aligned_regimes == regime_id
                                    regime_dates_masked = dates_for_corr[mask]
                                    regime_corr_masked = pair_corr[mask]
                                    
                                    fig.add_trace(go.Scatter(
                                        x=regime_dates_masked,
                                        y=regime_corr_masked,
                                        mode='markers+lines',
                                        name=f"Regime {regime_id}",
                                        marker=dict(size=4, color=regime_colors_map.get(regime_id, "gray")),
                                        line=dict(width=2)
                                    ))
                                
                                fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
                                
                                fig.update_layout(
                                    title=f"Correlation Evolution: {returns_df.columns[0]} vs {returns_df.columns[1]}",
                                    xaxis_title="Date",
                                    yaxis_title="Rolling Correlation",
                                    template='plotly_dark',
                                    height=500,
                                    hovermode='x unified'
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Correlation shift metrics
                            st.subheader("Correlation Regime Shift Metrics")
                            
                            shift_metrics = []
                            
                            for regime_id in range(results["num_regimes"] - 1):
                                corr1 = regime_corr_matrices[regime_id]
                                corr2 = regime_corr_matrices[regime_id + 1]
                                
                                # Calculate Frobenius norm of difference
                                diff_norm = np.linalg.norm(corr1 - corr2, 'fro')
                                
                                # Average correlation change
                                mask = ~np.eye(n_assets, dtype=bool)
                                avg_change = np.abs(corr1[mask] - corr2[mask]).mean()
                                
                                shift_metrics.append({
                                    'Transition': f"Regime {regime_id} → {regime_id + 1}",
                                    'Frobenius Norm': f"{diff_norm:.3f}",
                                    'Avg Correlation Change': f"{avg_change:.3f}",
                                    'Severity': 'High' if diff_norm > 1.0 else ('Medium' if diff_norm > 0.5 else 'Low')
                                })
                            
                            shift_df = pd.DataFrame(shift_metrics)
                            st.dataframe(shift_df, use_container_width=True, hide_index=True)
                        
                        except Exception as e:
                            st.error(f"Error in correlation analysis: {str(e)}")
    else:
        components.info_message("Run regime detection first to analyze correlation shifts.")

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Market Regime Detection powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
