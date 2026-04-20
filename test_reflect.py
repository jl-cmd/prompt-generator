"""Tests for reflect.py — the GEPA-inspired reflection step on eval failures."""

import json
from pathlib import Path

import pytest

import reflect
from reflect import (
    build_reflection_prompt,
    extract_failing_checks,
    load_report,
)

from config.eval_runner import REFLECTION_SYSTEM_PROMPT


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


class TestBuildReflectionPromptReinforcesNoEditOption:
    """User message restates the NO EDIT escape hatch close to the data."""

    def test_should_mention_no_edit_option_in_user_message(self) -> None:
        failing_check = {
            "skill": "pmid",
            "eval_id": 1,
            "criterion": "crit",
            "reason": "r",
            "rule_id": None,
            "offending_span": None,
        }
        prompt_text = build_reflection_prompt(failing_check, skill_source="body")
        assert "NO EDIT" in prompt_text


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


class TestReflectUsesHardenedSystemPrompt:
    """reflect.py must send the anti-hallucination system prompt from config."""

    def test_call_reflection_lm_should_send_hardened_system_prompt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured_messages: list[dict] = []

        def fake_completion(**kwargs: object) -> dict:
            captured_messages.extend(kwargs["messages"])
            return {"choices": [{"message": {"content": "ok"}}]}

        monkeypatch.setattr(reflect.litellm, "completion", fake_completion)

        reflect.call_reflection_lm("user prompt body", model_name="groq/test")

        system_message = next(each for each in captured_messages if each["role"] == "system")
        assert system_message["content"] == REFLECTION_SYSTEM_PROMPT


class TestResolveSkillSourcePathRejectsTraversal:
    """resolve_skill_source_path must reject skill names containing path separators."""

    def test_should_raise_when_skill_contains_parent_directory_segment(self) -> None:
        failing_check = {"skill": "../../etc/passwd"}
        with pytest.raises(ValueError):
            reflect.resolve_skill_source_path(failing_check, from_override=None)

    def test_should_raise_when_skill_contains_forward_slash(self) -> None:
        failing_check = {"skill": "pmid/evil"}
        with pytest.raises(ValueError):
            reflect.resolve_skill_source_path(failing_check, from_override=None)

    def test_should_raise_when_skill_contains_backslash(self) -> None:
        failing_check = {"skill": "pmid\\evil"}
        with pytest.raises(ValueError):
            reflect.resolve_skill_source_path(failing_check, from_override=None)

    def test_should_allow_simple_skill_name(self) -> None:
        failing_check = {"skill": "pmid"}
        resolved = reflect.resolve_skill_source_path(failing_check, from_override=None)
        assert resolved == Path("skills") / "pmid" / "SKILL.md"


class TestReflectOnFailuresReportsErrors:
    """reflect_on_failures must return a processed/errored tuple so main can signal."""

    def test_should_count_reflection_call_errors(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        report_path = tmp_path / "report.json"
        report_path.write_text(
            json.dumps(
                {
                    "evals": [
                        {
                            "skill": "pmid",
                            "eval_id": 1,
                            "eval_name": "n",
                            "checks": [
                                {
                                    "criterion": "c",
                                    "verdict": "FAIL",
                                    "reason": "r",
                                    "rule_id": None,
                                    "offending_span": None,
                                }
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        skill_source = tmp_path / "SKILL.md"
        skill_source.write_text("skill source body", encoding="utf-8")

        def always_fail(prompt_text: str, model_name: str) -> str:
            raise RuntimeError("boom")

        monkeypatch.setattr(reflect, "call_reflection_lm", always_fail)

        outcome = reflect.reflect_on_failures(
            report_path=report_path, skill_path_override=skill_source
        )

        assert outcome.total_failures == 1
        assert outcome.errored_count == 1

    def test_main_should_return_nonzero_when_every_reflection_errors(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        report_path = tmp_path / "report.json"
        report_path.write_text(
            json.dumps(
                {
                    "evals": [
                        {
                            "skill": "pmid",
                            "eval_id": 1,
                            "eval_name": "n",
                            "checks": [
                                {
                                    "criterion": "c",
                                    "verdict": "FAIL",
                                    "reason": "r",
                                    "rule_id": None,
                                    "offending_span": None,
                                }
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        skill_source = tmp_path / "SKILL.md"
        skill_source.write_text("x", encoding="utf-8")

        def always_fail(prompt_text: str, model_name: str) -> str:
            raise RuntimeError("boom")

        monkeypatch.setattr(reflect, "call_reflection_lm", always_fail)

        exit_code = reflect.main(
            [str(report_path), "--skill-path", str(skill_source)]
        )

        assert exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
