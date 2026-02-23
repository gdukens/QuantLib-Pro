import streamlit as st
import numpy as np
import plotly.graph_objs as go
from black_scholes import black_scholes_price, delta, gamma, vega, theta, rho

st.set_page_config(
    page_title="Black-Scholes Visual Explainer",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💹"
)

# --- Sidebar Controls ---
st.sidebar.title("⚙️ Controls")
st.sidebar.markdown("---")

S = st.sidebar.slider("Stock Price (S)", 10, 300, 100, 1)
K = st.sidebar.slider("Strike Price (K)", 10, 300, 100, 1)
sigma = st.sidebar.slider("Volatility (σ, %)", 1, 100, 20, 1) / 100
T = st.sidebar.slider("Time to Maturity (T, years)", 1, 365, 30, 1) / 365
r = st.sidebar.slider("Risk-Free Rate (r, %)", 0, 15, 2, 1) / 100
option_type = st.sidebar.radio("Option Type", ["call", "put"], horizontal=True)

# --- Main UI ---
st.markdown(
    """
    <style>
    .big-price {font-size: 3.5em; font-weight: bold; color: #00e6e6; text-align: center;}
    .greek-label {font-size: 1.2em; font-weight: bold;}
    .greek-value {font-size: 1.5em; font-weight: bold;}
    .greek-box {padding: 1em; border-radius: 10px; margin: 0.5em; display: inline-block; min-width: 120px;}
    .greek-delta {background: #1a1a2e; color: #00f2fe;}
    .greek-gamma {background: #16213e; color: #f6416c;}
    .greek-vega {background: #0f3460; color: #43e97b;}
    .greek-theta {background: #53354a; color: #ffbd39;}
    .greek-rho {background: #232526; color: #f7971e;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Calculate Option Price and Greeks ---
price = black_scholes_price(S, K, T, r, sigma, option_type)
delta_val = delta(S, K, T, r, sigma, option_type)
gamma_val = gamma(S, K, T, r, sigma)
vega_val = vega(S, K, T, r, sigma)
theta_val = theta(S, K, T, r, sigma, option_type)
rho_val = rho(S, K, T, r, sigma, option_type)

# --- Display Price ---
st.markdown(f'<div class="big-price">{option_type.capitalize()} Price: ${price:.2f}</div>', unsafe_allow_html=True)

# --- Display Greeks ---
greek_cols = st.columns(5)
greek_styles = ["greek-delta", "greek-gamma", "greek-vega", "greek-theta", "greek-rho"]
greek_names = ["Delta", "Gamma", "Vega", "Theta", "Rho"]
greek_vals = [delta_val, gamma_val, vega_val, theta_val, rho_val]
for i, col in enumerate(greek_cols):
    col.markdown(f'<div class="greek-box {greek_styles[i]}">'
                 f'<div class="greek-label">{greek_names[i]}</div>'
                 f'<div class="greek-value">{greek_vals[i]:.4f}</div>'
                 f'</div>', unsafe_allow_html=True)

st.markdown("---")

# --- 3D Surface Plot: S vs sigma vs Price ---
S_range = np.linspace(10, 300, 40)
sigma_range = np.linspace(0.01, 1, 40)
S_grid, sigma_grid = np.meshgrid(S_range, sigma_range)
price_grid = black_scholes_price(S_grid, K, T, r, sigma_grid, option_type)

surface = go.Surface(
    x=S_range, y=sigma_range*100, z=price_grid,
    colorscale='Viridis', showscale=True, opacity=0.95
)
layout = go.Layout(
    title=f"{option_type.capitalize()} Price Surface",
    scene=dict(
        xaxis_title='Stock Price (S)',
        yaxis_title='Volatility (%)',
        zaxis_title='Option Price',
        bgcolor='#181818',
    ),
    paper_bgcolor='#181818',
    font=dict(color='white'),
    margin=dict(l=0, r=0, b=0, t=40)
)
fig3d = go.Figure(data=[surface], layout=layout)
fig3d.update_layout(transition_duration=500)
st.plotly_chart(fig3d, use_container_width=True)

# --- 2D Plot: Delta vs S ---
delta_curve = [delta(s, K, T, r, sigma, option_type) for s in S_range]
fig2d = go.Figure()
fig2d.add_trace(go.Scatter(x=S_range, y=delta_curve, mode='lines', line=dict(color='#00f2fe', width=4)))
fig2d.update_layout(
    title="Delta vs Stock Price",
    xaxis_title="Stock Price (S)",
    yaxis_title="Delta",
    plot_bgcolor='#181818',
    paper_bgcolor='#181818',
    font=dict(color='white'),
    margin=dict(l=40, r=40, b=40, t=40),
    transition_duration=500
)
st.plotly_chart(fig2d, use_container_width=True)

# --- Footer ---
st.markdown("""
<div style='text-align:center; color:#888; font-size:1.1em;'>
  <b>Black-Scholes Visual Explainer</b> &mdash; Powered by Streamlit, Plotly, NumPy, SciPy
</div>
""", unsafe_allow_html=True)
