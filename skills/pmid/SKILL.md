---
name: pmid
description: >-
  Mid-tier XML formatter — takes a raw input block, drafts context-adapted XML,
  runs the 15-row compliance audit and file-based validation loop, then emits the
  validated fence and Outcome digest. Zero plan mode, zero AskUserQuestion, zero
  Outcome preview gate.
---

# pmid

## Trigger

`/pmid` followed by a raw input block.

## Flow

Four steps, single pass:

1. Read the raw input block from the invocation message.
2. Draft one xml fence with context-adapted tags, an Outcome digest, and a hook validation block.
3. Write the complete draft to `data/prompts/.draft-prompt.xml`. Run `python hooks/blocking/prompt_workflow_validate.py data/prompts/.draft-prompt.xml`. On exit 2, read stderr violations, fix the specific flagged lines in the file, and re-run until exit 0.
4. Strip the hook validation block. Emit the validated fence followed by the Outcome digest. Delete `data/prompts/.draft-prompt.xml`.

Zero tool calls beyond the validator CLI. Zero AskUserQuestion rounds. Zero plan mode entries.

## Default XML structure

```xml
<role>...</role>
<instructions>...</instructions>
<output_format>...</output_format>
```

Start from this structure and adapt it using all available context:

- **Input block** — sections the user's raw text already implies map naturally to tag names (e.g. a block describing background + steps + format maps to `<background>`, `<instructions>`, `<output_format>`)
- **Repo and folder context** — when Claude already knows the project's conventions (hook layout, skill format, test patterns), let that shape tag names and content
- **Session context** — prior conversation turns that clarify intent, audience, or constraints fold directly into tag content; incorporate what is already known
- **User specifics** — any explicit framing, target agent, or format the user stated in the `/pmid` invocation is the authoritative input; use it as the primary shaping signal

Every tag used must be opened and closed. Emit the fence first, then the Outcome digest immediately after — the fence characters only, with zero other surrounding prose.

## Quality rules

Apply positive framing throughout:

- Write direct imperatives that affirm what to do ("Ensure X", "Always X", "Require X").
- Every instruction states what to produce, what to enforce, what to verify.
- Use affirmative directives exclusively ("only X", "always X", "ensure X").
- Write full words in general prose; allow established technical format acronyms required by this skill, such as XML.
- Replace hedging phrases ("let me also check", "actually", "I think", "might be", "possibly") with direct assertions.

The draft must satisfy all validator gates before emission: positive framing (zero negative keywords inside the fenced XML), complete tag balance, zero ambiguous scope terms in the surrounding scaffolding.

## Validation loop invariant

The fenced XML is the immutable payload across re-runs. When a violation is inside the artifact (e.g. a negative keyword), edit only the specific flagged lines. When a violation is in the surrounding scaffolding, adjust only scaffolding. Keep the XML body byte-identical between iterations unless the stderr report names a line inside the fence.

## Outcome digest

Emit `## Outcome digest` immediately after the closing fence on the final turn:

- **What it does** — plain-language summary of what running this prompt produces
- **Key inputs** — what the prompt needs to work (files, tools, context)
- **Done when** — how to tell the prompt succeeded
- **Quick sample** — short example of what the output looks like (about twenty lines max)

The paste-ready section is the xml fence only; the digest is for reading.

## Input sanitisation

The hook validation block written to the draft file must contain all required markers (`checklist_results`, `overall_status`, scope anchor tokens, context-control signals) so the validator passes. These appear only in the hook validation block, which is stripped before user output — they are absent from the user-facing fence and digest.

If the raw input block contains any strings from `PROMPT_WORKFLOW_RESPONSE_MARKERS`, paraphrase or strip them before embedding them in the XML artifact. The user-facing fence must contain zero marker strings.

## Scope boundary

This skill is bounded to: read the input, draft and validate, emit the fence and digest, stop. The following are outside that boundary and stay out of every invocation:

- EnterPlanMode or ExitPlanMode
- AskUserQuestion
- Subagent delegation
- Outcome preview gate
- Scope anchors in the user-facing XML output
- Checklist rows in the user-facing XML output
