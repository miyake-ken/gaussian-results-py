"""Recursive coercion of Python values into JSON-safe primitives.

This is a private module used by :mod:`gaussian_job_results.parser` to
normalize the cclib ``data.metadata`` dict before it is stored on
:class:`gaussian_job_results.result.GaussianRunMetadata`. It is also
intended to be reused by a future ``raw`` ccData → JSON serializer.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any

import numpy as np
import polars as pl
from whenever import TimeDelta


def to_json_safe(value: Any) -> Any:
    """Recursively coerce ``value`` to JSON-friendly Python primitives.

    Coercions:

    * ``None``/``bool``/``int``/``float``/``str`` pass through unchanged.
    * ``datetime.timedelta`` → ISO 8601 duration string via
      :class:`whenever.TimeDelta`.
    * numpy scalar / array → Python primitive(s) via :class:`polars.Series`.
    * ``Mapping`` → ``dict`` (keys stringified, values recursed).
    * ``list`` / ``tuple`` → ``tuple`` (values recursed).
    * Other unknown types → ``str(value)`` as a safe fallback.

    Order of ``isinstance`` checks matters:

    * ``bool`` must be matched before ``int`` because
      ``isinstance(True, int)`` is ``True``.
    * ``np.generic`` (scalar) before ``np.ndarray``.
    * ``Mapping`` before ``list`` / ``tuple`` so ``OrderedDict`` etc. land
      in the dict branch.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, datetime.timedelta):
        return TimeDelta(seconds=value.total_seconds()).format_iso()
    if isinstance(value, np.generic):
        return _via_polars_scalar(value)
    if isinstance(value, np.ndarray):
        return _via_polars_array(value)
    if isinstance(value, Mapping):
        return {str(k): to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(to_json_safe(v) for v in value)
    return str(value)


def _via_polars_scalar(scalar: np.generic) -> Any:
    return pl.Series([scalar]).to_list()[0]


def _via_polars_array(array: np.ndarray) -> Any:
    if array.ndim == 0:
        return _via_polars_scalar(array.item())
    if array.ndim == 1:
        return tuple(pl.Series(array).to_list())
    return tuple(_via_polars_array(sub) for sub in array)
