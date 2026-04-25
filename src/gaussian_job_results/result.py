"""Curated, JSON-friendly result type for a parsed GAUSSIAN log.

This dataclass intentionally exposes a small, opinionated subset of what
``cclib`` parses out of a Gaussian ``.out`` file. The full ``ccData`` object
is available on :attr:`GaussianResult.raw` for callers that need attributes
not surfaced here.

All sequence/array fields are plain Python tuples (recursively for 2-D
geometry data) so that :func:`dataclasses.asdict` produces a JSON-ready
structure with no numpy types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

GeometryRow = tuple[float, float, float]


@dataclass(frozen=True)
class GaussianResult:
    """Parsed, curated result of a single GAUSSIAN job log."""

    source_path: Path
    package: str
    package_version: str | None
    success: bool
    methods: tuple[str, ...]
    basis_set: str | None
    natom: int
    charge: int | None
    multiplicity: int | None
    optdone: bool
    final_energy_eV: float | None
    final_geometry_angstrom: tuple[GeometryRow, ...] | None
    atomic_numbers: tuple[int, ...]
    vibfreqs_cm1: tuple[float, ...] | None
    vibirs_km_per_mol: tuple[float, ...] | None
    zpve_hartree: float | None
    enthalpy_hartree: float | None
    freeenergy_hartree: float | None
    entropy_hartree_per_K: float | None
    temperature_K: float | None
    pressure_atm: float | None
    raw: object | None = field(default=None, repr=False, compare=False)
