"""
Moving Average Crossover Strategy
A simple trading strategy that generates buy/sell signals based on moving average crossovers.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def fetch_stock_data(ticker, start_date, end_date):
    """
    Fetch historical stock data using yfinance.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
    
    Returns:
        pandas.DataFrame: Historical stock data
    """
    print(f"Fetching data for {ticker}...")
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    return data


def calculate_moving_averages(data, short_window=20, long_window=50):
    """
    Calculate short-term and long-term moving averages.
    
    Args:
        data (pandas.DataFrame): Stock data with 'Close' prices
        short_window (int): Short-term moving average period (default: 20 days)
        long_window (int): Long-term moving average period (default: 50 days)
    
    Returns:
        pandas.DataFrame: Data with added moving average columns
    """
    data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
    data['Long_MA'] = data['Close'].rolling(window=long_window).mean()
    return data


def generate_signals(data):
    """
    Generate buy and sell signals based on moving average crossovers.
    
    Buy Signal: When short-term MA crosses above long-term MA (Golden Cross)
    Sell Signal: When short-term MA crosses below long-term MA (Death Cross)
    
    Args:
        data (pandas.DataFrame): Data with moving averages
    
    Returns:
        pandas.DataFrame: Data with signal columns
    """
    # Initialize signal column (0 = no position, 1 = hold)
    data['Signal'] = 0
    
    # Generate signals: 1 when short MA > long MA, 0 otherwise
    data['Signal'] = np.where(data['Short_MA'] > data['Long_MA'], 1, 0)
    
    # Generate trading orders: difference in signals
    data['Position'] = data['Signal'].diff()
    
    # Position values:
    # 1.0 = Buy signal (crossover up)
    # -1.0 = Sell signal (crossover down)
    # 0 or NaN = No action
    
    return data


def plot_strategy(data, ticker):
    """
    Plot the stock price, moving averages, and buy/sell signals.
    
    Args:
        data (pandas.DataFrame): Data with all calculated values
        ticker (str): Stock ticker symbol for the title
    """
    plt.figure(figsize=(14, 8))
    
    # Plot stock price
    plt.plot(data.index, data['Close'], label='Stock Price', color='black', alpha=0.5, linewidth=1.5)
    
    # Plot moving averages
    plt.plot(data.index, data['Short_MA'], label='20-Day MA (Short)', color='blue', linewidth=2)
    plt.plot(data.index, data['Long_MA'], label='50-Day MA (Long)', color='red', linewidth=2)
    
    # Plot buy signals (green upward triangles)
    buy_signals = data[data['Position'] == 1]
    plt.scatter(buy_signals.index, buy_signals['Close'], 
                label='Buy Signal', marker='^', color='green', s=200, alpha=0.8, zorder=5)
    
    # Plot sell signals (red downward triangles)
    sell_signals = data[data['Position'] == -1]
    plt.scatter(sell_signals.index, sell_signals['Close'], 
                label='Sell Signal', marker='v', color='red', s=200, alpha=0.8, zorder=5)
    
    # Formatting
    plt.title(f'{ticker} - Moving Average Crossover Strategy', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price ($)', fontsize=12)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    print(f"\nDisplaying chart for {ticker}...")
    plt.show()


def print_signals(data):
    """
    Print buy and sell signals with dates and prices.
    
    Args:
        data (pandas.DataFrame): Data with signal information
    """
    buy_signals = data[data['Position'] == 1]
    sell_signals = data[data['Position'] == -1]
    
    print("\n" + "="*60)
    print("BUY SIGNALS (Golden Cross - Short MA crosses above Long MA)")
    print("="*60)
    if len(buy_signals) > 0:
        for date, row in buy_signals.iterrows():
            # Ensure date is a Timestamp and Close is a float
            date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
            close_val = row['Close']
            # Extract scalar if Series
            if isinstance(close_val, pd.Series):
                close_val = close_val.item()
            price = float(close_val) if not pd.isnull(close_val) else None
            if price is not None:
                print(f"Date: {date_str} | Price: ${price:.2f}")
            else:
                print(f"Date: {date_str} | Price: N/A")
    else:
        print("No buy signals generated in this period.")
    
    print("\n" + "="*60)
    print("SELL SIGNALS (Death Cross - Short MA crosses below Long MA)")
    print("="*60)
    if len(sell_signals) > 0:
        for date, row in sell_signals.iterrows():
            date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
            close_val = row['Close']
            if isinstance(close_val, pd.Series):
                close_val = close_val.item()
            price = float(close_val) if not pd.isnull(close_val) else None
            if price is not None:
                print(f"Date: {date_str} | Price: ${price:.2f}")
            else:
                print(f"Date: {date_str} | Price: N/A")
    else:
        print("No sell signals generated in this period.")
    print("="*60 + "\n")


def main():
    """
    Main function to run the moving average crossover strategy.
    """
    # Configuration
    TICKER = 'GOOGL'  # Changed default ticker to Google for reliability
    SHORT_WINDOW = 20  # Short-term moving average (20 days)
    LONG_WINDOW = 50   # Long-term moving average (50 days)
    
    # Date range (last 6 months for better visualization)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    print("="*60)
    print("MOVING AVERAGE CROSSOVER STRATEGY")
    print("="*60)
    print(f"Ticker: {TICKER}")
    print(f"Short-term MA: {SHORT_WINDOW} days")
    print(f"Long-term MA: {LONG_WINDOW} days")
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("="*60 + "\n")
    
    # Fetch stock data
    data = fetch_stock_data(TICKER, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    if data.empty:
        print("Error: No data retrieved. Please check the ticker symbol and try again.")
        return
    
    # Calculate moving averages
    data = calculate_moving_averages(data, SHORT_WINDOW, LONG_WINDOW)
    
    # Generate signals
    data = generate_signals(data)
    
    # Print signals
    print_signals(data)
    
    # Plot the strategy
    plot_strategy(data, TICKER)
    
    print("Analysis complete!")


if __name__ == "__main__":
    main()
