"""
Audit Trail Management Module.

Comprehensive audit logging for compliance and security:
- User action tracking
- Data access logging
- System event recording
- Tamper-proof log storage
- Audit trail reporting

Example
-------
>>> audit = AuditTrail()
>>> audit.log_event('user123', 'LOGIN', {'ip': '192.168.1.1'})
>>> audit.log_data_access('user123', 'portfolio_data', 'READ')
>>> report = audit.generate_audit_report('2024-01-01', '2024-01-31')
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

log = logging.getLogger(__name__)


class EventType(Enum):
    """Types of audit events."""
    LOGIN = 'login'
    LOGOUT = 'logout'
    DATA_ACCESS = 'data_access'
    DATA_MODIFICATION = 'data_modification'
    TRADE_EXECUTION = 'trade_execution'
    PORTFOLIO_UPDATE = 'portfolio_update'
    CONFIG_CHANGE = 'config_change'
    SECURITY_EVENT = 'security_event'
    SYSTEM_ERROR = 'system_error'


class Severity(Enum):
    """Event severity levels."""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


@dataclass
class AuditEvent:
    """Audit trail event record."""
    event_id: str
    timestamp: datetime
    user_id: str
    event_type: EventType
    severity: Severity
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    integrity_hash: Optional[str] = None
    
    def __post_init__(self):
        """Calculate integrity hash after initialization."""
        if self.integrity_hash is None:
            self.integrity_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash for tamper detection."""
        data = f"{self.event_id}{self.timestamp}{self.user_id}{self.event_type.value}{self.description}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify event integrity."""
        return self.integrity_hash == self._calculate_hash()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'metadata': self.metadata,
            'integrity_hash': self.integrity_hash,
        }


class AuditTrail:
    """
    Audit trail management system.
    
    Provides comprehensive logging and reporting for compliance.
    Events are tamper-resistant through integrity hashing.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.events: List[AuditEvent] = []
        self.storage_path = storage_path
        self.event_counter = 0
        
        log.info("Initialized Audit Trail")
    
    def log_event(
        self,
        user_id: str,
        event_type: str,
        description: str,
        severity: str = 'info',
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Parameters
        ----------
        user_id : str
            User who triggered the event
        event_type : str
            Type of event
        description : str
            Event description
        severity : str
            Event severity level
        metadata : dict, optional
            Additional event data
        
        Returns
        -------
        AuditEvent
            Created event record
        """
        self.event_counter += 1
        event_id = f"AE{self.event_counter:08d}"
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            user_id=user_id,
            event_type=EventType(event_type),
            severity=Severity(severity),
            description=description,
            metadata=metadata or {},
        )
        
        self.events.append(event)
        
        log.info(f"Logged audit event: {event_id} [{event_type}] {description}")
        
        # Persist to storage if configured
        if self.storage_path:
            self._persist_event(event)
        
        return event
    
    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """
        Log data access event.
        
        Parameters
        ----------
        user_id : str
            User accessing data
        resource : str
            Resource being accessed
        action : str
            Action performed (READ, WRITE, DELETE)
        metadata : dict, optional
            Additional context
        
        Returns
        -------
        AuditEvent
            Created event record
        """
        description = f"Data access: {action} on {resource}"
        
        event_metadata = {
            'resource': resource,
            'action': action,
            **(metadata or {})
        }
        
        return self.log_event(
            user_id=user_id,
            event_type='data_access',
            description=description,
            severity='info',
            metadata=event_metadata,
        )
    
    def log_trade(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """
        Log trade execution.
        
        Parameters
        ----------
        user_id : str
            User executing trade
        symbol : str
            Trading symbol
        side : str
            Trade side (BUY/SELL)
        quantity : float
            Trade quantity
        price : float
            Execution price
        metadata : dict, optional
            Additional trade data
        
        Returns
        -------
        AuditEvent
            Created event record
        """
        description = f"Trade executed: {side} {quantity} {symbol} @ ${price}"
        
        event_metadata = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'value': quantity * price,
            **(metadata or {})
        }
        
        return self.log_event(
            user_id=user_id,
            event_type='trade_execution',
            description=description,
            severity='info',
            metadata=event_metadata,
        )
    
    def log_security_event(
        self,
        user_id: str,
        description: str,
        severity: str = 'warning',
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """
        Log security-related event.
        
        Parameters
        ----------
        user_id : str
            User involved in event
        description : str
            Event description
        severity : str
            Event severity
        metadata : dict, optional
            Additional context
        
        Returns
        -------
        AuditEvent
            Created event record
        """
        return self.log_event(
            user_id=user_id,
            event_type='security_event',
            description=description,
            severity=severity,
            metadata=metadata,
        )
    
    def query_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.
        
        Parameters
        ----------
        start_date : datetime, optional
            Filter events after this date
        end_date : datetime, optional
            Filter events before this date
        user_id : str, optional
            Filter by user ID
        event_type : str, optional
            Filter by event type
        severity : str, optional
            Filter by severity
        
        Returns
        -------
        list of AuditEvent
            Matching events
        """
        results = self.events
        
        if start_date:
            results = [e for e in results if e.timestamp >= start_date]
        
        if end_date:
            results = [e for e in results if e.timestamp <= end_date]
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        
        if event_type:
            event_type_enum = EventType(event_type)
            results = [e for e in results if e.event_type == event_type_enum]
        
        if severity:
            severity_enum = Severity(severity)
            results = [e for e in results if e.severity == severity_enum]
        
        return results
    
    def generate_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Generate audit report for date range.
        
        Parameters
        ----------
        start_date : datetime
            Report start date
        end_date : datetime
            Report end date
        user_id : str, optional
            Filter by user ID
        
        Returns
        -------
        pd.DataFrame
            Audit report
        """
        events = self.query_events(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
        )
        
        if not events:
            return pd.DataFrame()
        
        data = []
        for event in events:
            data.append({
                'Event ID': event.event_id,
                'Timestamp': event.timestamp,
                'User ID': event.user_id,
                'Event Type': event.event_type.value,
                'Severity': event.severity.value,
                'Description': event.description,
                'Integrity OK': event.verify_integrity(),
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('Timestamp')
        
        return df
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify integrity of all audit events.
        
        Returns
        -------
        dict
            Integrity verification results
        """
        total_events = len(self.events)
        verified = sum(1 for e in self.events if e.verify_integrity())
        tampered = total_events - verified
        
        results = {
            'total_events': total_events,
            'verified': verified,
            'tampered': tampered,
            'integrity_rate': verified / total_events if total_events > 0 else 1.0,
        }
        
        if tampered > 0:
            tampered_events = [e for e in self.events if not e.verify_integrity()]
            results['tampered_event_ids'] = [e.event_id for e in tampered_events]
            log.error(f"Integrity check FAILED: {tampered} tampered events detected")
        else:
            log.info("Integrity check PASSED: All events verified")
        
        return results
    
    def get_statistics(self) -> pd.DataFrame:
        """
        Get audit trail statistics.
        
        Returns
        -------
        pd.DataFrame
            Event statistics by type and severity
        """
        if not self.events:
            return pd.DataFrame()
        
        # Count by event type
        type_counts = {}
        for event_type in EventType:
            type_counts[event_type.value] = sum(
                1 for e in self.events if e.event_type == event_type
            )
        
        # Count by severity
        severity_counts = {}
        for severity in Severity:
            severity_counts[severity.value] = sum(
                1 for e in self.events if e.severity == severity
            )
        
        # Count by user
        user_counts = {}
        for event in self.events:
            user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
        
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        data = {
            'Category': ['Total Events'] + 
                       [f'Type: {t}' for t in type_counts.keys()] +
                       [f'Severity: {s}' for s in severity_counts.keys()] +
                       [f'User: {u}' for u, _ in top_users],
            'Count': [len(self.events)] +
                    list(type_counts.values()) +
                    list(severity_counts.values()) +
                    [c for _, c in top_users],
        }
        
        return pd.DataFrame(data)
    
    def _persist_event(self, event: AuditEvent) -> None:
        """Persist event to storage (placeholder)."""
        # In production, would write to secure append-only storage
        # (blockchain, immutable database, etc.)
        pass
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export audit trail to JSON file.
        
        Parameters
        ----------
        filepath : str
            Output file path
        """
        data = [event.to_dict() for event in self.events]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        log.info(f"Exported {len(self.events)} events to {filepath}")
    
    def import_from_json(self, filepath: str) -> int:
        """
        Import audit trail from JSON file.
        
        Parameters
        ----------
        filepath : str
            Input file path
        
        Returns
        -------
        int
            Number of events imported
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        imported = 0
        for event_dict in data:
            event = AuditEvent(
                event_id=event_dict['event_id'],
                timestamp=datetime.fromisoformat(event_dict['timestamp']),
                user_id=event_dict['user_id'],
                event_type=EventType(event_dict['event_type']),
                severity=Severity(event_dict['severity']),
                description=event_dict['description'],
                metadata=event_dict['metadata'],
                integrity_hash=event_dict['integrity_hash'],
            )
            
            self.events.append(event)
            imported += 1
        
        log.info(f"Imported {imported} events from {filepath}")
        
        return imported
