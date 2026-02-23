import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns


def fetch_data(tickers, start, end):
    raw = yf.download(tickers, start=start, end=end)
    # Handle both single and multiple tickers
    if "Adj Close" in raw:
        data = raw["Adj Close"]
    elif "Close" in raw:
        data = raw["Close"]
    else:
        # If only one ticker, columns may not be multi-index
        if isinstance(raw.columns, pd.MultiIndex):
            raise KeyError("No 'Adj Close' or 'Close' column found in yfinance output.")
        else:
            # Single ticker, just return the dataframe
            return raw
    return data


def calculate_returns(data):
    returns = data.pct_change().dropna()
    return returns


def plot_correlation_heatmap(returns):
    corr = returns.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
    plt.title("Correlation Heatmap of Asset Returns")
    plt.show()


def show_risk_reduction(returns):
    indiv_std = returns.std()
    portfolio_std = returns.mean(axis=1).std()
    print("\nIndividual Asset Risks (Std Dev):")
    print(indiv_std)
    print(f"\nPortfolio Risk (Equal Weight, Std Dev): {portfolio_std:.4f}")
    print("\nDiversification reduces risk when portfolio risk is lower than most individual asset risks.")


def main():
    print("Portfolio Diversification Analyzer")
    tickers = input("Enter stock tickers separated by space (e.g. AAPL MSFT GOOGL): ").upper().split()
    start = input("Enter start date (YYYY-MM-DD): ")
    end = input("Enter end date (YYYY-MM-DD): ")

    data = fetch_data(tickers, start, end)
    if data.isnull().all().any():
        print("Some tickers returned no data. Please check your input.")
        return

    returns = calculate_returns(data)
    plot_correlation_heatmap(returns)
    show_risk_reduction(returns)


if __name__ == "__main__":
    main()
