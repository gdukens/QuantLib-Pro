# QuantLib Pro — Unified Quantitative Finance Suite

> Consolidation of 30 standalone quantitative finance applications into a single, production-grade platform.

[![CI](https://github.com/gdukens/quant-simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/gdukens/quant-simulator/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](https://www.python.org)

---

## Suites

| Suite | Domain | Projects |
|-------|--------|---------|
| **A** | Options Pricing & Derivatives | Black-Scholes, Monte Carlo, Volatility Surface |
| **B** | Risk Analysis & Metrics | Tail Risk, Stress Detection, Leverage Map |
| **C** | Portfolio Management & Optimization | Optimizer, Efficient Frontier, Diversification |
| **D** | Market Regime Detection | HMM Regimes, 3D State Machine, Alpha Decay |
| **E** | Execution & Market Microstructure | Order Book, Market Impact, Signals |
| **F** | Volatility Analysis | Vol Comparison, Surface Evolution, Shockwave |
| **G** | Macro & Systemic Risk | Contagion Network, Correlation Regime, Crash Cascade |

---

## Quick Start

```bash
# Clone
git clone https://github.com/gdukens/quant-simulator.git
cd quant-simulator

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install (dev mode)
pip install -e ".[dev]"

# Copy env template
cp .env.example .env

# Run tests
pytest tests/unit -m unit

# Start via Docker (infrastructure only)
docker compose up -d redis db

# Start Streamlit UI (local)
streamlit run quantlib_pro/ui/app.py
```

---

## Development Workflow

```bash
# Install pre-commit hooks (one-time)
pre-commit install

# Run linting manually
black quantlib_pro tests
flake8 quantlib_pro tests
isort quantlib_pro tests

# Run full test suite
pytest

# Run specific test categories
pytest -m unit           # Fast unit tests
pytest -m integration    # Requires Redis
pytest -m edge_case      # Boundary conditions
pytest -m load           # Performance tests (slow)
pytest -m security       # Security validation
```

---

## Project Structure

```
quantlib_pro/          # Main package
├── options/           # Suite A
├── risk/              # Suite B
├── portfolio/         # Suite C
├── market_regime/     # Suite D
├── execution/         # Suite E
├── volatility/        # Suite F
├── macro/             # Suite G
├── data/              # Data layer (fetching, caching, quality)
├── security/          # Auth, encryption, rate limiting
├── resilience/        # Circuit breaker, fallback chain
├── observability/     # Metrics, tracing, logging
├── audit/             # Calculation audit trail
├── governance/        # Data lineage, catalog, contracts
├── compliance/        # GDPR, consent, data retention
├── validation/        # Model risk framework
├── api/               # FastAPI REST layer
└── utils/             # Shared utilities

tests/
├── unit/              # Fast, no external deps
├── integration/       # Requires Redis/DB
├── edge_cases/        # Boundary conditions
├── load/              # Performance benchmarks
└── security/          # Security & injection tests

config/
├── prometheus/        # Metrics scrape config
├── grafana/           # Dashboards & datasources
├── logstash/          # Log pipeline
├── filebeat/          # Log shipper
└── redis/             # Redis production config

docs/
├── user_guide/
├── api_reference/
└── operations/        # DR runbook, on-call guide
```

---

## Documentation

- [SDLC Plan](QUANTITATIVE_FINANCE_MEGA_PROJECT_SDLC.md) — Full project plan (v4.0, 6032 lines)
- [Data Architecture](DATA_ARCHITECTURE_SPECIFICATION.md) — Data infrastructure design (v2.0)

---

## License

MIT
