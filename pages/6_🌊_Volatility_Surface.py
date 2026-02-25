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
    page_icon="🌊",
    layout="wide",
)

st.title("🌊 Volatility Surface")
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
    
    build_button = st.button("🏗️ Build Surface", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌊 3D Surface",
    "📊 Smile/Skew",
    "📈 Term Structure",
    "📶 Real Market Data",
    "🎬 Surface Evolution"
])

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
                    📈 **Upward Sloping Term Structure** (Contango)
                    - Market expects higher future volatility
                    - Uncertainty about future events
                    - Common in calm markets
                    - Calendar spreads: sell near, buy far
                    """
                )
            elif slope < -5:
                st.warning(
                    """
                    📉 **Downward Sloping Term Structure** (Backwardation)
                    - Elevated near-term uncertainty
                    - Market stress or event risk
                    - Expect volatility to decrease
                    - Calendar spreads: buy near, sell far
                    """
                )
            else:
                st.success(
                    """
                    ➡️ **Flat Term Structure**
                    - Stable volatility expectations
                    - No major structural changes expected
                    - Balanced risk environment
                    """
                )
        
    else:
        components.info_message("Build surface to see term structure analysis.")

# ============================================================================
# Tab 4: Real Market Data Volatility Surface
# ============================================================================
with tab4:
    st.header("📶 Real Market Data Volatility Surface")
    
    st.markdown("""
    **Live Option Chain Analysis** - Fetch real option chain data and calculate 
    implied volatility surface from actual market prices.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("⚙️ Data Parameters")
        
        real_ticker = st.text_input(
            "Ticker Symbol",
            value="AAPL",
            help="Stock ticker for option chain"
        )
        
        risk_free = st.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=1.5,
            step=0.1
        ) / 100
        
        option_type = st.selectbox(
            "Option Type",
            options=["call", "put"],
            index=0
        )
        
        min_iv = st.slider(
            "Min Valid IV (%)",
            min_value=0,
            max_value=100,
            value=5,
            help="Filter out options with IV below this threshold"
        ) / 100
        
        max_iv = st.slider(
            "Max Valid IV (%)",
            min_value=100,
            max_value=500,
            value=200,
            help="Filter out options with IV above this threshold"
        ) / 100
        
        if st.button("🚀 Fetch & Build Surface", type="primary"):
            with st.spinner(f"Fetching option chain for {real_ticker}..."):
                try:
                    import yfinance as yf
                    from scipy.optimize import minimize_scalar
                    from scipy.stats import norm
                    
                    # Fetch stock data
                    stock = yf.Ticker(real_ticker)
                    spot = stock.history(period='1d')['Close'].iloc[-1]
                    
                    st.write(f"✅ Spot Price: **${spot:.2f}**")
                    
                    # Get option expirations
                    expirations = stock.options
                    
                    if not expirations:
                        st.error("No option chain data available for this ticker")
                    else:
                        st.write(f"📊 Found **{len(expirations)}** expiration dates")
                        
                        # Black-Scholes pricing function
                        def black_scholes_price(S, K, T, r, sigma, option_type='call'):
                            if T <= 0 or sigma <= 0:
                                return 0
                            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
                            d2 = d1 - sigma*np.sqrt(T)
                            if option_type == 'call':
                                return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
                            else:
                                return K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
                        
                        # Implied volatility solver
                        def implied_volatility(price, S, K, T, r, option_type='call'):
                            if price <= 0 or T <= 0:
                                return None
                            
                            def objective(sigma):
                                return abs(black_scholes_price(S, K, T, r, sigma, option_type) - price)
                            
                            try:
                                result = minimize_scalar(objective, bounds=(0.01, 5.0), method='bounded')
                                return result.x if result.success else None
                            except:
                                return None
                        
                        # Process option chain
                        option_data = []
                        today = datetime.now()
                        
                        for exp in expirations[:10]:  # Limit to first 10 expirations
                            opt_chain = stock.option_chain(exp)
                            df = opt_chain.calls if option_type == 'call' else opt_chain.puts
                            
                            for _, row in df.iterrows():
                                T = (datetime.strptime(exp, '%Y-%m-%d') - today).days / 365.0
                                
                                if T <= 0 or row['lastPrice'] <= 0:
                                    continue
                                
                                iv = implied_volatility(
                                    price=row['lastPrice'],
                                    S=spot,
                                    K=row['strike'],
                                    T=T,
                                    r=risk_free,
                                    option_type=option_type
                                )
                                
                                if iv and min_iv < iv < max_iv:
                                    option_data.append({
                                        'strike': row['strike'],
                                        'T': T,
                                        'iv': iv,
                                        'price': row['lastPrice'],
                                        'volume': row.get('volume', 0)
                                    })
                        
                        st.session_state.real_vol_data = option_data
                        st.session_state.real_spot = spot
                        st.success(f"✅ Processed **{len(option_data)}** options with valid IV")
                        
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")
    
    with col1:
        if 'real_vol_data' in st.session_state and st.session_state.real_vol_data:
            option_data = st.session_state.real_vol_data
            spot = st.session_state.real_spot
            
            # Create DataFrame
            df = pd.DataFrame(option_data)
            
            # 3D Surface Plot
            st.subheader("🌊 3D Implied Volatility Surface")
            
            import plotly.graph_objects as go
            
            fig_3d = go.Figure(data=[go.Scatter3d(
                x=df['strike'],
                y=df['T'],
                z=df['iv'] * 100,
                mode='markers',
                marker=dict(
                    size=5,
                    color=df['iv'] * 100,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="IV (%)"),
                    line=dict(color='white', width=0.5)
                ),
                text=[f"Strike: ${s:.2f}<br>TTM: {t:.2f}y<br>IV: {iv*100:.1f}%" 
                      for s, t, iv in zip(df['strike'], df['T'], df['iv'])],
                hoverinfo='text'
            )])
            
            fig_3d.update_layout(
                template='plotly_dark',
                height=600,
                scene=dict(
                    xaxis_title='Strike ($)',
                    yaxis_title='Time to Maturity (years)',
                    zaxis_title='Implied Volatility (%)',
                    bgcolor='black',
                    xaxis=dict(backgroundcolor='black', gridcolor='gray'),
                    yaxis=dict(backgroundcolor='black', gridcolor='gray'),
                    zaxis=dict(backgroundcolor='black', gridcolor='gray')
                )
            )
            
            st.plotly_chart(fig_3d, use_container_width=True)
            
            # Volatility Smile
            st.subheader("😀 Volatility Smile")
            
            # Group by maturity (nearest 3)
            maturities = sorted(df['T'].unique())[:3]
            
            fig_smile = go.Figure()
            
            for i, maturity in enumerate(maturities):
                subset = df[df['T'] == maturity].sort_values('strike')
                
                fig_smile.add_trace(go.Scatter(
                    x=subset['strike'],
                    y=subset['iv'] * 100,
                    mode='lines+markers',
                    name=f"T = {maturity:.2f}y",
                    line=dict(width=2),
                    marker=dict(size=8)
                ))
            
            # Add ATM line
            fig_smile.add_vline(
                x=spot,
                line_dash="dash",
                line_color="red",
                annotation_text="ATM"
            )
            
            fig_smile.update_layout(
                template='plotly_dark',
                height=400,
                xaxis_title='Strike ($)',
                yaxis_title='Implied Volatility (%)',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_smile, use_container_width=True)
            
            # Statistics
            st.subheader("📊 Surface Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                atm_options = df[abs(df['strike'] - spot) < spot * 0.05]
                if not atm_options.empty:
                    atm_iv = atm_options['iv'].mean()
                    st.metric("ATM IV", f"{atm_iv*100:.2f}%")
                else:
                    st.metric("ATM IV", "N/A")
            
            with col2:
                min_strike_iv = df.loc[df['strike'].idxmin(), 'iv']
                max_strike_iv = df.loc[df['strike'].idxmax(), 'iv']
                skew = (min_strike_iv - max_strike_iv) * 100
                st.metric("Skew", f"{skew:.2f}%")
            
            with col3:
                st.metric("Total Options", len(df))
            
            with col4:
                avg_iv = df['iv'].mean()
                st.metric("Avg IV", f"{avg_iv*100:.2f}%")
            
        else:
            st.info("📈 Fetch option chain data to see real market volatility surface")

# ============================================================================
# Tab 5: Volatility Surface Evolution Engine
# ============================================================================
with tab5:
    st.header("🎬 Volatility Surface Evolution Engine")
    
    st.markdown("""
    **Dynamic Surface Animation** - Watch how the volatility surface evolves over time 
    with shocks and market stress. Adjust parameters to see real-time changes.
    """)
    
    # Initialize animation state
    if 'evo_frame' not in st.session_state:
        st.session_state.evo_frame = 0
    
    if 'evo_running' not in st.session_state:
        st.session_state.evo_running = False
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("🎮 Surface Controls")
        
        base_vol_evo = st.slider(
            "Base Volatility (%)",
            min_value=10,
            max_value=60,
            value=25,
            key="base_vol_evo"
        )
        
        smile_curve = st.slider(
            "Smile Curvature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.01,
            key="smile_curve"
        )
        
        shock_intensity = st.slider(
            "Shock Intensity",
            min_value=0.0,
            max_value=2.0,
            value=0.5,
            step=0.01,
            key="shock_intensity"
        )
        
        term_slope = st.slider(
            "Term Structure Slope",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.01,
            key="term_slope"
        )
        
        # Animation control
        st.markdown("---")
        st.markdown("**Animation**")
        
        if st.button("▶️ Start", key="start_evo"):
            st.session_state.evo_running = True
        
        if st.button("⏸️ Stop", key="stop_evo"):
            st.session_state.evo_running = False
            st.session_state.evo_frame = 0
        
        # Manual frame control
        if not st.session_state.evo_running:
            manual_frame = st.slider(
                "Manual Frame",
                min_value=0,
                max_value=100,
                value=0,
                key="manual_frame"
            )
            st.session_state.evo_frame = manual_frame
    
    with col1:
        # Generate surface
        strikes_evo = np.linspace(80, 120, 30)
        ttm_evo = np.linspace(0.1, 2.0, 30)
        strike_grid, ttm_grid = np.meshgrid(strikes_evo, ttm_evo)
        
        # Current frame
        frame = st.session_state.evo_frame
        t = frame / 20.0
        
        # Evolving slope
        dynamic_slope = term_slope + 0.1 * np.sin(0.3 * t)
        
        # Generate volatility surface
        atm_strike = 100
        skew = smile_curve + shock_intensity * 1.5
        
        vol_surface = (
            base_vol_evo
            + skew * ((strike_grid - atm_strike) ** 2) / 400
            + dynamic_slope * (ttm_grid - 0.1) * 10
            + shock_intensity * np.sin(0.5 * t) * np.exp(-((strike_grid - atm_strike) ** 2) / 200)
        )
        
        # Calculate metrics
        atm_idx = np.argmin(np.abs(strikes_evo - 100))
        atm_vol_val = np.mean(vol_surface[:, atm_idx])
        skew_val = np.mean(vol_surface[:, -1] - vol_surface[:, 0])
        term_slope_val = np.mean(vol_surface[-1, :] - vol_surface[0, :])
        
        # Display metrics
        st.subheader(f"📊 Live Metrics (Frame {frame})")
        
        col1a, col2a, col3a = st.columns(3)
        
        with col1a:
            st.metric("ATM Vol", f"{atm_vol_val:.2f}%")
        
        with col2a:
            st.metric("Skew", f"{skew_val:.2f}")
        
        with col3a:
            st.metric("Term Slope", f"{term_slope_val:.2f}")
        
        # 3D Surface plot
        import plotly.graph_objects as go
        
        colorscale = [
            [0.0, "#0a1a3c"],
            [0.3, "#3a1a6c"],
            [0.6, "#7d2ae8"],
            [0.9, "#f7e01d"],
            [1.0, "#fff700"]
        ]
        
        fig_evo = go.Figure(data=[go.Surface(
            x=strike_grid,
            y=ttm_grid,
            z=vol_surface,
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(title="IV (%)"),
            lighting=dict(
                ambient=0.7,
                diffuse=0.8,
                specular=0.2,
                roughness=0.5
            )
        )])
        
        fig_evo.update_layout(
            title=f"Volatility Surface Evolution - Frame {frame}",
            template='plotly_dark',
            height=600,
            margin=dict(l=0, r=0, b=0, t=40),
            scene=dict(
                xaxis=dict(
                    title="Strike",
                    backgroundcolor="#181A1B",
                    gridcolor="#23272A"
                ),
                yaxis=dict(
                    title="Time to Maturity",
                    backgroundcolor="#181A1B",
                    gridcolor="#23272A"
                ),
                zaxis=dict(
                    title="Implied Vol (%)",
                    backgroundcolor="#181A1B",
                    gridcolor="#23272A"
                ),
                camera=dict(eye=dict(x=1.7, y=1.7, z=1.2))
            )
        )
        
        st.plotly_chart(fig_evo, use_container_width=True)
        
        # Auto-advance frame if running
        if st.session_state.evo_running:
            st.session_state.evo_frame = (st.session_state.evo_frame + 1) % 100
            st.rerun()

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
