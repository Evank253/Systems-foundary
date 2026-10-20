# KCN Link — Evidence Spine (Foundation Slice)

**Status:** IMPLEMENTED IN BRANCH; execution, external authorization verification, and independent verification remain NOT_MEASURED.

KCN Link is the evidence-preserving interoperability layer for the KCN Systems Foundry ecosystem. This initial slice implements a local JSONL evidence ledger with a SHA-256 hash chain.

## Implemented in this slice

- Stable event IDs and UTC-aware timestamps.
- Explicit event vocabulary: `SENT`, `RECEIVED`, `VERIFIED`, `ABORTED`, `REVOKED`, `DISPUTED`, `PROMOTED`, `DENIED`, `FLAGGED`.
- Explicit evidence states including `NOT_MEASURED`, `BLOCKED`, `FAILED`, and `INCOMPLETE`.
- Canonical JSON serialization and a SHA-256 hash chain.
- Chain verification before each append; malformed or changed records block further appends.
- No update/delete API in the ledger interface.
- Unit tests for chain continuity, tampering, duplicate IDs, empty-ledger status, and timezone requirements.

## Run tests

From the repository root:

```bash
python -m unittest discover -s kcn_link/tests -v
```

No third-party dependencies are required for this package.

## Security and evidence limits

- A hash chain detects changes relative to the recorded chain; it does not establish authorship, truth, authorization, or human ratification.
- Local file permissions and the host administrator remain in the trust boundary. This is not immutable or tamper-proof storage.
- `authorization_ref` is recorded as provenance only. It is not validated and never grants permission.
- `VERIFIED` is an event type, not a claim that this package independently verified the event. The caller must supply evidence and provenance for any such assertion.
- An empty ledger returns `NOT_MEASURED`, not `PASSED`.
- No transport, external connector, cryptographic identity provider, external human-authority verifier, signer/quorum, or production execution adapter is implemented in this slice.

## Next implementation gates

1. Define a versioned transport envelope and canonical payload digest.
2. Add receive-side recomputation and explicit sent/received/verified/aborted state transitions.
3. Add an adapter contract with authorization checked at each consequential execution boundary.
4. Add an independently anchored checkpoint/signature strategy without making hashes a substitute for authority.
5. Add persistence/concurrency tests, failure injection, and independent verification.

Human Authority remains external to software. Capability is not authorization; evidence is not authority; execution is not correctness; verification is not qualification; qualification is not human ratification.
