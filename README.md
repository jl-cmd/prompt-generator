# @jl-cmd/prompt-generator

This package installs the **prompt-generator** and **agent-prompt** skills, supporting hooks and rules for a consistent prompt workflow. Use **`/prompt-generator`** to author repository-grounded XML prompt artifacts and **`/agent-prompt`** when you want the same workflow plus spawning a background agent after you confirm execution. Optional validation hooks enforce prompt-workflow signals at runtime.

## Install (Claude Code)

```bash
npx @jl-cmd/prompt-generator
```

Files are copied under `~/.claude/skills/` (per-skill folders), `~/.claude/hooks/` (including `blocking/`), and `~/.claude/rules/`. An install manifest is written to `~/.claude/.prompt-generator-manifest.json`.

Hook registration uses Claude Code’s settings JSON. See [Hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) and [Settings](https://docs.anthropic.com/en/docs/claude-code/settings).

## Install (Cursor + Third-party skills)

Enable **Third-party skills** in **Cursor Settings → Features**. Per [Third-party hooks](https://cursor.com/docs/reference/third-party-hooks), Cursor reads `.claude/settings.local.json`, `.claude/settings.json`, and `~/.claude/settings.json` for Claude-format hooks. This installer still copies hook scripts to `~/.claude/hooks/` so paths referenced in those settings stay valid.

For native Cursor hook configuration (version 1, JSON over stdio, exit code 2 to block), see [Cursor hooks](https://cursor.com/docs/hooks).

## Claude Code ↔ Cursor compatibility (hooks)

Claude Code hook names are automatically mapped to Cursor hook names:

| Claude Code Hook | Cursor Hook |
| --- | --- |
| `PreToolUse` | `preToolUse` |
| `PostToolUse` | `postToolUse` |
| `UserPromptSubmit` | `beforeSubmitPrompt` |
| `Stop` | `stop` |
| `SubagentStop` | `subagentStop` |
| `SessionStart` | `sessionStart` |
| `SessionEnd` | `sessionEnd` |
| `PreCompact` | `preCompact` |

## Tool name mapping (shared hooks)

Claude Code tool names are mapped to Cursor tool names:

| Claude Code Tool | Cursor Tool | Supported |
| --- | --- | --- |
| `Bash` | `Shell` | Yes |
| `Read` | `Read` | Yes |
| `Write` | `Write` | Yes |
| `Edit` | `Write` | Yes |
| `Grep` | `Grep` | Yes |
| `Task` | `Task` | Yes |
| `Glob` | - | No |
| `WebFetch` | - | No |
| `WebSearch` | - | No |

## Implementation snapshot

- **`bin/install.mjs`** — Copies `skills/prompt-generator` and `skills/agent-prompt` into `~/.claude/skills/`; copies listed hook files under `~/.claude/hooks/` (e.g. `blocking/*.py`, tests, `HOOK_SPECS_PROMPT_WORKFLOW.md`); copies `rules/prompt-workflow-context-controls.md` to `~/.claude/rules/`; writes `~/.claude/.prompt-generator-manifest.json`.
- **`skills/prompt-generator/SKILL.md`** — Prompt-generator skill entrypoint.
- **`hooks/blocking/prompt_workflow_validate.py`** — Validation hook implementation.
- **`hooks/HOOK_SPECS_PROMPT_WORKFLOW.md`** — Hook behavior specification for the prompt workflow.
- **`rules/prompt-workflow-context-controls.md`** — Durable prompt-workflow policy text for rules.

## License

This project is licensed under the MIT License; see [LICENSE](LICENSE).

## Issues

[https://github.com/jl-cmd/prompt-generator/issues](https://github.com/jl-cmd/prompt-generator/issues)
