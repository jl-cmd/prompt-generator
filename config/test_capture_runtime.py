"""Tests for config.capture_runtime: the skill-to-runtime classifier."""

import pytest

from config import capture_runtime


class TestCaptureRuntimeClassifier:
    """Decision rule: if a skill leans on AskUserQuestion or any Claude-Code-specific feature, it needs the Claude runtime to capture faithfully. Otherwise Groq suffices."""

    def test_pmin_should_route_to_groq(self) -> None:
        assert capture_runtime.runtime_for_skill("pmin") == "groq"

    def test_pmid_should_route_to_groq(self) -> None:
        assert capture_runtime.runtime_for_skill("pmid") == "groq"

    def test_pmax_should_route_to_groq(self) -> None:
        assert capture_runtime.runtime_for_skill("pmax") == "groq"

    def test_agent_prompt_should_route_to_groq(self) -> None:
        assert capture_runtime.runtime_for_skill("agent-prompt") == "groq"

    def test_prompt_generator_should_route_to_groq(self) -> None:
        assert capture_runtime.runtime_for_skill("prompt-generator") == "groq"

    def test_unknown_skill_should_raise(self) -> None:
        with pytest.raises(KeyError):
            capture_runtime.runtime_for_skill("unregistered-skill")

    def test_is_groq_runtime_true_for_all_registered_skills(self) -> None:
        for each_skill in ("pmin", "pmid", "pmax", "agent-prompt", "prompt-generator"):
            assert capture_runtime.is_groq_runtime(each_skill) is True

    def test_is_claude_runtime_false_for_all_registered_skills(self) -> None:
        for each_skill in ("pmin", "pmid", "pmax", "agent-prompt", "prompt-generator"):
            assert capture_runtime.is_claude_runtime(each_skill) is False
