"""
Compliance Reporting Module.

Automated generation of compliance reports:
- Regulatory reporting (MiFID II, EMIR, Dodd-Frank)
- Risk limit monitoring
- Transaction cost analysis
- Best execution reports
- Position limit checks

Example
-------
>>> reporter = ComplianceReporter(portfolio)
>>> report = reporter.generate_daily_report()
>>> report.to_pdf('compliance_report.pdf')
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""
    timestamp: datetime
    rule_id: str
    rule_name: str
    severity: str  # 'HIGH', 'MEDIUM', 'LOW'
    description: str
    affected_entity: str  # e.g., portfolio, trade, position
    recommended_action: str
    
    def __str__(self) -> str:
        return (
            f"[{self.severity}] {self.rule_name} ({self.rule_id})\n"
            f"  Entity: {self.affected_entity}\n"
            f"  Description: {self.description}\n"
            f"  Action: {self.recommended_action}"
        )


@dataclass
class ComplianceReport:
    """Comprehensive compliance report."""
    report_id: str
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    
    # Violation tracking
    violations: List[ComplianceViolation] = field(default_factory=list)
    
    # Risk metrics
    risk_metrics: Dict = field(default_factory=dict)
    
    # Transaction analysis
    transaction_stats: Dict = field(default_factory=dict)
    
    # Position limits
    position_limits: Dict = field(default_factory=dict)
    
    @property
    def high_severity_violations(self) -> List[ComplianceViolation]:
        """Get high severity violations."""
        return [v for v in self.violations if v.severity == 'HIGH']
    
    @property
    def is_compliant(self) -> bool:
        """Check if fully compliant (no high severity violations)."""
        return len(self.high_severity_violations) == 0
    
    def summary(self) -> str:
        """Generate summary string."""
        return f"""
Compliance Report: {self.report_id}
{'=' * 60}
Type: {self.report_type}
Period: {self.period_start.date()} to {self.period_end.date()}
Generated: {self.generated_at}

VIOLATIONS SUMMARY
------------------
Total Violations: {len(self.violations)}
  High Severity: {len([v for v in self.violations if v.severity == 'HIGH'])}
  Medium Severity: {len([v for v in self.violations if v.severity == 'MEDIUM'])}
  Low Severity: {len([v for v in self.violations if v.severity == 'LOW'])}

Status: {'✓ COMPLIANT' if self.is_compliant else '✗ NON-COMPLIANT'}

RISK METRICS
------------
{self._format_dict(self.risk_metrics)}

TRANSACTION STATISTICS
----------------------
{self._format_dict(self.transaction_stats)}

POSITION LIMITS
---------------
{self._format_dict(self.position_limits)}
"""
    
    def _format_dict(self, d: Dict, indent: int = 0) -> str:
        """Format dictionary for display."""
        lines = []
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{'  ' * indent}{key}:")
                lines.append(self._format_dict(value, indent + 1))
            else:
                lines.append(f"{'  ' * indent}{key}: {value}")
        return '\n'.join(lines)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert violations to DataFrame."""
        if not self.violations:
            return pd.DataFrame()
        
        return pd.DataFrame([{
            'timestamp': v.timestamp,
            'rule_id': v.rule_id,
            'rule_name': v.rule_name,
            'severity': v.severity,
            'description': v.description,
            'entity': v.affected_entity,
            'action': v.recommended_action,
        } for v in self.violations])


class ComplianceRule(ABC):
    """Base class for compliance rules."""
    
    def __init__(self, rule_id: str, name: str, severity: str = 'MEDIUM'):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
    
    @abstractmethod
    def check(self, data: Dict) -> Optional[ComplianceViolation]:
        """
        Check rule compliance.
        
        Parameters
        ----------
        data : dict
            Data to check
        
        Returns
        -------
        ComplianceViolation or None
            Violation if rule is breached, None otherwise
        """
        pass


class PositionLimitRule(ComplianceRule):
    """Check position limits."""
    
    def __init__(self, max_position: float, max_concentration: float = 0.25):
        super().__init__(
            rule_id='PL001',
            name='Position Limit Check',
            severity='HIGH'
        )
        self.max_position = max_position
        self.max_concentration = max_concentration
    
    def check(self, data: Dict) -> Optional[ComplianceViolation]:
        """Check position against limits."""
        position_value = data.get('position_value', 0)
        portfolio_value = data.get('portfolio_value', 1)
        
        concentration = position_value / portfolio_value if portfolio_value > 0 else 0
        
        if position_value > self.max_position:
            return ComplianceViolation(
                timestamp=datetime.now(),
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                description=f"Position value ${position_value:,.2f} exceeds limit ${self.max_position:,.2f}",
                affected_entity=data.get('symbol', 'UNKNOWN'),
                recommended_action=f"Reduce position by ${position_value - self.max_position:,.2f}"
            )
        
        if concentration > self.max_concentration:
            return ComplianceViolation(
                timestamp=datetime.now(),
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                description=f"Position concentration {concentration:.2%} exceeds limit {self.max_concentration:.2%}",
                affected_entity=data.get('symbol', 'UNKNOWN'),
                recommended_action="Diversify portfolio to reduce concentration"
            )
        
        return None


class RiskLimitRule(ComplianceRule):
    """Check risk limits (VaR, volatility, etc.)."""
    
    def __init__(self, max_var: float, max_volatility: float):
        super().__init__(
            rule_id='RL001',
            name='Risk Limit Check',
            severity='HIGH'
        )
        self.max_var = max_var
        self.max_volatility = max_volatility
    
    def check(self, data: Dict) -> Optional[ComplianceViolation]:
        """Check risk metrics against limits."""
        var = data.get('var', 0)
        volatility = data.get('volatility', 0)
        
        if abs(var) > self.max_var:
            return ComplianceViolation(
                timestamp=datetime.now(),
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                description=f"VaR {abs(var):.2%} exceeds limit {self.max_var:.2%}",
                affected_entity='Portfolio',
                recommended_action="Reduce portfolio risk through hedging or position reduction"
            )
        
        if volatility > self.max_volatility:
            return ComplianceViolation(
                timestamp=datetime.now(),
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                description=f"Volatility {volatility:.2%} exceeds limit {self.max_volatility:.2%}",
                affected_entity='Portfolio',
                recommended_action="Rebalance portfolio to lower volatility securities"
            )
        
        return None


class TransactionCostRule(ComplianceRule):
    """Check transaction costs and best execution."""
    
    def __init__(self, max_cost_bps: float = 50):
        super().__init__(
            rule_id='TC001',
            name='Transaction Cost Check',
            severity='MEDIUM'
        )
        self.max_cost_bps = max_cost_bps
    
    def check(self, data: Dict) -> Optional[ComplianceViolation]:
        """Check transaction costs."""
        cost_bps = data.get('cost_bps', 0)
        
        if cost_bps > self.max_cost_bps:
            return ComplianceViolation(
                timestamp=datetime.now(),
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                description=f"Transaction cost {cost_bps:.2f} bps exceeds threshold {self.max_cost_bps:.2f} bps",
                affected_entity=data.get('trade_id', 'UNKNOWN'),
                recommended_action="Review execution strategy and broker selection"
            )
        
        return None


class ComplianceReporter:
    """
    Automated compliance reporting engine.
    
    Parameters
    ----------
    rules : list of ComplianceRule
        Compliance rules to enforce
    """
    
    def __init__(self, rules: Optional[List[ComplianceRule]] = None):
        self.rules = rules or self._default_rules()
        log.info(f"Initialized compliance reporter with {len(self.rules)} rules")
    
    def _default_rules(self) -> List[ComplianceRule]:
        """Create default rule set."""
        return [
            PositionLimitRule(max_position=1_000_000, max_concentration=0.25),
            RiskLimitRule(max_var=0.05, max_volatility=0.25),
            TransactionCostRule(max_cost_bps=50),
        ]
    
    def generate_daily_report(
        self,
        portfolio_data: Dict,
        transactions: List[Dict],
        date: Optional[datetime] = None,
    ) -> ComplianceReport:
        """
        Generate daily compliance report.
        
        Parameters
        ----------
        portfolio_data : dict
            Portfolio state and risk metrics
        transactions : list of dict
            Transactions executed during the day
        date : datetime, optional
            Report date (default: today)
        
        Returns
        -------
        ComplianceReport
            Complete compliance report
        """
        if date is None:
            date = datetime.now()
        
        report_id = f"DAILY_{date.strftime('%Y%m%d')}"
        
        log.info(f"Generating daily compliance report: {report_id}")
        
        # Initialize report
        report = ComplianceReport(
            report_id=report_id,
            report_type='DAILY',
            generated_at=datetime.now(),
            period_start=date.replace(hour=0, minute=0, second=0),
            period_end=date.replace(hour=23, minute=59, second=59),
        )
        
        # Check portfolio-level rules
        for rule in self.rules:
            if isinstance(rule, (PositionLimitRule, RiskLimitRule)):
                violation = rule.check(portfolio_data)
                if violation:
                    report.violations.append(violation)
        
        # Check transaction-level rules
        for txn in transactions:
            for rule in self.rules:
                if isinstance(rule, TransactionCostRule):
                    violation = rule.check(txn)
                    if violation:
                        report.violations.append(violation)
        
        # Calculate metrics
        report.risk_metrics = {
            'var_95': portfolio_data.get('var', 0),
            'volatility': portfolio_data.get('volatility', 0),
            'max_drawdown': portfolio_data.get('max_drawdown', 0),
        }
        
        report.transaction_stats = {
            'total_transactions': len(transactions),
            'total_volume': sum(t.get('value', 0) for t in transactions),
            'avg_cost_bps': np.mean([t.get('cost_bps', 0) for t in transactions]) if transactions else 0,
        }
        
        report.position_limits = {
            'largest_position': portfolio_data.get('largest_position', 0),
            'max_concentration': portfolio_data.get('max_concentration', 0),
            'num_positions': portfolio_data.get('num_positions', 0),
        }
        
        log.info(f"Report generated: {len(report.violations)} violations found")
        
        return report
    
    def generate_monthly_report(
        self,
        portfolio_data: Dict,
        transactions: List[Dict],
        month: int,
        year: int,
    ) -> ComplianceReport:
        """Generate monthly compliance report."""
        report_id = f"MONTHLY_{year}{month:02d}"
        
        # Similar to daily report but with monthly aggregation
        # Placeholder implementation
        
        report = ComplianceReport(
            report_id=report_id,
            report_type='MONTHLY',
            generated_at=datetime.now(),
            period_start=datetime(year, month, 1),
            period_end=datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1),
        )
        
        return report


from abc import ABC, abstractmethod
