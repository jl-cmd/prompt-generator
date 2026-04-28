from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.assemble_prompt import (
    assemble_xml_from_ledger,
    group_entries_by_section,
    split_answer_into_sentences,
)
from scripts.validate_ledger import LedgerEntry


def make_entry(
    entry_id: str,
    section: str,
    answer: str,
) -> LedgerEntry:
    return LedgerEntry(
        entry_id=entry_id,
        section=section,
        question="sample",
        answer=answer,
        parent_entry_id=None,
    )


def test_single_sentence_answer_returns_one_sentence() -> None:
    sentences = split_answer_into_sentences("Senior database architect.")
    assert sentences == ["Senior database architect."]


def test_multi_sentence_answer_splits_on_terminator() -> None:
    sentences = split_answer_into_sentences(
        "Add theme_db_id as primary key. Allow content_id to be NULL."
    )
    assert sentences == [
        "Add theme_db_id as primary key.",
        "Allow content_id to be NULL.",
    ]


def test_answer_without_terminator_returns_as_one_sentence() -> None:
    sentences = split_answer_into_sentences("migrate theme_db schema")
    assert sentences == ["migrate theme_db schema"]


def test_group_entries_preserves_order_per_section() -> None:
    entries = [
        make_entry("E1", "role", "architect"),
        make_entry("E2", "instructions", "do X"),
        make_entry("E3", "role", "senior"),
    ]
    grouped = group_entries_by_section(entries)
    assert list(grouped.keys()) == ["role", "instructions"]
    assert [each.entry_id for each in grouped["role"]] == ["E1", "E3"]
    assert [each.entry_id for each in grouped["instructions"]] == ["E2"]


def test_assemble_emits_section_tags_and_entry_comments() -> None:
    entries = [
        make_entry("E1", "role", "Senior database architect."),
        make_entry(
            "E2", "instructions", "Add theme_db_id. Allow content_id to be NULL."
        ),
    ]
    assembled = assemble_xml_from_ledger(entries)
    assert "<role>" in assembled
    assert "</role>" in assembled
    assert "<instructions>" in assembled
    assert "</instructions>" in assembled
    assert "<!-- E1.1 -->" in assembled
    assert "Senior database architect." in assembled
    assert "<!-- E2.1 -->" in assembled
    assert "Add theme_db_id." in assembled
    assert "<!-- E2.2 -->" in assembled
    assert "Allow content_id to be NULL." in assembled


def test_assemble_places_comment_on_line_before_sentence() -> None:
    entries = [make_entry("E1", "role", "architect.")]
    assembled = assemble_xml_from_ledger(entries)
    output_lines = assembled.splitlines()
    for line_index, each_line in enumerate(output_lines):
        if each_line.strip() == "architect.":
            assert output_lines[line_index - 1].strip() == "<!-- E1.1 -->"
            return
    raise AssertionError("architect. line not found in assembled output")
