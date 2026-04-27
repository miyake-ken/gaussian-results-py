"""Parse a GAUSSIAN .out log into a :class:`GaussianResult` via cclib."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cclib
from cclib.parser.data import ccData

from ._json_safe import to_json_safe
from .discovery import find_log_in_compound_dir
from .result import GaussianResult, GaussianRunMetadata, GbasisAtom


def parse_log(path: Path | str) -> GaussianResult:
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
        raise ValueError(f"cclib could not identify {log_path} as a supported QC output")

    raw_meta = getattr(data, "metadata", None)
    package = raw_meta.get("package") if isinstance(raw_meta, dict) else None
    if not package:
        raise ValueError(
            f"cclib parsed {log_path} but could not identify the QC package "
            "(no metadata.package; likely an unsupported log format)"
        )

    return _build_result(log_path, data)


def parse_compound(
    compound_dir: Path | str,
    *,
    log_glob: str = "*.out",
) -> GaussianResult:
    """Parse the canonical log inside a compound directory."""
    log_path = find_log_in_compound_dir(Path(compound_dir), log_glob=log_glob)
    return parse_log(log_path)


def _build_result(source_path: Path, data: ccData) -> GaussianResult:
    return GaussianResult(
        run_info=_build_metadata(source_path, data),
        raw=data,
    )


def _build_metadata(source_path: Path, data: ccData) -> GaussianRunMetadata:
    raw_metadata: dict[str, Any] = getattr(data, "metadata", {}) or {}
    coerced_metadata = to_json_safe(raw_metadata)
    return GaussianRunMetadata(
        source_path=source_path,
        metadata=coerced_metadata,
        optdone=bool(getattr(data, "optdone", False)),
        natom=int(getattr(data, "natom", 0) or 0),
        charge=_int_or_none(getattr(data, "charge", None)),
        mult=_int_or_none(getattr(data, "mult", None)),
        gbasis=_gbasis(getattr(data, "gbasis", None)),
        scannames=_optional_tuple_of_str(getattr(data, "scannames", None)),
        temperature=_float_or_none(getattr(data, "temperature", None)),
        pressure=_float_or_none(getattr(data, "pressure", None)),
    )


def _gbasis(value: Any) -> tuple[GbasisAtom, ...] | None:
    if value is None:
        return None
    try:
        atoms: list[GbasisAtom] = []
        for atom_funcs in value:
            funcs: list[tuple[str, tuple[tuple[float, float], ...]]] = []
            for func in atom_funcs:
                label = str(func[0])
                contractions = tuple((float(c[0]), float(c[1])) for c in func[1])
                funcs.append((label, contractions))
            atoms.append(tuple(funcs))
        if not atoms:
            return None
        return tuple(atoms)
    except (TypeError, ValueError, IndexError):
        return None


def _optional_tuple_of_str(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    try:
        result = tuple(str(x) for x in value)
    except TypeError:
        return None
    return result if result else None


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
