"""Curated, JSON-friendly result type for a parsed GAUSSIAN log.

The dataclass groups a small, opinionated subset of cclib's parsed
attributes into two curated namespaces and keeps the raw cclib
``ccData`` object as the canonical source of computed outputs:

* :class:`GaussianRunInfo` — run identity (source path, package
  metadata, optimization completion, termination status).
* :class:`GaussianRunSetup` — calculation setup (basis, atom count,
  charge, multiplicity, scan names, temperature, pressure).
* :attr:`GaussianResult.raw` — the cclib ``ccData`` object. All
  computed quantities (final energy, geometry, vibrational data,
  thermochemistry) are read from here.

Field names match cclib's attribute names where applicable so that
callers can move freely between the curated view and ``raw`` without
remembering a translation table.

All sequence/array fields are plain Python tuples (recursively for
nested structures like ``gbasis``) so that :func:`dataclasses.asdict`
produces a JSON-ready structure with no numpy types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

GeometryRow = tuple[float, float, float]
GbasisContraction = tuple[float, float]
GbasisFunction = tuple[str, tuple[GbasisContraction, ...]]
GbasisAtom = tuple[GbasisFunction, ...]


@dataclass(frozen=True)
class GaussianRunInfo:
    """Run identity, package, and termination status.

    ``package`` is always a ``str`` (never ``None``); when cclib does not
    populate ``metadata['package']`` it defaults to the empty string ``""``.
    This asymmetry with ``package_version`` (``str | None``) is intentional
    and matches the spec — callers can rely on ``package`` being defined.
    """

    source_path: Path
    package: str
    package_version: str | None
    success: bool
    methods: tuple[str, ...]
    optdone: bool


@dataclass(frozen=True)
class GaussianRunSetup:
    """Calculation setup: the inputs that shaped the SCF."""

    basis_set: str | None
    natom: int
    charge: int | None
    mult: int | None
    gbasis: tuple[GbasisAtom, ...] | None
    scannames: tuple[str, ...] | None
    temperature: float | None
    pressure: float | None


@dataclass(frozen=True)
class GaussianResult:
    """Parsed result of a single GAUSSIAN job log.

    ``raw`` is always populated; computed outputs live there.
    """

    run_info: GaussianRunInfo
    run_setup: GaussianRunSetup
    raw: object = field(repr=False, compare=False)
