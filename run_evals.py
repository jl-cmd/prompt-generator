"""Automated eval runner for pmid and pmin skills.

Loads eval JSON specs from skills/{skill}/evals/{skill}.json, reads the
corresponding output from data/prompts/eval-{skill}-{id}-output.txt, runs
deterministic structural checks, and optionally runs an LLM judge for
semantic criteria when ANTHROPIC_API_KEY is present.

Exit code: 0 = all evals pass, 1 = one or more evals fail.
"""

import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic as _anthropic
except ImportError:
    _anthropic = None  # type: ignore[assignment]

try:
    import openai as _openai
except ImportError:
    _openai = None  # type: ignore[assignment]

from config.eval_runner import (
    ANSI_RESET,
    DETERMINISTIC_COVERED_PATTERNS,
    EVAL_SPECS,
    GROQ_BASE_URL,
    GROQ_JUDGE_MODEL,
    JSON_REPORT_INDENT,
    LLM_JUDGE_MAX_TOKENS,
    LLM_JUDGE_MODEL,
    LLM_JUDGE_OUTPUT_CHAR_LIMIT,
    LLM_JUDGE_SYSTEM_PROMPT,
    NESTED_BACKTICK_PATTERN,
    OUTCOME_DIGEST_HEADING,
    OUTCOME_DIGEST_PATTERN,
    PROCESS_ONLY_PATTERNS,
    PROSE_AUTHOR_PHRASES,
    REPORT_SEPARATOR_WIDTH,
    REQUIRED_DIGEST_HEADERS,
    VERDICT_COLORS,
    VERDICT_ICONS,
    XML_FENCE_CLOSE,
    XML_FENCE_OPEN_PATTERN,
    XML_FENCE_OPEN_PREFIXES,
)

Verdict = Literal["PASS", "FAIL", "SKIP"]


@dataclass
class CheckResult:
    criterion: str
    verdict: Verdict
    reason: str
    rule_id: Optional[str] = None
    offending_span: Optional[str] = None


@dataclass
class EvalResult:
    skill: str
    eval_id: int
    eval_name: str
    scenario: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.verdict in ("PASS", "SKIP") for check in self.checks)

    @property
    def fail_count(self) -> int:
        return sum(1 for check in self.checks if check.verdict == "FAIL")


# ---------------------------------------------------------------------------
# Structural (deterministic) checks
# ---------------------------------------------------------------------------


def check_zero_prose_before_fence(text: str) -> CheckResult:
    """Zero prose before the opening xml fence."""
    criterion = "Zero prose before the opening xml fence"
    all_lines = text.splitlines()
    for each_line_index, each_line in enumerate(all_lines):
        stripped = each_line.strip()
        if any(stripped.startswith(p) for p in XML_FENCE_OPEN_PREFIXES):
            if each_line_index == 0:
                return CheckResult(criterion, "PASS", "Fence opens on first line")
            pre = "\n".join(all_lines[:each_line_index]).strip()
            if pre:
                return CheckResult(
                    criterion, "FAIL", f"Found prose before fence: {pre[:80]!r}"
                )
            return CheckResult(criterion, "PASS", "No prose before fence")
    return CheckResult(criterion, "FAIL", "No xml fence found in output")


def check_exactly_one_xml_fence(text: str) -> CheckResult:
    """Exactly one xml fence opening present."""
    criterion = "Exactly one xml fence present"
    open_count = sum(
        1
        for each_line in text.splitlines()
        if any(each_line.strip().startswith(p) for p in XML_FENCE_OPEN_PREFIXES)
    )
    if open_count == 0:
        return CheckResult(criterion, "FAIL", "No xml fence opening found")
    if open_count > 1:
        return CheckResult(
            criterion, "FAIL", f"Found {open_count} xml fence openings; expected 1"
        )
    return CheckResult(criterion, "PASS", "Exactly one xml fence opening found")


def check_zero_prose_between_fence_and_digest(text: str) -> CheckResult:
    """Zero prose between the closing xml fence and ## Outcome digest."""
    criterion = "Zero prose between closing fence and ## Outcome digest"
    all_lines = text.splitlines()

    fence_close_index: int | None = None
    in_xml_fence = False
    for each_line_index, each_line in enumerate(all_lines):
        stripped = each_line.strip()
        if any(stripped.startswith(p) for p in XML_FENCE_OPEN_PREFIXES):
            in_xml_fence = True
        elif in_xml_fence and stripped == XML_FENCE_CLOSE:
            fence_close_index = each_line_index
            in_xml_fence = False

    if fence_close_index is None:
        return CheckResult(criterion, "FAIL", "No closing fence found")

    for each_line_index in range(fence_close_index + 1, len(all_lines)):
        stripped = all_lines[each_line_index].strip()
        if stripped.startswith(OUTCOME_DIGEST_HEADING):
            if each_line_index == fence_close_index + 1:
                return CheckResult(
                    criterion, "PASS", "Digest follows immediately after fence"
                )
            between = "\n".join(all_lines[fence_close_index + 1 : each_line_index]).strip()
            if between:
                return CheckResult(
                    criterion,
                    "FAIL",
                    f"Found prose between fence and digest: {between[:80]!r}",
                )
            return CheckResult(
                criterion, "PASS", "Only blank lines between fence and digest"
            )

    return CheckResult(
        criterion, "FAIL", "No '## Outcome digest' section found after fence"
    )


def check_outcome_digest_present(text: str) -> CheckResult:
    """## Outcome digest section is present."""
    criterion = "## Outcome digest section present"
    if OUTCOME_DIGEST_HEADING in text:
        return CheckResult(criterion, "PASS", "Digest heading found")
    return CheckResult(criterion, "FAIL", "No '## Outcome digest' heading found")


def check_four_required_digest_headers(text: str) -> CheckResult:
    """All four required bold headers present in correct order."""
    criterion = "Four required bold headers in order: What it does, Key inputs, Done when, Quick sample"
    digest_match = OUTCOME_DIGEST_PATTERN.search(text)
    if not digest_match:
        return CheckResult(criterion, "FAIL", "No Outcome digest section found")

    digest_body = digest_match.group(1)
    positions = []
    for header in REQUIRED_DIGEST_HEADERS:
        position = digest_body.find(header)
        if position == -1:
            return CheckResult(criterion, "FAIL", f"Missing required header: {header}")
        positions.append(position)

    if positions != sorted(positions):
        return CheckResult(
            criterion, "FAIL", "Headers present but not in required order"
        )

    return CheckResult(criterion, "PASS", "All four headers present in correct order")


def check_each_header_has_content(text: str) -> CheckResult:
    """Each required header is followed by at least one sentence of content."""
    criterion = "Each required header followed by substantive content"
    digest_match = OUTCOME_DIGEST_PATTERN.search(text)
    if not digest_match:
        return CheckResult(criterion, "SKIP", "No Outcome digest section to check")

    digest_body = digest_match.group(1)
    for index, header in enumerate(REQUIRED_DIGEST_HEADERS):
        header_position = digest_body.find(header)
        if header_position == -1:
            return CheckResult(
                criterion,
                "SKIP",
                f"Header {header} missing — checked by another criterion",
            )

        # Content may appear on the same line as the header or on subsequent lines
        header_token_end = header_position + len(header)
        line_end = digest_body.find("\n", header_token_end)
        if line_end == -1:
            line_end = len(digest_body)

        next_header_position = len(digest_body)
        for other_header in REQUIRED_DIGEST_HEADERS[index + 1 :]:
            position = digest_body.find(other_header, header_position + 1)
            if position != -1:
                next_header_position = min(next_header_position, position)

        same_line_content = digest_body[header_token_end:line_end].strip()
        subsequent_content = digest_body[line_end:next_header_position].strip()
        if not same_line_content and not subsequent_content:
            return CheckResult(
                criterion, "FAIL", f"Header {header} has no following content"
            )

    return CheckResult(criterion, "PASS", "All headers have substantive content")


def check_no_second_xml_fence_in_digest(text: str) -> CheckResult:
    """No second xml fence inside the Outcome digest section."""
    criterion = "No second xml fence inside Outcome digest"
    digest_match = OUTCOME_DIGEST_PATTERN.search(text)
    if not digest_match:
        return CheckResult(criterion, "SKIP", "No Outcome digest section to check")

    digest_body = digest_match.group(1)
    if XML_FENCE_OPEN_PATTERN.search(digest_body):
        return CheckResult(
            criterion, "FAIL", "Found a second xml fence inside Outcome digest"
        )
    return CheckResult(criterion, "PASS", "No second xml fence inside digest")


def check_zero_prose_after_digest(text: str) -> CheckResult:
    """Zero trailing prose after the final content of Outcome digest."""
    criterion = "Zero prose after the final content of Outcome digest"
    digest_match = OUTCOME_DIGEST_PATTERN.search(text)
    if not digest_match:
        return CheckResult(criterion, "SKIP", "No Outcome digest section to check")

    digest_body = digest_match.group(1).rstrip()
    present_header_positions = [
        digest_body.rfind(header)
        for header in REQUIRED_DIGEST_HEADERS
        if header in digest_body
    ]
    if not present_header_positions:
        return CheckResult(
            criterion,
            "SKIP",
            "Required headers not found — checked by another criterion",
        )

    last_header_position = max(present_header_positions)
    trailing = digest_body[last_header_position:].rstrip()
    if not trailing:
        return CheckResult(
            criterion, "FAIL", "Digest ends at last header with no content"
        )

    return CheckResult(criterion, "PASS", "Digest ends with content after last header")


def check_digest_not_a_table(text: str) -> CheckResult:
    """Outcome digest uses bullet sections, not a bare markdown table."""
    criterion = "Outcome digest uses bullet sections, not a bare markdown table"
    digest_match = OUTCOME_DIGEST_PATTERN.search(text)
    if not digest_match:
        return CheckResult(criterion, "SKIP", "No Outcome digest section to check")

    digest_body = digest_match.group(1)
    has_table_header = bool(
        re.search(r"^\|\s*\w.*\|\s*\w.*\|", digest_body, re.MULTILINE)
    )
    has_table_divider = bool(re.search(r"^\|[\s\-|]+\|", digest_body, re.MULTILINE))

    if has_table_header and has_table_divider:
        has_required_headers = all(
            header in digest_body for header in REQUIRED_DIGEST_HEADERS
        )
        if not has_required_headers:
            return CheckResult(
                criterion,
                "FAIL",
                "Digest appears to be a markdown table without the four required bullet sections",
            )

    return CheckResult(
        criterion, "PASS", "Digest uses bullet format, not a bare markdown table"
    )


def check_no_nested_backtick_fences_in_xml(text: str) -> CheckResult:
    """No triple-backtick code fences appear inside the xml fence content."""
    criterion = "No triple-backtick code fences inside the xml fence"
    all_lines = text.splitlines()

    open_index: int | None = None
    for each_line_index, each_line in enumerate(all_lines):
        stripped = each_line.strip()
        if any(stripped.startswith(p) for p in XML_FENCE_OPEN_PREFIXES):
            open_index = each_line_index
            break

    if open_index is None:
        return CheckResult(criterion, "SKIP", "No xml fence found — checked by another criterion")

    digest_index: int | None = None
    for each_line_index, each_line in enumerate(all_lines):
        if each_line.strip().startswith(OUTCOME_DIGEST_HEADING):
            digest_index = each_line_index
            break

    if digest_index is None:
        return CheckResult(criterion, "SKIP", "No Outcome digest found — checked by another criterion")

    close_index: int | None = None
    for each_line_index in range(digest_index - 1, open_index, -1):
        if all_lines[each_line_index].strip() == XML_FENCE_CLOSE:
            close_index = each_line_index
            break

    if close_index is None:
        return CheckResult(criterion, "FAIL", "No closing fence found before Outcome digest")

    nested_line_numbers = [
        each_line_index + 1
        for each_line_index in range(open_index + 1, close_index)
        if NESTED_BACKTICK_PATTERN.match(all_lines[each_line_index].strip())
    ]
    if nested_line_numbers:
        return CheckResult(
            criterion,
            "FAIL",
            f"Found nested backtick fence(s) at line(s) {nested_line_numbers} inside the xml fence",
        )

    return CheckResult(criterion, "PASS", "No nested backtick fences inside the xml fence")


def check_quick_sample_no_authoring_phrases(text: str) -> CheckResult:
    """Quick sample contains zero prompt-authoring phrases."""
    criterion = "Quick sample contains zero prompt-authoring phrases"
    digest_match = OUTCOME_DIGEST_PATTERN.search(text)
    if not digest_match:
        return CheckResult(criterion, "SKIP", "No Outcome digest section to check")

    digest_body = digest_match.group(1).lower()
    quick_sample_position = digest_body.find("**quick sample**")
    if quick_sample_position == -1:
        return CheckResult(criterion, "SKIP", "**Quick sample** header not found")

    quick_sample_body = digest_body[quick_sample_position:]
    found_phrases = [
        phrase for phrase in PROSE_AUTHOR_PHRASES if phrase.lower() in quick_sample_body
    ]
    if found_phrases:
        return CheckResult(
            criterion,
            "FAIL",
            f"Found authoring phrase(s) in Quick sample: {found_phrases}",
        )
    return CheckResult(criterion, "PASS", "No authoring phrases found in Quick sample")


def run_structural_checks(output_text: str) -> list[CheckResult]:
    """Run all deterministic structural checks against one output."""
    return [
        check_zero_prose_before_fence(output_text),
        check_exactly_one_xml_fence(output_text),
        check_zero_prose_between_fence_and_digest(output_text),
        check_outcome_digest_present(output_text),
        check_four_required_digest_headers(output_text),
        check_each_header_has_content(output_text),
        check_no_second_xml_fence_in_digest(output_text),
        check_no_nested_backtick_fences_in_xml(output_text),
        check_zero_prose_after_digest(output_text),
        check_digest_not_a_table(output_text),
        check_quick_sample_no_authoring_phrases(output_text),
    ]


# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------


def _build_judge_messages(criterion: str, output_text: str) -> tuple[str, str]:
    """Return (system_prompt, user_message) for the LLM judge."""
    user_message = textwrap.dedent(f"""\
        CRITERION:
        {criterion}

        OUTPUT TO EVALUATE:
        {output_text[:LLM_JUDGE_OUTPUT_CHAR_LIMIT]}
    """)
    return LLM_JUDGE_SYSTEM_PROMPT, user_message


def _call_groq_judge(output_text: str, criterion: str) -> Optional[CheckResult]:
    """Call Groq as judge. Returns None when Groq is unavailable."""
    if _openai is None:
        return None
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None

    system_prompt, user_message = _build_judge_messages(criterion, output_text)
    client = _openai.OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    try:
        response = client.chat.completions.create(
            model=GROQ_JUDGE_MODEL,
            max_tokens=LLM_JUDGE_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
    except Exception:
        return None
    raw = response.choices[0].message.content.strip()
    parsed = json.loads(raw)
    return CheckResult(criterion, parsed["verdict"], parsed["reason"])


def _call_anthropic_judge(output_text: str, criterion: str) -> Optional[CheckResult]:
    """Call Anthropic as judge. Returns None when Anthropic is unavailable."""
    if _anthropic is None:
        return None
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    system_prompt, user_message = _build_judge_messages(criterion, output_text)
    client = _anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=LLM_JUDGE_MODEL,
        max_tokens=LLM_JUDGE_MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    raw = response.content[0].text.strip()
    parsed = json.loads(raw)
    return CheckResult(criterion, parsed["verdict"], parsed["reason"])


def _call_llm_judge(output_text: str, criterion: str) -> CheckResult:
    """Call the best available judge: Groq first, Anthropic as fallback.

    Returns SKIP when neither provider is configured.
    """
    result = _call_groq_judge(output_text, criterion)
    if result is not None:
        return result
    result = _call_anthropic_judge(output_text, criterion)
    if result is not None:
        return result
    return CheckResult(
        criterion,
        "SKIP",
        "No LLM judge available (set GROQ_API_KEY or ANTHROPIC_API_KEY)",
    )


def grade_criterion(output_text: str, criterion: str) -> CheckResult:
    """Route one criterion: SKIP if process-only or structurally covered, else LLM judge."""
    criterion_lower = criterion.lower()
    for pattern in PROCESS_ONLY_PATTERNS:
        if pattern.lower() in criterion_lower:
            return CheckResult(
                criterion,
                "SKIP",
                "Process criterion: verifiable only via live session capture, not from saved output",
            )
    for pattern in DETERMINISTIC_COVERED_PATTERNS:
        if pattern.lower() in criterion_lower:
            return CheckResult(
                criterion,
                "SKIP",
                "Criterion covered by deterministic structural check",
            )
    return _call_llm_judge(output_text, criterion)


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------


def load_eval_spec(spec_path: Path) -> dict:
    """Load and return a parsed eval spec JSON file."""
    with open(spec_path) as file:
        return json.load(file)


def load_output(output_dir: Path, skill: str, eval_id: int) -> Optional[str]:
    """Load the saved output file for one eval, or return None if absent."""
    output_path = output_dir / f"eval-{skill}-{eval_id}-output.txt"
    if not output_path.exists():
        return None
    return output_path.read_text(encoding="utf-8")


def run_eval(skill: str, eval_spec: dict, output_dir: Path) -> EvalResult:
    """Grade one eval against its output file and return the full result."""
    eval_id: int = eval_spec["id"]
    result = EvalResult(
        skill=skill,
        eval_id=eval_id,
        eval_name=eval_spec["name"],
        scenario=eval_spec.get("scenario", ""),
    )

    output_text = load_output(output_dir, skill, eval_id)
    if output_text is None:
        result.checks.append(
            CheckResult(
                criterion="Output file exists",
                verdict="FAIL",
                reason=f"File data/prompts/eval-{skill}-{eval_id}-output.txt not found",
            )
        )
        return result

    result.checks.extend(run_structural_checks(output_text))

    for criterion in eval_spec.get("expected_behavior", []):
        result.checks.append(grade_criterion(output_text, criterion))

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _colored(verdict: str, text: str) -> str:
    """Wrap text in the ANSI color for the given verdict when writing to a terminal."""
    if not sys.stdout.isatty():
        return text
    color = VERDICT_COLORS.get(verdict, "")
    return f"{color}{text}{ANSI_RESET}"


def print_report(all_results: list[EvalResult]) -> None:
    """Print the full eval report to stdout."""
    total_evals = len(all_results)
    passed_evals = sum(1 for result in all_results if result.passed)
    failed_evals = total_evals - passed_evals

    separator = "=" * REPORT_SEPARATOR_WIDTH
    print()
    print(separator)
    print("  EVAL RESULTS")
    print(separator)

    for result in all_results:
        status = "PASS" if result.passed else "FAIL"
        icon = VERDICT_ICONS[status]
        header_line = (
            f"\n{_colored(status, icon)} [{result.skill.upper()}] eval {result.eval_id}:"
            f" {result.eval_name}"
        )
        print(header_line)
        if result.scenario:
            print(f"   Scenario: {result.scenario}")

        for check in result.checks:
            icon_char = VERDICT_ICONS.get(check.verdict, "?")
            colored_icon = _colored(check.verdict, icon_char)
            short_criterion = check.criterion[:60] + (
                "…" if len(check.criterion) > 60 else ""
            )
            print(f"   {colored_icon}  {short_criterion}")
            if check.verdict == "FAIL":
                print(f"      → {check.reason}")

    print()
    print(separator)
    summary_line = f"  {passed_evals}/{total_evals} evals passed"
    if failed_evals:
        print(_colored("FAIL", summary_line))
    else:
        print(_colored("PASS", summary_line))
    print(separator)
    print()


# ---------------------------------------------------------------------------
# JSON serialization for reflection pipeline
# ---------------------------------------------------------------------------


def check_result_to_dict(check: CheckResult) -> dict:
    """Serialize a CheckResult to a JSON-safe dict, including structured fields."""
    return {
        "criterion": check.criterion,
        "verdict": check.verdict,
        "reason": check.reason,
        "rule_id": check.rule_id,
        "offending_span": check.offending_span,
    }


def eval_result_to_dict(eval_outcome: EvalResult) -> dict:
    """Serialize an EvalResult (with all checks) to a JSON-safe dict."""
    return {
        "skill": eval_outcome.skill,
        "eval_id": eval_outcome.eval_id,
        "eval_name": eval_outcome.eval_name,
        "scenario": eval_outcome.scenario,
        "passed": eval_outcome.passed,
        "fail_count": eval_outcome.fail_count,
        "checks": [check_result_to_dict(check) for check in eval_outcome.checks],
    }


def build_json_report(all_results: list[EvalResult]) -> dict:
    """Build the full JSON report shape for --json output mode."""
    total_evals = len(all_results)
    passed_evals = sum(1 for each_outcome in all_results if each_outcome.passed)
    return {
        "evals": [eval_result_to_dict(each_outcome) for each_outcome in all_results],
        "summary": {
            "total": total_evals,
            "passed": passed_evals,
            "failed": total_evals - passed_evals,
        },
    }


def collect_all_results() -> Optional[list[EvalResult]]:
    """Run every configured eval and return the full list of results.

    Returns ``None`` when any configured spec file is missing, matching the
    abort-on-missing-spec behavior of the text-mode branch so ``--json``
    consumers never receive a silently-truncated report.
    """
    all_results: list[EvalResult] = []
    for skill, spec_path, output_dir in EVAL_SPECS:
        if not spec_path.exists():
            print(f"ERROR: Eval spec not found: {spec_path}", file=sys.stderr)
            return None
        spec = load_eval_spec(spec_path)
        for eval_spec in spec["evals"]:
            each_outcome = run_eval(skill, eval_spec, output_dir)
            all_results.append(each_outcome)
    return all_results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all evals and return 0 on full pass, 1 on any failure."""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined] # reason: reconfigure is a runtime-only method not in the TextIO stub
    is_json_mode = "--json" in sys.argv[1:]

    if is_json_mode:
        collected_results = collect_all_results()
        if collected_results is None:
            return 1
        report_payload = build_json_report(collected_results)
        print(json.dumps(report_payload, indent=JSON_REPORT_INDENT))
        has_failures = any(not each_outcome.passed for each_outcome in collected_results)
        return 1 if has_failures else 0

    all_results = []
    for skill, spec_path, output_dir in EVAL_SPECS:
        if not spec_path.exists():
            print(f"ERROR: Eval spec not found: {spec_path}", file=sys.stderr)
            return 1

        spec = load_eval_spec(spec_path)
        print(f"\nRunning {len(spec['evals'])} evals for skill: {skill}")

        for eval_spec in spec["evals"]:
            each_outcome = run_eval(skill, eval_spec, output_dir)
            all_results.append(each_outcome)
            status = "PASS" if each_outcome.passed else "FAIL"
            print(f"  [{status}] {eval_spec['id']}: {eval_spec['name']}")

    print_report(all_results)

    has_failures = any(not each_outcome.passed for each_outcome in all_results)
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
