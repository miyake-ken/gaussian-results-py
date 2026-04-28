"""Export a parsed Gaussian result as a Tripos mol2 file via OpenBabel."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Literal

from openbabel import openbabel as ob
from openbabel import pybel

from .parser import parse_log
from .result import GaussianResult

ChargeSource = Literal["auto", "esp", "mulliken", "none"]

_VALID_CHARGE_SOURCES: tuple[str, ...] = ("auto", "esp", "mulliken", "none")

_AUTO_PRIORITY: tuple[str, ...] = ("esp", "mulliken")

_CHARGE_LABELS: dict[str, str] = {
    "esp": "ESP",
    "mulliken": "Mulliken",
}


class NotConvergedError(ValueError):
    """Raised when a Gaussian opt run did not converge and the caller did
    not pass ``allow_incomplete=True``."""


def _build_molecule(
    data: Any,
    *,
    allow_incomplete: bool,
    charge_source: ChargeSource = "auto",
) -> pybel.Molecule:
    if charge_source not in _VALID_CHARGE_SOURCES:
        raise ValueError(
            f"invalid charge_source {charge_source!r}; "
            f"expected one of {list(_VALID_CHARGE_SOURCES)}"
        )

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

    resolved = _resolve_charges(data, charge_source, expected_natom=len(atomnos))

    obmol = ob.OBMol()
    obmol.BeginModify()
    atoms: list[ob.OBAtom] = []
    for z, (x, y, z_coord) in zip(atomnos, last_frame, strict=True):
        atom = obmol.NewAtom()
        atom.SetAtomicNum(int(z))
        atom.SetVector(float(x), float(y), float(z_coord))
        atoms.append(atom)
    obmol.EndModify()

    obmol.ConnectTheDots()
    obmol.PerceiveBondOrders()

    if resolved is not None:
        label, values = resolved
        for atom, value in zip(atoms, values, strict=True):
            atom.SetPartialCharge(float(value))
        obmol.SetPartialChargesPerceived(True)
        pair = ob.OBPairData()
        pair.SetAttribute("PartialCharges")
        pair.SetValue(label)
        obmol.CloneData(pair)

    return pybel.Molecule(obmol)


def _resolve_charges(
    data: Any,
    charge_source: ChargeSource,
    *,
    expected_natom: int,
) -> tuple[str, tuple[float, ...]] | None:
    """Return ``(label, values)`` to inject, or ``None`` to skip.

    Raises ``ValueError`` when the user asked for a specific source that
    is missing or length-mismatched. ``auto`` silently falls through to
    ``None`` so callers without any charges still get a Gasteiger mol2.
    """
    if charge_source == "none":
        return None

    atomcharges = getattr(data, "atomcharges", None) or {}

    if charge_source == "auto":
        for key in _AUTO_PRIORITY:
            values = atomcharges.get(key)
            if values is not None and len(values) == expected_natom:
                return _CHARGE_LABELS[key], tuple(float(v) for v in values)
        return None

    values = atomcharges.get(charge_source)
    if values is None:
        raise ValueError(
            f"charge_source={charge_source!r} requested but the parsed log "
            f"has no {charge_source!r} entry in atomcharges"
        )
    if len(values) != expected_natom:
        raise ValueError(
            f"{charge_source!r} charges length mismatch: "
            f"{len(values)} values vs {expected_natom} atoms"
        )
    return _CHARGE_LABELS[charge_source], tuple(float(v) for v in values)


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
    charge_source: ChargeSource = "auto",
) -> Path:
    """Write the optimized geometry of ``result`` as a Tripos mol2 file.

    ``charge_source`` controls the partial-charge column written into
    ``<TRIPOS>ATOM``:

    - ``"auto"`` (default): inject ESP charges if present, else Mulliken,
      else fall through to OpenBabel's default Gasteiger perception.
    - ``"esp"`` / ``"mulliken"``: require that source; raise
      ``ValueError`` if the parsed log lacks it.
    - ``"none"``: never inject; OpenBabel emits its default Gasteiger
      ``GASTEIGER`` mol2 instead of ``USER_CHARGES``.

    Note: ``"esp"`` is a Merz-Kollman ESP fit, NOT restrained ESP (RESP).
    True RESP requires a separate ``antechamber``/``resp`` step.

    See ``docs/superpowers/specs/2026-04-27-out-to-mol2-export-design.md``
    section 4.1 for the full contract.
    """
    out = Path(output_path)
    molecule = _build_molecule(
        result.raw,
        allow_incomplete=allow_incomplete,
        charge_source=charge_source,
    )
    return _write_mol2(molecule, out, overwrite=overwrite)


def export_mol2(
    log_path: Path | str,
    output_path: Path | str,
    *,
    allow_incomplete: bool = False,
    overwrite: bool = False,
    charge_source: ChargeSource = "auto",
) -> Path:
    """Convenience: ``parse_log(log_path)`` then ``result_to_mol2``."""
    result = parse_log(log_path)
    return result_to_mol2(
        result,
        output_path,
        allow_incomplete=allow_incomplete,
        overwrite=overwrite,
        charge_source=charge_source,
    )
