import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Dynamic Efficient Frontier Lab",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💹"
)

# --- Dark Theme Styling ---
st.markdown(
    """
    <style>
    body, .stApp { background-color: #18191A; color: #F5F6FA; }
    .stSlider > div { color: #F5F6FA; }
    .st-bb { background: #23272F; }
    .st-cq { color: #F5F6FA; }
    .stPlotlyChart { background: #18191A !important; }
    .css-1v0mbdj { background: #18191A; }
    .css-1d391kg { background: #18191A; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar Controls ---
st.sidebar.title("⚙️ Settings")
num_assets = st.sidebar.slider("Number of Assets", min_value=2, max_value=10, value=4, step=1)
sim_count = st.sidebar.slider("Simulation Count", min_value=500, max_value=10000, value=5000, step=500)
risk_free_rate = st.sidebar.slider("Risk-Free Rate (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1) / 100

# --- Synthetic Data Generation ---
np.random.seed(42)
days = 252
mean_returns = np.random.uniform(0.05, 0.25, num_assets) / 252  # daily mean
volatilities = np.random.uniform(0.10, 0.40, num_assets) / np.sqrt(252)  # daily std
corr_matrix = np.eye(num_assets)
for i in range(num_assets):
    for j in range(i+1, num_assets):
        corr = np.random.uniform(0.2, 0.8)
        corr_matrix[i, j] = corr
        corr_matrix[j, i] = corr
cov_matrix = np.outer(volatilities, volatilities) * corr_matrix
returns = np.random.multivariate_normal(mean_returns, cov_matrix, size=days)
prices = 100 * np.exp(np.cumsum(returns, axis=0))
assets = [f"Asset {i+1}" for i in range(num_assets)]
prices_df = pd.DataFrame(prices, columns=assets)

# --- Portfolio Simulation ---
port_returns = []
port_vols = []
port_sharpes = []
port_weights = []
for _ in range(sim_count):
    weights = np.random.dirichlet(np.ones(num_assets))
    exp_return = np.sum(mean_returns * weights) * days
    exp_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * days, weights)))
    sharpe = (exp_return - risk_free_rate) / exp_vol if exp_vol > 0 else 0
    port_returns.append(exp_return)
    port_vols.append(exp_vol)
    port_sharpes.append(sharpe)
    port_weights.append(weights)
port_returns = np.array(port_returns)
port_vols = np.array(port_vols)
port_sharpes = np.array(port_sharpes)
port_weights = np.array(port_weights)

# --- Find Special Portfolios ---
max_sharpe_idx = np.argmax(port_sharpes)
min_vol_idx = np.argmin(port_vols)

# --- Plotly Efficient Frontier ---
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=port_vols, y=port_returns,
    mode='markers',
    marker=dict(
        size=7,
        color=port_sharpes,
        colorscale='Viridis',
        colorbar=dict(title='Sharpe', thickness=20, x=1.02, y=0.5, len=0.8, outlinewidth=0, tickcolor='#fff'),
        line=dict(width=0.5, color='#222'),
        showscale=True
    ),
    text=[
        '<br>'.join([
            f"<b>{assets[i]}</b>: {w*100:.1f}%" for i, w in enumerate(ws)
        ]) for ws in port_weights
    ],
    hovertemplate=(
        'Volatility: <b>%{x:.2%}</b><br>'
        'Return: <b>%{y:.2%}</b><br>'
        'Sharpe: <b>%{marker.color:.2f}</b><br>'
        '%{text}<extra></extra>'
    ),
    name='Portfolios'
))
# Highlight max Sharpe
fig.add_trace(go.Scatter(
    x=[port_vols[max_sharpe_idx]],
    y=[port_returns[max_sharpe_idx]],
    mode='markers',
    marker=dict(color='red', size=16, line=dict(width=2, color='white')),
    name='Max Sharpe',
    hovertemplate=(
        '<b>Max Sharpe Portfolio</b><br>'
        'Volatility: <b>%{x:.2%}</b><br>'
        'Return: <b>%{y:.2%}</b><br>'
        'Sharpe: <b>' + f'{port_sharpes[max_sharpe_idx]:.2f}' + '</b><extra></extra>'
    )
))
# Highlight min Volatility
fig.add_trace(go.Scatter(
    x=[port_vols[min_vol_idx]],
    y=[port_returns[min_vol_idx]],
    mode='markers',
    marker=dict(color='cyan', size=16, line=dict(width=2, color='white')),
    name='Min Volatility',
    hovertemplate=(
        '<b>Min Volatility Portfolio</b><br>'
        'Volatility: <b>%{x:.2%}</b><br>'
        'Return: <b>%{y:.2%}</b><br>'
        'Sharpe: <b>' + f'{port_sharpes[min_vol_idx]:.2f}' + '</b><extra></extra>'
    )
))
fig.update_layout(
    template='plotly_dark',
    title='<b>Dynamic Efficient Frontier</b>',
    xaxis=dict(title='Volatility (Std Dev)', tickformat='.0%', gridcolor='#333'),
    yaxis=dict(title='Expected Return', tickformat='.0%', gridcolor='#333'),
    legend=dict(font=dict(size=16), orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    plot_bgcolor='#18191A',
    paper_bgcolor='#18191A',
    font=dict(size=18, color='#F5F6FA'),
    margin=dict(l=40, r=40, t=60, b=40),
    height=700,
)

# --- Streamlit Layout ---
st.title("💹 Dynamic Efficient Frontier Lab")
st.markdown("""
This interactive lab generates synthetic asset data and visualizes the efficient frontier for randomly simulated portfolios. 
- **Drag the sliders** to change the number of assets, simulation count, and risk-free rate.
- **Hover** on points for portfolio weights.
- **Red** = Max Sharpe, **Cyan** = Min Volatility.
""")
st.plotly_chart(fig, use_container_width=True)

# --- Show Portfolio Details ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Max Sharpe Portfolio")
    st.write(pd.DataFrame({
        'Asset': assets,
        'Weight (%)': (port_weights[max_sharpe_idx]*100).round(2)
    }))
    st.metric("Sharpe Ratio", f"{port_sharpes[max_sharpe_idx]:.2f}")
    st.metric("Expected Return", f"{port_returns[max_sharpe_idx]*100:.2f}%")
    st.metric("Volatility", f"{port_vols[max_sharpe_idx]*100:.2f}%")
with col2:
    st.subheader("Min Volatility Portfolio")
    st.write(pd.DataFrame({
        'Asset': assets,
        'Weight (%)': (port_weights[min_vol_idx]*100).round(2)
    }))
    st.metric("Sharpe Ratio", f"{port_sharpes[min_vol_idx]:.2f}")
    st.metric("Expected Return", f"{port_returns[min_vol_idx]*100:.2f}%")
    st.metric("Volatility", f"{port_vols[min_vol_idx]*100:.2f}%")

st.caption("© 2026 Dynamic Efficient Frontier Lab. All synthetic data. No internet required.")
