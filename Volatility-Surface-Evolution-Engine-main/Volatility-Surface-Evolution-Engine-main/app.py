import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="3D Volatility Surface Evolution Engine", layout="wide", page_icon="📈")
st.markdown("""
<style>
body { background-color: #181A1B; }
[data-testid="stAppViewContainer"] { background: #181A1B; }
[data-testid="stSidebar"] { background: #23272A; }
[data-testid="stMetric"] { color: #FFD700; }
</style>
""", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.title("Surface Controls")
base_vol = st.sidebar.slider("Base Volatility (%)", 10, 60, 25)
smile = st.sidebar.slider("Smile Curvature", 0.0, 2.0, 0.7, 0.01)
shock = st.sidebar.slider("Shock Intensity", 0.0, 2.0, 0.0, 0.01)
speed = st.sidebar.slider("Animation Speed (ms/frame)", 10, 200, 60)

# Model parameters
strikes = np.linspace(80, 120, 30)
ttm = np.linspace(0.1, 2.0, 30)
strike_grid, ttm_grid = np.meshgrid(strikes, ttm)

# Animation state
if "frame" not in st.session_state:
    st.session_state.frame = 0
frame = st.session_state.frame

# Animation controls
if "run_anim" not in st.session_state:
    st.session_state.run_anim = False

col1, col2 = st.columns([6, 2])

with col2:
    st.markdown("### Live Metrics")

# Volatility surface generator
def generate_surface(base, smile, slope, shock, t, strikes, ttm):
    atm = 100
    skew = smile + shock * 1.5
    term_slope = slope + shock * 0.5
    vol = (
        base
        + skew * ((strikes - atm) ** 2) / 400
        + term_slope * (ttm - 0.1)
        + shock * np.sin(0.5 * t) * np.exp(-((strikes - atm) ** 2) / 200)
    )
    return vol

# Animation loop
if st.button("Start Animation", key="start"):
    st.session_state.run_anim = True
if st.button("Stop Animation", key="stop"):
    st.session_state.run_anim = False

if st.session_state.run_anim:
    st.session_state.frame += 1
    frame = st.session_state.frame
else:
    st.session_state.frame = 0
    frame = 0

# Evolving parameters
t = frame / 20.0
slope = 0.2 + 0.1 * np.sin(0.3 * t)
vol_surface = generate_surface(base_vol, smile, slope, shock, t, strike_grid, ttm_grid)

# Metrics
atm_idx = np.argmin(np.abs(strikes - 100))
atm_vol = np.mean(vol_surface[:, atm_idx])
skew_val = np.mean(vol_surface[:, -1] - vol_surface[:, 0])
term_slope_val = np.mean(vol_surface[-1, :] - vol_surface[0, :])

with col2:
    st.metric("ATM Vol", f"{atm_vol:.2f}%")
    st.metric("Skew", f"{skew_val:.2f}")
    st.metric("Term Slope", f"{term_slope_val:.2f}")

# Plotly surface plot
colorscale = [
    [0.0, "#0a1a3c"],
    [0.3, "#3a1a6c"],
    [0.6, "#7d2ae8"],
    [0.9, "#f7e01d"],
    [1.0, "#fff700"]
]

surface = go.Surface(
    x=strike_grid,
    y=ttm_grid,
    z=vol_surface,
    colorscale=colorscale,
    showscale=True,
    lighting=dict(ambient=0.7, diffuse=0.8, specular=0.2, roughness=0.5),
)

layout = go.Layout(
    title="3D Volatility Surface Evolution Engine",
    autosize=True,
    template="plotly_dark",
    margin=dict(l=0, r=0, b=0, t=40),
    scene=dict(
        xaxis=dict(title="Strike", backgroundcolor="#181A1B", gridcolor="#23272A"),
        yaxis=dict(title="Time to Maturity", backgroundcolor="#181A1B", gridcolor="#23272A"),
        zaxis=dict(title="Implied Vol (%)", backgroundcolor="#181A1B", gridcolor="#23272A"),
        camera=dict(eye=dict(x=1.7, y=1.7, z=1.2)),
    ),
)

fig = go.Figure(data=[surface], layout=layout)

with col1:
    st.plotly_chart(fig, use_container_width=True)

if st.session_state.run_anim:
    st.experimental_rerun()

