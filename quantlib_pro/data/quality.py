"""
Data quality validation — contract-based checks applied to every
DataFrame before it enters the processing pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

import pandas as pd
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class QualityReport:
    asset_id: str
    is_valid: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    row_count: int = 0
    completeness: float = 1.0
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            raise DataQualityError(
                f"Quality contract violated for '{self.asset_id}':\n"
                + "\n".join(f"  • {v}" for v in self.violations)
            )


class DataQualityError(ValueError):
    pass


@dataclass
class QualityContract:
    """
    Formal specification of what constitutes valid data for an asset.
    """
    asset_id: str
    required_columns: list[str]
    not_null_columns: list[str]
    value_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    completeness_threshold: float = 0.95
    custom_checks: list[Callable[[pd.DataFrame], tuple[bool, str]]] = field(
        default_factory=list
    )


# ─── Standard contracts ──────────────────────────────────────────────────────

OHLCV_CONTRACT = QualityContract(
    asset_id="ohlcv",
    required_columns=["Open", "High", "Low", "Close", "Volume"],
    not_null_columns=["Close", "Volume"],
    value_ranges={
        "Open": (1e-4, 1e6),
        "High": (1e-4, 1e6),
        "Low": (1e-4, 1e6),
        "Close": (1e-4, 1e6),
        "Volume": (0.0, 1e13),
    },
    completeness_threshold=0.95,
    custom_checks=[
        lambda df: (
            (df["High"] >= df["Low"]).all(),
            "High must be >= Low for every row",
        ),
        lambda df: (
            (df["High"] >= df["Close"]).all(),
            "High must be >= Close for every row",
        ),
        lambda df: (
            (df["Low"] <= df["Close"]).all(),
            "Low must be <= Close for every row",
        ),
    ],
)

PORTFOLIO_CONTRACT = QualityContract(
    asset_id="user_portfolio",
    required_columns=["ticker", "weight"],
    not_null_columns=["ticker", "weight"],
    value_ranges={"weight": (0.0, 1.0)},
    completeness_threshold=1.0,
    custom_checks=[
        lambda df: (
            abs(df["weight"].sum() - 1.0) < 1e-6,
            f"Weights must sum to 1.0, got {df['weight'].sum():.6f}",
        ),
    ],
)


# ─── Validator ───────────────────────────────────────────────────────────────

class DataQualityValidator:
    """
    Validates a DataFrame against a :class:`QualityContract`.

    Usage::

        validator = DataQualityValidator()
        report = validator.validate(df, OHLCV_CONTRACT)
        report.raise_if_invalid()
    """

    def validate(self, df: pd.DataFrame, contract: QualityContract) -> QualityReport:
        violations: list[str] = []
        warnings: list[str] = []

        # 1. Row count
        if df.empty:
            return QualityReport(
                asset_id=contract.asset_id,
                is_valid=False,
                violations=["DataFrame is empty"],
                row_count=0,
            )

        # 2. Required columns
        missing = set(contract.required_columns) - set(df.columns)
        if missing:
            violations.append(f"Missing required columns: {sorted(missing)}")

        # 3. Null checks
        for col in contract.not_null_columns:
            if col not in df.columns:
                continue
            null_pct = df[col].isnull().mean()
            if null_pct > 0:
                msg = f"Null values in '{col}': {null_pct:.1%}"
                if null_pct > (1 - contract.completeness_threshold):
                    violations.append(msg)
                else:
                    warnings.append(msg)

        # 4. Value ranges
        for col, (lo, hi) in contract.value_ranges.items():
            if col not in df.columns:
                continue
            series = df[col].dropna()
            out_of_range = ((series < lo) | (series > hi)).sum()
            if out_of_range:
                violations.append(
                    f"'{col}': {out_of_range} value(s) outside [{lo}, {hi}]"
                )

        # 5. Completeness
        completeness = float(df.notnull().mean().mean())
        if completeness < contract.completeness_threshold:
            violations.append(
                f"Overall completeness {completeness:.1%} < threshold "
                f"{contract.completeness_threshold:.1%}"
            )

        # 6. Custom checks
        for check_fn in contract.custom_checks:
            try:
                passed, message = check_fn(df)
                if not passed:
                    violations.append(message)
            except Exception as exc:
                warnings.append(f"Custom check error: {exc}")

        report = QualityReport(
            asset_id=contract.asset_id,
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            row_count=len(df),
            completeness=completeness,
        )

        if violations:
            log.error("Quality violations [%s]: %s", contract.asset_id, violations)
        elif warnings:
            log.warning("Quality warnings [%s]: %s", contract.asset_id, warnings)
        else:
            log.debug("Quality OK [%s] – %d rows", contract.asset_id, len(df))

        return report

    def clean(self, df: pd.DataFrame, contract: QualityContract) -> pd.DataFrame:
        """
        Best-effort cleaning: fill small gaps, clip extreme values.
        Run *after* :meth:`validate` so you know the damage before fixing.
        """
        df = df.copy()

        # Forward-fill then backward-fill small gaps (<= 3 consecutive NaNs)
        df = df.ffill(limit=3).bfill(limit=3)

        # Clip values to allowed ranges
        for col, (lo, hi) in contract.value_ranges.items():
            if col in df.columns:
                df[col] = df[col].clip(lower=lo, upper=hi)

        return df
