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
