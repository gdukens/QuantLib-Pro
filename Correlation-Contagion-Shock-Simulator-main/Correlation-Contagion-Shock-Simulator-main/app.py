import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.linalg import eigh
from scipy.linalg import sqrtm

# ----------------------
# Utility Functions
# ----------------------
def make_psd(matrix, tol=1e-8):
    # Ensure matrix is symmetric and positive semi-definite
    sym = (matrix + matrix.T) / 2
    eigvals, eigvecs = eigh(sym)
    eigvals[eigvals < tol] = tol
    psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
    return (psd + psd.T) / 2

def nonlinear_shock(corr, shock):
    # Nonlinear transformation: push correlations toward 1 as shock increases
    # shock in [0, 1]
    return corr + (1 - corr) * (1 - np.exp(-3 * shock))

def simulate_cov_matrix(n_assets, base_corr, vol, shock):
    # Build base correlation matrix
    corr = np.full((n_assets, n_assets), base_corr)
    np.fill_diagonal(corr, 1.0)
    # Apply nonlinear shock
    shocked_corr = nonlinear_shock(corr, shock)
    shocked_corr = (shocked_corr + shocked_corr.T) / 2
    # Ensure PSD
    shocked_corr = make_psd(shocked_corr)
    # Build covariance
    vol_vec = np.full(n_assets, vol)
    cov = shocked_corr * np.outer(vol_vec, vol_vec)
    cov = make_psd(cov)
    return cov, shocked_corr

def portfolio_variance(cov, weights):
    return float(weights.T @ cov @ weights)

def max_drawdown(returns):
    # Compute max drawdown from cumulative returns
    cum = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(cum)
    dd = (cum - peak) / peak
    return np.min(dd)

def diversification_collapse(eigvals):
    # Collapse metric: largest eigenvalue / sum of all
    return eigvals[-1] / np.sum(eigvals)

# ----------------------
# Streamlit UI
# ----------------------
st.set_page_config(
    page_title="3D Correlation Contagion Shock Simulator",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📉"
)

st.markdown(
    """
    <style>
    body, .stApp { background-color: #18191A; color: #F5F6FA; }
    .st-bb { background: #23272F !important; }
    .st-cq { color: #F5F6FA !important; }
    .st-dc { color: #F5F6FA !important; }
    .st-eb { color: #F5F6FA !important; }
    .st-emotion-cache-1v0mbdj { background: #23272F !important; }
    .st-emotion-cache-1v0mbdj p { color: #F5F6FA !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("3D Correlation Contagion Shock Simulator")
st.markdown("""
Simulate how correlation breakdowns during stress events impact portfolio drawdowns, eigenvalue instability, and diversification collapse.
""")

# Sidebar controls
with st.sidebar:
    st.header("Simulation Controls")
    n_assets = st.slider("Number of Assets", 3, 30, 10)
    base_corr = st.slider("Base Correlation", 0.0, 0.99, 0.3, 0.01)
    vol = st.slider("Volatility (annualized %)", 1.0, 100.0, 20.0, 0.1) / 100
    time_steps = st.slider("Time Steps", 50, 500, 200, 10)
    shock_min, shock_max = st.slider("Shock Intensity Range", 0.0, 1.0, (0.0, 1.0), 0.01)
    shock_grid_points = st.slider("Shock Grid Points", 5, 30, 15)
    corr_min, corr_max = st.slider("Correlation Range", 0.0, 0.99, (base_corr, 0.99), 0.01)
    corr_grid_points = st.slider("Correlation Grid Points", 5, 20, 10)
    st.markdown("**Portfolio Weights** (sum to 1)")
    default_weights = np.ones(n_assets) / n_assets
    weights_input = st.text_area(
        "Comma-separated weights (optional)",
        value=", ".join(f"{w:.3f}" for w in default_weights),
        height=60
    )
    try:
        weights = np.array([float(x) for x in weights_input.split(",")])
        if len(weights) != n_assets or np.any(weights < 0):
            raise ValueError
        weights = weights / np.sum(weights)
    except Exception:
        st.warning("Invalid weights. Using equal weights.")
        weights = default_weights

# Prepare grid
shock_grid = np.linspace(shock_min, shock_max, shock_grid_points)
corr_grid = np.linspace(corr_min, corr_max, corr_grid_points)

# Results storage
drawdown_surface = np.zeros((corr_grid_points, shock_grid_points))
largest_eigen_surface = np.zeros_like(drawdown_surface)
div_collapse_surface = np.zeros_like(drawdown_surface)

# Main simulation loop
for i, base_c in enumerate(corr_grid):
    for j, shock in enumerate(shock_grid):
        cov, shocked_corr = simulate_cov_matrix(n_assets, base_c, vol, shock)
        # Simulate returns
        try:
            returns = np.random.multivariate_normal(
                mean=np.zeros(n_assets),
                cov=cov,
                size=time_steps
            ) @ weights
        except np.linalg.LinAlgError:
            # Fallback: add jitter
            cov = make_psd(cov + np.eye(n_assets) * 1e-6)
            returns = np.random.multivariate_normal(
                mean=np.zeros(n_assets),
                cov=cov,
                size=time_steps
            ) @ weights
        dd = max_drawdown(returns)
        eigvals = np.sort(eigh(shocked_corr, eigvals_only=True))
        drawdown_surface[i, j] = -dd  # positive drawdown
        largest_eigen_surface[i, j] = eigvals[-1]
        div_collapse_surface[i, j] = diversification_collapse(eigvals)

# 3D Surface Plot
fig = go.Figure()
fig.add_trace(go.Surface(
    x=shock_grid,
    y=corr_grid,
    z=drawdown_surface,
    colorscale="Inferno",
    colorbar=dict(title="Drawdown", tickformat=".2%"),
    name="Drawdown"
))
fig.update_layout(
    title="Portfolio Drawdown Surface",
    scene=dict(
        xaxis_title="Shock Intensity",
        yaxis_title="Base Correlation",
        zaxis_title="Portfolio Drawdown",
        bgcolor="#18191A",
        xaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
        yaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
        zaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
    ),
    margin=dict(l=10, r=10, b=10, t=40),
    paper_bgcolor="#18191A",
    font=dict(color="#F5F6FA")
)
st.plotly_chart(fig, use_container_width=True)

# Eigenvalue Visualization
st.subheader("Eigenvalue Instability and Diversification Collapse")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Largest Eigenvalue Surface**")
    fig_eig = go.Figure(go.Surface(
        x=shock_grid,
        y=corr_grid,
        z=largest_eigen_surface,
        colorscale="Viridis",
        colorbar=dict(title="Largest Eigenvalue"),
        name="Largest Eigenvalue"
    ))
    fig_eig.update_layout(
        scene=dict(
            xaxis_title="Shock Intensity",
            yaxis_title="Base Correlation",
            zaxis_title="Largest Eigenvalue",
            bgcolor="#18191A",
            xaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
            yaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
            zaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
        ),
        margin=dict(l=10, r=10, b=10, t=40),
        paper_bgcolor="#18191A",
        font=dict(color="#F5F6FA")
    )
    st.plotly_chart(fig_eig, use_container_width=True)

with col2:
    st.markdown("**Diversification Collapse Metric**")
    fig_div = go.Figure(go.Surface(
        x=shock_grid,
        y=corr_grid,
        z=div_collapse_surface,
        colorscale="Cividis",
        colorbar=dict(title="Collapse Metric"),
        name="Collapse"
    ))
    fig_div.update_layout(
        scene=dict(
            xaxis_title="Shock Intensity",
            yaxis_title="Base Correlation",
            zaxis_title="Collapse Metric",
            bgcolor="#18191A",
            xaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
            yaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
            zaxis=dict(backgroundcolor="#23272F", color="#F5F6FA"),
        ),
        margin=dict(l=10, r=10, b=10, t=40),
        paper_bgcolor="#18191A",
        font=dict(color="#F5F6FA")
    )
    st.plotly_chart(fig_div, use_container_width=True)

# Show sample eigenvalues for selected scenario
st.subheader("Sample Eigenvalues (Selected Parameters)")
cov, shocked_corr = simulate_cov_matrix(n_assets, base_corr, vol, shock_max)
eigvals = np.sort(eigh(shocked_corr, eigvals_only=True))

st.write(pd.DataFrame({
    "Eigenvalue": eigvals[::-1],
    "% of Total": eigvals[::-1] / np.sum(eigvals)
}))

st.markdown("""
---
**Notes:**
- Drawdown is simulated from synthetic returns using the shocked covariance matrix.
- Largest eigenvalue growth signals concentration risk and loss of diversification.
- Diversification collapse metric = Largest eigenvalue / sum(all eigenvalues).
- All matrices are forced to be positive semi-definite for stability.
""")
