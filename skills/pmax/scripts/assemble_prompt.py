from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.constants import (
    ARGV_INDEX_LEDGER_PATH,
    ARGV_MIN_LENGTH_WITHOUT_DRAFT,
    ENTRY_COMMENT_CLOSE,
    ENTRY_COMMENT_OPEN,
    ENTRY_ID_PREFIX,
    ENTRY_ID_SUBID_SEPARATOR,
    SENTENCE_SPLIT_REGEX,
    SENTENCE_TERMINATORS,
    VALIDATOR_EXIT_CODE_SUCCESS,
    VALIDATOR_EXIT_CODE_USAGE_ERROR,
    XML_INDENT_DOUBLE,
)
from scripts.validate_ledger import LedgerEntry


def split_answer_into_sentences(answer_text: str) -> list[str]:
    cleaned_answer_text = answer_text.strip()
    if not cleaned_answer_text:
        return []
    candidate_sentences = [
        each_candidate.strip()
        for each_candidate in SENTENCE_SPLIT_REGEX.split(cleaned_answer_text)
        if each_candidate.strip()
    ]
    if len(candidate_sentences) > 1:
        return candidate_sentences
    has_terminal_punctuation = any(
        cleaned_answer_text.endswith(each_terminator)
        for each_terminator in SENTENCE_TERMINATORS
    )
    if has_terminal_punctuation:
        return [cleaned_answer_text]
    return [cleaned_answer_text]


def group_entries_by_section(
    ledger_entries: list[LedgerEntry],
) -> dict[str, list[LedgerEntry]]:
    entries_by_section: dict[str, list[LedgerEntry]] = {}
    for each_entry in ledger_entries:
        entries_by_section.setdefault(each_entry.section, []).append(each_entry)
    return entries_by_section


def format_entry_comment(entry_id: str, sentence_index: int) -> str:
    numeric_part = entry_id[len(ENTRY_ID_PREFIX) :]
    sub_entry_id = (
        ENTRY_ID_PREFIX + numeric_part + ENTRY_ID_SUBID_SEPARATOR + str(sentence_index)
    )
    return ENTRY_COMMENT_OPEN + sub_entry_id + ENTRY_COMMENT_CLOSE


def render_entry_sentences(each_entry: LedgerEntry) -> list[str]:
    rendered_lines: list[str] = []
    sentences = split_answer_into_sentences(each_entry.answer)
    for sentence_index, each_sentence in enumerate(sentences, start=1):
        rendered_lines.append(
            XML_INDENT_DOUBLE
            + format_entry_comment(each_entry.entry_id, sentence_index)
        )
        rendered_lines.append(XML_INDENT_DOUBLE + each_sentence)
    return rendered_lines


def assemble_xml_from_ledger(ledger_entries: list[LedgerEntry]) -> str:
    entries_by_section = group_entries_by_section(ledger_entries)
    output_lines: list[str] = []
    for each_section_name, each_section_entries in entries_by_section.items():
        output_lines.append(f"<{each_section_name}>")
        for each_entry in each_section_entries:
            output_lines.extend(render_entry_sentences(each_entry))
        output_lines.append(f"</{each_section_name}>")
    return "\n".join(output_lines) + "\n"


def load_entries_from_ledger_file(ledger_file_path: Path) -> list[LedgerEntry]:
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


def main() -> int:
    if len(sys.argv) < ARGV_MIN_LENGTH_WITHOUT_DRAFT:
        print("usage: assemble_prompt.py <ledger.json>", file=sys.stderr)
        return VALIDATOR_EXIT_CODE_USAGE_ERROR
    ledger_file_path = Path(sys.argv[ARGV_INDEX_LEDGER_PATH])
    ledger_entries = load_entries_from_ledger_file(ledger_file_path)
    assembled_xml_text = assemble_xml_from_ledger(ledger_entries)
    sys.stdout.write(assembled_xml_text)
    return VALIDATOR_EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
