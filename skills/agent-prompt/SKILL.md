---
name: agent-prompt
description: >-
  Runs the full prompt-generator workflow, then spawns a background subagent whose task
  is the user-approved XML from that handoff. Use for /agent-prompt, delegated work, or
  background execution after a paste-ready prompt exists. Do not select when the user only
  wants the prompt artifact with no subagent run (/prompt-generator). Triggers: launch or
  spawn an agent, delegate this, run in background, execute the prompt with an agent.
---

@packages/claude-dev-env/skills/prompt-generator/SKILL.md
@packages/claude-dev-env/skills/prompt-generator/REFERENCE.md

# Agent prompt

## Summary

- Run **`prompt-generator` first** through its final handoff (same contract as `TARGET_OUTPUT.md`). The execution subagent **does not** see this conversation; only the fenced XML carries state, so paraphrasing or skipping steps drops scope, validation, and compliance signals.
- **Then** one execution `AskUserQuestion`, then spawn with `run_in_background: true` and `prompt` = approved XML only.
- **Slash text** after `/agent-prompt` is the goal string for `prompt-generator`, then the steps below.

## Evaluation

Grade behavior against `evals/agent-prompt.json` (three scenarios: happy path, no spawn without approval, edit-first loop). Add or tighten eval rows when you change this skill; do not expand SKILL.md without updating evals (see [Anthropic: evaluation and iteration](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration)).

## Workflow

Checklist pattern per [Agent Skills: workflows](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-workflows-for-complex-tasks). Copy into the thread and mark items complete as you go.

### Task progress

- [ ] Step 1: Prompt-generator finished; handoff matches `TARGET_OUTPUT.md` (XML in one `xml`-labeled markdown fence, then `## Outcome digest`).
- [ ] Step 2: Execution `AskUserQuestion` sent (subagent config summary, three options, each preview as specified).
- [ ] Step 3: Spawned only on **Launch it**; after **Edit first**, repeat Step 2 with updated XML; on **Cancel**, stop.

### Step 1 — Run prompt-generator (no shortcuts)

1. Open and follow `prompt-generator` end-to-end: discovery, `AskUserQuestion`, drafting subagent, Outcome preview gate, final handoff.
2. Stop after the **final** user-visible handoff: the full prompt XML inside **one** markdown code fence whose language tag is `xml`, then **`## Outcome digest`** immediately below, per `TARGET_OUTPUT.md`.
3. Keep all draft, refinement, file validation, and preview rounds **inside** `prompt-generator` only.

The XML inside that fence is the **execution payload** for a blank context.

### Step 2 — Approve execution

Use **one** `AskUserQuestion` after the prompt-generator handoff. Include in the question text:

- Proposed **subagent** configuration from the table below (`subagent_type`, `mode`, **kebab-case** `name`, 3–5 words) for follow-up (`SendMessage({to: name})` where supported).
- That **`prompt` will be the finalized XML** (verbatim), unless the user chose **Edit first** and supplied changes.

**Options** (each option’s `preview` shows the full XML the subagent would receive, or a short note for Cancel):

1. **Launch it** (recommended) — preview = exact XML from the fence.
2. **Edit first** — preview = note that the user will paste or describe edits; after edits, return to this step with the new artifact.
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

- **Launch only after Step 2** resolves to **Launch it** with the XML preview the user approved.
- **Ship the full approved XML** as the subagent `prompt` unless the user replaced it under **Edit first**.
- For **trivial** work (single quick read, one grep), complete it **inline** and explain that delegation would add overhead.
- When authoring via `prompt-generator`, you may **add** obstacle-handling lines inside the XML (for example avoid `--no-verify` or deleting unfamiliar files) **only** when the goal implies risky implementation.
