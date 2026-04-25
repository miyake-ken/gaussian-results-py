"""Tests for gaussian_job_results._json_safe.to_json_safe."""

from __future__ import annotations

import datetime
from collections import OrderedDict

import numpy as np
from whenever import TimeDelta

from gaussian_job_results._json_safe import to_json_safe


def test_primitives_pass_through() -> None:
    assert to_json_safe(None) is None
    assert to_json_safe(0) == 0
    assert to_json_safe(1.5) == 1.5
    assert to_json_safe("") == ""
    assert to_json_safe("hello") == "hello"


def test_bool_matched_before_int() -> None:
    # isinstance(True, int) is True — bool branch must be first.
    assert to_json_safe(True) is True
    assert to_json_safe(False) is False


def test_timedelta_to_iso_8601_round_trip() -> None:
    td = datetime.timedelta(seconds=12.5)
    iso = to_json_safe(td)
    assert isinstance(iso, str)
    assert iso.startswith("PT")
    # Round-trip via whenever to confirm the format is parseable.
    parsed = TimeDelta.parse_iso(iso)
    assert parsed.in_seconds() == 12.5


def test_numpy_float_scalar() -> None:
    out = to_json_safe(np.float64(1.5))
    assert isinstance(out, float)
    assert out == 1.5


def test_numpy_int_scalar() -> None:
    out = to_json_safe(np.int64(7))
    assert isinstance(out, int)
    assert out == 7


def test_numpy_bool_scalar() -> None:
    out = to_json_safe(np.bool_(True))
    assert out is True


def test_numpy_array_1d() -> None:
    out = to_json_safe(np.array([1, 2, 3], dtype=np.int32))
    assert out == (1, 2, 3)
    # Each element is a Python int, not numpy.
    for item in out:
        assert type(item) is int


def test_numpy_array_0d() -> None:
    out = to_json_safe(np.array(5.0))
    assert isinstance(out, float)
    assert out == 5.0


def test_numpy_array_2d() -> None:
    out = to_json_safe(np.array([[1, 2], [3, 4]]))
    assert out == ((1, 2), (3, 4))


def test_list_recurses_to_tuple() -> None:
    assert to_json_safe([1, "a", None]) == (1, "a", None)


def test_tuple_recurses_to_tuple() -> None:
    assert to_json_safe((1, "a", None)) == (1, "a", None)


def test_list_of_timedelta() -> None:
    items = [datetime.timedelta(seconds=1), datetime.timedelta(seconds=2)]
    out = to_json_safe(items)
    assert isinstance(out, tuple)
    assert all(isinstance(x, str) and x.startswith("PT") for x in out)


def test_mapping_stringifies_keys_and_recurses_values() -> None:
    out = to_json_safe(OrderedDict([("b", 1), ("a", 2)]))
    # Mapping path returns a dict; insertion order preserved here, sorting
    # happens later in json.dumps(sort_keys=True).
    assert out == {"b": 1, "a": 2}


def test_nested_mapping_with_numpy() -> None:
    raw = {
        "scalar": np.float64(1.5),
        "vector": np.array([1, 2]),
        "nested": {"timed": datetime.timedelta(seconds=3)},
    }
    out = to_json_safe(raw)
    assert out["scalar"] == 1.5
    assert out["vector"] == (1, 2)
    assert isinstance(out["nested"]["timed"], str)
    assert out["nested"]["timed"].startswith("PT")


def test_unknown_type_falls_back_to_str() -> None:
    class Unknown:
        def __str__(self) -> str:
            return "unknown-repr"

    assert to_json_safe(Unknown()) == "unknown-repr"


def test_empty_dict() -> None:
    assert to_json_safe({}) == {}


def test_empty_list() -> None:
    assert to_json_safe([]) == ()
