"""Dual-runtime capture harness for skill-eval outputs.

Dispatches each ``(skill, eval_id)`` to the runtime registered for that skill
in ``config.capture_runtime``:

- Skills whose behavior is single-turn text (e.g. ``pmin``, ``pmid``) are
  captured via Groq's free-tier Llama through LiteLLM — same client
  ``reflect.py`` already uses, zero new dependencies.
- Skills that lean on ``AskUserQuestion``, plan mode, or subagent spawns
  (e.g. ``pmax``, ``agent-prompt``, ``prompt-generator``) cannot be driven
  faithfully outside Claude Code, so they return a sentinel placeholder
  that the runner judges as FAIL until a Claude-Code-based harness
  overwrites the file with a real capture.

CLI usage::

    python capture_eval.py <skill> <eval_id> <output_path>
"""

import argparse
import json
import sys
import textwrap
from pathlib import Path

import litellm
from dotenv import load_dotenv

from config.capture_runtime import is_claude_runtime, is_groq_runtime
from config.eval_runner import GROQ_CAPTURE_MAX_TOKENS, REFLECTION_MODEL_DEFAULT

load_dotenv()


def load_eval_prompt(spec_path: Path, eval_id: int) -> str:
    """Return the ``prompt`` field for one eval inside a skill's spec JSON."""
    spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
    for each_eval in spec_data.get("evals", []):
        if each_eval.get("id") == eval_id:
            return each_eval.get("prompt", "")
    raise LookupError(f"No eval with id={eval_id} in {spec_path}")


def capture_via_groq(skill_md_path: Path, eval_prompt: str) -> str:
    """Call Groq-hosted Llama with the skill body as system + eval prompt as user."""
    groq_capture_max_tokens = GROQ_CAPTURE_MAX_TOKENS
    skill_body_text = skill_md_path.read_text(encoding="utf-8")
    system_prompt_text = textwrap.dedent(f"""\
        You are running this Claude Code skill. Follow the SKILL.md instructions
        below exactly and produce the output the skill is documented to produce.

        SKILL.md:
        {skill_body_text}
    """)
    completion_payload = litellm.completion(
        model=REFLECTION_MODEL_DEFAULT,
        max_tokens=groq_capture_max_tokens,
        messages=[
            {"role": "system", "content": system_prompt_text},
            {"role": "user", "content": eval_prompt},
        ],
    )
    return completion_payload["choices"][0]["message"]["content"]


def dispatch_capture(skill_name: str, skill_md_path: Path, eval_prompt: str) -> str:
    """Route a single eval to the runtime registered for its skill."""
    claude_runtime_skip_sentinel = (
        "SKILL_INVOCATION_SKIPPED: claude runtime required "
        "(skill uses AskUserQuestion or another Claude-Code-specific feature)"
    )
    if is_groq_runtime(skill_name):
        return capture_via_groq(skill_md_path=skill_md_path, eval_prompt=eval_prompt)
    if is_claude_runtime(skill_name):
        return claude_runtime_skip_sentinel
    raise ValueError(f"Unknown runtime for skill {skill_name!r}")


def resolve_skill_md_path(skill_name: str) -> Path:
    """Return the canonical ``skills/<skill>/SKILL.md`` path for a skill name."""
    return Path("skills") / skill_name / "SKILL.md"


def resolve_spec_path(skill_name: str) -> Path:
    """Return the canonical eval-spec path for a skill name."""
    return Path("skills") / skill_name / "evals" / f"{skill_name}.json"


def parse_command_line(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments for one-eval capture."""
    parser = argparse.ArgumentParser(
        description="Capture one skill-eval output via the registered runtime."
    )
    parser.add_argument("skill", type=str, help="Skill name (e.g. pmin, pmax)")
    parser.add_argument(
        "eval_id", type=int, help="Eval id inside the skill's spec JSON"
    )
    parser.add_argument(
        "output_path", type=Path, help="Destination file for the captured output"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Capture one eval and write the result to the destination path."""
    arguments = parse_command_line(argv if argv is not None else sys.argv[1:])
    spec_path = resolve_spec_path(arguments.skill)
    skill_md_path = resolve_skill_md_path(arguments.skill)
    eval_prompt = load_eval_prompt(spec_path=spec_path, eval_id=arguments.eval_id)
    captured_output_text = dispatch_capture(
        skill_name=arguments.skill,
        skill_md_path=skill_md_path,
        eval_prompt=eval_prompt,
    )
    arguments.output_path.write_text(captured_output_text, encoding="utf-8")
    print(
        f"Captured {arguments.skill} eval {arguments.eval_id} "
        f"({len(captured_output_text)} bytes) to {arguments.output_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
