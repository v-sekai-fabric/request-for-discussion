# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Fit springbone_mujoco's parameter mapping to a measured step response.

Reads the editor recording's extracted features, rebuilds the same rig in
MuJoCo, and solves for the (stiffness, damping) reproducing each chain. See
RFD 2247 and logbook-springbone-mujoco-two-wrong-metrics for why the original
constants were misassigned rather than merely unfitted.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import mujoco
import numpy as np

NBONES = 8
SEG = 0.05
STEP_M = 0.15
SETTLE_T = 1.0
DURATION = 6.0
DT = 0.005


def build_rig(stiffness: float, damping: float):
    bodies = "".join(
        f'<body pos="0 {-SEG} 0">'
        f'<joint type="ball" damping="{damping:.6f}" stiffness="{stiffness:.6f}"'
        f' armature="0.0005"/>'
        f'<geom type="capsule" fromto="0 0 0 0 {-SEG} 0" size="0.01"'
        f' density="200" contype="0" conaffinity="0"/>'
        for _ in range(NBONES))
    chain = bodies + "</body>" * NBONES

    # A servo, not a written qpos: imposed kinematics exert no force on children.
    return mujoco.MjModel.from_xml_string(f"""<mujoco model="calib">
  <option timestep="{DT}" gravity="0 0 0" integrator="implicitfast"/>
  <compiler angle="radian"/>
  <worldbody>
    <body name="driver" pos="0 2 0">
      <joint name="dx" type="slide" axis="1 0 0"/>
      <geom type="sphere" size="0.03" density="5000" contype="0" conaffinity="0"/>
      {chain}
    </body>
  </worldbody>
  <actuator><position joint="dx" kp="80000" kv="900"/></actuator>
</mujoco>""")


def step_response(model, gain=1.0):
    data = mujoco.MjData(model)
    ts, angs = [], []
    down = np.array([0.0, -1.0, 0.0])
    while data.time < DURATION:
        data.ctrl[0] = (STEP_M * gain) if data.time >= SETTLE_T else 0.0
        mujoco.mj_step(model, data)
        v = data.xpos[model.nbody - 1] - data.xpos[1]
        n = float(np.linalg.norm(v))
        angs.append(0.0 if n < 1e-12
                    else math.acos(float(np.clip(np.dot(v / n, down), -1, 1))))
        ts.append(data.time)
    return np.asarray(ts), np.asarray(angs)


def features(t, a, settle_t=SETTLE_T):
    """Peak angle and 5%-settling time, matching what the recording reports."""
    m = t >= settle_t
    ap, tp = a[m], t[m]
    if ap.size == 0:
        return 0.0, 0.0
    peak = float(ap.max())
    if peak <= 1e-9:
        return 0.0, 0.0
    above = np.where(ap > 0.05 * peak)[0]
    return peak, (float(tp[above[-1]] - settle_t) if above.size else 0.0)


def response_table(stiff_grid=None, damp_grid=None, gain=1.0):
    """Every chain shares one geometry, so one table serves all of them."""
    stiff_grid = np.geomspace(1e-4, 5.0, 24) if stiff_grid is None else stiff_grid
    damp_grid = np.geomspace(1e-4, 2.0, 24) if damp_grid is None else damp_grid
    rows = []
    for s in stiff_grid:
        for d in damp_grid:
            peak, settle = features(*step_response(build_rig(float(s), float(d)), gain))
            if peak > 1e-9:
                rows.append((float(s), float(d), peak, settle))
    return rows


def fit_from_table(rows, target_peak, target_settle):
    best = None
    for s, d, peak, settle in rows:
        err = (abs(peak - target_peak) / max(target_peak, 1e-6)
               + abs(settle - target_settle) / max(target_settle, 1e-3))
        if best is None or err < best[0]:
            best = (err, s, d, peak, settle)
    return best


def immobile_gain(meas):
    """immobile scales response size at fixed settling time, so it is a gain."""
    base = meas.get("immobile=0", {}).get("peak_rad")
    out = {}
    if not base:
        return out
    for label, f in meas.items():
        if label.startswith("immobile="):
            out[label] = f["peak_rad"] / base
    return out


def main(calib_json: str, out_json: str):
    meas = json.load(open(calib_json, encoding="utf-8"))
    rows = response_table()
    print(f"response table: {len(rows)} usable points")

    gains = immobile_gain(meas)
    results = {}
    for label, f in meas.items():
        best = fit_from_table(rows, f["peak_rad"], f["t_settle"])
        if best is None:
            continue
        err, s, d, peak, settle = best
        results[label] = dict(
            stiffness=s, damping=d, gain=gains.get(label, 1.0),
            sim_peak_deg=math.degrees(peak), sim_settle=settle,
            tgt_peak_deg=math.degrees(f["peak_rad"]), tgt_settle=f["t_settle"],
            err=err)
        print(f"{label:<16} k={s:8.4f} c={d:8.4f}  "
              f"peak {math.degrees(peak):6.2f}/{math.degrees(f['peak_rad']):<6.2f}  "
              f"settle {settle:5.2f}/{f['t_settle']:<5.2f}  err={err:.3f}")

    Path(out_json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nwrote {out_json}")
    return results


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])
