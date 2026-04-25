"""JSON serialization for :class:`GaussianResult`.

Every numeric / textual field on :class:`GaussianRunMetadata` is already
a JSON-safe Python type — primitives, tuples (for ``gbasis`` /
``scannames``), and a pre-coerced ``metadata`` dict produced by
:func:`gaussian_job_results._json_safe.to_json_safe`. A single pass
through the standard library ``json`` module is sufficient. The ``raw``
``ccData`` attribute is stripped before encoding.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .result import GaussianResult


def _to_serializable(result: GaussianResult) -> dict:
    payload = asdict(result)
    payload.pop("raw", None)
    payload["run_info"]["source_path"] = str(result.run_info.source_path)
    return payload


def to_json(result: GaussianResult, *, indent: int | None = 2) -> str:
    """Serialize a :class:`GaussianResult` to a JSON document string."""
    return json.dumps(_to_serializable(result), indent=indent, sort_keys=True)


def write_json(
    result: GaussianResult, path: Path, *, indent: int | None = 2
) -> None:
    """Write a :class:`GaussianResult` as JSON to ``path``.

    Parent directories are created on demand (``mkdir(parents=True,
    exist_ok=True)``).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_json(result, indent=indent))
