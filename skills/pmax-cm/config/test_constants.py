from __future__ import annotations
import re
from pathlib import Path

from config.constants import (
    ASKUSERQUESTION_MAX_OPTIONS,
    ASKUSERQUESTION_MAX_QUESTIONS_PER_ROUND,
    ASKUSERQUESTION_MIN_OPTIONS,
    BANNED_HEDGING_WORDS,
    DISCOVERED_OPTION_LABEL_SUFFIX,
    ENTRY_COMMENT_CLOSE,
    ENTRY_COMMENT_OPEN,
    ENTRY_ID_NUMERIC_PATTERN,
    ENTRY_ID_PREFIX,
    OUTCOME_PREVIEW_MAX_LINES,
    OUTCOME_PREVIEW_MAX_ROUNDS,
    PROMPT_WORKFLOW_VALIDATOR_PATH,
    RECOMMENDED_OPTION_LABEL_SUFFIX,
    SKILL_FROM_GROUND_UP_TEMPLATE,
    SKILL_REFINEMENT_PACKAGE_TEMPLATE,
    VALIDATOR_EXIT_CODE_SUCCESS,
    VALIDATOR_EXIT_CODE_VIOLATIONS,
)


def test_entry_comment_markers_are_html_comment_form() -> None:
    assert ENTRY_COMMENT_OPEN == "<!-- "
    assert ENTRY_COMMENT_CLOSE == " -->"


def test_entry_id_numeric_pattern_matches_simple_and_subids() -> None:
    compiled_pattern = re.compile(ENTRY_ID_NUMERIC_PATTERN)
    assert compiled_pattern.fullmatch("1") is not None
    assert compiled_pattern.fullmatch("12") is not None
    assert compiled_pattern.fullmatch("4.1") is not None
    assert compiled_pattern.fullmatch("4.12") is not None
    assert compiled_pattern.fullmatch("a") is None
    assert compiled_pattern.fullmatch("4.1.2") is None


def test_askuserquestion_option_caps_match_schema() -> None:
    assert ASKUSERQUESTION_MIN_OPTIONS == 2
    assert ASKUSERQUESTION_MAX_OPTIONS == 4
    assert ASKUSERQUESTION_MAX_QUESTIONS_PER_ROUND == 4


def test_outcome_preview_limits_are_positive() -> None:
    assert OUTCOME_PREVIEW_MAX_LINES > 0
    assert OUTCOME_PREVIEW_MAX_ROUNDS > 0


def test_banned_hedging_words_cover_documented_cases() -> None:
    for each_expected_word in ("plausibly", "maybe", "probably", "could", "might"):
        assert each_expected_word in BANNED_HEDGING_WORDS


def test_option_label_suffixes_are_nonempty_strings() -> None:
    assert isinstance(DISCOVERED_OPTION_LABEL_SUFFIX, str)
    assert isinstance(RECOMMENDED_OPTION_LABEL_SUFFIX, str)
    assert DISCOVERED_OPTION_LABEL_SUFFIX
    assert RECOMMENDED_OPTION_LABEL_SUFFIX


def test_validator_exit_codes_are_distinct() -> None:
    assert VALIDATOR_EXIT_CODE_SUCCESS != VALIDATOR_EXIT_CODE_VIOLATIONS


def test_referenced_external_paths_are_absolute() -> None:
    assert isinstance(PROMPT_WORKFLOW_VALIDATOR_PATH, Path)
    assert PROMPT_WORKFLOW_VALIDATOR_PATH.is_absolute()
    assert SKILL_FROM_GROUND_UP_TEMPLATE.is_absolute()
    assert SKILL_REFINEMENT_PACKAGE_TEMPLATE.is_absolute()
