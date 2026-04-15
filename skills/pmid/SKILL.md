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

Four steps in one user-facing turn (no plan mode, no AskUserQuestion rounds, no Outcome preview gate — step 3 runs an internal validation loop until the draft is clean):

1. Read the raw input block from the invocation message.
2. Draft one xml fence with context-adapted tags, an Outcome digest, and a hook validation block.
3. Write the complete draft to `data/prompts/.draft-prompt.xml`. Run `python packages/claude-dev-env/hooks/blocking/prompt_workflow_validate.py data/prompts/.draft-prompt.xml`. On exit 2, read stderr violations, fix the specific violations indicated by stderr (edit the flagged lines when stderr provides line numbers; fix the relevant section when it names a structural violation), and re-run until exit 0.
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

Every tag used must be opened and closed. On the final user-facing turn, emit the fence first, then the Outcome digest immediately after — the fence characters only, with zero other surrounding prose. The draft file used for validation may still include the hook validation block until step 4 strips it.

## Quality rules

Apply positive framing throughout:

- Write direct imperatives that affirm what to do ("Ensure X", "Always X", "Require X").
- Every instruction states what to produce, what to enforce, what to verify.
- Use affirmative directives exclusively ("only X", "always X", "ensure X").
- Write full words in general prose; allow established technical format acronyms required by this skill, such as XML.
- Replace hedging phrases ("let me also check", "actually", "I think", "might be", "possibly") with direct assertions.

The draft must satisfy all validator gates before emission: positive framing (zero negative keywords inside the fenced XML), complete tag balance, zero ambiguous scope terms in the surrounding scaffolding.

## Validation loop invariant

The fenced XML is the structurally stable payload across re-runs. When a violation is inside the artifact (e.g. a negative keyword), edit only the minimal specific flagged lines. When a violation is in the surrounding scaffolding, adjust only scaffolding. Keep section order and boundaries stable between iterations; change only lines the stderr report names as violations inside the fence.

## Outcome digest

Emit `## Outcome digest` immediately after the closing fence on the final turn:

- **What it does** — plain-language summary of what running this prompt produces
- **Key inputs** — what the prompt needs to work (files, tools, context)
- **Done when** — how to tell the prompt succeeded
- **Quick sample** — short example of what the output looks like (about twenty lines max). Write raw executor output — not a description of the prompt's behavior. Any code blocks inside the Quick sample must use plain triple backticks with no language tag (never ` ```xml ` or any other tagged fence) so the structural checker does not detect a second xml fence. Do not use authoring phrases ("moved into", "extracted as", "replaced the softer", "changes from the original", "updated to match", "now names", "was added", "has been updated", "now includes", "changed from") — write the sample as actual executor output, not commentary on what changed.

The paste-ready section is the xml fence only; the digest is for reading.

## Input sanitisation

The hook validation block written to the draft file must contain all required markers: `checklist_results`, `overall_status`, every deterministic checklist row token required by `REQUIRED_CHECKLIST_ROWS`, plus the scope anchor tokens and context-control signals. These appear only in the hook validation block, which is stripped before user output — they are absent from the user-facing fence and digest.

If the raw input block contains any strings from `PROMPT_WORKFLOW_RESPONSE_MARKERS`, paraphrase or strip them before embedding them in the XML artifact. The user-facing fence must contain zero marker strings.

## Scope boundary

This skill is bounded to: read the input, draft and validate, emit the fence and digest, stop. The following are outside that boundary and stay out of every invocation:

- EnterPlanMode or ExitPlanMode
- AskUserQuestion
- Subagent delegation
- Outcome preview gate
- Scope anchors in the user-facing XML output
- Checklist rows in the user-facing XML output
