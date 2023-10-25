from string import printable
import pytest

import numpy as np
from hypothesis import given
import hypothesis.strategies as st

from stackstac.coordinates_utils import (
    descalar_obj_array,
    deduplicate_axes,
    scalar_sequence,
    unnest_dicts,
)


def test_deduplicate_axes():
    a1 = np.arange(5)
    d = deduplicate_axes(a1)
    np.testing.assert_equal(d, a1)

    a1_d0 = np.repeat(1, 5)
    d = deduplicate_axes(a1_d0)
    assert d.shape == (1,)
    np.testing.assert_equal(d, [1])

    a2 = np.arange(3 * 4).reshape(3, 4)
    d = deduplicate_axes(a2)
    np.testing.assert_equal(d, a2)

    a2_d0 = np.stack([np.arange(4)] * 3)
    d = deduplicate_axes(a2_d0)
    assert d.shape == (1, a2_d0.shape[1])
    np.testing.assert_equal(d, a2_d0[[0]])

    a2_d1 = a2_d0.T
    d = deduplicate_axes(a2_d1)
    assert d.shape == (a2_d1.shape[0], 1)
    np.testing.assert_equal(d, a2_d1[:, [0]])

    a2_d01 = np.broadcast_to(1, (3, 4))
    d = deduplicate_axes(a2_d01)
    assert d.shape == (1, 1)
    np.testing.assert_equal(d, np.broadcast_to(1, (1, 1)))


@pytest.mark.parametrize(
    "input, expected",
    [
        # Unchanged, no nesting
        ({"a": 1, "b": "foo"}, {"a": 1, "b": "foo"}),
        # Single level nesting
        ({"a": 1, "b": {"a": "foo"}}, {"a": 1, "b_a": "foo"}),
        # Single level nesting, multiple subkeys
        ({"a": 1, "b": {"a": "foo", "b": "bar"}}, {"a": 1, "b_a": "foo", "b_b": "bar"}),
        (
            # Double level nesting
            {"a": 1, "b": {"a": "foo", "b": {"x": 0}}},
            {"a": 1, "b_a": "foo", "b_b_x": 0},
        ),
        (
            # Sequences are _not_ traversed
            [{"a": {"b": "c"}}, {"a2": {"b2": "c2"}}],
            [{"a": {"b": "c"}}, {"a2": {"b2": "c2"}}],
        ),
        # Basics are unchanged
        ("abc", "abc"),
        (1, 1),
        (None, None),
        ([1, 2, "foo", True], [1, 2, "foo", True]),
        ({"a": 1, "b": "foo"}, {"a": 1, "b": "foo"}),
    ],
)
def test_unnest_dicts(input, expected):
    assert unnest_dicts(input) == expected


jsons = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats()
    | st.datetimes()
    | st.text(printable),
    lambda children: st.lists(children) | st.dictionaries(st.text(printable), children),
)
# Modified from https://hypothesis.readthedocs.io/en/latest/data.html#recursive-data


@given(jsons)
def test_scalar_sequence_roundtrip(x):
    wrapped = scalar_sequence(x)
    arr = np.array([wrapped])
    assert arr.shape == (1,)
    descalared = descalar_obj_array(arr)
    assert descalared[0] == x