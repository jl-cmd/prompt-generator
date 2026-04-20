"""Smoke tests for config.eval_runner: verify module imports and regex patterns compile."""

import json
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

    def test_should_use_positive_directives_only(self) -> None:
        system_prompt_text = eval_runner.REFLECTION_SYSTEM_PROMPT.lower()
        assert "do not " not in system_prompt_text
        assert "don't " not in system_prompt_text


class TestJudgeSystemPromptHardening:
    """Judge prompt carries research-mode grounding and uses positive directives."""

    def test_should_use_positive_directives_only(self) -> None:
        judge_prompt_text = eval_runner.LLM_JUDGE_SYSTEM_PROMPT.lower()
        assert "do not " not in judge_prompt_text
        assert "don't " not in judge_prompt_text

    def test_should_require_verbatim_quote_in_reason(self) -> None:
        assert "verbatim" in eval_runner.LLM_JUDGE_SYSTEM_PROMPT.lower()

    def test_should_require_pre_output_self_check(self) -> None:
        judge_prompt_text = eval_runner.LLM_JUDGE_SYSTEM_PROMPT.lower()
        assert "before emitting" in judge_prompt_text


class TestReflectionPromptSpecificity:
    """REFLECTION_SYSTEM_PROMPT uses concrete, example-anchored instructions."""

    def test_should_tell_model_to_paste_identifiers_rather_than_copy_by_hand(self) -> None:
        reflection_prompt_text = eval_runner.REFLECTION_SYSTEM_PROMPT
        assert "by hand" not in reflection_prompt_text
        assert "paste" in reflection_prompt_text.lower()

    def test_should_show_concrete_diff_marker_example(self) -> None:
        reflection_prompt_text = eval_runner.REFLECTION_SYSTEM_PROMPT
        assert "Example of valid diff form" in reflection_prompt_text

    def test_should_show_concrete_citation_format_example(self) -> None:
        reflection_prompt_text = eval_runner.REFLECTION_SYSTEM_PROMPT
        assert "Example of valid citations" in reflection_prompt_text


class TestJudgePromptRoundTwoAuditFindings:
    """Round-2 audit: positive phrasing, raw-JSON sentence, and example block."""

    def test_should_use_new_fail_on_no_evidence_wording(self) -> None:
        judge_prompt_text = eval_runner.LLM_JUDGE_SYSTEM_PROMPT
        assert "no supporting substring found" in judge_prompt_text

    def test_should_use_new_raw_json_sentence(self) -> None:
        judge_prompt_text = eval_runner.LLM_JUDGE_SYSTEM_PROMPT
        assert "Output is raw JSON:" in judge_prompt_text

    def test_should_contain_verdict_example_block(self) -> None:
        judge_prompt_text = eval_runner.LLM_JUDGE_SYSTEM_PROMPT
        assert 'Example: {"verdict":"FAIL"' in judge_prompt_text


class TestReflectionPromptRoundTwoAuditFindings:
    """Round-2 audit: URL citations must include a section-heading anchor."""

    def test_should_require_section_anchor_in_citations_example(self) -> None:
        reflection_prompt_text = eval_runner.REFLECTION_SYSTEM_PROMPT
        assert "#" in reflection_prompt_text.split("Example of valid citations")[1]

    def test_should_still_include_skill_line_citation_example(self) -> None:
        reflection_prompt_text = eval_runner.REFLECTION_SYSTEM_PROMPT
        assert "SKILL line" in reflection_prompt_text


class TestEvalSpecsCoverEverySkill:
    """EVAL_SPECS must list every skill whose eval JSON is wired into run_evals.py."""

    def test_should_include_all_five_skills(self) -> None:
        skill_names = {each_spec[0] for each_spec in eval_runner.EVAL_SPECS}
        assert skill_names == {"pmid", "pmin", "agent-prompt", "prompt-generator", "pmax"}

    def test_every_spec_path_should_exist_on_disk(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        for each_skill, each_spec_path, _ in eval_runner.EVAL_SPECS:
            assert (repo_root / each_spec_path).exists(), (
                f"EVAL_SPECS entry for {each_skill} points at missing file {each_spec_path}"
            )

    def test_every_spec_should_parse_as_canonical_evals_shape(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        for each_skill, each_spec_path, _ in eval_runner.EVAL_SPECS:
            spec_data = json.loads((repo_root / each_spec_path).read_text(encoding="utf-8"))
            assert "evals" in spec_data, f"{each_skill} spec has no 'evals' key"
            assert isinstance(spec_data["evals"], list)
            assert len(spec_data["evals"]) > 0
            for each_item in spec_data["evals"]:
                assert "id" in each_item
                assert "name" in each_item
                assert "expected_behavior" in each_item


class TestVerdictColorsInlined:
    """Color escape codes live inside VERDICT_COLORS, not as separate file-global constants."""

    def test_should_not_expose_ansi_color_name_constants(self) -> None:
        assert not hasattr(eval_runner, "ANSI_GREEN")
        assert not hasattr(eval_runner, "ANSI_RED")
        assert not hasattr(eval_runner, "ANSI_YELLOW")

    def test_should_keep_ansi_reset_for_cross_module_use(self) -> None:
        assert eval_runner.ANSI_RESET == "\033[0m"

    def test_verdict_colors_should_map_to_escape_codes_directly(self) -> None:
        assert eval_runner.VERDICT_COLORS["PASS"] == "\033[32m"
        assert eval_runner.VERDICT_COLORS["FAIL"] == "\033[31m"
        assert eval_runner.VERDICT_COLORS["SKIP"] == "\033[33m"
