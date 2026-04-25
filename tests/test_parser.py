"""Tests for gaussian_job_results.parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from gaussian_job_results import (
    GaussianResult,
    GaussianRunMetadata,
    parse_compound,
    parse_log,
)


def test_parse_log_normal_termination(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)

    assert isinstance(result, GaussianResult)
    assert isinstance(result.run_info, GaussianRunMetadata)

    info = result.run_info

    # Identity / termination details are mirrored from cclib metadata.
    md = info.metadata
    assert md["package"] == "Gaussian"
    package_version = md["package_version"]
    assert isinstance(package_version, str)
    assert package_version.startswith("2016") or package_version.startswith("16")
    assert md["success"] is True
    assert "DFT" in md["methods"]
    assert md["basis_set"] == "6-31++G(d,p)"

    # ccData-derived attributes stay as direct fields.
    assert info.optdone is True
    assert info.natom == 11
    assert info.charge == 1
    assert info.mult == 1
    assert info.temperature == pytest.approx(298.15)
    assert info.pressure == pytest.approx(1.0)

    # gbasis / scannames: this fixture is opt+freq without gfprint or a scan,
    # so cclib does not populate these attributes — both are None.
    assert info.gbasis is None
    assert info.scannames is None


def test_parse_log_raw_is_populated(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)
    assert result.raw is not None
    assert hasattr(result.raw, "scfenergies")
    assert float(result.raw.scfenergies[-1]) < 0
    # 3N - 6 = 27 vibrational modes for 11 atoms.
    assert len(result.raw.vibfreqs) == 27


def test_parse_log_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_log(tmp_path / "nope.out")


def test_parse_log_unrecognized_file(replica_gjf_path: Path) -> None:
    with pytest.raises(ValueError, match="cclib could not identify"):
        parse_log(replica_gjf_path)


def test_parse_log_accepts_str_path(replica_log_path: Path) -> None:
    result = parse_log(str(replica_log_path))
    assert result.run_info.metadata["success"] is True


def test_parse_compound_main_out_preferred(
    replica_compound_dir: Path,
) -> None:
    result = parse_compound(replica_compound_dir)
    assert result.run_info.source_path.name == "main.out"
    assert result.run_info.metadata["success"] is True


def test_parse_compound_no_log_found(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no log matching"):
        parse_compound(tmp_path)


def test_metadata_is_a_fresh_dict(replica_log_path: Path) -> None:
    # Mutating the parsed metadata must not bleed back into cclib state.
    result = parse_log(replica_log_path)
    result.run_info.metadata["package"] = "MUTATED"
    second = parse_log(replica_log_path)
    assert second.run_info.metadata["package"] == "Gaussian"
