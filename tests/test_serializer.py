"""Tests for gaussian_job_results.serializer."""

from __future__ import annotations

import json
from pathlib import Path

from gaussian_job_results import parse_log, to_json, write_json


def test_to_json_round_trip(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result)
    decoded = json.loads(blob)

    assert decoded["package"] == "Gaussian"
    assert decoded["success"] is True
    assert decoded["natom"] == 11
    assert decoded["temperature_K"] == 298.15
    assert len(decoded["vibfreqs_cm1"]) == 27
    assert len(decoded["final_geometry_angstrom"]) == 11
    # source_path is serialized as a plain string.
    assert isinstance(decoded["source_path"], str)
    assert decoded["source_path"].endswith("main.out")


def test_to_json_excludes_raw(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path, keep_raw=True)
    decoded = json.loads(to_json(result))
    assert "raw" not in decoded


def test_to_json_keys_sorted(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result)
    decoded_keys = list(json.loads(blob).keys())
    assert decoded_keys == sorted(decoded_keys)


def test_write_json_creates_parent_dirs(
    tmp_path: Path, replica_log_path: Path
) -> None:
    result = parse_log(replica_log_path)
    target = tmp_path / "deep" / "nested" / "result.json"

    write_json(result, target)

    assert target.exists()
    decoded = json.loads(target.read_text())
    assert decoded["natom"] == 11


def test_to_json_indent_none_returns_compact(
    replica_log_path: Path,
) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result, indent=None)
    # Compact output has no newlines from indentation.
    assert "\n" not in blob
