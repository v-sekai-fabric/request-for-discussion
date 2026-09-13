# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Tier 3: cut the transform budget by decimating chains, scored on bend error.

Tiers 1 and 2 remove components and collision checks but not one transform:
merging preserves bone count, pruning touches no bones. The transform budget only
falls by deleting bones, which genuinely changes how a chain moves -- the one
reduction that has to be measured rather than argued.

Two corrections are baked in here, both found by the numbers refusing to make
sense:

  * A spring-bone component drives a TREE, not a chain. The avatar's Skirt_Root
    is 57 bones spanning 0.296 m -- 14 panels of 5 -- and modelling it as one
    serial chain invented segments between bones in different branches, giving a
    reference simulation that bent 73 deg on average. Chains are split into
    root-to-leaf paths first.
  * Savings are counted per COMPONENT, because that is what the platform counts,
    while dynamics are scored per PATH, because that is what is physical.

Scoring uses a rigid-motion-invariant bend metric: angles between consecutive
segments, unchanged by any translation or rotation of the whole chain.

Run:  pixi run python tier3_decimate.py springbones.json
"""

from __future__ import annotations

import collections
import json
import math
import sys

import numpy as np

from springbone_mujoco import build_model, decimate_chain, load_chains, simulate

POOR_TRANSFORMS = 256
BUDGET_P95_DEG = 8.0     # bend deviation a viewer will not read as wrong
MIN_PATH_BONES = 4       # below this there is no interior bone to spare


def bend_signature(traj):
    seg = np.diff(traj, axis=1)
    n = np.linalg.norm(seg, axis=2, keepdims=True)
    seg = seg / np.clip(n, 1e-12, None)
    dots = np.clip((seg[:, :-1] * seg[:, 1:]).sum(axis=2), -1.0, 1.0)
    return np.arccos(dots)


def resample(sig, n=10):
    if sig.shape[1] == 0:
        return np.zeros((sig.shape[0], n))
    x = np.linspace(0.0, 1.0, sig.shape[1])
    xi = np.linspace(0.0, 1.0, n)
    return np.stack([np.interp(xi, x, sig[f]) for f in range(sig.shape[0])])


def bend_error_deg(ref, cand, samples=10):
    a, b = resample(bend_signature(ref), samples), resample(bend_signature(cand), samples)
    t = min(a.shape[0], b.shape[0])
    d = np.abs(a[:t] - b[:t])
    return math.degrees(float(d.mean())), math.degrees(float(np.percentile(d, 95)))


def component_of(chain_name: str) -> str:
    return chain_name.split("#", 1)[0]


def main(path):
    chains, _ = load_chains(path)               # split into serial paths
    raw = json.load(open(path, encoding="utf-8"))
    total = sum(len(p.get("bones", [])) for p in raw["springbones"])
    need = total - POOR_TRANSFORMS
    print(f"transforms {total}, limit {POOR_TRANSFORMS} -> must remove {need}")
    print(f"{len(chains)} serial paths after branch split\n")

    by_comp = collections.defaultdict(list)
    for c in chains:
        by_comp[component_of(c.name)].append(c)

    print(f"{'component':<18} {'paths':>5} {'bones':>6}  every  {'saved':>5} "
          f"{'mean':>7} {'p95':>7}  (deg)")

    plan, saved_total = [], 0
    for comp, paths in sorted(by_comp.items(), key=lambda kv: -sum(len(c.bones) for c in kv[1])):
        bones = sum(len(c.bones) for c in paths)
        usable = [p for p in paths if len(p.bones) >= MIN_PATH_BONES]
        if not usable:
            continue

        best = None
        for every in (2, 3):
            means, p95s, saved = [], [], 0
            for p in usable:
                d = decimate_chain(p, every)
                if len(d.bones) >= len(p.bones):
                    continue
                ref = simulate(build_model([p]), duration=3.0)
                cand = simulate(build_model([d]), duration=3.0)
                m, q = bend_error_deg(ref, cand)
                means.append(m)
                p95s.append(q)
                saved += len(p.bones) - len(d.bones)
            if not means:
                continue
            mean_d, p95_d = float(np.mean(means)), float(np.max(p95s))
            ok = p95_d <= BUDGET_P95_DEG
            print(f"{comp:<18} {len(paths):>5} {bones:>6}    /{every}  {saved:>5} "
                  f"{mean_d:7.3f} {p95_d:7.3f}  {'OK' if ok else ''}")
            if ok and (best is None or saved > best[1]):
                best = (every, saved, mean_d, p95_d)
        if best:
            plan.append((comp, *best))
            saved_total += best[1]

    print(f"\n=== PLAN (worst-path p95 bend deviation <= {BUDGET_P95_DEG} deg) ===")
    for comp, every, saved, mean_d, p95_d in sorted(plan, key=lambda p: -p[2]):
        print(f"  {comp:<18} keep every {every}  saves {saved:>3} transforms"
              f"   (mean {mean_d:.2f} deg, worst p95 {p95_d:.2f} deg)")
    remaining = total - saved_total
    verdict = ("OK, under 256" if remaining <= POOR_TRANSFORMS
               else f"STILL OVER by {remaining - POOR_TRANSFORMS}")
    print(f"\n  transforms saved: {saved_total}   {total} -> {remaining}   {verdict}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "springbones.json")
