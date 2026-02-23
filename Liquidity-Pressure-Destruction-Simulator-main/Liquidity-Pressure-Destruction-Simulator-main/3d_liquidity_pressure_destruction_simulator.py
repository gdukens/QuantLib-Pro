import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(
    page_title="3D Liquidity Pressure Destruction Simulator",
    layout="wide",
    page_icon="💧",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
body { background-color: #181A1B; }
[data-testid="stSidebar"] { background-color: #23272F; }
[data-testid="stMetric"] { color: #fff; }
</style>
""", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.title("Simulation Controls")
base_liquidity = st.sidebar.slider("Base Liquidity", 100, 2000, 1000, 50)
shock_magnitude = st.sidebar.slider("Shock Magnitude", 0.0, 1.0, 0.3, 0.01)
shock_decay = st.sidebar.slider("Shock Decay Speed", 0.01, 0.5, 0.1, 0.01)
animation_speed = st.sidebar.slider("Animation Speed", 10, 200, 50, 5)

# Simulation parameters
n_prices = 41
n_times = 40
mid_price = 100.0
price_range = 10
prices = np.linspace(mid_price - price_range, mid_price + price_range, n_prices)
times = np.arange(n_times)

# Liquidity depth model
spread_base = 0.5
spread = spread_base + shock_magnitude * price_range * 0.5

# Generate synthetic liquidity surface
@st.cache_data(show_spinner=False)
def generate_liquidity_surface(base_liquidity, spread, shock_magnitude, shock_decay, n_prices, n_times):
    surface = np.zeros((n_times, n_prices))
    mid_idx = n_prices // 2
    for t in range(n_times):
        # Shock propagates and decays
        shock_effect = shock_magnitude * np.exp(-shock_decay * t)
        # Spread widens
        current_spread = spread_base + shock_effect * price_range * 0.5
        left = mid_price - current_spread
        right = mid_price + current_spread
        for i, p in enumerate(prices):
            # Exponential decay from mid-price
            dist = abs(p - mid_price)
            liquidity = base_liquidity * np.exp(-0.25 * dist)
            # Collapse effect: inside spread, liquidity drops
            if p < left or p > right:
                liquidity *= 1 - shock_effect * 0.7
            else:
                liquidity *= 1 - shock_effect
            surface[t, i] = max(liquidity, 0)
    return surface

surface = generate_liquidity_surface(
    base_liquidity, spread, shock_magnitude, shock_decay, n_prices, n_times
)

# Animation controls
frame = st.slider("Animation Frame", 0, n_times - 1, 0, 1)

# Metrics
current_depth = np.sum(surface[frame])
healthy_depth = np.sum(generate_liquidity_surface(base_liquidity, spread_base, 0, shock_decay, n_prices, n_times)[0])
liquidity_collapse_pct = 100 * (1 - current_depth / healthy_depth)

current_spread = spread_base + shock_magnitude * np.exp(-shock_decay * frame) * price_range * 0.5

# Metrics panel
st.markdown("### Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Current Spread", f"{current_spread:.2f}")
col2.metric("Total Depth", f"{current_depth:.0f}")
col3.metric("Liquidity Collapse %", f"{liquidity_collapse_pct:.1f}%")

# 3D Surface Plot
Z = surface[frame]
X, Y = np.meshgrid(prices, [frame])

# For animation, show all frames as a surface
X_anim, Y_anim = np.meshgrid(prices, times)
Z_anim = surface

mid_line = np.full(n_times, mid_price)
spread_left = mid_price - current_spread
spread_right = mid_price + current_spread

fig = go.Figure()
fig.add_trace(
    go.Surface(
        x=X_anim,
        y=Y_anim,
        z=Z_anim,
        colorscale=[
            [0.0, "#001f3f"],
            [0.5, "#0074D9"],
            [0.8, "#FF4136"],
            [1.0, "#FF0000"]
        ],
        showscale=True,
        opacity=0.95,
        contours={
            "z": {"show": True, "color": "white", "width": 2}
        },
    )
)
# Mid-price line
fig.add_trace(
    go.Scatter3d(
        x=mid_line,
        y=times,
        z=surface[:, n_prices // 2],
        mode="lines",
        line=dict(color="white", width=4),
        name="Mid-Price"
    )
)
# Spread lines
fig.add_trace(
    go.Scatter3d(
        x=np.full(n_times, spread_left),
        y=times,
        z=surface[:, np.argmin(np.abs(prices - spread_left))],
        mode="lines",
        line=dict(color="orange", width=2, dash="dash"),
        name="Spread Left"
    )
)
fig.add_trace(
    go.Scatter3d(
        x=np.full(n_times, spread_right),
        y=times,
        z=surface[:, np.argmin(np.abs(prices - spread_right))],
        mode="lines",
        line=dict(color="orange", width=2, dash="dash"),
        name="Spread Right"
    )
)

fig.update_layout(
    title="3D Liquidity Pressure Destruction Simulator",
    scene=dict(
        xaxis_title="Price Level",
        yaxis_title="Time",
        zaxis_title="Liquidity Depth",
        xaxis=dict(backgroundcolor="#181A1B", gridcolor="#444", showspikes=False),
        yaxis=dict(backgroundcolor="#181A1B", gridcolor="#444", showspikes=False),
        zaxis=dict(backgroundcolor="#181A1B", gridcolor="#444", showspikes=False),
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    paper_bgcolor="#181A1B",
    font=dict(color="white"),
    height=700,
)

st.plotly_chart(fig, use_container_width=True)

# Animation
if st.button("Play Animation"):
    import time
    for f in range(n_times):
        st.session_state["frame"] = f
        st.rerun()
        time.sleep(animation_speed / 1000)

st.caption("""
- Deep blue = healthy liquidity
- Red = collapsed liquidity
- White = mid-price
- Orange = spread boundaries
""")
