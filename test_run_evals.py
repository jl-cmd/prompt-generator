"""Tests for run_evals.py structured failure reasons and JSON output mode."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from run_evals import CheckResult, EvalResult, eval_result_to_dict


class TestCheckResultStructuredFields:
    """CheckResult should carry optional rule_id and offending_span for reflection."""

    def test_should_accept_rule_id_and_offending_span_as_optional_fields(self) -> None:
        check = CheckResult(
            criterion="Outcome digest present",
            verdict="FAIL",
            reason="No heading found",
            rule_id="REQUIRED_DIGEST_HEADERS",
            offending_span="## Wrong heading",
        )
        assert check.rule_id == "REQUIRED_DIGEST_HEADERS"
        assert check.offending_span == "## Wrong heading"

    def test_should_default_structured_fields_to_none_for_backward_compat(self) -> None:
        check = CheckResult(
            criterion="Some criterion",
            verdict="PASS",
            reason="Looks good",
        )
        assert check.rule_id is None
        assert check.offending_span is None


class TestEvalResultJsonSerialization:
    """EvalResult should serialize to JSON with structured failure fields."""

    def test_should_serialize_to_json_with_structured_fields(self) -> None:
        eval_result = EvalResult(
            skill="pmid",
            eval_id=1,
            eval_name="sample",
            scenario="test scenario",
        )
        eval_result.checks.append(
            CheckResult(
                criterion="Four required headers",
                verdict="FAIL",
                reason="Missing Quick sample header",
                rule_id="REQUIRED_DIGEST_HEADERS",
                offending_span="**What it does**\n**Key inputs**\n**Done when**",
            )
        )
        serialized = eval_result_to_dict(eval_result)

        assert serialized["skill"] == "pmid"
        assert serialized["eval_id"] == 1
        assert serialized["passed"] is False
        failing_check = serialized["checks"][0]
        assert failing_check["rule_id"] == "REQUIRED_DIGEST_HEADERS"
        assert failing_check["offending_span"].startswith("**What it does**")


class TestRunEvalsJsonMode:
    """run_evals.py --json should emit machine-readable output to stdout."""

    def test_should_emit_valid_json_when_json_flag_passed(self) -> None:
        repository_root = Path(__file__).parent
        process = subprocess.run(
            [sys.executable, "run_evals.py", "--json"],
            cwd=repository_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        parsed = json.loads(process.stdout)

        assert "evals" in parsed
        assert "summary" in parsed
        assert isinstance(parsed["evals"], list)
        assert "total" in parsed["summary"]
        assert "passed" in parsed["summary"]
        assert "failed" in parsed["summary"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
