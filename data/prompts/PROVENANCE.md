# Eval output provenance

This directory holds the captured skill outputs that `run_evals.py` scores against each eval's `expected_behavior`. Each `eval-<skill>-<id>-output.txt` should ideally be a **real skill run** — what the skill actually produced when a user gave it the eval's `prompt` field. The table below records the provenance of every file so the baseline is legible.

Provenance categories:

- **Real** — captured from an actual end-to-end skill invocation with real user gates.
- **Synthesized-to-contract** — written by a subagent to match the skill's documented output contract, because the skill's interactive gates (plan mode, AskUserQuestion rounds, subagent spawns) cannot be driven from a single subagent turn. LLM-judge scores on these are suggestive, not authoritative.
- **Skipped** — single line `SKILL_INVOCATION_SKIPPED: budget`. The runner converts these from file-not-found into a judged FAIL so the eval appears in the baseline report.

| Skill | Eval IDs | Provenance |
|---|---|---|
| `pmid` | 1–4 | Real (pre-existing) |
| `pmin` | 1–8 | Real (pre-existing) |
| `agent-prompt` | 1 | Real (one full skill invocation) |
| `agent-prompt` | 2, 3, 6 | Synthesized-to-contract (xml fence + Outcome digest) |
| `agent-prompt` | 4 | Synthesized (stay-inline routing path) |
| `agent-prompt` | 5 | Synthesized (inline answer path) |
| `pmax` | 1–7 | Synthesized-to-contract (ledger lines + fenced XML + digest) |
| `prompt-generator` | 1–17 | Skipped |

## How to promote a file from synthesized or skipped to real

1. Open a fresh Claude Code session in a clean working tree.
2. Paste the eval's `prompt` field verbatim as the user message.
3. Let the skill run end-to-end, answering any AskUserQuestion round with the plainest plausible option.
4. Save the skill's full response (for `agent-prompt`, stop at the fence + digest, before the Launch-execution gate) to `eval-<skill>-<id>-output.txt`, overwriting the current file.
5. Update the row in the table above.
