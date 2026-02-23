# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (layer cache)
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir build \
    && pip wheel --no-cache-dir --wheel-dir /wheels -e ".[dev]"

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd -r quantlib && useradd -r -g quantlib quantlib

WORKDIR /app

# System runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels /wheels/*.whl \
    && rm -rf /wheels

# Copy application code
COPY quantlib_pro/ ./quantlib_pro/
COPY pyproject.toml ./

RUN pip install --no-cache-dir -e . --no-deps

# Create required directories
RUN mkdir -p logs cache && chown -R quantlib:quantlib /app

USER quantlib

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT:-8000}/health || exit 1

EXPOSE 8000 8501

ENV APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "quantlib_pro.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
