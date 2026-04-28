# Ledger schema

## Contents

- Entry fields
- ID format and sub-IDs
- Chat display between rounds
- Full outline on request
- Cross-references
- Required sections

## Entry fields

| Field | Description |
|---|---|
| `id` | `E<integer>` or `E<integer>.<sub>` for sentence-level splits of a single answer. |
| `section` | XML tag name this entry belongs to (lowercase, underscores). Claude infers the section per entry based on the question being asked. |
| `question` | The AskUserQuestion question text verbatim. |
| `answer` | The user-chosen option label or free-text answer, verbatim. |
| `parent` | Another entry ID if this entry refines or depends on an earlier decision; empty otherwise. |

## ID format

Root IDs: `E1`, `E2`, `E3`, monotonically increasing.

Sentence-level sub-IDs: when an answer contains multiple sentences, assembly splits the answer into sub-entries `E<root>.1`, `E<root>.2`, etc. Sub-IDs exist only at assembly time (Phase 4). During Phase 2 elicitation, entries are always root IDs.

## Chat display — append-only between rounds

After each AskUserQuestion round, the skill posts only the new entries added in that round.

```
New:
E5 [instructions] Backfill approach = generate UUID per existing row
E6 [scope] target_local_roots = ["Y:/Projects/theme_db/"]
```

## Chat display — full outline on request

When the user asks "show ledger" (or equivalent), the skill posts the full running outline.

```
## Ledger

### prompt_type
- agent-harness (E1)

### role
- senior database architect (E2)
  - plain language tone (E3, refines E2)

### instructions
- primary task: migrate theme_db schema (E4)
- backfill approach: generate UUID per existing row (E5)
```

## Cross-references

An entry may cite earlier entries in its value ("use the strategy from E5"). The validator confirms every referenced ID exists in the ledger.

## Required sections

Claude infers required sections per prompt; no hardcoded list. Minimum guarantee: the ledger has at least one entry in at least one section at end of Phase 2. The validator fails if the ledger is empty.
