import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from datetime import datetime
from black_scholes import black_scholes_price
from iv_solver import implied_volatility

plt.style.use('dark_background')

RISK_FREE_RATE = 0.015  # 1.5% as example
STOCK = 'AAPL'


def fetch_option_chain(ticker):
    stock = yf.Ticker(ticker)
    expirations = stock.options
    option_data = []
    for exp in expirations:
        opt = stock.option_chain(exp)
        for option_type, df in [('call', opt.calls), ('put', opt.puts)]:
            for _, row in df.iterrows():
                option_data.append({
                    'expiration': exp,
                    'strike': row['strike'],
                    'lastPrice': row['lastPrice'],
                    'option_type': option_type
                })
    return option_data

def process_data(option_data, spot, r):
    processed = []
    today = datetime.now()
    for opt in option_data:
        T = (datetime.strptime(opt['expiration'], '%Y-%m-%d') - today).days / 365.0
        if T <= 0 or opt['lastPrice'] <= 0:
            continue
        iv = implied_volatility(
            price=opt['lastPrice'],
            S=spot,
            K=opt['strike'],
            T=T,
            r=r,
            option_type=opt['option_type']
        )
        if iv is not None and 0 < iv < 5:
            processed.append({
                'strike': opt['strike'],
                'T': T,
                'iv': iv,
                'option_type': opt['option_type']
            })
    return processed

def plot_vol_smile(processed, option_type='call'):
    data = [d for d in processed if d['option_type'] == option_type]
    strikes = [d['strike'] for d in data]
    ivs = [d['iv'] for d in data]
    plt.figure(figsize=(10,6))
    plt.plot(strikes, ivs, 'o-', color='cyan')
    plt.title(f'Volatility Smile ({option_type.capitalize()}s)')
    plt.xlabel('Strike Price')
    plt.ylabel('Implied Volatility')
    plt.grid(True, color='gray', linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_vol_surface(processed, option_type='call'):
    data = [d for d in processed if d['option_type'] == option_type]
    strikes = np.array([d['strike'] for d in data])
    Ts = np.array([d['T'] for d in data])
    ivs = np.array([d['iv'] for d in data])
    fig = plt.figure(figsize=(12,8))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_trisurf(strikes, Ts, ivs, cmap=cm.cool, linewidth=0.2, antialiased=True)
    ax.set_title(f'Volatility Surface ({option_type.capitalize()}s)')
    ax.set_xlabel('Strike Price')
    ax.set_ylabel('Time to Maturity (years)')
    ax.set_zlabel('Implied Volatility')
    fig.colorbar(surf, shrink=0.5, aspect=10)
    plt.tight_layout()
    plt.show()

def main():
    print(f"Fetching option chain for {STOCK}...")
    option_data = fetch_option_chain(STOCK)
    spot = yf.Ticker(STOCK).history(period='1d')['Close'].iloc[-1]
    print(f"Spot price: {spot:.2f}")
    processed = process_data(option_data, spot, RISK_FREE_RATE)
    print(f"Processed {len(processed)} options with valid IV.")
    plot_vol_smile(processed, option_type='call')
    plot_vol_surface(processed, option_type='call')

if __name__ == '__main__':
    main()
