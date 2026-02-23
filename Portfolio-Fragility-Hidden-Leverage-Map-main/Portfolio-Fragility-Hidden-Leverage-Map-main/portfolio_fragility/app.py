import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from .engine import Portfolio

def main():
    st.set_page_config(page_title="3D Portfolio Fragility & Hidden Leverage Map", layout="wide")
    st.title("3D Portfolio Fragility & Hidden Leverage Map")
    st.markdown("""
    **Explore nonlinear risk, fragility, and hidden leverage in multi-asset portfolios.**
    
    - Realistic nonlinear risk logic (no simplifications)
    - Vol targeting, dynamic leverage, convex payoffs
    - Stress test: volatility, correlation, liquidity
    - 3D surface: Vol shock × Corr shock → Portfolio loss
    """)

    # Sidebar controls
    st.sidebar.header("Portfolio Controls")
    assets = ["Equity", "Bond", "Commodity", "Illiquid"]
    weights = [st.sidebar.slider(f"Weight: {a}", 0.0, 1.0, 0.25) for a in assets]
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]
    vol_target = st.sidebar.slider("Vol Target (ann.)", 0.05, 0.5, 0.1, 0.01)
    leverage = st.sidebar.slider("Leverage Multiplier", 0.5, 5.0, 1.0, 0.05)
    convexity = st.sidebar.slider("Convexity Strength", 0.0, 2.0, 0.0, 0.01)
    rebalance = st.sidebar.selectbox("Rebalance Frequency (days)", [1, 5, 21, 63], index=2)

    # Stress scenario controls
    st.sidebar.header("Stress Scenarios")
    vol_shock = st.sidebar.slider("Volatility Shock", 0.5, 3.0, 1.0, 0.05)
    corr_shock = st.sidebar.slider("Correlation Shock", 0.5, 3.0, 1.0, 0.05)
    liquidity_haircut = st.sidebar.slider("Liquidity Haircut (%)", 0.0, 0.5, 0.0, 0.01)

    # Asset params (realistic)
    mu = np.array([0.07, 0.03, 0.05, 0.02]) / 252
    vols = np.array([0.18, 0.07, 0.15, 0.10])
    base_corr = np.array([
        [1.0, 0.2, 0.1, 0.05],
        [0.2, 1.0, 0.05, 0.02],
        [0.1, 0.05, 1.0, 0.01],
        [0.05, 0.02, 0.01, 1.0]
    ])
    cov = np.outer(vols, vols) * base_corr / 252

    # Portfolio object
    port = Portfolio(assets, weights, vol_target, leverage, convexity)

    # 3D surface grid
    x_range = np.linspace(0.5, 2.0, 20)  # Vol shock
    y_range = np.linspace(0.5, 2.0, 20)  # Corr shock
    z = np.zeros((len(x_range), len(y_range)))
    for i, x in enumerate(x_range):
        for j, y in enumerate(y_range):
            rets, _ = port.simulate(mu, cov, n_days=252, rebalance_freq=rebalance, vol_shock=x, corr_shock=y, liquidity_haircut=liquidity_haircut)
            z[i, j] = np.sum(rets)

    # 3D Plotly surface
    fig = go.Figure(data=[go.Surface(z=z, x=x_range, y=y_range, colorscale='RdBu', reversescale=True)])
    fig.update_layout(
        title="Portfolio Loss Surface",
        scene=dict(
            xaxis_title="Volatility Shock",
            yaxis_title="Correlation Shock",
            zaxis_title="Portfolio Loss"
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Simulate base scenario for metrics
    rets, asset_rets = port.simulate(mu, cov, n_days=252, rebalance_freq=rebalance, vol_shock=vol_shock, corr_shock=corr_shock, liquidity_haircut=liquidity_haircut)
    dd = Portfolio.max_drawdown(rets)
    tail = Portfolio.tail_loss(rets)
    frag = Portfolio.fragility_index(rets)
    convex = Portfolio.convexity_score(rets)
    hidden_lev = Portfolio.hidden_leverage_score(rets, leverage)

    # Metrics panel
    st.header("Risk Metrics")
    st.markdown(f"**Max Drawdown:** {dd:.2%}")
    st.markdown(f"**Tail Loss (1%):** {tail:.2%}")
    st.markdown(f"**Fragility Index:** {frag:.2f}")
    st.markdown(f"**Convexity Score:** {convex:.4f}")
    st.markdown(f"**Hidden Leverage Score:** {hidden_lev:.4f}")

    # Math explanations
    with st.expander("Show Math & Risk Logic"):
        st.markdown("""
        **Portfolio Simulation:**
        - Simulates daily returns from a multivariate normal with shocked vol/corr.
        - Vol targeting: scales returns to target annualized volatility.
        - Leverage: multiplies scaled returns.
        - Convexity: adds quadratic (gamma) term to returns.
        
        **Drawdown:**
        $$DD_t = \frac{P_t - \max_{s \leq t} P_s}{\max_{s \leq t} P_s}$$
        
        **Tail Loss:**
        - 1st percentile of daily returns.
        
        **Fragility Index:**
        $$\text{Fragility} = \left| \frac{\text{Tail Loss}}{\text{Mean Return}} \right|$$
        
        **Convexity Score:**
        - Difference in volatility of positive vs. negative returns.
        
        **Hidden Leverage:**
        - Ratio of tail loss to stated leverage.
        """)
