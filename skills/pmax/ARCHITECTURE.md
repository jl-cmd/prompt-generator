# pmax — file map

| Path | Role |
|---|---|
| `SKILL.md` | Orchestration checklist, invariants, refusals, phase overview. Entry point. |
| `TARGET_OUTPUT.md` | Eval-asserted user-visible output contract. Update alongside SKILL.md. |
| `ARCHITECTURE.md` | This file. Lists every file in the skill package. |
| `reference/ledger_schema.md` | Ledger entry fields, ID format, sub-ID format, chat display conventions. |
| `reference/elicitation.md` | Phase 2 (Ask the user) and Phase 3 (Check the answers) behavior. |
| `reference/assembly.md` | Phase 4 (Build the prompt), Phase 5 (Preview the outcome), Phase 6 (Show the prompt) behavior. |
| `reference/examples.md` | Three worked triples: initial prompt, full ledger trace, final XML output. |
| `evaluations/db_schema_migration.json` | Eval 1 — complex case: hierarchy, branching, cross-references, novice-safe options. |
| `evaluations/tiny_rename.json` | Eval 2 — over-elicitation guard: small scope should produce few rounds and a short prompt. |
| `evaluations/plain_language.json` | Eval 3 — plain language: skill never uses jargon in its own questions. |
| `evaluations/askuserquestion_usage.json` | Eval 4 — AskUserQuestion discipline: no free-text questions, no chat-context between rounds. |
| `evaluations/scope_discipline.json` | Eval 5 — scope discipline: no added steps, correct external integrations, re-ask check. |
| `evaluations/writing_mechanics.json` | Eval 6 — writing mechanics: third person, no hedging, 4-option cap. |
| `evaluations/preview_completeness.json` | Eval 7 — preview completeness: every ledger entry represented in Phase 5 preview. |
| `scripts/validate_ledger.py` | Runs ledger-specific structural checks, then shells out to prompt-generator's validator. |
| `scripts/assemble_prompt.py` | Groups ledger entries by section, emits XML with sentence-level HTML comments. |
| `config/constants.py` | Named constants shared across scripts: entry ID format, comment format, validator path, limits. |

## Reuse references (not files in this package)

| Referenced path | Reused for |
|---|---|
| `Y:/Projects/LLM Plugins/prompt-generator/hooks/blocking/prompt_workflow_validate.py` | Structural checks, 15-row compliance audit, positive framing. Shelled out via subprocess. |
| `Y:/Projects/LLM Plugins/prompt-generator/skills/prompt-generator/templates/skill-from-ground-up.md` | Template when the prompt being built is a skill. |
| `Y:/Projects/LLM Plugins/prompt-generator/skills/prompt-generator/templates/skill-refinement-package.md` | Template when the prompt refines an existing skill. |
