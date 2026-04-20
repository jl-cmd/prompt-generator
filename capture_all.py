"""Batch capture driver: iterate every registered eval and regenerate missing outputs.

Runs after ``capture_eval.py`` is trusted as the single-eval dispatcher. For
each ``(skill, eval_id)`` pair in ``EVAL_SPECS``, this driver:

1. Computes the canonical output path ``<output_dir>/eval-<skill>-<id>-output.txt``.
2. Skips the job when a real capture already lives there (see
   ``should_skip_existing_output``) so past real runs are never overwritten
   by a fresh Groq call.
3. Delegates to ``capture_eval.dispatch_capture`` otherwise, which routes
   Groq-classified skills through LiteLLM and Claude-classified skills to a
   sentinel placeholder.

CLI usage::

    python capture_all.py            # regenerate missing / sentinel files
    python capture_all.py --dry-run  # list jobs without calling any LLM
"""

import argparse
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import capture_eval
from config.eval_runner import (
    CAPTURE_INTER_REQUEST_THROTTLE_SECONDS,
    CAPTURE_MAX_RETRIES_PER_JOB,
    CAPTURE_RETRY_BACKOFF_BASE_SECONDS,
    CAPTURE_RETRY_BACKOFF_EXPONENT_BASE,
    EVAL_SPECS,
)


def iterate_eval_jobs() -> Iterator[tuple[str, int, Path]]:
    """Yield ``(skill_name, eval_id, output_path)`` for every registered eval."""
    for each_skill, each_spec_path, each_output_dir in EVAL_SPECS:
        spec_data = json.loads(Path(each_spec_path).read_text(encoding="utf-8"))
        for each_eval in spec_data.get("evals", []):
            eval_id = int(each_eval["id"])
            output_path = (
                Path(each_output_dir) / f"eval-{each_skill}-{eval_id}-output.txt"
            )
            yield each_skill, eval_id, output_path


def should_skip_existing_output(output_path: Path) -> bool:
    """Return ``True`` when the file holds a real capture worth preserving.

    A sentinel line (``SKILL_INVOCATION_SKIPPED: ...``) signals an earlier
    placeholder and should be overwritten by a real capture when possible.
    """
    if not output_path.exists():
        return False
    output_text = output_path.read_text(encoding="utf-8")
    if output_text.startswith("SKILL_INVOCATION_SKIPPED"):
        return False
    return True


def capture_one_job(skill_name: str, eval_id: int, output_path: Path) -> str:
    """Capture one eval's output and write it to ``output_path``.

    Retries up to ``MAX_RETRIES_PER_JOB`` with exponential backoff on any
    exception so Groq free-tier rate limits don't blow up a full batch.
    """
    spec_path = capture_eval.resolve_spec_path(skill_name)
    skill_md_path = capture_eval.resolve_skill_md_path(skill_name)
    eval_prompt = capture_eval.load_eval_prompt(spec_path=spec_path, eval_id=eval_id)

    last_error: Exception | None = None
    for each_attempt_index in range(CAPTURE_MAX_RETRIES_PER_JOB):
        try:
            captured_output_text = capture_eval.dispatch_capture(
                skill_name=skill_name,
                skill_md_path=skill_md_path,
                eval_prompt=eval_prompt,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(captured_output_text, encoding="utf-8")
            return captured_output_text
        except Exception as each_error:
            last_error = each_error
            sleep_seconds = CAPTURE_RETRY_BACKOFF_BASE_SECONDS * (
                CAPTURE_RETRY_BACKOFF_EXPONENT_BASE**each_attempt_index
            )
            time.sleep(sleep_seconds)
    raise RuntimeError(
        f"Capture failed after {CAPTURE_MAX_RETRIES_PER_JOB} attempts: {last_error}"
    )


def parse_command_line(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments for the batch driver."""
    parser = argparse.ArgumentParser(
        description="Capture every registered eval's output, skipping existing real captures."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List jobs that would run without invoking any LLM.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Iterate every eval job, skip existing real captures, dispatch the rest."""
    arguments = parse_command_line(argv if argv is not None else sys.argv[1:])
    captured_count = 0
    skipped_count = 0
    failed_count = 0

    for each_skill, each_eval_id, each_output_path in iterate_eval_jobs():
        if should_skip_existing_output(each_output_path):
            skipped_count += 1
            print(f"SKIP  {each_output_path} (existing real capture)")
            continue
        if arguments.dry_run:
            print(
                f"WOULD CAPTURE {each_skill} eval {each_eval_id} -> {each_output_path}"
            )
            continue
        try:
            captured_text = capture_one_job(
                skill_name=each_skill,
                eval_id=each_eval_id,
                output_path=each_output_path,
            )
        except Exception as each_error:
            failed_count += 1
            print(
                f"FAIL  {each_skill} eval {each_eval_id}: {each_error}", file=sys.stderr
            )
            continue
        captured_count += 1
        print(f"OK    {each_output_path} ({len(captured_text)} bytes)")
        time.sleep(CAPTURE_INTER_REQUEST_THROTTLE_SECONDS)

    print()
    print(f"captured={captured_count}, skipped={skipped_count}, failed={failed_count}")
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
