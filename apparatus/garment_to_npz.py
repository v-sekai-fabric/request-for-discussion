# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Convert an editor-exported garment into the npz shape SkinTokens loads.

NpzLazyAsset reads vertices, faces, joint_names, parents, matrix_local,
matrix_world and skin, so a skeleton can be SUPPLIED rather than predicted --
which is what `use_skeleton=True` conditions on. That matters because reducing a
chain's bone count is only safe if the mesh can be reskinned onto the reduced
skeleton; decimating bones alone leaves the skin bound to bones that are gone.

Deliberately does not touch the bpy loader: probe_forward reaches SkinTokens
through this npz path precisely so Blender is never imported.
"""

from __future__ import annotations

import argparse
import json

import numpy as np


def load_export(path):
    d = json.load(open(path, encoding="utf-8"))
    V = int(d["vertex_count"])
    J = int(d["joint_count"])
    vertices = np.asarray(d["vertices"], dtype=np.float32).reshape(V, 3)
    faces = np.asarray(d["faces"], dtype=np.int64).reshape(-1, 3)
    parents = np.asarray(d["parents"], dtype=np.int64)
    names = np.asarray(d["joint_names"], dtype=object)
    mworld = np.asarray(d["matrix_world"], dtype=np.float32).reshape(J, 4, 4)

    # Dense (V, J) ground truth from the engine's 4-influence representation.
    si = np.asarray(d["skin_indices"], dtype=np.int64).reshape(V, 4)
    sw = np.asarray(d["skin_weights"], dtype=np.float32).reshape(V, 4)
    skin = np.zeros((V, J), dtype=np.float32)
    rows = np.repeat(np.arange(V), 4)
    np.add.at(skin, (rows, si.ravel()), sw.ravel())
    return dict(vertices=vertices, faces=faces, parents=parents,
                joint_names=names, matrix_world=mworld, skin=skin)


def local_from_world(mworld, parents):
    """matrix_local = parent_world^-1 @ world, with roots keeping their world."""
    out = np.empty_like(mworld)
    for j in range(mworld.shape[0]):
        p = int(parents[j])
        out[j] = mworld[j] if p < 0 else np.linalg.inv(mworld[p]) @ mworld[j]
    return out


def write_npz(data, out_path, include_skin=False):
    kw = dict(
        vertices=data["vertices"],
        faces=data["faces"],
        joint_names=data["joint_names"],
        parents=data["parents"],
        matrix_world=data["matrix_world"],
        matrix_local=local_from_world(data["matrix_world"], data["parents"]),
        armature_name=np.array("Armature", dtype=object),
    )
    if include_skin:
        kw["skin"] = data["skin"]
    np.savez(out_path, **kw)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_json")
    ap.add_argument("--out", default="garment.npz")
    ap.add_argument("--with-skin", action="store_true",
                    help="include ground-truth skin (for comparison, not for prediction)")
    a = ap.parse_args()

    d = load_export(a.export_json)
    V, J = d["vertices"].shape[0], d["parents"].shape[0]
    used = int((d["skin"] > 1e-6).any(axis=0).sum())
    infl = float((d["skin"] > 1e-6).sum(axis=1).mean())
    print(f"{a.export_json}: verts={V} faces={len(d['faces'])} joints={J}")
    print(f"  joints actually skinned: {used}/{J}")
    print(f"  ground-truth influences/vertex: {infl:.2f}")
    print(f"  ground-truth row sums: {d['skin'].sum(axis=1).min():.4f} .. "
          f"{d['skin'].sum(axis=1).max():.4f}")
    print("wrote", write_npz(d, a.out, include_skin=a.with_skin))


if __name__ == "__main__":
    main()
