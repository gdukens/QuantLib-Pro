"""
QuantLib Pro CLI Tool
~~~~~~~~~~~~~~~~~~~~~

Command-line interface for the QuantLib Pro API.

Usage::

    quantlib login --username demo --password demo123
    quantlib portfolio optimize --tickers AAPL,GOOGL,MSFT --budget 100000
    quantlib health
    quantlib signals current AAPL

:license: MIT
"""

from quantlib_cli.cli import main

__version__ = "1.0.0"
__all__ = ["main"]
