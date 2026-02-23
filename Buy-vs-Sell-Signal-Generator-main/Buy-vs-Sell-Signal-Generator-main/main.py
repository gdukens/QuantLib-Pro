import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# --- Settings ---
STOCK_SYMBOL = 'AAPL'  # Change to any valid stock symbol
START_DATE = '2022-01-01'
END_DATE = '2023-01-01'
SHORT_WINDOW = 20
LONG_WINDOW = 50

# --- Fetch historical data ---
def fetch_data(symbol, start, end):
    """Fetch historical stock data using yfinance."""
    data = yf.download(symbol, start=start, end=end)
    return data

# --- Calculate moving averages ---
def calculate_moving_averages(data, short_window, long_window):
    """Add short and long moving averages to DataFrame."""
    data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
    data['Long_MA'] = data['Close'].rolling(window=long_window).mean()
    return data

# --- Generate signals ---
def generate_signals(data):
    """Generate buy/sell signals based on MA crossovers."""
    data['Signal'] = 0
    # Buy: Short MA crosses above Long MA
    data['Signal'][SHORT_WINDOW:] = (
        (data['Short_MA'][SHORT_WINDOW:] > data['Long_MA'][SHORT_WINDOW:]) &
        (data['Short_MA'][SHORT_WINDOW:].shift(1) <= data['Long_MA'][SHORT_WINDOW:].shift(1))
    ).astype(int)
    # Sell: Short MA crosses below Long MA
    data['Signal'][SHORT_WINDOW:] -= (
        (data['Short_MA'][SHORT_WINDOW:] < data['Long_MA'][SHORT_WINDOW:]) &
        (data['Short_MA'][SHORT_WINDOW:].shift(1) >= data['Long_MA'][SHORT_WINDOW:].shift(1))
    ).astype(int)
    return data

# --- Plotting ---
def plot_signals(data):
    """Plot stock price, moving averages, and buy/sell signals."""
    plt.figure(figsize=(14, 7))
    plt.plot(data['Close'], label='Close Price', color='blue')
    plt.plot(data['Short_MA'], label=f'{SHORT_WINDOW}-Day MA', color='orange')
    plt.plot(data['Long_MA'], label=f'{LONG_WINDOW}-Day MA', color='purple')

    # Mark buy/sell signals
    buy_signals = data[data['Signal'] == 1]
    sell_signals = data[data['Signal'] == -1]
    plt.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', label='Buy Signal', s=100)
    plt.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', label='Sell Signal', s=100)

    plt.title(f'{STOCK_SYMBOL} Buy vs Sell Signal Generator')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- Main workflow ---
def main():
    # Fetch data
    data = fetch_data(STOCK_SYMBOL, START_DATE, END_DATE)
    # Calculate moving averages
    data = calculate_moving_averages(data, SHORT_WINDOW, LONG_WINDOW)
    # Generate signals
    data = generate_signals(data)
    # Plot results
    plot_signals(data)

if __name__ == '__main__':
    main()
