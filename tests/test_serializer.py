"""Tests for gaussian_job_results.serializer."""

from __future__ import annotations

import json
from pathlib import Path

from gaussian_job_results import parse_log, to_json, write_json


def test_to_json_round_trip(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result)
    decoded = json.loads(blob)

    assert decoded["run_info"]["package"] == "Gaussian"
    assert decoded["run_info"]["success"] is True
    assert decoded["run_setup"]["natom"] == 11
    assert decoded["run_setup"]["temperature"] == 298.15
    assert decoded["run_setup"]["pressure"] == 1.0
    # source_path is serialized as a plain string under run_info.
    assert isinstance(decoded["run_info"]["source_path"], str)
    assert decoded["run_info"]["source_path"].endswith("main.out")


def test_to_json_excludes_raw(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    decoded = json.loads(to_json(result))
    assert "raw" not in decoded


def test_to_json_top_level_keys(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    decoded = json.loads(to_json(result))
    # Exactly two namespaces; raw is excluded.
    assert set(decoded.keys()) == {"run_info", "run_setup"}


def test_to_json_keys_sorted(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result)
    decoded = json.loads(blob)
    # sort_keys=True applies recursively.
    for value in decoded.values():
        keys = list(value.keys())
        assert keys == sorted(keys)


def test_write_json_creates_parent_dirs(
    tmp_path: Path, replica_log_path: Path
) -> None:
    result = parse_log(replica_log_path)
    target = tmp_path / "deep" / "nested" / "result.json"

    write_json(result, target)

    assert target.exists()
    decoded = json.loads(target.read_text())
    assert decoded["run_setup"]["natom"] == 11


def test_to_json_indent_none_returns_compact(
    replica_log_path: Path,
) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result, indent=None)
    # Compact output has no newlines from indentation.
    assert "\n" not in blob
