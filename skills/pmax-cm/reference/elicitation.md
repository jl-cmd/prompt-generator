# Elicitation — Phases 2 and 3

## Contents

- Phase 2 loop
- Stop detection
- Dynamic queue
- Phase 3 checks
- Failure recovery

## Phase 2 — Ask the user

Loop until stop detected. Each iteration:

1. Select next question topic based on ledger state and uncovered sections.
2. Issue one AskUserQuestion call with 2–4 related multiple-choice options.
3. On answer, append new entries to the ledger.
4. If the answer spawns sub-questions, prepend them to the question queue.
5. Post only the new entries to chat (append-only per invariant 4).

Round-size cap: 4 questions per AskUserQuestion call (schema limit).

Related-only rule: questions in the same round share a topic. Unrelated questions go in separate rounds.

## Stop detection

The skill infers the user is done when the user:

- Types "done", "that's enough", "build it", or similar.
- Signals end through context.

When the skill detects that every required section has ≥1 entry and no open sub-threads exist, it asks one AskUserQuestion: "Ready to build the prompt?" with three options — Ship / Keep asking / Refine a section.

## Dynamic queue

A decision can produce follow-up questions. Example:

```
E3 [role] primary key type = UUID
 → spawns: UUID version? (v4 random, v7 time-sortable)
 → spawns: existing rows backfill? (generate fresh, reuse content_id hash)
```

The queue re-plans after every answer. The skill does not pre-declare the full question list.

## Phase 3 — Check the answers

Runs before every transition to Phase 4. `scripts/validate_ledger.py` performs these checks in order:

1. Every required section has ≥1 entry.
2. No entry references a missing entry ID.
3. No duplicate entry IDs.
4. No open sub-threads (parent answered, child unanswered).
5. Shells out to `hooks/blocking/prompt_workflow_validate.py` for structural and 15-row compliance checks.

## Failure recovery

On fail: plain-language report such as "E12 references E99 which does not exist; add an entry for the missing step." The skill returns to Phase 2 and issues a targeted AskUserQuestion to fix the gap. No auto-fix; every resolution is a user-approved ledger entry.

On pass: proceed to Phase 4.
