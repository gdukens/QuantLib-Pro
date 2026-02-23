import numpy as np
import pandas as pd
import plotly.graph_objs as go

def plot_3d_surface(time, regime, alpha_strength, animate=False):
    """
    Render a 3D surface: X=Time, Y=Regime, Z=Alpha Strength, colored by regime.
    If animate=True, returns a Plotly Figure with animation frames.
    """
    # Prepare meshgrid for color mapping
    # Map regime to a set of distinct colors (categorical)
    regime_unique = np.unique(regime)
    color_palette = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999']
    color_map = {r: color_palette[i % len(color_palette)] for i, r in enumerate(regime_unique)}
    color_array = np.array([color_map[r] for r in regime])

    surface = go.Scatter3d(
        x=time,
        y=regime,
        z=alpha_strength,
        mode='markers',
        marker=dict(
            size=5,
            color=color_array,
            opacity=0.85,
            line=dict(width=0.5, color='DarkSlateGrey')
        ),
        text=[f'Regime: {r}' for r in regime],
        name='Alpha Strength'
    )
    layout = go.Layout(
        title="Alpha Strength by Regime Over Time",
        scene=dict(
            xaxis_title='Time',
            yaxis_title='Regime',
            zaxis_title='Alpha Strength',
            bgcolor='#222',
            xaxis=dict(showbackground=True, backgroundcolor='#222'),
            yaxis=dict(showbackground=True, backgroundcolor='#222'),
            zaxis=dict(showbackground=True, backgroundcolor='#222'),
        ),
        template='plotly_dark',
        autosize=True,
        margin=dict(l=0, r=0, b=0, t=40)
    )
    fig = go.Figure(data=[surface], layout=layout)
    if animate:
        frames = []
        for t in range(1, len(time)):
            frame = go.Frame(data=[go.Scatter3d(
                x=time[:t+1],
                y=regime[:t+1],
                z=alpha_strength[:t+1],
                mode='markers',
                marker=dict(
                    size=5,
                    color=color_array[:t+1],
                    opacity=0.85,
                    line=dict(width=0.5, color='DarkSlateGrey')
                ),
                text=[f'Regime: {r}' for r in regime[:t+1]],
                name='Alpha Strength'
            )])
            frames.append(frame)
        fig.frames = frames
        fig.update_layout(updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [{
                'label': 'Play',
                'method': 'animate',
                'args': [None, {'frame': {'duration': 50, 'redraw': True}, 'fromcurrent': True}]
            }]
        }])
    return fig
