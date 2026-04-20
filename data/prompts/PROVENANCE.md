# Eval output provenance

This directory holds the captured skill outputs that `run_evals.py` scores against each eval's `expected_behavior`. Each `eval-<skill>-<id>-output.txt` should be a **real capture** — what the skill actually produces when given the eval's `prompt` field. The table below records the provenance of every file so the baseline is legible.

## Capture provenance

| Skill | Eval IDs | Provenance | Runtime |
|---|---|---|---|
| `pmid` | 1–4 | Real (pre-existing) | Past Claude Code session |
| `pmin` | 1–8 | Real (pre-existing) | Past Claude Code session |
| `agent-prompt` | 1–6 | Real | Groq `llama-3.3-70b-versatile` via `capture_all.py` |
| `pmax` | 1–7 | Real | Groq `llama-3.3-70b-versatile` via `capture_all.py` |
| `prompt-generator` | 2, 3, 7, 13, 16 | Real | Groq `llama-3.3-70b-versatile` via `capture_all.py` |
| `prompt-generator` | 1, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 17 | Skipped (pending Groq TPD reset) | — |

## About the 12 pending prompt-generator files

`prompt-generator` has the largest `SKILL.md` in the repo (360 lines, ~12k tokens per call). The first `capture_all.py` run exhausted Groq's free-tier tokens-per-day limit (100 000 TPD) before finishing. These files currently contain the sentinel line `SKILL_INVOCATION_SKIPPED: claude runtime required ...` from an earlier routing decision that has since been flipped.

**To fill them:** after the Groq free-tier budget resets (daily), run `python capture_all.py`. The driver skips existing real captures and only redoes files that contain a sentinel or are missing, so no manual cleanup is needed.

## How capture routing works

`config/capture_runtime.py` classifies each skill. Currently every registered skill routes to Groq (`groq/llama-3.3-70b-versatile` via LiteLLM). If a future skill needs Claude Code's runtime (because its evals test `AskUserQuestion`, `EnterPlanMode`, or subagent spawns directly rather than output shape), add it to the classifier with `"claude"` and the dispatcher will write a skipped sentinel until a Claude-runtime capture path is added.

## How to promote a file to Real manually

If you run a skill in a live Claude Code session and want to capture that output instead of Groq's:

1. Open a fresh session in a clean working tree.
2. Paste the eval's `prompt` field verbatim as the user message.
3. Let the skill run end-to-end, answering any AskUserQuestion round with the plainest plausible option.
4. Save the skill's full response to `eval-<skill>-<id>-output.txt`, overwriting the current file.
5. Update the row above.
