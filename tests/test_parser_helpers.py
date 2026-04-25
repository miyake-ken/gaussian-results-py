"""Defensive-path tests for the small helpers in parser.py.

These exist so a partially-populated ``ccData`` (truncated log, killed job,
unsupported method) degrades to ``None`` rather than raising. The replica
fixture is fully populated, so these branches need to be exercised against
synthetic inputs.
"""

from __future__ import annotations

from gaussian_job_results.parser import (
    _float_or_none,
    _gbasis,
    _int_or_none,
    _optional_tuple_of_str,
    _str_or_none,
    _tuple_of_str,
)


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
    assert _tuple_of_str(42) == ()


def test_optional_tuple_of_str_paths() -> None:
    assert _optional_tuple_of_str(None) is None
    assert _optional_tuple_of_str("R1") == ("R1",)
    assert _optional_tuple_of_str(["R1", "R2"]) == ("R1", "R2")
    # Empty iterable collapses to None to indicate absence.
    assert _optional_tuple_of_str([]) is None
    # Non-iterable, non-string falls back to None.
    assert _optional_tuple_of_str(42) is None


def test_gbasis_none_and_empty() -> None:
    assert _gbasis(None) is None
    assert _gbasis([]) is None


def test_gbasis_valid_shape() -> None:
    # cclib gbasis: list of [(label, [(exp, coef), ...]), ...] per atom.
    raw = [
        [("S", [(1.0, 0.5), (2.0, 0.5)])],
        [("P", [(3.0, 1.0)])],
    ]
    result = _gbasis(raw)
    assert result == (
        (("S", ((1.0, 0.5), (2.0, 0.5))),),
        (("P", ((3.0, 1.0),)),),
    )


def test_gbasis_malformed_shape() -> None:
    # Missing the contraction pair; helper returns None instead of raising.
    assert _gbasis([[("S",)]]) is None
