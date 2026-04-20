"""Tests for capture_all.py — the batch capture driver."""

from pathlib import Path

import pytest

import capture_all


class TestIterateEvalJobs:
    """iterate_eval_jobs yields (skill, eval_id, output_path) for every registered eval."""

    def test_should_yield_one_job_per_eval_in_every_spec(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_spec_a = tmp_path / "a.json"
        fake_spec_b = tmp_path / "b.json"
        fake_spec_a.write_text('{"evals": [{"id": 1}, {"id": 2}]}', encoding="utf-8")
        fake_spec_b.write_text('{"evals": [{"id": 5}]}', encoding="utf-8")
        output_dir = tmp_path / "out"

        monkeypatch.setattr(
            capture_all,
            "EVAL_SPECS",
            [("alpha", fake_spec_a, output_dir), ("beta", fake_spec_b, output_dir)],
        )

        all_jobs = list(capture_all.iterate_eval_jobs())

        assert all_jobs == [
            ("alpha", 1, output_dir / "eval-alpha-1-output.txt"),
            ("alpha", 2, output_dir / "eval-alpha-2-output.txt"),
            ("beta", 5, output_dir / "eval-beta-5-output.txt"),
        ]


class TestCaptureRetryKnobsSourcedFromConfig:
    """Throttle / retry values live in config/eval_runner.py, not as local constants."""

    def test_capture_all_should_import_throttle_and_retry_from_config(self) -> None:
        source_text = Path(capture_all.__file__).read_text(encoding="utf-8")
        assert "CAPTURE_INTER_REQUEST_THROTTLE_SECONDS" in source_text
        assert "CAPTURE_MAX_RETRIES_PER_JOB" in source_text
        assert "CAPTURE_RETRY_BACKOFF_BASE_SECONDS" in source_text
        assert "CAPTURE_RETRY_BACKOFF_EXPONENT_BASE" in source_text


class TestShouldSkipExistingOutput:
    """An existing non-sentinel output file is preserved; sentinel files are rewritten."""

    def test_should_skip_when_file_has_real_content(self, tmp_path: Path) -> None:
        output_path = tmp_path / "out.txt"
        output_path.write_text("real skill output from past run", encoding="utf-8")

        assert capture_all.should_skip_existing_output(output_path) is True

    def test_should_rewrite_when_file_contains_sentinel(self, tmp_path: Path) -> None:
        output_path = tmp_path / "out.txt"
        output_path.write_text("SKILL_INVOCATION_SKIPPED: budget", encoding="utf-8")

        assert capture_all.should_skip_existing_output(output_path) is False

    def test_should_not_skip_when_file_missing(self, tmp_path: Path) -> None:
        output_path = tmp_path / "missing.txt"

        assert capture_all.should_skip_existing_output(output_path) is False
