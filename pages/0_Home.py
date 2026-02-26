"""QuantLib Pro — Home / Landing Page"""
import streamlit as st

st.markdown(
    """
    <style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1f77b4; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.2rem; color: #666; margin-bottom: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">QuantLib Pro</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Quantitative Finance Platform — '
    'Portfolio Optimization, Risk Analysis &amp; Derivatives Pricing</div>',
    unsafe_allow_html=True,
)

st.divider()

# ── Top feature cards ─────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### Portfolio Analysis")
        st.markdown(
            "- Mean-variance optimization\n"
            "- Efficient frontier visualization\n"
            "- Risk parity allocation\n"
            "- Performance analytics"
        )

with col2:
    with st.container(border=True):
        st.markdown("### Risk Management")
        st.markdown(
            "- Value-at-Risk (VaR) calculation\n"
            "- Stress testing & scenarios\n"
            "- Tail risk analysis\n"
            "- Real-time monitoring"
        )

with col3:
    with st.container(border=True):
        st.markdown("### Options Pricing")
        st.markdown(
            "- Black-Scholes · Bachelier · Binomial\n"
            "- Monte Carlo simulation\n"
            "- Greeks analysis\n"
            "- Volatility surface"
        )

st.divider()

# ── Additional features grid ──────────────────────────────────────────────────
st.markdown("### More Tools")

c1, c2, c3, c4 = st.columns(4)
tiles = [
    ("Market Regime",  "Detect market states via HMM"),
    ("Macro Analysis", "Economic indicators & yield curves"),
    ("Vol Surface",    "Implied volatility term structure"),
    ("Backtesting",    "Strategy performance testing"),
    ("Trading Signals","Momentum, mean-reversion, cross-overs"),
    ("Liquidity",      "Order book depth & flash-crash simulator"),
    ("Systemic Risk",  "Contagion network & concentration risk"),
    ("Stress Monitor", "Real-time facial stress detection"),
]

for i, (title, desc) in enumerate(tiles):
    col = [c1, c2, c3, c4][i % 4]
    with col:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(desc)

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center; color:#666; font-size:0.9rem;'>"
    "QuantLib Pro &copy; 2026 | Built with Streamlit | "
    "<a href='https://github.com/gdukens/quant-simulator' target='_blank'>GitHub</a>"
    "</div>",
    unsafe_allow_html=True,
)
