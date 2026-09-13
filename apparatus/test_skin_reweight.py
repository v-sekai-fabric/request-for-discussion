# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Property tests for skin reweighting, each with its falsification (RFD 2247)."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from skin_reweight import MAX_INFLUENCES, reweight

S = settings(max_examples=150, deadline=None)
floats = lambda lo, hi: st.floats(min_value=lo, max_value=hi,
                                  allow_nan=False, allow_infinity=False)


@st.composite
def weight_matrices(draw, min_v=1, max_v=40, min_j=1, max_j=30):
    V = draw(st.integers(min_v, max_v))
    J = draw(st.integers(min_j, max_j))
    vals = draw(st.lists(floats(-0.5, 3.0), min_size=V * J, max_size=V * J))
    return np.array(vals, dtype=np.float64).reshape(V, J)


@S
@given(w=weight_matrices())
def test_rows_sum_to_one(w):
    """PROPERTY: every row sums to 1, the invariant linear blend skinning needs."""
    out, _ = reweight(w)
    assert np.allclose(out.sum(axis=1), 1.0, atol=1e-9)


@S
@given(w=weight_matrices())
def test_no_negative_weights(w):
    """PROPERTY: no negative influence survives; it would drag vertices backwards."""
    out, _ = reweight(w)
    assert (out >= 0.0).all()


@S
@given(w=weight_matrices(min_j=5, max_j=30), k=st.integers(1, 4))
def test_influence_budget_respected(w, k):
    """PROPERTY: never more than k influences per vertex; the engine budget is 4."""
    out, _ = reweight(w, max_influences=k)
    assert (out > 1e-6).sum(axis=1).max() <= k


@S
@given(w=weight_matrices(min_j=6, max_j=20))
def test_keeps_the_largest_influences(w):
    """PROPERTY: the kept set is the top-k by magnitude, not an arbitrary k."""
    out, _ = reweight(w)
    pos = np.clip(w, 0.0, None)
    for i in range(w.shape[0]):
        if pos[i].sum() <= 1e-12:
            continue                      # dead row: rescued, not ranked
        kept = np.where(out[i] > 1e-6)[0]
        k = min(MAX_INFLUENCES, w.shape[1])
        expected = set(np.argsort(pos[i])[-k:])
        assert set(kept).issubset(expected | {int(np.argmax(pos[i]))})


@S
@given(J=st.integers(1, 12), V=st.integers(1, 20))
def test_FALSIFY_all_zero_rows_are_rescued_not_left_zero(J, V):
    """FALSIFICATION: an all-zero row is rescued, not left to collapse to origin."""
    w = np.zeros((V, J), dtype=np.float64)
    out, rep = reweight(w)
    assert rep["dead_rows"] == V
    assert np.allclose(out.sum(axis=1), 1.0)
    assert (out >= 0).all()


@S
@given(w=weight_matrices(min_j=5, max_j=20), scale=floats(0.01, 50.0))
def test_scale_invariance_where_no_row_dies(w, scale):
    """PROPERTY: ratio decides, not magnitude, where scaling kills no row."""
    a, ra = reweight(w)
    b, rb = reweight(w * scale)
    assume(ra["dead_rows"] == 0 and rb["dead_rows"] == 0)
    assert np.allclose(a, b, atol=1e-9)


@S
@given(tiny=floats(1e-14, 9e-13), scale=floats(2.0, 50.0))
def test_scaling_a_near_floor_row_changes_whether_it_dies(tiny, scale):
    """PROPERTY: the dead-row floor is absolute, so scaling moves a row across it."""
    w = np.zeros((2, 5), dtype=np.float64)
    w[0, 4] = 1.0
    w[1, 0] = tiny
    assume(tiny <= 1e-12 < tiny * scale)

    below, r_below = reweight(w)
    above, r_above = reweight(w * scale)

    assert r_below["dead_rows"] == 1, "a row under the floor is dead"
    assert r_above["dead_rows"] == 0, "the same row scaled over the floor is not"
    assert below[1].argmax() != 0, "the dead row was bound to the dominant joint"
    assert above[1].argmax() == 0, "the live row kept its own influence"
    assert np.allclose(below.sum(axis=1), 1.0)
    assert np.allclose(above.sum(axis=1), 1.0)


@S
@given(w=weight_matrices(min_j=5, max_j=20))
def test_FALSIFY_reweighting_changes_unnormalised_input(w):
    """FALSIFICATION: on input that does not sum to 1, the output must differ."""
    pos = np.clip(w, 0.0, None)
    sums = pos.sum(axis=1)
    if np.allclose(sums, 1.0, atol=1e-6) or (sums <= 1e-12).all():
        return                              # already normalised, or all dead
    out, _ = reweight(w)
    assert not np.allclose(out, w, atol=1e-9)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
