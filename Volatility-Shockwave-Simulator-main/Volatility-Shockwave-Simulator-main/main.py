import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from simulator import VolatilityShockwaveSimulator
from pricing import black_scholes_call, delta, vega

import pandas as pd

plt.style.use('dark_background')

# Simulation parameters
S0 = 100
mu = 0.05
sigma_low = 0.2
sigma_high = 0.6
T = 2.0
N = 400
K = 100
r = 0.01
switch_prob = 0.03
shock_prob = 0.01
shock_magnitude = 2.5

dt = T / N
sim = VolatilityShockwaveSimulator(S0, mu, sigma_low, sigma_high, T, dt, switch_prob, shock_prob, shock_magnitude)
sim.reset()

prices = [S0]
vols = [sigma_low]
shocks = [False]
option_prices = [black_scholes_call(S0, K, T, r, sigma_low)]
deltas = [delta(S0, K, T, r, sigma_low)]
vegas = [vega(S0, K, T, r, sigma_low)]

fig = plt.figure(figsize=(12, 8))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[2, 1])

ax_stock = plt.subplot(gs[0, 0])
ax_option = plt.subplot(gs[1, 0])
ax_side = plt.subplot(gs[:, 1])

stock_line, = ax_stock.plot([], [], lw=2, color='cyan')
vol_spike = ax_stock.fill_between([], [], [], color='red', alpha=0.3)
option_line, = ax_option.plot([], [], lw=2, color='orange')
vega_meter = ax_side.barh(['Vega'], [0], color='magenta', alpha=0.7)
vol_text = ax_side.text(0.1, 0.7, '', fontsize=14, color='white', transform=ax_side.transAxes)
shock_text = ax_side.text(0.1, 0.5, '', fontsize=14, color='red', transform=ax_side.transAxes)

ax_stock.set_title('Stock Price', color='white')
ax_option.set_title('Option Price', color='white')
ax_side.set_title('Live Metrics', color='white')
ax_stock.set_xlim(0, N)
ax_stock.set_ylim(S0 * 0.5, S0 * 1.5)
ax_option.set_xlim(0, N)
ax_option.set_ylim(0, S0 * 0.5)
ax_side.set_xlim(0, 1)
ax_side.set_ylim(0, 1)
ax_side.axis('off')

# Animation update function
def update(frame):
    sim.step()
    prices.append(sim.prices[-1])
    vols.append(sim.volatility[-1])
    shocks.append(sim.shockwaves[-1])
    t_remain = T - frame * dt
    opt_price = black_scholes_call(prices[-1], K, max(t_remain, 1e-6), r, vols[-1])
    option_prices.append(opt_price)
    deltas.append(delta(prices[-1], K, max(t_remain, 1e-6), r, vols[-1]))
    vegas.append(vega(prices[-1], K, max(t_remain, 1e-6), r, vols[-1]))

    stock_line.set_data(range(len(prices)), prices)
    # Highlight volatility spikes
    spike_indices = [i for i, s in enumerate(shocks) if s]
    if spike_indices:
        ax_stock.cla()
        ax_stock.set_title('Stock Price', color='white')
        ax_stock.set_xlim(0, N)
        ax_stock.set_ylim(S0 * 0.5, S0 * 1.5)
        ax_stock.plot(range(len(prices)), prices, lw=2, color='cyan')
        for idx in spike_indices:
            ax_stock.axvspan(idx-1, idx+1, color='red', alpha=0.3)
    option_line.set_data(range(len(option_prices)), option_prices)
    # Vega meter
    ax_side.clear()
    ax_side.barh(['Vega'], [vegas[-1]/max(vegas)], color='magenta', alpha=0.7)
    ax_side.text(0.1, 0.7, f'Volatility: {vols[-1]:.2f}', fontsize=14, color='white', transform=ax_side.transAxes)
    if shocks[-1]:
        ax_side.text(0.1, 0.5, 'Shockwave!', fontsize=14, color='red', transform=ax_side.transAxes)
    else:
        ax_side.text(0.1, 0.5, '', fontsize=14, color='red', transform=ax_side.transAxes)
    ax_side.set_title('Live Metrics', color='white')
    ax_side.set_xlim(0, 1)
    ax_side.set_ylim(0, 1)
    ax_side.axis('off')
    return stock_line, option_line

ani = animation.FuncAnimation(fig, update, frames=N, interval=40, blit=False)
plt.tight_layout()
plt.show()
