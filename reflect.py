"""GEPA-inspired reflection step over eval failures.

Reads the JSON report produced by ``run_evals.py --json``, extracts every
failing check with its structured rule_id and offending_span, calls a
reflection LLM via LiteLLM, and prints a proposed edit for each failure.

Default reflection model: ``groq/llama-3.3-70b-versatile`` — free-tier
Groq endpoint. Override with the ``REFLECTION_MODEL`` environment
variable (any LiteLLM-compatible model string).

Usage:
    python run_evals.py --json > report.json
    python reflect.py report.json [--skill-path skills/pmid/SKILL.md]
"""

import argparse
import json
import os
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import litellm
from dotenv import load_dotenv

from config.eval_runner import (
    REFLECTION_CRITERION_PREVIEW_WIDTH,
    REFLECTION_MAX_TOKENS,
    REFLECTION_MODEL_DEFAULT,
    REFLECTION_SYSTEM_PROMPT,
    REPORT_SEPARATOR_WIDTH,
)


@dataclass
class ReflectionRunOutcome:
    """Summary of a reflect_on_failures run: how many failures were processed vs errored."""

    total_failures: int
    errored_count: int

load_dotenv()


def load_report(report_path: Path) -> dict:
    """Parse the JSON report emitted by run_evals.py --json."""
    return json.loads(report_path.read_text(encoding="utf-8"))


def extract_failing_checks(report_payload: dict) -> list[dict]:
    """Return one flat list of FAIL-verdict checks with skill + eval_id provenance."""
    all_failures: list[dict] = []
    for each_eval in report_payload.get("evals", []):
        for each_check in each_eval.get("checks", []):
            if each_check.get("verdict") != "FAIL":
                continue
            all_failures.append(
                {
                    "skill": each_eval["skill"],
                    "eval_id": each_eval["eval_id"],
                    "eval_name": each_eval["eval_name"],
                    "criterion": each_check["criterion"],
                    "reason": each_check["reason"],
                    "rule_id": each_check.get("rule_id"),
                    "offending_span": each_check.get("offending_span"),
                }
            )
    return all_failures


def build_reflection_prompt(failing_check: dict, skill_source: str) -> str:
    """Assemble the reflection-LLM user message for one failing check."""
    return textwrap.dedent(f"""\
        SKILL: {failing_check["skill"]}
        EVAL ID: {failing_check["eval_id"]}
        CRITERION: {failing_check["criterion"]}
        FAILURE REASON: {failing_check["reason"]}
        RULE ID: {failing_check.get("rule_id") or "(none)"}
        OFFENDING SPAN:
        {failing_check.get("offending_span") or "(none captured)"}

        CURRENT SKILL SOURCE:
        {skill_source}

        Propose the smallest edit to the skill source that would have made \
        this check pass.
    """)


def call_reflection_lm(prompt_text: str, model_name: str) -> str:
    """Call the reflection LLM via LiteLLM and return its text response."""
    completion_payload = litellm.completion(
        model=model_name,
        max_tokens=REFLECTION_MAX_TOKENS,
        messages=[
            {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ],
    )
    return completion_payload["choices"][0]["message"]["content"]


def resolve_skill_source_path(
    failing_check: dict, from_override: Optional[Path]
) -> Path:
    """Resolve which skill source file to feed into the reflection prompt.

    Rejects skill names containing path separators or parent-directory segments
    so a hostile JSON report cannot traverse outside the ``skills/`` directory.
    """
    if from_override is not None:
        return from_override
    skill_name = failing_check["skill"]
    if "/" in skill_name or "\\" in skill_name or ".." in skill_name.split("/") or skill_name in ("", ".", ".."):
        raise ValueError(
            f"Refusing to resolve skill source path for unsafe skill name: {skill_name!r}"
        )
    return Path("skills") / skill_name / "SKILL.md"


def reflect_on_failures(
    report_path: Path,
    skill_path_override: Optional[Path] = None,
    model_name: str = REFLECTION_MODEL_DEFAULT,
) -> ReflectionRunOutcome:
    """Run reflection on every failure in the report.

    Returns a :class:`ReflectionRunOutcome` with the total number of failing
    checks found and how many of those raised during the reflection call, so
    the CLI entry point can surface a non-zero exit code when every call
    failed (rate limits, auth, network outage) rather than silently succeeding.
    """
    report_payload = load_report(report_path)
    all_failures = extract_failing_checks(report_payload)

    if not all_failures:
        print("No failing checks found in report. Nothing to reflect on.")
        return ReflectionRunOutcome(total_failures=0, errored_count=0)

    separator_line = "=" * REPORT_SEPARATOR_WIDTH
    errored_count = 0
    for each_index, each_failure in enumerate(all_failures, start=1):
        skill_source_path = resolve_skill_source_path(each_failure, skill_path_override)
        if not skill_source_path.exists():
            print(
                f"WARN: skill source not found at {skill_source_path}; "
                f"skipping failure {each_index}",
                file=sys.stderr,
            )
            errored_count += 1
            continue

        skill_source_text = skill_source_path.read_text(encoding="utf-8")
        prompt_text = build_reflection_prompt(each_failure, skill_source_text)

        criterion_preview = each_failure["criterion"][:REFLECTION_CRITERION_PREVIEW_WIDTH]
        print(f"\n{separator_line}")
        print(
            f"Failure {each_index}/{len(all_failures)}: "
            f"[{each_failure['skill']}] eval {each_failure['eval_id']} — "
            f"{criterion_preview}"
        )
        print(separator_line)

        try:
            reflection_text = call_reflection_lm(prompt_text, model_name)
        except Exception as each_error:
            print(f"Reflection call failed: {each_error}", file=sys.stderr)
            errored_count += 1
            continue

        print(reflection_text)

    return ReflectionRunOutcome(
        total_failures=len(all_failures), errored_count=errored_count
    )


def parse_command_line(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments for the reflection script."""
    parser = argparse.ArgumentParser(
        description="Reflect on eval failures and propose skill-source edits."
    )
    parser.add_argument(
        "report_path",
        type=Path,
        help="Path to the JSON report produced by run_evals.py --json",
    )
    parser.add_argument(
        "--skill-path",
        type=Path,
        default=None,
        help="Override skill source path (default: skills/<skill>/SKILL.md)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("REFLECTION_MODEL", REFLECTION_MODEL_DEFAULT),
        help=f"LiteLLM model string (default: {REFLECTION_MODEL_DEFAULT})",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point: parse args and run reflection.

    Returns 0 when every failure was reflected on without error. Returns 1
    when any reflection call or skill-source lookup failed, so CI callers
    can distinguish a clean run from one where the underlying LLM rejected
    every request (auth error, rate limit, network outage).
    """
    arguments = parse_command_line(argv if argv is not None else sys.argv[1:])
    outcome = reflect_on_failures(
        report_path=arguments.report_path,
        skill_path_override=arguments.skill_path,
        model_name=arguments.model,
    )
    if outcome.errored_count > 0:
        print(
            f"ERROR: {outcome.errored_count}/{outcome.total_failures} "
            f"reflections failed; see stderr for details.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
