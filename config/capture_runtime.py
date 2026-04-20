"""Skill-to-runtime classifier for the eval-output capture harness.

Rule: a skill whose documented behavior depends on a Claude-Code-specific
tool or mode (``AskUserQuestion``, ``EnterPlanMode`` / ``ExitPlanMode``, the
``Skill`` tool, or spawning a subagent) can only be captured faithfully by
driving it inside Claude Code itself. Every other skill produces a single
text response from an LLM reading its ``SKILL.md``, so Groq's free tier is
enough.

Used by ``scripts/capture_eval.py`` to dispatch each eval to the right
backend.
"""

def runtime_for_skill(skill_name: str) -> str:
    """Return the capture runtime string ('groq' or 'claude') registered for a skill.

    Raises ``KeyError`` for unregistered skills so the harness fails loudly
    rather than silently defaulting an unclassified skill to a runtime that
    cannot capture it faithfully.
    """
    runtime_by_skill_name: dict[str, str] = {
        "pmin": "groq",
        "pmid": "groq",
        "pmax": "groq",
        "agent-prompt": "groq",
        "prompt-generator": "groq",
    }
    return runtime_by_skill_name[skill_name]


def is_groq_runtime(skill_name: str) -> bool:
    """Return ``True`` when the skill is captured via Groq."""
    return runtime_for_skill(skill_name) == "groq"


def is_claude_runtime(skill_name: str) -> bool:
    """Return ``True`` when the skill needs the Claude runtime to capture."""
    return runtime_for_skill(skill_name) == "claude"
