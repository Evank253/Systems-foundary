import json
import tempfile
import unittest
from pathlib import Path

from kcn_link import (
    EvidenceLedger,
    EvidenceStatus,
    EventType,
    LedgerIntegrityError,
)


class EvidenceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name) / "evidence.jsonl"
        self.ledger = EvidenceLedger(self.path)

    def test_empty_ledger_is_not_measured_not_passed(self):
        report = self.ledger.verify()
        self.assertEqual(report.status, "NOT_MEASURED")
        self.assertTrue(report.valid)
        self.assertEqual(report.event_count, 0)

    def test_append_creates_hash_chained_events(self):
        first = self.ledger.append(
            event_type=EventType.SENT,
            actor="test-adapter",
            subject="system-a",
            status=EvidenceStatus.OBSERVED,
            payload={"bytes": 12},
            event_id="event-1",
        )
        second = self.ledger.append(
            event_type=EventType.RECEIVED,
            actor="test-adapter",
            subject="system-b",
            status=EvidenceStatus.NOT_MEASURED,
            payload={"transport_check": "NOT_MEASURED"},
            event_id="event-2",
        )
        report = self.ledger.verify()
        self.assertEqual(report.status, "PASSED")
        self.assertEqual(report.event_count, 2)
        self.assertEqual(second.previous_hash, first.event_hash)
        self.assertEqual(report.head_hash, second.event_hash)
        self.assertEqual(len(report.head_hash), 64)

    def test_authorization_reference_is_recorded_not_validated(self):
        event = self.ledger.append(
            event_type=EventType.VERIFIED,
            actor="verifier-placeholder",
            subject="artifact-1",
            status=EvidenceStatus.NOT_MEASURED,
            authorization_ref="human-record-ref",
            event_id="event-auth",
        )
        self.assertEqual(event.authorization_ref, "human-record-ref")
        self.assertEqual(self.ledger.verify().status, "PASSED")

    def test_modified_payload_breaks_chain_and_blocks_append(self):
        self.ledger.append(
            event_type=EventType.RECEIVED,
            actor="adapter",
            subject="artifact",
            status=EvidenceStatus.OBSERVED,
            payload={"result": "original"},
            event_id="event-tamper",
        )
        record = json.loads(self.path.read_text(encoding="utf-8"))
        record["payload"]["result"] = "changed"
        self.path.write_text(json.dumps(record) + "\n", encoding="utf-8")

        report = self.ledger.verify()
        self.assertEqual(report.status, "FAILED")
        self.assertIn("event_hash mismatch", report.error)
        with self.assertRaisesRegex(LedgerIntegrityError, "verification failed"):
            self.ledger.append(
                event_type=EventType.FLAGGED,
                actor="adapter",
                subject="artifact",
                status=EvidenceStatus.FAILED,
                event_id="event-after-tamper",
            )

    def test_duplicate_event_id_is_rejected(self):
        args = dict(
            event_type=EventType.DENIED,
            actor="policy-check",
            subject="operation-1",
            status=EvidenceStatus.BLOCKED,
            event_id="same-id",
        )
        self.ledger.append(**args)
        with self.assertRaisesRegex(LedgerIntegrityError, "duplicate event_id"):
            self.ledger.append(**args)

    def test_timezone_is_required(self):
        with self.assertRaisesRegex(ValueError, "include a timezone"):
            self.ledger.append(
                event_type=EventType.FLAGGED,
                actor="test",
                subject="artifact",
                status=EvidenceStatus.NOT_MEASURED,
                occurred_at="2026-10-19T09:00:00",
            )


if __name__ == "__main__":
    unittest.main()
