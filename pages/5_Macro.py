"""
 Macro Analysis Dashboard

Comprehensive macro-economic analysis including:
- Macro regime detection
- Market sentiment analysis 
- Cross-asset correlation analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from quantlib_pro.ui import components
from quantlib_pro.macro.macro_regime import detect_macro_regime
from quantlib_pro.macro.sentiment import fear_greed_index, vix_sentiment_level
from quantlib_pro.macro.correlation import correlation_regime

# Page config
st.set_page_config(
    page_title="Macro Analysis",
    page_icon="🌍",
    layout="wide",
)

st.title("Macro Analysis")
st.markdown("Economic regime detection, sentiment analysis, and correlation analysis")

# Initialize session state
if "macro_results" not in st.session_state:
    st.session_state.macro_results = None

# Analysis parameters
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Macro Regime", "Sentiment Analysis", "Correlation Analysis"],
        help="Choose the type of macro analysis to perform"
    )

with col2:
    lookback_period = st.selectbox(
        "Analysis Period",
        ["1 Month", "3 Months", "6 Months", "1 Year"],
        index=2,
        help="Historical period for analysis"
    )

with col3:
    analyze_button = st.button("Analyze", type="primary", use_container_width=True)

# Create tabs for different analyses
tab1, tab2, tab3 = st.tabs([
    "Macro Regime",
    "Market Sentiment", 
    "Correlation Analysis"
])

# ============================================================================
# Tab 1: Macro Regime Analysis
# ============================================================================
with tab1:
    st.header("Economic Regime Detection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if analyze_button and analysis_type == "Macro Regime":
            with st.spinner("Analyzing macro-economic regime..."):
                try:
                    # Simulate economic indicators
                    gdp_growth = np.random.uniform(0.5, 4.0)
                    unemployment = np.random.uniform(3.5, 8.0)
                    pmi = np.random.normal(52.5, 2.0)
                    
                    # Generate correlation matrix and volatility for macro regime detection
                    symbols = ['SPY', 'TLT', 'GLD', 'VIX']
                    corr_data = np.random.RandomState(42).uniform(0.1, 0.9, (4, 4))
                    np.fill_diagonal(corr_data, 1.0)
                    corr_matrix = pd.DataFrame(corr_data, index=symbols, columns=symbols)
                    
                    volatility = pd.Series(np.random.RandomState(42).uniform(0.1, 0.4, 30), 
                                         name='volatility')
                    
                    # Detect macro regime
                    result = detect_macro_regime(
                        correlation_matrix=corr_matrix,
                        volatility_series=volatility,
                    )
                    
                    # Enhanced regime classification
                    regime_descriptions = {
                        "Risk On": "Growth-oriented environment, low volatility, risk assets outperforming",
                        "Risk Off": "Flight to quality, high volatility, safe haven assets preferred", 
                        "Sector Rotation": "Selective market with sector-specific opportunities",
                        "Crisis": "Market stress, high correlations, defensive positioning required",
                        "Recovery": "Early recovery phase, improving fundamentals",
                        "Normal": "Balanced market conditions with normal correlations"
                    }
                    
                    regime_name = result.value
                    regime_desc = regime_descriptions.get(regime_name, "Market regime based on correlation and volatility patterns")
                    
                    st.session_state.macro_results = {
                        "type": "macro_regime",
                        "current_regime": regime_name,
                        "regime_description": regime_desc,
                        "indicators": {
                            "gdp_growth": gdp_growth,
                            "unemployment": unemployment,
                            "pmi": pmi
                        },
                        "recession_probability": max(0.05, (unemployment - 4.0) / 20.0),
                        "gdp_growth": gdp_growth,
                        "unemployment": unemployment,
                        "pmi": pmi,
                        "correlation_matrix": corr_matrix,
                        "avg_volatility": volatility.mean()
                    }
                    
                    components.success_message("Macro regime analysis complete!")
                    
                except Exception as e:
                    components.error_message(f"Analysis failed: {str(e)}")
                    st.session_state.macro_results = None
    
        # Display macro regime results
        if st.session_state.macro_results and st.session_state.macro_results.get("type") == "macro_regime":
            results = st.session_state.macro_results
            
            st.success(f"**Current Regime: {results['current_regime']}**")
            st.markdown(f"**Analysis:** {results['regime_description']}")
            
            # Economic indicators chart
            indicators_data = pd.DataFrame([
                {"Indicator": "GDP Growth", "Value": results["gdp_growth"], "Unit": "%"},
                {"Indicator": "Unemployment", "Value": results["unemployment"], "Unit": "%"},
                {"Indicator": "PMI", "Value": results["pmi"], "Unit": "Index"},
                {"Indicator": "Avg Volatility", "Value": results["avg_volatility"] * 100, "Unit": "%"}
            ])
            
            fig = px.bar(
                indicators_data, 
                x="Indicator", 
                y="Value",
                title="Key Economic Indicators",
                text="Value"
            )
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if st.session_state.macro_results and st.session_state.macro_results.get("type") == "macro_regime":
            results = st.session_state.macro_results
            
            st.subheader("Key Metrics")
            
            st.metric(
                "GDP Growth",
                f"{results['gdp_growth']:.1f}%",
                delta=f"{'Above' if results['gdp_growth'] > 2.0 else 'Below'} trend"
            )
            
            st.metric(
                "Unemployment", 
                f"{results['unemployment']:.1f}%",
                delta=f"{'High' if results['unemployment'] > 5.0 else 'Low'}"
            )
            
            st.metric(
                "PMI",
                f"{results['pmi']:.1f}",
                delta=f"{'Expansion' if results['pmi'] > 50 else 'Contraction'}"
            )
            
            recession_prob = results['recession_probability'] * 100
            st.metric(
                "Recession Risk",
                f"{recession_prob:.1f}%",
                delta=f"{'High' if recession_prob > 25 else 'Low'} risk"
            )

# ============================================================================
# Tab 2: Market Sentiment Analysis
# ============================================================================
with tab2:
    st.header("Market Sentiment Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Fear & Greed Analysis")
        
        if analyze_button and analysis_type == "Sentiment Analysis":
            with st.spinner("Analyzing market sentiment..."):
                try:
                    # Simulate real-time sentiment data
                    vix_level = np.random.uniform(12, 35)
                    put_call_ratio = np.random.uniform(0.6, 1.4)
                    advance_decline = np.random.uniform(-0.2, 0.3)
                    new_high_low = np.random.uniform(-0.3, 0.4)
                    
                    # Calculate composite fear/greed index with proper parameters
                    fear_greed = fear_greed_index(
                        vix=vix_level,
                        put_call_ratio=put_call_ratio,
                        advance_decline=advance_decline,
                        new_high_low=new_high_low
                    )
                    
                    vix_sentiment = vix_sentiment_level(vix_level)
                    
                    # Determine overall sentiment regime
                    if fear_greed < 25:
                        sentiment_label = "Extreme Fear"
                        color = "red"
                        regime_description = "Market panic, oversold conditions, potential buying opportunity"
                    elif fear_greed < 45:
                        sentiment_label = "Fear"
                        color = "orange"
                        regime_description = "Cautious sentiment, defensive positioning dominates"
                    elif fear_greed < 55:
                        sentiment_label = "Neutral"
                        color = "gray"
                        regime_description = "Balanced sentiment, mixed signals from indicators"
                    elif fear_greed < 75:
                        sentiment_label = "Greed"
                        color = "lightgreen"
                        regime_description = "Optimistic sentiment, risk-on behavior prevalent"
                    else:
                        sentiment_label = "Extreme Greed"
                        color = "green"
                        regime_description = "Euphoric conditions, overbought, potential correction risk"
                    
                    # Store enhanced results
                    st.session_state.macro_results = {
                        "type": "sentiment_analysis",
                        "sentiment_regime": sentiment_label,
                        "fear_greed_index": fear_greed,
                        "vix_level": vix_level,
                        "vix_sentiment": vix_sentiment,
                        "put_call_ratio": put_call_ratio,
                        "advance_decline": advance_decline,
                        "new_high_low": new_high_low,
                        "regime_description": regime_description,
                        "color": color,
                        "market_stress": vix_level > 30,
                        "contrarian_signal": fear_greed < 20 or fear_greed > 80
                    }
                    
                    components.success_message("Sentiment analysis complete!")
                    
                except Exception as e:
                    components.error_message(f"Analysis failed: {str(e)}")
                    st.session_state.macro_results = None
        
        # Display sentiment analysis results  
        if st.session_state.macro_results and st.session_state.macro_results.get("type") == "sentiment_analysis":
            results = st.session_state.macro_results
            
            # Fear & Greed Gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=results["fear_greed_index"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Fear & Greed Index", 'font': {'size': 20}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1},
                    'bar': {'color': "darkblue", 'thickness': 0.3},
                    'steps': [
                        {'range': [0, 25], 'color': "darkred"},
                        {'range': [25, 45], 'color': "orange"},
                        {'range': [45, 55], 'color': "yellow"},
                        {'range': [55, 75], 'color': "lightgreen"},
                        {'range': [75, 100], 'color': "darkgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': results["fear_greed_index"]
                    }
                }
            ))
            
            fig.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
            # Regime description
            st.success(f"**{results['sentiment_regime']}**: {results['regime_description']}")
            
            # Component breakdown
            st.subheader("Sentiment Components")
            
            component_data = pd.DataFrame([
                {"Component": "VIX Level", "Value": results["vix_level"], "Signal": "Stress" if results["market_stress"] else "Calm"},
                {"Component": "Put/Call Ratio", "Value": results["put_call_ratio"], "Signal": "Bearish" if results["put_call_ratio"] > 1.0 else "Bullish"},
                {"Component": "Advance/Decline", "Value": results["advance_decline"] * 100, "Signal": "Positive" if results["advance_decline"] > 0 else "Negative"},
                {"Component": "New High/Low", "Value": results["new_high_low"] * 100, "Signal": "Bullish" if results["new_high_low"] > 0 else "Bearish"}
            ])
            
            st.dataframe(component_data, use_container_width=True, hide_index=True)
            
            # Contrarian signal alert
            if results['contrarian_signal']:
                if results['fear_greed_index'] < 20:
                    st.success("**Contrarian Buy Signal**: Extreme fear may present opportunity")
                else:
                    st.warning("**Contrarian Sell Signal**: Extreme greed suggests caution")
    
    with col2:
        st.subheader("Market Stress Indicators")
        
        if st.session_state.macro_results and st.session_state.macro_results.get("type") == "sentiment_analysis":
            results = st.session_state.macro_results
            
            # Key sentiment metrics
            st.metric(
                "Fear & Greed Index",
                f"{results['fear_greed_index']:.0f}/100",
                delta=results['sentiment_regime']
            )
            
            st.metric(
                "VIX Level",
                f"{results['vix_level']:.1f}",
                delta="High Stress" if results['market_stress'] else "Low Stress"
            )
            
            st.metric(
                "Put/Call Ratio", 
                f"{results['put_call_ratio']:.2f}",
                delta="Bearish" if results['put_call_ratio'] > 1.1 else "Bullish"
            )
            
            # Market internals
            st.markdown("**Market Internals**")
            
            ad_pct = results['advance_decline'] * 100
            st.metric(
                "Advance/Decline",
                f"{ad_pct:+.1f}%"
            )
            
            hl_pct = results['new_high_low'] * 100
            st.metric(
                "New High/Low Ratio", 
                f"{hl_pct:+.1f}%"
            )

# ============================================================================
# Tab 3: Correlation Analysis  
# ============================================================================
with tab3:
    st.header("Cross-Asset Correlation Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if analyze_button and analysis_type == "Correlation Analysis":
            with st.spinner("Analyzing correlation regimes..."):
                try:
                    # Enhanced correlation analysis with multiple asset classes
                    assets = ['SPY', 'TLT', 'GLD', 'DXY', 'VIX', 'HYG', 'EEM', 'REIT']
                    n_assets = len(assets)
                    
                    # Generate more realistic correlation matrix
                    base_correlations = np.random.RandomState(42).uniform(0.1, 0.7, (n_assets, n_assets))
                    np.fill_diagonal(base_correlations, 1.0)
                    
                    # Make it symmetric
                    correlation_matrix = (base_correlations + base_correlations.T) / 2
                    np.fill_diagonal(correlation_matrix, 1.0)
                    
                    corr_df = pd.DataFrame(correlation_matrix, index=assets, columns=assets)
                    
                    # Calculate correlation regime metrics
                    avg_correlation = np.mean(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])
                    max_correlation = np.max(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])
                    min_correlation = np.min(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])
                    
                    # Regime classification
                    regime_result = correlation_regime(avg_correlation)
                    
                    if avg_correlation > 0.7:
                        correlation_regime_label = "High Correlation (Crisis/Risk-Off)"
                        regime_color = "red"
                        regime_description = "Assets moving together, diversification benefits reduced"
                    elif avg_correlation > 0.5:
                        correlation_regime_label = "Elevated Correlation (Market Stress)"
                        regime_color = "orange"  
                        regime_description = "Moderate correlation, some diversification intact"
                    elif avg_correlation > 0.3:
                        correlation_regime_label = "Normal Correlation (Stable Market)"
                        regime_color = "green"
                        regime_description = "Healthy diversification, asset-specific factors dominate"
                    else:
                        correlation_regime_label = "Low Correlation (Fragmented Market)"
                        regime_color = "blue"
                        regime_description = "Strong diversification, idiosyncratic risks prevalent"
                    
                    # Store comprehensive correlation results
                    st.session_state.macro_results = {
                        "type": "correlation_analysis", 
                        "correlation_matrix": corr_df,
                        "avg_correlation": avg_correlation,
                        "max_correlation": max_correlation,
                        "min_correlation": min_correlation,
                        "correlation_regime": correlation_regime_label,
                        "regime_color": regime_color,
                        "regime_description": regime_description,
                        "assets": assets,
                        "regime_result": regime_result
                    }
                    
                    components.success_message("Correlation analysis complete!")
                    
                except Exception as e:
                    components.error_message(f"Correlation analysis failed: {str(e)}")
                    st.session_state.macro_results = None
        
        # Display correlation analysis results
        if st.session_state.macro_results and st.session_state.macro_results.get("type") == "correlation_analysis":
            results = st.session_state.macro_results
            
            # Correlation heatmap
            fig = px.imshow(
                results['correlation_matrix'], 
                title="Cross-Asset Correlation Matrix",
                color_continuous_scale='RdYlBu_r',
                aspect='auto',
                text_auto='.2f'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Regime summary
            if results['avg_correlation'] > 0.7:
                st.error(f"**{results['correlation_regime']}**")
            elif results['avg_correlation'] > 0.5:
                st.warning(f"**{results['correlation_regime']}**")
            else:
                st.success(f"**{results['correlation_regime']}**")
            
            st.markdown(f"**Analysis:** {results['regime_description']}")
            
            # Key correlation pairs analysis
            st.subheader("Key Correlation Pairs")
            
            key_pairs = [
                ('SPY', 'TLT', 'Stocks vs Bonds'),
                ('SPY', 'GLD', 'Stocks vs Gold'), 
                ('DXY', 'GLD', 'Dollar vs Gold'),
                ('VIX', 'SPY', 'Fear vs Stocks'),
                ('HYG', 'SPY', 'Credit vs Equity')
            ]
            
            pair_data = []
            for asset1, asset2, desc in key_pairs:
                if asset1 in results['assets'] and asset2 in results['assets']:
                    corr_value = results['correlation_matrix'].loc[asset1, asset2]
                    pair_data.append({
                        "Pair": desc,
                        "Correlation": f"{corr_value:.3f}", 
                        "Strength": "Strong" if abs(corr_value) > 0.6 else "Moderate" if abs(corr_value) > 0.3 else "Weak",
                        "Direction": "Positive" if corr_value > 0 else "Negative"
                    })
            
            if pair_data:
                pairs_df = pd.DataFrame(pair_data)
                st.dataframe(pairs_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Correlation Metrics")
        
        if st.session_state.macro_results and st.session_state.macro_results.get("type") == "correlation_analysis":
            results = st.session_state.macro_results
            
            # Main correlation metrics
            st.metric(
                "Average Correlation",
                f"{results['avg_correlation']:.3f}",
                delta=results['correlation_regime'].split('(')[0].strip()
            )
            
            st.metric(
                "Max Correlation", 
                f"{results['max_correlation']:.3f}"
            )
            
            st.metric(
                "Min Correlation",
                f"{results['min_correlation']:.3f}"
            )
            
            # Diversification score
            diversification_score = (1 - results['avg_correlation']) * 100
            st.metric(
                "Diversification Score",
                f"{diversification_score:.0f}/100",
                delta="Excellent" if diversification_score > 60 else "Good" if diversification_score > 40 else "Poor"
            )
            
            # Trading implications
            st.markdown("**Trading Implications**")
            
            if results['avg_correlation'] > 0.7:
                st.warning("High correlation regime")
                st.markdown("• Reduce position sizing")
                st.markdown("• Increase cash allocation")
                st.markdown("• Focus on quality assets")
            elif results['avg_correlation'] < 0.3:
                st.success("Low correlation regime")
                st.markdown("• Increase position sizing")
                st.markdown("• Focus on alpha generation")
                st.markdown("• Sector rotation strategies")
            else:
                st.info("Normal correlation regime")
                st.markdown("• Standard diversification")
                st.markdown("• Mixed factor exposure")
                st.markdown("• Tactical adjustments")

# ============================================================================
# Analysis Summary Section
# ============================================================================
if st.session_state.macro_results:
    results = st.session_state.macro_results
    
    st.markdown("---")
    st.subheader("Analysis Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if results.get("type") == "macro_regime":
            st.info(f"**Economic Regime:** {results['current_regime']}")
            
    with col2:
        if results.get("type") == "sentiment_analysis":
            st.info(f"**Market Sentiment:** {results['sentiment_regime']} ({results['fear_greed_index']:.0f}/100)")
            
    with col3:
        if results.get("type") == "correlation_analysis":
            st.info(f"**Correlation Regime:** {results['correlation_regime'].split('(')[0].strip()}")

else:
    # Show instruction when no analysis has been run
    st.info("Select an analysis type and click 'Analyze' to view market regime insights.")
    
    # Show example of what each analysis provides
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Macro Regime**")
        st.markdown("• Economic cycle analysis")
        st.markdown("• Growth/inflation dynamics")
        st.markdown("• Policy regime identification")
    
    with col2:
        st.markdown("**Sentiment Analysis**")
        st.markdown("• Fear & Greed Index")
        st.markdown("• Market stress indicators")
        st.markdown("• Contrarian signals")
    
    with col3:
        st.markdown("**Correlation Analysis**")
        st.markdown("• Cross-asset correlations")
        st.markdown("• Diversification metrics")
        st.markdown("• Regime change detection")