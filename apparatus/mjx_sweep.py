"""Batched spring-bone step-response sweep on GPU via MJX.

The serial search covered a few hundred configurations and kept hitting a peak
cap near 26 deg whenever settling was ~1.2 s. That is either a real property of
ball-joint dynamics or an under-searched space. vmap over the whole grid at once
settles it: thousands of configurations, one rollout.

Target comes from the editor recording: peak 58.72 deg, 5%-settling 1.18 s.
"""
import json
import math
import sys

import jax
import jax.numpy as jp
import mujoco
import numpy as np
from mujoco import mjx

NB, SEG, DT = 8, 0.05, 0.004
STEP_M, SETTLE_T, DURATION = 0.15, 1.0, 6.0
NSTEP = int(DURATION / DT)
TARGET_PEAK, TARGET_SETTLE = math.radians(58.72), 1.18
DOWN = jp.array([0.0, -1.0, 0.0])


def base_xml(density=1000.0, kp=200000.0, kv=400.0):
    bodies = "".join(
        f'<body pos="0 {-SEG} 0">'
        f'<joint type="ball" damping="0.03" stiffness="0.05" armature="1e-7"/>'
        f'<geom type="capsule" fromto="0 0 0 0 {-SEG} 0" size="0.012"'
        f' density="{density}" contype="0" conaffinity="0"/>'
        for _ in range(NB))
    return f"""<mujoco>
  <option timestep="{DT}" gravity="0 0 0" integrator="implicitfast"
          iterations="4" ls_iterations="8"/>
  <compiler angle="radian"/>
  <worldbody><body name="driver" pos="0 2 0">
    <joint name="dx" type="slide" axis="1 0 0"/>
    <geom type="sphere" size="0.03" density="2000" contype="0" conaffinity="0"/>
    {bodies + "</body>" * NB}
  </body></worldbody>
  <actuator><position joint="dx" kp="{kp}" kv="{kv}"/></actuator>
</mujoco>"""


def build():
    m = mujoco.MjModel.from_xml_string(base_xml())
    return m, mjx.put_model(m)


def make_rollout(mx, nbody):
    def rollout(stiff, damp):
        model = mx.tree_replace({
            "jnt_stiffness": mx.jnt_stiffness.at[1:].set(stiff),
            "dof_damping": mx.dof_damping.at[1:].set(damp),
        })
        d = mjx.make_data(model)

        def step(d, _):
            ctrl = jp.where(d.time >= SETTLE_T, STEP_M, 0.0)
            d = d.replace(ctrl=d.ctrl.at[0].set(ctrl))
            d = mjx.step(model, d)
            v = d.xpos[nbody - 1] - d.xpos[1]
            n = jp.linalg.norm(v)
            ang = jp.arccos(jp.clip(jp.dot(v / jp.maximum(n, 1e-12), DOWN), -1.0, 1.0))
            return d, (d.time, ang)

        _, (ts, angs) = jax.lax.scan(step, d, None, length=NSTEP)
        return ts, angs
    return rollout


def features(ts, angs):
    """Peak and 5%-settling after the step, branch-free for vmap."""
    post = ts >= SETTLE_T
    ap = jp.where(post, angs, 0.0)
    peak = jp.max(ap)
    thresh = 0.05 * peak
    above = jp.where(post & (angs > thresh), ts, 0.0)
    settle = jp.max(above) - SETTLE_T
    return peak, jp.maximum(settle, 0.0)


def main():
    m, mx = build()
    print("nbody", m.nbody, "njnt", m.njnt, "nv", m.nv)
    print("backend", jax.default_backend(), jax.devices())

    ns, nd = 48, 40
    S = jp.asarray(np.geomspace(1e-4, 20.0, ns))
    D = jp.asarray(np.geomspace(1e-4, 5.0, nd))
    SS, DD = jp.meshgrid(S, D, indexing="ij")
    flat_s, flat_d = SS.ravel(), DD.ravel()
    print(f"sweeping {flat_s.size} configs on {jax.default_backend()}")

    rollout = make_rollout(mx, m.nbody)

    def one(s, d):
        ts, angs = rollout(s, jp.full(mx.dof_damping.shape[0] - 1, d))
        return features(ts, angs)

    batched = jax.jit(jax.vmap(one))
    peaks, settles = batched(flat_s, flat_d)
    peaks, settles = np.asarray(peaks), np.asarray(settles)

    err = (np.abs(peaks - TARGET_PEAK) / TARGET_PEAK
           + np.abs(settles - TARGET_SETTLE) / TARGET_SETTLE)
    err = np.where(peaks > 1e-9, err, np.inf)
    order = np.argsort(err)

    print(f"\nreachable: peak {math.degrees(peaks.min()):.2f}"
          f"..{math.degrees(peaks.max()):.2f} deg, "
          f"settle {settles.min():.2f}..{settles.max():.2f} s")
    print(f"\ntarget peak {math.degrees(TARGET_PEAK):.2f} deg  settle {TARGET_SETTLE:.2f} s")
    print(f"{'err':>7} {'stiff':>10} {'damp':>10}  {'peak deg':>9} {'settle s':>9}")
    for i in order[:12]:
        print(f"{err[i]:7.3f} {float(flat_s[i]):10.5f} {float(flat_d[i]):10.5f}"
              f"  {math.degrees(peaks[i]):9.2f} {settles[i]:9.2f}")

    out = dict(best_err=float(err[order[0]]),
               stiffness=float(flat_s[order[0]]), damping=float(flat_d[order[0]]),
               peak_deg=float(math.degrees(peaks[order[0]])),
               settle=float(settles[order[0]]),
               reach_peak_deg=[float(math.degrees(peaks.min())),
                               float(math.degrees(peaks.max()))],
               reach_settle=[float(settles.min()), float(settles.max())],
               n=int(flat_s.size))
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "mjx_sweep.json", "w"),
              indent=2)


if __name__ == "__main__":
    main()
