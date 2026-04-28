# pragma: no-tdd-gate
from __future__ import annotations
import re
from pathlib import Path
from typing import Final, Pattern

ENTRY_ID_PREFIX: Final[str] = "E"
ENTRY_ID_SUBID_SEPARATOR: Final[str] = "."
ENTRY_COMMENT_OPEN: Final[str] = "<!-- "
ENTRY_COMMENT_CLOSE: Final[str] = " -->"
ENTRY_ID_NUMERIC_PATTERN: Final[str] = r"\d+(?:\.\d+)?"

SENTENCE_TERMINATORS: Final[tuple[str, ...]] = (".", "?", "!")
SENTENCE_SPLIT_PATTERN: Final[str] = r"(?<=[.?!])\s+(?=[A-Z])"

ASKUSERQUESTION_MIN_OPTIONS: Final[int] = 2
ASKUSERQUESTION_MAX_OPTIONS: Final[int] = 4
ASKUSERQUESTION_MAX_QUESTIONS_PER_ROUND: Final[int] = 4

OUTCOME_PREVIEW_MAX_LINES: Final[int] = 20
OUTCOME_PREVIEW_MAX_ROUNDS: Final[int] = 3

DRAFT_PROMPT_RELATIVE_PATH: Final[str] = "data/prompts/.draft-prompt.xml"

PROMPT_WORKFLOW_VALIDATOR_PATH: Final[Path] = Path(
    "Y:/Projects/LLM Plugins/prompt-generator/hooks/blocking/prompt_workflow_validate.py"
)
SKILL_FROM_GROUND_UP_TEMPLATE: Final[Path] = Path(
    "Y:/Projects/LLM Plugins/prompt-generator/skills/prompt-generator/templates/skill-from-ground-up.md"
)
SKILL_REFINEMENT_PACKAGE_TEMPLATE: Final[Path] = Path(
    "Y:/Projects/LLM Plugins/prompt-generator/skills/prompt-generator/templates/skill-refinement-package.md"
)

BANNED_HEDGING_WORDS: Final[frozenset[str]] = frozenset(
    {
        "plausibly",
        "maybe",
        "probably",
        "could",
        "might",
        "possibly",
        "perhaps",
    }
)

DISCOVERED_OPTION_LABEL_SUFFIX: Final[str] = "[discovered]"
RECOMMENDED_OPTION_LABEL_SUFFIX: Final[str] = "(Recommended)"

VALIDATOR_EXIT_CODE_SUCCESS: Final[int] = 0
VALIDATOR_EXIT_CODE_VIOLATIONS: Final[int] = 2
VALIDATOR_EXIT_CODE_USAGE_ERROR: Final[int] = 1

ARGV_INDEX_LEDGER_PATH: Final[int] = 1
ARGV_INDEX_ASSEMBLED_DRAFT_PATH: Final[int] = 2
ARGV_MIN_LENGTH_WITH_DRAFT: Final[int] = 3
ARGV_MIN_LENGTH_WITHOUT_DRAFT: Final[int] = 2

ENTRY_ID_FULL_REFERENCE_PATTERN: Final[Pattern[str]] = re.compile(
    r"\b" + re.escape(ENTRY_ID_PREFIX) + ENTRY_ID_NUMERIC_PATTERN + r"\b"
)
ENTRY_COMMENT_PATTERN: Final[Pattern[str]] = re.compile(
    re.escape(ENTRY_COMMENT_OPEN)
    + re.escape(ENTRY_ID_PREFIX)
    + ENTRY_ID_NUMERIC_PATTERN
    + re.escape(ENTRY_COMMENT_CLOSE)
)
SENTENCE_SPLIT_REGEX: Final[Pattern[str]] = re.compile(SENTENCE_SPLIT_PATTERN)

XML_INDENT_DOUBLE: Final[str] = "    "
