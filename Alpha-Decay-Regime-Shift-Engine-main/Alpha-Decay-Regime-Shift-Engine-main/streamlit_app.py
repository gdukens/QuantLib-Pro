import streamlit as st
import numpy as np
import pandas as pd
from alpha_engine.data import generate_synthetic_data
from alpha_engine.alphas import momentum_alpha, mean_reversion_alpha, volatility_carry_alpha
from alpha_engine.regime import detect_regimes, regime_persistence
from alpha_engine.decay import rolling_ic, alpha_decay_half_life
from alpha_engine.metrics import turnover_adjusted_returns
from alpha_engine.viz import plot_3d_surface

st.set_page_config(page_title="3D Alpha Decay & Regime Shift Engine", layout="wide", initial_sidebar_state="expanded")
st.title("3D Alpha Decay & Regime Shift Engine")

# Sidebar controls
st.sidebar.header("Parameters")
lookback = st.sidebar.slider("Lookback Window", 5, 120, 20, 1)
transaction_cost = st.sidebar.slider("Transaction Cost (bps)", 0, 50, 5, 1) / 10000
regime_sensitivity = st.sidebar.slider("Regime Sensitivity", 0.1, 3.0, 1.0, 0.05)
alpha_decay_speed = st.sidebar.slider("Alpha Decay Speed", 0.1, 2.0, 1.0, 0.05)

# Data generation
n_assets = st.sidebar.selectbox("Number of Assets", [1, 2, 3, 5, 10], index=2)
n_days = st.sidebar.slider("Number of Days", 250, 2000, 1000, 50)
data = generate_synthetic_data(n_assets=n_assets, n_days=n_days)

# Asset selection
assets = data['Asset'].unique()
asset = st.selectbox("Select Asset", assets)
asset_data = data[data['Asset'] == asset].set_index('Date')
prices = asset_data['Price']
returns = prices.pct_change().fillna(0)

# Alpha selection
alpha_type = st.selectbox("Alpha Type", ["Momentum", "Mean Reversion", "Volatility Carry"])
if alpha_type == "Momentum":
    alpha = momentum_alpha(prices, lookback)
elif alpha_type == "Mean Reversion":
    alpha = mean_reversion_alpha(prices, lookback)
else:
    alpha = volatility_carry_alpha(prices, lookback)

# Regime detection
hidden_states, hmm_model = detect_regimes(returns.values, n_regimes=3, regime_sensitivity=regime_sensitivity)
regime_series = pd.Series(hidden_states, index=returns.index)

# Rolling IC and half-life
future_returns = returns.shift(-lookback)
ic_series = rolling_ic(alpha, future_returns, window=lookback)
hl = alpha_decay_half_life(ic_series)
try:
    if hl is not None and not (isinstance(hl, float) and np.isnan(hl)):
        half_life = hl / alpha_decay_speed
    else:
        half_life = np.nan
except Exception:
    half_life = np.nan

# Turnover-adjusted returns
cumret, turnover = turnover_adjusted_returns(alpha, returns, transaction_cost)

# 3D Visualization
# Prepare meshgrid for surface: X=Time, Y=Regime, Z=Alpha Strength
T = np.arange(len(prices))
Y = regime_series.values
Z = alpha.values
fig = plot_3d_surface(T, Y, Z, animate=True)
st.plotly_chart(fig, use_container_width=True)

# Metrics panel
st.markdown("### Metrics Panel")
col1, col2, col3 = st.columns(3)
col1.metric("Alpha Half-Life", f"{half_life:.2f}" if not np.isnan(half_life) else "N/A")
col2.metric("Regime Persistence", f"{regime_persistence(hmm_model):.2f}")
col3.metric("Turnover-Adj. Return", f"{cumret.iloc[-1]:.2%}")

# Animation note
st.info("Use the Play button on the 3D chart to animate regime transitions over time.")
