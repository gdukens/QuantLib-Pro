import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(
    page_title="3D Correlation Regime Tectonic Shift Engine",
    layout="wide",
    page_icon="🌋",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
body { background-color: #181818; }
[data-testid="stAppViewContainer"] { background: #181818; }
[data-testid="stSidebar"] { background: #232323; }
</style>
""", unsafe_allow_html=True)

st.title("3D Correlation Regime Tectonic Shift Engine")

# Parameters
n_clusters = 8
n_assets_per_cluster = 10
n_time = 40

# Sidebar controls
st.sidebar.header("Regime Controls")
crisis_shock = st.sidebar.slider("Crisis Shock", 0.0, 1.0, 0.2, 0.01)
regime_prob = st.sidebar.slider("Regime Probability", 0.0, 1.0, 0.1, 0.01)

# Synthetic regime state
np.random.seed(42)
regime_states = np.zeros(n_time)
for t in range(n_time):
    if np.random.rand() < regime_prob:
        regime_states[t] = 2  # Crisis
    elif np.random.rand() < 0.3:
        regime_states[t] = 1  # Stress
    else:
        regime_states[t] = 0  # Calm

# Generate synthetic correlation matrices
corr_matrices = []
for t in range(n_time):
    base_corr = 0.1 + 0.2 * np.random.rand()
    if regime_states[t] == 1:
        base_corr += 0.2
    elif regime_states[t] == 2:
        base_corr += crisis_shock + 0.4
    mat = np.eye(n_clusters * n_assets_per_cluster)
    for c in range(n_clusters):
        start = c * n_assets_per_cluster
        end = start + n_assets_per_cluster
        intra = base_corr + 0.1 * np.random.rand()
        mat[start:end, start:end] = intra
    mat += 0.01 * np.random.randn(*mat.shape)
    np.fill_diagonal(mat, 1.0)
    mat = np.clip(mat, -1, 1)
    corr_matrices.append(mat)

# Compute cluster-level average correlations
avg_corrs = np.zeros((n_clusters, n_time))
for t in range(n_time):
    mat = corr_matrices[t]
    for c in range(n_clusters):
        start = c * n_assets_per_cluster
        end = start + n_assets_per_cluster
        cluster = mat[start:end, start:end]
        avg_corr = (np.sum(cluster) - n_assets_per_cluster) / (n_assets_per_cluster**2 - n_assets_per_cluster)
        avg_corrs[c, t] = avg_corr

# Color scale
def get_color(val):
    # Blue (low) → Orange → Red (high)
    if val < 0.3:
        return "#1f77b4"  # blue
    elif val < 0.6:
        return "#ff7f0e"  # orange
    else:
        return "#d62728"  # red

# Animation
frame = st.slider("Animation Frame", 0, n_time - 1, n_time - 1, 1)

# 3D Surface Plot
X, Y = np.meshgrid(np.arange(n_clusters), np.arange(n_time))
Z = avg_corrs.T

color_vals = np.array([get_color(val) for val in Z.flatten()])
color_vals = color_vals.reshape(Z.shape)

surface_colors = np.zeros(Z.shape, dtype=object)
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        surface_colors[i, j] = get_color(Z[i, j])

fig = go.Figure(
    data=[
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            surfacecolor=Z,
            colorscale=[
                [0, "#1f77b4"],
                [0.5, "#ff7f0e"],
                [1, "#d62728"]
            ],
            cmin=0,
            cmax=1,
            showscale=True,
            opacity=0.95,
        )
    ]
)
fig.update_layout(
    template="plotly_dark",
    margin=dict(l=0, r=0, b=0, t=40),
    scene=dict(
        xaxis_title="Asset Cluster",
        yaxis_title="Time",
        zaxis_title="Avg Intra-Cluster Correlation",
        zaxis=dict(range=[0, 1]),
        xaxis=dict(backgroundcolor="#181818"),
        yaxis=dict(backgroundcolor="#181818"),
        bgcolor="#181818",
    ),
    height=700,
)

# Animate morphing
if st.button("Play Animation"):
    import time
    for f in range(n_time):
        Z_anim = avg_corrs.T.copy()
        fig.data[0].z = Z_anim
        fig.data[0].surfacecolor = Z_anim
        st.plotly_chart(fig, use_container_width=True)
        time.sleep(0.05)
else:
    # Show current frame
    Z_frame = avg_corrs.T.copy()
    fig.data[0].z = Z_frame
    fig.data[0].surfacecolor = Z_frame
    st.plotly_chart(fig, use_container_width=True)

# Metrics Panel
st.sidebar.header("Metrics Panel")
avg_corr = np.mean(avg_corrs[:, frame])
systemic_risk = np.mean(regime_states[frame:frame+1]) * avg_corr
regime_state = ["Calm", "Stress", "Crisis"][int(regime_states[frame])]

st.sidebar.metric("Average Correlation", f"{avg_corr:.3f}")
st.sidebar.metric("Systemic Risk Score", f"{systemic_risk:.3f}")
st.sidebar.metric("Regime State", regime_state)

# requirements.txt
requirements = """
streamlit
numpy
pandas
plotly
"""
st.sidebar.header("requirements.txt")
st.sidebar.code(requirements)
