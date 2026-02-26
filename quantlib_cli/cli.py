"""
QuantLib Pro CLI — Main Command Interface

All CLI commands are defined here using Click.

Usage::

    quantlib login
    quantlib health
    quantlib portfolio optimize --tickers AAPL,GOOGL --budget 100000
    quantlib risk var --confidence 0.95 --method monte_carlo
    quantlib endpoints list
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

import click

from quantlib_cli.auth_store import (
    clear_credentials,
    get_token,
    get_url,
    load_credentials,
    save_credentials,
)
from quantlib_cli.formatters import (
    print_error,
    print_info,
    print_json,
    print_success,
    print_table,
    print_warning,
)

# Lazy import SDK to avoid import errors if not installed
def get_client(require_auth: bool = True):
    """Get an authenticated QuantLib client."""
    try:
        from quantlib_api import QuantLibClient
    except ImportError:
        print_error("quantlib_api not installed. Run: pip install -e .")
        sys.exit(1)

    creds = load_credentials()
    if require_auth and not creds:
        print_error("Not authenticated. Run: quantlib login")
        sys.exit(2)

    url = get_url()
    client = QuantLibClient(base_url=url)
    if creds and creds.get("token"):
        client._http.set_token(creds["token"])
    return client


# ─────────────────────────────────────────────────────────────────────────────
# Root CLI Group
# ─────────────────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="quantlib")
@click.pass_context
def cli(ctx):
    """QuantLib Pro CLI — Command-line interface for the quantitative finance API."""
    ctx.ensure_object(dict)


# ─────────────────────────────────────────────────────────────────────────────
# Auth Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--url", default="http://localhost:8000", help="API base URL")
@click.option("--username", "-u", prompt=True, help="Username")
@click.option("--password", "-p", prompt=True, hide_input=True, help="Password")
def login(url: str, username: str, password: str):
    """Authenticate with the QuantLib Pro API."""
    try:
        from quantlib_api import QuantLibClient
    except ImportError:
        print_error("quantlib_api not installed. Run: pip install -e .")
        sys.exit(1)

    try:
        client = QuantLibClient(base_url=url, username=username, password=password)
        token = client.login()
        save_credentials(url, token, username)
        print_success(f"Logged in as {username} at {url}")
    except Exception as e:
        print_error(f"Login failed: {e}")
        sys.exit(2)


@cli.command()
def logout():
    """Clear stored credentials."""
    clear_credentials()
    print_success("Logged out. Credentials cleared.")


@cli.command()
def whoami():
    """Show current authentication status."""
    creds = load_credentials()
    if creds and creds.get("token"):
        print_info(f"Logged in as: {creds.get('username', 'unknown')}")
        print_info(f"API URL: {creds.get('url', 'unknown')}")
    else:
        print_warning("Not authenticated. Run: quantlib login")


# ─────────────────────────────────────────────────────────────────────────────
# Health Command
# ─────────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--url", default=None, help="Override API URL")
@click.option("--watch", is_flag=True, help="Continuously poll health")
@click.option("--interval", default=30, help="Poll interval in seconds")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def health(url: str, watch: bool, interval: int, as_json: bool):
    """Check API health status."""
    import time
    client = get_client(require_auth=False)

    def check():
        try:
            result = client.health.check()
            if as_json:
                print_json(result)
            else:
                status = result.get("status", "unknown")
                if status == "healthy":
                    print_success(f"API is healthy • {result.get('version', 'v?')}")
                else:
                    print_warning(f"API status: {status}")
            return True
        except Exception as e:
            print_error(f"Health check failed: {e}")
            return False

    if watch:
        print_info(f"Watching health every {interval}s (Ctrl+C to stop)")
        while True:
            check()
            time.sleep(interval)
    else:
        success = check()
        sys.exit(0 if success else 1)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints Command Group
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def endpoints():
    """List and describe API endpoints."""
    pass


@endpoints.command("list")
@click.option("--domain", "-d", help="Filter by domain (portfolio, risk, options, ...)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def endpoints_list(domain: str, as_json: bool):
    """List all available API endpoints."""
    from quantlib_cli._endpoints import ENDPOINT_LIST

    data = ENDPOINT_LIST
    if domain:
        data = [e for e in data if e["domain"].lower() == domain.lower()]

    if as_json:
        print_json(data)
    else:
        print_table(data, title="API Endpoints")


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def portfolio():
    """Portfolio optimization and management."""
    pass


@portfolio.command("optimize")
@click.option("--tickers", "-t", required=True, help="Comma-separated tickers (AAPL,GOOGL,MSFT)")
@click.option("--budget", "-b", default=100000.0, type=float, help="Investment budget ($)")
@click.option("--target", default="sharpe", type=click.Choice(["sharpe", "min_volatility", "max_return"]))
@click.option("--risk-free-rate", default=0.045, type=float, help="Risk-free rate")
@click.option("--max-position", default=0.40, type=float, help="Max single position weight")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def portfolio_optimize(tickers: str, budget: float, target: str, risk_free_rate: float, max_position: float, as_json: bool):
    """Optimize portfolio weights using Modern Portfolio Theory."""
    client = get_client()
    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    try:
        result = client.portfolio.optimize(
            tickers=ticker_list,
            budget=budget,
            risk_free_rate=risk_free_rate,
            optimization_target=target,
            max_position_size=max_position,
        )
        if as_json:
            print_json(result)
        else:
            print_table(result, title="Optimal Portfolio")
    except Exception as e:
        print_error(f"Optimization failed: {e}")
        sys.exit(1)


@portfolio.command("performance")
@click.option("--portfolio-id", "-p", default="DEMO_PORT", help="Portfolio ID")
@click.option("--period", default=252, type=int, help="Period in days")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def portfolio_performance(portfolio_id: str, period: int, as_json: bool):
    """Get portfolio performance metrics."""
    client = get_client()
    try:
        result = client.portfolio.performance(portfolio_id=portfolio_id, period_days=period)
        if as_json:
            print_json(result)
        else:
            print_table(result, title="Portfolio Performance")
    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Risk Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def risk():
    """Risk analysis: VaR, stress testing, tail risk."""
    pass


@risk.command("var")
@click.option("--portfolio-id", "-p", default="DEMO_PORT", help="Portfolio ID")
@click.option("--confidence", "-c", default=0.95, type=float, help="Confidence level (0.90-0.999)")
@click.option("--method", "-m", default="historical", type=click.Choice(["historical", "parametric", "monte_carlo"]))
@click.option("--horizon", default=10, type=int, help="Time horizon in days")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def risk_var(portfolio_id: str, confidence: float, method: str, horizon: int, as_json: bool):
    """Compute Value at Risk (VaR) and Conditional VaR."""
    client = get_client()
    try:
        result = client.risk.var(
            portfolio_id=portfolio_id,
            confidence_level=confidence,
            method=method,
            horizon_days=horizon,
        )
        if as_json:
            print_json(result)
        else:
            print_table(result, title=f"VaR Analysis ({method})")
    except Exception as e:
        print_error(f"VaR calculation failed: {e}")
        sys.exit(1)


@risk.command("stress-test")
@click.option("--portfolio-id", "-p", default="DEMO_PORT", help="Portfolio ID")
@click.option("--scenarios", "-s", default="2008_crisis,covid_crash,rate_shock", help="Comma-separated scenarios")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def risk_stress_test(portfolio_id: str, scenarios: str, as_json: bool):
    """Run stress test scenarios."""
    client = get_client()
    scenario_list = [s.strip() for s in scenarios.split(",")]
    try:
        result = client.risk.stress_test(portfolio_id=portfolio_id, scenarios=scenario_list)
        if as_json:
            print_json(result)
        else:
            print_table(result, title="Stress Test Results")
    except Exception as e:
        print_error(f"Stress test failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Options Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def options():
    """Options pricing and Greeks calculation."""
    pass


@options.command("price")
@click.option("--spot", "-s", required=True, type=float, help="Current underlying price")
@click.option("--strike", "-k", required=True, type=float, help="Strike price")
@click.option("--expiry", "-e", required=True, type=int, help="Days to expiration")
@click.option("--volatility", "-v", default=0.25, type=float, help="Implied volatility")
@click.option("--rate", "-r", default=0.045, type=float, help="Risk-free rate")
@click.option("--type", "opt_type", default="call", type=click.Choice(["call", "put"]))
@click.option("--model", default="black_scholes", type=click.Choice(["black_scholes", "binomial", "monte_carlo"]))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def options_price(spot: float, strike: float, expiry: int, volatility: float, rate: float, opt_type: str, model: str, as_json: bool):
    """Price an option using Black-Scholes or Monte Carlo."""
    client = get_client()
    try:
        result = client.options.price(
            spot=spot,
            strike=strike,
            expiry_days=expiry,
            volatility=volatility,
            risk_free_rate=rate,
            option_type=opt_type,
            model=model,
        )
        if as_json:
            print_json(result)
        else:
            print_table(result, title=f"Option Price ({model})")
    except Exception as e:
        print_error(f"Pricing failed: {e}")
        sys.exit(1)


@options.command("greeks")
@click.option("--spot", "-s", required=True, type=float, help="Current underlying price")
@click.option("--strike", "-k", required=True, type=float, help="Strike price")
@click.option("--expiry", "-e", required=True, type=int, help="Days to expiration")
@click.option("--volatility", "-v", default=0.25, type=float, help="Implied volatility")
@click.option("--type", "opt_type", default="call", type=click.Choice(["call", "put"]))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def options_greeks(spot: float, strike: float, expiry: int, volatility: float, opt_type: str, as_json: bool):
    """Calculate option Greeks (Delta, Gamma, Theta, Vega, Rho)."""
    client = get_client()
    try:
        result = client.options.greeks(
            spot=spot,
            strike=strike,
            expiry_days=expiry,
            volatility=volatility,
            option_type=opt_type,
        )
        if as_json:
            print_json(result)
        else:
            print_table(result, title="Option Greeks")
    except Exception as e:
        print_error(f"Greeks calculation failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Signals Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def signals():
    """Trading signal generation."""
    pass


@signals.command("generate")
@click.option("--ticker", "-t", required=True, help="Stock ticker")
@click.option("--strategies", "-s", default="MA_CROSSOVER,RSI,MACD", help="Comma-separated strategies")
@click.option("--lookback", default=60, type=int, help="Lookback period in days")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def signals_generate(ticker: str, strategies: str, lookback: int, as_json: bool):
    """Generate trading signals for a ticker."""
    client = get_client()
    strategy_list = [s.strip().upper() for s in strategies.split(",")]
    try:
        result = client.signals.generate(ticker=ticker.upper(), strategies=strategy_list, lookback_days=lookback)
        if as_json:
            print_json(result)
        else:
            print_table(result, title=f"Signals for {ticker.upper()}")
    except Exception as e:
        print_error(f"Signal generation failed: {e}")
        sys.exit(1)


@signals.command("current")
@click.argument("ticker")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def signals_current(ticker: str, as_json: bool):
    """Get current signals for a ticker."""
    client = get_client()
    try:
        result = client.signals.current(ticker.upper())
        if as_json:
            print_json(result)
        else:
            print_table(result, title=f"Current Signals: {ticker.upper()}")
    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Execution Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def execution():
    """Execution optimization: VWAP, TWAP, market impact."""
    pass


@execution.command("vwap")
@click.option("--ticker", "-t", required=True, help="Stock ticker")
@click.option("--shares", "-s", required=True, type=int, help="Number of shares")
@click.option("--hours", default=4.0, type=float, help="Time horizon in hours")
@click.option("--slices", default=8, type=int, help="Number of execution slices")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def execution_vwap(ticker: str, shares: int, hours: float, slices: int, as_json: bool):
    """Generate VWAP execution schedule."""
    client = get_client()
    try:
        result = client.execution.vwap_schedule(
            ticker=ticker.upper(),
            shares=shares,
            time_horizon_hours=hours,
            n_slices=slices,
        )
        if as_json:
            print_json(result)
        else:
            print_table(result, title="VWAP Schedule")
    except Exception as e:
        print_error(f"VWAP scheduling failed: {e}")
        sys.exit(1)


@execution.command("twap")
@click.option("--ticker", "-t", required=True, help="Stock ticker")
@click.option("--shares", "-s", required=True, type=int, help="Number of shares")
@click.option("--hours", default=4.0, type=float, help="Time horizon in hours")
@click.option("--slices", default=8, type=int, help="Number of execution slices")
@click.option("--randomize/--no-randomize", default=True, help="Add randomization")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def execution_twap(ticker: str, shares: int, hours: float, slices: int, randomize: bool, as_json: bool):
    """Generate TWAP execution schedule."""
    client = get_client()
    try:
        result = client.execution.twap_schedule(
            ticker=ticker.upper(),
            shares=shares,
            time_horizon_hours=hours,
            n_slices=slices,
            randomize=randomize,
        )
        if as_json:
            print_json(result)
        else:
            print_table(result, title="TWAP Schedule")
    except Exception as e:
        print_error(f"TWAP scheduling failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Compliance Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def compliance():
    """Compliance checks and regulatory reporting."""
    pass


@compliance.command("trade-check")
@click.option("--ticker", "-t", required=True, help="Stock ticker")
@click.option("--side", required=True, type=click.Choice(["buy", "sell"]))
@click.option("--quantity", "-q", required=True, type=int, help="Trade quantity")
@click.option("--portfolio-id", "-p", default="DEMO_PORT", help="Portfolio ID")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def compliance_trade_check(ticker: str, side: str, quantity: int, portfolio_id: str, as_json: bool):
    """Pre-trade compliance check."""
    client = get_client()
    try:
        result = client.compliance.trade_check(
            ticker=ticker.upper(),
            side=side,
            quantity=quantity,
            portfolio_id=portfolio_id,
        )
        if as_json:
            print_json(result)
        else:
            print_table(result, title="Compliance Check")
    except Exception as e:
        print_error(f"Compliance check failed: {e}")
        sys.exit(1)


@compliance.command("gdpr-status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def compliance_gdpr(as_json: bool):
    """Get GDPR compliance status."""
    client = get_client()
    try:
        result = client.compliance.gdpr_status()
        if as_json:
            print_json(result)
        else:
            print_table(result, title="GDPR Status")
    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)


@compliance.command("position-limits")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def compliance_position_limits(as_json: bool):
    """Get position limit monitoring."""
    client = get_client()
    try:
        result = client.compliance.position_limits()
        if as_json:
            print_json(result)
        else:
            print_table(result, title="Position Limits")
    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Data Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def data():
    """Market data access."""
    pass


@data.command("market-status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def data_market_status(as_json: bool):
    """Get current market status (open/closed)."""
    client = get_client(require_auth=False)
    try:
        result = client.data.market_status()
        if as_json:
            print_json(result)
        else:
            status = result.get("status", "unknown")
            print_success(f"Market is {status.upper()}")
    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)


@data.command("quote")
@click.argument("ticker")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def data_quote(ticker: str, as_json: bool):
    """Get real-time quote for a ticker."""
    client = get_client(require_auth=False)
    try:
        result = client.data.quote(ticker.upper())
        if as_json:
            print_json(result)
        else:
            print_table(result, title=f"Quote: {ticker.upper()}")
    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Systemic Risk Commands
# ─────────────────────────────────────────────────────────────────────────────

@cli.group()
def systemic_risk():
    """Systemic risk and contagion analysis."""
    pass


@systemic_risk.command("too-big-to-fail")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def systemic_risk_tbtf(as_json: bool):
    """Get too-big-to-fail scoring."""
    client = get_client()
    try:
        result = client.systemic_risk.too_big_to_fail()
        if as_json:
            print_json(result)
        else:
            print_table(result, title="TBTF Scores")
    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
