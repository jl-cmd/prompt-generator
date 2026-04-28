from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_ledger import (
    LedgerEntry,
    find_duplicate_entry_ids,
    find_every_sentence_has_backing_comment,
    find_missing_required_sections,
    find_orphan_cross_references,
    load_ledger_from_json,
)


def make_entry(
    entry_id: str,
    section: str = "role",
    answer: str = "example answer",
    parent_entry_id: str | None = None,
) -> LedgerEntry:
    return LedgerEntry(
        entry_id=entry_id,
        section=section,
        question="sample question",
        answer=answer,
        parent_entry_id=parent_entry_id,
    )


def test_empty_ledger_fails_missing_sections_check() -> None:
    failures = find_missing_required_sections([])
    assert len(failures) == 1
    assert "empty" in failures[0].failure_reason


def test_non_empty_ledger_passes_missing_sections_check() -> None:
    failures = find_missing_required_sections([make_entry("E1")])
    assert failures == []


def test_orphan_cross_reference_detected_in_answer_text() -> None:
    entries = [make_entry("E1", answer="see strategy from E99")]
    failures = find_orphan_cross_references(entries)
    assert len(failures) == 1
    assert "E99" in failures[0].failure_reason


def test_valid_cross_reference_does_not_fail() -> None:
    entries = [
        make_entry("E1", answer="base decision"),
        make_entry("E2", answer="refines the approach from E1"),
    ]
    failures = find_orphan_cross_references(entries)
    assert failures == []


def test_orphan_parent_id_detected() -> None:
    entries = [make_entry("E2", parent_entry_id="E7")]
    failures = find_orphan_cross_references(entries)
    assert any("parent" in each.failure_reason for each in failures)


def test_duplicate_entry_ids_detected() -> None:
    entries = [make_entry("E1"), make_entry("E1")]
    failures = find_duplicate_entry_ids(entries)
    assert len(failures) == 1


def test_unique_entry_ids_pass_duplicate_check() -> None:
    entries = [make_entry("E1"), make_entry("E2")]
    failures = find_duplicate_entry_ids(entries)
    assert failures == []


def test_sentence_without_preceding_comment_is_flagged() -> None:
    assembled_xml = "<role>\n  Senior architect.\n</role>\n"
    failures = find_every_sentence_has_backing_comment(assembled_xml)
    assert len(failures) == 1
    assert "Senior architect" in (failures[0].offending_line or "")


def test_sentence_with_preceding_comment_passes() -> None:
    assembled_xml = "<role>\n  <!-- E2.1 -->\n  Senior architect.\n</role>\n"
    failures = find_every_sentence_has_backing_comment(assembled_xml)
    assert failures == []


def test_multiple_sentences_each_need_their_own_comment() -> None:
    assembled_xml = (
        "<role>\n"
        "  <!-- E2.1 -->\n"
        "  First sentence.\n"
        "  Second sentence without comment.\n"
        "</role>\n"
    )
    failures = find_every_sentence_has_backing_comment(assembled_xml)
    assert len(failures) == 1


def test_load_ledger_from_json_parses_entries(tmp_path: Path) -> None:
    ledger_json_path = tmp_path / "ledger.json"
    ledger_json_path.write_text(
        json.dumps(
            [
                {
                    "id": "E1",
                    "section": "role",
                    "question": "q",
                    "answer": "a",
                    "parent": None,
                },
                {
                    "id": "E2",
                    "section": "role",
                    "question": "q",
                    "answer": "b",
                    "parent": "E1",
                },
            ]
        ),
        encoding="utf-8",
    )
    loaded_entries = load_ledger_from_json(ledger_json_path)
    assert len(loaded_entries) == 2
    assert loaded_entries[0].entry_id == "E1"
    assert loaded_entries[1].parent_entry_id == "E1"
