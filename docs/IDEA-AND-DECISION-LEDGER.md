# Idea and Decision Ledger — Proposed

**Status:** SPECIFIED at document level only. Persistence APIs and database tables are not yet implemented or tested.

## Purpose

Prevent ideas, design decisions, and project continuation points from being lost when conversations end or multiple projects progress at once.

## Required behavior

- Capture the original idea in the user's own wording wherever practical.
- Give each record a stable, unique ID.
- Record capture time and a source/context reference when available.
- Link ideas to one or more projects without forcing premature assignment.
- Preserve revisions and supersession links instead of silently overwriting history.
- Distinguish raw ideas, accepted requirements, decisions, tasks, and completed work.
- Provide status, priority, tags, dependencies, and next action.
- Allow a project handoff snapshot to be exported as portable Markdown/JSON.
- Do not treat a conversational mention as permission to modify a repository or deploy software.
- Do not invent details missing from the source conversation.

## Suggested record states

- INBOX
- TRIAGE
- ACCEPTED
- PLANNED
- IN_PROGRESS
- BLOCKED
- DEFERRED
- COMPLETED
- REJECTED
- SUPERSEDED

A rejected or superseded idea remains in the history with its rationale where known.

## Suggested record shape

```json
{
  "id": "IDEA-YYYYMMDD-0001",
  "type": "idea",
  "title": "Short searchable title",
  "original_text": "Original user wording",
  "captured_at": "ISO-8601 timestamp",
  "source_ref": "conversation or artifact reference when available",
  "project_ids": [],
  "tags": [],
  "status": "INBOX",
  "priority": "UNSET",
  "related_record_ids": [],
  "decision_refs": [],
  "next_action": "Triage and link to a project",
  "evidence_refs": []
}
```

The example is a schema proposal, not a real captured user record or a running database.

## Project continuation snapshot

Each project should maintain a compact handoff record with:
- project identity and objective
- verified current state
- key decisions and constraints
- completed items with evidence references
- in-progress tasks
- blockers and unresolved questions
- repository, branch, and commit references
- next concrete action
- last-updated timestamp

The snapshot must separate verified facts from proposals and assumptions.

## Storage and recovery

The implementation should use a durable database with migrations and backups. A portable export should allow recovery if a provider changes or a cloud free tier disappears. Credentials and secrets must never be stored in the plain-text ledger.

## First acceptance tests

1. Save an idea and retrieve it after restarting the application.
2. Link one idea to two projects without duplicating its identity.
3. Preserve the original wording after adding a normalized title.
4. Supersede a decision while retaining the old decision and relationship.
5. Export and re-import records without losing identifiers or status.
6. Ensure one project's private data is not visible to an unauthorized project or user.
