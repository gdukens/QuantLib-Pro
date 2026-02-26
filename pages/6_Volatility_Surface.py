"""
Volatility Surface Dashboard

Week 13: Streamlit page for volatility surface visualization and analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from quantlib_pro.ui import components
from quantlib_pro.volatility.surface import construct_volatility_surface

# Page config
st.set_page_config(
    page_title="Volatility Surface - QuantLib Pro",
    page_icon="",
    layout="wide",
)

st.title("Volatility Surface")
st.markdown("Construct and analyze implied volatility surfaces across strikes and maturities.")

# Initialize session state
if "vol_surface_results" not in st.session_state:
    st.session_state.vol_surface_results = None

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    ticker = st.text_input("Underlying Ticker", value="SPY", help="Ticker symbol for vol surface")
    
    spot_price = st.number_input(
        "Current Spot Price ($)",
        min_value=1.0,
        max_value=10000.0,
        value=450.0,
        step=1.0,
    )
    
    st.subheader("Surface Parameters")
    
    strike_range = st.slider(
        "Strike Range (% of spot)",
        min_value=50,
        max_value=150,
        value=(80, 120),
        step=5,
    )
    
    num_strikes = st.slider(
        "Number of Strikes",
        min_value=5,
        max_value=20,
        value=10,
        step=1,
    )
    
    maturities = st.multiselect(
        "Maturities (days)",
        options=[7, 14, 30, 60, 90, 180, 365],
        default=[30, 60, 90, 180],
    )
    
    st.subheader("Market Conditions")
    
    atm_vol = st.slider(
        "ATM Volatility (%)",
        min_value=5,
        max_value=100,
        value=20,
        step=1,
    ) / 100
    
    skew_intensity = st.slider(
        "Skew Intensity",
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Higher = more pronounced volatility skew",
    )
    
    build_button = st.button(" Build Surface", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3 = st.tabs([" 3D Surface", " Smile/Skew", " Term Structure"])

with tab1:
    st.header("3D Volatility Surface")
    
    if build_button:
        with st.spinner("Constructing volatility surface..."):
            try:
                # Generate strike grid
                strike_min = spot_price * (strike_range[0] / 100)
                strike_max = spot_price * (strike_range[1] / 100)
                strikes = np.linspace(strike_min, strike_max, num_strikes)
                
                # Sort maturities
                maturities_sorted = sorted(maturities)
                
                # Construct surface using parametric model
                surface = np.zeros((len(strikes), len(maturities_sorted)))
                
                for i, strike in enumerate(strikes):
                    for j, maturity in enumerate(maturities_sorted):
                        # Moneyness
                        moneyness = np.log(strike / spot_price)
                        time_years = maturity / 365.0
                        
                        # Parametric smile: quadratic in log-moneyness
                        # Vol smile formula: σ(K,T) = σ_ATM + a*m² + b*m
                        # where m = log(K/S) is log-moneyness
                        
                        # Term structure: vol decreases with maturity
                        term_factor = 1.0 + 0.3 * np.exp(-time_years * 0.5)
                        
                        # Skew: asymmetric smile (put skew)
                        skew_factor = skew_intensity * moneyness * (1 - 0.5 * moneyness)
                        
                        # Convexity: smile curvature
                        convexity_factor = 0.3 * moneyness ** 2
                        
                        vol = atm_vol * term_factor + skew_factor + convexity_factor
                        vol = max(vol, 0.05)  # Floor at 5%
                        
                        surface[i, j] = vol
                
                st.session_state.vol_surface_results = {
                    "surface": surface,
                    "strikes": strikes,
                    "maturities": maturities_sorted,
                    "spot": spot_price,
                    "atm_vol": atm_vol,
                    "ticker": ticker,
                }
                
                components.success_message("Volatility surface constructed!")
                
            except Exception as e:
                components.error_message(f"Surface construction failed: {str(e)}")
                st.session_state.vol_surface_results = None
    
    # Display 3D surface
    if st.session_state.vol_surface_results:
        results = st.session_state.vol_surface_results
        
        # Metrics
        components.multi_metric_row([
            {
                "title": "Underlying",
                "value": results["ticker"],
                "help": "Underlying asset",
            },
            {
                "title": "Spot Price",
                "value": f"${results['spot']:.2f}",
                "help": "Current price of underlying",
            },
            {
                "title": "ATM Vol",
                "value": f"{results['atm_vol']*100:.1f}%",
                "help": "At-the-money volatility",
            },
            {
                "title": "Surface Points",
                "value": f"{len(results['strikes'])}×{len(results['maturities'])}",
                "help": "Strikes × Maturities",
            },
        ])
        
        st.markdown("---")
        
        # 3D Surface plot
        import plotly.graph_objects as go
        
        # Create meshgrid
        X, Y = np.meshgrid(results["maturities"], results["strikes"])
        Z = results["surface"] * 100  # Convert to percentage
        
        fig = go.Figure(data=[go.Surface(
            x=X,
            y=Y,
            z=Z,
            colorscale="Viridis",
            colorbar=dict(title="IV (%)"),
        )])
        
        fig.update_layout(
            title=f"{results['ticker']} Implied Volatility Surface",
            scene=dict(
                xaxis_title="Maturity (days)",
                yaxis_title="Strike ($)",
                zaxis_title="Implied Vol (%)",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.3)),
            ),
            height=600,
            template="plotly_white",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Click 'Build Surface' to construct the volatility surface.")

with tab2:
    st.header("Volatility Smile & Skew")
    
    if st.session_state.vol_surface_results:
        results = st.session_state.vol_surface_results
        
        # Plot smile for each maturity
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        colors = ["blue", "green", "orange", "red", "purple", "brown", "pink"]
        
        for j, maturity in enumerate(results["maturities"]):
            moneyness = results["strikes"] / results["spot"]
            vols = results["surface"][:, j] * 100
            
            fig.add_trace(go.Scatter(
                x=moneyness,
                y=vols,
                mode="lines+markers",
                name=f"{maturity}D",
                line=dict(color=colors[j % len(colors)], width=2),
            ))
        
        # Add ATM reference line
        fig.add_vline(x=1.0, line_dash="dash", line_color="gray",
                      annotation_text="ATM", annotation_position="top")
        
        fig.update_layout(
            title="Volatility Smile Curves",
            xaxis_title="Moneyness (Strike/Spot)",
            yaxis_title="Implied Volatility (%)",
            height=450,
            template="plotly_white",
            hovermode="x unified",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Skew metrics
        st.subheader("Skew Metrics")
        
        skew_metrics = []
        
        for j, maturity in enumerate(results["maturities"]):
            vols = results["surface"][:, j]
            
            # Find ATM, 25 delta put, 25 delta call
            atm_idx = np.argmin(np.abs(results["strikes"] - results["spot"]))
            
            # OTM put (lower strike)
            otm_put_idx = max(0, atm_idx - 2)
            # OTM call (higher strike)
            otm_call_idx = min(len(results["strikes"]) - 1, atm_idx + 2)
            
            atm_vol = vols[atm_idx]
            put_vol = vols[otm_put_idx]
            call_vol = vols[otm_call_idx]
            
            # Skew = Put Vol - Call Vol
            skew = (put_vol - call_vol) * 100
            
            # Convexity = (Put Vol + Call Vol)/2 - ATM Vol
            convexity = ((put_vol + call_vol) / 2 - atm_vol) * 100
            
            skew_metrics.append({
                "Maturity": f"{maturity}D",
                "ATM Vol (%)": f"{atm_vol*100:.2f}",
                "Skew (%)": f"{skew:.2f}",
                "Convexity (%)": f"{convexity:.2f}",
            })
        
        skew_df = pd.DataFrame(skew_metrics)
        components.data_table(skew_df)
        
    else:
        components.info_message("Build surface to see smile/skew analysis.")

with tab3:
    st.header("Volatility Term Structure")
    
    if st.session_state.vol_surface_results:
        results = st.session_state.vol_surface_results
        
        # Plot term structure for different strikes
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Select 3 strikes: ITM, ATM, OTM
        n_strikes = len(results["strikes"])
        strike_indices = [
            n_strikes // 4,      # ITM
            n_strikes // 2,      # ATM
            3 * n_strikes // 4,  # OTM
        ]
        
        labels = ["ITM", "ATM", "OTM"]
        colors = ["green", "blue", "red"]
        
        for idx, strike_idx in enumerate(strike_indices):
            strike = results["strikes"][strike_idx]
            vols = results["surface"][strike_idx, :] * 100
            
            fig.add_trace(go.Scatter(
                x=results["maturities"],
                y=vols,
                mode="lines+markers",
                name=f"{labels[idx]} (K=${strike:.0f})",
                line=dict(color=colors[idx], width=2),
            ))
        
        fig.update_layout(
            title="Volatility Term Structure",
            xaxis_title="Maturity (days)",
            yaxis_title="Implied Volatility (%)",
            height=400,
            template="plotly_white",
            hovermode="x unified",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Term structure analysis
        st.subheader("Term Structure Analysis")
        
        # Get ATM vols across maturities
        atm_idx = np.argmin(np.abs(results["strikes"] - results["spot"]))
        atm_vols = results["surface"][atm_idx, :] * 100
        
        # Calculate term structure slope
        if len(atm_vols) >= 2:
            short_vol = atm_vols[0]
            long_vol = atm_vols[-1]
            slope = long_vol - short_vol
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Short-term Vol",
                    f"{short_vol:.2f}%",
                    help=f"{results['maturities'][0]} day volatility",
                )
            
            with col2:
                st.metric(
                    "Long-term Vol",
                    f"{long_vol:.2f}%",
                    help=f"{results['maturities'][-1]} day volatility",
                )
            
            with col3:
                st.metric(
                    "Term Structure Slope",
                    f"{slope:.2f}%",
                    delta=f"{'Upward' if slope > 0 else 'Downward'} sloping",
                    help="Difference between long and short term vol",
                )
            
            # Interpretation
            st.markdown("---")
            st.subheader("Interpretation")
            
            if slope > 5:
                st.info(
                    """
                     **Upward Sloping Term Structure** (Contango)
                    - Market expects higher future volatility
                    - Uncertainty about future events
                    - Common in calm markets
                    - Calendar spreads: sell near, buy far
                    """
                )
            elif slope < -5:
                st.warning(
                    """
                     **Downward Sloping Term Structure** (Backwardation)
                    - Elevated near-term uncertainty
                    - Market stress or event risk
                    - Expect volatility to decrease
                    - Calendar spreads: buy near, sell far
                    """
                )
            else:
                st.success(
                    """
                     **Flat Term Structure**
                    - Stable volatility expectations
                    - No major structural changes expected
                    - Balanced risk environment
                    """
                )
        
    else:
        components.info_message("Build surface to see term structure analysis.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Volatility Surface powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
