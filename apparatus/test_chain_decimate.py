# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from chain_decimate import (apply_plan, children_of, find_runs, fold_weights,
                            is_protected, plan)

S = settings(max_examples=150, deadline=None)

@st.composite
def skeleton(draw, min_j=4, max_j=40):
    J = draw(st.integers(min_j, max_j))
    par = [-1] + [draw(st.integers(0, i - 1)) for i in range(1, J)]
    names = [f"Bone_{i}" for i in range(J)]
    return np.array(par, dtype=np.int64), names

@st.composite
def strand_skeleton(draw):
    n_strands = draw(st.integers(1, 5))
    length = draw(st.integers(3, 7))
    par, names = [-1], ["Hips"]
    for s in range(n_strands):
        prev = 0
        for k in range(length):
            par.append(prev)
            prev = len(par) - 1
            names.append(f"Skirt_{chr(65 + s)}_{k}")
    return np.array(par, dtype=np.int64), names

@S
@given(sk=skeleton(), k=st.integers(2, 4))
def test_kept_joints_form_a_valid_tree(sk, k):
    par, names = sk
    keep, drop = plan(par, names, keep_every=k)
    new_par, _ = apply_plan(par, keep)
    assert len(new_par) == len(keep)
    assert (new_par < len(keep)).all()
    for i, p in enumerate(new_par):
        assert p < i                      # parents precede children
    assert int((new_par < 0).sum()) == int((np.asarray(par) < 0).sum())

@S
@given(sk=skeleton(), k=st.integers(2, 4))
def test_FALSIFY_no_branch_point_is_ever_dropped(sk, k):
    par, names = sk
    keep, drop = plan(par, names, keep_every=k)
    kids = children_of(par)
    for j in drop:
        assert len(kids.get(j, [])) == 1

@S
@given(sk=strand_skeleton(), k=st.integers(2, 4))
def test_FALSIFY_humanoid_bones_are_never_dropped(sk, k):
    par, names = sk
    _, drop = plan(par, names, keep_every=k)
    assert not any(is_protected(names[j]) for j in drop)

@S
@given(sk=strand_skeleton(), k=st.integers(2, 4))
def test_FALSIFY_weight_never_crosses_to_another_strand(sk, k):
    par, names = sk
    keep, _ = plan(par, names, keep_every=k)
    _, fold = apply_plan(par, keep)

    def strand(j):
        n = names[j]
        return n.split("_")[1] if n.startswith("Skirt_") else None

    for j in range(len(par)):
        src, dst = strand(j), strand(int(keep[fold[j]]))
        if src is not None and dst is not None:
            assert src == dst

@S
@given(sk=skeleton(), k=st.integers(2, 4))
def test_folding_conserves_every_vertex_total_weight(sk, k):
    par, names = sk
    keep, _ = plan(par, names, keep_every=k)
    _, fold = apply_plan(par, keep)
    rng = np.random.default_rng(0)
    w = rng.random((12, len(par)))
    out = fold_weights(w, fold, len(keep))
    assert np.allclose(out.sum(axis=1), w.sum(axis=1), atol=1e-9)

@S
@given(sk=skeleton(min_j=6), k=st.integers(2, 4))
def test_FALSIFY_endpoints_of_a_run_survive(sk, k):
    par, names = sk
    _, drop = plan(par, names, keep_every=k)
    dropped = set(drop)
    for run in find_runs(par, names):
        assert run[0] not in dropped
        assert run[-1] not in dropped

@S
@given(sk=skeleton())
def test_FALSIFY_runs_do_not_overlap(sk):
    par, names = sk
    seen = set()
    for run in find_runs(par, names):
        assert not (seen & set(run))
        seen |= set(run)

@S
@given(sk=skeleton(), k=st.integers(2, 4))
def test_keep_every_one_changes_nothing(sk, k):
    par, names = sk
    keep, drop = plan(par, names, keep_every=1)
    assert len(drop) == 0
    assert len(keep) == len(par)

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
