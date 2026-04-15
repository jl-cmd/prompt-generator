---
name: pmin
description: >-
  Single-pass XML formatter — takes a raw input block and returns a clean xml
  fence with role, instructions, and output_format tags. No plan mode, no
  searches, no validation loop, no digest.
---

# pmin

## Trigger

`/pmin` followed by a raw input block.

## Flow

Read the raw input block in the invocation message. Emit one xml fence. Stop.

Zero tool calls. Zero AskUserQuestion rounds. Zero plan mode entries.

## Default XML structure

```xml
<role>...</role>
<instructions>...</instructions>
<output_format>...</output_format>
```

Fill each tag with a clean structural improvement of the input block. Every tag must be opened and closed in the output fence.

## Quality rules

Apply positive framing throughout:

- Write direct imperatives that affirm what to do ("Ensure X", "Always X", "Require X").
- Every instruction states what to produce, what to enforce, what to verify.
- Use affirmative directives exclusively ("only X", "always X", "ensure X").
- Write full words — zero abbreviations.
- Replace hedging phrases ("let me also check", "actually", "I think", "might be", "possibly") with direct assertions.

## Explicit exclusions

This skill performs none of the following:

- EnterPlanMode or ExitPlanMode
- AskUserQuestion
- Subagent delegation
- 15-row compliance audit
- File-based validation loop
- Scope anchors (target_local_roots, target_canonical_roots, target_file_globs, comparison_basis, completion_boundary)
- Checklist rows
- Outcome digest
- Outcome preview gate
