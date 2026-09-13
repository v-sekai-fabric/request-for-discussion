"""Refine the spring-bone (stiffness, damping) fit around the coarse GPU optimum.

The coarse 1920-point sweep landed at k=4.21, c=1.65 with settling exact and
peak 7.4% high. This searches a tight box around it, and reports the reachable
set with NaN configurations excluded rather than poisoning the min/max.
"""
import json
import math
import sys

import jax
import jax.numpy as jp
import numpy as np

from mjx_sweep import TARGET_PEAK, TARGET_SETTLE, build, features, make_rollout


def main(out_path="mjx_refine.json", k0=4.21, c0=1.6483, span=2.2, n=56):
    m, mx = build()
    print("backend", jax.default_backend(), jax.devices())

    S = jp.asarray(np.geomspace(k0 / span, k0 * span, n))
    D = jp.asarray(np.geomspace(c0 / span, c0 * span, n))
    SS, DD = jp.meshgrid(S, D, indexing="ij")
    fs, fd = SS.ravel(), DD.ravel()
    print(f"refining {fs.size} configs around k={k0:.3f} c={c0:.4f}")

    rollout = make_rollout(mx, m.nbody)
    ndof = mx.dof_damping.shape[0] - 1

    def one(s, d):
        return features(*rollout(s, jp.full(ndof, d)))

    peaks, settles = jax.jit(jax.vmap(one))(fs, fd)
    peaks, settles = np.asarray(peaks), np.asarray(settles)

    ok = np.isfinite(peaks) & np.isfinite(settles) & (peaks > 1e-9)
    err = np.full(peaks.shape, np.inf)
    err[ok] = (np.abs(peaks[ok] - TARGET_PEAK) / TARGET_PEAK
               + np.abs(settles[ok] - TARGET_SETTLE) / TARGET_SETTLE)
    order = np.argsort(err)

    print(f"\nvalid {ok.sum()}/{ok.size}; reachable peak "
          f"{math.degrees(peaks[ok].min()):.2f}..{math.degrees(peaks[ok].max()):.2f} deg, "
          f"settle {settles[ok].min():.2f}..{settles[ok].max():.2f} s")
    print(f"\ntarget peak {math.degrees(TARGET_PEAK):.2f} deg  settle {TARGET_SETTLE:.2f} s")
    print(f"{'err':>7} {'stiff':>10} {'damp':>10}  {'peak deg':>9} {'settle s':>9}")
    for i in order[:10]:
        print(f"{err[i]:7.4f} {float(fs[i]):10.5f} {float(fd[i]):10.5f}"
              f"  {math.degrees(peaks[i]):9.2f} {settles[i]:9.2f}")

    b = order[0]
    json.dump(dict(stiffness=float(fs[b]), damping=float(fd[b]), err=float(err[b]),
                   peak_deg=float(math.degrees(peaks[b])), settle=float(settles[b]),
                   target_peak_deg=float(math.degrees(TARGET_PEAK)),
                   target_settle=TARGET_SETTLE, n=int(fs.size)),
              open(out_path, "w"), indent=2)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mjx_refine.json")
