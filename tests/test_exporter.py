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
                [[0.0, 0.0, 0.0], [0.0, 0.0, 1.50]],   # initial
                [[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]],   # last (used)
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
        atomnos=None,           # type: ignore[arg-type]
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
