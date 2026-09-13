# Copyright (c) 2026 K. S. Ernest (iFire) Lee
# SPDX-License-Identifier: MIT
#
# RFD 2250. `mix rfd.render` renders rfd/2250-cloth-fit-as-one-burrito-binary/README.md and
# DETAILS.md from this file; the Markdown is a build artifact (RFD 2232).
defmodule RFD2250 do
  use RFD.DSL

  rfd 2250, "cloth-fit ships as one Burrito binary" do
    state :discussion

    feature "cloth-fit ships as a single self-contained Elixir Burrito CLI\nthat drives the PolyFEM garment solver over OpenUSD, with no runtime\ntoolchain on the target"

    scope "`V-Sekai-fire/cloth-fit`, `fabric-stage-runtime` and its\n`stage_runtime` Hex package, and the four build triplets"

    decision ~S"""
    One binary per triplet, carrying its own native artifacts. The C++
    binding is Fine rather than Unifex, the OpenUSD SDK arrives as a
    prebuilt per-triplet Hex dependency rather than a local build, and the
    solver reaches USD through a dlopen'd C-ABI bridge so USD's TBB stays
    isolated from PolyFEM's static oneTBB. Assets normalise on load to one
    convention, +Y up and +Z front, right-handed and metric, and output
    carries the matching metadata so a consumer places it without guessing.

    `DETAILS.md` carries the five workstreams and what is still open.
    """

    problem ~S"""
    The solver needed a C++ toolchain, a local OpenUSD build and a Mix
    environment on any machine that ran it, which is three things to
    reproduce before one garment is retargeted once. A prebuilt per-triplet
    SDK and a self-extracting binary remove all three, and remove the reason
    two TBBs ever met in one process.
    """

    related ~S"""
    - [RFD 2234](../2234-dress-on-pipeline/): the dress-on pipeline this
      solver serves.
    - [RFD 2249](../2249-cloth-by-vertex-block-descent/): the descent
      formulation, where this RFD is the shipping vehicle.
    - [RFD 1053](../1053-openusd-as-the-internal-format/): why the round
      trip is USD rather than OBJ.
    - Moved from `V-Sekai-fire/cloth-fit` issue 2, now closed.
    """

    details_title "cloth-fit ships as one Burrito binary"

    details "Where this came from", ~S"""
    This RFD is `V-Sekai-fire/cloth-fit` issue 2, moved. The issue was a
    checklist tracker opened 2026-07-11 and last updated 2026-07-12. It is
    closed, and this document is where the work is now described.

    The status below is the issue's own, transcribed rather than re-verified.
    Nothing here was measured on 2026-09-12.
    """

    details "1. Fine replaces Unifex for the C++ binding", ~S"""
    Landed. `fine` plus `elixir_make`, with `unifex` and `bundlex` dropped
    from `cloth_fit_cli/mix.exs`. The five NIFs are stateless, so no
    resource pointer was needed, and the Unifex `.spec.exs` and generated
    scaffolding are deleted.

    The link recipe is a Makefile driven by `elixir_make`. Include dirs,
    defines and the static-lib list all come from response files generated
    by the build, so no path or library name is hardcoded.

    The solver NIF runs dirty (`ERL_NIF_DIRTY_JOB_CPU_BOUND`) so it does not
    block the scheduler. Progress reporting and cancellation are open.

    The portable build is one step: `mix cloth_fit.build_native` builds a
    static oneTBB and PolyFEM, generates the flag files, and builds the NIF.
    `elixir_make` is gated on the generated link response file, so a fresh
    checkout bootstraps in a single command. The C++ runtime is linked
    statically so the shared library bundles with no external runtime.
    """

    details "2. The OpenUSD SDK as a prebuilt per-triplet dependency", ~S"""
    Landed, in `fabric-stage-runtime`, modelled on `elixir-nx/xla` and built
    with `elixir_make` rather than SCons.

    Four triplets: `x86_64-linux-gnu`, `aarch64-apple-darwin`,
    `x86_64-windows-msvc`, and `x86_64-windows-gnu`. The last was added
    because cloth-fit's Windows toolchain is GNU-ABI and cannot link the
    MSVC-ABI build.

    Archives and a checksum file publish to releases; the Hex package carries
    the resolver, the build machinery and the checksums, with binaries left
    on the release. Published at `0.1.0-dev.7`, consumed from
    `cloth_fit_cli` with `mix.lock` pinned to it.

    The naming avoids the OpenUSD trademark by construction: the repository
    is `fabric-stage-runtime`, the package `stage_runtime`, the module
    `StageRuntime`.

    Open: rewire the downstream adapters to fetch the prebuilt SDK through a
    single root rather than compiling it.
    """

    details "3. The solver reads and writes USD", ~S"""
    Landed on all three desktop platforms, with two pieces open.

    The reader and writer sit behind a dlopen'd `cloth_fit_usd` C-ABI
    bridge. The NIF links no USD at all and resolves the bridge at runtime,
    which is what keeps USD's TBB away from PolyFEM's static oneTBB; linking
    both into one process aborts on a double instance.

    A canonical convention is enforced on load: inputs are normalised from
    their declared authoring convention, defaulting to Z-up with -Y front,
    and output carries `upAxis="Y"` with right-handed mesh orientation. This
    fixed a latent defect where geometry was Z-up and the USD layer asserted
    Y-up, and an avatar validator that had Y-up hardcoded.

    UVs, normals, per-face materials and vertex order survive the round trip;
    the writer keeps groups as native subsets plus custom attributes and does
    not triangulate authored faces. Ngon preservation of solver OUTPUT is
    descoped: the solver works on triangles, so its output is triangulated
    the way the OBJ path already was.

    Open: read garment, avatar and skeleton correspondence from a single USD
    stage rather than an OBJ and JSON pair; convert the four bundled examples
    and diff against the OBJ baselines, where only one is verified so far;
    and decide whether OBJ stays as an import-only fallback.
    """

    details "4. Burrito packaging", ~S"""
    Landed for two targets. `cloth_fit_cli` is a Mix release whose
    application runs the CLI, and which stays an ordinary OTP application
    outside the packaged binary.

    Linux x86_64 builds natively and Windows x86_64 cross-builds, each
    shipping its own native library. The USD runtime bundles once: the
    private directory carries the bridge, the monolithic USD library, oneTBB
    and a relocatable plugin tree.

    Both binaries build, self-extract, load the NIF and run end-to-end in CI.

    Open: macOS arm64 and Linux arm64 targets; running all four examples,
    which needs the bundled garment assets; and publishing the binaries to
    releases rather than leaving them as build artifacts.
    """

    details "5. Demo and QA, and the open questions", ~S"""
    Not started. A `fit` command demonstrating the retarget from the
    standalone binary, an Elixir-bound Polyscope viewer for the solver's USD
    output, a QA pass per example confirming an intersection-free fit with no
    lost ngons, UVs or materials, and the end-to-end documentation.

    Two questions the issue left open. Whether the downstream USD adapter can
    expose USD without its engine-addon layer, or whether a headless build is
    needed. And whether the viewer has a C++ API surface stable enough to
    bind across all four triplets.
    """


    drafted_by :ai
  end
end
