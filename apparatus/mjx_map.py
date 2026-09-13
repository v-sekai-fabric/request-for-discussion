"""Derive the spring-bone knob -> MuJoCo (stiffness, damping) mapping on GPU.

Fits every recorded setup against a response table. `immobile` enters as the
forcing gain the recording measured -- peak scales, settling does not -- so its
rows are fitted against tables built at their own gain rather than being absorbed
into the dynamics.

Reads calib_features.json, writes mjx_map.json.
"""
import json
import math
import sys

import jax
import jax.numpy as jp
import numpy as np

from mjx_sweep import build, features, make_rollout

K_GRID = np.geomspace(0.05, 200.0, 46)
C_GRID = np.geomspace(0.01, 60.0, 42)
CHUNK = 700          # keeps each vmap under the 4090's comfortable allocation


def table_for_gain(rollout, ndof, gain):
    KK, CC = np.meshgrid(K_GRID, C_GRID, indexing="ij")
    ks, cs = KK.ravel(), CC.ravel()

    def one(s, d):
        return features(*rollout(s, jp.full(ndof, d)))

    batched = jax.jit(jax.vmap(one))
    peaks, settles = [], []
    for i in range(0, ks.size, CHUNK):
        p, s = batched(jp.asarray(ks[i:i + CHUNK]), jp.asarray(cs[i:i + CHUNK]))
        peaks.append(np.asarray(p))
        settles.append(np.asarray(s))
    peaks, settles = np.concatenate(peaks), np.concatenate(settles)
    ok = np.isfinite(peaks) & np.isfinite(settles) & (peaks > 1e-9)
    return ks, cs, peaks, settles, ok


def fit(ks, cs, peaks, settles, ok, tgt_peak, tgt_settle):
    err = np.full(peaks.shape, np.inf)
    err[ok] = (np.abs(peaks[ok] - tgt_peak) / tgt_peak
               + np.abs(settles[ok] - tgt_settle) / max(tgt_settle, 1e-3))
    i = int(np.argmin(err))
    return dict(stiffness=float(ks[i]), damping=float(cs[i]),
                ratio=float(cs[i] / ks[i]), err=float(err[i]),
                sim_peak_deg=float(math.degrees(peaks[i])), sim_settle=float(settles[i]))


def main(calib_path, out_path):
    meas = json.load(open(calib_path, encoding="utf-8"))
    m, mx = build()
    rollout = make_rollout(mx, m.nbody)
    ndof = mx.dof_damping.shape[0] - 1
    print("backend", jax.default_backend(), jax.devices())

    base_peak = meas["immobile=0"]["peak_rad"]
    gains = {}
    for label, f in meas.items():
        gains[label] = (f["peak_rad"] / base_peak) if label.startswith("immobile=") else 1.0

    tables = {}
    for g in sorted(set(gains.values())):
        print(f"building table at gain {g:.3f} ({K_GRID.size * C_GRID.size} configs)...")
        tables[g] = table_for_gain(rollout, ndof, g)

    out = {}
    print(f"\n{'setup':<16} {'gain':>6} {'k':>9} {'c':>9} {'c/k':>7}"
          f"  {'peak sim/meas':>16}  {'settle sim/meas':>16}  {'err':>6}")
    for label, f in meas.items():
        g = gains[label]
        r = fit(*tables[g], f["peak_rad"], f["t_settle"])
        r["gain"] = g
        r["tgt_peak_deg"] = math.degrees(f["peak_rad"])
        r["tgt_settle"] = f["t_settle"]
        out[label] = r
        print(f"{label:<16} {g:6.3f} {r['stiffness']:9.4f} {r['damping']:9.4f}"
              f" {r['ratio']:7.4f}  {r['sim_peak_deg']:6.2f}/{r['tgt_peak_deg']:<8.2f}"
              f"  {r['sim_settle']:6.2f}/{r['tgt_settle']:<8.2f}  {r['err']:6.3f}")

    good = sum(1 for r in out.values() if r["err"] < 0.15)
    print(f"\n{good}/{len(out)} setups within 15% combined error")

    print("\n=== knob -> c/k (settling) and k (amplitude) ===")
    for knob in ("pull", "spring", "stiffness", "immobile"):
        rows = [(lab, r) for lab, r in out.items() if lab.startswith(knob + "=")]
        if not rows:
            continue
        print(f"  {knob}:")
        for lab, r in sorted(rows, key=lambda x: float(x[0].split("=")[1])):
            print(f"    {lab:<16} c/k={r['ratio']:.4f}  k={r['stiffness']:8.4f}"
                  f"  gain={r['gain']:.3f}")

    json.dump(out, open(out_path, "w"), indent=2)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
