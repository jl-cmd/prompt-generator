# @jl-cmd/prompt-generator

Standalone **prompt-generator** and **agent-prompt** skills for Claude Code, plus prompt-workflow hooks and rules. Install with `npx`. Layout matches [claude-code-config](https://github.com/jl-cmd/claude-code-config) for drop-in parity.

## Install (Claude Code)

```bash
npx @jl-cmd/prompt-generator
```

This copies:

- `skills/prompt-generator/` and `skills/agent-prompt/` → `~/.claude/skills/<skill-name>/`
- Hook scripts (under `hooks/`, including `blocking/` and tests) → `~/.claude/hooks/`
- `rules/prompt-workflow-context-controls.md` → `~/.claude/rules/`
- A manifest at `~/.claude/.prompt-generator-manifest.json`

Hook scripts on disk are separate from **registration**: lifecycle hooks are wired in Claude Code [settings](https://docs.anthropic.com/en/docs/claude-code/settings) using the [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) schema (`~/.claude/settings.json`, `.claude/settings.json`, or `.claude/settings.local.json`) so those commands run when you want them to.

## Install (Cursor, Third-party skills)

In Cursor, enable **Third-party skills** under **Settings → Features**. Cursor loads Claude-format hook definitions from `.claude/settings.local.json`, `.claude/settings.json`, and `~/.claude/settings.json` as described in [Third-party hooks](https://cursor.com/docs/reference/third-party-hooks). This package still places hook scripts under `~/.claude/hooks/`, so paths referenced from settings stay valid.

Native Cursor hooks use `hooks.json` (`version: 1`, JSON on stdin/stdout, exit code `2` to block); see [Hooks](https://cursor.com/docs/hooks).

## Skills

### `prompt-generator` (`/prompt-generator`)

Authors a repository-grounded XML prompt: discovery, `AskUserQuestion`, drafting with refinement and the file-based validation loop, an Outcome preview gate, then a single handoff with one markdown code fence labeled `xml` plus `## Outcome digest` per `TARGET_OUTPUT.md`. Delivers a paste-ready artifact; execution of that work is a separate step.

### `agent-prompt` (`/agent-prompt`)

Runs the **same** prompt-generator flow through that final handoff (discovery → preview → fenced XML + digest). Refinement, validation, and preview rounds live entirely inside prompt-generator; agent-prompt starts after that handoff.

After the handoff, it sends **one** execution `AskUserQuestion` (**Launch it**, **Edit first**, **Cancel**). On **Launch it**, it spawns a background Agent/Task with `run_in_background: true` and `prompt` set to the **approved XML** from the preview (full content, no summarization—the execution payload for a new context).

Typical **logical** role → **Cursor Task** `subagent_type` mapping (always confirm against your live tool schema—see `skills/agent-prompt/REFERENCE.md`):

| Task type | subagent_type | mode |
| --- | --- | --- |
| Codebase exploration, search, research | `explore` | default |
| Code implementation, bug fix, refactoring | `generalPurpose` | auto |
| Read-only audit, analysis, review | `generalPurpose` | default |
| Architecture, multi-step planning | `plan` | plan |

Use `/prompt-generator` when only the artifact is needed; use `/agent-prompt` when the user wants a subagent to execute after approval.

## Hooks and rules

- **`hooks/blocking/`** — Shared validator and gate helpers (for example `prompt_workflow_validate.py`, `prompt_workflow_gate_core.py`). Spec: `hooks/HOOK_SPECS_PROMPT_WORKFLOW.md`.
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
