"""Smoke tests for config.eval_runner: verify module imports and regex patterns compile."""

import re
from pathlib import Path

from config import eval_runner

EVAL_RUNNER_SOURCE_PATH: Path = Path(__file__).parent / "eval_runner.py"


class TestEvalRunnerModuleImports:
    def test_should_compile_nested_backtick_pattern(self) -> None:
        assert isinstance(eval_runner.NESTED_BACKTICK_PATTERN, re.Pattern)

    def test_should_compile_xml_fence_open_pattern(self) -> None:
        assert isinstance(eval_runner.XML_FENCE_OPEN_PATTERN, re.Pattern)

    def test_should_compile_outcome_digest_pattern(self) -> None:
        assert isinstance(eval_runner.OUTCOME_DIGEST_PATTERN, re.Pattern)

    def test_should_not_contain_tdd_gate_pragma(self) -> None:
        assert "pragma: no-tdd-gate" not in EVAL_RUNNER_SOURCE_PATH.read_text(encoding="utf-8")


class TestReflectionSystemPromptHardening:
    """Reflection system prompt carries research-mode-style grounding rules."""

    def test_should_require_citations_section(self) -> None:
        assert "CITATIONS:" in eval_runner.REFLECTION_SYSTEM_PROMPT

    def test_should_offer_no_edit_escape_hatch(self) -> None:
        assert "NO EDIT" in eval_runner.REFLECTION_SYSTEM_PROMPT

    def test_should_list_canonical_claude_docs_urls(self) -> None:
        system_prompt_text = eval_runner.REFLECTION_SYSTEM_PROMPT
        assert "https://docs.anthropic.com/en/docs/claude-code/skills" in system_prompt_text
        assert "https://docs.anthropic.com/en/docs/claude-code/hooks" in system_prompt_text
        assert "https://docs.anthropic.com/en/docs/claude-code/sub-agents" in system_prompt_text
