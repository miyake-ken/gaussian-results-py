"""Tests for gaussian_job_results.discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from gaussian_job_results import find_log_in_compound_dir


def test_finds_preferred_basename(tmp_path: Path) -> None:
    (tmp_path / "main.out").write_text("dummy")
    (tmp_path / "stray.out").write_text("dummy")

    found = find_log_in_compound_dir(tmp_path)
    assert found.name == "main.out"


def test_falls_back_to_unique_glob_match(tmp_path: Path) -> None:
    (tmp_path / "job_42.out").write_text("dummy")

    found = find_log_in_compound_dir(tmp_path)
    assert found.name == "job_42.out"


def test_ambiguous_glob_without_preferred_raises(tmp_path: Path) -> None:
    (tmp_path / "a.out").write_text("dummy")
    (tmp_path / "b.out").write_text("dummy")

    with pytest.raises(ValueError, match="ambiguous log discovery"):
        find_log_in_compound_dir(tmp_path)


def test_no_match_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no log matching"):
        find_log_in_compound_dir(tmp_path)


def test_missing_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        find_log_in_compound_dir(tmp_path / "does-not-exist")


def test_path_pointing_at_file_raises(tmp_path: Path) -> None:
    target = tmp_path / "regular.txt"
    target.write_text("not a directory")
    with pytest.raises(FileNotFoundError, match="not a directory"):
        find_log_in_compound_dir(target)


def test_custom_preferred_basename(tmp_path: Path) -> None:
    (tmp_path / "result.log").write_text("dummy")
    (tmp_path / "other.log").write_text("dummy")

    found = find_log_in_compound_dir(
        tmp_path, log_glob="*.log", preferred_basenames=("result.log",)
    )
    assert found.name == "result.log"


def test_replica_fixture(replica_compound_dir: Path) -> None:
    found = find_log_in_compound_dir(replica_compound_dir)
    assert found.name == "main.out"
