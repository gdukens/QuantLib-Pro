import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd

REGIME_COLORS = {'Bull': '#00FF99', 'Bear': '#FF3366', 'Sideways': '#3399FF'}

plt.style.use('dark_background')

def visualize_regimes(model):
    pca_data = model.pca_data
    labels = model.labels
    dates = model.features.index
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    scat = ax.scatter([], [], [], s=40)
    legend_handles = [plt.Line2D([0], [0], marker='o', color='w', label=regime,
                                 markerfacecolor=color, markersize=10)
                     for regime, color in REGIME_COLORS.items()]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=12)
    ax.set_xlabel('PCA 1')
    ax.set_ylabel('PCA 2')
    ax.set_zlabel('PCA 3')
    ax.set_title('3D Market Regime State Machine', color='w', fontsize=16)

    def update(frame):
        ax.cla()
        ax.set_xlabel('PCA 1')
        ax.set_ylabel('PCA 2')
        ax.set_zlabel('PCA 3')
        ax.set_title('3D Market Regime State Machine', color='w', fontsize=16)
        # Smooth rotation
        angle = frame * 0.7
        ax.view_init(elev=30, azim=angle)
        # Plot up to current frame
        x, y, z = pca_data[:frame+1, 0], pca_data[:frame+1, 1], pca_data[:frame+1, 2]
        regime = labels[frame]
        colors = [REGIME_COLORS[l] for l in labels[:frame+1]]
        scat = ax.scatter(x, y, z, c=colors, s=40, alpha=0.8, edgecolors='w', linewidths=0.5)
        # Glowing effect for active regime
        ax.scatter(x[-1], y[-1], z[-1], c=REGIME_COLORS[regime], s=200, alpha=0.9, edgecolors='w', linewidths=2)
        # Regime label
        ax.text2D(0.05, 0.95, f'Regime: {regime}', transform=ax.transAxes, color=REGIME_COLORS[regime], fontsize=18)
        # Timestamp
        ax.text2D(0.05, 0.90, f"Time: {dates[frame].strftime('%Y-%m-%d')}", transform=ax.transAxes, color='w', fontsize=14)
        # Legend
        ax.legend(handles=legend_handles, loc='upper left', fontsize=12)

    ani = FuncAnimation(fig, update, frames=len(pca_data), interval=40, repeat=False)
    plt.show()
