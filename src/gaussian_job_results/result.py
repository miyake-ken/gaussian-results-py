"""Curated, JSON-friendly result type for a parsed GAUSSIAN log.

The dataclass exposes a single curated namespace,
:class:`GaussianRunMetadata`, accessible via :attr:`GaussianResult.run_info`.
It surfaces cclib's full ``data.metadata`` dict verbatim under a
``metadata`` field (already normalized to JSON-safe primitives by
:func:`gaussian_job_results._json_safe.to_json_safe`) plus the
ccData-derived attributes that are not present in cclib's metadata dict.

The cclib ``ccData`` object stays on :attr:`GaussianResult.raw`. All
computed quantities (final energy, geometry, vibrational data,
thermochemistry) are read from there.

Field names match cclib's ``ccData`` attribute names where applicable so
that callers can move freely between the curated view and ``raw`` without
remembering a translation table.

All sequence/array fields are plain Python tuples (recursively for nested
structures like ``gbasis``) so that :func:`dataclasses.asdict` produces
a JSON-ready structure with no numpy types. The ``metadata`` dict is
likewise pre-coerced to JSON-safe primitives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

GeometryRow = tuple[float, float, float]
GbasisContraction = tuple[float, float]
GbasisFunction = tuple[str, tuple[GbasisContraction, ...]]
GbasisAtom = tuple[GbasisFunction, ...]


@dataclass(frozen=True)
class GaussianRunMetadata:
    """Run identity, package, termination status, and calculation setup.

    The full cclib ``data.metadata`` dict (package name, version,
    success flag, methods, basis_set, cpu_time, wall_time, …) is
    available verbatim under :attr:`metadata`. The remaining attributes
    are the cclib ``ccData`` attributes that do not appear in
    ``data.metadata`` (and hence do not duplicate it).

    The dataclass is frozen, but :attr:`metadata` is a plain ``dict``
    and is therefore mutable from Python. Treat it as read-only by
    convention; the parser builds a fresh dict on every parse, so
    mutation does not leak back into cclib state.
    """

    source_path: Path
    metadata: dict[str, Any]
    optdone: bool
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

    run_info: GaussianRunMetadata
    raw: object = field(repr=False, compare=False)
