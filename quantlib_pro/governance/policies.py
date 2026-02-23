"""
Governance Policies Module.

Policy-based governance framework for risk management:
- Risk limit policies
- Trading restrictions
- Approval workflows
- Policy enforcement engine
- Compliance monitoring

Example
-------
>>> policy_engine = PolicyEngine()
>>> policy = RiskLimitPolicy(max_var=0.05, max_leverage=2.0)
>>> policy_engine.add_policy(policy)
>>> result = policy_engine.evaluate_trade(trade_data)
>>> if not result.approved:
...     print(f"Trade rejected: {result.rejection_reason}")
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

log = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of governance policies."""
    RISK_LIMIT = 'risk_limit'
    POSITION_LIMIT = 'position_limit'
    CONCENTRATION_LIMIT = 'concentration_limit'
    LEVERAGE_LIMIT = 'leverage_limit'
    TRADING_RESTRICTION = 'trading_restriction'
    COUNTERPARTY_LIMIT = 'counterparty_limit'


class ApprovalStatus(Enum):
    """Approval workflow statuses."""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    ESCALATED = 'escalated'


@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation."""
    policy_id: str
    policy_name: str
    approved: bool
    rejection_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        status = "APPROVED" if self.approved else "REJECTED"
        output = f"[{status}] {self.policy_name} ({self.policy_id})"
        
        if self.rejection_reason:
            output += f"\n  Reason: {self.rejection_reason}"
        
        if self.warnings:
            output += f"\n  Warnings: {', '.join(self.warnings)}"
        
        return output


class Policy(ABC):
    """Base class for governance policies."""
    
    def __init__(
        self,
        policy_id: str,
        name: str,
        policy_type: PolicyType,
        enabled: bool = True,
    ):
        self.policy_id = policy_id
        self.name = name
        self.policy_type = policy_type
        self.enabled = enabled
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
    
    @abstractmethod
    def evaluate(self, data: Dict) -> PolicyEvaluationResult:
        """
        Evaluate data against policy.
        
        Parameters
        ----------
        data : dict
            Data to evaluate
        
        Returns
        -------
        PolicyEvaluationResult
            Evaluation result
        """
        pass
    
    def update(self) -> None:
        """Update last modified timestamp."""
        self.last_modified = datetime.now()


class RiskLimitPolicy(Policy):
    """Risk limit governance policy."""
    
    def __init__(
        self,
        max_var: float = 0.05,
        max_volatility: float = 0.30,
        max_drawdown: float = 0.20,
        max_leverage: float = 2.0,
    ):
        super().__init__(
            policy_id='POL_RISK_001',
            name='Risk Limit Policy',
            policy_type=PolicyType.RISK_LIMIT,
        )
        self.max_var = max_var
        self.max_volatility = max_volatility
        self.max_drawdown = max_drawdown
        self.max_leverage = max_leverage
    
    def evaluate(self, data: Dict) -> PolicyEvaluationResult:
        """Evaluate risk metrics against limits."""
        warnings = []
        
        # VaR check
        var = abs(data.get('var', 0))
        if var > self.max_var:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"VaR {var:.2%} exceeds limit {self.max_var:.2%}",
            )
        elif var > self.max_var * 0.9:
            warnings.append(f"VaR approaching limit ({var:.2%} of {self.max_var:.2%})")
        
        # Volatility check
        volatility = data.get('volatility', 0)
        if volatility > self.max_volatility:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"Volatility {volatility:.2%} exceeds limit {self.max_volatility:.2%}",
            )
        elif volatility > self.max_volatility * 0.9:
            warnings.append(f"Volatility approaching limit ({volatility:.2%} of {self.max_volatility:.2%})")
        
        # Drawdown check
        drawdown = abs(data.get('max_drawdown', 0))
        if drawdown > self.max_drawdown:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"Drawdown {drawdown:.2%} exceeds limit {self.max_drawdown:.2%}",
            )
        
        # Leverage check
        leverage = data.get('leverage', 1.0)
        if leverage > self.max_leverage:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"Leverage {leverage:.2f}x exceeds limit {self.max_leverage:.2f}x",
            )
        
        return PolicyEvaluationResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            approved=True,
            warnings=warnings,
        )


class PositionLimitPolicy(Policy):
    """Position size limit policy."""
    
    def __init__(
        self,
        max_position_value: float = 1_000_000,
        max_concentration: float = 0.25,
        max_sector_concentration: float = 0.40,
    ):
        super().__init__(
            policy_id='POL_POS_001',
            name='Position Limit Policy',
            policy_type=PolicyType.POSITION_LIMIT,
        )
        self.max_position_value = max_position_value
        self.max_concentration = max_concentration
        self.max_sector_concentration = max_sector_concentration
    
    def evaluate(self, data: Dict) -> PolicyEvaluationResult:
        """Evaluate position against limits."""
        warnings = []
        
        # Position value check
        position_value = abs(data.get('position_value', 0))
        if position_value > self.max_position_value:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"Position value ${position_value:,.0f} exceeds limit ${self.max_position_value:,.0f}",
            )
        
        # Concentration check
        portfolio_value = data.get('portfolio_value', 1)
        concentration = position_value / portfolio_value if portfolio_value > 0 else 0
        
        if concentration > self.max_concentration:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"Concentration {concentration:.2%} exceeds limit {self.max_concentration:.2%}",
            )
        elif concentration > self.max_concentration * 0.9:
            warnings.append(f"Concentration approaching limit ({concentration:.2%})")
        
        # Sector concentration check
        sector_concentration = data.get('sector_concentration', 0)
        if sector_concentration > self.max_sector_concentration:
            warnings.append(f"Sector concentration {sector_concentration:.2%} exceeds recommended limit {self.max_sector_concentration:.2%}")
        
        return PolicyEvaluationResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            approved=True,
            warnings=warnings,
        )


class TradingRestrictionPolicy(Policy):
    """Trading restriction policy (blacklist, time windows)."""
    
    def __init__(
        self,
        blacklisted_symbols: Optional[List[str]] = None,
        restricted_hours: Optional[List[int]] = None,
        min_trade_value: float = 1000,
    ):
        super().__init__(
            policy_id='POL_TRD_001',
            name='Trading Restriction Policy',
            policy_type=PolicyType.TRADING_RESTRICTION,
        )
        self.blacklisted_symbols = set(blacklisted_symbols or [])
        self.restricted_hours = set(restricted_hours or [])  # Hours when trading is restricted
        self.min_trade_value = min_trade_value
    
    def evaluate(self, data: Dict) -> PolicyEvaluationResult:
        """Evaluate trade against restrictions."""
        warnings = []
        
        # Symbol blacklist check
        symbol = data.get('symbol', '')
        if symbol in self.blacklisted_symbols:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"Symbol {symbol} is blacklisted",
            )
        
        # Trading hours check
        current_hour = datetime.now().hour
        if current_hour in self.restricted_hours:
            warnings.append(f"Trading during restricted hours ({current_hour}:00)")
        
        # Minimum trade value check
        trade_value = abs(data.get('trade_value', 0))
        if trade_value < self.min_trade_value:
            return PolicyEvaluationResult(
                policy_id=self.policy_id,
                policy_name=self.name,
                approved=False,
                rejection_reason=f"Trade value ${trade_value:,.0f} below minimum ${self.min_trade_value:,.0f}",
            )
        
        return PolicyEvaluationResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            approved=True,
            warnings=warnings,
        )


@dataclass
class ApprovalRequest:
    """Approval workflow request."""
    request_id: str
    requestor: str
    request_type: str
    description: str
    data: Dict
    submitted_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: str = ''
    
    def approve(self, approver: str, notes: str = '') -> None:
        """Approve the request."""
        self.status = ApprovalStatus.APPROVED
        self.approver = approver
        self.approved_at = datetime.now()
        self.notes = notes
    
    def reject(self, approver: str, notes: str) -> None:
        """Reject the request."""
        self.status = ApprovalStatus.REJECTED
        self.approver = approver
        self.approved_at = datetime.now()
        self.notes = notes
    
    def escalate(self, notes: str = '') -> None:
        """Escalate to higher authority."""
        self.status = ApprovalStatus.ESCALATED
        self.notes = notes


class ApprovalWorkflow:
    """Approval workflow management."""
    
    def __init__(self):
        self.requests: Dict[str, ApprovalRequest] = {}
        self.request_counter = 0
        log.info("Initialized Approval Workflow")
    
    def submit_request(
        self,
        requestor: str,
        request_type: str,
        description: str,
        data: Dict,
    ) -> ApprovalRequest:
        """
        Submit approval request.
        
        Parameters
        ----------
        requestor : str
            User submitting request
        request_type : str
            Type of request
        description : str
            Request description
        data : dict
            Request data
        
        Returns
        -------
        ApprovalRequest
            Created request
        """
        self.request_counter += 1
        request_id = f"APR{self.request_counter:06d}"
        
        request = ApprovalRequest(
            request_id=request_id,
            requestor=requestor,
            request_type=request_type,
            description=description,
            data=data,
            submitted_at=datetime.now(),
        )
        
        self.requests[request_id] = request
        
        log.info(f"Approval request submitted: {request_id} by {requestor}")
        
        return request
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending requests."""
        return [
            r for r in self.requests.values()
            if r.status == ApprovalStatus.PENDING
        ]
    
    def process_request(
        self,
        request_id: str,
        approver: str,
        action: str,
        notes: str = '',
    ) -> ApprovalRequest:
        """
        Process approval request.
        
        Parameters
        ----------
        request_id : str
            Request identifier
        approver : str
            User processing request
        action : str
            Action to take ('approve', 'reject', 'escalate')
        notes : str
            Approval notes
        
        Returns
        -------
        ApprovalRequest
            Updated request
        """
        if request_id not in self.requests:
            raise ValueError(f"Request not found: {request_id}")
        
        request = self.requests[request_id]
        
        if action == 'approve':
            request.approve(approver, notes)
            log.info(f"Request {request_id} approved by {approver}")
        elif action == 'reject':
            request.reject(approver, notes)
            log.info(f"Request {request_id} rejected by {approver}")
        elif action == 'escalate':
            request.escalate(notes)
            log.info(f"Request {request_id} escalated")
        else:
            raise ValueError(f"Invalid action: {action}")
        
        return request


class PolicyEngine:
    """
    Policy enforcement engine.
    
    Evaluates actions against governance policies and manages
    approval workflows.
    """
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.workflow = ApprovalWorkflow()
        self.evaluation_history: List[Dict] = []
        
        log.info("Initialized Policy Engine")
    
    def add_policy(self, policy: Policy) -> None:
        """Add policy to engine."""
        self.policies[policy.policy_id] = policy
        log.info(f"Added policy: {policy.name} ({policy.policy_id})")
    
    def remove_policy(self, policy_id: str) -> None:
        """Remove policy from engine."""
        if policy_id in self.policies:
            del self.policies[policy_id]
            log.info(f"Removed policy: {policy_id}")
    
    def evaluate_trade(self, trade_data: Dict) -> PolicyEvaluationResult:
        """
        Evaluate trade against all applicable policies.
        
        Parameters
        ----------
        trade_data : dict
            Trade data to evaluate
        
        Returns
        -------
        PolicyEvaluationResult
            Combined evaluation result
        """
        all_warnings = []
        
        for policy in self.policies.values():
            if not policy.enabled:
                continue
            
            result = policy.evaluate(trade_data)
            
            if not result.approved:
                # Record evaluation
                self.evaluation_history.append({
                    'timestamp': datetime.now(),
                    'policy_id': policy.policy_id,
                    'approved': False,
                    'reason': result.rejection_reason,
                })
                
                return result
            
            all_warnings.extend(result.warnings)
        
        # All policies passed
        combined_result = PolicyEvaluationResult(
            policy_id='COMBINED',
            policy_name='All Policies',
            approved=True,
            warnings=all_warnings,
        )
        
        # Record evaluation
        self.evaluation_history.append({
            'timestamp': datetime.now(),
            'policy_id': 'COMBINED',
            'approved': True,
            'warnings': len(all_warnings),
        })
        
        return combined_result
    
    def get_policy_report(self) -> pd.DataFrame:
        """
        Generate policy compliance report.
        
        Returns
        -------
        pd.DataFrame
            Policy statistics
        """
        data = []
        
        for policy in self.policies.values():
            data.append({
                'Policy ID': policy.policy_id,
                'Name': policy.name,
                'Type': policy.policy_type.value,
                'Enabled': policy.enabled,
                'Created': policy.created_at,
                'Last Modified': policy.last_modified,
            })
        
        return pd.DataFrame(data)
