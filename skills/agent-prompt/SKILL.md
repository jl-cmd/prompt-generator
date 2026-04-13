---
name: agent-prompt
description: >-
  Runs the full prompt-generator workflow, then spawns a background subagent using
  the user-approved XML prompt as its task. Use for /agent-prompt, delegated or
  background execution after a paste-ready prompt; use /prompt-generator when only
  the artifact is needed. Triggers include "launch an agent", "spawn agent to do X",
  "delegate this", and "run this in background".
---

@packages/claude-dev-env/skills/prompt-generator/SKILL.md
@packages/claude-dev-env/skills/prompt-generator/REFERENCE.md

# Agent prompt

## Summary

- **Prompt authoring:** Identical to `prompt-generator` (order, validation, `TARGET_OUTPUT.md` handoff). This skill does not add a second refinement pipeline.
- **Extra step:** After the handoff, one execution approval, then a background Agent/Task whose `prompt` is the finalized XML (verbatim).
- **Use this skill when:** The user wants a subagent to execute the work, not only receive the prompt file.
- **Use `/prompt-generator` instead when:** The user only needs the fenced XML and outcome digest.
- **Slash args** (e.g. `/agent-prompt fix the auth bug via TDD`): Treat as the goal string for `prompt-generator`, then run the workflow steps below.

## Workflow

Checklist pattern per [Agent Skills: workflows](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-workflows-for-complex-tasks). Copy into the thread and mark items complete as you go.

### Task progress

- [ ] Step 1: Prompt-generator finished; handoff matches `TARGET_OUTPUT.md` (XML in one `xml`-labeled markdown fence, then `## Outcome digest`).
- [ ] Step 2: Execution `AskUserQuestion` sent (subagent config summary, three options, each preview as specified).
- [ ] Step 3: Spawned only on **Launch it**; after **Edit first**, repeat Step 2 with updated XML; on **Cancel**, stop.

### Step 1 — Run prompt-generator (no shortcuts)

1. Open and follow `prompt-generator` end-to-end: discovery, `AskUserQuestion`, drafting subagent, Outcome preview gate, final handoff.
2. Stop after the **final** user-visible handoff from prompt-generator: the full prompt XML inside **one** markdown code fence whose language tag is `xml`, then **`## Outcome digest`** immediately below, per `TARGET_OUTPUT.md`.
3. Do **not** run a second refinement pipeline, duplicate compliance audit, or re-author sections here—prompt-generator already owns draft, refinement, validation loop, and preview rounds.

The XML inside that fence is the **execution payload**: self-contained instructions for a new context with no access to this chat.

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
