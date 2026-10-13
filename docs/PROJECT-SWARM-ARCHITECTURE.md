# Project Swarm Architecture — Proposed

**Status:** SPECIFIED at document level only. No runtime implementation is implied.

## Purpose

Coordinate multiple software projects concurrently from one engineering portal while keeping project context, tasks, artifacts, permissions, and evidence separated. Preserve ideas captured during conversations so they can be triaged and resumed later.

## Core records

- **Project:** stable ID, title, purpose, owner, status, repository references, current-state snapshot.
- **Idea:** stable ID, original wording, capture time, source/context reference, tags, related projects, triage state.
- **Requirement:** stable ID, rationale, acceptance criteria, priority, linked ideas, verification method.
- **Decision:** stable ID, decision, rationale, alternatives, author/approver, timestamp, supersedes relation.
- **Task:** stable ID, project ID, scope, owner/role, dependencies, permissions, input artifacts, output artifacts, acceptance criteria, status.
- **Artifact:** stable ID, URI/reference, content digest when available, producing task, source revision, license/provenance metadata.
- **Evidence record:** stable ID, claim tested, method, environment, result, raw result references, verifier identity, status.
- **Handoff snapshot:** current objective, completed work, active work, blockers, decisions, next action, relevant identifiers and repository revisions.

## Workflow

1. Capture a raw idea without rewriting away the original meaning.
2. Assign a stable identifier and persist it.
3. Link it to an existing project or mark it for triage.
4. Convert accepted ideas into requirements and acceptance criteria.
5. Decompose requirements into a dependency graph.
6. Assign bounded tasks to specialist roles.
7. Execute independent tasks in isolated workspaces or branches.
8. Review interfaces and artifacts before integration.
9. Run required tests and preserve results.
10. Update the project snapshot and next action.
11. Keep blocked, failed, incomplete, and unmeasured states explicit.

## Roles

- Context curator: gathers existing project decisions and avoids reopening completed work without evidence.
- Requirements analyst: converts goals into testable acceptance criteria.
- Architect: defines boundaries, interfaces, dependencies, and design decisions.
- Implementer: modifies only assigned scope and reports changed files and tests.
- Test engineer: executes specified tests and records raw results.
- Security/governance reviewer: checks permission boundaries and unsafe assumptions.
- Integration coordinator: resolves dependencies and combines reviewed outputs.
- Human decision point: approves defined privileged, destructive, external, or production actions.

Roles are logical responsibilities; the initial implementation may execute them sequentially or through existing tools. A document describing roles is not proof that autonomous agents or parallel execution exist.

## Parallel execution controls

- Each task has one accountable owner and explicit write scope.
- Parallel tasks share versioned interface contracts.
- Writes use isolated branches/worktrees or equivalent isolation.
- Concurrent changes are reconciled before integration.
- No task may modify authority policies or grant itself permissions.
- The coordinator may schedule and report; it cannot self-certify independent verification.
- Retry limits, timeouts, cancellation, and failure recovery must be explicit.
- A task is complete only when its acceptance criteria and required evidence are satisfied.

## Multi-project isolation

Every task, artifact, secret reference, and evidence record must carry a project scope. Cross-project reuse requires explicit authorization and provenance/licensing checks. Shared infrastructure does not mean shared permissions.

## Acceptance criteria for a first implementation

1. Create two projects and store distinct state for each.
2. Capture and retrieve ideas across sessions.
3. Generate a resumable snapshot for each project.
4. Create tasks with dependencies and role assignments.
5. Prevent a task from running while required dependencies are incomplete.
6. Reject unauthorized operations.
7. Preserve failures and missing evidence instead of reporting success.
8. Reconcile previously completed work rather than automatically reopening it.
