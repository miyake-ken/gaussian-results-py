"""Tests for gaussian_job_results.exporter."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest


def test_exporter_module_exposes_public_symbols():
    from gaussian_job_results.exporter import (
        NotConvergedError,
        export_mol2,
        result_to_mol2,
    )

    assert issubclass(NotConvergedError, ValueError)
    assert callable(result_to_mol2)
    assert callable(export_mol2)


from gaussian_job_results.exporter import NotConvergedError, _build_molecule


@dataclass
class _StubCcData:
    """Mutable ccData-shaped stub for fast unit tests without log parsing."""

    atomnos: np.ndarray
    atomcoords: np.ndarray
    optdone: bool = True
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {"package": "Gaussian"}


def _h2_stub(*, optdone: bool = True) -> _StubCcData:
    """Two-atom H2-like stub: well-defined geometry, deterministic bonds."""
    return _StubCcData(
        atomnos=np.array([1, 1], dtype=int),
        atomcoords=np.array([[[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]]], dtype=float),
        optdone=optdone,
    )


def test_build_molecule_raises_when_not_converged():
    data = _h2_stub(optdone=False)
    with pytest.raises(NotConvergedError):
        _build_molecule(data, allow_incomplete=False)


def test_build_molecule_allows_incomplete_when_opted_in():
    data = _h2_stub(optdone=False)
    mol = _build_molecule(data, allow_incomplete=True)
    assert mol.OBMol.NumAtoms() == 2


def test_build_molecule_uses_last_frame():
    data = _StubCcData(
        atomnos=np.array([1, 1], dtype=int),
        atomcoords=np.array(
            [
                [[0.0, 0.0, 0.0], [0.0, 0.0, 1.50]],  # initial
                [[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]],  # last (used)
            ],
            dtype=float,
        ),
    )
    mol = _build_molecule(data, allow_incomplete=False)
    atoms = list(mol.atoms)
    assert atoms[0].atomicnum == 1
    assert atoms[1].atomicnum == 1
    assert atoms[0].coords == pytest.approx((0.0, 0.0, 0.0), abs=1e-6)
    assert atoms[1].coords == pytest.approx((0.0, 0.0, 0.74), abs=1e-6)


def test_build_molecule_rejects_missing_atoms():
    data = _StubCcData(
        atomnos=None,  # type: ignore[arg-type]
        atomcoords=np.array([], dtype=float),
    )
    with pytest.raises(ValueError, match="atomnos"):
        _build_molecule(data, allow_incomplete=True)


def test_build_molecule_rejects_length_mismatch():
    data = _StubCcData(
        atomnos=np.array([1, 1, 1], dtype=int),
        atomcoords=np.array([[[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]]], dtype=float),
    )
    with pytest.raises(ValueError, match="length mismatch"):
        _build_molecule(data, allow_incomplete=True)


from pathlib import Path

from gaussian_job_results.exporter import _write_mol2


def _h2_molecule():
    return _build_molecule(_h2_stub(), allow_incomplete=False)


def test_write_mol2_writes_file_at_path(tmp_path):
    out = tmp_path / "h2.mol2"
    written = _write_mol2(_h2_molecule(), out, overwrite=False)
    assert written == out.resolve()
    assert out.exists()
    text = out.read_text()
    assert "<TRIPOS>MOLECULE" in text
    assert "<TRIPOS>ATOM" in text


def test_write_mol2_refuses_to_overwrite_by_default(tmp_path):
    out = tmp_path / "exists.mol2"
    out.write_text("placeholder")
    with pytest.raises(FileExistsError):
        _write_mol2(_h2_molecule(), out, overwrite=False)
    assert out.read_text() == "placeholder"


def test_write_mol2_overwrites_when_requested(tmp_path):
    out = tmp_path / "exists.mol2"
    out.write_text("placeholder")
    _write_mol2(_h2_molecule(), out, overwrite=True)
    assert "<TRIPOS>MOLECULE" in out.read_text()


def test_write_mol2_does_not_leave_tmp_file_after_failure(tmp_path, monkeypatch):
    out = tmp_path / "h2.mol2"

    def boom(self: Path, target: Path) -> Path:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(Path, "replace", boom)
    with pytest.raises(OSError, match="simulated"):
        _write_mol2(_h2_molecule(), out, overwrite=False)

    leftover = list(tmp_path.glob("*.tmp-*"))
    assert leftover == [], f"tmp file survived: {leftover}"
    assert not out.exists()


from gaussian_job_results import GaussianResult, parse_log
from gaussian_job_results.exporter import result_to_mol2
from gaussian_job_results.result import GaussianRunMetadata


def _result_from_stub(data: _StubCcData) -> GaussianResult:
    return GaussianResult(
        run_info=GaussianRunMetadata(
            source_path=Path("/dev/null"),
            metadata={},
            optdone=data.optdone,
            natom=int(len(data.atomnos)),
            charge=None,
            mult=None,
            gbasis=None,
            scannames=None,
            temperature=None,
            pressure=None,
        ),
        raw=data,
    )


def _parse_mol2_atoms(text: str) -> list[tuple[str, float, float, float]]:
    """Pull (symbol, x, y, z) tuples from the <TRIPOS>ATOM section."""
    atoms: list[tuple[str, float, float, float]] = []
    in_atom = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("@<TRIPOS>"):
            in_atom = stripped == "@<TRIPOS>ATOM"
            continue
        if not in_atom or not stripped:
            continue
        parts = stripped.split()
        atom_name = parts[1]
        symbol = "".join(ch for ch in atom_name if ch.isalpha())
        atoms.append((symbol, float(parts[2]), float(parts[3]), float(parts[4])))
    return atoms


def test_result_to_mol2_writes_file(tmp_path, replica_result):
    out = tmp_path / "main.mol2"
    written = result_to_mol2(replica_result, out)
    assert written == out.resolve()
    assert out.exists()
    text = out.read_text()
    assert "<TRIPOS>MOLECULE" in text
    assert "<TRIPOS>ATOM" in text
    assert "<TRIPOS>BOND" in text


def test_result_to_mol2_atom_count_matches_natom(tmp_path, replica_result):
    out = tmp_path / "main.mol2"
    result_to_mol2(replica_result, out)
    atoms = _parse_mol2_atoms(out.read_text())
    assert len(atoms) == replica_result.run_info.natom


def test_result_to_mol2_coords_match_last_frame(tmp_path, replica_result):
    out = tmp_path / "main.mol2"
    result_to_mol2(replica_result, out)

    written_atoms = _parse_mol2_atoms(out.read_text())
    last = replica_result.raw.atomcoords[-1]
    for (sym, x, y, z), (rx, ry, rz) in zip(written_atoms, last, strict=True):
        assert abs(x - rx) <= 1e-4
        assert abs(y - ry) <= 1e-4
        assert abs(z - rz) <= 1e-4


def test_result_to_mol2_raises_when_not_converged(tmp_path):
    out = tmp_path / "h2.mol2"
    result = _result_from_stub(_h2_stub(optdone=False))
    with pytest.raises(NotConvergedError):
        result_to_mol2(result, out)
    assert not out.exists()


def test_result_to_mol2_allow_incomplete_writes(tmp_path):
    out = tmp_path / "h2.mol2"
    result = _result_from_stub(_h2_stub(optdone=False))
    result_to_mol2(result, out, allow_incomplete=True)
    assert out.exists()


def test_result_to_mol2_raises_on_existing_output(tmp_path):
    out = tmp_path / "h2.mol2"
    out.write_text("existing")
    result = _result_from_stub(_h2_stub())
    with pytest.raises(FileExistsError):
        result_to_mol2(result, out)
    assert out.read_text() == "existing"


def test_result_to_mol2_overwrites_when_requested(tmp_path):
    out = tmp_path / "h2.mol2"
    out.write_text("existing")
    result = _result_from_stub(_h2_stub())
    result_to_mol2(result, out, overwrite=True)
    assert "<TRIPOS>MOLECULE" in out.read_text()


from gaussian_job_results.exporter import export_mol2


def test_export_mol2_matches_result_to_mol2(tmp_path, replica_log_path, replica_result):
    via_path = tmp_path / "viapath.mol2"
    via_result = tmp_path / "viaresult.mol2"

    export_mol2(replica_log_path, via_path)
    result_to_mol2(replica_result, via_result)

    assert _parse_mol2_atoms(via_path.read_text()) == _parse_mol2_atoms(via_result.read_text())


def test_export_mol2_raises_for_missing_log(tmp_path):
    out = tmp_path / "x.mol2"
    with pytest.raises(FileNotFoundError):
        export_mol2(tmp_path / "does-not-exist.out", out)


def test_top_level_imports_expose_exporter_symbols():
    import gaussian_job_results as g

    assert g.NotConvergedError is not None
    assert g.result_to_mol2 is not None
    assert g.export_mol2 is not None
    assert "NotConvergedError" in g.__all__
    assert "result_to_mol2" in g.__all__
    assert "export_mol2" in g.__all__


def _h2_stub_with_charges(charges_dict: dict) -> _StubCcData:
    stub = _h2_stub()
    stub.atomcharges = charges_dict
    return stub


def test_build_molecule_default_auto_with_no_atomcharges_skips_partial():
    """Backward-compat: stub without atomcharges + default charge_source must
    leave PartialChargesPerceived False (so mol2 falls back to Gasteiger)."""
    mol = _build_molecule(_h2_stub(), allow_incomplete=False)
    assert mol.OBMol.HasPartialChargesPerceived() is False


def test_build_molecule_charge_source_esp_sets_user_charges():
    data = _h2_stub_with_charges({"esp": np.array([-0.5, 0.5])})
    mol = _build_molecule(data, allow_incomplete=False, charge_source="esp")
    assert mol.OBMol.HasPartialChargesPerceived() is True
    atoms = list(mol.atoms)
    assert atoms[0].partialcharge == pytest.approx(-0.5)
    assert atoms[1].partialcharge == pytest.approx(0.5)


def test_build_molecule_charge_source_auto_prefers_esp_over_mulliken():
    data = _h2_stub_with_charges(
        {
            "esp": np.array([-0.1, 0.1]),
            "mulliken": np.array([-0.9, 0.9]),
        }
    )
    mol = _build_molecule(data, allow_incomplete=False, charge_source="auto")
    atoms = list(mol.atoms)
    assert atoms[0].partialcharge == pytest.approx(-0.1)


def test_build_molecule_charge_source_auto_falls_back_to_mulliken():
    data = _h2_stub_with_charges({"mulliken": np.array([-0.3, 0.3])})
    mol = _build_molecule(data, allow_incomplete=False, charge_source="auto")
    atoms = list(mol.atoms)
    assert atoms[0].partialcharge == pytest.approx(-0.3)


def test_build_molecule_charge_source_none_skips_partial_charges():
    data = _h2_stub_with_charges({"esp": np.array([-0.5, 0.5])})
    mol = _build_molecule(data, allow_incomplete=False, charge_source="none")
    assert mol.OBMol.HasPartialChargesPerceived() is False


def test_build_molecule_charge_source_explicit_missing_raises():
    """Asking for ESP when the log has no ESP block must fail loudly."""
    data = _h2_stub_with_charges({"mulliken": np.array([-0.3, 0.3])})
    with pytest.raises(ValueError, match="esp"):
        _build_molecule(data, allow_incomplete=False, charge_source="esp")


def test_build_molecule_charge_source_invalid_raises():
    with pytest.raises(ValueError, match="charge_source"):
        _build_molecule(_h2_stub(), allow_incomplete=False, charge_source="bogus")


def test_build_molecule_length_mismatch_in_charges_raises():
    data = _h2_stub_with_charges({"esp": np.array([-0.5, 0.5, 0.0])})
    with pytest.raises(ValueError, match="length"):
        _build_molecule(data, allow_incomplete=False, charge_source="esp")


def test_result_to_mol2_writes_user_charges_for_real_log(tmp_path, replica_result):
    out = tmp_path / "main.mol2"
    result_to_mol2(replica_result, out, charge_source="esp")
    text = out.read_text()
    assert "USER_CHARGES" in text
    atom_lines = []
    in_atom = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("@<TRIPOS>"):
            in_atom = s == "@<TRIPOS>ATOM"
            continue
        if in_atom and s:
            atom_lines.append(s)
    parts = atom_lines[0].split()
    assert float(parts[-1]) == pytest.approx(-0.0999, abs=1e-4)


def test_result_to_mol2_default_auto_picks_esp_for_real_log(tmp_path, replica_result):
    out = tmp_path / "main.mol2"
    result_to_mol2(replica_result, out)
    text = out.read_text()
    assert "USER_CHARGES" in text


def test_result_to_mol2_charge_source_none_emits_default_gasteiger(tmp_path, replica_result):
    out = tmp_path / "main.mol2"
    result_to_mol2(replica_result, out, charge_source="none")
    text = out.read_text()
    assert "USER_CHARGES" not in text
    assert "GASTEIGER" in text
