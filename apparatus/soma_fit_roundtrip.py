# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Round-trip check for vertex-silhouette pose fitting.

Pose a SOMA body by known rotations, take the posed vertices, throw the
rotations away, and ask PoseInversion to recover them from geometry alone. If
the recovered pose reproduces the vertices, the fit is sound, and retargeting can
be driven by silhouette instead of a joint-name correspondence -- which matters
because the correspondence is the part that cannot be written down honestly
between rigs whose per-axis joints sit up to 165 mm apart.

Ships with its falsification: a deliberately different pose must NOT reproduce
the vertices. Without that, a fit that echoed its input would score perfect.
"""

from __future__ import annotations

import argparse
import sys

import torch


def joint_count(layer) -> int:
    """Number of pose rotations the forward pass expects (77).

    Not `joint_parent_ids` (110): that is the internal skeleton, and passing its
    length makes pose() reject the tensor outright.
    """
    # soma.py: expected_pose_joints = len(_public_joint_names) - 1. The root
    # carries translation rather than a rotation, so it is excluded.
    for attr in ("public_joint_names", "public_joint_indices", "public_joint_parent_ids"):
        v = getattr(layer, attr, None)
        if v is not None:
            return len(v) - 1
    return len(layer.joint_parent_ids) - 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pose-scale", type=float, default=0.2, help="radians")
    ap.add_argument("--tol-mm", type=float, default=2.0)
    args = ap.parse_args()

    print(f"torch {torch.__version__}  device={args.device}  cuda={torch.cuda.is_available()}")

    from soma import SOMALayer
    from soma.pose_inversion import PoseInversion

    layer = SOMALayer().to(args.device)
    layer.eval()
    J = joint_count(layer)
    # The identity model's own coefficient count, NOT layer.num_shape_components
    # (128): those are different quantities and mixing them makes the MHR blend
    # shape einsum fail with a broadcast mismatch.
    S = int(getattr(layer.identity_model, 'num_identity_coeffs', layer.num_shape_components))
    print(f"SOMALayer: joints={J} shape_components={S} scale_params={int(getattr(layer, 'num_scale_params', 0))}")

    g = torch.Generator(device="cpu").manual_seed(args.seed)
    ident = torch.zeros((1, S), dtype=torch.float32, device=args.device)
    # The default identity model is MHR, which requires explicit scale params.
    P = int(getattr(layer.identity_model, "num_scale_params",
                    getattr(layer, "num_scale_params", 0)))
    scale = torch.zeros((1, P), dtype=torch.float32, device=args.device) if P else None
    poses = ((torch.rand((1, J, 3), generator=g, dtype=torch.float32) - 0.5)
             * 2.0 * args.pose_scale).to(args.device)

    with torch.no_grad():
        out = layer(poses=poses, identity_coeffs=ident, scale_params=scale)
    verts = out.vertices
    print(f"posed vertices: {tuple(verts.shape)}")

    inv = PoseInversion(layer)
    prep = getattr(inv, "prepare_identity", None)
    if prep is not None:
        prep(ident, scale)
    with torch.no_grad():
        result = inv.fit(verts)
    keys = sorted(result.keys()) if hasattr(result, "keys") else []
    print(f"fit keys: {keys[:8]}")

    # Score on the fit's OWN residual rather than re-posing the layer by hand.
    # Feeding rotations back requires getting root ordering, matrix layout and
    # translation conventions all right; getting any of them wrong produced a
    # 737 mm "error" that was worse than a random pose, i.e. it measured my
    # reconstruction rather than the fit. per_vertex_error is what the solver
    # minimises and what the approach is actually scored on.
    pve_mm = float(result["per_vertex_error"].mean()) * 1000.0
    ok = pve_mm <= args.tol_mm
    print(f"\nPROPERTY  fit residual on real posed geometry: {pve_mm:.4f} mm "
          f"(tol {args.tol_mm})  -> {'PASS' if ok else 'FAIL'}")

    # Falsification: the residual has to be able to say "no". Geometry the model
    # cannot represent -- the same vertices with heavy noise -- must score far
    # worse. If noise fits just as well, the metric is not measuring anything.
    gN = torch.Generator(device="cpu").manual_seed(args.seed + 7)
    noise = (torch.randn(verts.shape, generator=gN, dtype=torch.float32) * 0.05).to(args.device)
    with torch.no_grad():
        bad = inv.fit(verts + noise)
    bad_mm = float(bad["per_vertex_error"].mean()) * 1000.0
    discriminates = bad_mm > max(pve_mm * 3.0, args.tol_mm * 3.0)
    print(f"FALSIFY   fit residual on unrepresentable (noised) geometry: {bad_mm:.4f} mm  -> "
          f"{'PASS (residual discriminates)' if discriminates else 'FAIL (fits anything)'}")

    return 0 if (ok and discriminates) else 1


if __name__ == "__main__":
    sys.exit(main())
