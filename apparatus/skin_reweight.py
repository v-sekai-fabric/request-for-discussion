# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Turn predicted skin weights into weights an engine will accept.

TokenRig returns a dense (V, J) weight matrix whose rows do not sum to 1 -- first
light measured 0.045 to 2.573, because the voxel post-process is not applied.
Feeding that to a renderer deforms the mesh wrongly: a row summing to 0.045
leaves a vertex almost unbound and it collapses toward the origin, while a row
summing above 1 over-drives it.

Reweighting is three steps, and the order matters:

  1. clamp negatives -- a negative influence has no meaning in linear blend
     skinning and will drag vertices backwards;
  2. keep the top K influences per vertex -- the social VR platforms and the
     engines that host them budget 4, and dropping the tail before normalising
     is what makes the kept weights carry the full deformation rather than a
     fraction of it;
  3. normalise each row to 1.

A row that is entirely zero after clamping cannot be normalised. Those vertices
are bound to their single nearest joint instead, which is wrong but bounded --
leaving them at zero detaches them from the skeleton completely.
"""

from __future__ import annotations

import numpy as np

MAX_INFLUENCES = 4


def reweight(weights: np.ndarray, joint_positions: np.ndarray | None = None,
             vertices: np.ndarray | None = None,
             max_influences: int = MAX_INFLUENCES):
    """(V, J) predicted weights -> (V, J) engine-ready weights.

    Returns (weights, report). The report carries the before/after row-sum range
    so a caller can tell a rescue apart from a silent fudge.
    """
    w = np.asarray(weights, dtype=np.float64).copy()
    if w.ndim != 2:
        raise ValueError(f"expected (V, J) weights, got {w.shape}")
    V, J = w.shape

    before = w.sum(axis=1)
    report = {
        "vertices": int(V), "joints": int(J),
        "row_sum_before": (float(before.min()), float(before.max())),
        "negatives": int((w < 0).sum()),
    }

    w[w < 0.0] = 0.0

    k = min(max_influences, J)
    if k < J:
        # Zero everything outside the top-k per row.
        cut = np.argpartition(w, J - k, axis=1)[:, :J - k]
        np.put_along_axis(w, cut, 0.0, axis=1)

    sums = w.sum(axis=1)
    dead = sums <= 1e-12
    report["dead_rows"] = int(dead.sum())

    if dead.any():
        if joint_positions is not None and vertices is not None:
            jp = np.asarray(joint_positions, dtype=np.float64)
            vs = np.asarray(vertices, dtype=np.float64)[dead]
            nearest = np.argmin(
                ((vs[:, None, :] - jp[None, :, :]) ** 2).sum(axis=2), axis=1)
            w[np.where(dead)[0], nearest] = 1.0
            report["dead_row_policy"] = "bound to nearest joint"
        else:
            # No geometry to fall back on: bind to the most-used joint overall so
            # the vertex still follows the body rather than detaching.
            fallback = int(np.argmax(w.sum(axis=0))) if w.sum() > 0 else 0
            w[dead, fallback] = 1.0
            report["dead_row_policy"] = f"bound to dominant joint {fallback}"
        sums = w.sum(axis=1)

    w /= sums[:, None]

    after = w.sum(axis=1)
    report["row_sum_after"] = (float(after.min()), float(after.max()))
    report["influences_mean"] = float((w > 1e-6).sum(axis=1).mean())
    report["influences_max"] = int((w > 1e-6).sum(axis=1).max())
    return w, report


def format_report(r: dict) -> str:
    lo, hi = r["row_sum_before"]
    alo, ahi = r["row_sum_after"]
    return (f"  vertices={r['vertices']} joints={r['joints']}\n"
            f"  row sums before: {lo:.4f} .. {hi:.4f}\n"
            f"  row sums after:  {alo:.6f} .. {ahi:.6f}\n"
            f"  negatives clamped: {r['negatives']}\n"
            f"  dead rows: {r['dead_rows']}"
            + (f" ({r['dead_row_policy']})" if r["dead_rows"] else "") + "\n"
            f"  influences/vertex: mean {r['influences_mean']:.2f}, "
            f"max {r['influences_max']}")
