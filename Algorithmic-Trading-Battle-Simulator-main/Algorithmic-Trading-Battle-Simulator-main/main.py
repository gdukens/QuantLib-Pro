"""
main.py

Entry point for Algorithmic Trading Battle Simulator.
Downloads data, runs strategies, animates equity race, and displays scoreboard.
"""

import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from strategies import MomentumStrategy, MeanReversionStrategy, RandomStrategy
from backtester import Backtester

plt.style.use('dark_background')

# Settings
TICKER = 'SPY'
START = '2018-01-01'
END = '2023-01-01'
INITIAL_CAPITAL = 10000

# Download data
data = yf.download(TICKER, start=START, end=END)

# Initialize strategies
strategies = [
    ('Momentum', MomentumStrategy()),
    ('Mean Reversion', MeanReversionStrategy()),
    ('Random', RandomStrategy(seed=42)),
]

# Backtest all strategies
results = {}
metrics = {}
for name, strat in strategies:
    signals = strat.generate_signals(data)
    bt = Backtester(data, signals, initial_capital=INITIAL_CAPITAL)
    res = bt.run()
    results[name] = res
    metrics[name] = {
        'Cumulative Return': bt.cumulative_return(),
        'Sharpe Ratio': bt.sharpe_ratio(),
        'Max Drawdown': bt.max_drawdown(),
        'Win Rate': bt.win_rate(),
    }

# Animation setup
dates = data.index
fig, ax = plt.subplots(figsize=(12, 7))
colors = ['#00e6e6', '#e67e22', '#e74c3c']
lines = []
for i, (name, _) in enumerate(strategies):
    line, = ax.plot([], [], label=name, color=colors[i], lw=2)
    lines.append(line)

scoreboard_template = """
{:<16} | ${:,.2f} | Sharpe: {:>5.2f}
"""

scoreboard_box = ax.text(1.02, 0.95, '', transform=ax.transAxes, fontsize=13, va='top', ha='left', family='monospace', bbox=dict(facecolor='#222', edgecolor='#00e6e6', boxstyle='round,pad=0.5'))
leader_box = ax.text(0.5, 1.05, '', transform=ax.transAxes, fontsize=18, va='bottom', ha='center', color='#00ff99', weight='bold')

ax.set_title('Algorithmic Trading Battle Simulator', fontsize=18, color='#00e6e6', pad=20)
ax.set_xlabel('Date', fontsize=14)
ax.set_ylabel('Portfolio Value ($)', fontsize=14)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper left', fontsize=13)

# Set dark finance style
def set_dark_style():
    ax.set_facecolor('#181a20')
    fig.patch.set_facecolor('#181a20')
    ax.spines['bottom'].set_color('#00e6e6')
    ax.spines['top'].set_color('#00e6e6')
    ax.spines['right'].set_color('#00e6e6')
    ax.spines['left'].set_color('#00e6e6')
    ax.tick_params(colors='#e6e6e6')
set_dark_style()

# Animation function
def animate(i):
    if i == 0:
        for line in lines:
            line.set_data([], [])
        scoreboard_box.set_text('')
        leader_box.set_text('')
        return lines + [scoreboard_box, leader_box]
    x = dates[:i]
    eqs = []
    for idx, (name, _) in enumerate(strategies):
        y = results[name]['Equity'].values[:i]
        lines[idx].set_data(x, y)
        eqs.append(y[-1] if len(y) else INITIAL_CAPITAL)
    # Dynamically set axis limits
    ax.set_xlim(dates[0], dates[min(i, len(dates)-1)])
    all_y = np.concatenate([results[name]['Equity'].values[:i] for name, _ in strategies])
    if len(all_y) > 0:
        ax.set_ylim(np.min(all_y)*0.98, np.max(all_y)*1.02)
    # Scoreboard
    scoreboard = 'Strategy         | Portfolio   | Sharpe\n' + '-'*40 + '\n'
    for idx, (name, _) in enumerate(strategies):
        scoreboard += scoreboard_template.format(
            name, eqs[idx], metrics[name]['Sharpe Ratio'])
    # Highlight leader
    leader_idx = int(np.argmax(eqs))
    for idx, line in enumerate(lines):
        line.set_alpha(1.0 if idx == leader_idx else 0.5)
        line.set_linewidth(3 if idx == leader_idx else 2)
    scoreboard_box.set_text(scoreboard)
    leader_box.set_text(f"🏆 Leader: {strategies[leader_idx][0]}")
    return lines + [scoreboard_box, leader_box]

ani = animation.FuncAnimation(
    fig, animate, frames=len(dates)+30, interval=40, blit=True, repeat=False)

# Celebration at the end
def on_animation_end(*args):
    final_eqs = [results[name]['Equity'].iloc[-1] for name, _ in strategies]
    winner_idx = int(np.argmax(final_eqs))
    leader_box.set_text(f"🎉 Winner: {strategies[winner_idx][0]}! 🎉")
    leader_box.set_color('#ffff00')
    scoreboard_box.set_bbox(dict(facecolor='#222', edgecolor='#ffff00', boxstyle='round,pad=0.5'))
ani._stop = lambda *args, **kwargs: (on_animation_end(), animation.Animation._stop(ani, *args, **kwargs))

plt.tight_layout()
plt.show()
