"""
Trading Signals & Strategy Lab
Complete trading signal generation and strategy backtesting platform.
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

# Configure page
st.set_page_config(
    page_title="Trading Signals & Strategy Lab",
    page_icon="📡",
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
# Strategy Classes
# ============================================================================

class MomentumStrategy:
    """Moving Average Crossover Strategy"""
    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window
        self.name = f"Momentum ({short_window}/{long_window})"
    
    def generate_signals(self, data):
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        signals['short_ma'] = data['Close'].rolling(window=self.short_window).mean()
        signals['long_ma'] = data['Close'].rolling(window=self.long_window).mean()
        
        # Signal: 1 = Long, 0 = No position, -1 = Short
        signals['signal'] = 0
        signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
        signals.loc[signals['short_ma'] < signals['long_ma'], 'signal'] = -1
        
        # Position changes (for marking trades)
        signals['position_change'] = signals['signal'].diff()
        
        return signals

class MeanReversionStrategy:
    """RSI-based Mean Reversion Strategy"""
    def __init__(self, rsi_period=14, oversold=30, overbought=70):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"Mean Reversion (RSI {rsi_period})"
    
    def compute_rsi(self, prices):
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.rsi_period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, data):
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        signals['rsi'] = self.compute_rsi(data['Close'])
        
        # Signal: 1 = Long (oversold), -1 = Short (overbought), 0 = neutral
        signals['signal'] = 0
        signals.loc[signals['rsi'] < self.oversold, 'signal'] = 1
        signals.loc[signals['rsi'] > self.overbought, 'signal'] = -1
        
        signals['position_change'] = signals['signal'].diff()
        
        return signals

class BollingerBandsStrategy:
    """Bollinger Bands Breakout Strategy"""
    def __init__(self, window=20, num_std=2):
        self.window = window
        self.num_std = num_std
        self.name = f"Bollinger Bands ({window})"
    
    def generate_signals(self, data):
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        
        # Calculate Bollinger Bands
        signals['ma'] = data['Close'].rolling(window=self.window).mean()
        signals['std'] = data['Close'].rolling(window=self.window).std()
        signals['upper_band'] = signals['ma'] + (signals['std'] * self.num_std)
        signals['lower_band'] = signals['ma'] - (signals['std'] * self.num_std)
        
        # Signal: Buy when price touches lower band, sell when touches upper
        signals['signal'] = 0
        signals.loc[signals['price'] < signals['lower_band'], 'signal'] = 1
        signals.loc[signals['price'] > signals['upper_band'], 'signal'] = -1
        
        signals['position_change'] = signals['signal'].diff()
        
        return signals

class RandomStrategy:
    """Random Trading Strategy (Baseline for Comparison)"""
    def __init__(self, seed=42):
        self.seed = seed
        self.name = "Random (Baseline)"
    
    def generate_signals(self, data):
        np.random.seed(self.seed)
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        
        # Random signals: 1, 0, or -1
        signals['signal'] = np.random.choice([-1, 0, 1], size=len(data))
        signals['position_change'] = signals['signal'].diff()
        
        return signals

class Backtester:
    """Backtesting engine with performance metrics"""
    def __init__(self, data, signals, initial_capital=100000, commission=0.001):
        self.data = data
        self.signals = signals
        self.initial_capital = initial_capital
        self.commission = commission
        self.results = None
    
    def run(self):
        # Calculate returns
        returns = self.data['Close'].pct_change().fillna(0)
        
        # Strategy returns (with commission)
        strategy_returns = returns * self.signals['signal'].shift(1)
        
        # Apply commission on position changes
        position_changes = self.signals['signal'].diff().abs()
        commission_cost = position_changes * self.commission
        strategy_returns = strategy_returns - commission_cost
        
        # Calculate equity curve
        equity = (1 + strategy_returns).cumprod() * self.initial_capital
        
        # Buy & hold benchmark
        buy_hold_equity = (1 + returns).cumprod() * self.initial_capital
        
        self.results = pd.DataFrame({
            'equity': equity,
            'returns': strategy_returns,
            'buy_hold': buy_hold_equity,
            'position': self.signals['signal']
        }, index=self.data.index)
        
        return self.results
    
    def get_metrics(self):
        if self.results is None:
            self.run()
        
        total_return = (self.results['equity'].iloc[-1] / self.initial_capital - 1) * 100
        buy_hold_return = (self.results['buy_hold'].iloc[-1] / self.initial_capital - 1) * 100
        
        annual_return = ((self.results['equity'].iloc[-1] / self.initial_capital) ** (252 / len(self.results)) - 1) * 100
        
        volatility = self.results['returns'].std() * np.sqrt(252) * 100
        sharpe = (self.results['returns'].mean() / (self.results['returns'].std() + 1e-10)) * np.sqrt(252)
        
        # Max drawdown
        cum_max = self.results['equity'].cummax()
        drawdown = (self.results['equity'] - cum_max) / cum_max
        max_dd = drawdown.min() * 100
        
        # Win rate
        winning_days = (self.results['returns'] > 0).sum()
        total_trading_days = (self.results['returns'] != 0).sum()
        win_rate = (winning_days / total_trading_days * 100) if total_trading_days > 0 else 0
        
        # Number of trades
        num_trades = self.signals['position_change'].abs().sum() / 2  # Divide by 2 (entry + exit)
        
        return {
            'Total Return': total_return,
            'Annual Return': annual_return,
            'Buy & Hold Return': buy_hold_return,
            'Volatility': volatility,
            'Sharpe Ratio': sharpe,
            'Max Drawdown': max_dd,
            'Win Rate': win_rate,
            'Number of Trades': num_trades
        }

# ============================================================================
# Page Header
# ============================================================================
st.title("📡 Trading Signals & Strategy Lab")
st.markdown("""
Generate trading signals and backtest strategies with real market data
""")

# ============================================================================
# Sidebar Configuration
# ============================================================================
st.sidebar.header("⚙️ Configuration")

# Stock selection
st.sidebar.subheader("📊 Stock Selection")
ticker = st.sidebar.selectbox(
    "Select Asset",
    options=COMMON_TICKERS,
    index=COMMON_TICKERS.index("AAPL") if "AAPL" in COMMON_TICKERS else 0,
    help="Select a ticker to analyze"
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

# Date range
st.sidebar.subheader("📅 Date Range")
date_preset = st.sidebar.selectbox(
    "Preset Range",
    ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "5 Years", "Custom"]
)

if date_preset == "Custom":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start", value=datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End", value=datetime.now())
else:
    days_map = {
        "1 Month": 30,
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365,
        "2 Years": 730,
        "5 Years": 1825
    }
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_map[date_preset])

# Strategy parameters
st.sidebar.subheader("📈 Strategy Parameters")

# Momentum parameters
with st.sidebar.expander("Momentum Strategy", expanded=True):
    momentum_short = st.slider("Short MA", 5, 50, 20, help="Short-term moving average period")
    momentum_long = st.slider("Long MA", 20, 200, 50, help="Long-term moving average period")

# Mean reversion parameters
with st.sidebar.expander("Mean Reversion Strategy"):
    rsi_period = st.slider("RSI Period", 5, 30, 14)
    rsi_oversold = st.slider("Oversold Level", 10, 40, 30)
    rsi_overbought = st.slider("Overbought Level", 60, 90, 70)

# Bollinger Bands parameters
with st.sidebar.expander("Bollinger Bands Strategy"):
    bb_window = st.slider("BB Window", 10, 50, 20)
    bb_std = st.slider("Std Deviations", 1.0, 3.0, 2.0, 0.5)

# Backtesting parameters
st.sidebar.subheader("💰 Backtesting Setup")
initial_capital = st.sidebar.number_input(
    "Initial Capital ($)",
    min_value=1000,
    max_value=10000000,
    value=100000,
    step=10000
)

commission = st.sidebar.slider(
    "Commission (%)",
    min_value=0.0,
    max_value=1.0,
    value=0.1,
    step=0.01,
    help="Commission per trade as percentage"
) / 100

# ============================================================================
# Fetch Data
# ============================================================================
@st.cache_data(ttl=300)
def load_stock_data(ticker, start, end):
    provider = MarketDataProvider()
    data = provider.get_stock_data(
        ticker,
        start_date=start,
        end_date=end
    )
    return data

try:
    with st.spinner(f"Loading {ticker} data..."):
        stock_data = load_stock_data(ticker, start_date, end_date)
    
    if stock_data.empty:
        st.error(f"No data available for {ticker}")
        st.stop()
    
    # Display current price
    current_price = stock_data['Close'].iloc[-1]
    prev_price = stock_data['Close'].iloc[-2]
    price_change = ((current_price / prev_price) - 1) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ticker", ticker)
    with col2:
        st.metric("Current Price", f"${current_price:.2f}", f"{price_change:+.2f}%")
    with col3:
        st.metric("Data Points", len(stock_data))
    with col4:
        st.metric("Date Range", f"{(end_date - start_date).days} days")
    
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    logger.error(f"Data loading error: {str(e)}")
    st.stop()

# ============================================================================
# Tabs
# ============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Signal Generator",
    "⚔️ Strategy Battle",
    "📈 Signal Analysis",
    "🎯 Performance Metrics",
    "🏆 Battle Simulator",
    "💹 Buy vs Sell Signals"
])

# ============================================================================
# Tab 1: Signal Generator (MA Crossover)
# ============================================================================
with tab1:
    st.header("Buy/Sell Signal Generator")
    
    st.markdown("""
    **Moving Average Crossover Signals** - Classic trend-following strategy.
    - **Buy Signal** (🟢): Short MA crosses above Long MA
    - **Sell Signal** (🔴): Short MA crosses below Long MA
    """)
    
    # Generate signals
    strategy = MomentumStrategy(momentum_short, momentum_long)
    signals = strategy.generate_signals(stock_data)
    
    # Create comprehensive chart
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(
            f'{ticker} Price & Signals',
            'Position',
            'Moving Averages Distance'
        )
    )
    
    # Price and MAs
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=stock_data['Close'],
            name='Price',
            line=dict(color='white', width=2)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=signals.index,
            y=signals['short_ma'],
            name=f'{momentum_short}D MA',
            line=dict(color='orange', width=1.5)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=signals.index,
            y=signals['long_ma'],
            name=f'{momentum_long}D MA',
            line=dict(color='purple', width=1.5)
        ),
        row=1, col=1
    )
    
    # Buy signals
    buy_signals = signals[signals['position_change'] > 0]
    if not buy_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=buy_signals.index,
                y=buy_signals['price'],
                mode='markers',
                name='Buy Signal',
                marker=dict(symbol='triangle-up', size=12, color='lime')
            ),
            row=1, col=1
        )
    
    # Sell signals
    sell_signals = signals[signals['position_change'] < 0]
    if not sell_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=sell_signals.index,
                y=sell_signals['price'],
                mode='markers',
                name='Sell Signal',
                marker=dict(symbol='triangle-down', size=12, color='red')
            ),
            row=1, col=1
        )
    
    # Position
    fig.add_trace(
        go.Scatter(
            x=signals.index,
            y=signals['signal'],
            name='Position',
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.2)',
            line=dict(color='lime', width=1)
        ),
        row=2, col=1
    )
    
    # MA distance
    ma_distance = ((signals['short_ma'] - signals['long_ma']) / signals['long_ma'] * 100).fillna(0)
    fig.add_trace(
        go.Scatter(
            x=signals.index,
            y=ma_distance,
            name='MA Distance %',
            fill='tozeroy',
            line=dict(color='cyan', width=1)
        ),
        row=3, col=1
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=3, col=1)
    
    fig.update_layout(
        template='plotly_dark',
        height=800,
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Position", row=2, col=1)
    fig.update_yaxes(title_text="Distance (%)", row=3, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Signal statistics
    st.subheader("Signal Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    num_buy = len(buy_signals)
    num_sell = len(sell_signals)
    total_signals = num_buy + num_sell
    
    with col1:
        st.metric("Buy Signals", num_buy)
    with col2:
        st.metric("Sell Signals", num_sell)
    with col3:
        st.metric("Total Signals", total_signals)
    with col4:
        avg_days_between = len(signals) / (total_signals + 1)
        st.metric("Avg Days Between Signals", f"{avg_days_between:.1f}")

# ============================================================================
# Tab 2: Strategy Battle
# ============================================================================
with tab2:
    st.header("Strategy Battle Arena")
    
    st.markdown("""
    **Compare Multiple Strategies** - See which strategy performs best on historical data.
    """)
    
    # Create strategies
    strategies = [
        MomentumStrategy(momentum_short, momentum_long),
        MeanReversionStrategy(rsi_period, rsi_oversold, rsi_overbought),
        BollingerBandsStrategy(bb_window, bb_std)
    ]
    
    if st.button("Run Battle", type="primary"):
        with st.spinner("Backtesting all strategies..."):
            results = []
            equity_curves = {}
            
            for strategy in strategies:
                # Generate signals
                signals = strategy.generate_signals(stock_data)
                
                # Backtest
                backtester = Backtester(stock_data, signals, initial_capital, commission)
                backtest_results = backtester.run()
                metrics = backtester.get_metrics()
                
                # Store results
                results.append({
                    'Strategy': strategy.name,
                    **metrics
                })
                
                equity_curves[strategy.name] = backtest_results['equity']
            
            # Create results DataFrame
            results_df = pd.DataFrame(results)
            
            # Plot equity curves
            fig = go.Figure()
            
            colors = ['#00ff00', '#ff00ff', '#00ffff', '#ffff00']
            
            for idx, (strategy_name, equity) in enumerate(equity_curves.items()):
                fig.add_trace(go.Scatter(
                    x=equity.index,
                    y=equity,
                    name=strategy_name,
                    line=dict(width=2, color=colors[idx % len(colors)])
                ))
            
            # Add buy & hold
            buy_hold = (1 + stock_data['Close'].pct_change()).cumprod() * initial_capital
            fig.add_trace(go.Scatter(
                x=buy_hold.index,
                y=buy_hold,
                name='Buy & Hold',
                line=dict(width=2, color='white', dash='dash')
            ))
            
            fig.update_layout(
                title="Strategy Equity Curves",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                template='plotly_dark',
                height=500,
                hovermode='x unified',
                yaxis=dict(tickformat='$,.0f')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance comparison table
            st.subheader("Performance Comparison")
            
            # Style the dataframe
            def style_metric(val, metric_name):
                if metric_name in ['Total Return', 'Annual Return', 'Sharpe Ratio']:
                    color = 'lightgreen' if val > 0 else 'lightcoral'
                elif metric_name == 'Max Drawdown':
                    color = 'lightgreen' if val > -10 else 'lightcoral'
                else:
                    return ''
                return f'background-color: {color}'
            
            styled_df = results_df.style.format({
                'Total Return': '{:.2f}%',
                'Annual Return': '{:.2f}%',
                'Buy & Hold Return': '{:.2f}%',
                'Volatility': '{:.2f}%',
                'Sharpe Ratio': '{:.2f}',
                'Max Drawdown': '{:.2f}%',
                'Win Rate': '{:.2f}%',
                'Number of Trades': '{:.0f}'
            })
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Winner announcement
            best_strategy_idx = results_df['Sharpe Ratio'].idxmax()
            best_strategy = results_df.loc[best_strategy_idx]
            
            st.success(f"""
            🏆 **Winner**: {best_strategy['Strategy']}
            - Total Return: {best_strategy['Total Return']:.2f}%
            - Sharpe Ratio: {best_strategy['Sharpe Ratio']:.2f}
            - Max Drawdown: {best_strategy['Max Drawdown']:.2f}%
            """)

# ============================================================================
# Tab 3: Signal Analysis
# ============================================================================
with tab3:
    st.header("Signal Analysis & Patterns")
    
    st.markdown("**Deep Dive into Trading Signals** - Analyze signal characteristics and patterns.")
    
    # Use momentum strategy as primary
    strategy = MomentumStrategy(momentum_short, momentum_long)
    signals = strategy.generate_signals(stock_data)
    
    # Calculate signal metrics
    buy_points = signals[signals['position_change'] > 0].copy()
    sell_points = signals[signals['position_change'] < 0].copy()
    
    if not buy_points.empty and not sell_points.empty:
        # Returns after buy signals
        buy_returns = []
        for idx in buy_points.index:
            future_idx = stock_data.index.get_loc(idx) + 20  # 20-day forward return
            if future_idx < len(stock_data):
                future_price = stock_data['Close'].iloc[future_idx]
                current_price = stock_data.loc[idx, 'Close']
                ret = (future_price / current_price - 1) * 100
                buy_returns.append(ret)
        
        # Distribution of returns after buy signals
        if buy_returns:
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=buy_returns,
                nbinsx=30,
                name='20-Day Returns After Buy',
                marker_color='lightgreen',
                opacity=0.7
            ))
            
            fig.add_vline(
                x=np.mean(buy_returns),
                line_dash="dash",
                line_color="white",
                annotation_text=f"Mean: {np.mean(buy_returns):.2f}%"
            )
            
            fig.update_layout(
                title="Distribution of 20-Day Returns After Buy Signals",
                xaxis_title="Return (%)",
                yaxis_title="Frequency",
                template='plotly_dark',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Signal quality metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_return = np.mean(buy_returns)
                st.metric("Avg 20-Day Return After Buy", f"{avg_return:.2f}%")
            
            with col2:
                positive_rate = (np.array(buy_returns) > 0).mean() * 100
                st.metric("Success Rate", f"{positive_rate:.1f}%")
            
            with col3:
                max_return = np.max(buy_returns)
                st.metric("Best 20-Day Return", f"{max_return:.2f}%")
        
        # Signal timing analysis
        st.subheader("Signal Timing Distribution")
        
        # Day of week analysis
        buy_points['day_of_week'] = buy_points.index.dayofweek
        day_counts = buy_points['day_of_week'].value_counts().sort_index()
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=day_names,
            y=[day_counts.get(i, 0) for i in range(5)],
            marker_color='skyblue'
        ))
        
        fig.update_layout(
            title="Buy Signals by Day of Week",
            xaxis_title="Day",
            yaxis_title="Number of Signals",
            template='plotly_dark',
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough signals in the selected period for detailed analysis.")

# ============================================================================
# Tab 4: Performance Metrics
# ============================================================================
with tab4:
    st.header("Detailed Performance Metrics")
    
    st.markdown("**Comprehensive Backtesting Results** - Full performance breakdown for each strategy.")
    
    # Select strategy
    strategy_choice = st.selectbox(
        "Select Strategy",
        ["Momentum", "Mean Reversion", "Bollinger Bands"]
    )
    
    if strategy_choice == "Momentum":
        strategy = MomentumStrategy(momentum_short, momentum_long)
    elif strategy_choice == "Mean Reversion":
        strategy = MeanReversionStrategy(rsi_period, rsi_oversold, rsi_overbought)
    else:
        strategy = BollingerBandsStrategy(bb_window, bb_std)
    
    if st.button("Calculate Metrics", type="primary"):
        with st.spinner("Running backtest..."):
            # Generate signals and backtest
            signals = strategy.generate_signals(stock_data)
            backtester = Backtester(stock_data, signals, initial_capital, commission)
            results = backtester.run()
            metrics = backtester.get_metrics()
            
            # Display metrics
            st.subheader("Performance Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Return",
                    f"{metrics['Total Return']:.2f}%",
                    delta=f"vs B&H: {metrics['Total Return'] - metrics['Buy & Hold Return']:.2f}%"
                )
            
            with col2:
                st.metric(
                    "Sharpe Ratio",
                    f"{metrics['Sharpe Ratio']:.2f}"
                )
            
            with col3:
                st.metric(
                    "Max Drawdown",
                    f"{metrics['Max Drawdown']:.2f}%"
                )
            
            with col4:
                st.metric(
                    "Win Rate",
                    f"{metrics['Win Rate']:.1f}%"
                )
            
            # Equity curve with drawdown
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3],
                subplot_titles=('Equity Curve', 'Drawdown')
            )
            
            # Equity
            fig.add_trace(
                go.Scatter(
                    x=results.index,
                    y=results['equity'],
                    name='Strategy',
                    line=dict(color='lime', width=2)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=results.index,
                    y=results['buy_hold'],
                    name='Buy & Hold',
                    line=dict(color='white', width=2, dash='dash')
                ),
                row=1, col=1
            )
            
            # Drawdown
            cum_max = results['equity'].cummax()
            drawdown = (results['equity'] - cum_max) / cum_max * 100
            
            fig.add_trace(
                go.Scatter(
                    x=results.index,
                    y=drawdown,
                    name='Drawdown',
                    fill='tozeroy',
                    fillcolor='rgba(255, 0, 0, 0.3)',
                    line=dict(color='red', width=1)
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                template='plotly_dark',
                height=600,
                hovermode='x unified'
            )
            
            fig.update_yaxes(title_text="Value ($)", row=1, col=1, tickformat='$,.0f')
            fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # All metrics table
            st.subheader("All Metrics")
            
            metrics_data = []
            for key, value in metrics.items():
                if 'Return' in key or 'Drawdown' in key or 'Rate' in key or 'Volatility' in key:
                    formatted_value = f"{value:.2f}%"
                elif 'Ratio' in key:
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = f"{value:.0f}"
                
                metrics_data.append({
                    'Metric': key,
                    'Value': formatted_value
                })
            
            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # Trade log
            st.subheader("Trade Log (Last 10 Trades)")
            
            trade_changes = signals[signals['position_change'] != 0].copy()
            
            if not trade_changes.empty:
                trade_log = []
                for idx in trade_changes.index[-10:]:
                    trade_log.append({
                        'Date': idx.strftime('%Y-%m-%d'),
                        'Action': 'BUY' if signals.loc[idx, 'position_change'] > 0 else 'SELL',
                        'Price': f"${signals.loc[idx, 'price']:.2f}",
                        'Position': signals.loc[idx, 'signal']
                    })
                
                trade_df = pd.DataFrame(trade_log)
                st.dataframe(trade_df, use_container_width=True, hide_index=True)
            else:
                st.info("No trades in selected period")

# ============================================================================
# Tab 5: Algorithmic Trading Battle Simulator
# ============================================================================
with tab5:
    st.header("⚔️ Algorithmic Trading Battle Simulator")
    
    st.markdown("""
    **Strategy Showdown** - Watch three different trading strategies compete head-to-head on the same market data.
    Compare Momentum, Mean Reversion, and Random baseline strategies to see which performs best.
    """)
    
    # Battle configuration
    col1, col2 = st.columns(2)
    
    with col1:
        battle_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000,
            max_value=10000000,
            value=100000,
            step=10000
        )
    
    with col2:
        battle_commission = st.slider(
            "Commission Rate (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01
        ) / 100
    
    if st.button("🚀 Start Battle", type="primary"):
        with st.spinner("Running strategy battle..."):
            # Create strategies
            momentum_strat = MomentumStrategy(20, 50)
            mean_rev_strat = MeanReversionStrategy(14, 30, 70)
            random_strat = RandomStrategy(42)
            
            strategies = [
                ("Momentum", momentum_strat),
                ("Mean Reversion", mean_rev_strat),
                ("Random Baseline", random_strat)
            ]
            
            # Run backtests
            results_data = []
            equity_curves = {}
            
            for strategy_name, strategy in strategies:
                signals = strategy.generate_signals(stock_data)
                backtester = Backtester(stock_data, signals, battle_capital, battle_commission)
                results = backtester.run()
                metrics = backtester.get_metrics()
                
                equity_curves[strategy_name] = results['equity']
                
                results_data.append({
                    'Strategy': strategy_name,
                    'Total Return (%)': metrics['Total Return'],
                    'Sharpe Ratio': metrics['Sharpe Ratio'],
                    'Max Drawdown (%)': metrics['Max Drawdown'],
                    'Win Rate (%)': metrics['Win Rate'],
                    'Trades': int(metrics['Number of Trades'])
                })
            
            # Display scoreboard
            st.subheader("🏆 Final Scoreboard")
            
            scoreboard_df = pd.DataFrame(results_data)
            scoreboard_df = scoreboard_df.sort_values('Total Return (%)', ascending=False)
            
            # Highlight winner
            winner_idx = scoreboard_df.index[0]
            
            # Format numeric columns
            for col in ['Total Return (%)', 'Sharpe Ratio', 'Max Drawdown (%)', 'Win Rate (%)']:
                if col in scoreboard_df.columns:
                    scoreboard_df[col] = scoreboard_df[col].round(2)
            
            st.dataframe(
                scoreboard_df.style.highlight_max(
                    subset=['Total Return (%)'],
                    color='lightgreen'
                ).highlight_min(
                    subset=['Max Drawdown (%)'],
                    color='lightcoral'
                ),
                use_container_width=True,
                hide_index=True
            )
            
            # Winner callout
            winner_name = scoreboard_df.iloc[0]['Strategy']
            winner_return = scoreboard_df.iloc[0]['Total Return (%)']
            
            st.success(f"🏆 **{winner_name}** wins with {winner_return:.2f}% return!")
            
            # Equity race chart
            st.subheader("📈 Equity Curve Race")
            
            fig = go.Figure()
            
            colors = {'Momentum': 'cyan', 'Mean Reversion': 'yellow', 'Random Baseline': 'red'}
            
            for strategy_name, equity in equity_curves.items():
                fig.add_trace(go.Scatter(
                    x=equity.index,
                    y=equity,
                    name=strategy_name,
                    mode='lines',
                    line=dict(color=colors.get(strategy_name, 'white'), width=3)
                ))
            
            fig.update_layout(
                template='plotly_dark',
                height=500,
                hovermode='x unified',
                yaxis_title='Portfolio Value ($)',
                xaxis_title='Date',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            
            fig.update_yaxes(tickformat='$,.0f')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance comparison radar chart
            st.subheader("📊 Multi-Metric Comparison")
            
            # Prepare data for radar chart
            metrics_list = ['Total Return (%)', 'Sharpe Ratio', 'Win Rate (%)']
            
            fig_radar = go.Figure()
            
            for idx, row in scoreboard_df.iterrows():
                strategy_name = row['Strategy']
                
                # Normalize metrics to 0-100 scale for radar chart
                normalized_values = []
                for metric in metrics_list:
                    val = row[metric]
                    if metric == 'Total Return (%)':
                        normalized_values.append(max(0, min(100, val + 50)))  # Shift and cap
                    elif metric == 'Sharpe Ratio':
                        normalized_values.append(max(0, min(100, val * 20)))  # Scale up
                    else:
                        normalized_values.append(max(0, min(100, val)))
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=normalized_values + [normalized_values[0]],  # Close the loop
                    theta=metrics_list + [metrics_list[0]],
                    fill='toself',
                    name=strategy_name,
                    line=dict(color=colors.get(strategy_name, 'white'))
                ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=True,
                template='plotly_dark',
                height=400
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Key insights
            st.subheader("🔍 Key Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                best_return = scoreboard_df.iloc[0]
                st.metric(
                    "Best Performer",
                    best_return['Strategy'],
                    f"+{best_return['Total Return (%)']:.2f}%"
                )
            
            with col2:
                best_sharpe = scoreboard_df.loc[scoreboard_df['Sharpe Ratio'].idxmax()]
                st.metric(
                    "Best Risk-Adjusted",
                    best_sharpe['Strategy'],
                    f"Sharpe: {best_sharpe['Sharpe Ratio']:.2f}"
                )
            
            with col3:
                best_drawdown = scoreboard_df.loc[scoreboard_df['Max Drawdown (%)'].idxmax()]
                st.metric(
                    "Lowest Drawdown",
                    best_drawdown['Strategy'],
                    f"{best_drawdown['Max Drawdown (%)']:.2f}%"
                )

# ============================================================================
# Tab 6: Buy vs Sell Signal Generator
# ============================================================================
with tab6:
    st.header("📊 Buy vs Sell Signal Generator")
    
    st.markdown("""
    **Smart Signal Detection** - Identify optimal buy and sell points based on moving average crossovers.
    Green markers indicate buy signals, red markers indicate sell signals.
    """)
    
    # Signal parameters
    col1, col2 = st.columns(2)
    
    with col1:
        signal_short_window = st.slider(
            "Short MA Window",
            min_value=5,
            max_value=50,
            value=20,
            help="Shorter moving average period"
        )
    
    with col2:
        signal_long_window = st.slider(
            "Long MA Window",
            min_value=20,
            max_value=200,
            value=50,
            help="Longer moving average period"
        )
    
    if signal_short_window >= signal_long_window:
        st.warning("⚠️ Short window must be less than long window")
        st.stop()
    
    if st.button("Generate Signals", type="primary"):
        with st.spinner("Detecting buy and sell signals..."):
            # Calculate moving averages
            signal_data = stock_data.copy()
            signal_data['Short_MA'] = signal_data['Close'].rolling(window=signal_short_window).mean()
            signal_data['Long_MA'] = signal_data['Close'].rolling(window=signal_long_window).mean()
            
            # Generate signals
            signal_data['Signal'] = 0
            signal_data['Position'] = 0
            
            # Buy signal: Short MA crosses above Long MA
            signal_data.iloc[signal_short_window:, signal_data.columns.get_loc('Signal')] = np.where(
                (signal_data['Short_MA'].iloc[signal_short_window:] > signal_data['Long_MA'].iloc[signal_short_window:]) &
                (signal_data['Short_MA'].iloc[signal_short_window:].shift(1) <= signal_data['Long_MA'].iloc[signal_short_window:].shift(1)),
                1,  # Buy
                0
            )
            
            # Sell signal: Short MA crosses below Long MA
            signal_data.iloc[signal_short_window:, signal_data.columns.get_loc('Position')] = np.where(
                (signal_data['Short_MA'][signal_short_window:] < signal_data['Long_MA'][signal_short_window:]) &
                (signal_data['Short_MA'][signal_short_window:].shift(1) >= signal_data['Long_MA'][signal_short_window:].shift(1)),
                -1,  # Sell
                0
            )
            
            # Combine buy and sell
            signal_data['Combined_Signal'] = signal_data['Signal'] + signal_data['Position']
            
            # Get signal points
            buy_signals = signal_data[signal_data['Signal'] == 1]
            sell_signals = signal_data[signal_data['Position'] == -1]
            
            # Display statistics
            st.subheader("📈 Signal Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Buy Signals", len(buy_signals))
            
            with col2:
                st.metric("Total Sell Signals", len(sell_signals))
            
            with col3:
                total_signals = len(buy_signals) + len(sell_signals)
                st.metric("Total Signals", total_signals)
            
            with col4:
                days_per_signal = len(signal_data) / total_signals if total_signals > 0 else 0
                st.metric("Avg Days/Signal", f"{days_per_signal:.1f}")
            
            # Plot signals
            st.subheader("📊 Price Chart with Buy/Sell Signals")
            
            fig = go.Figure()
            
            # Price line
            fig.add_trace(go.Scatter(
                x=signal_data.index,
                y=signal_data['Close'],
                name='Price',
                line=dict(color='white', width=2)
            ))
            
            # Short MA
            fig.add_trace(go.Scatter(
                x=signal_data.index,
                y=signal_data['Short_MA'],
                name=f'Short MA ({signal_short_window})',
                line=dict(color='cyan', width=1.5)
            ))
            
            # Long MA
            fig.add_trace(go.Scatter(
                x=signal_data.index,
                y=signal_data['Long_MA'],
                name=f'Long MA ({signal_long_window})',
                line=dict(color='orange', width=1.5)
            ))
            
            # Buy signals
            if not buy_signals.empty:
                fig.add_trace(go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['Close'],
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(
                        symbol='triangle-up',
                        size=15,
                        color='lime',
                        line=dict(color='white', width=1)
                    )
                ))
            
            # Sell signals
            if not sell_signals.empty:
                fig.add_trace(go.Scatter(
                    x=sell_signals.index,
                    y=sell_signals['Close'],
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(
                        symbol='triangle-down',
                        size=15,
                        color='red',
                        line=dict(color='white', width=1)
                    )
                ))
            
            fig.update_layout(
                template='plotly_dark',
                height=600,
                hovermode='x unified',
                yaxis_title='Price ($)',
                xaxis_title='Date'
            )
            
            fig.update_yaxes(tickformat='$,.2f')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent signals table
            st.subheader("📋 Recent Signals (Last 10)")
            
            # Combine and sort signals
            all_signals = []
            
            for idx in buy_signals.index[-5:]:
                all_signals.append({
                    'Date': idx.strftime('%Y-%m-%d'),
                    'Type': '🟢 BUY',
                    'Price': f"${buy_signals.loc[idx, 'Close']:.2f}",
                    'Short MA': f"${buy_signals.loc[idx, 'Short_MA']:.2f}",
                    'Long MA': f"${buy_signals.loc[idx, 'Long_MA']:.2f}"
                })
            
            for idx in sell_signals.index[-5:]:
                all_signals.append({
                    'Date': idx.strftime('%Y-%m-%d'),
                    'Type': '🔴 SELL',
                    'Price': f"${sell_signals.loc[idx, 'Close']:.2f}",
                    'Short MA': f"${sell_signals.loc[idx, 'Short_MA']:.2f}",
                    'Long MA': f"${sell_signals.loc[idx, 'Long_MA']:.2f}"
                })
            
            if all_signals:
                signals_df = pd.DataFrame(all_signals)
                signals_df = signals_df.sort_values('Date', ascending=False).head(10)
                st.dataframe(signals_df, use_container_width=True, hide_index=True)
            else:
                st.info("No signals generated in the selected period")
            
            # Signal quality analysis
            st.subheader("🎯 Signal Quality Analysis")
            
            if len(buy_signals) > 0 and len(sell_signals) > 0:
                # Calculate forward returns after buy signals
                buy_forward_returns = []
                for buy_date in buy_signals.index:
                    try:
                        buy_price = signal_data.loc[buy_date, 'Close']
                        # Look ahead 10 days
                        future_idx = signal_data.index.get_loc(buy_date) + 10
                        if future_idx < len(signal_data):
                            future_price = signal_data.iloc[future_idx]['Close']
                            forward_return = (future_price - buy_price) / buy_price * 100
                            buy_forward_returns.append(forward_return)
                    except:
                        pass
                
                if buy_forward_returns:
                    avg_buy_return = np.mean(buy_forward_returns)
                    win_rate = (np.array(buy_forward_returns) > 0).sum() / len(buy_forward_returns) * 100
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            "Avg 10-Day Return (from Buys)",
                            f"{avg_buy_return:.2f}%",
                            delta=f"Win Rate: {win_rate:.1f}%"
                        )
                    
                    with col2:
                        if avg_buy_return > 0:
                            st.success("✅ Buy signals show positive forward returns")
                        else:
                            st.warning("⚠️ Buy signals show negative forward returns")

# Footer
st.markdown("---")
st.markdown(
    "**Trading Signals & Strategy Lab** | Powered by Real Market Data | "
    "⚠️ Past performance does not guarantee future results"
)
