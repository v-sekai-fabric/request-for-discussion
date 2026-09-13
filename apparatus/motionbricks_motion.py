# Copyright 2026 V-Sekai contributors.
# SPDX-License-Identifier: Apache-2.0 OR MPL-2.0

from __future__ import annotations

import ctypes
import math
import os
from ctypes import (POINTER, c_char, c_char_p, c_float, c_int32, c_uint32,
                    c_uint64, c_void_p)

import numpy as np

ROOT = os.environ.get("MOTIONBRICKS_ROOT",
                      r"C:\weftspun\3-interactor\motion-bricks-cpp")
DLL = os.path.join(ROOT, "build", "release", "motionbricks.dll")
# The ggml backends sit in bin/ next to the CLI, not beside the library, and
DEPS = os.path.join(ROOT, "build", "release", "bin")
BUNDLE = os.path.join(ROOT, "generated", "g1-f32")
STYLES = os.path.join(ROOT, "generated", "styles")

MB_OK = 0
MB_DEVICE_AUTO, MB_DEVICE_CPU, MB_DEVICE_VULKAN = 0, 1, 2
FPS = 30.0

class MotionBricksError(RuntimeError):
    pass

def _load():
    if os.path.isdir(DEPS) and hasattr(os, "add_dll_directory"):
        os.add_dll_directory(DEPS)
    lib = ctypes.CDLL(DLL)
    err = [POINTER(c_char), c_uint64]

    def sig(name, args, res=c_uint32):
        fn = getattr(lib, name)
        fn.argtypes = args
        fn.restype = res
        return fn

    lib.mb_abi_version.restype = c_uint32
    lib.mb_status_string.argtypes = [c_uint32]
    lib.mb_status_string.restype = c_char_p
    sig("mb_runtime_options_create", [POINTER(c_void_p)] + err)
    sig("mb_runtime_options_set_device", [c_void_p, c_uint32] + err)
    sig("mb_runtime_options_free", [c_void_p], None)
    sig("mb_model_load", [c_char_p, c_void_p, POINTER(c_void_p)] + err)
    sig("mb_model_free", [c_void_p], None)
    sig("mb_style_load", [c_void_p, c_char_p, POINTER(c_void_p)] + err)
    sig("mb_style_free", [c_void_p], None)
    sig("mb_agent_create", [c_void_p, POINTER(c_void_p)] + err)
    sig("mb_agent_reset", [c_void_p, c_void_p] + err)
    sig("mb_agent_plan", [c_void_p, c_void_p, POINTER(c_void_p)] + err)
    sig("mb_agent_advance", [c_void_p, c_uint32] + err)
    sig("mb_agent_free", [c_void_p], None)
    sig("mb_command_create", [POINTER(c_void_p)] + err)
    sig("mb_command_set_style", [c_void_p, c_void_p] + err)
    sig("mb_command_set_movement_direction", [c_void_p, c_float, c_float, c_float] + err)
    sig("mb_command_set_facing_direction", [c_void_p, c_float, c_float, c_float] + err)
    sig("mb_command_set_target_speed", [c_void_p, c_float] + err)
    sig("mb_command_set_seed", [c_void_p, c_uint64] + err)
    sig("mb_command_free", [c_void_p], None)
    sig("mb_motion_get_frame_count", [c_void_p, POINTER(c_uint64)] + err)
    sig("mb_motion_get_root_translations",
        [c_void_p, POINTER(POINTER(c_float)), POINTER(c_uint64)] + err)
    sig("mb_motion_get_local_rotations_xyzw",
        [c_void_p, POINTER(POINTER(c_float)), POINTER(c_uint64)] + err)
    sig("mb_motion_get_joint_count", [c_void_p, POINTER(c_uint64)] + err)
    sig("mb_motion_free", [c_void_p], None)
    return lib

_LIB = None

def lib():
    global _LIB
    if _LIB is None:
        _LIB = _load()
    return _LIB

class _Err:

    def __init__(self, n=512):
        self.buf = ctypes.create_string_buffer(n)
        self.n = c_uint64(n)

    def args(self):
        return (ctypes.cast(self.buf, POINTER(c_char)), self.n)

    def text(self):
        return self.buf.value.decode("utf-8", "replace")

def _check(status, err, what):
    if status != MB_OK:
        name = lib().mb_status_string(status)
        raise MotionBricksError(
            f"{what}: {name.decode() if name else status} -- {err.text()}")

def root_trajectory(style="walk", seconds=6.0, speed=1.2, device=MB_DEVICE_AUTO,
                    seed=1171, turn=True):
    e = _Err()
    L = lib()
    if L.mb_abi_version() != 1:
        raise MotionBricksError(f"unexpected ABI {L.mb_abi_version()}")

    opts = c_void_p()
    _check(L.mb_runtime_options_create(ctypes.byref(opts), *e.args()), e, "options")
    _check(L.mb_runtime_options_set_device(opts, device, *e.args()), e, "device")

    model = c_void_p()
    _check(L.mb_model_load(BUNDLE.encode(), opts, ctypes.byref(model), *e.args()),
           e, "model_load")

    st = c_void_p()
    path = os.path.join(STYLES, f"{style}.mbstyle")
    _check(L.mb_style_load(model, path.encode(), ctypes.byref(st), *e.args()),
           e, f"style_load({style})")

    agent = c_void_p()
    _check(L.mb_agent_create(model, ctypes.byref(agent), *e.args()), e, "agent")
    _check(L.mb_agent_reset(agent, st, *e.args()), e, "reset")

    cmd = c_void_p()
    _check(L.mb_command_create(ctypes.byref(cmd), *e.args()), e, "command")
    _check(L.mb_command_set_style(cmd, st, *e.args()), e, "set_style")
    _check(L.mb_command_set_target_speed(cmd, c_float(speed), *e.args()), e, "speed")
    _check(L.mb_command_set_seed(cmd, c_uint64(seed), *e.args()), e, "seed")

    out = []
    want = int(seconds * FPS)
    heading = 0.0
    while len(out) < want:
        if turn:
            heading += 0.6 * math.sin(len(out) / FPS * 0.5)
        dx, dz = math.sin(heading), math.cos(heading)
        _check(L.mb_command_set_movement_direction(cmd, c_float(dx), c_float(0.0),
                                                   c_float(dz), *e.args()),
               e, "move_dir")
        _check(L.mb_command_set_facing_direction(cmd, c_float(dx), c_float(0.0),
                                                 c_float(dz), *e.args()),
               e, "face_dir")

        motion = c_void_p()
        _check(L.mb_agent_plan(agent, cmd, ctypes.byref(motion), *e.args()), e, "plan")

        frames = c_uint64()
        _check(L.mb_motion_get_frame_count(motion, ctypes.byref(frames), *e.args()),
               e, "frame_count")
        joints = c_uint64()
        _check(L.mb_motion_get_joint_count(motion, ctypes.byref(joints), *e.args()),
               e, "joint_count")

        ptr, n = POINTER(c_float)(), c_uint64()
        _check(L.mb_motion_get_root_translations(motion, ctypes.byref(ptr),
                                                 ctypes.byref(n), *e.args()),
               e, "root_translations")
        trans = np.ctypeslib.as_array(ptr, shape=(int(n.value),)).reshape(-1, 3).copy()

        rptr, rn = POINTER(c_float)(), c_uint64()
        _check(L.mb_motion_get_local_rotations_xyzw(motion, ctypes.byref(rptr),
                                                    ctypes.byref(rn), *e.args()),
               e, "local_rotations")
        rots = np.ctypeslib.as_array(rptr, shape=(int(rn.value),)).reshape(
            int(frames.value), int(joints.value), 4).copy()

        x, y, z, w = rots[:, 0, 0], rots[:, 0, 1], rots[:, 0, 2], rots[:, 0, 3]
        yaw = np.arctan2(2.0 * (w * y + x * z), 1.0 - 2.0 * (y * y + z * z))

        take = min(len(trans), want - len(out))
        for i in range(take):
            out.append((float(trans[i, 0]), float(trans[i, 1]),
                        float(trans[i, 2]), float(yaw[i])))

        adv = int(min(take, frames.value))
        L.mb_motion_free(motion)
        if adv <= 0:
            raise MotionBricksError("planner returned no frames")
        _check(L.mb_agent_advance(agent, c_uint32(adv), *e.args()), e, "advance")

    L.mb_command_free(cmd)
    L.mb_agent_free(agent)
    L.mb_style_free(st)
    L.mb_model_free(model)
    L.mb_runtime_options_free(opts)
    return np.asarray(out, dtype=float)

def as_motion_fn(traj, fps=FPS):
    traj = np.asarray(traj, dtype=float)
    n = len(traj)

    def fn(t):
        u = float(t) * fps
        i = int(math.floor(u))
        if i < 0:
            return tuple(traj[0])
        if i >= n - 1:
            return tuple(traj[-1])
        a = u - i
        v = traj[i] * (1.0 - a) + traj[i + 1] * a
        return tuple(v)

    return fn
