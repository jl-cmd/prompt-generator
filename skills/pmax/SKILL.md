---
name: pmax
description: Builds prompts decision by decision. Asks structured multiple-choice questions in small rounds, posts each approved answer as a tagged line in chat, then assembles the final prompt only from those tagged lines so nothing unapproved is added. Use when the user wants a prompt built piece by piece without re-reading drafts. Triggers: '/pmax', 'build a prompt with me', 'pmax', 'incremental prompt builder'.
---

# pmax

Authors XML prompt artifacts through incremental multiple-choice elicitation. Sibling of `/pmin` (single-pass) and `/pmid` (validated draft). Sits in the same prompt-generator family and reuses its validator, scope block, templates, and Outcome digest format.

## Trigger

`/pmax` followed by an initial prompt or task description. If the initial input is missing or too vague to infer file scope, the skill asks one AskUserQuestion before starting Phase 1.

## Six phases

1. **Read project files** — silent. The skill uses the initial prompt to infer which project files are relevant and reads them with Glob/Read. No user interaction. If the inferred file count is 0 or 1, the skill asks one AskUserQuestion to confirm scope.
2. **Ask the user** — one AskUserQuestion round at a time, up to 4 related questions per round. Each chosen option becomes a ledger entry.
3. **Check the answers** — runs `scripts/validate_ledger.py`. On failure, plain-language report returns control to Phase 2 with a targeted question.
4. **Build the prompt** — `scripts/assemble_prompt.py` groups ledger entries by section, emits XML tags, splits answers into sentences, places an HTML comment `<!-- E#.# -->` before every sentence.
5. **Preview the outcome** — one AskUserQuestion with `### Outcome preview` bullets (What it does, Key inputs, Done when, Quick sample). Options: Ship / two contextual alternates / Refine with free text. Cap 3 rounds.
6. **Show the prompt** — emits one fenced XML block in chat, copies XML to clipboard, then `## Outcome digest`.

See [reference/elicitation.md](reference/elicitation.md) for Phases 2 and 3 detail. See [reference/assembly.md](reference/assembly.md) for Phases 4, 5, 6 detail.

## Invariants

1. Ask related questions together in one round. Never batch unrelated ones.
2. No final prompt until the skill detects the user is done. Detection is inferred from context; no fixed stop phrase.
3. Ledger is append-only. Old entries are never rewritten.
4. Chat between rounds shows only the new entries added that round. Full running outline appears only when the user asks (e.g. "show ledger").
5. Phase gates are explicit. Phase N completes before Phase N+1 begins.
6. Every option uses plain language. When an option has a technical term, the description includes a plain-language explanation inline.
7. Questions can spawn sub-questions dynamically. The queue re-plans after every answer.
8. Phase 0 reads files silently before any questions fire.
9. Every sentence in the final prompt has a backing `<!-- E#.# -->` comment. The validator fails if any sentence is unbacked.

## Authoring rules for the skill's own output

- Every AskUserQuestion option lists the best option first. The best option is the actual recommendation.
- Option count per question stays within 2–4 (AskUserQuestion schema cap).
- Context and explanations live inside the AskUserQuestion question body and option descriptions, not in chat text between rounds.
- Sample artifacts (rendered XML, example prompt output) may appear in chat because the sample is the subject of the decision.
- Skill writes in third person.
- Skill avoids hedging words (plausibly, maybe, probably, could) in its own prompts.

See [reference/ledger_schema.md](reference/ledger_schema.md) for entry field definitions and display format.

## Refusals

First match wins. Reply with the exact quoted line and stop:

- **No initial prompt given.** `/pmax needs an initial prompt or task. Example: /pmax build a prompt for migrating a database schema.`
- **Initial prompt too vague to infer scope.** The skill asks one AskUserQuestion listing candidate paths or asking for the task domain, then proceeds.

## Reuse from prompt-generator

- Validator shell-out: `python hooks/blocking/prompt_workflow_validate.py <draft-file>` runs structural checks and the 15-row compliance audit.
- Scope block: five-key grammar (`target_local_roots`, `target_canonical_roots`, `target_file_globs`, `comparison_basis`, `completion_boundary`) when a `<scope>` section is needed.
- Outcome digest format: four bullets (What it does, Key inputs, Done when, Quick sample).
- Outcome preview gate: Phase 5 matches prompt-generator's preview turn shape (Ship / two alternates / Refine with free text).
- Templates folder (conditional): `templates/skill-from-ground-up.md`, `templates/skill-refinement-package.md` when the prompt being built is a skill.
- `[discovered]` option label for choices sourced from Phase 0 file reads.
- Clarity bar: every AskUserQuestion field, XML tag, and digest bullet states concrete outcomes, explicit formats, and checkable done-when signals.

## File plan

```
pmax/
├── SKILL.md
├── TARGET_OUTPUT.md          — eval-asserted output contract
├── ARCHITECTURE.md           — file map
├── reference/
│   ├── ledger_schema.md      — entry fields, display, sub-IDs
│   ├── elicitation.md        — Phases 2 and 3
│   ├── assembly.md           — Phases 4, 5, 6
│   └── examples.md           — three worked triples
├── evaluations/              — seven JSON scenarios
├── scripts/
│   ├── validate_ledger.py    — ledger checks + prompt-generator validator
│   └── assemble_prompt.py    — sentence-level XML assembly
└── config/
    └── constants.py          — named constants shared across scripts
```

## Outbound handoff

None. `/pmax` ends at the fenced XML plus Outcome digest. Execution of the generated prompt is inbound from `/agent-prompt` when the user routes it.

## Out of scope

- Plan mode.
- Drafting subagent.
- Multi-model testing for v1.

## Evaluations

Seven scenarios in `evaluations/`. Each JSON follows the Anthropic Agent Skills eval schema. The skill is considered correct when every listed `expected_behavior` bullet in every file passes.

See [reference/examples.md](reference/examples.md) for three worked input-to-ledger-to-output triples.
