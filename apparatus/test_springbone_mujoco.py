# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Property tests for springbone_mujoco, each paired with its falsification."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from springbone_mujoco import (Chain, build_model, chain_curve_error,
                               decimate_chain, resample_curve, simulate,
                               tier1_exact_merges, tier2_collider_prune)

COMBI = settings(max_examples=200, deadline=None)

floats = lambda lo, hi: st.floats(min_value=lo, max_value=hi,
                                  allow_nan=False, allow_infinity=False)

params_st = st.fixed_dictionaries({
    "pull": floats(0.0, 1.0),
    "spring": floats(0.0, 1.0),
    "stiffness": floats(0.0, 1.0),
    "gravity": floats(0.0, 1.0),
    "immobile": floats(0.0, 1.0),
    "radius": floats(0.004, 0.08),
})


def make_chain(name="c", n=6, params=None, colliders=None, seg=0.05,
               axis=(0.0, -1.0, 0.0)):
    p = params or {}
    a = np.asarray(axis, dtype=float)
    return Chain(
        name=name,
        bones=[(f"{name}_{i}", a * seg * i) for i in range(n)],
        colliders=list(colliders or []),
        pull=p.get("pull", 0.2), spring=p.get("spring", 0.05),
        stiffness=p.get("stiffness", 0.1), gravity=p.get("gravity", 1.0),
        immobile=p.get("immobile", 0.0), radius=p.get("radius", 0.02),
    )


HORIZ = (1.0, 0.0, 0.0)


def articulation(traj):
    """How much the chain BENT, in radians, invariant to rigid motion."""
    seg = np.diff(traj, axis=1)                                   # (T, N-1, 3)
    norm = np.linalg.norm(seg, axis=2, keepdims=True)
    seg = seg / np.clip(norm, 1e-12, None)
    dots = np.clip((seg[:, :-1] * seg[:, 1:]).sum(axis=2), -1.0, 1.0)
    angles = np.arccos(dots)                                      # (T, N-2)
    if angles.shape[1] == 0:
        return 0.0
    return float(np.abs(angles[-1] - angles[0]).max())



@COMBI
@given(params=params_st, n=st.integers(2, 8),
       colliders=st.lists(st.sampled_from(["L", "R", "C"]), max_size=3, unique=True))
def test_identical_chains_always_group(params, n, colliders):
    """PROPERTY: chains agreeing on every parameter and collider set are interchangeable."""
    a = make_chain("a", n, params, colliders)
    b = make_chain("b", n, params, colliders)
    groups = tier1_exact_merges([a, b])
    assert len(groups) == 1 and len(groups[0]) == 2


@COMBI
@given(params=params_st, key=st.sampled_from(
    ["pull", "spring", "stiffness", "gravity", "immobile", "radius"]),
       delta=floats(0.05, 0.5))
def test_FALSIFY_any_differing_parameter_prevents_grouping(params, key, delta):
    """FALSIFICATION: perturbing any single parameter must prevent the merge."""
    other = dict(params)
    other[key] = params[key] + delta
    a, b = make_chain("a", 6, params), make_chain("b", 6, other)
    assert tier1_exact_merges([a, b]) == [], f"grouped despite differing {key}"


@COMBI
@given(params=params_st,
       ca=st.lists(st.sampled_from(["L", "R", "C"]), min_size=1, max_size=3, unique=True),
       cb=st.lists(st.sampled_from(["L", "R", "C"]), min_size=1, max_size=3, unique=True))
def test_FALSIFY_differing_colliders_prevent_grouping(params, ca, cb):
    """FALSIFICATION: equal parameters with different colliders are not interchangeable."""
    assume(sorted(ca) != sorted(cb))
    a, b = make_chain("a", 6, params, ca), make_chain("b", 6, params, cb)
    assert tier1_exact_merges([a, b]) == []


@COMBI
@given(params=params_st, n=st.integers(2, 10), k=st.integers(2, 5))
def test_merging_conserves_transform_count(params, n, k):
    """PROPERTY: a merge changes component count, never the transform count."""
    chains = [make_chain(f"c{i}", n, params) for i in range(k)]
    before = sum(c.transform_count for c in chains)
    groups = tier1_exact_merges(chains)
    assert sum(c.transform_count for c in groups[0]) == before


@COMBI
@given(params=params_st, n=st.integers(2, 8), k=st.integers(2, 5),
       perm=st.randoms(use_true_random=False))
def test_grouping_is_order_invariant(params, n, k, perm):
    chains = [make_chain(f"c{i}", n, params) for i in range(k)]
    shuffled = list(chains)
    perm.shuffle(shuffled)
    assert (len(tier1_exact_merges(chains)[0])
            == len(tier1_exact_merges(shuffled)[0]))



@given(pull_lo=floats(0.0, 0.2), bump=floats(0.5, 3.0))
@settings(max_examples=12, deadline=None,
          suppress_health_check=[HealthCheck.too_slow])
def test_deflection_is_monotone_in_pull(pull_lo, bump):
    """PROPERTY: more pull bends less, monotonically."""
    soft = make_chain("s", 8, {"pull": pull_lo, "gravity": 1.0}, axis=HORIZ)
    stiff = make_chain("s", 8, {"pull": pull_lo + bump, "gravity": 1.0}, axis=HORIZ)
    d_soft = articulation(simulate(build_model([soft]), 2.0))
    d_stiff = articulation(simulate(build_model([stiff]), 2.0))
    assert d_stiff <= d_soft + 1e-3, f"stiff {d_stiff:.5f} rad > soft {d_soft:.5f} rad"


@given(g=floats(0.3, 1.0))
@settings(max_examples=8, deadline=None,
          suppress_health_check=[HealthCheck.too_slow])
def test_gravity_articulates_a_loose_chain(g):
    ch = make_chain("g", 8, {"gravity": g, "pull": 0.01, "immobile": 0.0}, axis=HORIZ)
    assert articulation(simulate(build_model([ch]), 2.0)) > 1e-3


@given(pull=floats(0.8, 1.0), immobile=floats(0.9, 1.0))
@settings(max_examples=8, deadline=None,
          suppress_health_check=[HealthCheck.too_slow])
def test_FALSIFY_frozen_chain_does_not_articulate(pull, immobile):
    """FALSIFICATION: a gravity-free, fully immobile chain must not bend."""
    ch = make_chain("f", 8, {"gravity": 0.0, "pull": pull,
                             "immobile": immobile, "spring": 0.0}, axis=HORIZ)
    assert articulation(simulate(build_model([ch]), 2.0)) < 5e-2



@given(dist=floats(2.0, 20.0))
@settings(max_examples=8, deadline=None,
          suppress_health_check=[HealthCheck.too_slow])
def test_far_colliders_are_prunable(dist):
    """PROPERTY: a collider never approached costs a check a frame and is prunable."""
    ch = make_chain("c", 6, colliders=["far"])
    colliders = {"far": {"p": [dist, dist, dist], "radius": 0.05}}
    m = build_model([ch])
    prunable, kept = tier2_collider_prune([ch], colliders, m, simulate(m, 1.0))
    assert len(prunable) == 1 and kept == 0


@given(radius=floats(0.4, 1.2))
@settings(max_examples=8, deadline=None,
          suppress_health_check=[HealthCheck.too_slow])
def test_FALSIFY_engaged_colliders_are_never_pruned(radius):
    """FALSIFICATION: a collider the chain engages is never pruned."""
    ch = make_chain("c", 6, colliders=["near"])
    colliders = {"near": {"p": [0.0, -0.10, 0.0], "radius": radius}}
    m = build_model([ch])
    prunable, kept = tier2_collider_prune([ch], colliders, m, simulate(m, 1.0))
    assert prunable == [] and kept == 1



@COMBI
@given(n=st.integers(4, 40), k=st.integers(2, 6))
def test_decimation_keeps_endpoints_and_shrinks(n, k):
    """PROPERTY: decimation lowers bone count and keeps the anchor and the tip."""
    ch = make_chain("c", n)
    d = decimate_chain(ch, k)
    assert len(d.bones) <= len(ch.bones)
    assert d.bones[0][0] == ch.bones[0][0]
    assert d.bones[-1][0] == ch.bones[-1][0]


@COMBI
@given(k=st.integers(2, 8), n=st.integers(2, 3))
def test_FALSIFY_tiny_chains_are_never_shortened(k, n):
    """FALSIFICATION: a chain of three or fewer is never shortened."""
    ch = make_chain("c", n)
    assert len(decimate_chain(ch, k).bones) == n


@COMBI
@given(n=st.integers(3, 60), seg=floats(0.005, 0.2), samples=st.integers(4, 32))
def test_resampling_is_invariant_to_discretisation(n, seg, samples):
    """PROPERTY: the same curve resamples alike at any source resolution."""
    fine = [np.array([0.0, -seg * i, 0.0]) for i in range(n)]
    total = seg * (n - 1)
    coarse = [np.array([0.0, -total * t, 0.0]) for t in np.linspace(0, 1, 4)]
    a, b = resample_curve(fine, samples), resample_curve(coarse, samples)
    assert np.abs(a - b).max() < 1e-6


@COMBI
@given(bend=floats(0.01, 0.2), n=st.integers(5, 30))
def test_FALSIFY_resampling_preserves_a_real_shape_difference(bend, n):
    """FALSIFICATION: a real shape difference must survive resampling."""
    straight = [np.array([0.0, -0.05 * i, 0.0]) for i in range(n)]
    bent = [np.array([bend * i, -0.05 * i, 0.0]) for i in range(n)]
    a, b = resample_curve(straight, 16), resample_curve(bent, 16)
    assert np.abs(a - b).max() > 1e-4


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
