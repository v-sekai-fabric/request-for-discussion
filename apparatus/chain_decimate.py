# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0

from __future__ import annotations

import numpy as np

HUMANOID = (
    "hips", "spine", "chest", "upperchest", "neck", "head", "eye", "jaw",
    "shoulder", "upperarm", "lowerarm", "hand", "upperleg", "lowerleg",
    "foot", "toe", "thumb", "index", "middle", "ring", "little", "pinky",
)

def is_protected(name: str) -> bool:
    n = str(name).lower().replace("_", "").replace(".", "")
    return any(h in n for h in HUMANOID)

def children_of(parents):
    kids = {}
    for j, p in enumerate(np.asarray(parents)):
        kids.setdefault(int(p), []).append(j)
    return kids

def find_runs(parents, names, min_length=3):
    parents = np.asarray(parents)
    kids = children_of(parents)
    prot = [is_protected(n) for n in names]

    runs, seen = [], set()
    for j in range(len(parents)):
        if j in seen or prot[j]:
            continue
        p = int(parents[j])
        if p >= 0 and not prot[p] and len(kids.get(p, [])) == 1:
            continue
        run = []
        cur = j
        while (cur >= 0 and not prot[cur] and len(kids.get(cur, [])) <= 1
               and cur not in seen):
            run.append(cur)
            seen.add(cur)
            nxt = kids.get(cur, [])
            cur = nxt[0] if len(nxt) == 1 else -1
        if len(run) >= min_length:
            runs.append(run)
    return runs

def plan(parents, names, keep_every=2, min_length=3):
    parents = np.asarray(parents)
    drop = set()
    for run in find_runs(parents, names, min_length=min_length):
        for k, j in enumerate(run):
            if k == 0 or k == len(run) - 1:
                continue
            if k % keep_every != 0:
                drop.add(j)
    keep = np.array([j for j in range(len(parents)) if j not in drop], dtype=np.int64)
    return keep, sorted(drop)

def apply_plan(parents, keep):
    parents = np.asarray(parents)
    kept = set(int(k) for k in keep)
    new_index = {int(j): i for i, j in enumerate(keep)}

    def nearest_kept_ancestor(j):
        p = int(parents[j])
        while p >= 0 and p not in kept:
            p = int(parents[p])
        return p

    new_parents = np.array(
        [new_index[nearest_kept_ancestor(int(j))] if nearest_kept_ancestor(int(j)) >= 0
         else -1 for j in keep], dtype=np.int64)

    fold = np.empty(len(parents), dtype=np.int64)
    for j in range(len(parents)):
        t = j
        while t >= 0 and t not in kept:
            t = int(parents[t])
        fold[j] = new_index[t] if t >= 0 else 0
    return new_parents, fold

def fold_weights(skin, fold, n_new):
    skin = np.asarray(skin, dtype=np.float64)
    out = np.zeros((skin.shape[0], n_new), dtype=np.float64)
    np.add.at(out.T, fold[:skin.shape[1]], skin.T)
    return out

def summarise(parents, names, keep, drop, runs=None):
    runs = runs if runs is not None else find_runs(parents, names)
    return (f"  runs found: {len(runs)} "
            f"(lengths {sorted((len(r) for r in runs), reverse=True)[:12]})\n"
            f"  joints: {len(parents)} -> {len(keep)}  (dropped {len(drop)})")
