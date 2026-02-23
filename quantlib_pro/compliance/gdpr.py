"""
GDPR Compliance Module.

Tools for GDPR (General Data Protection Regulation) compliance:
- Data subject rights (access, rectification, erasure, portability)
- Consent management
- Data retention policies
- Privacy impact assessments
- Data breach notification

Example
-------
>>> gdpr = GDPRManager()
>>> gdpr.record_consent('user123', ['analytics', 'marketing'])
>>> data = gdpr.export_user_data('user123')
>>> gdpr.anonymize_user('user123')
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

import pandas as pd

log = logging.getLogger(__name__)


class ConsentType(Enum):
    """Types of data processing consent."""
    ESSENTIAL = 'essential'  # Required for service operation
    ANALYTICS = 'analytics'  # Performance and usage analytics
    MARKETING = 'marketing'  # Marketing communications
    THIRD_PARTY = 'third_party'  # Third-party data sharing


class DataSubjectRight(Enum):
    """GDPR data subject rights."""
    ACCESS = 'access'  # Right to access personal data
    RECTIFICATION = 'rectification'  # Right to correct inaccurate data
    ERASURE = 'erasure'  # Right to be forgotten
    PORTABILITY = 'portability'  # Right to data portability
    RESTRICTION = 'restriction'  # Right to restrict processing
    OBJECTION = 'objection'  # Right to object to processing


@dataclass
class ConsentRecord:
    """Record of user consent."""
    user_id: str
    consent_types: Set[ConsentType]
    granted_at: datetime
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if consent is still active."""
        if self.expires_at is None:
            return True
        return datetime.now() < self.expires_at
    
    def has_consent(self, consent_type: ConsentType) -> bool:
        """Check if specific consent is granted."""
        return self.is_active() and consent_type in self.consent_types


@dataclass
class DataRetentionPolicy:
    """Data retention policy configuration."""
    data_category: str
    retention_period_days: int
    auto_delete: bool = True
    anonymize_on_expiry: bool = False
    
    def is_expired(self, timestamp: datetime) -> bool:
        """Check if data timestamp exceeded retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_period_days)
        return timestamp < cutoff


@dataclass
class DataSubjectRequest:
    """GDPR data subject request."""
    request_id: str
    user_id: str
    request_type: DataSubjectRight
    requested_at: datetime
    completed_at: Optional[datetime] = None
    status: str = 'PENDING'  # PENDING, IN_PROGRESS, COMPLETED, REJECTED
    notes: str = ''
    
    def complete(self, notes: str = '') -> None:
        """Mark request as completed."""
        self.status = 'COMPLETED'
        self.completed_at = datetime.now()
        self.notes = notes


class GDPRManager:
    """
    GDPR compliance manager.
    
    Handles consent management, data subject rights, retention policies,
    and privacy compliance automation.
    """
    
    def __init__(self):
        self.consents: Dict[str, ConsentRecord] = {}
        self.retention_policies: List[DataRetentionPolicy] = self._default_policies()
        self.requests: Dict[str, DataSubjectRequest] = {}
        
        log.info("Initialized GDPR Manager")
    
    def _default_policies(self) -> List[DataRetentionPolicy]:
        """Create default retention policies."""
        return [
            DataRetentionPolicy('transaction_logs', retention_period_days=2555, auto_delete=False),  # 7 years
            DataRetentionPolicy('user_analytics', retention_period_days=730, auto_delete=True),  # 2 years
            DataRetentionPolicy('session_data', retention_period_days=90, auto_delete=True),  # 3 months
            DataRetentionPolicy('marketing_data', retention_period_days=365, auto_delete=True),  # 1 year
        ]
    
    def record_consent(
        self,
        user_id: str,
        consent_types: List[str],
        duration_days: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentRecord:
        """
        Record user consent.
        
        Parameters
        ----------
        user_id : str
            User identifier
        consent_types : list of str
            Types of consent granted
        duration_days : int, optional
            Consent duration in days (None = indefinite)
        ip_address : str, optional
            User's IP address
        user_agent : str, optional
            User's browser user agent
        
        Returns
        -------
        ConsentRecord
            Record of granted consent
        """
        consent_enums = {ConsentType(ct) for ct in consent_types}
        
        granted_at = datetime.now()
        expires_at = granted_at + timedelta(days=duration_days) if duration_days else None
        
        consent = ConsentRecord(
            user_id=user_id,
            consent_types=consent_enums,
            granted_at=granted_at,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.consents[user_id] = consent
        
        log.info(f"Recorded consent for user {user_id}: {consent_types}")
        
        return consent
    
    def check_consent(self, user_id: str, consent_type: str) -> bool:
        """
        Check if user has granted specific consent.
        
        Parameters
        ----------
        user_id : str
            User identifier
        consent_type : str
            Type of consent to check
        
        Returns
        -------
        bool
            True if consent is active and granted
        """
        if user_id not in self.consents:
            return False
        
        consent = self.consents[user_id]
        consent_enum = ConsentType(consent_type)
        
        return consent.has_consent(consent_enum)
    
    def revoke_consent(self, user_id: str, consent_types: Optional[List[str]] = None) -> None:
        """
        Revoke user consent.
        
        Parameters
        ----------
        user_id : str
            User identifier
        consent_types : list of str, optional
            Specific types to revoke (None = revoke all)
        """
        if user_id not in self.consents:
            log.warning(f"No consent record found for user {user_id}")
            return
        
        if consent_types is None:
            # Revoke all
            del self.consents[user_id]
            log.info(f"Revoked all consents for user {user_id}")
        else:
            # Revoke specific types
            consent = self.consents[user_id]
            for ct in consent_types:
                consent_enum = ConsentType(ct)
                consent.consent_types.discard(consent_enum)
            
            log.info(f"Revoked consents {consent_types} for user {user_id}")
    
    def export_user_data(self, user_id: str) -> Dict:
        """
        Export all user data (data portability right).
        
        Parameters
        ----------
        user_id : str
            User identifier
        
        Returns
        -------
        dict
            All user data in structured format
        """
        log.info(f"Exporting data for user {user_id}")
        
        # In production, would query all data stores
        data = {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'consent_record': self._export_consent(user_id),
            'requests': self._export_requests(user_id),
            # Add other data categories as needed
        }
        
        return data
    
    def _export_consent(self, user_id: str) -> Optional[Dict]:
        """Export user's consent record."""
        if user_id not in self.consents:
            return None
        
        consent = self.consents[user_id]
        return {
            'granted_at': consent.granted_at.isoformat(),
            'expires_at': consent.expires_at.isoformat() if consent.expires_at else None,
            'consent_types': [ct.value for ct in consent.consent_types],
            'is_active': consent.is_active(),
        }
    
    def _export_requests(self, user_id: str) -> List[Dict]:
        """Export user's GDPR requests."""
        user_requests = [
            r for r in self.requests.values()
            if r.user_id == user_id
        ]
        
        return [{
            'request_id': r.request_id,
            'type': r.request_type.value,
            'requested_at': r.requested_at.isoformat(),
            'status': r.status,
            'completed_at': r.completed_at.isoformat() if r.completed_at else None,
        } for r in user_requests]
    
    def anonymize_user(self, user_id: str) -> None:
        """
        Anonymize user data (right to erasure).
        
        Replaces personal identifiers with hashed values.
        """
        log.info(f"Anonymizing data for user {user_id}")
        
        # Generate anonymous ID
        anon_id = self._hash_user_id(user_id)
        
        # Remove consent records
        if user_id in self.consents:
            del self.consents[user_id]
        
        # Anonymize requests
        for request in self.requests.values():
            if request.user_id == user_id:
                request.user_id = anon_id
        
        log.info(f"User {user_id} anonymized to {anon_id}")
    
    def _hash_user_id(self, user_id: str) -> str:
        """Generate anonymized user ID."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def delete_user_data(self, user_id: str) -> None:
        """
        Permanently delete user data (right to erasure).
        
        WARNING: This is irreversible.
        """
        log.warning(f"PERMANENTLY DELETING data for user {user_id}")
        
        # Remove consent records
        if user_id in self.consents:
            del self.consents[user_id]
        
        # Remove requests
        request_ids_to_delete = [
            rid for rid, r in self.requests.items()
            if r.user_id == user_id
        ]
        for rid in request_ids_to_delete:
            del self.requests[rid]
        
        # In production, would cascade delete across all data stores
        
        log.warning(f"User {user_id} data permanently deleted")
    
    def submit_request(
        self,
        user_id: str,
        request_type: str,
    ) -> DataSubjectRequest:
        """
        Submit data subject request.
        
        Parameters
        ----------
        user_id : str
            User identifier
        request_type : str
            Type of request (access, erasure, etc.)
        
        Returns
        -------
        DataSubjectRequest
            Request record
        """
        request_id = f"{request_type}_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        request = DataSubjectRequest(
            request_id=request_id,
            user_id=user_id,
            request_type=DataSubjectRight(request_type),
            requested_at=datetime.now(),
        )
        
        self.requests[request_id] = request
        
        log.info(f"Submitted {request_type} request for user {user_id}: {request_id}")
        
        return request
    
    def process_request(self, request_id: str) -> None:
        """
        Process data subject request.
        
        Parameters
        ----------
        request_id : str
            Request identifier
        """
        if request_id not in self.requests:
            raise ValueError(f"Request not found: {request_id}")
        
        request = self.requests[request_id]
        request.status = 'IN_PROGRESS'
        
        log.info(f"Processing request {request_id}")
        
        # Execute request based on type
        if request.request_type == DataSubjectRight.ACCESS:
            data = self.export_user_data(request.user_id)
            request.complete(f"Data exported: {len(data)} categories")
        
        elif request.request_type == DataSubjectRight.ERASURE:
            self.delete_user_data(request.user_id)
            request.complete("User data permanently deleted")
        
        elif request.request_type == DataSubjectRight.PORTABILITY:
            data = self.export_user_data(request.user_id)
            request.complete(f"Data package created: {len(data)} categories")
        
        else:
            request.complete(f"Request type {request.request_type.value} processed")
        
        log.info(f"Request {request_id} completed")
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired data according to retention policies.
        
        Returns
        -------
        dict
            Counts of deleted/anonymized records by category
        """
        log.info("Running data retention cleanup")
        
        results = {}
        
        # In production, would scan all data stores and apply policies
        # This is a simplified example
        
        # Clean up expired consents
        expired_consents = [
            uid for uid, consent in self.consents.items()
            if not consent.is_active()
        ]
        
        for uid in expired_consents:
            del self.consents[uid]
        
        results['expired_consents'] = len(expired_consents)
        
        log.info(f"Cleanup complete: {results}")
        
        return results
    
    def generate_privacy_report(self) -> pd.DataFrame:
        """
        Generate privacy compliance report.
        
        Returns
        -------
        pd.DataFrame
            Summary of privacy compliance metrics
        """
        total_users = len(self.consents)
        active_consents = sum(1 for c in self.consents.values() if c.is_active())
        
        consent_breakdown = {ct: 0 for ct in ConsentType}
        for consent in self.consents.values():
            for ct in consent.consent_types:
                consent_breakdown[ct] += 1
        
        pending_requests = sum(1 for r in self.requests.values() if r.status == 'PENDING')
        completed_requests = sum(1 for r in self.requests.values() if r.status == 'COMPLETED')
        
        data = {
            'Metric': [
                'Total Users',
                'Active Consents',
                'Essential Consent',
                'Analytics Consent',
                'Marketing Consent',
                'Third Party Consent',
                'Pending Requests',
                'Completed Requests',
            ],
            'Value': [
                total_users,
                active_consents,
                consent_breakdown[ConsentType.ESSENTIAL],
                consent_breakdown[ConsentType.ANALYTICS],
                consent_breakdown[ConsentType.MARKETING],
                consent_breakdown[ConsentType.THIRD_PARTY],
                pending_requests,
                completed_requests,
            ]
        }
        
        return pd.DataFrame(data)
