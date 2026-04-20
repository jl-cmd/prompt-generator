"""Tests for reflect.py — the GEPA-inspired reflection step on eval failures."""

import json
from pathlib import Path

import pytest

from reflect import (
    build_reflection_prompt,
    extract_failing_checks,
    load_report,
)


class TestLoadReport:
    """load_report parses the JSON output produced by run_evals.py --json."""

    def test_should_parse_valid_report_from_path(self, tmp_path: Path) -> None:
        report_path = tmp_path / "report.json"
        report_payload = {
            "evals": [],
            "summary": {"total": 0, "passed": 0, "failed": 0},
        }
        report_path.write_text(json.dumps(report_payload), encoding="utf-8")

        loaded = load_report(report_path)

        assert loaded["summary"]["total"] == 0


class TestExtractFailingChecks:
    """extract_failing_checks returns only FAIL-verdict checks with provenance."""

    def test_should_return_only_failing_checks_with_skill_and_eval_id(self) -> None:
        report_payload = {
            "evals": [
                {
                    "skill": "pmid",
                    "eval_id": 1,
                    "eval_name": "sample",
                    "scenario": "s",
                    "passed": False,
                    "fail_count": 1,
                    "checks": [
                        {
                            "criterion": "A",
                            "verdict": "PASS",
                            "reason": "ok",
                            "rule_id": None,
                            "offending_span": None,
                        },
                        {
                            "criterion": "B",
                            "verdict": "FAIL",
                            "reason": "missing thing",
                            "rule_id": "RULE_B",
                            "offending_span": "bad text",
                        },
                    ],
                },
            ],
            "summary": {"total": 1, "passed": 0, "failed": 1},
        }

        failing = extract_failing_checks(report_payload)

        assert len(failing) == 1
        only_failure = failing[0]
        assert only_failure["skill"] == "pmid"
        assert only_failure["eval_id"] == 1
        assert only_failure["criterion"] == "B"
        assert only_failure["rule_id"] == "RULE_B"


class TestBuildReflectionPrompt:
    """build_reflection_prompt produces a prompt referencing failure context."""

    def test_should_include_criterion_and_reason_in_prompt(self) -> None:
        failing_check = {
            "skill": "pmid",
            "eval_id": 7,
            "criterion": "Four required headers",
            "reason": "Missing Quick sample header",
            "rule_id": "REQUIRED_DIGEST_HEADERS",
            "offending_span": "**What it does**\n**Key inputs**",
        }

        prompt_text = build_reflection_prompt(
            failing_check, skill_source="SKILL content here"
        )

        assert "Four required headers" in prompt_text
        assert "Missing Quick sample header" in prompt_text
        assert "REQUIRED_DIGEST_HEADERS" in prompt_text
        assert "SKILL content here" in prompt_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
