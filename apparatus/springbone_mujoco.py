# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0
"""Spring-bone chains in MuJoCo, so a chain budget is met by measured silhouette error
rather than a guessed knob (RFD 2234). Tiers: exact merge, collider prune, scored merge."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import mujoco
import numpy as np

# --- spring-bone -> MuJoCo parameter mapping (MEASURED) -----------------------
# Measured, not assumed: logbook-springbone-parameter-mapping-measured.md.
_PULL_K = [(0.1, 1.9947), (0.2, 4.1694), (0.4, 10.4785), (0.8, 55.0439)]
_DAMPING = 1.6278
_IMMOBILE_GAIN = [(0.0, 1.000), (0.3, 0.828), (0.6, 0.571), (0.9, 0.169)]
_SPRING_K_SCALE = [(0.0, 1.0), (0.3, 1.0), (0.6, 1.445)]


def _interp_loglog(table, x):
    xs = [p[0] for p in table]
    ys = [p[1] for p in table]
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lx = math.log(max(x, 1e-9))
    return float(math.exp(np.interp(lx, [math.log(v) for v in xs],
                                    [math.log(v) for v in ys])))


def _interp_linear(table, x):
    xs = [p[0] for p in table]
    ys = [p[1] for p in table]
    return float(np.interp(x, xs, ys))


_CAL_LINK_M = 0.0299
_CAL_SEG = 0.05
_CAL_INERTIA = sum(_CAL_LINK_M * (_CAL_SEG * i) ** 2 for i in range(1, 9))  # 0.01525


def chain_inertia(bones, radius: float, density: float = 200.0) -> float:
    """Rough inertia of a chain about its anchor: sum of m_i * r_i^2."""
    if len(bones) < 2:
        return _CAL_INERTIA
    anchor = bones[0][1]
    r = max(float(radius), 0.004)
    total = 0.0
    for i in range(1, len(bones)):
        seg = float(np.linalg.norm(bones[i][1] - bones[i - 1][1]))
        m = density * math.pi * r * r * max(seg, 1e-4)
        d = float(np.linalg.norm(bones[i][1] - anchor))
        total += m * d * d
    return max(total, 1e-9)


def mujoco_params(pull: float, spring: float, immobile: float,
                  inertia: float | None = None):
    """Measured spring-bone knobs -> (joint stiffness, joint damping, forcing gain)."""
    k = _interp_loglog(_PULL_K, max(pull, 1e-6))
    k *= _interp_linear(_SPRING_K_SCALE, spring)
    c = _DAMPING
    if inertia is not None and inertia > 0.0:
        scale = inertia / _CAL_INERTIA
        k *= scale
        c *= scale
    gain = _interp_linear(_IMMOBILE_GAIN, immobile)
    return k, c, gain


@dataclass
class Chain:
    """One spring-bone component: an ordered bone list plus its parameters."""
    name: str
    bones: list           # [(bone_name, np.array xyz in avatar-root space)]
    colliders: list       # collider names this chain is checked against
    pull: float = 0.2
    spring: float = 0.05
    stiffness: float = 0.1
    gravity: float = 0.0
    immobile: float = 0.0
    radius: float = 0.02          # collision radius, as the platform means it
    # Half-thickness sets mass and inertia, not the collision radius.
    thickness: float = 0.02

    def param_key(self):
        """Chains sharing this key are dynamically interchangeable (tier 1)."""
        return (round(self.pull, 4), round(self.spring, 4), round(self.stiffness, 4),
                round(self.gravity, 4), round(self.immobile, 4), round(self.radius, 4),
                tuple(sorted(self.colliders)))

    @property
    def transform_count(self):
        return len(self.bones)

    @property
    def collision_checks(self):
        return max(0, len(self.bones) - 1) * len(self.colliders)


def _root_to_leaf_paths(raw_bones):
    by_name = {b["n"]: b for b in raw_bones}
    children = {}
    for b in raw_bones:
        children.setdefault(b.get("par", ""), []).append(b["n"])
    names = set(by_name)
    roots = [b["n"] for b in raw_bones if b.get("par", "") not in names]

    paths = []

    def walk(name, acc):
        acc = acc + [name]
        kids = children.get(name, [])
        if not kids:
            paths.append(acc)
            return
        for k in kids:
            walk(k, acc)

    for r in roots:
        walk(r, [])
    return paths


def load_chains(path, split_branches: bool = True):
    """Read the JSON emitted by the editor-side PbExport into Chain objects."""
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for pb in d["springbones"]:
        raw = pb.get("bones", [])
        pos = {b["n"]: np.array(b["p"], dtype=float) for b in raw}

        if split_branches and raw:
            paths = _root_to_leaf_paths(raw)
            for pi, pth in enumerate(paths):
                if len(pth) < 2:
                    continue
                out.append(Chain(
                    name=f"{pb['go'].split('/')[-1]}#{pi}",
                    bones=[(n, pos[n]) for n in pth],
                    colliders=list(pb.get("colliders", [])),
                    pull=float(pb.get("pull", 0.2)),
                    spring=float(pb.get("spring", 0.05)),
                    stiffness=float(pb.get("stiffness", 0.1)),
                    gravity=float(pb.get("gravity", 0.0)),
                    immobile=float(pb.get("immobile", 0.0)),
                    radius=float(pb.get("radius", 0.02)),
                ))
            continue

        bones = [(b["n"], np.array(b["p"], dtype=float)) for b in raw]
        if len(bones) < 2:
            continue  # a single-transform chain has no articulation to simulate
        out.append(Chain(
            name=pb["go"].split("/")[-1],
            bones=bones,
            colliders=list(pb.get("colliders", [])),
            pull=float(pb.get("pull", 0.2)),
            spring=float(pb.get("spring", 0.05)),
            stiffness=float(pb.get("stiffness", 0.1)),
            gravity=float(pb.get("gravity", 0.0)),
            immobile=float(pb.get("immobile", 0.0)),
            radius=float(pb.get("radius", 0.02)),
        ))
    colliders = {c["n"].split("/")[-1]: c for c in d.get("colliders", [])}
    return out, colliders


def chain_mjcf(chain: Chain, root_body="root"):
    stiff, damp, _gain = mujoco_params(
        chain.pull, chain.spring, chain.immobile,
        inertia=chain_inertia(chain.bones, chain.thickness))

    xml, close = [], 0
    prev = chain.bones[0][1]
    for i in range(1, len(chain.bones)):
        name, pos = chain.bones[i]
        off = pos - prev
        L = float(np.linalg.norm(off))
        if L < 1e-6:
            off, L = np.array([0.0, -0.01, 0.0]), 0.01
        safe = f"{chain.name}_{i}".replace("/", "_").replace(".", "_").replace(" ", "_")
        # gravcomp 1.0 cancels gravity, so the spring-bone fraction is its complement.
        xml.append(
            f'<body name="{safe}" pos="{off[0]:.6f} {off[1]:.6f} {off[2]:.6f}" '
            f'gravcomp="{max(0.0, min(1.0, 1.0 - chain.gravity)):.4f}">'
            f'<joint name="j_{safe}" type="ball" damping="{damp:.4f}" '
            f'stiffness="{stiff:.4f}" armature="0.001"/>'
            f'<geom name="g_{safe}" type="capsule" fromto="0 0 0 '
            f'{off[0]:.6f} {off[1]:.6f} {off[2]:.6f}" size="{max(chain.thickness,0.004):.4f}" '
            f'density="200" contype="0" conaffinity="0"/>'
        )
        close += 1
        prev = pos
    return "".join(xml) + "</body>" * close


def build_model(chains, dt=0.005):
    """One free-floating carrier body that the motion suite drives, with every
    chain hung off it -- so chains share a frame and an integrator."""
    bodies = []
    for ch in chains:
        p = ch.bones[0][1]
        bodies.append(
            f'<body name="anchor_{ch.name}" pos="{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}">'
            + chain_mjcf(ch) + "</body>")
    xml = f"""<mujoco model="springbone">
  <option timestep="{dt}" gravity="0 -9.81 0" integrator="implicitfast"/>
  <compiler angle="radian"/>
  <worldbody>
    <body name="carrier" pos="0 0 0">
      <joint name="carrier_x" type="slide" axis="1 0 0"/>
      <joint name="carrier_y" type="slide" axis="0 1 0"/>
      <joint name="carrier_z" type="slide" axis="0 0 1"/>
      <joint name="carrier_yaw" type="hinge" axis="0 1 0"/>
      <geom type="sphere" size="0.02" density="1" contype="0" conaffinity="0"/>
      {''.join(bodies)}
    </body>
  </worldbody>
  <actuator>
    <position joint="carrier_x" kp="200000" kv="2000"/>
    <position joint="carrier_y" kp="200000" kv="2000"/>
    <position joint="carrier_z" kp="200000" kv="2000"/>
    <position joint="carrier_yaw" kp="200000" kv="2000"/>
  </actuator>
</mujoco>"""
    return mujoco.MjModel.from_xml_string(xml)


# --- motion suite -----------------------------------------------------------
# Harsh on purpose: walk bob, a yaw turn, and a hard stop, not a T-pose.

def motion_suite(t):
    walk_y = 0.02 * math.sin(2 * math.pi * 1.9 * t)
    walk_x = 0.35 * math.sin(2 * math.pi * 0.55 * t)
    yaw = 0.9 * math.sin(2 * math.pi * 0.35 * t)
    if t > 3.0:                      # hard stop: everything keeps swinging
        walk_x = 0.35 * math.sin(2 * math.pi * 0.55 * 3.0)
        yaw = 0.9 * math.sin(2 * math.pi * 0.35 * 3.0)
    return walk_x, walk_y, 0.0, yaw


def simulate(model, duration=5.0, sample_hz=60, motion=None):
    """Run a motion; return (T, N, 3) world positions of every chain body."""
    motion = motion or motion_suite
    data = mujoco.MjData(model)
    n = model.nbody
    dt = model.opt.timestep
    stride = max(1, int(round(1.0 / (sample_hz * dt))))

    start = np.array(motion(0.0), dtype=float)
    data.qpos[0:3] = start[0:3]
    data.qpos[3] = start[3]
    data.ctrl[0:4] = start[[0, 1, 2, 3]]
    mujoco.mj_forward(model, data)

    frames, step = [], 0
    while data.time < duration:
        cur = np.array(motion(data.time + dt), dtype=float)
        data.ctrl[0:4] = cur[[0, 1, 2, 3]]
        mujoco.mj_step(model, data)
        if step % stride == 0:
            frames.append(np.array(data.xpos[1:n]))  # skip world body
        step += 1
    return np.asarray(frames)


def silhouette_error(ref, cand):
    n = min(ref.shape[0], cand.shape[0])
    m = min(ref.shape[1], cand.shape[1])
    d = np.linalg.norm(ref[:n, :m] - cand[:n, :m], axis=2)
    per_frame = np.sqrt((d ** 2).mean(axis=1))
    return {
        "mean_mm": float(per_frame.mean() * 1000.0),
        "p95_mm": float(np.percentile(per_frame, 95) * 1000.0),
        "max_mm": float(per_frame.max() * 1000.0),
    }


# --- tier 1: exact merge ----------------------------------------------------

def tier1_exact_merges(chains):
    groups = {}
    for ch in chains:
        groups.setdefault(ch.param_key(), []).append(ch)
    return [g for g in groups.values() if len(g) > 1]


# --- tier 3: scored chain decimation ---------------------------------------

def decimate_chain(chain: Chain, keep_every: int) -> Chain:
    """Drop intermediate bones, always keeping the root and the tip."""
    if keep_every <= 1 or len(chain.bones) <= 3:
        return chain
    idx = list(range(0, len(chain.bones), keep_every))
    if idx[-1] != len(chain.bones) - 1:
        idx.append(len(chain.bones) - 1)
    out = Chain(
        name=chain.name + f"_d{keep_every}",
        bones=[chain.bones[i] for i in idx],
        colliders=list(chain.colliders),
        pull=chain.pull, spring=chain.spring,
        stiffness=chain.stiffness / float(keep_every),
        gravity=chain.gravity, immobile=chain.immobile, radius=chain.radius,
        thickness=chain.thickness,
    )
    return out


def resample_curve(pts, n=16):
    """Resample a polyline to n points by arclength, so chains of different
    bone counts become comparable curves."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 2:
        return np.repeat(pts, n, axis=0)[:n]
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    if s[-1] <= 1e-9:
        return np.repeat(pts[:1], n, axis=0)
    t = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], axis=1)


def chain_curve_error(model_ref, traj_ref, ref_name, n_ref,
                      model_cand, traj_cand, cand_name, n_cand, samples=16):
    """Arclength-resampled deviation between one chain's reference and
    decimated trajectories, in millimetres."""
    def gather(model, traj, prefix, count):
        names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
                 for i in range(model.nbody)]
        anchor = [i - 1 for i in range(1, model.nbody)
                  if (names[i] or "") == "anchor_" + prefix]
        idx = [i - 1 for i in range(1, model.nbody)
               if (names[i] or "").startswith(prefix + "_")]
        return traj[:, anchor + idx, :]

    a = gather(model_ref, traj_ref, ref_name, n_ref)
    b = gather(model_cand, traj_cand, cand_name, n_cand)
    if a.shape[1] == 0 or b.shape[1] == 0:
        return None
    T = min(a.shape[0], b.shape[0])
    errs = []
    for f in range(T):
        ca = resample_curve(a[f], samples)
        cb = resample_curve(b[f], samples)
        errs.append(np.linalg.norm(ca - cb, axis=1).mean())
    errs = np.asarray(errs)
    return {"mean_mm": float(errs.mean() * 1000),
            "p95_mm": float(np.percentile(errs, 95) * 1000),
            "max_mm": float(errs.max() * 1000)}


# --- tier 2: collider pruning ----------------------------------------------

def tier2_collider_prune(chains, colliders, model, traj, margin=0.05):
    """Find (chain, collider) pairs whose closest approach never gets near."""
    name_of_body = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
                    for i in range(model.nbody)]
    prunable, kept = [], 0
    for ch in chains:
        idx = [i - 1 for i in range(1, model.nbody)
               if (name_of_body[i] or "").startswith(f"{ch.name}_")]
        if not idx:
            continue
        pts = traj[:, idx, :]
        for cname in ch.colliders:
            c = colliders.get(cname.split("/")[-1])
            if c is None:
                continue
            cpos = np.array(c.get("p", [0, 0, 0]), dtype=float)
            crad = float(c.get("radius", 0.05))
            closest = float(np.linalg.norm(pts - cpos, axis=2).min())
            if closest > crad + ch.radius + margin:
                prunable.append((ch.name, cname.split("/")[-1],
                                 round(closest, 4), max(0, len(ch.bones) - 1)))
            else:
                kept += 1
    return prunable, kept
