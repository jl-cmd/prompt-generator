"""Tests for capture_eval.py — the dual-runtime eval-output capture harness."""

import json
from pathlib import Path

import pytest

import capture_eval


class TestLoadEvalPrompt:
    """load_eval_prompt fetches one eval's prompt field from its spec JSON."""

    def test_should_return_prompt_for_matching_id(self, tmp_path: Path) -> None:
        spec_path = tmp_path / "spec.json"
        spec_path.write_text(
            json.dumps({"evals": [{"id": 1, "name": "n", "prompt": "hi"}]}),
            encoding="utf-8",
        )

        prompt_text = capture_eval.load_eval_prompt(spec_path, eval_id=1)

        assert prompt_text == "hi"

    def test_should_raise_when_eval_id_missing(self, tmp_path: Path) -> None:
        spec_path = tmp_path / "spec.json"
        spec_path.write_text(json.dumps({"evals": []}), encoding="utf-8")

        with pytest.raises(LookupError):
            capture_eval.load_eval_prompt(spec_path, eval_id=99)


class TestCaptureViaGroq:
    """capture_via_groq sends the skill body plus eval prompt to Groq and returns text."""

    def test_should_send_skill_md_as_system_and_prompt_as_user(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        skill_md_path = tmp_path / "SKILL.md"
        skill_md_path.write_text("SKILL BODY", encoding="utf-8")

        captured_messages: list[dict] = []

        def fake_completion(**kwargs: object) -> dict:
            captured_messages.extend(kwargs["messages"])
            return {"choices": [{"message": {"content": "captured output"}}]}

        monkeypatch.setattr(capture_eval.litellm, "completion", fake_completion)

        output_text = capture_eval.capture_via_groq(
            skill_md_path=skill_md_path, eval_prompt="do the thing"
        )

        assert output_text == "captured output"
        system_message = next(
            each for each in captured_messages if each["role"] == "system"
        )
        user_message = next(
            each for each in captured_messages if each["role"] == "user"
        )
        assert "SKILL BODY" in system_message["content"]
        assert user_message["content"] == "do the thing"


class TestDispatchBySkill:
    """dispatch_capture routes Groq skills to capture_via_groq and Claude skills to a skipped placeholder."""

    def test_groq_skill_should_call_groq_backend(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        skill_md_path = tmp_path / "SKILL.md"
        skill_md_path.write_text("SKILL BODY", encoding="utf-8")

        def fake_capture_via_groq(skill_md_path: Path, eval_prompt: str) -> str:
            return "groq-captured"

        monkeypatch.setattr(capture_eval, "capture_via_groq", fake_capture_via_groq)

        output_text = capture_eval.dispatch_capture(
            skill_name="pmin", skill_md_path=skill_md_path, eval_prompt="do it"
        )

        assert output_text == "groq-captured"

    def test_claude_routed_skill_should_return_skipped_sentinel(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        skill_md_path = tmp_path / "SKILL.md"
        skill_md_path.write_text("SKILL BODY", encoding="utf-8")

        monkeypatch.setattr(capture_eval, "is_groq_runtime", lambda skill_name: False)
        monkeypatch.setattr(capture_eval, "is_claude_runtime", lambda skill_name: True)

        output_text = capture_eval.dispatch_capture(
            skill_name="any-skill", skill_md_path=skill_md_path, eval_prompt="do it"
        )

        assert output_text.startswith("SKILL_INVOCATION_SKIPPED")
        assert "claude runtime" in output_text.lower()
