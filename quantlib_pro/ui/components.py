"""
QuantLib Pro UI Components

Week 12: Reusable Streamlit components for dashboards.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


def metric_card(title: str, value: Any, delta: Optional[str] = None, help_text: Optional[str] = None):
    """Display a metric card with optional delta and help text."""
    st.metric(label=title, value=value, delta=delta, help=help_text)


def multi_metric_row(metrics: List[Dict[str, Any]]):
    """Display multiple metrics in a row.
    
    Args:
        metrics: List of dicts with keys: title, value, delta (optional), help (optional)
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            metric_card(
                title=metric["title"],
                value=metric["value"],
                delta=metric.get("delta"),
                help_text=metric.get("help"),
            )


def plot_time_series(
    data: pd.DataFrame,
    title: str,
    x_col: str = "date",
    y_cols: Optional[List[str]] = None,
    height: int = 400,
) -> go.Figure:
    """Create an interactive time series plot.
    
    Args:
        data: DataFrame with time series data
        title: Plot title
        x_col: Column name for x-axis
        y_cols: List of column names to plot (if None, uses all numeric columns)
        height: Plot height in pixels
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    if y_cols is None:
        y_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in y_cols:
        fig.add_trace(
            go.Scatter(
                x=data[x_col],
                y=data[col],
                mode="lines",
                name=col,
            )
        )
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col.capitalize(),
        yaxis_title="Value",
        hovermode="x unified",
        height=height,
        template="plotly_white",
    )
    
    return fig


def plot_efficient_frontier(
    returns: np.ndarray,
    volatilities: np.ndarray,
    sharpe_ratios: np.ndarray,
    optimal_idx: Optional[int] = None,
    height: int = 500,
) -> go.Figure:
    """Plot the efficient frontier with Sharpe ratio coloring.
    
    Args:
        returns: Array of portfolio returns
        volatilities: Array of portfolio volatilities
        sharpe_ratios: Array of Sharpe ratios
        optimal_idx: Index of the optimal portfolio (max Sharpe ratio)
        height: Plot height in pixels
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Efficient frontier colored by Sharpe ratio
    fig.add_trace(
        go.Scatter(
            x=volatilities * 100,
            y=returns * 100,
            mode="markers",
            marker=dict(
                size=8,
                color=sharpe_ratios,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Sharpe Ratio"),
            ),
            text=[f"Sharpe: {sr:.2f}" for sr in sharpe_ratios],
            hovertemplate="<b>Volatility:</b> %{x:.2f}%<br>"
            + "<b>Return:</b> %{y:.2f}%<br>"
            + "%{text}<br>"
            + "<extra></extra>",
            name="Efficient Frontier",
        )
    )
    
    # Mark optimal portfolio
    if optimal_idx is not None:
        fig.add_trace(
            go.Scatter(
                x=[volatilities[optimal_idx] * 100],
                y=[returns[optimal_idx] * 100],
                mode="markers",
                marker=dict(size=15, color="red", symbol="star"),
                name="Optimal Portfolio",
                hovertemplate="<b>Optimal Portfolio</b><br>"
                + f"Volatility: {volatilities[optimal_idx]*100:.2f}%<br>"
                + f"Return: {returns[optimal_idx]*100:.2f}%<br>"
                + f"Sharpe: {sharpe_ratios[optimal_idx]:.2f}<br>"
                + "<extra></extra>",
            )
        )
    
    fig.update_layout(
        title="Efficient Frontier",
        xaxis_title="Annualized Volatility (%)",
        yaxis_title="Annualized Return (%)",
        hovermode="closest",
        height=height,
        template="plotly_white",
    )
    
    return fig


def plot_portfolio_weights(
    weights: Dict[str, float],
    title: str = "Portfolio Allocation",
    height: int = 400,
) -> go.Figure:
    """Create a pie chart of portfolio weights.
    
    Args:
        weights: Dict mapping ticker to weight
        title: Chart title
        height: Plot height in pixels
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(weights.keys()),
                values=list(weights.values()),
                hole=0.3,
                textposition="inside",
                textinfo="label+percent",
            )
        ]
    )
    
    fig.update_layout(
        title=title,
        height=height,
        template="plotly_white",
    )
    
    return fig


def plot_correlation_matrix(
    corr_matrix: pd.DataFrame,
    title: str = "Correlation Matrix",
    height: int = 500,
) -> go.Figure:
    """Create a heatmap of the correlation matrix.
    
    Args:
        corr_matrix: Correlation matrix DataFrame
        title: Chart title
        height: Plot height in pixels
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale="RdBu",
            zmid=0,
            text=corr_matrix.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            colorbar=dict(title="Correlation"),
        )
    )
    
    fig.update_layout(
        title=title,
        height=height,
        template="plotly_white",
    )
    
    return fig


def plot_var_distribution(
    returns: np.ndarray,
    var_value: float,
    cvar_value: float,
    confidence_level: float = 0.95,
    height: int = 400,
) -> go.Figure:
    """Plot return distribution with VaR and CVaR markers.
    
    Args:
        returns: Array of historical returns
        var_value: VaR value
        cvar_value: CVaR value
        confidence_level: Confidence level for VaR
        height: Plot height in pixels
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Histogram of returns
    fig.add_trace(
        go.Histogram(
            x=returns * 100,
            nbinsx=50,
            name="Returns",
            marker=dict(color="lightblue", line=dict(color="darkblue", width=1)),
        )
    )
    
    # VaR line
    fig.add_vline(
        x=var_value * 100,
        line_dash="dash",
        line_color="red",
        annotation_text=f"VaR ({confidence_level*100:.0f}%)",
        annotation_position="top",
    )
    
    # CVaR line
    fig.add_vline(
        x=cvar_value * 100,
        line_dash="dash",
        line_color="darkred",
        annotation_text=f"CVaR ({confidence_level*100:.0f}%)",
        annotation_position="bottom",
    )
    
    fig.update_layout(
        title="Return Distribution with VaR/CVaR",
        xaxis_title="Returns (%)",
        yaxis_title="Frequency",
        height=height,
        template="plotly_white",
        showlegend=True,
    )
    
    return fig


def plot_stress_test(
    scenarios: Dict[str, float],
    title: str = "Stress Test Scenarios",
    height: int = 400,
) -> go.Figure:
    """Create a bar chart of stress test scenario impacts.
    
    Args:
        scenarios: Dict mapping scenario name to percentage impact
        title: Chart title
        height: Plot height in pixels
        
    Returns:
        Plotly figure
    """
    scenario_names = list(scenarios.keys())
    impacts = list(scenarios.values())
    
    colors = ["red" if impact < 0 else "green" for impact in impacts]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=scenario_names,
                y=impacts,
                marker=dict(color=colors),
                text=[f"{impact:.2f}%" for impact in impacts],
                textposition="outside",
            )
        ]
    )
    
    fig.update_layout(
        title=title,
        xaxis_title="Scenario",
        yaxis_title="Portfolio Impact (%)",
        height=height,
        template="plotly_white",
        showlegend=False,
    )
    
    return fig


def plot_greeks(
    greeks: Dict[str, float],
    title: str = "Option Greeks",
    height: int = 300,
) -> go.Figure:
    """Create a bar chart of option Greeks.
    
    Args:
        greeks: Dict mapping Greek name to value
        title: Chart title
        height: Plot height in pixels
        
    Returns:
        Plotly figure
    """
    greek_names = list(greeks.keys())
    greek_values = list(greeks.values())
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=greek_names,
                y=greek_values,
                marker=dict(color="steelblue"),
                text=[f"{val:.4f}" for val in greek_values],
                textposition="outside",
            )
        ]
    )
    
    fig.update_layout(
        title=title,
        xaxis_title="Greek",
        yaxis_title="Value",
        height=height,
        template="plotly_white",
        showlegend=False,
    )
    
    return fig


def data_table(
    data: pd.DataFrame,
    title: Optional[str] = None,
    height: Optional[int] = None,
):
    """Display a formatted data table.
    
    Args:
        data: DataFrame to display
        title: Optional title
        height: Optional table height
    """
    if title:
        st.markdown(f"#### {title}")
    
    # Use default height if not specified
    if height is None:
        height = 400
    
    st.dataframe(data, height=height, width="stretch")


def error_message(message: str):
    """Display an error message with consistent styling."""
    st.error(f"❌ {message}")


def success_message(message: str):
    """Display a success message with consistent styling."""
    st.success(f"✅ {message}")


def warning_message(message: str):
    """Display a warning message with consistent styling."""
    st.warning(f"⚠️ {message}")


def info_message(message: str):
    """Display an info message with consistent styling."""
    st.info(f"ℹ️ {message}")


def loading_spinner(message: str = "Loading..."):
    """Context manager for displaying a loading spinner."""
    return st.spinner(message)


def download_button(data: Any, filename: str, label: str, mime_type: str = "text/csv"):
    """Create a download button for data.
    
    Args:
        data: Data to download (will be converted based on mime_type)
        filename: Name of the downloaded file
        label: Button label
        mime_type: MIME type of the data
    """
    st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime=mime_type,
    )
