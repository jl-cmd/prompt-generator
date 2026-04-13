---
name: agent-prompt
description: >-
  Run the full prompt-generator workflow, then—after explicit user approval—spawn a
  background subagent whose task prompt is that finalized XML artifact. Use instead of
  /prompt-generator when the user wants the same prompt quality plus delegated execution.
  Triggers on /agent-prompt, "launch an agent for this", "spawn agent to do X",
  "delegate this", "run this in background", or any task that benefits from agent
  execution after a paste-ready prompt exists.
---

@packages/claude-dev-env/skills/prompt-generator/SKILL.md
@packages/claude-dev-env/skills/prompt-generator/REFERENCE.md

# Agent prompt

**Relationship to prompt-generator:** Do everything prompt-generator does, in the same order and to the same delivery contract (`TARGET_OUTPUT.md`). The only addition is a final execution gate and a background subagent that runs using the approved prompt artifact as its instructions.

**When this skill applies:** The user wants work executed by a subagent, not only a paste-ready prompt. If they only want the artifact, use `/prompt-generator`.

**Invocation with arguments** (e.g. `/agent-prompt fix the auth bug via TDD`): Treat the arguments as the user goal passed into prompt-generator (same as starting `/prompt-generator` with that text), then continue to execution steps below.

## Workflow

Copy this checklist and check off items as you complete them (see [Agent Skills best practices — workflows](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-workflows-for-complex-tasks)):

**Task progress**

- [ ] Step 1: Prompt-generator complete (`xml` fence + `## Outcome digest` per `TARGET_OUTPUT.md`)
- [ ] Step 2: Execution `AskUserQuestion` shown (config summary + three options with previews)
- [ ] Step 3: Spawn only on **Launch it**; loop Step 2 after **Edit first**; stop on **Cancel**

### Step 1 — Run prompt-generator (no shortcuts)

1. Open and follow `prompt-generator` end-to-end: discovery, `AskUserQuestion`, drafting subagent, Outcome preview gate, final handoff.
2. Stop after you have the **final** user-visible deliverable from prompt-generator: **one** complete ` ```xml ` fence (the prompt artifact) plus **`## Outcome digest`** immediately after it, per `TARGET_OUTPUT.md`.
3. Do **not** run a second refinement pipeline, duplicate compliance audit, or re-author sections here—prompt-generator already owns draft, refinement, validation loop, and preview rounds.

The string inside the `xml` fence is the **execution payload**: self-contained instructions for a new context with no access to this chat.

### Step 2 — Approve execution

Use **one** `AskUserQuestion` after the prompt-generator handoff. Summarize in the question text:

- Proposed **subagent** configuration (see table below): `subagent_type`, `mode` if applicable, **kebab-case** `name` (3–5 words) for follow-up (`SendMessage({to: name})` where supported).
- That the subagent **`prompt` will be the finalized XML only** (verbatim), unless the user edits under **Edit first**.

**Options** (each option’s `preview` shows the full XML artifact the subagent will receive, or a short note for Cancel):

1. **Launch it** (recommended) — preview = exact XML from the fence.
2. **Edit first** — preview = note that the user will paste or describe edits; after edits, return to this step with the updated XML as the new payload.
3. **Cancel** — no execution; stop.

### Step 3 — Spawn (or stop)

- **Launch it:** Call the Agent/Task tool with `run_in_background: true`, the chosen `name`, `subagent_type` and `mode` from the mapping below, and **`prompt` set to the approved XML text** (byte-for-byte the artifact, no summarization).
- **Edit first:** Show the current XML in the chat if needed; after the user supplies changes, treat the result as the new artifact and repeat Step 2.
- **Cancel:** Acknowledge and stop.

### Subagent configuration (Step 2)

| Task type | subagent_type | mode |
|-----------|---------------|------|
| Codebase exploration, search, research | explore | default |
| Code implementation, bug fix, refactoring | general-purpose | auto |
| Read-only audit, analysis, review | general-purpose | default |
| Architecture, multi-step planning | plan | plan |

Always set `run_in_background: true`.

## Constraints

- **No launch without Step 2 approval.**
- **Execution prompt = approved XML artifact**; do not substitute an abbreviated brief unless the user explicitly replaces the artifact under **Edit first**.
- If the task is too small to justify a subagent (single quick read, one grep), say so and complete it inline instead of running this workflow.
- Optional one-line guardrail to include inside the XML when authoring via prompt-generator (not a second pipeline here): obstacle handling such as avoiding destructive shortcuts (for example `--no-verify`, deleting unfamiliar files) — only when the goal implies implementation risk.
