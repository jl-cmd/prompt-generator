from __future__ import annotations
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.constants import (
    ARGV_INDEX_ASSEMBLED_DRAFT_PATH,
    ARGV_INDEX_LEDGER_PATH,
    ARGV_MIN_LENGTH_WITH_DRAFT,
    ARGV_MIN_LENGTH_WITHOUT_DRAFT,
    ENTRY_COMMENT_PATTERN,
    ENTRY_ID_FULL_REFERENCE_PATTERN,
    PROMPT_WORKFLOW_VALIDATOR_PATH,
    VALIDATOR_EXIT_CODE_SUCCESS,
    VALIDATOR_EXIT_CODE_USAGE_ERROR,
    VALIDATOR_EXIT_CODE_VIOLATIONS,
)


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    section: str
    question: str
    answer: str
    parent_entry_id: Optional[str]


@dataclass(frozen=True)
class ValidationFailure:
    failure_reason: str
    offending_entry_id: Optional[str]
    offending_line: Optional[str]


def load_ledger_from_json(ledger_file_path: Path) -> list[LedgerEntry]:
    raw_entries = json.loads(ledger_file_path.read_text(encoding="utf-8"))
    return [
        LedgerEntry(
            entry_id=raw["id"],
            section=raw["section"],
            question=raw["question"],
            answer=raw["answer"],
            parent_entry_id=raw.get("parent") or None,
        )
        for raw in raw_entries
    ]


def find_missing_required_sections(
    ledger_entries: list[LedgerEntry],
) -> list[ValidationFailure]:
    if not ledger_entries:
        return [
            ValidationFailure(
                failure_reason="ledger is empty at end of Phase 2",
                offending_entry_id=None,
                offending_line=None,
            )
        ]
    return []


def find_orphan_cross_references(
    ledger_entries: list[LedgerEntry],
) -> list[ValidationFailure]:
    known_entry_ids = {each_entry.entry_id for each_entry in ledger_entries}
    orphan_failures: list[ValidationFailure] = []
    for each_entry in ledger_entries:
        for referenced_id in ENTRY_ID_FULL_REFERENCE_PATTERN.findall(each_entry.answer):
            if referenced_id == each_entry.entry_id:
                continue
            if referenced_id not in known_entry_ids:
                orphan_failures.append(
                    ValidationFailure(
                        failure_reason=f"{each_entry.entry_id} references {referenced_id} which does not exist",
                        offending_entry_id=each_entry.entry_id,
                        offending_line=each_entry.answer,
                    )
                )
        if (
            each_entry.parent_entry_id
            and each_entry.parent_entry_id not in known_entry_ids
        ):
            orphan_failures.append(
                ValidationFailure(
                    failure_reason=f"{each_entry.entry_id} parent {each_entry.parent_entry_id} does not exist",
                    offending_entry_id=each_entry.entry_id,
                    offending_line=None,
                )
            )
    return orphan_failures


def find_duplicate_entry_ids(
    ledger_entries: list[LedgerEntry],
) -> list[ValidationFailure]:
    seen_ids: set[str] = set()
    duplicate_failures: list[ValidationFailure] = []
    for each_entry in ledger_entries:
        if each_entry.entry_id in seen_ids:
            duplicate_failures.append(
                ValidationFailure(
                    failure_reason=f"entry id {each_entry.entry_id} appears more than once",
                    offending_entry_id=each_entry.entry_id,
                    offending_line=None,
                )
            )
        seen_ids.add(each_entry.entry_id)
    return duplicate_failures


def find_every_sentence_has_backing_comment(
    assembled_xml_text: str,
) -> list[ValidationFailure]:
    unbacked_failures: list[ValidationFailure] = []
    has_preceding_entry_comment = False
    for each_raw_line in assembled_xml_text.splitlines():
        stripped_line = each_raw_line.strip()
        if not stripped_line:
            has_preceding_entry_comment = False
            continue
        if ENTRY_COMMENT_PATTERN.search(stripped_line):
            has_preceding_entry_comment = True
            continue
        if stripped_line.startswith("<") and stripped_line.endswith(">"):
            has_preceding_entry_comment = False
            continue
        if not has_preceding_entry_comment:
            unbacked_failures.append(
                ValidationFailure(
                    failure_reason="sentence line has no preceding entry comment",
                    offending_entry_id=None,
                    offending_line=stripped_line,
                )
            )
        has_preceding_entry_comment = False
    return unbacked_failures


def run_prompt_generator_validator(
    draft_file_path: Path,
) -> Optional[ValidationFailure]:
    completed_process = subprocess.run(
        ["python", str(PROMPT_WORKFLOW_VALIDATOR_PATH), str(draft_file_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed_process.returncode == VALIDATOR_EXIT_CODE_SUCCESS:
        return None
    return ValidationFailure(
        failure_reason=f"prompt-generator validator failed: {completed_process.stderr.strip()}",
        offending_entry_id=None,
        offending_line=None,
    )


def validate_ledger_and_draft(
    ledger_file_path: Path,
    assembled_draft_path: Optional[Path],
) -> list[ValidationFailure]:
    ledger_entries = load_ledger_from_json(ledger_file_path)
    collected_failures: list[ValidationFailure] = []
    collected_failures.extend(find_missing_required_sections(ledger_entries))
    collected_failures.extend(find_orphan_cross_references(ledger_entries))
    collected_failures.extend(find_duplicate_entry_ids(ledger_entries))
    if assembled_draft_path is not None:
        assembled_xml_text = assembled_draft_path.read_text(encoding="utf-8")
        collected_failures.extend(
            find_every_sentence_has_backing_comment(assembled_xml_text)
        )
        upstream_failure = run_prompt_generator_validator(assembled_draft_path)
        if upstream_failure is not None:
            collected_failures.append(upstream_failure)
    return collected_failures


def main() -> int:
    if len(sys.argv) < ARGV_MIN_LENGTH_WITHOUT_DRAFT:
        print(
            "usage: validate_ledger.py <ledger.json> [<assembled.xml>]", file=sys.stderr
        )
        return VALIDATOR_EXIT_CODE_USAGE_ERROR
    ledger_file_path = Path(sys.argv[ARGV_INDEX_LEDGER_PATH])
    assembled_draft_path = (
        Path(sys.argv[ARGV_INDEX_ASSEMBLED_DRAFT_PATH])
        if len(sys.argv) >= ARGV_MIN_LENGTH_WITH_DRAFT
        else None
    )
    all_failures = validate_ledger_and_draft(ledger_file_path, assembled_draft_path)
    if not all_failures:
        print("validate_ledger: pass")
        return VALIDATOR_EXIT_CODE_SUCCESS
    for each_failure in all_failures:
        print(f"validate_ledger: FAIL - {each_failure.failure_reason}", file=sys.stderr)
    return VALIDATOR_EXIT_CODE_VIOLATIONS


if __name__ == "__main__":
    sys.exit(main())
