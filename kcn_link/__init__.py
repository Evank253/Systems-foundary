"""KCN Link: evidence-preserving interoperability primitives.

This package records evidence events. It does not confer authority, authorize
operations, or execute connected systems.
"""
from .ledger import EvidenceEvent, EvidenceLedger, EventType, EvidenceStatus, LedgerIntegrityError

__all__ = [
    "EvidenceEvent",
    "EvidenceLedger",
    "EventType",
    "EvidenceStatus",
    "LedgerIntegrityError",
]
