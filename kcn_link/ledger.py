"""Append-only-by-interface, hash-chained local evidence ledger.

Security boundary: SHA-256 detects byte/record changes relative to the chain; it
does not prove authorship, human authorization, truth, or external immutability.
The file remains subject to the permissions and trust of its host environment.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


GENESIS_HASH = "0" * 64


class EventType(str, Enum):
    SENT = "SENT"
    RECEIVED = "RECEIVED"
    VERIFIED = "VERIFIED"
    ABORTED = "ABORTED"
    REVOKED = "REVOKED"
    DISPUTED = "DISPUTED"
    PROMOTED = "PROMOTED"
    DENIED = "DENIED"
    FLAGGED = "FLAGGED"


class EvidenceStatus(str, Enum):
    PROPOSED = "PROPOSED"
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"
    NOT_MEASURED = "NOT_MEASURED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


class LedgerIntegrityError(RuntimeError):
    """Raised when the existing ledger cannot safely accept another event."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceEvent:
    event_id: str
    event_type: str
    occurred_at: str
    actor: str
    subject: str
    status: str
    payload: Mapping[str, Any]
    authorization_ref: str | None
    previous_hash: str
    event_hash: str

    def hash_material(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("event_hash")
        return data


@dataclass(frozen=True)
class LedgerVerification:
    status: str
    event_count: int
    head_hash: str
    error: str | None = None

    @property
    def valid(self) -> bool:
        return self.status in ("PASSED", "NOT_MEASURED")


class EvidenceLedger:
    """Local JSONL ledger that verifies the prior chain before every append.

    There is intentionally no update/delete API. This is not a substitute for
    external access controls, signed checkpoints, replicated storage, or review.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _read_records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    raise LedgerIntegrityError(f"blank line at record {line_number}")
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LedgerIntegrityError(
                        f"invalid JSON at record {line_number}"
                    ) from exc
                if not isinstance(value, dict):
                    raise LedgerIntegrityError(f"record {line_number} is not an object")
                records.append(value)
        return records

    def verify(self) -> LedgerVerification:
        try:
            records = self._read_records()
            previous_hash = GENESIS_HASH
            seen_ids: set[str] = set()
            for index, record in enumerate(records, start=1):
                required = {
                    "event_id", "event_type", "occurred_at", "actor", "subject",
                    "status", "payload", "authorization_ref", "previous_hash",
                    "event_hash",
                }
                if set(record) != required:
                    return LedgerVerification(
                        "FAILED", len(records), previous_hash,
                        f"record {index} has missing or unexpected fields",
                    )
                if not isinstance(record["event_id"], str) or not record["event_id"]:
                    return LedgerVerification("FAILED", len(records), previous_hash,
                                              f"record {index} has invalid event_id")
                if record["event_id"] in seen_ids:
                    return LedgerVerification("FAILED", len(records), previous_hash,
                                              f"duplicate event_id at record {index}")
                seen_ids.add(record["event_id"])
                if record["previous_hash"] != previous_hash:
                    return LedgerVerification("FAILED", len(records), previous_hash,
                                              f"previous_hash mismatch at record {index}")
                material = dict(record)
                actual_hash = material.pop("event_hash")
                expected_hash = _sha256(_canonical_json(material))
                if actual_hash != expected_hash:
                    return LedgerVerification("FAILED", len(records), previous_hash,
                                              f"event_hash mismatch at record {index}")
                previous_hash = actual_hash
            if not records:
                return LedgerVerification("NOT_MEASURED", 0, GENESIS_HASH)
            return LedgerVerification("PASSED", len(records), previous_hash)
        except (OSError, LedgerIntegrityError) as exc:
            return LedgerVerification("FAILED", 0, GENESIS_HASH, str(exc))

    def append(
        self,
        *,
        event_type: EventType,
        actor: str,
        subject: str,
        status: EvidenceStatus,
        payload: Mapping[str, Any] | None = None,
        authorization_ref: str | None = None,
        event_id: str | None = None,
        occurred_at: str | None = None,
    ) -> EvidenceEvent:
        """Append one event after validating the current chain.

        authorization_ref is provenance only; this class does not validate it
        and does not treat it as permission to perform any operation.
        """
        if not actor.strip() or not subject.strip():
            raise ValueError("actor and subject are required")
        if event_id is None:
            # UUID is not an authority token; it only provides event identity.
            import uuid
            event_id = str(uuid.uuid4())
        if not event_id.strip():
            raise ValueError("event_id is required")
        if occurred_at is None:
            occurred_at = datetime.now(timezone.utc).isoformat()
        try:
            parsed = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("occurred_at must be an ISO-8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")

        report = self.verify()
        if report.status == "FAILED":
            raise LedgerIntegrityError(
                f"refusing append because ledger verification failed: {report.error}"
            )
        if event_id in {r["event_id"] for r in self._read_records()}:
            raise LedgerIntegrityError(f"duplicate event_id: {event_id}")

        material = {
            "event_id": event_id,
            "event_type": EventType(event_type).value,
            "occurred_at": occurred_at,
            "actor": actor,
            "subject": subject,
            "status": EvidenceStatus(status).value,
            "payload": dict(payload or {}),
            "authorization_ref": authorization_ref,
            "previous_hash": report.head_hash,
        }
        event_hash = _sha256(_canonical_json(material))
        event = EvidenceEvent(**material, event_hash=event_hash)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = _canonical_json(asdict(event)) + "\n"
        # O_APPEND prevents this process from replacing prior bytes; it does not
        # provide cross-process locking or protect against a privileged host user.
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            # fdopen owns the descriptor after successful construction.
            raise
        return event
