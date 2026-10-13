# Systems Foundry Bridge — Prototype

**Status:** Prototype scaffold; not production-ready and not connected to live external ecosystems.
**Purpose:** Convert one authorized mission into multiple explicit, prompt-scoped job plans, select capabilities for each job, and identify which jobs may be scheduled in parallel.

## Mission versus jobs

One mission may contain multiple jobs. A job is not inferred from a vague mission title: each job must have a unique ID, specific prompt/instructions, required capability tags, a maximum risk level, acceptance criteria, and declared dependencies.

- Jobs with no dependency between them are placed in the same parallel batch and are candidates for simultaneous execution.
- Jobs with dependencies are placed in later batches after their declared prerequisites.
- Every job receives its own capability-selection and risk checks.
- Any missing eligible capability, authorization failure, controller disagreement, duplicate job ID, unknown dependency, or dependency cycle halts planning.
- This prototype plans concurrency only. It does **not** execute jobs or prove that parallel execution is safe for shared files, resources, or environments. A future execution layer must add workspace isolation, resource locks, conflict detection, cancellation, and integration checks.

## What this prototype does

- Registers capability descriptors with stable IDs, system identity, tags, risk level, and adapter name.
- Accepts a mission request that references an external human-authorization record.
- Runs two policy controllers in parallel against the same registry snapshot for each job.
- Emits a mission plan with per-job capability selections and dependency-safe parallel batches.
- Emits plans only; it does **not** invoke tools, execute code, call external systems, provision resources, or deploy anything.
- Keeps authority verification behind an injected `AuthorityVerifier` interface. The default verifier denies all missions. A string supplied by a caller is not proof of human authorization.

## Important limitations

This is a bridge kernel prototype, not the completed Systems Foundry. It uses an in-memory registry and has no authentication server, cryptographic identity implementation, persistent audit ledger, live connector adapters, isolation sandbox, or independent security review. The controllers are separate policy paths in one process and are **not** independent trust domains. The test authority used in unit tests is a test double only.

Do not connect production credentials or expose this prototype to an untrusted network. Do not treat a successful plan as execution, qualification, or human ratification.

## Contract

1. Human authority remains external to the software.
2. The mission's authorization reference must be validated by a trusted external verifier; default behavior is deny.
3. Capability discovery never grants permission.
4. Each job must have prompt-specific scope, acceptance criteria, required capability tags, risk limit, and dependency declarations.
5. Both controllers must agree on each job's capability/system selection.
6. Independent jobs may be scheduled in the same proposed parallel batch; dependencies create ordered batches.
7. Any disagreement or missing evidence returns a halt; there is no majority override.
8. The output is a proposed plan, not permission to execute it.
9. Every future adapter must enforce authorization at its own execution boundary, not rely solely on this planner.

## Run tests

From the repository root:

```bash
python -m unittest discover -s bridge/tests -v
```

No third-party packages are required for the core prototype.
