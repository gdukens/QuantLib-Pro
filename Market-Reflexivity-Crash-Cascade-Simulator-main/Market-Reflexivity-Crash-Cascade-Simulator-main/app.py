import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from scipy.special import expit

# --- Styling ---
st.set_page_config(
    page_title="3D Market Reflexivity & Crash Cascade Simulator",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💥"
)

# --- Sidebar Controls ---
st.sidebar.title("Simulation Controls")

initial_leverage = st.sidebar.slider(
    "Initial Leverage", min_value=1.0, max_value=10.0, value=5.0, step=0.1
)
vol_sensitivity = st.sidebar.slider(
    "Volatility Sensitivity", min_value=0.01, max_value=1.0, value=0.2, step=0.01
)
liquidation_threshold = st.sidebar.slider(
    "Liquidation Threshold", min_value=0.1, max_value=2.0, value=1.0, step=0.01
)
feedback_strength = st.sidebar.slider(
    "Feedback Strength", min_value=0.01, max_value=2.0, value=0.5, step=0.01
)
sim_steps = st.sidebar.slider(
    "Simulation Steps", min_value=50, max_value=500, value=200, step=10
)

# --- Helper Functions ---
def clamp(x, min_val, max_val):
    return np.clip(x, min_val, max_val)

def compute_feedback(P, V, L, params):
    # Volatility increases nonlinearly with price deviation
    V_new = V + params['vol_sensitivity'] * np.tanh(np.abs(P))
    V_new = clamp(V_new, 1e-6, 10.0)
    # Leverage decays with volatility (exponential decay)
    L_new = L * np.exp(-params['feedback_strength'] * V_new)
    L_new = clamp(L_new, 0.1, params['initial_leverage'])
    # Liquidation intensity: sigmoid threshold on leverage drop
    dL = L - L_new
    F = expit((params['liquidation_threshold'] - L_new) * 5.0) * dL * 10.0
    F = clamp(F, 0.0, 5.0)
    return V_new, L_new, F

def simulate_market(params, steps):
    P = np.zeros(steps)
    V = np.zeros(steps)
    L = np.zeros(steps)
    F = np.zeros(steps)
    P[0] = 0.0
    V[0] = 1.0
    L[0] = params['initial_leverage']
    F[0] = 0.0
    for t in range(1, steps):
        V[t], L[t], F[t] = compute_feedback(P[t-1], V[t-1], L[t-1], params)
        # Price update: mean reversion + liquidation pressure
        dP = -0.05 * P[t-1] + 0.1 * np.tanh(F[t])
        P[t] = clamp(P[t-1] + dP, -3.0, 3.0)
        # Numerical stability
        if np.isnan(P[t]) or np.isnan(V[t]) or np.isnan(L[t]) or np.isnan(F[t]):
            P[t], V[t], L[t], F[t] = 0.0, 1.0, params['initial_leverage'], 0.0
    df = pd.DataFrame({
        'Step': np.arange(steps),
        'Price Deviation': P,
        'Volatility': V,
        'Leverage': L,
        'Liquidation Intensity': F
    })
    return df

def build_3d_surface(P_series, L_series, F_series, step):
    # Interpolate to grid for surface
    grid_size = 40
    P_grid = np.linspace(np.min(P_series), np.max(P_series), grid_size)
    L_grid = np.linspace(np.min(L_series), np.max(L_series), grid_size)
    P_mesh, L_mesh = np.meshgrid(P_grid, L_grid)
    F_mesh = np.zeros_like(P_mesh)
    for i in range(grid_size):
        for j in range(grid_size):
            # Find closest time index
            idx = np.argmin((P_series - P_mesh[i, j])**2 + (L_series - L_mesh[i, j])**2)
            F_mesh[i, j] = F_series[idx]
    surface = go.Surface(
        x=P_mesh, y=L_mesh, z=F_mesh,
        colorscale='Inferno',
        cmin=0, cmax=5,
        showscale=True,
        name=f"Step {step}"
    )
    layout = go.Layout(
        title=f"3D Surface: Price Deviation vs Leverage vs Liquidation (Step {step})",
        scene=dict(
            xaxis=dict(title="Price Deviation", backgroundcolor="#222", color="#fff"),
            yaxis=dict(title="Leverage", backgroundcolor="#222", color="#fff"),
            zaxis=dict(title="Liquidation Intensity", backgroundcolor="#222", color="#fff"),
            bgcolor="#111"
        ),
        paper_bgcolor="#111",
        plot_bgcolor="#111",
        font=dict(color="#fff"),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    fig = go.Figure(data=[surface], layout=layout)
    return fig

# --- Main App ---
st.title("3D Market Reflexivity & Crash Cascade Simulator")
st.markdown("""
This simulator models a nonlinear feedback loop in financial markets:
- Price deviation increases volatility
- Volatility reduces leverage
- Falling leverage triggers liquidations
- Liquidations further pressure price
""")

params = {
    'initial_leverage': initial_leverage,
    'vol_sensitivity': vol_sensitivity,
    'liquidation_threshold': liquidation_threshold,
    'feedback_strength': feedback_strength
}

sim_data = simulate_market(params, sim_steps)

st.subheader("Simulation Time Series")
st.line_chart(sim_data.set_index('Step')[['Price Deviation', 'Leverage', 'Volatility', 'Liquidation Intensity']])

st.subheader("3D Surface Animation")

# Animation slider
time_step = st.slider(
    "Animation Step", min_value=1, max_value=sim_steps-1, value=1, step=1
)

fig = build_3d_surface(
    sim_data['Price Deviation'].values[:time_step],
    sim_data['Leverage'].values[:time_step],
    sim_data['Liquidation Intensity'].values[:time_step],
    time_step
)

st.plotly_chart(fig, use_container_width=True)

st.caption("""
**X-axis:** Price Deviation | **Y-axis:** Leverage | **Z-axis:** Liquidation Intensity

All calculations are numerically stabilized and clamped to avoid runaway values or NaNs.
""")
