# Systems Foundry

**Working designation:** KCN Engineering Infrastructure Platform (KEIP-001)  
**Central workspace:** KCN Systems Foundry  
**Status:** Initial architecture baseline — proposed; implementation not yet verified.

Systems Foundry is intended to become a personal engineering platform and systems directory for designing, developing, integrating, testing, storing, and deploying multiple software projects from one governed workspace. It is more than a GitHub front end: it combines source-control integration, project workspaces, architecture design, connector management, build/test workflows, deployment adapters, persistent project records, and a coordinated project-agent workforce.

## Core outcome

From one workspace, the user can register or create multiple projects, preserve every idea and decision, assign bounded work to specialized agents, track dependencies and progress, integrate project outputs, test changes, and resume work later without losing the context or evidence.

## Foundational rules

1. Human Authority remains external to the software. No agent, model, or subsystem can self-authorize, self-ratify, or redefine the authority boundary.
2. Capability is not authorization. A registered connector or discovered tool may only perform operations explicitly permitted to it.
3. Execution is not correctness; verification is not qualification; qualification is not human ratification.
4. NOT_MEASURED, BLOCKED, FAILED, INCOMPLETE, and PASSED are distinct states. Missing evidence must not be presented as success.
5. Ideas, decisions, requirements, tasks, artifacts, and evidence must be durably recorded with stable IDs and provenance.
6. Multiple projects can progress concurrently, but each project has separate scope, state, permissions, artifacts, and release gates.
7. External platforms remain independently owned systems. Their API limits, permissions, licenses, costs, and terms continue to apply.
8. Prefer mature, replaceable open-source components over rebuilding foundational infrastructure without a clear benefit.
9. No deployment or paid-resource provisioning happens implicitly. Cost-bearing actions must be visible and authorized.
10. Do not mark a capability implemented until its code and required tests/evidence support that status.

## Proposed platform areas

- **Systems Registry:** projects, systems, components, interfaces, dependencies, and lifecycle state.
- **Idea & Decision Ledger:** durable capture of ideas, decisions, requirements, assumptions, questions, and supersession history.
- **Project Swarm Workforce:** bounded specialist agents/workers, task DAGs, shared contracts, isolated workspaces, conflict handling, integration, and review.
- **Connector Hub:** adapters for Git hosting, AI providers, databases, developer tools, cloud providers, documentation, and the user's own systems.
- **Architecture Studio:** system diagrams, API contracts, data models, dependency and compatibility analysis.
- **Engineering Workspace:** source-code and project editing, workspaces, branches, patches, and reviews.
- **Build & Test Engine:** isolated builds, unit/integration/contract/security/regression tests, logs, artifacts, and reproducibility records.
- **Deployment Fabric:** local, container, Kubernetes, static, serverless, and supported cloud targets through explicit adapters.
- **Project Vault:** project metadata, artifact references, configuration versions, backups, and durable project state.
- **Evidence & Governance:** provenance, audit history, permission checks, independent verification, qualification gates, and human approval records.
- **Cost & Resource Guard:** resource budgets, free-tier awareness, usage limits, and explicit confirmation before potentially billable actions.

These are target capabilities, not claims of current implementation.

## Project swarm operating model

The swarm is a project workforce, not an unrestricted set of autonomous agents. A project request is captured first, converted into a requirement and task graph, then assigned to bounded roles such as:

- Requirements & context curator
- Architecture & interface designer
- Repository/artifact investigator
- Frontend implementer
- Backend implementer
- Data/storage engineer
- Test & verification engineer
- Security/governance reviewer
- Integration/release coordinator

Roles may be combined for small projects. Parallel tasks must have explicit ownership, interfaces, dependencies, and isolated branches/workspaces. A coordinator can schedule and integrate work but cannot override permissions or declare its own output independently verified. Human approval remains required for defined privileged, destructive, external, or production actions.

## Multi-project continuity

The platform must support a portfolio view and per-project workspaces. Every new idea from a conversation should be captured as an inbox item with a stable ID, timestamp, source/context reference, status, and links to affected projects. It is not silently converted into an implementation task until triaged. Decisions and rejected alternatives are retained, and completed work is reconciled rather than automatically reopened.

Each project should maintain:
- PROJECT.md — purpose, boundaries, current state, and next action
- requirements and decision records
- task graph and ownership
- architecture/interface contracts
- repository and commit references
- tests, artifacts, deployment records, and unresolved findings
- a concise resumable handoff snapshot

## Initial delivery sequence

1. Establish product charter, architecture boundaries, status vocabulary, and idea/decision ledger.
2. Build a project portfolio and persistent project/idea APIs backed by a database.
3. Add one safe connector and demonstrate permission-scoped capability discovery and execution.
4. Add Git hosting/repository workflows and isolated task/workspace tracking.
5. Add bounded project swarm orchestration with explicit task ownership and review.
6. Add build/test workers and artifact/evidence records.
7. Add deployment adapters, resource-cost controls, and release gates.
8. Integrate KCN, MANIFEX, KSI, and other systems only after inspecting actual implementations and defining explicit contracts.

## Evidence labels

- **PROPOSED:** design intent only.
- **SPECIFIED:** documented interface or requirement exists.
- **IMPLEMENTED:** code exists.
- **TESTED:** specified tests executed with recorded results.
- **INDEPENDENTLY VERIFIED:** a separate verifier reproduced or confirmed the claim.
- **QUALIFIED:** required qualification criteria met.
- **HUMAN-RATIFIED:** explicit human ratification recorded where required.
- **NOT_MEASURED:** no adequate measurement/evidence.
- **BLOCKED / FAILED / INCOMPLETE:** reported distinctly.

## Current status

This repository's initial source tree has not yet been independently inspected or tested. The architecture in this README is a proposed baseline. A successful document commit does not mean the platform or swarm runtime exists.

## First acceptance criteria

- New ideas can be captured and retrieved after a session ends.
- A user can create multiple projects and switch between them without mixing project state.
- Each project has stable identifiers, a current-state summary, and a next action.
- Swarm tasks have explicit dependencies, owners, permissions, and completion evidence.
- Agents cannot promote their own output to independently verified or human-approved.
- Failed, blocked, incomplete, and unmeasured work stays visible.
- No paid service or production deployment is triggered without an explicit authorized action.
