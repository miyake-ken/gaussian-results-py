"""Export a parsed Gaussian result as a Tripos mol2 file via OpenBabel."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from openbabel import openbabel as ob
from openbabel import pybel

from .parser import parse_log
from .result import GaussianResult


class NotConvergedError(ValueError):
    """Raised when a Gaussian opt run did not converge and the caller did
    not pass ``allow_incomplete=True``."""


def _build_molecule(data: Any, *, allow_incomplete: bool) -> pybel.Molecule:
    optdone = bool(getattr(data, "optdone", False))
    if not optdone and not allow_incomplete:
        raise NotConvergedError(
            "Gaussian opt did not converge (optdone=False). "
            "Pass allow_incomplete=True to export the last recorded geometry."
        )

    atomnos = getattr(data, "atomnos", None)
    atomcoords = getattr(data, "atomcoords", None)
    if atomnos is None or atomcoords is None or len(atomcoords) == 0:
        raise ValueError(
            "ccData has no atomnos / atomcoords; cannot build mol2 geometry."
        )

    last_frame = atomcoords[-1]
    if len(last_frame) != len(atomnos):
        raise ValueError(
            f"atomnos / atomcoords length mismatch: "
            f"{len(atomnos)} vs {len(last_frame)}"
        )

    obmol = ob.OBMol()
    obmol.BeginModify()
    for z, (x, y, z_coord) in zip(atomnos, last_frame, strict=True):
        atom = obmol.NewAtom()
        atom.SetAtomicNum(int(z))
        atom.SetVector(float(x), float(y), float(z_coord))
    obmol.EndModify()

    obmol.ConnectTheDots()
    obmol.PerceiveBondOrders()

    return pybel.Molecule(obmol)


def _write_mol2(molecule: pybel.Molecule, output_path: Path, *, overwrite: bool) -> Path:
    if output_path.exists() and not overwrite:
        raise FileExistsError(output_path)
    tmp = output_path.with_suffix(
        output_path.suffix + f".tmp-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    )
    try:
        molecule.write("mol2", str(tmp), overwrite=True)
        tmp.replace(output_path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return output_path.resolve()


def result_to_mol2(
    result: GaussianResult,
    output_path: Path | str,
    *,
    allow_incomplete: bool = False,
    overwrite: bool = False,
) -> Path:
    """Write the optimized geometry of ``result`` as a Tripos mol2 file.

    See ``docs/superpowers/specs/2026-04-27-out-to-mol2-export-design.md``
    section 4.1 for the full contract.
    """
    out = Path(output_path)
    molecule = _build_molecule(result.raw, allow_incomplete=allow_incomplete)
    return _write_mol2(molecule, out, overwrite=overwrite)


def export_mol2(
    log_path: Path | str,
    output_path: Path | str,
    *,
    allow_incomplete: bool = False,
    overwrite: bool = False,
) -> Path:
    """Convenience: ``parse_log(log_path)`` then ``result_to_mol2``."""
    result = parse_log(log_path)
    return result_to_mol2(
        result,
        output_path,
        allow_incomplete=allow_incomplete,
        overwrite=overwrite,
    )
