# Agent prompt — reference

Load this file when you need paths, host tool enums, or trigger-eval text. Keep `SKILL.md` as the execution checklist.

## Single capability

This skill provides **one** behavior: produce a **prompt-generator-quality** XML handoff, get explicit approval, then run that XML as the **sole** task instructions for a **background** subagent. It does not replace `prompt-generator` for artifact-only requests.

## Dependency paths (sibling skill layout)

Claude Code installs this skill next to `prompt-generator` under the same parent (for example `~/.claude/skills/agent-prompt/` and `~/.claude/skills/prompt-generator/`). **Resolve paths from the directory that contains this `SKILL.md`.**

| Artifact | Path from this skill directory | Same file in `@jl-cmd/prompt-generator` repo (workspace root) |
|----------|--------------------------------|---------------------------------------------------------------|
| Prompt-generator instructions | `../prompt-generator/SKILL.md` | `skills/prompt-generator/SKILL.md` |
| Prompt-generator supporting detail | `../prompt-generator/REFERENCE.md` | `skills/prompt-generator/REFERENCE.md` |
| Handoff contract | `../prompt-generator/TARGET_OUTPUT.md` | `skills/prompt-generator/TARGET_OUTPUT.md` |
| Graded scenarios | `evals/agent-prompt.json` | `skills/agent-prompt/evals/agent-prompt.json` |
| Trigger query sets | `evals/agent-prompt-triggers.json` | `skills/agent-prompt/evals/agent-prompt-triggers.json` |

Where the host expands `${CLAUDE_SKILL_DIR}`, you may read `${CLAUDE_SKILL_DIR}/../prompt-generator/SKILL.md` instead.

At the **start of Step 1**, read `../prompt-generator/SKILL.md` and follow it through the final handoff. Read `../prompt-generator/REFERENCE.md` only when rubric, templates, or drafting detail requires it.

## Subagent type: use the host tool schema

`SKILL.md` uses **roles** (explore, implementation, read-only audit, planning). Your **Agent** or **Task** tool expects a specific `subagent_type` string (or equivalent).

1. Open the tool descriptor for your environment **before** spawning.
2. Map each row using the **exact** enum string the schema allows (case-sensitive).

| Role in SKILL.md | Typical Cursor `Task` `subagent_type` (confirm in live schema) |
|------------------|----------------------------------------------------------------|
| Codebase exploration, search, research | `explore` |
| Code implementation, bug fix, refactoring | `generalPurpose` |
| Read-only audit, analysis, review | `generalPurpose` |
| Architecture, multi-step planning | `plan` |

If the schema differs (hyphenated names, aliases, or extra types), **the schema wins**. Do not invent strings.

## Approved XML for `prompt`

Use the **full text** of the prompt XML as last approved for **Launch it**—same elements and order as in the preview, **no summarization**. Normalizing trivial copy-paste whitespace is acceptable only if the user explicitly agrees; default is to treat the preview string as authoritative.

## Process gaps this file does not automate

- **Trigger optimization** (train/test splits, description scoring): run your `skill-creator` or internal harness against `evals/agent-prompt-triggers.json` when tuning discovery.
- **Claude B transcripts**: run `evals/agent-prompt.json` scenarios in a subagent and archive observations per skill-builder **improve-skill** workflow.
