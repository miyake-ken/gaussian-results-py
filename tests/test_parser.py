"""Tests for gaussian_job_results.parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from gaussian_job_results import (
    GaussianResult,
    GaussianRunInfo,
    GaussianRunSetup,
    parse_compound,
    parse_log,
)


def test_parse_log_normal_termination(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)

    assert isinstance(result, GaussianResult)
    assert isinstance(result.run_info, GaussianRunInfo)
    assert isinstance(result.run_setup, GaussianRunSetup)

    info = result.run_info
    assert info.success is True
    assert info.package == "Gaussian"
    assert info.package_version is not None
    assert info.package_version.startswith("2016") or info.package_version.startswith("16")
    assert "DFT" in info.methods
    assert info.optdone is True

    setup = result.run_setup
    assert setup.basis_set == "6-31++G(d,p)"
    assert setup.natom == 11
    assert setup.charge == 1
    assert setup.mult == 1
    assert setup.temperature == pytest.approx(298.15)
    assert setup.pressure == pytest.approx(1.0)

    # gbasis / scannames: this fixture is opt+freq without gfprint or a scan,
    # so cclib does not populate these attributes — both are None.
    assert setup.gbasis is None
    assert setup.scannames is None


def test_parse_log_raw_is_populated(replica_log_path: Path) -> None:
    # `raw` is always set; outputs are read from it.
    result = parse_log(replica_log_path)
    assert result.raw is not None
    assert hasattr(result.raw, "scfenergies")
    # Final SCF energy in eV is finite and negative.
    assert float(result.raw.scfenergies[-1]) < 0
    # 3N - 6 = 27 vibrational modes for 11 atoms.
    assert len(result.raw.vibfreqs) == 27


def test_parse_log_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_log(tmp_path / "nope.out")


def test_parse_log_unrecognized_file(replica_gjf_path: Path) -> None:
    # Pass the .gjf input deck — cclib does not recognize it as a parsable
    # output log and ccread returns None.
    with pytest.raises(ValueError, match="cclib could not identify"):
        parse_log(replica_gjf_path)


def test_parse_log_accepts_str_path(replica_log_path: Path) -> None:
    result = parse_log(str(replica_log_path))
    assert result.run_info.success is True


def test_parse_compound_main_out_preferred(
    replica_compound_dir: Path,
) -> None:
    result = parse_compound(replica_compound_dir)
    assert result.run_info.source_path.name == "main.out"
    assert result.run_info.success is True


def test_parse_compound_no_log_found(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no log matching"):
        parse_compound(tmp_path)
