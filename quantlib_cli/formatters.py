"""
QuantLib Pro CLI — Output Formatters

Formats API responses as tables, JSON, or rich console output.
"""

import json
from typing import Any, Dict

# Try to use rich for pretty tables
try:
    from rich.console import Console
    from rich.table import Table
    from rich.json import JSON as RichJSON
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


def format_json(data: Any) -> str:
    """Format data as indented JSON."""
    return json.dumps(data, indent=2, default=str)


def print_json(data: Any):
    """Print data as JSON to console."""
    if HAS_RICH:
        console.print(RichJSON(format_json(data)))
    else:
        print(format_json(data))


def print_table(data: Any, title: str = None):
    """
    Print data as a formatted table.

    Handles:
    - dict: key-value pairs
    - list of dicts: tabular data
    - other: falls back to JSON
    """
    if not HAS_RICH:
        print(format_json(data))
        return

    if isinstance(data, dict):
        # Check if it's a dict of simple values (show as key-value table)
        if all(not isinstance(v, (dict, list)) for v in data.values()):
            table = Table(title=title or "Result")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            for k, v in data.items():
                table.add_row(str(k), _format_value(v))
            console.print(table)
            return

        # Otherwise print as JSON
        print_json(data)

    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        # List of dicts → table
        keys = list(data[0].keys())
        table = Table(title=title or "Results")
        for key in keys:
            table.add_column(key.replace("_", " ").title(), style="cyan")
        for row in data:
            table.add_row(*[_format_value(row.get(k, "")) for k in keys])
        console.print(table)

    else:
        print_json(data)


def _format_value(v: Any) -> str:
    """Format a single value for table display."""
    if v is None:
        return "-"
    if isinstance(v, float):
        if abs(v) < 0.01 or abs(v) > 10000:
            return f"{v:.4e}"
        return f"{v:.4f}"
    if isinstance(v, bool):
        return "✓" if v else "✗"
    if isinstance(v, (list, dict)):
        return json.dumps(v, default=str)[:50] + "..."
    return str(v)


def print_success(message: str):
    """Print a success message."""
    if HAS_RICH:
        console.print(f"[green]✓[/green] {message}")
    else:
        print(f"✓ {message}")


def print_error(message: str):
    """Print an error message."""
    if HAS_RICH:
        console.print(f"[red]✗[/red] {message}")
    else:
        print(f"✗ {message}")


def print_warning(message: str):
    """Print a warning message."""
    if HAS_RICH:
        console.print(f"[yellow]![/yellow] {message}")
    else:
        print(f"! {message}")


def print_info(message: str):
    """Print an info message."""
    if HAS_RICH:
        console.print(f"[blue]ℹ[/blue] {message}")
    else:
        print(f"ℹ {message}")
