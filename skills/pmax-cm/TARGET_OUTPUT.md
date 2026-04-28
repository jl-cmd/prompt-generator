# pmax — user-visible output contract

Methodology: [Anthropic Agent Skills evaluation and iteration](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration).

## Terminology

- **Ledger** — Running list of approved decisions shown in chat. Append-only. Each entry has an ID, section, question, answer, optional parent ID.
- **Outcome preview** — Phase 5 AskUserQuestion turn. Four-bullet summary (What it does, Key inputs, Done when, Quick sample) plus Ship / two contextual alternates / Refine-with-free-text options.
- **Outcome digest** — `## Outcome digest` markdown block after the closing fence on the final handoff. Same four bullets, tightened.
- **Entry tag** — HTML comment `<!-- E#.# -->` placed before every sentence in the final XML. Validator enforces presence.

## Contract

- **Clarity bar** — Every AskUserQuestion field, XML body, Outcome digest bullet, and Ledger entry states concrete outcomes, explicit formats, and checkable done-when signals.
- **Questions** — Every clarifying question uses AskUserQuestion. Up to 4 related options per question. Best option listed first. Options sourced from Phase 0 file reads carry the `[discovered]` label.
- **Chat between rounds** — Only the new ledger entries added that round. Sample artifacts may appear in chat because the sample is the subject of the decision.
- **Ledger display** — Append-only after each round. Full outline rendered only on user request.
- **Outcome preview turn (mandatory)** — Fires immediately before Phase 6. Bullets stay under 20 lines. Quick sample shows real executor output, not a description of it.
- **Final assistant message**
  1. One `xml` fenced block containing the full prompt.
  2. `## Outcome digest` after the closing fence.
  3. XML copied to clipboard unless `PROMPT_WORKFLOW_SKIP_CLIPBOARD=1`.
- **Line format inside the fence** — One sentence per line. A `<!-- E#.# -->` comment precedes every sentence. Validator fails on any unbacked sentence.
- **File-based validation loop** — `scripts/validate_ledger.py` runs ledger-specific checks, then shells out to `prompt_workflow_validate.py` for structural and 15-row audit. On failure: plain-language report, return to Phase 2.
- **Decision stability** — Once the skill commits to a section plan, it stays stable. New facts from user answers can add entries; they do not delete approved entries.

## Scenarios

### Scenario A — Complex task (DB migration)

Trigger: `/pmax` with a task requiring hierarchical decisions, cross-references, or novice-safe framing.

Expected: many Phase 2 rounds with sub-question queuing, `[discovered]` labels on options derived from silent Phase 0 reads, preview bullets that mention every ledger entry.

### Scenario B — Tiny task (single rename)

Trigger: `/pmax` with a scope limited to one or two decisions.

Expected: 3 or fewer Phase 2 rounds, no unneeded sub-questions, final prompt under 30 lines.

### Scenario C — Skill-shaped prompt

Trigger: `/pmax` where the prompt being built is itself a Claude Code skill.

Expected: Phase 0 loads `templates/skill-from-ground-up.md` or `templates/skill-refinement-package.md` from prompt-generator. Sections mirror template structure. Ledger entries correspond to template slots.

## Eval expectations

Every JSON in `evaluations/` asserts `expected_behavior` bullets against this contract. See `evaluations/*.json` for specific scenarios.
