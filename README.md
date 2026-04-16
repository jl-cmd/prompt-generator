# @jl-cmd/prompt-generator

Standalone **prompt-generator** and **agent-prompt** skills for Claude Code, plus prompt-workflow hooks and rules. Install with `npx`. Layout matches [claude-code-config](https://github.com/jl-cmd/claude-code-config).

## Install (Claude Code)

```bash
npx @jl-cmd/prompt-generator
```

This copies:

- `skills/prompt-generator/` and `skills/agent-prompt/` → `~/.claude/skills/<skill-name>/`
- Hook scripts (under `hooks/`, including `blocking/` and tests) → `~/.claude/hooks/`
- `rules/prompt-workflow-context-controls.md` → `~/.claude/rules/`
- A manifest at `~/.claude/.prompt-generator-manifest.json

Hook scripts on disk are separate from **registration**: lifecycle hooks are wired in Claude Code [settings](https://docs.anthropic.com/en/docs/claude-code/settings) using the [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) key in `settings.json`.

## Install (Cursor, Third-party skills)

In Cursor, enable **Third-party skills** under **Settings → Features**. Cursor loads Claude-format hook definitions from `.claude/settings.local.json`, `.claude/settings.json`, and `~/.claude/settings.json`.

Native Cursor hooks use `hooks.json` (`version: 1`, JSON on stdin/stdout, exit code `2` to block); see [Hooks](https://cursor.com/docs/hooks).

## Skills

### `prompt-generator` (`/prompt-generator`)

Authors a repository-grounded XML prompt: discovery, `AskUserQuestion`, drafting with refinement and the file-based validation loop, an Outcome preview gate, then a single handoff with one markdown code fence and an Outcome digest.

### `agent-prompt` (`/agent-prompt`)

Runs the **same** prompt-generator flow through that final handoff (discovery → preview → fenced XML + digest). Refinement, validation, and preview rounds live entirely inside prompt-generator; agent-prompt starts after the fence is emitted.

After the handoff, it sends **one** execution `AskUserQuestion` (**Launch it**, **Edit first**, **Cancel**). On **Launch it**, it spawns a background Agent/Task with `run_in_background: true` and `prompt` set to the validated XML fence.

Typical **logical** role → **Cursor Task** `subagent_type` mapping (always confirm against your live tool schema—see `skills/agent-prompt/REFERENCE.md`; runtime reads use `../prompt-generator/` from the agent-prompt skill directory):

| Task type | subagent_type | mode |
| --- | --- | --- |
| Codebase exploration, search, research | `explore` | default |
| Code implementation, bug fix, refactoring | `generalPurpose` | auto |
| Read-only audit, analysis, review | `generalPurpose` | default |
| Architecture, multi-step planning | `plan` | plan |

Use `/prompt-generator` when only the artifact is needed; use `/agent-prompt` when the user wants a subagent to execute after approval.

### `pmin` (`/pmin`)

Single-pass XML formatter — takes a raw input block, emits one clean `xml` fence with context-adapted tags and an Outcome digest. Zero tool calls, zero plan mode, zero validation loop.

### `pmid` (`/pmid`)

Mid-tier XML formatter — takes a raw input block, drafts context-adapted XML, runs the 15-row compliance audit and file-based validation loop, then emits the validated fence and Outcome digest. Zero plan mode, zero `AskUserQuestion`, zero Outcome preview gate.

Use `/pmin` for a quick single-pass format; use `/pmid` when validation is needed without the full interactive flow; use `/prompt-generator` for the full guided authoring experience.

#### Example — removing a scheduled task and blocking future recreation

A task that is specific enough to guide execution but contains no personal data is a natural fit for `/pmin`:

```
/pmin i need to modify or delete the task, and block any future creations of similar tasks from uipath
```

`/pmin` infers the platform (Windows Task Scheduler) and emits a structured XML prompt with `<role>`, `<instructions>`, and `<output_format>` tags that instruct a downstream agent to generate a step-by-step runbook covering task discovery, deletion, verification, and layered blocking (AppLocker, icacls, executable renaming, service disable). The Outcome digest summarizes the intended scope and verification criteria for that generated runbook — no PII required, no session context carried over.

## Hooks and rules

- **`hooks/blocking/`** — Shared validator and gate helpers (for example `prompt_workflow_validate.py`, `prompt_workflow_gate_core.py`, `prompt_workflow_gate_config.py`, `prompt_workflow_clipboard.py`). Spec: `hooks/HOOK_SPECS_PROMPT_WORKFLOW.md`.
- **`rules/prompt-workflow-context-controls.md`** — Stable policy pointers for prompt-workflow context.

## Claude Code ↔ Cursor (hooks)

Hook name mapping when using Claude-format settings in Cursor:

| Claude Code hook | Cursor hook |
| --- | --- |
| `PreToolUse` | `preToolUse` |
| `PostToolUse` | `postToolUse` |
| `UserPromptSubmit` | `beforeSubmitPrompt` |
| `Stop` | `stop` |
| `SubagentStop` | `subagentStop` |
| `SessionStart` | `sessionStart` |
| `SessionEnd` | `sessionEnd` |
| `PreCompact` | `preCompact` |

Tool name mapping for shared hook tooling (same source):

| Claude Code tool | Cursor tool | Supported |
| --- | --- | --- |
| `Bash` | `Shell` | Yes |
| `Read` | `Read` | Yes |
| `Write` | `Write` | Yes |
| `Edit` | `Write` | Yes |
| `Grep` | `Grep` | Yes |
| `Task` | `Task` | Yes |
| `Glob` | — | No |
| `WebFetch` | — | No |
| `WebSearch` | — | No |

## License

MIT — see [LICENSE](LICENSE).

## Issues

[github.com/jl-cmd/prompt-generator/issues](https://github.com/jl-cmd/prompt-generator/issues)