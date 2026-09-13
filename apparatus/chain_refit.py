# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0

from __future__ import annotations

import numpy as np

import mujoco

from springbone_mujoco import (Chain, build_model, chain_curve_error,
                               decimate_chain, simulate)
from tier3_decimate import bend_error_deg

PULL_RANGE = (0.0, 1.0)
SPRING_RANGE = (0.0, 1.0)
STIFF_RANGE = (0.0, 1.0)

def _clamp(v, lo_hi):
    return float(min(max(v, lo_hi[0]), lo_hi[1]))

def with_params(chain: Chain, pull, spring, stiffness) -> Chain:
    return Chain(name=chain.name, bones=list(chain.bones),
                 colliders=list(chain.colliders),
                 pull=_clamp(pull, PULL_RANGE),
                 spring=_clamp(spring, SPRING_RANGE),
                 stiffness=_clamp(stiffness, STIFF_RANGE),
                 gravity=chain.gravity, immobile=chain.immobile,
                 radius=chain.radius, thickness=chain.thickness)

def trajectory(chain: Chain, motion, duration=4.0, dt=0.005, sample_hz=60):
    model = build_model([chain], dt=dt)
    traj = simulate(model, duration=duration, sample_hz=sample_hz, motion=motion)
    return model, traj

def _gather(model, traj, name):
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
             for i in range(model.nbody)]
    anchor = [i - 1 for i in range(1, model.nbody)
              if (names[i] or "") == "anchor_" + name]
    idx = [i - 1 for i in range(1, model.nbody)
           if (names[i] or "").startswith(name + "_")]
    return traj[:, anchor + idx, :]

def errors(ref, cand, motion, duration=4.0, samples=16):
    m_ref, t_ref = trajectory(ref, motion, duration=duration)
    m_cand, t_cand = trajectory(cand, motion, duration=duration)
    static = chain_curve_error(m_ref, t_ref, ref.name, len(ref.bones),
                               m_cand, t_cand, cand.name, len(cand.bones),
                               samples=samples)
    a, b = _gather(m_ref, t_ref, ref.name), _gather(m_cand, t_cand, cand.name)
    out = dict(static or {})
    mean_deg, p95_deg = bend_error_deg(a, b)
    out["bend_deg"], out["bend_p95_deg"] = float(mean_deg), float(p95_deg)
    out["ref_bend_deg"] = float(np.degrees(_bend_amp(a)))
    return out

def _bend_amp(traj):
    from tier3_decimate import bend_signature
    sig = bend_signature(traj)
    return float(np.ptp(sig, axis=0).mean()) if sig.size else 0.0

def refit(chain: Chain, keep_every, motion, duration=4.0, iters=40, seed=1171,
          metric="bend_deg"):
    rng = np.random.default_rng(seed)
    heuristic = decimate_chain(chain, keep_every)
    if len(heuristic.bones) == len(chain.bones):
        return dict(skipped="chain too short to decimate", chain=chain.name)

    base = errors(chain, heuristic, motion, duration=duration)
    best = dict(pull=heuristic.pull, spring=heuristic.spring,
                stiffness=heuristic.stiffness, error=base[metric], errors=base)

    span = np.array([0.5, 0.5, 0.5])
    for i in range(iters):
        span = span * 0.93
        cand = with_params(
            heuristic,
            best["pull"] + rng.normal(0, span[0]),
            best["spring"] + rng.normal(0, span[1]),
            best["stiffness"] + rng.normal(0, span[2]))
        e = errors(chain, cand, motion, duration=duration)
        if e is not None and e[metric] < best["error"]:
            best = dict(pull=cand.pull, spring=cand.spring,
                        stiffness=cand.stiffness, error=e[metric], errors=e)

    return dict(chain=chain.name, bones=len(chain.bones),
                reduced_bones=len(heuristic.bones),
                heuristic_bend_deg=base["bend_deg"],
                fitted_bend_deg=best["errors"]["bend_deg"],
                heuristic_bend_p95_deg=base["bend_p95_deg"],
                fitted_bend_p95_deg=best["errors"]["bend_p95_deg"],
                ref_bend_deg=base["ref_bend_deg"],
                static_mm=base["mean_mm"],
                pull=best["pull"], spring=best["spring"], stiffness=best["stiffness"],
                improvement=base[metric] - best["error"])

def format_row(r):
    if "skipped" in r:
        return f"  {r['chain']:<22} skipped: {r['skipped']}"
    return (f"  {r['chain']:<16} {r['bones']}->{r['reduced_bones']}  "
            f"bend err {r['heuristic_bend_deg']:6.3f} -> {r['fitted_bend_deg']:6.3f} deg  "
            f"(chain bends {r['ref_bend_deg']:6.3f} deg; static {r['static_mm']:6.1f} mm)")
