# Systems Foundry Bridge — Prototype

**Status:** Prototype scaffold; not production-ready and not connected to live external ecosystems.
**Purpose:** Provide a minimal, fail-closed bridge contract for discovering declared capabilities and producing a bounded mission plan under two parallel controllers.

## What this prototype does

- Registers capability descriptors with stable IDs, system identity, tags, risk level, and adapter name.
- Accepts a mission request that references an external human-authorization record.
- Runs two independent policy controllers in parallel against the same registry snapshot and mission.
- Compares the controllers' canonical plan digests. A disagreement, controller error, missing authorization reference, or empty eligible plan halts planning.
- Emits a plan only; it does **not** invoke tools, execute code, call external systems, provision resources, or deploy anything.
- Keeps authority verification behind an injected `AuthorityVerifier` interface. The default verifier denies all missions. A string supplied by a caller is not proof of human authorization.

## Important limitations

This is a first bridge kernel, not the completed Systems Foundry. It uses an in-memory registry and has no authentication server, cryptographic identity implementation, persistent audit ledger, live connector adapters, isolation sandbox, or independent security review. The two controller implementations are separate code paths, but they still run within one process and share the same host and inputs; they are **not** independent trust domains.

Do not connect production credentials or expose this prototype to an untrusted network. Do not treat a successful plan as qualification or human ratification.

## Contract

1. Human authority remains external to the software.
2. The mission's authorization reference must be validated by a trusted external verifier; default behavior is deny.
3. Capability discovery never grants permission.
4. Both controllers must produce the same canonical plan digest.
5. Any disagreement or missing evidence returns a halt; there is no majority override.
6. The output is a proposed plan, not permission to execute it.
7. Every future adapter must enforce authorization at its own execution boundary, not rely solely on this planner.

## Run tests

From the repository root:

```bash
python -m unittest discover -s bridge/tests -v
```

No third-party packages are required for the core prototype.
