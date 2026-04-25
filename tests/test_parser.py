"""Tests for gaussian_job_results.parser."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from gaussian_job_results import GaussianResult, parse_compound, parse_log


def test_parse_log_normal_termination(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path)

    assert isinstance(result, GaussianResult)
    assert result.success is True
    assert result.package == "Gaussian"
    assert result.package_version is not None
    assert (
        result.package_version.startswith("2016")
        or result.package_version.startswith("16")
    )
    assert "DFT" in result.methods
    assert result.basis_set == "6-31++G(d,p)"
    assert result.natom == 11
    assert result.optdone is True

    # Final energy: cclib reports scfenergies in eV.
    assert result.final_energy_eV is not None
    assert math.isfinite(result.final_energy_eV)
    assert result.final_energy_eV < 0

    # Geometry: 11 atoms, 3 coordinates each.
    geom = result.final_geometry_angstrom
    assert geom is not None
    assert len(geom) == 11
    for row in geom:
        assert len(row) == 3
        assert all(isinstance(c, float) for c in row)

    # Atomic numbers: trimethylamine cation skeleton starts with N, C, C, ...
    assert result.atomic_numbers[:3] == (7, 6, 6)
    assert len(result.atomic_numbers) == 11

    # Frequencies: 3N-6 = 27 normal modes.
    assert result.vibfreqs_cm1 is not None
    assert len(result.vibfreqs_cm1) == 27
    assert result.vibirs_km_per_mol is not None
    assert len(result.vibirs_km_per_mol) == 27

    # Thermochemistry.
    assert result.zpve_hartree is not None
    assert result.enthalpy_hartree is not None
    assert result.freeenergy_hartree is not None
    assert result.entropy_hartree_per_K is not None
    assert result.temperature_K == pytest.approx(298.15)
    assert result.pressure_atm == pytest.approx(1.0)


def test_parse_log_keep_raw_true(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path, keep_raw=True)
    assert result.raw is not None
    # cclib's parsed object exposes .scfenergies — duck-type rather than
    # importing the private cclib data class.
    assert hasattr(result.raw, "scfenergies")


def test_parse_log_keep_raw_false(replica_log_path: Path) -> None:
    result = parse_log(replica_log_path, keep_raw=False)
    assert result.raw is None


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
    assert result.success is True


def test_parse_compound_main_out_preferred(
    replica_compound_dir: Path,
) -> None:
    result = parse_compound(replica_compound_dir)
    assert result.source_path.name == "main.out"
    assert result.success is True


def test_parse_compound_no_log_found(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no log matching"):
        parse_compound(tmp_path)
