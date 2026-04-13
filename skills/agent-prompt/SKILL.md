---
name: agent-prompt
argument-hint: "[goal or brief — becomes the prompt-generator user goal]"
description: >-
  Runs the prompt-generator workflow through its paste-ready XML handoff, then spawns
  a background subagent whose task is that user-approved XML. Triggers: '/agent-prompt',
  'launch an agent', 'spawn agent to do X', 'delegate this', 'run in background',
  'execute the prompt with an agent'. Does not apply when the user only needs the
  fenced prompt and digest with no subagent (/prompt-generator).
---

# Agent prompt

**Capability:** One end-to-end behavior — **handoff-quality XML via prompt-generator**, explicit execution approval, then **background** delegation using that XML alone as the subagent task. Not a second prompt author.

**Arguments:** Treat `$ARGUMENTS` (text after `/agent-prompt`) as the **goal string** for prompt-generator, then run the workflow below.

## Summary

- **Step 1** loads and follows the sibling **`prompt-generator`** skill (read `../prompt-generator/SKILL.md` from this skill directory, or see `REFERENCE.md` for repo-root equivalents). The execution subagent does **not** see this thread; only the fenced XML carries enough state. Paraphrasing or skipping prompt-generator drops scope and validation.
- **Step 2** is one execution `AskUserQuestion`. **Step 3** spawns with `run_in_background: true` and the **approved XML** as `prompt` (see `REFERENCE.md` for host tool enum mapping).

## Evaluation

| Asset | Purpose |
|-------|---------|
| `evals/agent-prompt.json` | Behavior scenarios (happy path, safety, edit loop, routing, trivial task) |
| `evals/agent-prompt-triggers.json` | Should-trigger / should-not-trigger phrases for description tuning (skill-builder polish) |

When changing `SKILL.md` or `REFERENCE.md`, update the relevant `expected_behavior` rows and, if discovery shifts, refresh trigger queries. Full trigger optimization loops belong in `skill-creator` (or equivalent), not in this file.

## Workflow

Checklist pattern per [Agent Skills: workflows](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-workflows-for-complex-tasks). Copy into the thread and mark items complete as you go.

### Task progress

- [ ] Step 1: Read `../prompt-generator/SKILL.md` (sibling skill) and run it through final handoff per `TARGET_OUTPUT.md` (one `xml` fence, then `## Outcome digest`).
- [ ] Step 2: Execution `AskUserQuestion` sent (subagent config from host schema via `REFERENCE.md`, three options, previews as specified).
- [ ] Step 3: Spawn only on **Launch it**; after **Edit first**, repeat Step 2 with updated XML; on **Cancel**, stop.

### Step 1 — Run prompt-generator (no shortcuts)

1. **Read** `../prompt-generator/SKILL.md` and execute it end-to-end: discovery, `AskUserQuestion`, drafting subagent, Outcome preview gate, final handoff. **Read** `../prompt-generator/REFERENCE.md` only when that workflow or the drafting agent requires rubric or template detail.
2. Stop after the **final** user-visible handoff: full prompt XML in **one** markdown code fence with language tag `xml`, then **`## Outcome digest`** immediately below, per prompt-generator’s output contract.
3. Keep draft, refinement, file validation, and preview rounds **inside** prompt-generator only—do not add a parallel refinement pipeline in this skill.

The XML inside that fence is the **execution payload** for a blank context.

### Step 2 — Approve execution

Use **one** `AskUserQuestion` after the prompt-generator handoff. Include in the question text:

- Proposed **subagent** configuration: map task to **host** `subagent_type` and `mode` using **`REFERENCE.md` § Subagent type** (confirm enums against the live tool descriptor).
- **Kebab-case** `name` (3–5 words) for follow-up where the host supports it (e.g. `SendMessage({to: name})`).
- That **`prompt` will be the finalized XML** (verbatim as approved), except after **Edit first** when the user replaces it.

**Options** (each option’s `preview` shows the full XML the subagent would receive, or a short note for Cancel):

1. **Launch it** (recommended) — preview = exact XML from the fence.
2. **Edit first** — preview = note that the user will paste or describe edits; after edits, return to this step with the new artifact.
3. **Cancel** — no execution; stop.

### Step 3 — Spawn (or stop)

- **Launch it:** Call the Agent/Task tool with `run_in_background: true`, the chosen `name`, host-valid `subagent_type` and `mode`, and **`prompt` set to the approved XML** — full content as shown in the **Launch it** preview, **no summarization or paraphrase**.
- **Edit first:** Show the current XML in the chat if needed; after the user supplies changes, treat the result as the new artifact and repeat Step 2.
- **Cancel:** Acknowledge and stop.

### If the user only needed the artifact

When the user clearly wants **only** `/prompt-generator` output (no subagent), **stop** using this skill and follow `../prompt-generator/SKILL.md` without an execution gate.

## When to stay inline

For **trivial** work (single quick read, one `grep`, one-line JSON check), **complete inline** and state that spawning a subagent would add overhead without benefit. Do not run prompt-generator solely to wrap a trivial lookup unless the user insists.

## Optional authoring note

When the goal implies risky implementation, the **XML** authored inside prompt-generator may include obstacle-handling lines (for example avoiding `--no-verify` or deleting unfamiliar files). That lives in the handoff artifact, not in extra steps here.
