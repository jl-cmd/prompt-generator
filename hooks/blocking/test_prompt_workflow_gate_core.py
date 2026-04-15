"""Unit tests for shared prompt workflow gate logic."""

from prompt_workflow_gate_core import (
    build_expected_tag_list,
    extract_fenced_xml_content,
    extract_fenced_xml_content_from_export,
    extract_plan_section_headers,
    find_ambiguous_scope_terms,
    has_checklist_container,
    has_internal_object_leak,
    is_prompt_workflow_response,
    missing_context_control_signals,
    missing_checklist_rows,
    missing_plan_derived_xml_sections,
    missing_required_xml_sections,
    missing_scope_anchors,
    normalize_prompt_workflow_export,
)

def test_internal_object_leak_detected() -> None:
    text = '{"pipeline_mode": "internal_section_refinement_with_final_audit"}'
    assert has_internal_object_leak(text)

def test_missing_scope_anchors_returns_expected_rows() -> None:
    text = "target_local_roots only."
    missing = missing_scope_anchors(text)
    assert "target_canonical_roots" in missing
    assert "completion_boundary" in missing

def test_missing_checklist_rows_detected() -> None:
    text = "checklist_results: structured_scoped_instructions only"
    missing = missing_checklist_rows(text)
    assert "completion_boundary_measurable" in missing

def test_checklist_container_detection() -> None:
    assert has_checklist_container("checklist_results:\n- structured_scoped_instructions")

def test_prompt_workflow_response_detection() -> None:
    message = (
        "overall_status: pass\n"
        "target_local_roots: /repo\n"
        "comparison_basis: current behavior vs deterministic guarantees\n"
    )
    assert is_prompt_workflow_response(message)

def test_missing_context_control_signals_detected() -> None:
    missing = missing_context_control_signals("base_minimal_instruction_layer: true")
    assert "on_demand_skill_loading: true" in missing

def test_ambiguous_scope_terms_detected() -> None:
    text = "Scope applies to this session and current files."
    terms = find_ambiguous_scope_terms(text)
    assert "this session" in terms
    assert "current files" in terms

def _fenced_xml(body: str) -> str:
    return f"```xml\n{body}\n```"

def _runtime_context_lines() -> tuple[str, ...]:
    return (
        "<runtime_context>",
        "base_minimal_instruction_layer: true",
        "on_demand_skill_loading: true",
        "</runtime_context>",
        "",
    )

def _flattened_transcript(*lines: str) -> str:
    return "\n".join(lines) + "\n"

def _flattened_attempt(*body_lines: str, audit_line: str = "Audit: pass 15/15") -> str:
    flattened_lines = [audit_line, ""]
    for line in body_lines:
        flattened_lines.append(f"  {line}" if line else "")
    return "\n".join(flattened_lines)

def test_missing_required_xml_sections_all_present_returns_empty() -> None:
    body = (
        "<role>R.</role>\n"
        "<background>C.</background>\n"
        "<instructions>I.</instructions>\n"
        "<constraints>Co.</constraints>\n"
        "<output_format>O.</output_format>\n"
    )
    assert missing_required_xml_sections(_fenced_xml(body)) == []

def test_missing_required_xml_sections_empty_when_no_fixed_sections() -> None:
    body = "<context>C.</context>\n<delivery>D.</delivery>\n"
    assert missing_required_xml_sections(_fenced_xml(body)) == []

def test_missing_required_xml_sections_no_fence_returns_empty() -> None:
    assert missing_required_xml_sections("no fenced xml here") == []

def test_plan_derived_sections_missing_background() -> None:
    plan_sections = ["role", "background", "instructions", "constraints", "output_format"]
    body = (
        "<role>R.</role>\n"
        "<instructions>I.</instructions>\n"
        "<constraints>Co.</constraints>\n"
        "<output_format>O.</output_format>\n"
    )
    assert missing_plan_derived_xml_sections(_fenced_xml(body), plan_sections) == ["background"]

def test_plan_derived_sections_prose_without_tags_counts_as_missing() -> None:
    plan_sections = ["role", "background", "instructions", "constraints", "output_format"]
    body = (
        "<role>R.</role>\n"
        "background appears in prose but has no tags.\n"
        "<instructions>I.</instructions>\n"
        "<constraints>Co.</constraints>\n"
        "<output_format>O.</output_format>\n"
    )
    assert missing_plan_derived_xml_sections(_fenced_xml(body), plan_sections) == ["background"]

def test_extract_plan_section_headers_single_depth() -> None:
    plan = "# Context\nSome content\n## Goal\nGoal content\n"
    headers = extract_plan_section_headers(plan)
    assert headers == [(1, "context"), (2, "goal")]


def test_extract_plan_section_headers_multi_depth() -> None:
    plan = (
        "# Context\n"
        "## Goal\n"
        "### Sub detail\n"
        "# Delivery\n"
        "## Primary path\n"
    )
    headers = extract_plan_section_headers(plan)
    assert headers == [
        (1, "context"),
        (2, "goal"),
        (3, "sub_detail"),
        (1, "delivery"),
        (2, "primary_path"),
    ]


def test_extract_plan_section_headers_normalizes_special_characters() -> None:
    plan = "# Target repos (32)\n## File content (draft, <4000 chars)\n"
    headers = extract_plan_section_headers(plan)
    assert headers == [
        (1, "target_repos_32"),
        (2, "file_content_draft_4000_chars"),
    ]


def test_extract_plan_section_headers_ignores_non_header_lines() -> None:
    plan = "Regular text\n# Only header\nMore text\n"
    headers = extract_plan_section_headers(plan)
    assert headers == [(1, "only_header")]


def test_build_expected_tag_list_returns_all_tag_names() -> None:
    headers = [(1, "context"), (2, "goal"), (2, "verified_facts"), (1, "delivery")]
    tag_list = build_expected_tag_list(headers)
    assert tag_list == ["context", "goal", "verified_facts", "delivery"]


def test_missing_plan_derived_xml_sections_all_present() -> None:
    fenced_xml = _fenced_xml(
        "<context><goal>G</goal></context>\n<delivery>D</delivery>"
    )
    missing = missing_plan_derived_xml_sections(
        fenced_xml, ["context", "goal", "delivery"]
    )
    assert missing == []


def test_missing_plan_derived_xml_sections_detects_missing() -> None:
    fenced_xml = _fenced_xml("<context>C</context>")
    missing = missing_plan_derived_xml_sections(
        fenced_xml, ["context", "goal", "delivery"]
    )
    assert missing == ["goal", "delivery"]


def test_extract_fenced_xml_preserves_content_after_nested_inner_fence() -> None:
    message = (
        "```xml\n"
        "<role>R</role>\n"
        "<illustrations>\n"
        "```bash\necho hi\n```\n"
        "</illustrations>\n"
        "<background>B</background>\n"
        "<instructions>I</instructions>\n"
        "<constraints>C</constraints>\n"
        "<output_format>O</output_format>\n"
        "```\n"
    )
    extracted = extract_fenced_xml_content(message)
    assert "</illustrations>" in extracted
    assert "<background>B</background>" in extracted

def test_normalize_prompt_workflow_export_rebuilds_fence_from_flattened_transcript() -> None:
    transcript = _flattened_transcript(
        _flattened_attempt(
            *_runtime_context_lines(),
            "<role>R</role>",
            "<background>B</background>",
            "<instructions>I</instructions>",
            "<constraints>C</constraints>",
            "<output_format>O</output_format>",
            "✻ Worked for 1m 7s",
            audit_line="● Audit: pass 15/15",
        ),
    )
    normalized = normalize_prompt_workflow_export(transcript)
    assert normalized.startswith("Audit: pass 15/15\n```xml\n")
    assert normalized.endswith("\n```")
    assert "<runtime_context>" in normalized
    assert "✻ Worked for 1m 7s" not in normalized

def test_normalize_prompt_workflow_export_uses_last_audit_attempt() -> None:
    first_attempt = _flattened_attempt(
        "<role>FIRST</role>",
        "<background>Old</background>",
        "<instructions>Old</instructions>",
        "<constraints>Old</constraints>",
        "<output_format>Old</output_format>",
        audit_line="● Audit: pass 15/15",
    )
    second_attempt = _flattened_attempt(
        *_runtime_context_lines(),
        "<role>FINAL</role>",
        "<background>Fresh</background>",
        "<instructions>I</instructions>",
        "<constraints>C</constraints>",
        "<output_format>O</output_format>",
        "✻ Worked for 2m 8s",
    )
    transcript = _flattened_transcript(
        first_attempt,
        "",
        "● Re-emitting the full artifact with the runtime signals added.",
        "",
        second_attempt,
    )
    normalized = normalize_prompt_workflow_export(transcript)
    assert "<role>FINAL</role>" in normalized
    assert "<role>FIRST</role>" not in normalized

def test_extract_fenced_xml_content_from_export_supports_flattened_transcript() -> None:
    transcript = _flattened_transcript(
        _flattened_attempt(
            "<role>R</role>",
            "<background>B</background>",
            "<instructions>I</instructions>",
            "<constraints>C</constraints>",
            "<output_format>O</output_format>",
            "✻ Worked for 31s",
            audit_line="● Audit: pass 15/15",
        ),
    )
    extracted = extract_fenced_xml_content_from_export(transcript)
    assert extracted.startswith("<role>R</role>")
    assert "<output_format>O</output_format>" in extracted
    assert "Worked for" not in extracted

def test_extract_plan_section_headers_ignores_headers_inside_backtick_fence() -> None:
    plan = "# real\n```python\n# not a header\n```\n## also_real\n"
    headers = extract_plan_section_headers(plan)
    tag_names = [name for _depth, name in headers]
    assert "real" in tag_names
    assert "also_real" in tag_names
    assert "not_a_header" not in tag_names

def test_extract_plan_section_headers_ignores_headers_inside_tilde_fence() -> None:
    plan = "# outside\n~~~\n# inside_fence\n~~~\n"
    headers = extract_plan_section_headers(plan)
    tag_names = [name for _depth, name in headers]
    assert "outside" in tag_names
    assert "inside_fence" not in tag_names

def test_extract_plan_section_headers_ignores_indented_headers() -> None:
    plan = "# real_header\n  # indented_not_a_header\n"
    headers = extract_plan_section_headers(plan)
    tag_names = [name for _depth, name in headers]
    assert "real_header" in tag_names
    assert "indented_not_a_header" not in tag_names

def test_normalize_header_to_tag_name_prefixes_digit_leading_names() -> None:
    plan = "## 0. Initialize context\n# 1 setup\n"
    headers = extract_plan_section_headers(plan)
    tag_names = [name for _depth, name in headers]
    for name in tag_names:
        assert not name[0].isdigit(), f"tag name '{name}' starts with digit"
        assert name.startswith("section_"), f"expected section_ prefix, got '{name}'"
