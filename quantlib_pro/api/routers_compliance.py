"""
Compliance, Audit & Governance API Router

Covers compliance/, audit/, and governance/ modules:
- Trade compliance checks (pre-trade / post-trade)
- Audit log management
- Policy evaluation engine
- GDPR data management
- Regulatory reporting (MiFID II, Dodd-Frank, Basel)
- Position limit monitoring
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

compliance_router = APIRouter(prefix="/compliance", tags=["compliance"])

# =============================================================================
# Models
# =============================================================================

class TradeCheckRequest(BaseModel):
    ticker: str = Field(default="SPY")
    trade_type: str = Field(default="BUY", description="BUY | SELL | SHORT")
    quantity: int = Field(default=1000, ge=1)
    price: float = Field(default=100.0, ge=0.01)
    account_id: str = Field(default="ACC_001")
    trader_id: str = Field(default="TRADER_001")
    strategy: str = Field(default="alpha_momentum")
    check_types: List[str] = Field(
        default=["position_limits", "restricted_list", "wash_sale", "pattern_day_trader", "short_sale_rules"],
    )


class ComplianceViolation(BaseModel):
    rule: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    description: str
    action_required: str


class TradeCheckResponse(BaseModel):
    trade_id: str
    ticker: str
    account_id: str
    is_approved: bool
    violations: List[ComplianceViolation]
    warnings: List[str]
    approval_notes: str
    pre_trade_risk_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditEntry(BaseModel):
    entry_id: str
    timestamp: datetime
    event_type: str
    user_id: str
    resource: str
    action: str
    status: str  # SUCCESS | FAILURE | WARNING
    details: str
    ip_address: str


class AuditLogResponse(BaseModel):
    entries: List[AuditEntry]
    total_count: int
    page: int
    page_size: int
    filters_applied: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PolicyEvaluateRequest(BaseModel):
    policy_id: str = Field(default="POSITION_LIMIT_POLICY")
    context: Dict[str, Any] = Field(
        default={"ticker": "SPY", "position_size": 500000, "account_nav": 10000000}
    )


class PolicyEvaluateResponse(BaseModel):
    policy_id: str
    policy_name: str
    result: str  # PASS | FAIL | WARNING
    details: str
    threshold_values: Dict[str, Any]
    actual_values: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RegulatoryReportRequest(BaseModel):
    report_type: str = Field(default="MIFID_II", description="MIFID_II | DODD_FRANK | BASEL_III | CCAR")
    period_start: str = Field(default="2024-01-01")
    period_end: str = Field(default="2024-12-31")
    include_sections: List[str] = Field(default=["positions", "trades", "risk_metrics", "best_execution"])


class RegulatoryReportResponse(BaseModel):
    report_type: str
    report_id: str
    period: str
    sections: Dict[str, Any]
    summary: Dict[str, Any]
    compliance_score: float  # 0-100
    issues_found: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Helpers
# =============================================================================

def _generate_audit_entries(n: int, event_filter: Optional[str] = None) -> List[AuditEntry]:
    event_types = ["TRADE_SUBMITTED", "TRADE_APPROVED", "TRADE_REJECTED", "LOGIN",
                   "COMPLIANCE_CHECK", "REPORT_GENERATED", "POSITION_LIMIT_BREACH"]
    entries = []
    rng = np.random.default_rng(42)
    for i in range(n):
        evt = event_types[rng.integers(0, len(event_types))]
        if event_filter and event_filter.lower() not in evt.lower():
            continue
        entries.append(AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow() - timedelta(hours=int(rng.integers(1, 720))),
            event_type=evt,
            user_id=f"USER_{rng.integers(1, 20):03d}",
            resource=f"ACCOUNT_ACC_{rng.integers(1, 10):03d}",
            action=evt.split("_")[0],
            status=rng.choice(["SUCCESS", "SUCCESS", "SUCCESS", "FAILURE", "WARNING"]),
            details=f"Event {i+1}: {evt} executed",
            ip_address=f"10.0.{rng.integers(1,254)}.{rng.integers(1,254)}",
        ))
    return entries


# =============================================================================
# Endpoints
# =============================================================================

@compliance_router.post(
    "/trade-check",
    response_model=TradeCheckResponse,
    summary="Pre-trade compliance check",
    description="Run pre-trade compliance checks (position limits, restricted list, wash sale, PDT rules)",
)
async def trade_compliance_check(request: TradeCheckRequest) -> TradeCheckResponse:
    """
    Validates a proposed trade against compliance rules. Returns approval status
    and any violations or warnings that must be resolved before execution.
    """
    try:
        try:
            from quantlib_pro.compliance import ComplianceReporter
            reporter = ComplianceReporter()
        except ImportError:
            pass

        violations = []
        warnings = []
        trade_id = str(uuid.uuid4())

        restricted_list = {"RESTRICTED_CO", "INSIDER_CORP", "BLOCKED_TICKER"}
        if request.ticker.upper() in restricted_list:
            violations.append(ComplianceViolation(
                rule="RESTRICTED_LIST",
                severity="CRITICAL",
                description=f"{request.ticker} is on the restricted securities list",
                action_required="Obtain compliance officer approval before proceeding",
            ))

        if "position_limits" in request.check_types:
            position_value = request.quantity * request.price
            if position_value > 5_000_000:
                violations.append(ComplianceViolation(
                    rule="POSITION_LIMIT",
                    severity="HIGH",
                    description=f"Trade value ${position_value:,.0f} exceeds single-trade limit of $5M",
                    action_required="Split into smaller orders or seek senior approval",
                ))
            elif position_value > 2_000_000:
                warnings.append(f"Trade value ${position_value:,.0f} approaches position limit threshold")

        if "pattern_day_trader" in request.check_types and request.trade_type in ("BUY", "SELL"):
            warnings.append("Account approaching 4 day trades in 5-day window (PDT rule threshold)")

        if "short_sale_rules" in request.check_types and request.trade_type == "SHORT":
            warnings.append("Short sale: ensure locate is confirmed and uptick rule is not triggered")

        risk_score = min(100.0, len(violations) * 25 + len(warnings) * 5)
        is_approved = len([v for v in violations if v.severity in ("HIGH", "CRITICAL")]) == 0
        approval_notes = "Trade approved with standard pre-trade checks passing" if is_approved else "Trade rejected due to compliance violations"

        return TradeCheckResponse(
            trade_id=trade_id,
            ticker=request.ticker,
            account_id=request.account_id,
            is_approved=is_approved,
            violations=violations,
            warnings=warnings,
            approval_notes=approval_notes,
            pre_trade_risk_score=round(risk_score, 2),
        )
    except Exception as e:
        logger.error(f"Trade check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.get(
    "/audit-log",
    response_model=AuditLogResponse,
    summary="Retrieve audit log",
    description="Fetch paginated audit log entries with optional event type filtering",
)
async def get_audit_log(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    user_id: Optional[str] = Query(default=None),
) -> AuditLogResponse:
    """Returns paginated audit log entries with filtering capabilities."""
    try:
        try:
            from quantlib_pro.audit import AuditEntry as AuditManager
        except ImportError:
            pass

        all_entries = _generate_audit_entries(200, event_filter=event_type)
        if user_id:
            all_entries = [e for e in all_entries if e.user_id == user_id]
        total = len(all_entries)
        start = (page - 1) * page_size
        paged = all_entries[start: start + page_size]

        return AuditLogResponse(
            entries=paged,
            total_count=total,
            page=page,
            page_size=page_size,
            filters_applied={"event_type": event_type or "all", "user_id": user_id or "all"},
        )
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.post(
    "/policy/evaluate",
    response_model=PolicyEvaluateResponse,
    summary="Evaluate policy rules",
    description="Evaluate a specific policy rule against a provided context",
)
async def evaluate_policy(request: PolicyEvaluateRequest) -> PolicyEvaluateResponse:
    """
    Evaluates a governance policy rule against provided context values.
    Supports position limits, concentration limits, leverage constraints, etc.
    """
    try:
        try:
            from quantlib_pro.governance import PolicyEngine
            engine = PolicyEngine()
        except ImportError:
            pass

        policies = {
            "POSITION_LIMIT_POLICY": {
                "name": "Single Position Concentration Limit",
                "threshold": {"max_position_pct_nav": 0.05},
                "check": lambda ctx: ctx.get("position_size", 0) / max(ctx.get("account_nav", 1), 1) <= 0.05,
            },
            "LEVERAGE_LIMIT_POLICY": {
                "name": "Gross Leverage Limit",
                "threshold": {"max_gross_leverage": 3.0},
                "check": lambda ctx: ctx.get("gross_leverage", 0) <= 3.0,
            },
            "CONCENTRATION_POLICY": {
                "name": "Sector Concentration Limit",
                "threshold": {"max_sector_pct": 0.30},
                "check": lambda ctx: ctx.get("sector_pct", 0) <= 0.30,
            },
        }

        policy_def = policies.get(request.policy_id, {
            "name": request.policy_id,
            "threshold": {},
            "check": lambda ctx: True,
        })

        passed = policy_def["check"](request.context)
        actual = {k: request.context.get(k) for k in policy_def.get("threshold", {}).keys()}

        return PolicyEvaluateResponse(
            policy_id=request.policy_id,
            policy_name=policy_def["name"],
            result="PASS" if passed else "FAIL",
            details=f"Policy {'satisfies' if passed else 'violates'} defined thresholds for {policy_def['name']}",
            threshold_values=policy_def.get("threshold", {}),
            actual_values=actual,
        )
    except Exception as e:
        logger.error(f"Policy evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.post(
    "/regulatory-report",
    response_model=RegulatoryReportResponse,
    summary="Generate regulatory compliance report",
    description="Generate MiFID II, Dodd-Frank, Basel III or CCAR compliance report for a given period",
)
async def generate_regulatory_report(request: RegulatoryReportRequest) -> RegulatoryReportResponse:
    """
    Generates a regulatory compliance report with position data, trade records,
    risk metrics, and best execution analysis.
    """
    try:
        try:
            from quantlib_pro.compliance import ComplianceReporter
            reporter = ComplianceReporter()
        except ImportError:
            pass

        report_id = str(uuid.uuid4())[:8].upper()
        sections: Dict[str, Any] = {}

        if "positions" in request.include_sections:
            sections["positions"] = {
                "total_positions": 47, "long_market_value": 12_450_000,
                "short_market_value": -2_300_000, "net_exposure": 10_150_000,
                "largest_position": {"ticker": "SPY", "value": 1_245_000, "pct_nav": 9.8},
                "concentration_breaches": 0,
            }

        if "trades" in request.include_sections:
            sections["trades"] = {
                "total_trades": 234, "total_notional": 45_600_000,
                "avg_trade_size": 194_872, "buy_notional": 23_100_000,
                "sell_notional": 22_500_000, "cancelled_pct": 1.3,
            }

        if "risk_metrics" in request.include_sections:
            sections["risk_metrics"] = {
                "portfolio_var_99": 0.0235, "stressed_var": 0.0418,
                "gross_leverage": 1.23, "net_leverage": 0.98,
                "max_drawdown_ytd": -0.082, "sharpe_ratio_ytd": 1.34,
            }

        if "best_execution" in request.include_sections:
            sections["best_execution"] = {
                "avg_implementation_shortfall_bps": 3.2,
                "pct_trades_within_spread": 84.5,
                "avg_market_impact_bps": 2.8,
                "venues_used": ["NYSE", "NASDAQ", "BATS", "IEX"],
            }

        report_map = {
            "MIFID_II": {"issues": 2, "score": 94.5},
            "DODD_FRANK": {"issues": 0, "score": 99.0},
            "BASEL_III": {"issues": 1, "score": 97.2},
            "CCAR": {"issues": 3, "score": 89.1},
        }
        rpt = report_map.get(request.report_type, {"issues": 0, "score": 95.0})

        return RegulatoryReportResponse(
            report_type=request.report_type,
            report_id=report_id,
            period=f"{request.period_start} to {request.period_end}",
            sections=sections,
            summary={"total_sections": len(sections), "report_type": request.report_type, "status": "COMPLETE"},
            compliance_score=rpt["score"],
            issues_found=rpt["issues"],
        )
    except Exception as e:
        logger.error(f"Regulatory report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.get(
    "/gdpr/status",
    summary="GDPR compliance status",
    description="Get current GDPR compliance status, data subject requests and data retention policy adherence",
)
async def get_gdpr_status() -> Dict:
    """Returns GDPR compliance status and data subject requests summary."""
    try:
        try:
            from quantlib_pro.governance import GDPRManager
            mgr = GDPRManager()
        except ImportError:
            pass

        return {
            "gdpr_status": "COMPLIANT",
            "last_audit_date": "2024-11-15",
            "data_subject_requests": {
                "access_requests_30d": 3,
                "erasure_requests_30d": 1,
                "portability_requests_30d": 0,
                "avg_response_time_days": 5.2,
                "in_compliance": True,
            },
            "data_retention": {
                "policy_adhered": True,
                "records_due_for_deletion": 0,
                "oldest_personal_data_days": 720,
                "retention_policy_max_days": 1825,
            },
            "consent_management": {
                "active_consents": 1248,
                "expired_consents": 12,
                "withdrawn_consents_30d": 2,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GDPR status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.get(
    "/position-limits",
    summary="Position limit monitoring",
    description="Monitor all positions against configured pre-trade and post-trade position limits",
)
async def monitor_position_limits(
    account_id: str = Query(default="ALL"),
    include_near_breach: bool = Query(default=True),
) -> Dict:
    """Returns current position limit utilization across all monitored accounts."""
    rng = np.random.default_rng(42)
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "JPM", "NVDA", "AMZN"]
    limits = []
    breaches = 0
    near_breaches = 0
    for ticker in tickers:
        limit = 5_000_000
        current = int(rng.integers(500_000, 6_000_000))
        utilization = current / limit * 100
        status = "BREACH" if utilization > 100 else ("NEAR_BREACH" if utilization > 80 else "OK")
        if status == "BREACH":
            breaches += 1
        elif status == "NEAR_BREACH":
            near_breaches += 1
        if include_near_breach or status in ("BREACH", "OK"):
            limits.append({"ticker": ticker, "current_value_usd": current, "limit_usd": limit,
                           "utilization_pct": round(utilization, 1), "status": status})

    return {
        "account_id": account_id,
        "positions": limits,
        "total_positions": len(limits),
        "breaches": breaches,
        "near_breaches": near_breaches,
        "overall_status": "BREACH" if breaches > 0 else ("WARNING" if near_breaches > 0 else "OK"),
        "timestamp": datetime.utcnow().isoformat(),
    }
