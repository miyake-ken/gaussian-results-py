"""Tests for gaussian_job_results.serializer."""

from __future__ import annotations

import json
from pathlib import Path

from gaussian_job_results import parse_log, to_json, write_json


def test_to_json_round_trip(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result)
    decoded = json.loads(blob)

    info = decoded["run_info"]

    md = info["metadata"]
    assert md["package"] == "Gaussian"
    assert md["success"] is True
    assert md["basis_set"] == "6-31++G(d,p)"
    assert "DFT" in md["methods"]

    assert info["natom"] == 11
    assert info["temperature"] == 298.15
    assert info["pressure"] == 1.0
    assert info["optdone"] is True

    # source_path is serialized as a plain string.
    assert isinstance(info["source_path"], str)
    assert info["source_path"].endswith("main.out")


def test_to_json_excludes_raw(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    decoded = json.loads(to_json(result))
    assert "raw" not in decoded


def test_to_json_top_level_keys(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    decoded = json.loads(to_json(result))
    # Single namespace; raw is excluded.
    assert set(decoded.keys()) == {"run_info"}


def test_to_json_keys_sorted_recursively(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result)
    decoded = json.loads(blob)

    # Top-level run_info keys are alphabetized.
    run_info_keys = list(decoded["run_info"].keys())
    assert run_info_keys == sorted(run_info_keys)

    # metadata nested keys are alphabetized.
    metadata_keys = list(decoded["run_info"]["metadata"].keys())
    assert metadata_keys == sorted(metadata_keys)


def test_write_json_creates_parent_dirs(
    tmp_path: Path, replica_log_path: Path
) -> None:
    result = parse_log(replica_log_path)
    target = tmp_path / "deep" / "nested" / "result.json"

    write_json(result, target)

    assert target.exists()
    decoded = json.loads(target.read_text())
    assert decoded["run_info"]["natom"] == 11


def test_to_json_indent_none_returns_compact(
    replica_log_path: Path,
) -> None:
    result = parse_log(replica_log_path)
    blob = to_json(result, indent=None)
    assert "\n" not in blob


def test_metadata_timedelta_values_are_iso_strings(
    replica_log_path: Path,
) -> None:
    # Gaussian logs typically include cpu_time / wall_time. These should
    # be serialized as ISO 8601 strings starting with "PT". If the replica
    # fixture does not include either key, the test simply asserts nothing —
    # the timedelta branch is exercised directly by test_json_safe.
    result = parse_log(replica_log_path)
    md = result.run_info.metadata
    for key in ("cpu_time", "wall_time"):
        if key not in md:
            continue
        values = md[key]
        # The coercion uses tuple(...) for sequences but JSON renders as list.
        assert isinstance(values, (list, tuple))
        for entry in values:
            assert isinstance(entry, str)
            assert entry.startswith("PT")
