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

```
/pmin i need to modify or delete the task, and block any future creations of similar tasks from uipath
```

`/pmin` infers the platform (Windows Task Scheduler) and emits a structured XML prompt with `<role>`, `<instructions>`, and `<output_format>` tags that instruct a downstream agent to generate a step-by-step runbook covering task discovery, deletion, verification, and layered blocking (AppLocker, executable renaming, service disable). The Outcome digest summarizes the intended scope and verification criteria for that generated runbook — no PII required, no session context carried over.

Illustrative XML portion of the output (the Outcome digest is omitted here for brevity; task name and SID are discovered at runtime via `schtasks /query`):

```xml
<role>
You are a Windows system administrator with expertise in Task Scheduler, registry policy, and software restriction. You are helping the user remove a UiPath-created scheduled task and prevent UiPath from recreating it.
</role>

<instructions>
1. Identify the exact task to remove. Run the following to find UiPath tasks and note the full task name:

    schtasks /query /fo LIST /v | findstr /i "uipath"

   Use the exact TaskName returned (e.g. "UiPath Connected Updater App-S-1-5-21-{{USER_SID}}") in subsequent steps.

2. Delete the task using one of two methods:

   Method A — schtasks (may not require elevation for some per-user tasks):

    schtasks /delete /tn "{{TASK_NAME}}" /f

   Method B — Task Scheduler GUI: open taskschd.msc, locate the task, right-click, Delete.

3. Verify deletion:

    schtasks /query /tn "{{TASK_NAME}}"

   Expect an error indicating the task cannot be found — that confirms removal.

4. Block future task creation by UiPath. Apply one or more of these targeted layers:

   Layer 1 — AppLocker or Software Restriction Policy. Create a rule that blocks UiPath.Connected.Updater.App.exe from running at all, which prevents it from registering tasks:

    - Open secpol.msc → Application Control Policies → AppLocker → Executable Rules
    - Add a Deny rule for path: %LOCALAPPDATA%\Programs\UiPathPlatform\Updater\*.exe
    - Apply to "Everyone" or your user account.

   Layer 2 — Rename or remove the executable so the task cannot fire even if recreated:

    ren "%LOCALAPPDATA%\Programs\UiPathPlatform\Updater\UiPath.Connected.Updater.App.exe" UiPath.Connected.Updater.App.exe.disabled

   Layer 3 — Block the UiPath update service if one is registered:

    sc query | findstr /i uipath
    sc stop  UiPathUpdaterService
    sc config UiPathUpdaterService start= disabled

5. Confirm no residual UiPath tasks remain:

    schtasks /query /fo LIST | findstr /i "uipath"

   Expect: no output.
</instructions>

<output_format>
For each step, emit:
- The exact command run
- The raw terminal output (or "no output" if silent)
- A one-line status verdict: DONE / FAILED / SKIPPED (with reason)

End with a summary table:

    Step | Action                  | Status
    -----|-------------------------|-------
    1    | Identify task           | DONE
    2    | Delete task             | DONE
    3    | Verify deletion         | DONE
    4a   | AppLocker deny rule     | DONE
    4b   | Executable disabled     | SKIPPED – AppLocker preferred
    5    | Confirm no residual     | DONE
</output_format>
```

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