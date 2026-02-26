"""
Backtesting Dashboard

Test trading strategies with historical data and analyze performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from quantlib_pro.execution.backtesting import (
    BacktestEngine,
    MovingAverageCrossover,
    MeanReversionStrategy,
    MomentumStrategy,
)
from quantlib_pro.data.providers_legacy import DataProviderFactory

st.set_page_config(page_title="Backtesting", page_icon="", layout="wide")

st.title("Strategy Backtesting")
st.markdown("Test trading strategies with historical data and analyze performance metrics.")

# Sidebar configuration
st.sidebar.header("Configuration")

# Data provider selection
provider_type = st.sidebar.selectbox(
    "Data Provider",
    options=['simulated', 'yahoo'],
    help="Choose data source for backtesting"
)

# Symbol input (for non-simulated data)
if provider_type == 'yahoo':
    symbol = st.sidebar.text_input("Symbol", value="SPY", help="Ticker symbol to backtest")
else:
    symbol = "SIMULATED"

# Date range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=730),  # 2 years ago
        help="Backtest start date"
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now() - timedelta(days=1),
        help="Backtest end date"
    )

# Backtest parameters
st.sidebar.subheader("Backtest Parameters")

initial_capital = st.sidebar.number_input(
    "Initial Capital ($)",
    min_value=1000,
    max_value=10000000,
    value=100000,
    step=10000,
    help="Starting capital for backtest"
)

commission = st.sidebar.slider(
    "Commission (%)",
    min_value=0.0,
    max_value=1.0,
    value=0.1,
    step=0.01,
    help="Trading commission percentage"
) / 100

slippage = st.sidebar.slider(
    "Slippage (%)",
    min_value=0.0,
    max_value=0.5,
    value=0.05,
    step=0.01,
    help="Expected slippage percentage"
) / 100

# Strategy selection
st.sidebar.subheader("Strategy")

strategy_type = st.sidebar.selectbox(
    "Strategy Type",
    options=['MA Crossover', 'Mean Reversion', 'Momentum (RSI)'],
    help="Trading strategy to test"
)

# Strategy parameters
if strategy_type == 'MA Crossover':
    st.sidebar.markdown("**Moving Average Parameters**")
    short_window = st.sidebar.slider("Short Window", 5, 50, 20)
    long_window = st.sidebar.slider("Long Window", 20, 200, 50)
    
elif strategy_type == 'Mean Reversion':
    st.sidebar.markdown("**Bollinger Bands Parameters**")
    bb_window = st.sidebar.slider("Window", 10, 50, 20)
    bb_std = st.sidebar.slider("Std Dev", 1.0, 3.0, 2.0, step=0.1)
    
else:  # Momentum
    st.sidebar.markdown("**RSI Parameters**")
    rsi_period = st.sidebar.slider("Period", 5, 30, 14)
    oversold = st.sidebar.slider("Oversold", 10, 40, 30)
    overbought = st.sidebar.slider("Overbought", 60, 90, 70)

# Run backtest button
run_backtest = st.sidebar.button(" Run Backtest", type="primary", use_container_width=True)

# Main content
if run_backtest:
    with st.spinner("Fetching data and running backtest..."):
        try:
            # 1. Fetch data
            if provider_type == 'yahoo':
                provider = DataProviderFactory.create('yahoo')
            else:
                provider = DataProviderFactory.create('simulated', config={'seed': 42})
            
            data = provider.fetch_historical(
                symbol=symbol,
                start_date=str(start_date),
                end_date=str(end_date),
                interval='1d'
            )
            
            st.success(f" Fetched {len(data)} bars of data")
            
            # 2. Create strategy
            if strategy_type == 'MA Crossover':
                strategy = MovingAverageCrossover(
                    short_window=short_window,
                    long_window=long_window
                )
            elif strategy_type == 'Mean Reversion':
                strategy = MeanReversionStrategy(
                    window=bb_window,
                    num_std=bb_std
                )
            else:  # Momentum
                strategy = MomentumStrategy(
                    period=rsi_period,
                    oversold=oversold,
                    overbought=overbought
                )
            
            # 3. Run backtest
            engine = BacktestEngine(
                data=data,
                initial_capital=initial_capital,
                commission=commission,
                slippage=slippage,
            )
            
            results = engine.run(strategy)
            
            st.success(f" Backtest completed: {results.total_trades} trades executed")
            
            # Display results in tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                " Performance",
                " Metrics",
                " Trades",
                " Drawdown"
            ])
            
            with tab1:
                st.subheader("Equity Curve")
                
                # Plot equity curve
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=results.equity_curve.index,
                    y=results.equity_curve.values,
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='#00D9FF', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0, 217, 255, 0.1)',
                ))
                
                # Add buy-and-hold benchmark
                buy_hold = initial_capital * (data['Close'] / data['Close'].iloc[0])
                fig.add_trace(go.Scatter(
                    x=buy_hold.index,
                    y=buy_hold.values,
                    mode='lines',
                    name='Buy & Hold',
                    line=dict(color='#FF6B6B', width=2, dash='dash'),
                ))
                
                fig.update_layout(
                    title="Portfolio Equity Over Time",
                    xaxis_title="Date",
                    yaxis_title="Portfolio Value ($)",
                    hovermode='x unified',
                    template='plotly_dark',
                    height=500,
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Performance comparison
                st.subheader("Performance Comparison")
                
                strategy_return = results.total_return
                bh_return = (buy_hold.iloc[-1] - initial_capital) / initial_capital
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Strategy Return",
                        f"{strategy_return:.2%}",
                        delta=f"{strategy_return - bh_return:.2%} vs Buy & Hold"
                    )
                
                with col2:
                    st.metric(
                        "Buy & Hold Return",
                        f"{bh_return:.2%}"
                    )
                
                with col3:
                    outperformance = strategy_return > bh_return
                    st.metric(
                        "Outperformance",
                        " YES" if outperformance else " NO",
                        delta=None
                    )
            
            with tab2:
                st.subheader("Performance Metrics")
                
                # Key metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Return", f"{results.total_return:.2%}")
                    st.metric("Sharpe Ratio", f"{results.sharpe_ratio:.2f}")
                
                with col2:
                    st.metric("Annualized Return", f"{results.annualized_return:.2%}")
                    st.metric("Sortino Ratio", f"{results.sortino_ratio:.2f}")
                
                with col3:
                    st.metric("Volatility", f"{results.volatility:.2%}")
                    st.metric("Max Drawdown", f"{results.max_drawdown:.2%}")
                
                with col4:
                    st.metric("Calmar Ratio", f"{results.calmar_ratio:.2f}")
                    st.metric("Win Rate", f"{results.win_rate:.2%}")
                
                # Trade statistics
                st.subheader("Trade Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Trades", f"{results.total_trades:,}")
                    st.metric("Winning Trades", f"{results.winning_trades:,}")
                
                with col2:
                    st.metric("Losing Trades", f"{results.losing_trades:,}")
                    st.metric("Profit Factor", f"{results.profit_factor:.2f}")
                
                with col3:
                    st.metric("Avg Win", f"${results.avg_win:,.2f}")
                    st.metric("Avg Loss", f"${results.avg_loss:,.2f}")
                
                with col4:
                    st.metric("VaR (95%)", f"{results.var_95:.2%}")
                    st.metric("CVaR (95%)", f"{results.cvar_95:.2%}")
                
                # Returns distribution
                st.subheader("Returns Distribution")
                
                fig = go.Figure()
                
                fig.add_trace(go.Histogram(
                    x=results.returns * 100,
                    nbinsx=50,
                    name='Returns',
                    marker=dict(color='#00D9FF'),
                ))
                
                fig.update_layout(
                    title="Daily Returns Distribution",
                    xaxis_title="Return (%)",
                    yaxis_title="Frequency",
                    template='plotly_dark',
                    height=400,
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("Trade History")
                
                if results.total_trades > 0:
                    # Create trades DataFrame
                    trades_data = []
                    for trade in results.trades:
                        trades_data.append({
                            'Timestamp': trade.timestamp,
                            'Side': trade.side,
                            'Quantity': f"{trade.quantity:.2f}",
                            'Price': f"${trade.price:.2f}",
                            'Value': f"${trade.value:,.2f}",
                            'Commission': f"${trade.commission:.2f}",
                            'Total Cost': f"${trade.total_cost:.2f}",
                        })
                    
                    trades_df = pd.DataFrame(trades_data)
                    
                    # Display trades table
                    st.dataframe(
                        trades_df,
                        use_container_width=True,
                        height=400,
                    )
                    
                    # Trade distribution
                    st.subheader("Trade Distribution")
                    
                    buy_trades = sum(1 for t in results.trades if t.side == 'BUY')
                    sell_trades = sum(1 for t in results.trades if t.side == 'SELL')
                    
                    fig = go.Figure(data=[
                        go.Pie(
                            labels=['BUY', 'SELL'],
                            values=[buy_trades, sell_trades],
                            marker=dict(colors=['#00D9FF', '#FF6B6B']),
                            hole=0.4,
                        )
                    ])
                    
                    fig.update_layout(
                        title="Buy vs Sell Trades",
                        template='plotly_dark',
                        height=400,
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No trades executed during backtest period")
            
            with tab4:
                st.subheader("Drawdown Analysis")
                
                # Calculate drawdown
                cumulative = (1 + results.returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                
                # Plot drawdown
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values * 100,
                    mode='lines',
                    name='Drawdown',
                    line=dict(color='#FF6B6B', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255, 107, 107, 0.3)',
                ))
                
                fig.update_layout(
                    title="Portfolio Drawdown Over Time",
                    xaxis_title="Date",
                    yaxis_title="Drawdown (%)",
                    hovermode='x unified',
                    template='plotly_dark',
                    height=500,
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Drawdown statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Max Drawdown", f"{results.max_drawdown:.2%}")
                
                with col2:
                    # Find longest drawdown period
                    in_drawdown = drawdown < 0
                    drawdown_periods = []
                    current_period = 0
                    for val in in_drawdown:
                        if val:
                            current_period += 1
                        else:
                            if current_period > 0:
                                drawdown_periods.append(current_period)
                            current_period = 0
                    
                    longest_dd = max(drawdown_periods) if drawdown_periods else 0
                    st.metric("Longest Drawdown", f"{longest_dd} days")
                
                with col3:
                    st.metric("Calmar Ratio", f"{results.calmar_ratio:.2f}")
        
        except Exception as e:
            st.error(f"Error running backtest: {str(e)}")
            st.exception(e)

else:
    # Welcome message
    st.info(" Configure your backtest parameters in the sidebar and click 'Run Backtest' to begin.")
    
    # Show strategy explanations
    st.subheader("Available Strategies")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ** MA Crossover**
        
        Classic trend-following strategy:
        - Buy when short MA crosses above long MA
        - Sell when short MA crosses below long MA
        - Best for trending markets
        """)
    
    with col2:
        st.markdown("""
        ** Mean Reversion**
        
        Volatility-based strategy:
        - Buy when price touches lower Bollinger Band
        - Sell when price touches upper Bollinger Band
        - Best for range-bound markets
        """)
    
    with col3:
        st.markdown("""
        ** Momentum (RSI)**
        
        Oscillator-based strategy:
        - Buy when RSI indicates oversold (<30)
        - Sell when RSI indicates overbought (>70)
        - Best for volatile markets
        """)

# Footer
st.markdown("---")
st.markdown("""
**Note:** Past performance is not indicative of future results. 
Backtesting has inherent limitations including survivorship bias and overfitting risks.
""")
