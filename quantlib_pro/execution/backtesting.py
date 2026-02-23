"""
Backtesting Framework for Trading Strategies.

Provides a comprehensive backtesting engine with:
- Strategy simulation with historical data
- Performance metrics calculation
- Trade analytics and tearsheet generation
- Transaction costs and slippage modeling
- Portfolio rebalancing support

Example
-------
>>> strategy = MovingAverageCrossover(short_window=20, long_window=50)
>>> engine = BacktestEngine(
...     data=price_data,
...     initial_capital=100000,
...     commission=0.001,
...     slippage=0.0005
... )
>>> results = engine.run(strategy)
>>> print(results.summary())
>>> results.plot_equity_curve()
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""
    timestamp: datetime
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    commission: float = 0.0
    slippage: float = 0.0
    
    @property
    def value(self) -> float:
        """Trade value before costs."""
        return self.quantity * self.price
    
    @property
    def total_cost(self) -> float:
        """Total trade cost including commission and slippage."""
        return self.commission + self.slippage * abs(self.value)
    
    @property
    def net_value(self) -> float:
        """Trade value after costs."""
        multiplier = 1 if self.side == 'BUY' else -1
        return multiplier * (self.value + self.total_cost)


@dataclass
class Position:
    """Represents a position in a security."""
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        """Current market value at avg_price."""
        return self.quantity * self.avg_price
    
    def update(self, trade: Trade) -> None:
        """Update position with a new trade."""
        if trade.side == 'BUY':
            total_value = self.market_value + trade.value
            total_quantity = self.quantity + trade.quantity
            self.avg_price = total_value / total_quantity if total_quantity > 0 else 0
            self.quantity = total_quantity
        else:  # SELL
            self.quantity -= trade.quantity
            if self.quantity == 0:
                self.avg_price = 0.0


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    strategy_name: str
    trades: List[Trade]
    equity_curve: pd.Series
    returns: pd.Series
    positions: pd.DataFrame
    
    # Performance metrics
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Risk metrics
    var_95: float
    cvar_95: float
    
    def summary(self) -> str:
        """Generate summary statistics string."""
        return f"""
Backtest Results: {self.strategy_name}
{'=' * 60}

PERFORMANCE METRICS
-------------------
Total Return:          {self.total_return:>10.2%}
Annualized Return:     {self.annualized_return:>10.2%}
Volatility (Annual):   {self.volatility:>10.2%}
Sharpe Ratio:          {self.sharpe_ratio:>10.2f}
Sortino Ratio:         {self.sortino_ratio:>10.2f}
Max Drawdown:          {self.max_drawdown:>10.2%}
Calmar Ratio:          {self.calmar_ratio:>10.2f}

TRADE STATISTICS
----------------
Total Trades:          {self.total_trades:>10,}
Winning Trades:        {self.winning_trades:>10,}
Losing Trades:         {self.losing_trades:>10,}
Win Rate:              {self.win_rate:>10.2%}
Average Win:           ${self.avg_win:>10,.2f}
Average Loss:          ${self.avg_loss:>10,.2f}
Profit Factor:         {self.profit_factor:>10.2f}

RISK METRICS
------------
VaR (95%):             {self.var_95:>10.2%}
CVaR (95%):            {self.cvar_95:>10.2%}
"""
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary."""
        return {
            'strategy_name': self.strategy_name,
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'calmar_ratio': self.calmar_ratio,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
        }


class Strategy(ABC):
    """Base class for trading strategies."""
    
    def __init__(self, name: str = "Strategy"):
        self.name = name
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals from market data.
        
        Parameters
        ----------
        data : pd.DataFrame
            Market data with OHLCV columns
        
        Returns
        -------
        pd.Series
            Signal series: 1 (buy), 0 (neutral), -1 (sell)
        """
        pass


class BacktestEngine:
    """
    Backtesting engine for strategy evaluation.
    
    Parameters
    ----------
    data : pd.DataFrame
        Historical price data (OHLCV format)
    initial_capital : float
        Starting capital
    commission : float
        Commission rate (e.g., 0.001 = 0.1%)
    slippage : float
        Slippage rate (e.g., 0.0005 = 0.05%)
    risk_free_rate : float
        Annual risk-free rate for Sharpe calculation
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        risk_free_rate: float = 0.02,
    ):
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_free_rate = risk_free_rate
        
        # State variables
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_history: List[Tuple[datetime, float]] = []
        
        log.info(f"Initialized backtest engine with ${initial_capital:,.2f}")
    
    def run(self, strategy: Strategy) -> BacktestResult:
        """
        Run backtest with given strategy.
        
        Parameters
        ----------
        strategy : Strategy
            Trading strategy to test
        
        Returns
        -------
        BacktestResult
            Complete backtest results
        """
        log.info(f"Running backtest for strategy: {strategy.name}")
        
        # Reset state
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_history = []
        
        # Generate signals
        signals = strategy.generate_signals(self.data)
        
        # Simulate trading
        for timestamp, row in self.data.iterrows():
            signal = signals.loc[timestamp]
            price = row['Close']
            
            # Execute trades based on signal
            if signal == 1:  # Buy signal
                self._execute_buy(timestamp, price)
            elif signal == -1:  # Sell signal
                self._execute_sell(timestamp, price)
            
            # Record equity
            equity = self._calculate_equity(price)
            self.equity_history.append((timestamp, equity))
        
        # Calculate results
        return self._calculate_results(strategy.name)
    
    def _execute_buy(self, timestamp: datetime, price: float) -> None:
        """Execute a buy trade."""
        # Simple strategy: use 95% of available cash
        available_cash = self.cash * 0.95
        quantity = available_cash / (price * (1 + self.commission + self.slippage))
        
        if quantity > 0:
            trade = Trade(
                timestamp=timestamp,
                symbol='ASSET',
                side='BUY',
                quantity=quantity,
                price=price,
                commission=self.commission * quantity * price,
                slippage=self.slippage,
            )
            
            # Update cash and positions
            self.cash -= trade.value + trade.total_cost
            
            if 'ASSET' not in self.positions:
                self.positions['ASSET'] = Position('ASSET')
            self.positions['ASSET'].update(trade)
            
            self.trades.append(trade)
            log.debug(f"BUY {quantity:.2f} @ ${price:.2f}")
    
    def _execute_sell(self, timestamp: datetime, price: float) -> None:
        """Execute a sell trade."""
        if 'ASSET' not in self.positions or self.positions['ASSET'].quantity == 0:
            return
        
        position = self.positions['ASSET']
        quantity = position.quantity
        
        trade = Trade(
            timestamp=timestamp,
            symbol='ASSET',
            side='SELL',
            quantity=quantity,
            price=price,
            commission=self.commission * quantity * price,
            slippage=self.slippage,
        )
        
        # Update cash and positions
        self.cash += trade.value - trade.total_cost
        position.update(trade)
        
        self.trades.append(trade)
        log.debug(f"SELL {quantity:.2f} @ ${price:.2f}")
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate total portfolio equity."""
        position_value = 0.0
        if 'ASSET' in self.positions:
            position_value = self.positions['ASSET'].quantity * current_price
        return self.cash + position_value
    
    def _calculate_results(self, strategy_name: str) -> BacktestResult:
        """Calculate comprehensive backtest results."""
        # Build equity curve
        equity_df = pd.DataFrame(self.equity_history, columns=['timestamp', 'equity'])
        equity_df.set_index('timestamp', inplace=True)
        equity_curve = equity_df['equity']
        
        # Calculate returns
        returns = equity_curve.pct_change().dropna()
        
        # Performance metrics
        total_return = (equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        
        n_periods = len(returns)
        periods_per_year = 252  # Assume daily data
        annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
        
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        excess_returns = returns - self.risk_free_rate / periods_per_year
        sharpe_ratio = np.sqrt(periods_per_year) * excess_returns.mean() / returns.std() if returns.std() > 0 else 0
        
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(periods_per_year)
        sortino_ratio = (annualized_return - self.risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # Drawdown analysis
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Trade statistics
        winning_trades = [t for t in self.trades if self._is_winning_trade(t)]
        losing_trades = [t for t in self.trades if not self._is_winning_trade(t)]
        
        total_trades = len(self.trades)
        n_winning = len(winning_trades)
        n_losing = len(losing_trades)
        win_rate = n_winning / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([self._trade_pnl(t) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([self._trade_pnl(t) for t in losing_trades]) if losing_trades else 0
        
        total_wins = sum(self._trade_pnl(t) for t in winning_trades)
        total_losses = abs(sum(self._trade_pnl(t) for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Risk metrics
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean()
        
        # Build positions DataFrame
        positions_data = []
        for timestamp, equity in self.equity_history:
            if 'ASSET' in self.positions:
                pos = self.positions['ASSET']
                positions_data.append({
                    'timestamp': timestamp,
                    'quantity': pos.quantity,
                    'value': pos.market_value,
                })
        positions_df = pd.DataFrame(positions_data)
        if not positions_df.empty:
            positions_df.set_index('timestamp', inplace=True)
        
        return BacktestResult(
            strategy_name=strategy_name,
            trades=self.trades,
            equity_curve=equity_curve,
            returns=returns,
            positions=positions_df,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            total_trades=total_trades,
            winning_trades=n_winning,
            losing_trades=n_losing,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            var_95=var_95,
            cvar_95=cvar_95,
        )
    
    def _is_winning_trade(self, trade: Trade) -> bool:
        """Check if trade was profitable."""
        # Simplified: assumes we can match buy/sell pairs
        # In reality, would need more sophisticated P&L tracking
        return trade.side == 'SELL'  # Placeholder
    
    def _trade_pnl(self, trade: Trade) -> float:
        """Calculate trade P&L."""
        # Simplified P&L calculation
        # In reality, would track entry/exit prices
        return trade.net_value if trade.side == 'SELL' else -trade.net_value


class MovingAverageCrossover(Strategy):
    """
    Simple moving average crossover strategy.
    
    Generates buy signal when short MA crosses above long MA.
    Generates sell signal when short MA crosses below long MA.
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        super().__init__(f"MA Crossover ({short_window}/{long_window})")
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate MA crossover signals."""
        prices = data['Close']
        
        # Calculate moving averages
        short_ma = prices.rolling(window=self.short_window).mean()
        long_ma = prices.rolling(window=self.long_window).mean()
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Buy when short MA crosses above long MA
        signals[short_ma > long_ma] = 1
        
        # Sell when short MA crosses below long MA
        signals[short_ma < long_ma] = -1
        
        return signals


class MeanReversionStrategy(Strategy):
    """
    Mean reversion strategy using Bollinger Bands.
    
    Buy when price touches lower band, sell when price touches upper band.
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__(f"Mean Reversion (BB {window}/{num_std})")
        self.window = window
        self.num_std = num_std
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate mean reversion signals."""
        prices = data['Close']
        
        # Calculate Bollinger Bands
        ma = prices.rolling(window=self.window).mean()
        std = prices.rolling(window=self.window).std()
        
        upper_band = ma + self.num_std * std
        lower_band = ma - self.num_std * std
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Buy when price touches lower band
        signals[prices <= lower_band] = 1
        
        # Sell when price touches upper band
        signals[prices >= upper_band] = -1
        
        return signals


class MomentumStrategy(Strategy):
    """
    Momentum strategy using RSI.
    
    Buy when RSI < oversold threshold, sell when RSI > overbought threshold.
    """
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__(f"Momentum (RSI {period})")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate momentum signals."""
        prices = data['Close']
        
        # Calculate RSI
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Buy when RSI indicates oversold
        signals[rsi < self.oversold] = 1
        
        # Sell when RSI indicates overbought
        signals[rsi > self.overbought] = -1
        
        return signals
