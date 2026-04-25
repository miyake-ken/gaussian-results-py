"""Defensive-path tests for the small helpers in parser.py.

These exist so a partially-populated ``ccData`` (truncated log, killed job,
unsupported method) degrades to ``None`` rather than raising. The replica
fixture is fully populated, so these branches need to be exercised against
synthetic inputs.
"""

from __future__ import annotations

from gaussian_job_results.parser import (
    _float_or_none,
    _floats,
    _ints,
    _int_or_none,
    _last_float,
    _last_geometry,
    _str_or_none,
    _tuple_of_str,
)


def test_last_float_none_and_empty() -> None:
    assert _last_float(None) is None
    assert _last_float([]) is None


def test_last_float_invalid_type() -> None:
    # An object that has no len/__getitem__ should swallow.
    assert _last_float(object()) is None


def test_last_geometry_none_and_empty() -> None:
    assert _last_geometry(None) is None
    assert _last_geometry([]) is None


def test_last_geometry_bad_shape() -> None:
    # Rows shorter than 3 elements raise IndexError; helper returns None.
    assert _last_geometry([[(1.0, 2.0)]]) is None


def test_floats_none_and_bad_value() -> None:
    assert _floats(None) is None
    assert _floats(["not-a-number"]) is None


def test_ints_none_and_bad_value() -> None:
    assert _ints(None) == ()
    assert _ints(["not-an-int"]) == ()


def test_float_or_none_paths() -> None:
    assert _float_or_none(None) is None
    assert _float_or_none("nope") is None
    assert _float_or_none(1.5) == 1.5


def test_int_or_none_paths() -> None:
    assert _int_or_none(None) is None
    assert _int_or_none("nope") is None
    assert _int_or_none(7) == 7


def test_str_or_none_paths() -> None:
    assert _str_or_none(None) is None
    assert _str_or_none("") is None
    assert _str_or_none("Gaussian") == "Gaussian"


def test_tuple_of_str_paths() -> None:
    assert _tuple_of_str(None) == ()
    assert _tuple_of_str("DFT") == ("DFT",)
    assert _tuple_of_str(["DFT", "MP2"]) == ("DFT", "MP2")
    # Non-iterable, non-string falls back to empty.
    assert _tuple_of_str(42) == ()
