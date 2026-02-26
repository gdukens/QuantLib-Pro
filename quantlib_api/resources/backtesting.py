"""
QuantLib Pro SDK — Backtesting Resource
"""
from typing import Any, Dict, List
from quantlib_api.resources.base import BaseResource


class BacktestingResource(BaseResource):
    """Strategy backtesting and performance analysis."""

    PREFIX = "/api/v1/backtesting"

    def strategies(self) -> Dict[str, Any]:
        """List available backtesting strategies."""
        return self._http.get(self._url("/strategies"))

    def run(
        self,
        strategy: str,
        tickers: List[str],
        start_date: str = None,
        end_date: str = None,
        initial_capital: float = 100000.0,
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Run backtest for a strategy.

        Parameters
        ----------
        strategy : str
            Strategy name (e.g., "momentum", "mean_reversion", "pairs_trading")
        tickers : list of str
            Universe of tickers
        start_date : str
            Backtest start date (YYYY-MM-DD)
        end_date : str
            Backtest end date (YYYY-MM-DD)
        initial_capital : float
            Starting capital
        parameters : dict
            Strategy-specific parameters

        Returns
        -------
        dict
            Backtest results: returns, Sharpe, drawdown, trade log
        """
        return self._http.post(
            self._url("/run"),
            json={
                "strategy": strategy,
                "tickers": tickers,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "parameters": parameters or {},
            },
        )

    def performance(
        self,
        backtest_id: str,
    ) -> Dict[str, Any]:
        """Get detailed performance metrics for a backtest."""
        return self._http.get(self._url(f"/performance/{backtest_id}"))

    def compare(
        self,
        backtest_ids: List[str],
    ) -> Dict[str, Any]:
        """Compare multiple backtest results."""
        return self._http.post(
            self._url("/compare"),
            json={"backtest_ids": backtest_ids},
        )
