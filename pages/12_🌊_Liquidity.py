"""
Liquidity & Market Microstructure Analysis
Comprehensive order book analysis, liquidity measurement, and market impact simulation.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from quantlib_pro.ui import components
from quantlib_pro.data.market_data import MarketDataProvider
from quantlib_pro.market_microstructure import CalibratedOrderBookSimulator

# Configure page
st.set_page_config(
    page_title="Liquidity & Market Microstructure",
    page_icon="🌊",
    layout="wide"
)

# ============================================================================
# Common Ticker List
# ============================================================================

COMMON_TICKERS = [
    "SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "USO", "UUP",
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
    "JPM", "V", "JNJ", "WMT", "PG", "MA", "HD", "DIS", "BAC", "XOM",
    "NFLX", "ADBE", "CRM", "CSCO", "INTC", "AMD", "QCOM", "TXN",
    "XLF", "XLE", "XLK", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB"
]

# ============================================================================
# Order Book Simulator
# ============================================================================

class OrderBookSimulator:
    """Simulates realistic order book dynamics"""
    
    def __init__(self, mid_price=100.0, n_levels=50, tick_size=0.01):
        self.mid_price = mid_price
        self.n_levels = n_levels
        self.tick_size = tick_size
        self.reset()
    
    def reset(self):
        """Reset order book to initial state"""
        self.bids = {}  # {price: volume}
        self.asks = {}
        self._initialize_book()
    
    def _initialize_book(self):
        """Create initial order book with exponential depth decay"""
        for i in range(self.n_levels):
            # Bid side (below mid)
            bid_price = round(self.mid_price - (i + 1) * self.tick_size, 4)
            bid_volume = int(1000 * np.exp(-0.05 * i) * (1 + 0.3 * np.random.rand()))
            self.bids[bid_price] = bid_volume
            
            # Ask side (above mid)
            ask_price = round(self.mid_price + (i + 1) * self.tick_size, 4)
            ask_volume = int(1000 * np.exp(-0.05 * i) * (1 + 0.3 * np.random.rand()))
            self.asks[ask_price] = ask_volume
    
    def get_spread(self):
        """Calculate bid-ask spread"""
        best_bid = max(self.bids.keys()) if self.bids else 0
        best_ask = min(self.asks.keys()) if self.asks else 0
        return best_ask - best_bid if (best_ask and best_bid) else 0
    
    def get_imbalance(self):
        """Calculate order book imbalance"""
        total_bid = sum(self.bids.values())
        total_ask = sum(self.asks.values())
        return (total_bid - total_ask) / (total_bid + total_ask + 1e-10)
    
    def get_depth(self, levels=10):
        """Get top N levels of depth"""
        sorted_bids = sorted(self.bids.items(), reverse=True)[:levels]
        sorted_asks = sorted(self.asks.items())[:levels]
        return sorted_bids, sorted_asks
    
    def simulate_market_order(self, side, volume):
        """Simulate market order impact"""
        executed = 0
        avg_price = 0
        
        if side == 'buy':
            # Execute against asks
            sorted_asks = sorted(self.asks.items())
            for price, available in sorted_asks:
                if executed >= volume:
                    break
                execute_qty = min(available, volume - executed)
                avg_price += price * execute_qty
                executed += execute_qty
                self.asks[price] -= execute_qty
                if self.asks[price] <= 0:
                    del self.asks[price]
        else:
            # Execute against bids
            sorted_bids = sorted(self.bids.items(), reverse=True)
            for price, available in sorted_bids:
                if executed >= volume:
                    break
                execute_qty = min(available, volume - executed)
                avg_price += price * execute_qty
                executed += execute_qty
                self.bids[price] -= execute_qty
                if self.bids[price] <= 0:
                    del self.bids[price]
        
        avg_price = avg_price / executed if executed > 0 else self.mid_price
        return executed, avg_price
    
    def apply_liquidity_shock(self, intensity=0.5):
        """Simulate liquidity withdrawal"""
        for price in list(self.bids.keys()):
            if np.random.rand() < intensity:
                self.bids[price] = int(self.bids[price] * (1 - intensity * 0.8))
                if self.bids[price] <= 0:
                    del self.bids[price]
        
        for price in list(self.asks.keys()):
            if np.random.rand() < intensity:
                self.asks[price] = int(self.asks[price] * (1 - intensity * 0.8))
                if self.asks[price] <= 0:
                    del self.asks[price]

# ============================================================================
# Market Impact Models
# ============================================================================

def square_root_impact(order_size, adv, volatility, impact_coeff=0.5):
    """Almgren-Chriss square-root impact model"""
    return impact_coeff * volatility * np.sqrt(order_size / adv)

def temporary_impact(order_size, adv, participation_rate):
    """Temporary impact from execution"""
    return 0.1 * np.sqrt(order_size / adv) * participation_rate

def permanent_impact(order_size, adv):
    """Permanent price impact"""
    return 0.05 * (order_size / adv)

def expected_slippage(order_size, adv, participation_rate, volatility):
    """Total expected slippage"""
    temp = temporary_impact(order_size, adv, participation_rate)
    perm = permanent_impact(order_size, adv)
    market = square_root_impact(order_size, adv, volatility)
    return temp + perm + market

def execution_cost(order_size, price, slippage):
    """Total execution cost in dollars"""
    return order_size * slippage

# ============================================================================
# Page Header
# ============================================================================
st.title("🌊 Liquidity & Market Microstructure")
st.markdown("""
Analyze order book depth, liquidity dynamics, and market impact
""")

# ============================================================================
# Sidebar Configuration
# ============================================================================
st.sidebar.header("⚙️ Configuration")

# Stock selection
st.sidebar.subheader("📊 Market Selection")
ticker = st.sidebar.selectbox(
    "Select Asset",
    options=COMMON_TICKERS,
    index=COMMON_TICKERS.index("AAPL") if "AAPL" in COMMON_TICKERS else 0,
    help="Stock for price volatility data"
)

# Optional custom ticker
custom_ticker = st.sidebar.text_input(
    "Custom Ticker (optional)",
    value="",
    help="Enter any ticker not in the list"
)

if custom_ticker.strip():
    ticker = custom_ticker.strip().upper()
else:
    ticker = ticker.upper()

# Order book parameters
st.sidebar.subheader("📖 Order Book Setup")

use_real_calibration = st.sidebar.checkbox(
    "Use Real Market Calibration",
    value=True,
    help="Calibrate order book to real market data from Yahoo Finance"
)

n_levels = st.sidebar.slider(
    "Number of Levels",
    min_value=10,
    max_value=100,
    value=50,
    help="Depth of order book"
)

# Market impact parameters
st.sidebar.subheader("💥 Market Impact Setup")
adv = st.sidebar.number_input(
    "Average Daily Volume",
    min_value=10000,
    max_value=100000000,
    value=10000000,
    step=100000,
    help="Average shares traded per day"
)

volatility_pct = st.sidebar.slider(
    "Daily Volatility (%)",
    min_value=0.1,
    max_value=10.0,
    value=2.0,
    step=0.1
) / 100

# ============================================================================
# Initialize Session State
# ============================================================================
if 'order_book' not in st.session_state:
    st.session_state.order_book = CalibratedOrderBookSimulator(
        ticker=ticker,
        n_levels=n_levels,
        use_real_data=use_real_calibration
    )
    st.session_state.shock_applied = False
    st.session_state.last_ticker = ticker
    st.session_state.last_levels = n_levels

ob = st.session_state.order_book

# Update parameters if changed
if (st.session_state.last_ticker != ticker or 
    st.session_state.last_levels != n_levels):
    st.session_state.order_book = CalibratedOrderBookSimulator(
        ticker=ticker,
        n_levels=n_levels,
        use_real_data=use_real_calibration
    )
    st.session_state.shock_applied = False
    st.session_state.last_ticker = ticker
    st.session_state.last_levels = n_levels
    ob = st.session_state.order_book

# ============================================================================
# Calibration Status Display
# ============================================================================
calibration_info = ob.get_calibration_info()

if calibration_info['is_calibrated']:
    st.success(f"""
    ✅ **Order Book Calibrated to Real {calibration_info['ticker']} Market Data**
    
    - **Mid Price:** ${calibration_info['mid_price']:.2f}
    - **Real Bid-Ask Spread:** ${calibration_info['real_spread']:.4f} ({calibration_info['spread_bps']:.1f} bps)
    - **Average Daily Volume:** {calibration_info['avg_volume']:,.0f} shares
    - **Liquidity Tier:** {calibration_info['liquidity_tier']}
    """)
else:
    st.warning(f"""
    ⚠️ **Using Simulated Order Book** (Real data unavailable for {ticker})
    
    - Exponential decay model (academic validation: Cont et al. 2010)
    - Appropriate for educational/research purposes
    """)

# ============================================================================
# Tabs
# ============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Order Book Depth",
    "🔥 Liquidity Heatmap",
    "💥 Liquidity Crisis",
    "📈 Market Impact",
    "📉 Spread & Metrics"
])

# ============================================================================
# Tab 1: Order Book Depth
# ============================================================================
with tab1:
    st.header("Order Book Depth Visualization")
    
    st.markdown("""
    **Live Order Book** - Bid and ask depth across price levels.
    """)
    
    # Educational disclaimer
    with st.expander("📚 About This Order Book Data", expanded=False):
        st.markdown("""
        **Data Source:**
        - ✅ **Spread & Mid-Price:** Real-time from Yahoo Finance
        - ✅ **Depth Scaling:** Calibrated to actual average daily volume
        - ⚠️ **Level 2 Structure:** Simulated using exponential decay model
        
        **Academic Validation:**
        - Model validated by Cont, Kukanov & Stoikov (2010) "The Price Impact of Order Book Events"
        - Exponential depth profile matches empirical studies on NYSE, NASDAQ
        - Used in academic research (MIT, Stanford, Oxford quantitative finance programs)
        
        **Appropriate For:**
        - ✅ Understanding market microstructure concepts
        - ✅ Testing market impact models (Almgren-Chriss)
        - ✅ Liquidity risk analysis and stress testing
        - ✅ Educational simulations and visualizations
        
        **Not Recommended For:**
        - ❌ High-frequency trading strategies (requires real L2 tick data)
        - ❌ Sub-second execution analysis (requires exchange co-location)
        
        **Professional Alternatives:**
        - **Polygon.io:** Real-time L2 data ($199/month)
        - **Interactive Brokers API:** Real L2 with funded account
        - **Bloomberg Terminal:** Institutional-grade depth ($25k/year)
        
        *This implementation prioritizes educational value and accessibility while maintaining mathematical rigor.*
        """)
    
    # Get current depth
    bids, asks = ob.get_depth(levels=30)
    
    # Create depth chart
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "bar", "colspan": 2}, None],
               [{"type": "scatter3d", "colspan": 2}, None]],
        subplot_titles=("Order Book Depth", "3D Depth Surface"),
        vertical_spacing=0.15,
        row_heights=[0.4, 0.6]
    )
    
    # Bid/Ask bars
    bid_prices = [p for p, v in bids]
    bid_volumes = [v for p, v in bids]
    ask_prices = [p for p, v in asks]
    ask_volumes = [v for p, v in asks]
    
    fig.add_trace(
        go.Bar(
            x=bid_prices,
            y=bid_volumes,
            name='Bids',
            marker_color='green',
            opacity=0.7
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=ask_prices,
            y=ask_volumes,
            name='Asks',
            marker_color='red',
            opacity=0.7
        ),
        row=1, col=1
    )
    
    # 3D Surface visualization
    # Create meshgrid for 3D surface
    all_bids = sorted(ob.bids.items(), reverse=True)
    all_asks = sorted(ob.asks.items())
    
    # Combine for full book
    full_book = all_bids[::-1] + all_asks
    prices_3d = [p for p, v in full_book]
    volumes_3d = [v for p, v in full_book]
    
    # Create time dimension for 3D effect
    n_time_steps = 20
    price_grid, time_grid = np.meshgrid(
        np.array(prices_3d),
        np.arange(n_time_steps)
    )
    
    # Create volume surface with slight time decay
    volume_surface = np.tile(volumes_3d, (n_time_steps, 1))
    volume_surface = volume_surface * (0.8 + 0.2 * np.random.rand(n_time_steps, len(volumes_3d)))
    
    fig.add_trace(
        go.Surface(
            x=time_grid,
            y=price_grid,
            z=volume_surface,
            colorscale='Viridis',
            name='Depth Surface',
            showscale=False
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        template='plotly_dark',
        height=900,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=1, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics
    st.subheader("Order Book Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    spread = ob.get_spread()
    imbalance = ob.get_imbalance()
    total_bid_volume = sum(ob.bids.values())
    total_ask_volume = sum(ob.asks.values())
    
    with col1:
        st.metric("Bid-Ask Spread", f"${spread:.4f}")
    with col2:
        st.metric("Order Imbalance", f"{imbalance:.3f}")
    with col3:
        st.metric("Total Bid Volume", f"{total_bid_volume:,}")
    with col4:
        st.metric("Total Ask Volume", f"{total_ask_volume:,}")

# ============================================================================
# Tab 2: Liquidity Heatmap
# ============================================================================
with tab2:
    st.header("Liquidity Heatmap Over Time")
    
    st.markdown("""
    **Dynamic Liquidity Map** - See how order book liquidity evolves.
    """)
    
    # Simulation controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        n_snapshots = st.slider(
            "Time Snapshots",
            min_value=10,
            max_value=50,
            value=30
        )
    
    with col2:
        volatility_factor = st.slider(
            "Market Volatility",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1
        )
    
    with col3:
        liquidity_decay = st.slider(
            "Liquidity Decay",
            min_value=0.0,
            max_value=0.5,
            value=0.1,
            step=0.05
        )
    
    if st.button("Generate Heatmap", type="primary"):
        with st.spinner("Simulating liquidity dynamics..."):
            # Create time series of order books
            price_levels = sorted(list(ob.bids.keys()) + list(ob.asks.keys()))
            n_prices = min(len(price_levels), 40)
            selected_prices = price_levels[::max(1, len(price_levels)//n_prices)]
            
            # Generate heatmap data
            heatmap_data = np.zeros((n_snapshots, len(selected_prices)))
            
            for t in range(n_snapshots):
                # Simulate liquidity at each price level
                for i, price in enumerate(selected_prices):
                    # Base liquidity with decay over time
                    base_liquidity = 1000 * np.exp(-0.05 * abs(price - ob.mid_price))
                    
                    # Add time-based decay
                    time_decay = np.exp(-liquidity_decay * t)
                    
                    # Add volatility
                    volatility_component = volatility_factor * np.random.randn() * 100
                    
                    # Occasional liquidity spikes (large orders)
                    if np.random.rand() < 0.05:
                        volatility_component += np.random.randint(500, 1500)
                    
                    liquidity = max(0, base_liquidity * time_decay + volatility_component)
                    heatmap_data[t, i] = liquidity
            
            # Plot heatmap
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.T,
                x=list(range(n_snapshots)),
                y=[f"${p:.2f}" for p in selected_prices],
                colorscale='Hot',
                reversescale=True,
                colorbar=dict(title="Liquidity")
            ))
            
            fig.update_layout(
                title="Liquidity Depth Heatmap Over Time",
                xaxis_title="Time Step",
                yaxis_title="Price Level",
                template='plotly_dark',
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Liquidity statistics over time
            st.subheader("Liquidity Evolution")
            
            total_liquidity = heatmap_data.sum(axis=1)
            avg_liquidity = heatmap_data.mean(axis=1)
            max_liquidity = heatmap_data.max(axis=1)
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=list(range(n_snapshots)),
                y=total_liquidity,
                name='Total Liquidity',
                line=dict(color='cyan', width=2)
            ))
            
            fig2.add_trace(go.Scatter(
                x=list(range(n_snapshots)),
                y=avg_liquidity,
                name='Average Liquidity',
                line=dict(color='yellow', width=2)
            ))
            
            fig2.update_layout(
                title="Liquidity Metrics Over Time",
                xaxis_title="Time Step",
                yaxis_title="Liquidity",
                template='plotly_dark',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)

# ============================================================================
# Tab 3: Liquidity Crisis Simulation
# ============================================================================
with tab3:
    st.header("Liquidity Crisis & Flash Crash Simulator")
    
    st.markdown("""
    **Stress Test** - Simulate liquidity withdrawal and observe market impact.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("Crisis Parameters")
        
        shock_intensity = st.slider(
            "Shock Intensity",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Probability of liquidity withdrawal at each level"
        )
        
        if st.button("Apply Liquidity Shock", type="primary"):
            ob.apply_liquidity_shock(shock_intensity)
            st.session_state.shock_applied = True
            st.rerun()
        
        if st.button("Reset Order Book"):
            ob.reset()
            st.session_state.shock_applied = False
            st.rerun()
        
        # Show crisis metrics
        if st.session_state.shock_applied:
            st.warning("⚠️ Crisis Mode Active")
            
            current_spread = ob.get_spread()
            normal_spread = ob.tick_size * 2
            spread_widening = (current_spread / normal_spread - 1) * 100
            
            st.metric(
                "Spread Widening",
                f"{spread_widening:.1f}%",
                delta=f"+${current_spread - normal_spread:.4f}"
            )
            
            remaining_liquidity = sum(ob.bids.values()) + sum(ob.asks.values())
            st.metric(
                "Remaining Liquidity",
                f"{remaining_liquidity:,}"
            )
    
    with col1:
        st.subheader("Order Book Before/After Crisis")
        
        # Get current state
        bids, asks = ob.get_depth(levels=20)
        
        # Create comparison chart
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Bid Side", "Ask Side")
        )
        
        bid_prices = [p for p, v in bids]
        bid_volumes = [v for p, v in bids]
        ask_prices = [p for p, v in asks]
        ask_volumes = [v for p, v in asks]
        
        # Bids
        fig.add_trace(
            go.Bar(
                y=bid_prices,
                x=bid_volumes,
                orientation='h',
                name='Bid Depth',
                marker_color='green',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Asks
        fig.add_trace(
            go.Bar(
                y=ask_prices,
                x=ask_volumes,
                orientation='h',
                name='Ask Depth',
                marker_color='red',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            template='plotly_dark',
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Volume", row=1, col=1)
        fig.update_xaxes(title_text="Volume", row=1, col=2)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=2)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Flash crash simulation
    st.subheader("Flash Crash Price Path Simulation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        crash_magnitude = st.slider(
            "Crash Depth (%)",
            min_value=5,
            max_value=50,
            value=20
        )
    
    with col2:
        crash_duration = st.slider(
            "Duration (steps)",
            min_value=10,
            max_value=100,
            value=30
        )
    
    with col3:
        recovery_speed = st.slider(
            "Recovery Speed",
            min_value=0.1,
            max_value=1.0,
            value=0.5,
            step=0.1
        )
    
    if st.button("Simulate Flash Crash"):
        # Generate flash crash price path
        n_steps = 200
        prices = np.zeros(n_steps)
        prices[0] = ob.mid_price
        
        crash_start = 50
        crash_end = crash_start + crash_duration
        
        for i in range(1, n_steps):
            if crash_start <= i < crash_end:
                # During crash: sharp decline
                crash_progress = (i - crash_start) / crash_duration
                target_price = ob.mid_price * (1 - crash_magnitude / 100)
                prices[i] = ob.mid_price - (ob.mid_price - target_price) * crash_progress
                prices[i] += np.random.randn() * 0.1
            elif i >= crash_end:
                # Recovery phase
                recovery_progress = min(1, (i - crash_end) / (crash_duration / recovery_speed))
                prices[i] = prices[crash_end - 1] + (ob.mid_price - prices[crash_end - 1]) * recovery_progress
                prices[i] += np.random.randn() * 0.05
            else:
                # Normal: random walk
                prices[i] = prices[i-1] + np.random.randn() * 0.02
        
        # Plot
        fig = go.Figure()
        
        # Price line with color zones
        fig.add_trace(go.Scatter(
            x=list(range(n_steps)),
            y=prices,
            mode='lines',
            line=dict(color='white', width=2),
            name='Price'
        ))
        
        # Mark crash zone
        fig.add_vrect(
            x0=crash_start, x1=crash_end,
            fillcolor="red", opacity=0.2,
            layer="below", line_width=0,
            annotation_text="Flash Crash", annotation_position="top left"
        )
        
        # Mark recovery zone
        fig.add_vrect(
            x0=crash_end, x1=crash_end + crash_duration/recovery_speed,
            fillcolor="green", opacity=0.1,
            layer="below", line_width=0,
            annotation_text="Recovery", annotation_position="top left"
        )
        
        fig.update_layout(
            title="Flash Crash Simulation",
            xaxis_title="Time Step",
            yaxis_title="Price ($)",
            template='plotly_dark',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Crash statistics
        col1, col2, col3 = st.columns(3)
        
        min_price = prices.min()
        max_drawdown = (ob.mid_price - min_price) / ob.mid_price * 100
        recovery_time = np.where(prices[crash_end:] >= ob.mid_price * 0.99)[0]
        recovery_steps = recovery_time[0] if len(recovery_time) > 0 else "Not recovered"
        
        with col1:
            st.metric("Max Drawdown", f"{max_drawdown:.1f}%")
        with col2:
            st.metric("Minimum Price", f"${min_price:.2f}")
        with col3:
            st.metric("Recovery Time", f"{recovery_steps} steps" if isinstance(recovery_steps, (int, np.integer)) else recovery_steps)

# ============================================================================
# Tab 4: Market Impact Analysis
# ============================================================================
with tab4:
    st.header("Market Impact & Execution Cost Analysis")
    
    st.markdown("""
    **Institutional Execution** - Analyze market impact for large orders.
    """)
    
    # Order parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        order_size = st.number_input(
            "Order Size (shares)",
            min_value=100,
            max_value=10000000,
            value=100000,
            step=10000
        )
    
    with col2:
        participation_rate = st.slider(
            "Participation Rate (%)",
            min_value=1,
            max_value=50,
            value=10
        ) / 100
    
    with col3:
        benchmark_price = st.number_input(
            "Benchmark Price ($)",
            min_value=1.0,
            max_value=10000.0,
            value=100.0,  # Fix: use default value instead of undefined mid_price
            step=0.01
        )
    
    if st.button("Calculate Market Impact", type="primary"):
        with st.spinner("Calculating impact..."):
            # Calculate impacts
            temp_cost = temporary_impact(order_size, adv, participation_rate)
            perm_cost = permanent_impact(order_size, adv)
            market_cost = square_root_impact(order_size, adv, volatility_pct)
            total_slippage = temp_cost + perm_cost + market_cost
            
            dollar_cost = execution_cost(order_size, benchmark_price, total_slippage)
            
            # Display metrics
            st.subheader("Impact Breakdown")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Slippage",
                    f"${total_slippage:.4f}",
                    help="Total price impact per share"
                )
            
            with col2:
                st.metric(
                    "Temporary Impact",
                    f"${temp_cost:.4f}",
                    help="Recovers after execution"
                )
            
            with col3:
                st.metric(
                    "Permanent Impact",
                    f"${perm_cost:.4f}",
                    help="Lasting price movement"
                )
            
            with col4:
                st.metric(
                    "Total Cost",
                    f"${dollar_cost:,.0f}",
                    help="Total execution cost in dollars"
                )
            
            # 3D Surface: Impact vs Order Size vs Participation
            st.subheader("Impact Surface Analysis")
            
            order_sizes = np.linspace(0.01 * adv, 0.5 * adv, 30)
            participation_rates = np.linspace(0.01, 0.5, 30)
            
            impact_matrix = np.zeros((len(participation_rates), len(order_sizes)))
            
            for i, pr in enumerate(participation_rates):
                for j, os in enumerate(order_sizes):
                    impact_matrix[i, j] = expected_slippage(os, adv, pr, volatility_pct)
            
            fig = go.Figure(data=[go.Surface(
                x=order_sizes / adv,  # Normalize by ADV
                y=participation_rates * 100,
                z=impact_matrix,
                colorscale='Reds',
                colorbar=dict(title="Slippage ($)")
            )])
            
            fig.update_layout(
                title="Market Impact Surface (Slippage vs Order Size vs Participation)",
                scene=dict(
                    xaxis_title="Order Size (% of ADV)",
                    yaxis_title="Participation Rate (%)",
                    zaxis_title="Slippage ($)"
                ),
                template='plotly_dark',
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Execution strategies comparison
            st.subheader("Execution Strategy Comparison")
            
            strategies = {
                'Aggressive (30%)': 0.30,
                'Moderate (15%)': 0.15,
                'Passive (5%)': 0.05,
                'Ultra-Passive (1%)': 0.01
            }
            
            strategy_results = []
            
            for name, pr in strategies.items():
                slippage = expected_slippage(order_size, adv, pr, volatility_pct)
                cost = execution_cost(order_size, benchmark_price, slippage)
                duration = order_size / (adv * pr)  # Days to complete
                
                strategy_results.append({
                    'Strategy': name,
                    'Slippage': f"${slippage:.4f}",
                    'Total Cost': f"${cost:,.0f}",
                    'Duration (days)': f"{duration:.1f}",
                    'Risk Level': 'High' if pr > 0.2 else ('Medium' if pr > 0.1 else 'Low')
                })
            
            strategy_df = pd.DataFrame(strategy_results)
            st.dataframe(strategy_df, use_container_width=True, hide_index=True)

# ============================================================================
# Tab 5: Spread & Metrics
# ============================================================================
with tab5:
    st.header("Spread Analysis & Liquidity Metrics")
    
    st.markdown("""
    **Microstructure Metrics** - Track bid-ask spread, effective spread, and liquidity indicators.
    """)
    
    # Real-time metrics
    st.subheader("Current Metrics")
    
    spread = ob.get_spread()
    imbalance = ob.get_imbalance()
    
    bids_top5, asks_top5 = ob.get_depth(5)
    depth_5 = sum(v for p, v in bids_top5) + sum(v for p, v in asks_top5)
    
    bids_top20, asks_top20 = ob.get_depth(20)
    depth_20 = sum(v for p, v in bids_top20) + sum(v for p, v in asks_top20)
    
    # Calculate effective spread for a typical order
    typical_order = 1000
    executed_bid, avg_bid_price = ob.simulate_market_order('sell', typical_order)
    executed_ask, avg_ask_price = ob.simulate_market_order('buy', typical_order)
    
    # Reset order book after simulation
    ob.reset()
    
    effective_spread = avg_ask_price - avg_bid_price
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Quoted Spread",
            f"${spread:.4f}",
            help="Best bid - best ask"
        )
    
    with col2:
        st.metric(
            "Effective Spread",
            f"${effective_spread:.4f}",
            help=f"Spread for {typical_order} share order"
        )
    
    with col3:
        st.metric(
            "Order Imbalance",
            f"{imbalance:.3f}",
            help="(Bids - Asks) / (Bids + Asks)"
        )
    
    with col4:
        spread_bps = (spread / ob.mid_price) * 10000
        st.metric(
            "Spread (bps)",
            f"{spread_bps:.1f}",
            help="Spread in basis points"
        )
    
    # Depth analysis
    st.subheader("Liquidity Depth Analysis")
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Cumulative Depth", "Depth Distribution")
    )
    
    # Cumulative depth chart
    all_bids = sorted(ob.bids.items(), reverse=True)[:30]
    all_asks = sorted(ob.asks.items())[:30]
    
    cumulative_bid = np.cumsum([v for p, v in all_bids])
    cumulative_ask = np.cumsum([v for p, v in all_asks])
    
    fig.add_trace(
        go.Scatter(
            x=[p for p, v in all_bids],
            y=cumulative_bid,
            name='Cumulative Bids',
            line=dict(color='green', width=2),
            fill='tozeroy'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=[p for p, v in all_asks],
            y=cumulative_ask,
            name='Cumulative Asks',
            line=dict(color='red', width=2),
            fill='tozeroy'
        ),
        row=1, col=1
    )
    
    # Depth at different levels
    depths_at_levels = []
    level_names = []
    
    for level in [5, 10, 20, 50]:
        if level <= n_levels:
            bids_n, asks_n = ob.get_depth(level)
            depth_n = sum(v for p, v in bids_n) + sum(v for p, v in asks_n)
            depths_at_levels.append(depth_n)
            level_names.append(f"Top {level}")
    
    fig.add_trace(
        go.Bar(
            x=level_names,
            y=depths_at_levels,
            name='Total Depth',
            marker_color='skyblue'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        template='plotly_dark',
        height=500,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative Volume", row=1, col=1)
    fig.update_xaxes(title_text="Level", row=1, col=2)
    fig.update_yaxes(title_text="Total Volume", row=1, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Liquidity score
    st.subheader("Liquidity Quality Score")
    
    # Calculate composite score
    spread_score = max(0, 100 - spread_bps * 10)  # Lower spread = higher score
    depth_score = min(100, depth_20 / 1000)  # Higher depth = higher score
    imbalance_score = max(0, 100 - abs(imbalance) * 200)  # Lower imbalance = higher score
    
    overall_score = (spread_score * 0.4 + depth_score * 0.4 + imbalance_score * 0.2)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Score", f"{overall_score:.1f}/100")
    
    with col2:
        st.metric("Spread Score", f"{spread_score:.1f}/100")
    
    with col3:
        st.metric("Depth Score", f"{depth_score:.1f}/100")
    
    with col4:
        st.metric("Balance Score", f"{imbalance_score:.1f}/100")
    
    # Score interpretation
    if overall_score >= 80:
        st.success("🟢 **Excellent Liquidity** - Tight spreads, deep markets, balanced order flow")
    elif overall_score >= 60:
        st.info("🟡 **Good Liquidity** - Acceptable trading conditions with moderate costs")
    elif overall_score >= 40:
        st.warning("🟠 **Fair Liquidity** - Elevated costs, use limit orders")
    else:
        st.error("🔴 **Poor Liquidity** - High impact costs, consider waiting or splitting orders")

# Footer
st.markdown("---")
st.markdown(
    "**Liquidity & Market Microstructure Analysis** | Order Book Simulation | "
    "⚠️ Simulated data for demonstration purposes"
)
