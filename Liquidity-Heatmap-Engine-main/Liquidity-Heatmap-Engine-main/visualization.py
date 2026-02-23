import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seaborn as sns

class LiquidityHeatmapVisualizer:
    def __init__(self, simulator):
        self.simulator = simulator
        self.n_steps = simulator.n_steps
        self.n_levels = simulator.n_levels
        self.order_books = simulator.order_books
        self.mid_prices = simulator.mid_prices
        self.stats = simulator.stats

    def animate(self):
        # Prepare heatmap data
        heatmap = np.zeros((self.n_levels, self.n_steps))
        for t, (prices, bid_volumes, ask_volumes) in enumerate(self.order_books):
            heatmap[:, t] = bid_volumes + ask_volumes

        fig = plt.figure(figsize=(12, 6), facecolor='#181a1b')
        gs = fig.add_gridspec(1, 2, width_ratios=[3, 1])
        ax_heatmap = fig.add_subplot(gs[0, 0])
        ax_stats = fig.add_subplot(gs[0, 1])

        # Dark theme
        fig.patch.set_facecolor('#181a1b')
        ax_heatmap.set_facecolor('#181a1b')
        ax_stats.set_facecolor('#181a1b')

        # Heatmap styling
        cmap = sns.color_palette("rocket", as_cmap=True)
        im = ax_heatmap.imshow(heatmap, aspect='auto', cmap=cmap, origin='lower',
                              interpolation='bilinear')
        ax_heatmap.set_title('Liquidity Heatmap', color='w', fontsize=16)
        ax_heatmap.set_xlabel('Time', color='w')
        ax_heatmap.set_ylabel('Price Level', color='w')
        ax_heatmap.tick_params(axis='both', colors='w')

        # Mid-price line
        mid_line, = ax_heatmap.plot([], [], color='cyan', lw=2, label='Mid Price')
        wall_scatter = ax_heatmap.scatter([], [], s=120, color='yellow', marker='s', label='Liquidity Wall')

        # Imbalance meter
        ax_stats.set_title('Imbalance Meter', color='w', fontsize=14)
        bar = ax_stats.barh([0], [0], color='lime', height=0.5)
        ax_stats.set_xlim(-1, 1)
        ax_stats.set_yticks([])
        ax_stats.set_xticks([-1, 0, 1])
        ax_stats.tick_params(axis='x', colors='w')
        ax_stats.spines['bottom'].set_color('w')
        ax_stats.spines['top'].set_color('w')
        ax_stats.spines['left'].set_color('w')
        ax_stats.spines['right'].set_color('w')

        stats_text = ax_stats.text(0, 0.7, '', color='w', fontsize=12, va='center')

        def update(frame):
            # Update heatmap
            im.set_data(heatmap[:, :frame+1])
            # Update mid-price line
            mid_line.set_data(np.arange(frame+1),
                             [self.n_levels//2 + (self.mid_prices[i] - self.mid_prices[0])/self.simulator.tick_size for i in range(frame+1)])
            # Highlight liquidity walls
            stats = self.stats[frame]
            walls = stats['walls']
            wall_y = walls
            wall_x = np.full_like(walls, frame)
            wall_scatter.set_offsets(np.c_[wall_x, wall_y])
            # Update imbalance meter
            bar[0].set_width(stats['imbalance'])
            # Update stats text
            stats_text.set_text(f"Bid Vol: {int(stats['bid_sum'])}\nAsk Vol: {int(stats['ask_sum'])}\nImbalance: {stats['imbalance']:.2f}")
            return [im, mid_line, wall_scatter, bar[0], stats_text]

        ani = animation.FuncAnimation(fig, update, frames=self.n_steps,
                                      interval=60, blit=True, repeat=False)
        plt.tight_layout()
        plt.show()
