"""Parse a GAUSSIAN .out log into a :class:`GaussianResult` via cclib."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cclib

from .discovery import find_log_in_compound_dir
from .result import GaussianResult, GeometryRow


def parse_log(path: Path | str, *, keep_raw: bool = True) -> GaussianResult:
    """Parse a single Gaussian ``.out`` / ``.log`` file.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: if cclib does not recognize the file as a supported
            QC package log.
    """
    log_path = Path(path)
    if not log_path.exists():
        raise FileNotFoundError(f"log file not found: {log_path}")

    data = cclib.io.ccread(str(log_path))
    if data is None:
        raise ValueError(
            f"cclib could not identify {log_path} as a supported QC output"
        )

    return _build_result(log_path, data, keep_raw=keep_raw)


def parse_compound(
    compound_dir: Path | str,
    *,
    log_glob: str = "*.out",
    keep_raw: bool = True,
) -> GaussianResult:
    """Parse the canonical log inside a compound directory."""
    log_path = find_log_in_compound_dir(Path(compound_dir), log_glob=log_glob)
    return parse_log(log_path, keep_raw=keep_raw)


def _build_result(
    source_path: Path, data: Any, *, keep_raw: bool
) -> GaussianResult:
    metadata = getattr(data, "metadata", {}) or {}

    final_energy = _last_float(getattr(data, "scfenergies", None))
    final_geometry = _last_geometry(getattr(data, "atomcoords", None))
    atomic_numbers = _ints(getattr(data, "atomnos", None))
    vibfreqs = _floats(getattr(data, "vibfreqs", None))
    vibirs = _floats(getattr(data, "vibirs", None))

    return GaussianResult(
        source_path=source_path,
        package=str(metadata.get("package", "")),
        package_version=_str_or_none(metadata.get("package_version")),
        success=bool(metadata.get("success", False)),
        methods=_tuple_of_str(metadata.get("methods")),
        basis_set=_str_or_none(metadata.get("basis_set")),
        natom=int(getattr(data, "natom", 0) or 0),
        charge=_int_or_none(getattr(data, "charge", None)),
        multiplicity=_int_or_none(getattr(data, "mult", None)),
        optdone=bool(getattr(data, "optdone", False)),
        final_energy_eV=final_energy,
        final_geometry_angstrom=final_geometry,
        atomic_numbers=atomic_numbers,
        vibfreqs_cm1=vibfreqs,
        vibirs_km_per_mol=vibirs,
        zpve_hartree=_float_or_none(getattr(data, "zpve", None)),
        enthalpy_hartree=_float_or_none(getattr(data, "enthalpy", None)),
        freeenergy_hartree=_float_or_none(getattr(data, "freeenergy", None)),
        entropy_hartree_per_K=_float_or_none(getattr(data, "entropy", None)),
        temperature_K=_float_or_none(getattr(data, "temperature", None)),
        pressure_atm=_float_or_none(getattr(data, "pressure", None)),
        raw=data if keep_raw else None,
    )


def _last_float(seq: Any) -> float | None:
    if seq is None:
        return None
    try:
        if len(seq) == 0:
            return None
        return float(seq[-1])
    except (TypeError, ValueError):
        return None


def _last_geometry(coords: Any) -> tuple[GeometryRow, ...] | None:
    if coords is None:
        return None
    try:
        if len(coords) == 0:
            return None
        last = coords[-1]
        return tuple((float(r[0]), float(r[1]), float(r[2])) for r in last)
    except (TypeError, ValueError, IndexError):
        return None


def _ints(seq: Any) -> tuple[int, ...]:
    if seq is None:
        return ()
    try:
        return tuple(int(x) for x in seq)
    except (TypeError, ValueError):
        return ()


def _floats(seq: Any) -> tuple[float, ...] | None:
    if seq is None:
        return None
    try:
        return tuple(float(x) for x in seq)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _tuple_of_str(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    try:
        return tuple(str(x) for x in value)
    except TypeError:
        return ()
