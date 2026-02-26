"""
Systemic Risk & Contagion Analysis
Network-based analysis of systemic risk, contagion effects, and portfolio fragility.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# import networkx as nx  # Not available in current environment
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from quantlib_pro.ui import components
from quantlib_pro.data.market_data import MarketDataProvider

# Configure page
st.set_page_config(
    page_title="Systemic Risk & Contagion",
    page_icon="",
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
# Helper Classes
# ============================================================================

class ContagionNetwork:
    """Model financial contagion through network structure (NetworkX-free implementation)"""
    
    def __init__(self, n_nodes=20):
        self.n_nodes = n_nodes
        self.adjacency_matrix = np.zeros((n_nodes, n_nodes))
        self.weights = {}
        self._build_network()
    
    def _build_network(self):
        """Build random network with preferential attachment"""
        # Add edges with preferential attachment (scale-free network)
        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                # Probability decreases with distance
                prob = 0.3 * np.exp(-0.1 * abs(i - j))
                if np.random.rand() < prob:
                    weight = np.random.uniform(0.1, 1.0)
                    self.adjacency_matrix[i, j] = weight
                    self.adjacency_matrix[j, i] = weight  # Symmetric
                    self.weights[(i, j)] = weight
                    self.weights[(j, i)] = weight
    
    def get_neighbors(self, node):
        """Get neighbors of a node"""
        return [i for i in range(self.n_nodes) if self.adjacency_matrix[node, i] > 0]
    
    def get_edge_weight(self, node1, node2):
        """Get weight of edge between two nodes"""
        return self.adjacency_matrix[node1, node2]
    
    def simulate_shock(self, initial_nodes, shock_strength=1.0, decay=0.8, max_steps=10):
        """Simulate shock propagation through network"""
        
        # Initialize impact levels
        impact = np.zeros(self.n_nodes)
        
        # Set initial shocks
        for node in initial_nodes:
            if node < self.n_nodes:
                impact[node] = shock_strength
        
        # Track history
        history = [impact.copy()]
        
        # Propagate shock
        for step in range(max_steps):
            new_impact = impact.copy()
            
            for node in range(self.n_nodes):
                # Calculate incoming shock from neighbors
                neighbor_shock = 0.0
                neighbors = self.get_neighbors(node)
                
                for neighbor in neighbors:
                    edge_weight = self.get_edge_weight(node, neighbor)
                    neighbor_shock += impact[neighbor] * edge_weight * decay
                
                # Update impact (accumulate)
                new_impact[node] = max(impact[node], neighbor_shock)
            
            impact = new_impact
            history.append(impact.copy())
        
        return history
    
    def calculate_centrality(self):
        """Calculate simple centrality measures without NetworkX"""
        # Degree centrality (number of connections)
        degree_cent = {}
        for i in range(self.n_nodes):
            degree = np.sum(self.adjacency_matrix[i] > 0)
            degree_cent[i] = degree / (self.n_nodes - 1) if self.n_nodes > 1 else 0
        
        # Simple betweenness approximation (weighted degree)
        betweenness_cent = {}
        for i in range(self.n_nodes):
            weighted_degree = np.sum(self.adjacency_matrix[i])
            betweenness_cent[i] = weighted_degree / np.sum(self.adjacency_matrix) if np.sum(self.adjacency_matrix) > 0 else 0
        
        # Eigenvector centrality approximation (iterative approach)
        eigenvector_cent = {}
        centrality = np.ones(self.n_nodes)
        for _ in range(10):  # Simple iteration
            new_centrality = np.dot(self.adjacency_matrix, centrality)
            if np.sum(new_centrality) > 0:
                centrality = new_centrality / np.linalg.norm(new_centrality)
        
        for i in range(self.n_nodes):
            eigenvector_cent[i] = centrality[i]
        
        return {
            'degree': degree_cent,
            'betweenness': betweenness_cent,
            'eigenvector': eigenvector_cent
        }
    
    def get_spring_layout(self, seed=42):
        """Generate spring layout positions for network visualization"""
        np.random.seed(seed)
        positions = {}
        
        # Generate initial random positions
        for i in range(self.n_nodes):
            positions[i] = np.random.uniform(-1, 1, 2)
        
        # Simple spring layout algorithm
        for iteration in range(50):  # 50 iterations
            forces = {i: np.zeros(2) for i in range(self.n_nodes)}
            
            # Calculate forces
            for i in range(self.n_nodes):
                for j in range(self.n_nodes):
                    if i != j:
                        diff = positions[j] - positions[i]
                        dist = np.linalg.norm(diff)
                        if dist > 0:
                            # Repulsive force
                            forces[i] -= diff / (dist ** 2) * 0.1
                            
                            # Attractive force for connected nodes
                            if self.adjacency_matrix[i, j] > 0:
                                forces[i] += diff * 0.05
            
            # Update positions
            for i in range(self.n_nodes):
                positions[i] += forces[i] * 0.1
                # Keep within bounds
                positions[i] = np.clip(positions[i], -2, 2)
        
        return positions
    
    def get_edges(self):
        """Get list of edges with weights"""
        edges = []
        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                if self.adjacency_matrix[i, j] > 0:
                    edges.append((i, j, self.adjacency_matrix[i, j]))
        return edges
    
    def get_nodes(self):
        """Get list of nodes"""
        return list(range(self.n_nodes))
    
    def number_of_edges(self):
        """Get total number of edges"""
        return len(self.get_edges())
    
    def get_density(self):
        """Calculate network density"""
        max_edges = self.n_nodes * (self.n_nodes - 1) / 2
        actual_edges = self.number_of_edges()
        return actual_edges / max_edges if max_edges > 0 else 0

def calculate_portfolio_fragility(returns_df, lookback=60):
    """Calculate portfolio fragility metrics"""
    
    # Rolling correlation
    rolling_corr = returns_df.rolling(lookback).corr()
    
    # Average correlation (measure of concentration risk)
    avg_correlations = []
    dates = returns_df.index[lookback:]
    
    for date in dates:
        corr_matrix = returns_df.loc[:date].tail(lookback).corr()
        mask = ~np.eye(len(corr_matrix), dtype=bool)
        avg_corr = corr_matrix.values[mask].mean()
        avg_correlations.append(avg_corr)
    
    # Volatility concentration
    rolling_vol = returns_df.rolling(lookback).std()
    vol_concentration = rolling_vol.max(axis=1) / (rolling_vol.mean(axis=1) + 1e-10)
    
    # Hidden leverage indicator (vol regime jumps)
    vol_change = rolling_vol.mean(axis=1).pct_change()
    leverage_spikes = (vol_change > vol_change.quantile(0.95)).astype(int)
    
    return {
        'avg_correlation': pd.Series(avg_correlations, index=dates),
        'vol_concentration': vol_concentration,
        'leverage_spikes': leverage_spikes
    }

# ============================================================================
# Page Header
# ============================================================================
st.title("Systemic Risk & Contagion Analysis")
st.markdown("""
Network-based analysis of interconnected risks and cascade effects
""")

# ============================================================================
# Sidebar Configuration
# ============================================================================
st.sidebar.header("Configuration")

# Stock selection
st.sidebar.subheader("Asset Universe")

# Multi-select dropdown
selected_tickers = st.sidebar.multiselect(
    "Select Assets",
    options=COMMON_TICKERS,
    default=["SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "USO", "UUP"],
    help="Select multiple assets to analyze for systemic risk"
)

# Optional custom tickers
custom_tickers = st.sidebar.text_input(
    "Add Custom Tickers (comma-separated)",
    value="",
    help="Add any tickers not in the list"
)

if custom_tickers.strip():
    custom_list = [t.strip().upper() for t in custom_tickers.split(',') if t.strip()]
    selected_tickers.extend(custom_list)

tickers = selected_tickers

# Date range
st.sidebar.subheader("Date Range")
date_preset = st.sidebar.selectbox(
    "Preset Range",
    ["6 Months", "1 Year", "2 Years", "3 Years", "Custom"]
)

if date_preset == "Custom":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start", value=datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End", value=datetime.now())
else:
    days_map = {"6 Months": 180, "1 Year": 365, "2 Years": 730, "3 Years": 1095}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_map[date_preset])

# Contagion parameters
st.sidebar.subheader("Contagion Setup")
shock_strength = st.sidebar.slider(
    "Initial Shock Strength",
    min_value=0.1,
    max_value=3.0,
    value=1.0,
    step=0.1
)

decay_rate = st.sidebar.slider(
    "Decay Rate",
    min_value=0.3,
    max_value=0.95,
    value=0.7,
    step=0.05,
    help="How much shock dissipates through network"
)

# ============================================================================
# Load Data
# ============================================================================
@st.cache_data(ttl=300)
def load_multi_asset_data(tickers, start, end):
    provider = MarketDataProvider()
    all_data = {}
    
    for ticker in tickers:
        try:
            data = provider.get_stock_data(ticker, start_date=start, end_date=end)
            if not data.empty:
                all_data[ticker] = data['Close']
        except Exception as e:
            logger.warning(f"Failed to load {ticker}: {str(e)}")
    
    return pd.DataFrame(all_data)

try:
    if not tickers:
        st.error("Please select at least one ticker")
        st.stop()
    
    with st.spinner(f"Loading data for {len(tickers)} assets..."):
        price_data = load_multi_asset_data(tickers, start_date, end_date)
    
    if price_data.empty:
        st.error("No data available for the selected tickers")
        st.stop()
    
    # Calculate returns
    returns_data = price_data.pct_change().dropna()
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Assets Loaded", len(price_data.columns))
    with col2:
        st.metric("Data Points", len(price_data))
    with col3:
        st.metric("Date Range", f"{(end_date - start_date).days} days")
    with col4:
        avg_vol = returns_data.std().mean() * np.sqrt(252) * 100
        st.metric("Avg Volatility", f"{avg_vol:.1f}%")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# ============================================================================
# Tabs
# ============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    " Contagion Network",
    " Correlation Shock",
    " Crash Cascade",
    " Portfolio Fragility",
    " Matrix Evolution",
    " 3D Market Contagion"
])

# ============================================================================
# Tab 1: Contagion Network
# ============================================================================
with tab1:
    st.header("Systemic Risk Contagion Network")
    
    st.markdown("""
    **Network Analysis** - Model how shocks propagate through interconnected financial system.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("Network Setup")
        
        n_nodes = st.slider("Number of Institutions", 10, 50, 20)
        
        shock_nodes_input = st.text_input(
            "Initial Shock Nodes",
            value="0,1",
            help="Comma-separated node IDs"
        )
        
        max_steps = st.slider("Propagation Steps", 5, 20, 10)
        
        if st.button("Run Contagion Simulation", type="primary"):
            with st.spinner("Simulating contagion..."):
                # Create network
                network = ContagionNetwork(n_nodes)
                
                # Parse shock nodes
                shock_nodes = [int(x.strip()) for x in shock_nodes_input.split(',') if x.strip().isdigit()]
                shock_nodes = [n for n in shock_nodes if n < n_nodes]
                
                # Run simulation
                impact_history = network.simulate_shock(
                    shock_nodes,
                    shock_strength,
                    decay_rate,
                    max_steps
                )
                
                st.session_state.contagion_network = network
                st.session_state.impact_history = impact_history
    
    with col1:
        if 'contagion_network' in st.session_state and 'impact_history' in st.session_state:
            network = st.session_state.contagion_network
            impact_history = st.session_state.impact_history
            
            # Create network visualization  
            pos = network.get_spring_layout(seed=42)
            
            # Select time step
            time_step = st.slider("Time Step", 0, len(impact_history) - 1, len(impact_history) - 1)
            
            impact = impact_history[time_step]
            
            # Extract edges
            edge_x = []
            edge_y = []
            edge_weights = []
            
            for edge_info in network.get_edges():
                i, j, weight = edge_info
                x0, y0 = pos[i]
                x1, y1 = pos[j]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_weights.append(weight)
            
            # Extract nodes
            node_x = [pos[node][0] for node in network.get_nodes()]
            node_y = [pos[node][1] for node in network.get_nodes()]
            node_impact = [impact[node] for node in network.get_nodes()]
            
            # Create figure
            fig = go.Figure()
            
            # Add edges
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                mode='lines',
                line=dict(width=0.5, color='gray'),
                hoverinfo='none',
                showlegend=False
            ))
            
            # Add nodes
            fig.add_trace(go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                marker=dict(
                    size=[20 + i * 30 for i in node_impact],
                    color=node_impact,
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Impact"),
                    line=dict(width=2, color='white')
                ),
                text=[str(i) for i in range(len(node_x))],
                textposition="middle center",
                hovertemplate='Node: %{text}<br>Impact: %{marker.color:.3f}<extra></extra>',
                showlegend=False
            ))
            
            fig.update_layout(
                title=f"Contagion Network - Step {time_step}",
                showlegend=False,
                template='plotly_dark',
                height=600,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Impact statistics
            st.subheader("Contagion Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_impact = np.sum(impact)
            affected_nodes = np.sum(impact > 0.1)
            max_impact = np.max(impact)
            
            with col1:
                st.metric("Total System Impact", f"{total_impact:.2f}")
            with col2:
                st.metric("Affected Institutions", f"{affected_nodes}/{n_nodes}")
            with col3:
                st.metric("Max Impact", f"{max_impact:.3f}")
            with col4:
                infection_rate = affected_nodes / n_nodes * 100
                st.metric("Infection Rate", f"{infection_rate:.1f}%")
            
            # Centrality analysis
            st.subheader("Systemically Important Institutions")
            
            centrality = network.calculate_centrality()
            
            centrality_df = pd.DataFrame({
                'Node': list(centrality['degree'].keys()),
                'Degree Centrality': list(centrality['degree'].values()),
                'Betweenness': list(centrality['betweenness'].values()),
                'Eigenvector': list(centrality['eigenvector'].values()),
                'Final Impact': [impact[node] for node in centrality['degree'].keys()]
            }).sort_values('Final Impact', ascending=False).head(10)
            
            st.dataframe(
                centrality_df.style.format({
                    'Degree Centrality': '{:.3f}',
                    'Betweenness': '{:.3f}',
                    'Eigenvector': '{:.3f}',
                    'Final Impact': '{:.3f}'
                }).background_gradient(subset=['Final Impact'], cmap='Reds'),
                use_container_width=True,
                hide_index=True
            )
        
        else:
            st.info("Run contagion simulation to see network visualization")

# ============================================================================
# Tab 2: Correlation Shock
# ============================================================================
with tab2:
    st.header("Correlation Contagion & Shock Analysis")
    
    st.markdown("""
    **Correlation Breakdown** - Analyze how correlations spike during stress periods.
    """)
    
    # Calculate rolling correlation
    col1, col2 = st.columns(2)
    
    with col1:
        corr_window = st.slider("Correlation Window", 20, 120, 60)
    
    with col2:
        shock_threshold = st.slider(
            "Shock Threshold (% correlation increase)",
            5, 50, 20
        ) / 100
    
    if st.button("Analyze Correlation Shocks", type="primary"):
        with st.spinner("Calculating correlation dynamics..."):
            # Calculate rolling average correlation
            dates = returns_data.index[corr_window:]
            avg_corrs = []
            max_corrs = []
            
            for i in range(corr_window, len(returns_data)):
                window_data = returns_data.iloc[i-corr_window:i]
                corr_matrix = window_data.corr()
                
                # Get off-diagonal correlations
                mask = ~np.eye(len(corr_matrix), dtype=bool)
                corrs = corr_matrix.values[mask]
                
                avg_corrs.append(corrs.mean())
                max_corrs.append(corrs.max())
            
            avg_corr_series = pd.Series(avg_corrs, index=dates)
            max_corr_series = pd.Series(max_corrs, index=dates)
            
            # Detect shocks (sudden increases)
            corr_change = avg_corr_series.pct_change()
            shocks = corr_change > shock_threshold
            
            # Plot
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3],
                subplot_titles=("Average Correlation Over Time", "Correlation Shocks")
            )
            
            # Average correlation
            fig.add_trace(
                go.Scatter(
                    x=avg_corr_series.index,
                    y=avg_corr_series.values,
                    name='Avg Correlation',
                    line=dict(color='cyan', width=2)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=max_corr_series.index,
                    y=max_corr_series.values,
                    name='Max Correlation',
                    line=dict(color='orange', width=1.5, dash='dash')
                ),
                row=1, col=1
            )
            
            # Mark shock periods
            shock_dates = avg_corr_series.index[shocks]
            shock_values = avg_corr_series[shocks]
            
            fig.add_trace(
                go.Scatter(
                    x=shock_dates,
                    y=shock_values,
                    mode='markers',
                    name='Correlation Shock',
                    marker=dict(size=10, color='red', symbol='x')
                ),
                row=1, col=1
            )
            
            # Shock intensity
            fig.add_trace(
                go.Bar(
                    x=corr_change.index,
                    y=corr_change.values * 100,
                    name='Correlation Change %',
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
            
            fig.add_hline(
                y=shock_threshold * 100,
                line_dash="dash",
                line_color="red",
                row=2, col=1,
                annotation_text=f"Shock Threshold ({shock_threshold*100:.0f}%)"
            )
            
            fig.update_layout(
                template='plotly_dark',
                height=700,
                hovermode='x unified',
                showlegend=True
            )
            
            fig.update_yaxes(title_text="Correlation", row=1, col=1)
            fig.update_yaxes(title_text="Change (%)", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Shock summary
            st.subheader("Correlation Shock Events")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Number of Shocks", shocks.sum())
            with col2:
                st.metric("Current Correlation", f"{avg_corrs[-1]:.3f}")
            with col3:
                st.metric("Peak Correlation", f"{max(avg_corrs):.3f}")
            with col4:
                st.metric("Min Correlation", f"{min(avg_corrs):.3f}")

# ============================================================================
# Tab 3: Crash Cascade
# ============================================================================
with tab3:
    st.header("Market Reflexivity & Crash Cascade")
    
    st.markdown("""
    **Cascade Simulation** - Model how market sell-offs create feedback loops and cascading crashes.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_drop = st.slider("Initial Drop (%)", 1, 30, 10)
    
    with col2:
        feedback_strength = st.slider("Feedback Strength", 0.1, 0.9, 0.5, 0.1)
    
    with col3:
        cascade_steps = st.slider("Cascade Steps", 5, 30, 15)
    
    if st.button("Simulate Crash Cascade", type="primary"):
        with st.spinner("Simulating cascade..."):
            # Simulate cascade for each asset
            n_assets = len(price_data.columns)
            cascade_paths = np.zeros((cascade_steps, n_assets))
            
            # Set initial drop
            cascade_paths[0, :] = -initial_drop / 100
            
            # Simulate cascade with reflexivity
            for step in range(1, cascade_steps):
                # Previous drops create selling pressure
                prev_drop = cascade_paths[step - 1, :].mean()
                
                # Reflexive feedback
                additional_drop = prev_drop * feedback_strength
                
                # Add some randomness
                noise = np.random.randn(n_assets) * 0.01
                
                # Accumulate drops
                cascade_paths[step, :] = cascade_paths[step - 1, :] + additional_drop + noise
                
                # Apply floor (can't drop below -95%)
                cascade_paths[step, :] = np.maximum(cascade_paths[step, :], -0.95)
            
            # Convert to cumulative price impact
            price_paths = (1 + cascade_paths) * 100  # Starting from 100
            
            # Plot cascade
            fig = go.Figure()
            
            for i, ticker in enumerate(price_data.columns):
                fig.add_trace(go.Scatter(
                    x=list(range(cascade_steps)),
                    y=price_paths[:, i],
                    name=ticker,
                    mode='lines',
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="Crash Cascade Simulation",
                xaxis_title="Cascade Step",
                yaxis_title="Price (Initial = 100)",
                template='plotly_dark',
                height=600,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Cascade statistics
            st.subheader("Cascade Impact Metrics")
            
            final_drops = cascade_paths[-1, :] * 100
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg Final Drop", f"{final_drops.mean():.1f}%")
            with col2:
                st.metric("Worst Asset Drop", f"{final_drops.min():.1f}%")
            with col3:
                st.metric("Best Asset Drop", f"{final_drops.max():.1f}%")
            with col4:
                amplification = abs(final_drops.mean() / initial_drop)
                st.metric("Amplification Factor", f"{amplification:.2f}x")
            
            # Individual asset drops
            drop_df = pd.DataFrame({
                'Asset': price_data.columns,
                'Final Drop (%)': final_drops,
                'Final Price': price_paths[-1, :]
            }).sort_values('Final Drop (%)')
            
            st.dataframe(
                drop_df.style.format({
                    'Final Drop (%)': '{:.2f}%',
                    'Final Price': '{:.2f}'
                }).background_gradient(subset=['Final Drop (%)'], cmap='Reds_r'),
                use_container_width=True,
                hide_index=True
            )

# ============================================================================
# Tab 4: Portfolio Fragility
# ============================================================================
with tab4:
    st.header("Portfolio Fragility & Hidden Leverage")
    
    st.markdown("""
    **Fragility Detection** - Identify hidden leverage and concentration risks.
    """)
    
    lookback = st.slider("Analysis Window", 30, 120, 60)
    
    if st.button("Analyze Portfolio Fragility", type="primary"):
        with st.spinner("Calculating fragility metrics..."):
            fragility = calculate_portfolio_fragility(returns_data, lookback)
            
            # Plot fragility metrics
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.08,
                subplot_titles=(
                    "Average Correlation (Concentration Risk)",
                    "Volatility Concentration",
                    "Hidden Leverage Spikes"
                ),
                row_heights=[0.35, 0.35, 0.3]
            )
            
            # Average correlation
            fig.add_trace(
                go.Scatter(
                    x=fragility['avg_correlation'].index,
                    y=fragility['avg_correlation'].values,
                    name='Avg Correlation',
                    line=dict(color='orange', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255, 165, 0, 0.2)'
                ),
                row=1, col=1
            )
            
            # Volatility concentration
            fig.add_trace(
                go.Scatter(
                    x=fragility['vol_concentration'].index,
                    y=fragility['vol_concentration'].values,
                    name='Vol Concentration',
                    line=dict(color='cyan', width=2)
                ),
                row=2, col=1
            )
            
            # Leverage spikes
            spike_dates = fragility['leverage_spikes'].index[fragility['leverage_spikes'] == 1]
            spike_values = [1] * len(spike_dates)
            
            fig.add_trace(
                go.Scatter(
                    x=spike_dates,
                    y=spike_values,
                    mode='markers',
                    name='Leverage Spike',
                    marker=dict(size=10, color='red', symbol='diamond')
                ),
                row=3, col=1
            )
            
            fig.update_layout(
                template='plotly_dark',
                height=800,
                showlegend=True,
                hovermode='x unified'
            )
            
            fig.update_yaxes(title_text="Correlation", row=1, col=1)
            fig.update_yaxes(title_text="Ratio", row=2, col=1)
            fig.update_yaxes(title_text="Spike", row=3, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Fragility score
            st.subheader("Fragility Score")
            
            # Calculate composite score
            current_corr = fragility['avg_correlation'].iloc[-1]
            current_vol_conc = fragility['vol_concentration'].iloc[-1]
            recent_spikes = fragility['leverage_spikes'].tail(20).sum()
            
            # Score components (0-100, higher = more fragile)
            corr_score = min(100, current_corr * 150)  # High correlation = fragile
            vol_conc_score = min(100, (current_vol_conc - 1) * 100)  # Concentration = fragile
            spike_score = min(100, recent_spikes * 10)  # Recent spikes = fragile
            
            overall_score = (corr_score * 0.4 + vol_conc_score * 0.4 + spike_score * 0.2)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Overall Fragility", f"{overall_score:.0f}/100")
            
            with col2:
                st.metric("Correlation Score", f"{corr_score:.0f}/100")
            
            with col3:
                st.metric("Concentration Score", f"{vol_conc_score:.0f}/100")
            
            with col4:
                st.metric("Leverage Spike Score", f"{spike_score:.0f}/100")
            
            # Risk assessment
            if overall_score >= 75:
                st.error(" **Critical Fragility** - Portfolio extremely vulnerable to shocks")
            elif overall_score >= 50:
                st.warning(" **High Fragility** - Significant concentration and leverage risks")
            elif overall_score >= 25:
                st.info(" **Moderate Fragility** - Some vulnerability present, monitor closely")
            else:
                st.success(" **Low Fragility** - Portfolio relatively resilient to shocks")

# ============================================================================
# Tab 5: Correlation Matrix Evolution
# ============================================================================
with tab5:
    st.header("Correlation Matrix Evolution")
    
    st.markdown("""
    **Dynamic Correlation** - Watch how correlation structure morphs over time.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        evolution_window = st.slider("Window Size", 30, 120, 60, key="evolution_window")
    
    with col2:
        n_snapshots = st.slider("Number of Snapshots", 3, 12, 6)
    
    if st.button("Generate Evolution", type="primary"):
        with st.spinner("Computing correlation evolution..."):
            # Calculate snapshots at regular intervals
            total_points = len(returns_data)
            snapshot_indices = np.linspace(
                evolution_window,
                total_points - 1,  # Fix: subtract 1 to stay within bounds
                n_snapshots,
                dtype=int
            )
            
            # Create subplots for matrices
            cols_per_row = min(3, n_snapshots)
            n_rows = int(np.ceil(n_snapshots / cols_per_row))
            
            fig = make_subplots(
                rows=n_rows,
                cols=cols_per_row,
                subplot_titles=[returns_data.index[min(idx, len(returns_data.index) - 1)].strftime('%Y-%m-%d') 
                               for idx in snapshot_indices],
                specs=[[{'type': 'heatmap'} for _ in range(cols_per_row)] 
                      for _ in range(n_rows)]
            )
            
            for idx, snapshot_idx in enumerate(snapshot_indices):
                row = idx // cols_per_row + 1
                col = idx % cols_per_row + 1
                
                # Calculate correlation for this snapshot
                window_data = returns_data.iloc[snapshot_idx - evolution_window:snapshot_idx]
                corr_matrix = window_data.corr()
                
                fig.add_trace(
                    go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns,
                        y=corr_matrix.index,
                        colorscale='RdBu',
                        zmid=0,
                        zmin=-1,
                        zmax=1,
                        showscale=(idx == 0),
                        colorbar=dict(title="Correlation", x=1.1) if idx == 0 else None
                    ),
                    row=row,
                    col=col
                )
            
            fig.update_layout(
                template='plotly_dark',
                height=300 * n_rows,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Evolution metrics
            st.subheader("Evolution Statistics")
            
            # Calculate average correlation for each snapshot
            avg_corrs = []
            for snapshot_idx in snapshot_indices:
                window_data = returns_data.iloc[snapshot_idx - evolution_window:snapshot_idx]
                corr_matrix = window_data.corr()
                mask = ~np.eye(len(corr_matrix), dtype=bool)
                avg_corrs.append(corr_matrix.values[mask].mean())
            
            # Plot evolution
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=[returns_data.index[idx] for idx in snapshot_indices],
                y=avg_corrs,
                mode='lines+markers',
                name='Avg Correlation',
                line=dict(color='cyan', width=3),
                marker=dict(size=10)
            ))
            
            fig2.update_layout(
                title="Average Correlation Evolution",
                xaxis_title="Date",
                yaxis_title="Average Correlation",
                template='plotly_dark',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Initial Correlation", f"{avg_corrs[0]:.3f}")
            with col2:
                st.metric("Final Correlation", f"{avg_corrs[-1]:.3f}")
            with col3:
                change = avg_corrs[-1] - avg_corrs[0]
                st.metric("Total Change", f"{change:+.3f}")

# ============================================================================
# Tab 6: 3D Market Contagion Network
# ============================================================================
with tab6:
    st.header("3D Market Contagion Network")
    
    st.markdown("""
    **3D Correlation-Based Contagion** - Visualize how market shocks propagate through 
    actual correlation networks in three-dimensional space. Assets are connected by correlation strength.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("Contagion Parameters")
        
        shock_ticker = st.selectbox(
            "Shock Asset",
            options=tickers,
            index=0,
            help="Asset that receives the initial shock"
        )
        
        shock_magnitude = st.slider(
            "Shock Magnitude",
            min_value=0.01,
            max_value=1.0,
            value=0.3,
            step=0.01,
            help="Initial stress level (0-1)"
        )
        
        decay_rate = st.slider(
            "Decay Speed",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.01,
            help="How fast stress decays over time"
        )
        
        corr_threshold = st.slider(
            "Correlation Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="Minimum correlation to create network edge"
        )
        
        time_steps = st.slider(
            "Propagation Steps",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="Number of contagion propagation steps"
        )
        
        if st.button(" Simulate 3D Contagion", type="primary"):
            with st.spinner("Building 3D correlation network..."):
                try:
                    # Calculate returns and correlation matrix
                    corr_matrix = returns_data.corr()
                    
                    st.info("""
                     **NetworkX Dependency Required**
                    
                    The 3D network visualization requires NetworkX which is not available in the current environment.
                    To use this feature, install NetworkX:
                    ```bash
                    pip install networkx
                    ```
                    
                    **Alternative**: View the correlation matrix heatmap below.
                    """)
                    
                    # Show correlation heatmap instead
                    st.subheader("Correlation Matrix Heatmap")
                    
                    fig_heatmap = go.Figure(data=go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns,
                        y=corr_matrix.index,
                        colorscale='RdBu',
                        zmid=0,
                        colorbar=dict(title="Correlation")
                    ))
                    
                    fig_heatmap.update_layout(
                        title="Asset Correlation Matrix",
                        template='plotly_dark',
                        height=600,
                        width=600
                    )
                    
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                    # Simple contagion simulation based on correlation matrix
                    stress = {ticker: 0.0 for ticker in tickers}
                    stress[shock_ticker] = shock_magnitude
                    
                    stress_history = [stress.copy()]
                    
                    for t in range(time_steps):
                        new_stress = stress.copy()
                        
                        # Propagate stress based on correlations
                        for i, ticker_i in enumerate(tickers):
                            for j, ticker_j in enumerate(tickers):
                                if i != j:
                                    corr_val = abs(corr_matrix.iloc[i, j])
                                    if corr_val >= corr_threshold:
                                        # Propagate stress based on correlation strength
                                        new_stress[ticker_j] += stress[ticker_i] * corr_val * (1 - decay_rate)
                        
                        # Apply decay
                        for ticker in new_stress:
                            new_stress[ticker] *= (1 - decay_rate)
                            # Cap stress at 1.0
                            new_stress[ticker] = min(new_stress[ticker], 1.0)
                        
                        stress = new_stress
                        stress_history.append(stress.copy())
                    
                    # Store results
                    st.session_state.contagion_3d_stress = stress_history
                    st.session_state.contagion_3d_corr = corr_matrix
                    st.session_state.contagion_tickers = tickers
                    
                    st.success(f"Simulation completed! {len(stress_history)} time steps generated.")
                    
                except Exception as e:
                    st.error(f"Error in 3D contagion simulation: {str(e)}")
    
    with col1:
        if 'contagion_3d_stress' in st.session_state:
            stress_history = st.session_state.contagion_3d_stress
            corr_matrix = st.session_state.contagion_3d_corr
            tickers = st.session_state.contagion_tickers
            
            # Time step selector
            selected_step = st.slider(
                "View Time Step",
                min_value=0,
                max_value=len(stress_history) - 1,
                value=len(stress_history) - 1,
                help="Select propagation step to visualize"
            )
            
            current_stress = stress_history[selected_step]
            
            # Create stress visualization
            fig_stress = go.Figure()
            
            x_vals = list(current_stress.keys())
            y_vals = list(current_stress.values())
            
            # Color code by stress level
            colors = ['red' if stress > 0.5 else 'orange' if stress > 0.2 else 'green' for stress in y_vals]
            
            fig_stress.add_trace(go.Bar(
                x=x_vals,
                y=y_vals,
                marker_color=colors,
                text=[f'{stress:.3f}' for stress in y_vals],
                textposition='auto'
            ))
            
            fig_stress.update_layout(
                title=f'System Stress at Step {selected_step}',
                template='plotly_dark',
                height=400,
                xaxis_title='Assets',
                yaxis_title='Stress Level',
                showlegend=False
            )
            
            st.plotly_chart(fig_stress, use_container_width=True)
            
            # Contagion metrics  
            st.subheader("Contagion Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_stress = sum(current_stress.values())
            affected_assets = sum(1 for s in current_stress.values() if s > 0.01)
            max_stress = max(current_stress.values())
            avg_stress = total_stress / len(current_stress)
            
            with col1:
                st.metric("Total System Stress", f"{total_stress:.3f}")
            
            with col2:
                st.metric("Affected Assets", f"{affected_assets}/{len(tickers)}")
            
            with col3:
                st.metric("Max Stress", f"{max_stress:.3f}")
            
            with col4:
                st.metric("Average Stress", f"{avg_stress:.3f}")
            
            # Network statistics
            st.subheader("Network Structure")
            
            col1, col2, col3 = st.columns(3)
            
            # Calculate network stats from correlation matrix
            num_nodes = len(tickers)
            corr_threshold = 0.3  # Use same threshold as simulation
            
            # Count edges (correlations above threshold)
            strong_corrs = 0
            for i in range(len(tickers)):
                for j in range(i + 1, len(tickers)):
                    if abs(corr_matrix.iloc[i, j]) >= corr_threshold:
                        strong_corrs += 1
            
            max_possible_edges = num_nodes * (num_nodes - 1) // 2
            density = strong_corrs / max_possible_edges if max_possible_edges > 0 else 0
            
            with col1:
                st.metric("Number of Nodes", f"{num_nodes}")
            
            with col2:
                st.metric("Strong Correlations", f"{strong_corrs}")
            
            with col3:
                st.metric("Network Density", f"{density:.3f}")
            
            # Most correlated assets
            st.markdown("**Most Systemically Important Assets:**")
            
            # Calculate centrality as sum of strong correlations
            centrality = {}
            for i, ticker in enumerate(tickers):
                strong_connections = sum(1 for j in range(len(tickers)) 
                                       if i != j and abs(corr_matrix.iloc[i, j]) >= corr_threshold)
                centrality[ticker] = strong_connections / (len(tickers) - 1) if len(tickers) > 1 else 0
            
            central_df = pd.DataFrame({
                'Asset': list(centrality.keys()),
                'Centrality': list(centrality.values()),
                'Final Stress': [current_stress[ticker] for ticker in centrality.keys()]
            }).sort_values('Centrality', ascending=False).head(10)
            
            st.dataframe(central_df, use_container_width=True, hide_index=True)
            
        else:
            st.info("▶ Run simulation to visualize 3D market contagion network")

# Footer
st.markdown("---")
st.markdown(
    "**Systemic Risk & Contagion Analysis** | Network Models & Cascade Simulations | "
    " For Risk Assessment Purposes Only"
)
