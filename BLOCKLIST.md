# Why each blocklist entry is blocked

`CLAUDE.md` carries the blocklist itself -- the table of what is excluded and the one-line
reason for each. This file carries the argument behind the rows that need one.

**The table is the rule; this is the reasoning.** They are split because they are read at
different times. Somebody checking whether a source is permitted reads a table and stops;
somebody proposing to lift an entry, or wondering whether their case is the one it was written
against, needs the measurement and the retractions. Keeping both in one document meant 570
lines of argument sat between a reader and the next agreement.

Neither half is allowed to drift from the other. `scripts/check_blocklist_detail.py` requires
that every row saying "see below" resolves to a section here, and that every section here
corresponds to a row -- so an entry cannot lose its argument, and an argument cannot outlive
the entry it defends.

### Abliteration is blocked, and the model's own card is the argument

`huihui-ai/Huihui-Qwen3.5-9B-abliterated` is the named instance and the
technique is what is blocked. It came up as a base for an EditScore reward
model, because a grader that refuses to look at an unclothed figure render
scores it low for the wrong reason, and our renders are unclothed bodies.

The card says what was done, in its own words:

> This is a crude, proof-of-concept implementation to remove refusals from an
> LLM model without using TransformerLens.

A refusal direction is found and subtracted from the weights. What that
subtraction does to everything else is not measured, and for a **reward model**
that is the whole problem: the artefact's job is to be a reliable judge, and it
has been edited in a way nobody characterised. A generator that drifts produces
a picture somebody looks at. A judge that drifts silently relabels a corpus.

Tensor parity is not evidence of behavioural parity, and it was tempting to
treat it as such: the abliterated model keeps all 775 tensors against the base's
775, where the Heretic-tool build drops the 15 `mtp.*` ones. Same shapes, edited
values.

**Heretic is permitted, and the line is measurement rather than technique.**
Heretic is automated abliteration — the same directional ablation with a
parameter search over it — so a technique-shaped rule would catch both, and this
one does not. What is blocked is a _crude, unmeasured_ edit, of the kind its own
author calls a proof of concept. A search that optimises against a stated
objective has an argument behind each weight it moves; a hand-subtracted
direction has none.

That distinction is doing real work rather than splitting hairs, and it can be
checked: an abliterated model comes with no statement of what its edit cost, and
a Heretic build comes with the objective it was optimised against. If a future
candidate offers neither, it is the crude case whatever it is called.

**MEASURED: THE STOCK MODEL DOES NOT REFUSE, SO THE PREMISE WAS FALSE.** This
section first said the count was one run away. It has been run.
`Qwen/Qwen3-VL-8B-Instruct` with the stock
`EditScore/EditScore-Qwen3-VL-8B-Instruct` adapter, no uncensoring of any kind,
was asked to grade twelve restyles of an unclothed ANNY render:

    1024x1024 inputs   0 refusals of 12
    512x512 inputs     0 refusals of 12

Every frame came back with a number. A refusal here would be a non-answer rather
than a low score, and there were none of either kind — the low scores it did
return are judgements about edits that ignored their instruction, which is the
model working.

So the reason for reaching for an edited base did not exist. Nobody had checked,
and the check cost one run against images we already had. That is the whole
entry: refusal tuning targets requests to _produce_ content, grading is not
producing, and an unmeasured assumption sent us looking for weights that
somebody had modified in ways nobody characterised.

The sizing came free with it, and it is the useful half now. At NF4 the weights
are 6.29 GiB and the peak is 8.60 GiB on 1024x1024 inputs — over the ASUS
UGen300's 8 GB — but 6.75 GiB at 512x512, which is `image_max_pixels` in
EditScore's own training config. The vision tokens were the budget, not the
weights, and feeding the model four times the pixels it was trained on was our
error rather than the device's limit.

### `rf-detr-keypoint-data` is the holdout, not a training set

It is **validation only, never training**, for two independent reasons. Either
one is enough.

**It contains the entire blinded holdout.** The repository takes every val2017
image with a non-crowd keypointed person, 2,346 of 5,000, and splits them 2,112
train and 234 test. The 523 images of `coco_person_commercial_val2017` are all
inside it:

    holdout images in its TRAIN split   481
    holdout images in its TEST split     42
    total                               523 of 523

Training on it trains on the holdout. The blinded rule is not only about
gradient steps, and a split labelled `train-*.parquet` is the most direct way
there is to take one.

**And 78% of it is licence-dirty.** Only 523 of val2017's 5,000 person images
are commercial and derivatives safe, which is what `filter_coco_licenses.py`
measures. This set has 2,346, so 1,823 carry the NC, ND and share-alike terms
that filter exists to drop. Its README states `CC BY 4.0` for the whole set, and
that claim is wrong.

The two faults compound rather than overlap. The licence-clean images are
exactly the holdout, so there is no subset that is both trainable and clean. A
keypoint training set has to be built rather than filtered out of this one,
which is what the renderer in RFD 1122 is for.

`rf-detr-detection-data` and `rf-detr-segmentation-data` are unaffected. Both
come from a Roboflow clothing set rather than COCO, and neither contains a
holdout image.

### `uv` is blocklisted for project environments, and `pixi` is why

The objection is the same one submodules get, one layer down. A `uv pip install`
leaves an environment that no file declares, no lockfile pins, and nobody else
can rebuild. `repo status` cannot see it, a diff cannot show it, and the next
desk gets a different set of versions with no report.

The failure is not hypothetical and is recorded next door. Standing up the Hailo
compiler on a Mac took more than twenty packages, discovered one
`ModuleNotFoundError` at a time, installed ad hoc. Every one of them was a real
dependency of a real tool, and after the session none of it existed anywhere:
not in a manifest, not in a lock, not in the logbook. The work was repeatable
only by repeating the guessing.

`pixi` answers exactly that. `pixi.toml` declares the environment, `pixi.lock`
pins it, both are tracked, and a second environment for a second job is a
`[feature]` rather than a second undeclared venv. `tropes-removal-model` now
carries a `gate` environment with `no-default-feature` for precisely this: the
gate's dependencies were being hand-listed in two CI `pip install` lines that
could drift from the manifest without anybody noticing.

Two limits worth stating rather than discovering.

**This is about PROJECT environments, not about the binary.** `uvx` or `uv run`
to invoke a one-shot tool that touches nothing is not what this blocks. What it
blocks is an environment that work depends on and no file describes.

**A tool that ships its own resolver keeps it.** This rule does not ask anybody
to rewrite a dependency stack that already declares itself elsewhere, and it
does not reach into third-party projects, where the density rule above already
says to match what is there.

**An embedded interpreter that declares its pins in source is exempt.** This is a
third limit and it was added because the rule as written forbade something it was
never aimed at. `pythonx` embeds CPython in a NIF and its entry point is
`Pythonx.uv_init/1`, which takes a `pyproject.toml` as a string literal:

    Pythonx.uv_init("""
    [project]
    name = "nx_shuttle_secondary"
    version = "0.0.0"
    requires-python = "==3.11.*"
    dependencies = ["onnxruntime==1.20.1", "onnx==1.17.0", "numpy"]
    """)

That block is the declaration. It is tracked, it appears in a diff, it pins the
interpreter and the packages, and anybody running the code gets the same set. The
hazard this row names -- an environment nothing declares and nobody can rebuild --
is absent. Measured once: the resolve took 219ms and installed onnxruntime 1.20.1,
onnx 1.17.0 and numpy 2.4.6, from a list a reader can see.

The reason it cannot be `pixi` instead is `weft-warp-burrito`. Burrito packages an
Elixir application into one executable, and an executable cannot shell out to an
environment that is not inside it. An embedded interpreter travels; a `pixi`
environment beside the binary does not.

What stays blocked is the shape, not the letters `uv`: an interpreter whose
packages arrive by hand, a `uv pip install` issued at runtime against a set no
file lists, or a `uv_init` block that drifts from what the code actually imports.
The pins are the exemption. Without them this is the Mac session again, with an
extra layer.

### Git submodules are blocklisted, and `default.xml` is why

A submodule pins a dependency in a file only `git` reads. `repo status` does not
see it, the manifest does not carry it, and a bumped submodule appears in a diff
as a bare hash with no name, no branch and no reason attached.

That is the same invisibility the **Sides** rule exists to stop. An unplaced
project is drift, and a submodule is an unplaced project that also claims to be
placed.

So a third-party dependency is a `<project>` in the goal manifest's
`default.xml`, on a side, with a pinned `revision`. The entry answers "what
version, and from where" in fields a tool reads: a name, a path, a remote and a
revision. A `.gitmodules` line answers the same two questions with a bare hash
and no name attached, which is the whole of the difference.

**Corrected: the "why" is not in the manifest, and the earlier wording said it
was.** This paragraph used to read that the manifest answers "what version, from
where, and why, because a comment can sit beside the entry". Comments in a
manifest are now blocklisted and `check_manifest_comments.py` in
`weftspun/weftspun-keypoint` enforces it, so that clause describes an
arrangement that no longer exists.

The reason is that a comment beside a `<project>` is the one thing in an
otherwise checkable file that nothing can check. Paths resolve, revisions fetch,
linkfiles are followed — and the paragraph above an entry goes on describing the
path or revision it had when somebody wrote it, with no diff, no CI run and no
`repo` command reporting that the two have parted. That is the same
second-place-a-fact-lives failure this section is itself written against, one
layer down.

So the "why" moves to the commit message and the pull request description, which
is where the rule on editing other people's codebases already sends it, and to
an RFD when it is durable. Both are reviewed when written and neither claims to
describe a current state, so neither can go stale in place.

Two consequences worth stating rather than discovering:

- **Fork before you pin.** A `revision` on somebody else's repository is a
  promise they have not made. `godot-cpp` is forked to `weftspun/godot-cpp` for
  exactly this, and pinned at the commit `godot-whisper` ships, so a
  nine-platform build is a question about our code rather than about the binding
  library.
- **A vendored copy is not a submodule and is not blocked.** Copying source into
  `thirdparty/` with its licence and a recorded upstream hash is visible in
  every diff, which is the property submodules lack. Prefer a manifest entry,
  vendor when the dependency is small and stable, and do not reach for a
  submodule in either case.

### Blender is blocklisted, and reproducibility is why

A render is a measurement, and a measurement that cannot be re-run identically
is not one. Blender's headless output moves with the version and with the build
flags it was compiled against, so the same scene rendered on two desks is two
corpora with one name. Nothing reports the difference: the images look right in
both places.

**No exceptions.** Not for a depth pass, not for a one-off bake, not for a
person opening the GUI to check something by eye. A carve-out for manual use is
how the dependency comes back, because the manual result is what somebody then
wants to keep.

The version installed here when this was written was **5.2.0 LTS**, build date
2026-07-14, from a package manager, pinned by nothing. That is the whole
argument in one line: no file in this workspace records it, `repo status` cannot
see it, and the next desk has whatever its own package manager last offered.

**What this costs, stated rather than discovered.** Two things depended on it
and both are now open questions rather than solved problems.

`render_image.py` in `6-datasource/dataflow-coco-gemx` runs as `blender -b
--python render_image.py`, and it writes the depth pass. Depth is the
conditioning signal for the generation path, not a by-product, so this is a hole
in the pipeline and not a tidying-up. The file stays in the tree as the record
of what the pass has to produce; it is not the way to produce it any more.

RFD 1122's PBR bake said to do the bake in Blender because MPFB2 is a Blender
addon and the material was authored there. That method is gone with this entry.
The bake still has to happen -- albedo, roughness and normal over the hm08 UV
layout, metallic a constant zero -- and it now needs a renderer that a
`pixi.toml` can pin.

The replacement is not named here, because naming one without measuring it is
how the last unpinnable dependency arrived. What a candidate has to show: it
installs from a lockfile, it renders the same bytes twice on two machines, and
the check for that ships with it.

### BRIA RMBG is blocklisted, and we already own the alternative

`briaai/RMBG-2.0` removes an image background, and Pixal3D's `preprocess_image`
reaches for it whenever an input has no alpha channel. It fails two bars at
once.

**It is gated.** Hugging Face answers `401 ... Access to model briaai/RMBG-2.0
is restricted` until somebody accepts terms in a browser. A licence that cannot
be read without accepting it cannot be gated on, which is the same objection
that keeps DWPose out: terms nobody has read travel into whatever the model
touches.

**And it is non-commercial.** RMBG is offered for non-commercial use with a
separate paid agreement for anything else, which is the class
`filter_coco_licenses.py` exists to drop.

**What replaces it, and the answer is different for the two cases.**

For anything this workspace renders, no matting model is needed at all. The
silhouette of a render is not a thing to infer from pixels: it is which rays hit
the body, which the depth AOV already reports exactly. `render_view.py` writes
RGBA with that alpha, and `preprocess_image` uses an existing alpha channel
directly rather than calling any model. The matte is then ground truth rather
than a prediction, which is strictly better than what the blocked model would
have produced.

For images we did not render, See-Through is the in-house route. It is
passthrough by construction, it already separates a picture into labelled
layers, and RFD 1079 covers what it does and does not model. Reaching for a
gated third-party matter when the workspace maintains a segmentation model of
its own is the drift this table exists to stop.

The distinction worth keeping: the render case removes the dependency, and the
photograph case replaces it. Only the second is a substitution, and only the
second needs measuring against what it replaced.

### Qwen-Image-Edit corrupts at the only precision this desk can run it

Apache-2.0 in base and weights alike, and that is not the problem. It is 20.43B
parameters, 57.7 GB on disk, needing roughly 38 GB at bf16 against a 24 GB card.
So it runs here at NF4 or not at all, and at NF4 it corrupts (the measurement
that follows is the reason).

What makes it a blocklist entry rather than a hardware note is that the
quantised path is also measurably broken. At NF4 it peaks at 11.9 GiB and
returns images speckled across every pixel — camera-correct and noise-corrupted,
the figure roughly in place under a layer of grain. The silhouette scores run
0.098 to 0.719 against a control of 0.222, so some frames are barely
distinguishable from a body that moved 20 px.

Three explanations were eliminated rather than assumed, and each cost a run:

- **Not the torch version.** `interactor-pixal3d` recorded the same corruption
  with torch 2.4.1 the one constant, and asked for a retest at 2.6 or newer. On
  torch 2.11.0+cu128, diffusers 0.40.0 and bitsandbytes 0.50.1 it is unchanged,
  so that hypothesis is retired rather than carried forward.
- **Not the guidance.** The first run passed `true_cfg_scale=4.0` with no
  negative prompt, which diffusers silently ignores. Re-run with guidance
  actually on: same corruption, twice the time.
- **Not the input.** OmniGen2 edits the identical grey matte render cleanly, so
  the frame is not out of distribution in a way that would break any editor.

8-bit would have isolated the quantiser and is not available here: int8 puts
about 20 GB of weights on a 24 GB card, and the run reached step 3 of 30 at
4,925 s/it with 42 GB resident in host RAM — 37 hours projected for one image,
against 3.3 s/it at NF4.

**The corruption was measured under our settings, not upstream's, and is not
being chased.** Both runs used 30 inference steps where upstream's examples use
50, and the guidance re-run passed an empty negative prompt -- the same empty
string that turned out to be doing all the work in the OmniGen2 comparison
retracted above. So "broken at NF4" should be read as broken under a
configuration we chose, with at least two knobs untouched.

Nothing about the block depends on that, which is why it is a qualification
rather than a retraction. The model needs about 38 GB at bf16 against a 24 GB
card, so on this desk it runs only in the mode that does not produce corpus
data, and that is true whatever the step count says. The honest position is:
blocked for a structural reason, plus a quality observation that was not run to
ground.

**Not blocked for hardware that can hold it.** A card with 48 GB or more runs
the published bf16 path, which nothing here has tested and nothing here impugns.
The entry says something narrower: on this desk the only runnable mode is the
one that corrupts, and the retraction of Condition 5 on 2026-09-02 (which had
also forbidden it as policy) does not change the corruption.

OmniGen2 is the replacement and needs no exception — 7.8B, Apache-2.0, 17.3 GiB
at bf16, clean output on the same input.

### P3-SAM's licence excludes territories, which is a different failure

`Tencent-Hunyuan/Hunyuan3D-Part` ships under Tencent's own Community License
Agreement, and it carves out the EU, the UK and South Korea. RFD 1041 records
the model as MIT; that is wrong, and `logbook-rfd1016-model-repos.md` already
corrected it by reading the real LICENSE file.

The other entries here block on what the output may be used for. This one blocks
on **who may run the tool at all**, which is a worse property for a workspace
whose collaborators and customers are not enumerated in advance. A restriction
on the output can at least be traced through a corpus; a restriction on the
operator means the same command is permitted at one desk and forbidden at
another, and nothing in a manifest or a build log would show the difference.

Passthrough does not rescue it either, and it is worth saying why, because the
OpenRAIL entry does rescue passthrough uses. That exemption turns on the
restriction travelling with a single artefact to whoever supplied it. A
territory exclusion does not travel with the artefact — it sits on the person
invoking the model — so the distinction the OpenRAIL rule is built on has
nothing to bite.

### Krea 2 is revenue-gated, and that propagates

The Krea 2 Community License permits commercial use free only below \$1M
company-wide annual revenue and fewer than 50 seats; above either line it needs
a separate enterprise agreement. That is a use restriction, and this workspace
already has a rule about those: OpenRAIL-M is blocked as a _generator_ because
restrictions travel into whatever trains on the output, where no licence check
can see them afterwards. Krea 2 is a text-to-image generator, so its outputs are
corpus data, so the same reasoning applies unchanged.

The revenue threshold makes it worse rather than better, and the reason is worth
stating. Whether the licence is satisfied depends on _who deploys the trained
model_, which is not a fact about our corpus and not one we can settle in
advance. A term that clears today for a small deployer and fails for their
customer is a term that cannot be gated on at corpus-build time.
`logbook-rfd1016-model-repos.md` already flagged this as "clears the bar for a
small deployer, not for every possible customer" — this entry is that flag
resolved rather than carried.

**The second reason is newer and independent.** RFD 1016's plan for it was the
Q4_K_M GGUF set: 33.8 GB bf16 down to 9.30 GB quantised, because that is what
fits. GGUF is blocklisted as a model format (see the ggml row above), and the
Q4_K_M path is exactly what GGUF's blocklist entry addresses. So even with the
licence resolved, the deployment shape RFD 1016 planned is closed by the GGUF
row rather than by the licence row.

Neither reason depends on the other. A permissive re-licence would leave the Q4
problem, and a 48 GB card running bf16 would leave the revenue gate.

### A corpus generator must be a checkpoint we hold

Any API-only model is excluded as a _corpus source_, and the reason is
structural rather than contractual, so it survives whatever the terms happen to
say this year.

**Condition 1 cannot be satisfied.** The generated-synthetic rule requires the
generating model and checkpoint recorded with the data so the corpus can be
regenerated and its provenance answered later. A hosted model has no checkpoint
to pin: the weights change on the vendor's schedule and the endpoint is
eventually retired, so "generated by X" stops resolving to the thing that
generated it. That is the same failure `EasyDiffusion outputs` is blocklisted
for, arriving through a different door.

Two further reasons apply to Nano-banana / Gemini specifically, and both would
be sufficient on their own:

- The [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms)
  state that users "may not use the services to develop models that compete with
  the services", nor "reverse engineer, extract, or replicate any component of
  the services, including underlying data or models". Building a training corpus
  _is_ using the service to develop a model; whether the result competes is a
  judgement we are not positioned to make, which is the same propagation problem
  OpenRAIL poses, now with a counterparty able to enforce it.
- On the unpaid tier and AI Studio, Google uses submitted content **and
  generated responses** to improve its products, and human reviewers may read
  them. Our renders, prompts and captions would go with it.

Worth recording how SDPose-OOD actually used it, because the paper is the reason
the question came up: Nano-banana produced the colour-sketch variant of COCO-OOD
— an **evaluation** set, not training data — and the sets under test were
deliberately made with CycleGAN and StyTR² "to avoid introducing priors from
large-scale pretrained diffusion models". Their own caution is the argument
against reaching further than they did.

Nothing is lost by the exclusion. CycleGAN fills the stylisation role and clears
all three bars: BSD, offline, and pinnable.

### A generator needs licence-clean depth conditioning, not just a licence

The permissive licence is the easy half and it is not the deciding one. Every
corpus use here renders an ANNY pose and requires the generated image to keep
that geometry, so a generator that cannot take a **depth** control cannot do the
job however clean its terms are.

Stating it as a rule rather than a list, because the list keeps growing and each
entry arrives looking attractive:

- **HiDream-I1** is **MIT** — the most permissive licence of any candidate
  reviewed — and its only conditioning is `ControlNetLoRA/hidream-i1`: a single
  LoRA, not a ControlNet family, under `license:other`, with 14 downloads and no
  likes. That fails the same way the FLUX ControlNets do, on unreadable terms
  rather than on absence.
- **SANA** is Apache-2.0 throughout and its ControlNet _architecture_ supports
  depth — `SanaControlNetModel` is in diffusers. **No depth checkpoint is
  published**: the released weights are HED only. Edge conditioning from a
  render carries silhouette and internal contours with no depth ordering, so it
  cannot say which limb is in front, and for a body limb overlap is the hard
  part. This is the one candidate whose gap is _work rather than terms_ — the
  licence is clean end to end, so a depth ControlNet could be trained. Costed as
  a training job, not adopted as-is.
- **FLUX.1** fails a third way, below.

Three clear at the time of writing, all Apache-2.0 in base _and_ control:

- **Qwen-Image** — a union plus a dedicated depth model, from several
  independent maintainers.
- **Z-Image-Turbo** — union, `alibaba-pai`. **Kolors is not blocklisted, and its
  position is precise.** It is the only from-scratch, Apache-2.0,
  SDXL-architecture model with its own ControlNets — trained by Kwai with a
  ChatGLM text encoder, so it carries no SDXL weight lineage and none of
  OpenRAIL's terms. Architecture similarity is not licence inheritance, and the
  converse holds too: relabelling an SDXL _derivative_ as Apache-2.0 does not
  shed OpenRAIL++'s use restrictions, which is what makes `segmind/SSD-1B` a
  trap rather than an alternative.

Two measurements bound what it can do, and both were taken rather than assumed.

**It cannot borrow SDXL's ControlNet ecosystem.**
`xinsir/controlnet-union-sdxl-1.0` and `-depth-sdxl-1.0` are Apache-2.0 and
heavily exercised — 112,265 and 17,763 downloads — so pairing one with Kolors
would have solved the exposure problem outright. Comparing configs says no:
`cross_attention_dim`, `block_out_channels` and `transformer_layers_per_block`
all match, and two things do not. Kolors'
`projection_class_embeddings_input_dim` is **5632** against SDXL's **2816** —
exactly double, because ChatGLM's pooled embedding is larger — and Kolors
carries `encoder_hid_dim` 4096 for its 4096→2048 projection where the SDXL
ControlNet has `None`. The shapes disagree, so the load fails rather than
degrades.

**And its ControlNets are off the standard path.** `Kolors-ControlNet-Depth`
declares `_class_name: ControlNetModel_JQ`, a bespoke class, and diffusers has
no `controlnet_kolors.py` — so using it means Kwai's own inference code, not
stock diffusers.

So Kolors is available and carries a real cost: ~150 downloads on its depth
control, plus a non-standard code path. That is a fallback to reach for
deliberately, not a peer of the exercised options.

**The consequence, stated rather than left implicit: nothing non-Alibaba
clears.** Qwen-Image and Z-Image-Turbo are the same house in base and control
alike — Qwen team and Tongyi-MAI, with `alibaba-pai` publishing controls for
both. So the two remaining options are one lineage wearing two names, in the
same way three COCO-trained estimators looked like three opinions and were one.
Kolors was the only different house (Kwai), and dropping it leaves the
common-mode exposure unaddressed rather than solved.

That is an accepted risk, not an absent one. If a corpus later needs
cross-checking against a generator sharing no lineage with the one that produced
it, this is the gap it will run into, and the answer will be to qualify a new
candidate rather than to rediscover that none exists.

Kolors also proves the point above from inside one organisation:
`Kolors-ControlNet-Depth` and `-Canny` are tagged Apache-2.0 while `-Canny`'s
sibling `Kolors-ControlNet-Pose` carries **no licence tag at all**, despite more
downloads. One control's terms say nothing about another's, even under the same
owner.

An enumeration by model name is not sufficient to establish this, and the first
pass here got it wrong twice: HiDream's ControlNet is published under a
different org, so a name-scoped search missed it, and SANA's architecture
supports depth even though its checkpoints do not. Search the ecosystem, then
read the licence of the _control_ weights, not only the base.

Popularity is not the measure. Z-Image-Turbo has roughly 27x Qwen-Image's hosted
run count and that decided nothing; conditioning did. And a hosted endpoint adds
the platform's terms to the model's, which matters here for the same reason the
OpenRAIL analysis did — restrictions propagate into weights, and a corpus
generated through an API carries both sets.

### FLUX.1: split in the wrong place

The two releases fail in opposite directions, and neither half is usable for a
conditioned corpus.

**FLUX.1 [dev]** is non-commercial. That is the ordinary NC exclusion, the same
class as Sapiens, and it needs no further argument.

**FLUX.1 [schnell]** is Apache-2.0 and 4-step distilled, which reads as ideal —
and it has no licence-clean way to be conditioned. Every FLUX ControlNet targets
_[dev]_: InstantX Union, Shakker-Labs Union-Pro and Depth, InstantX Canny. All
of them are tagged `license:other`, which is unreadable under the rule above,
and all are trained against a non-commercial base.

Loading a _[dev]_ ControlNet onto _[schnell]_ fails twice over. The two models
differ in guidance behaviour, so it is not merely a licence question — and it
propagates the base model's terms into whatever the output trains, which is the
same propagation that blocks OpenRAIL-M as a generator.

So schnell is usable for unconditioned text-to-image and unusable wherever
geometry must be pinned, which is every corpus use this workspace has. A
generator that cannot take a depth control is not a generator for this pipeline.

Qwen-Image is the replacement and does not have this split: the base is
Apache-2.0 and so are the ControlNets, from several independent maintainers,
including a dedicated depth model rather than only a union.

### OpenRAIL-M: blocked as a generator, permitted as passthrough

The line is what the model is _for_, not which weights it is:

- **Passthrough** — the model transforms an input the user supplied and hands
  the result back. LayerDiffuse cutting an image into layers, Marigold reading
  depth off a photo, LaMa filling a hole. The input carries the provenance, the
  output goes to whoever supplied it, and the restriction travels with a single
  artefact. **Permitted.**
- **Generator** — the model samples new content, and that content becomes a
  corpus something else trains on. Here the restriction does not stay with one
  artefact: it propagates into weights, where no licence check can see it
  afterwards. **Blocked.**

This is the same cut the synthetic-data rule already makes. A transformation of
an asset we hold is closer to _constructed_; sampling appearance from a learned
distribution and training on it is _generated_, with condition 1 — recorded
provenance — becoming unanswerable once the result is inside somebody's weights.

So `seethrough-ggml` is compliant. It is SDXL-derived through JuggernautXL v6
and OpenRAIL-M throughout, and it is passthrough by construction: See-Through
takes the user's image and cuts it. Nothing it emits trains anything.

**The case this rule does not settle, and must not be assumed either way.**
Rendering an ANNY pose and running img2img over it is _operationally_
passthrough — our own asset in, geometry preserved, appearance changed — but its
destination is a training corpus, which is the generator case. Operation says
permitted, destination says blocked.

Destination wins, because destination is what the restriction is about. A corpus
generated this way propagates OpenRAIL-M terms into a model, and after training
there is nothing left to inspect. That closes the ANNY → ControlNet →
JuggernautXL pipeline as a corpus route.

Permissively licensed generators are the way through if that pipeline is wanted,
and the choice is narrower than it first appears. **Qwen-Image** (Apache-2.0) is
the one that clears both halves: the base and its ControlNets are Apache-2.0,
from several maintainers, with a dedicated depth model. FLUX.1 is blocklisted
above for the split that makes it useless here. Lumina-Next is Apache-2.0 but
its conditioning support has not been checked.

None is a drop-in; all are non-SDXL, so ControlNets and any ggml port would need
redoing. Nothing about See-Through's own stack has to change, because
See-Through does not generate.

The `anime-with-caption-cc0` entry is a **quality** exclusion, not a licensing
one — the licence is CC0 and could not be cleaner. Hands are malformed across
the set, and `handwear` is one of the 24 body-part tags See-Through must
separate, so the defect lands directly on a supervised output rather than
somewhere harmless. A corpus that is free to use and wrong about the thing being
learned is worse than one that is merely encumbered.

**The captions are separable from the images, and they are not excluded.** The
defect is in the pixels: hands are drawn wrong. A caption is text, and carries
none of it. So the entry blocks the _images_ and permits the _captions_, which
may be reused as prompt conditioning — the intended use is generation where ANNY
supplies the shape and the caption supplies the language, so no pixel from this
dataset reaches the corpus.

That split is worth stating rather than leaving to judgement, because the two
obvious readings are both wrong. Blocking the captions too would discard clean
CC0 text over a defect it does not contain; unblocking the dataset because "we
only wanted the captions anyway" would leave the images available to whoever
reads the entry next.

One consequence of permitting the captions: a generator prompted by them still
draws its own hands, and SDXL hands are a known weak point. Excluding a corpus
for malformed hands and then generating a replacement with a model that malforms
them differently is not an improvement, it is the same defect with our
provenance on it. Hand quality in generated output is therefore measured —
`pose-consensus`'s finger-chain gate exists for this — before any volume run.

One consequence to keep straight:
`seethrough-ggml/art/concept/anime_with_caption_cc0_0023.jpg` comes from this
dataset and is the reference input for every timing in MADR 0010/0011/0013 and
the optimization ladder. Those measurements stay valid — a benchmark input needs
to be fixed and representative, not defect-free, and re-basing them would
discard the comparability that makes them a ladder. The exclusion is on
_training_, not on that one image's continued use as a stopwatch.

### The Neural Engine is blocked as an execution target, and 2 GiB is why

Measured on the M2 Pro in RFD 1142, with `scripts/ane_bench.py`. The part is
fast. It is also too small, and the second fact decides.

**The ceiling is 2 GiB of weights, at exactly 2^31 bytes.** A model at 2002.4
MiB places entirely on the device; one at 2058.0 MiB places entirely on the
GPU. It fails wholesale rather than splitting, so a model that crosses the line
does not degrade, it relocates.

    weights MiB   ops   on ANE
    1946.8         72   1.000
    2002.4         74   1.000
    2058.0         76   0.000
    8176.2        296   0.000, and Metal takes all 296

A second cap sits on any single weight tensor near 224 MiB: 220.5 MiB places,
228.4 MiB does not. The two are independent, and a sweep that grows only width
finds the second and reports it as the first. Neither is documented; Apple does
not publish the internal buffer limits, and the per-axis extent cap that IS
documented is orders of magnitude away from where these fail.

**Metal on the same machine holds 8176.2 MiB at full placement**, which is the
UGen300's whole 8 GiB working set. So the alternative is not a compromise: it
is the same silicon package, four times the capacity, and no wall in sight
where the search stopped.

**And on the real model Metal is also faster.** The RF-DETR device half at 576,
converted natively, places 373 of 373 operations on either engine:

    ane    119.7 ms
    gpu     62.7 ms

The Neural Engine wins on a synthetic 3x3 stride-1 convolution stack, 13.58
TFLOP/s against 6.98, and loses by 1.9x on the graph we actually ship. A
benchmark shape chosen for the accelerator flatters it, which is the reason
that row exists here rather than a claim that the part is slow.

**What this entry does not say.** It does not say the Neural Engine is unusable,
and it does not retire `ane_bench.py` — a part reaching 86% of its cited peak is
worth re-testing when a model fits under 2 GiB, and the apparatus is kept so
that re-test costs a command. The blocklist is about what may be planned
around, and an undocumented 2 GiB ceiling fails that test.

**The third ground is numeric, and it is the one that decides.** At fp16 the
device half converted natively agrees with PyTorch to:

    units   ms med   max|diff|   the port's 4.2e-03 bound
    ane      121.6   4.311e-02   FAIL, ten times over
    gpu       62.0   3.524e-03   ok
    cpu      133.0   2.425e-01   FAIL

Metal is the only configuration that both passes and is fastest. The Neural
Engine runs every one of the 373 operations and still misses the bound the port
already holds, so its speed comes only at an accuracy we cannot ship.

This also settles `neuralEngineUsefulForBackbone = 0` in `rfd1122-plan.usda`,
which was measured through onnxruntime's CoreML provider at 1685.1 ms and
reproduced here at 3758.9. Natively the same graph runs at 121.6 ms, so that
figure was 31x pessimistic and was measuring a partitioner. The flag's VERDICT
survives its evidence being wrong: the Neural Engine is unsuitable for this
backbone, on precision rather than on speed. A right answer for a wrong reason
is still worth correcting, because the wrong reason predicts wrongly elsewhere.

These figures come from an explicit pairing matrix. An earlier version of
`gate_coreml_device.py` matched outputs by shape, and the device half returns
two tensors of identical (1, 256, 48, 48) shape, so it compared one reference
against the other output and reported 2.5e+00 on every row. The CPU row is what
exposed it: Core ML's own CPU cannot disagree with PyTorch by 2.5.

### The tinygrad NVIDIA eGPU is allowlisted; the operational costs are why the record stays

The eGPU is allowlisted under CLAUDE.md's compute rule ("GPUs the operator
owns are the only compute"). The three failure modes below still hold and
are accepted as operational costs; this section stays as the record of
what those costs are.

An RTX 3090 in a Sonnet eGFX Breakaway Box reaches this Mac mini over
Thunderbolt, driven by `org.tinygrad.tinygpu.driver2`, a DriverKit extension.
It enumerates, it is `arch=sm_86`, and it works. It was dropped in the
first pass and is unblocked now.

**The device takes one initialisation per power cycle.** `nvd.py`, the resident
daemon written to hold that one init, states the consequence in its own
docstring: a second init fails, BAR0 returns all-ones, and no reset recovers
it. Recovery is a reboot or a dock power cycle. So the process holding the
device cannot be restarted to pick up a change — editing it spends a reboot —
and any crash spends one too.

That cost was paid during RFD 1142. The daemon had held the device for three
days and served 9,645 requests when the `TinyGPU` userspace server restarted
underneath it. `nvd` captured its socket at init and cannot reconnect, so every
compute request now returns `BrokenPipeError` while `ping` and `info` keep
answering. A liveness check that passes while the device is unusable is the
shape of failure this workspace names in rule 3.

**Its guard against the second init fails open.** `boot_id()` compares the whole
of `kern.boottime`, including a `usec` field that moved during this boot:

    guard:   { sec = 1787432316, usec = 580657 }
    current: { sec = 1787432316, usec = 809637 }

The strings differ, the guard concludes a different boot, and a restart would
attempt exactly the second init it exists to prevent. Comparing `sec` alone
repairs it, and the repair is not attempted here because the entry is a
decision to stop rather than a bug report.

**What replaces it is already measured.** RFD 1142 puts Metal at 8176.2 MiB of
weights at full placement and 62.0 ms on the RF-DETR device half, inside the
port's numeric bound. The eGPU's advantage was capacity, and a 24 GiB card
still has more; what it does not have is a compute path that survives its own
daemon restarting.

`~/.local/nvd` stays on disk and outside any manifest, which is its own finding:
three days of measurements ran through a daemon launched by `uv run --with
tinygrad`, unpinned and undeclared, in a workspace whose blocklist has a row
about exactly that.

### onnxruntime's macOS GPU providers are blocked, and the measurements are why

Two execution providers can reach this Mac's GPU from onnxruntime, and
neither earns a place. Measured on one convolution stack, fp16, 541.6 GFLOP
per inference, against Core ML driving the same GPU at 6.97 TFLOP/s:

    provider                        TFLOP/s   of the same GPU
    CoreML EP, MLComputeUnits=CPUAndGPU  7.01   1.006
    WebGPU EP                            1.90   0.272

**The CoreML provider only looks like a second backend.** Pinned to the GPU it lands
within 0.6% of native Core ML, which is run-to-run spread. It is a front end
onto the Metal path Core ML already provides, so it inherits every reason
Core ML was dropped: the per-model porting cost, and a graph it cannot take
whole gets partitioned back to the CPU. On the RF-DETR device half that
partitioning measured 3758.9 ms against the CPU's 710.7.

**The WebGPU provider is a genuine second path and is 3.7x slower.** It
reaches Metal through Dawn without Core ML, which is the thing worth wanting,
and it returns 0.27x of what the same silicon gives through Core ML.

A note on how this entry came to exist, because the first reading was wrong.
`get_available_providers()` on the stock wheel returns CoreML, Azure and CPU,
and that was read as onnxruntime having no Metal path but Core ML's.
`onnxruntime-webgpu` 1.27.0 does ship macOS arm64 wheels; they need
`macos = "14.0"` in pixi's system requirements, because the wheel is tagged
`macosx_14_0_arm64` and pixi targets 13.0 by default. One build's provider
list describes that build.

**Neither provider reaches past 2 GiB on the Neural Engine either.** That
ceiling belongs to the ANE compiler rather than to any runtime, so no
execution provider moves it.

**THIS ROW IS ABOUT macOS AND NOTHING ELSE.** onnxruntime is the runtime that
spans the fleet, and the other desks are well served by it:
`DmlExecutionProvider` on Windows and `CUDAExecutionProvider` on Linux, both in
the stock build alongside TensorRT, ROCm and OpenVINO. Blocking two providers on
one platform says nothing about those.

macOS was the hole. Its two providers reach the GPU through Core ML or through
Dawn, and the measurements above are what each returns. `onnxruntime-mlx` is the
third way in — an out-of-tree plugin EP over MLX, Apple's own Metal framework,
which a stock `libonnxruntime.dylib` loads without a fork. It is placed and
pinned in the goal manifest, and nothing about it is measured yet, so it is a
candidate rather than an answer.

onnxruntime keeps two more jobs here whichever provider wins. It is the
interchange format the Hailo Dataflow Compiler reads, and its CPU provider is
the numeric oracle every other row gets diffed against — `gate_onnx_device.py`
measures 5.066e-06 against PyTorch there.

### ggml and GGUF are blocklisted, and the missing graph is why

ggml is quick on this desk. This entry turns on a different question — where a
model in GGUF can go — and the answer is: this GPU and other desktop GPUs, the
Cloud TPU not at all, and Hailo through the vendor's own runtime rather than
through the compiler.

**"NEITHER OF THE DEVICES THIS WORK IS AIMED AT" IS RETRACTED, AND HALF OF IT WAS
ALWAYS WRONG.** `3-interactor/llama-cpp-npu-vision-upstream` is pinned in the live
manifest at `6a272903`, and the commit under it is `d35d0ec1`, authored by
`hailort@hailo.ai` and merged from `hailo-ai/hailo-mtmd-vision-encoder`. It
offloads a vision encoder to a Hailo NPU from inside llama.cpp, reading input
size, patch size and embedding sizes out of a `.hef` passed to `--mmproj`. GGUF
reaches Hailo. It reached Hailo while this paragraph said it could not, and the
checkout proving it sat in the same manifest as the paragraph.

The Cloud TPU half stands: PJRT consumes StableHLO and ggml still does not emit
it. So the sentence was half a measurement and half an assumption, and the
assumption is the half that shipped.

Hailo's Dataflow Compiler parses a TensorFlow checkpoint, a TensorFlow frozen
graph, a TFLite file or an ONNX file. GGUF is on none of those lists. Cloud TPU
runs PJRT, which consumes StableHLO, and ggml does not emit it. So ggml's
target set is a strict subset of LiteRT's, and a format that cannot reach the
deliverable hardware cannot be the single format however fast it is locally.

**No exporter can close this, which is the part worth writing down.** GGUF
carries no graph at all. `convert_ss_dec_to_gguf.py` in
`3-interactor/trellis2cpp` writes key-value metadata -- `kv_u32`, `kv_f32`,
`kv_bool`, `kv_str` -- and tensor bytes, and nothing else. The graph is 3420
lines of hand-written C++ in `trellis2.cpp`: 79 distinct `ggml_*` ops across 7
`ggml_build_forward_expand` sites, for one model. A ggml-to-anything converter
would have to lift imperative C++ back into an IR, so the gap is structural
rather than a missing tool somebody could write.

That answers a question that was asked directly and is worth closing: **ggml
cannot be converted to LiteRT.** The two share an ancestor -- the torch model
both descend from -- not an edge between them.

**This entry does not say ggml is slow, and must not be edited to say so.** No
Metal figure belongs here, and neither does the 0.27x measured against
onnxruntime's WebGPU EP. ggml was excluded on where it can go, not on how fast
it gets there. An entry that overstates its case invites the next reader to
re-derive it, find ggml quick, and quietly drop the whole row.

**What it costs, stated rather than discovered.** ggml was the only candidate
that produced a single static executable for macOS, Windows and Linux, with
native Metal, CUDA, HIP, Vulkan, SYCL, OpenCL and BLAS backends in `ggml/src`
and `GGML_METAL_EMBED_LIBRARY ON` compiling the shader source into the binary.

**"NO PROVIDER AT ALL" IS RETRACTED.** `V-Sekai-fire/turboquant-godot`, branch
`feat/turboquant-on-master`, carries "Add LLM module with llama.cpp for on-device
inference" dated 2026-07-29, MIT like the engine around it. A Godot binary with an
embedded llama.cpp module is the single-binary deliverable this paragraph said had
no provider. The loss was real when it was written and it has since been repaid —
by a repository in no manifest, which is why nobody noticed. Placement is the fix
for that, not this entry.

**The checkouts stay.** `3-interactor/trellis2cpp` and the `weftspun/ggml` fork
pinned at `331b9cba` remain in the live manifest, and so do the TRELLIS.2 port's
published f16 figures -- rel L2 2e-5 on the SS decoder, under 1e-3 on the SS-flow
DiT -- which are the nearest correctness reference for whatever replaces them.

**"THIS ENTRY GOVERNS NEW WORK" IS RETRACTED.** It was written as a boundary and
did not hold as one. Two of the checkouts above are new ggml work done after this
entry: Hailo's vision encoder at `d35d0ec1`, dated 2026-08-27, and the Godot LLM
module dated 2026-07-29. A rule new work crosses twice with no exception filed is
not governing new work, it is describing a preference. Saying so is cheaper than a
third crossing.

**Both crossings are allowed, named here so nobody has to file for them.**
`3-interactor/llama-cpp-npu-vision-upstream` and `V-Sekai-fire/turboquant-godot`
are permitted uses of ggml, and so is new work on either. A vendor's own runtime
reaching a vendor's own device is exempt, which is the ONNX row's wording and the
same reasoning: Hailo shipping a Hailo NPU encoder inside llama.cpp is Hailo's
business, not our interchange decision. An on-device single-binary deliverable is
exempt for the reason ggml was valued here in the first place — that was recorded
above as the cost of the ban and it is now the ground for the exemption.

What the row still says is narrow and factual: **GGUF carries no graph, so nothing
converts out of it.** That is the finding worth keeping, and it constrains where a
model of ours is _stored for conversion_ rather than which runtimes may be built.
Neither repository converts a GGUF to anything — Hailo runs a separate HEF beside
ggml, Godot embeds ggml whole — so neither is affected by it.

A blocklisted backend with live checkouts is exactly the shape that rots quietly,
and this row rotted three claims deep before a reader went and looked.

### The CPU is blocklisted as a model execution target, and orchestration is exempt

With the XDNA NPU blocked, the execution targets are the **Radeon 780M** through DirectML,
the **Hailo-10H**, and the RTX 3090. The first two are the deployment target -- an integrated
GPU beside a USB accelerator is an edge box -- and this row is what stops work drifting off
the accelerators onto the interpreter's own processor.

**WHAT IS BLOCKED IS WHERE A MODEL RUNS, NOT WHERE PYTHON RUNS.** The interpreter, the data
loader, the tokeniser, the JSON parsing and every gate in `scripts/` run on the CPU and always
will; a row forbidding that would forbid the machine working at all. What is blocked is the CPU
as the device a model's tensors live on: `device="cpu"` for weights or activations, an ONNX
Runtime CPU execution provider, a `--device cpu` flag. Orchestration is exempt because
orchestration is not the thing being proven.

**THE SILENT FALLBACK IS THE TRAP, AND IT IS THE SAME SHAPE AS THE DIRECTML DEFAULT.** DirectML
does not implement every operator. An unsupported op does not raise; it falls back, and the run
completes with a number that looks like a 780M measurement and is partly a CPU one. That is
rule 3 again -- a silent skip reads exactly like a pass -- and it is worse here than the device-0
trap, because device 0 is at least visible in a device name. A run that claims the 780M prints
the resolved device and asserts no fallback occurred, or it has not measured what it says.

**THE DFC RUNTIME IS EXEMPT, AND THE BOUNDARY IS WHAT IT IS FOR.** `ClientRunner.infer` in
Hailo's Dataflow Compiler runs a translated graph in emulation, on the CPU, and that is how you
find out whether a compile is worth making before you make it. It is the same act as
`gate_onnx_device.py` exporting an ONNX to diff against PyTorch, and it earns the same exemption
the ONNX row already grants twice -- a vendor's internal use, and a gate's own scratch file.

The boundary is the purpose rather than the processor. Emulating a graph to decide whether it
compiles, to read its quantisation behaviour, or to diff it against full precision is exempt.
Emulating one because it is easier than getting it onto the device is the thing this row exists
to stop, and it looks identical from the outside. What separates them is that an exempt run
produces a decision about the device; a violating run produces an answer somebody uses instead
of the device.

**What this costs, stated rather than discovered.** A CPU fallback is the thing that makes an
unsupported operator survivable: with it, a graph runs slowly; without it, the graph fails. So
this row converts performance bugs into hard errors, which is the intent and is also why a first
run against a new model will fail more often than it did.

**Gradients have somewhere to go.** The Hailo cannot compute one -- HailoRT's nine verbs are
inference and diagnostics, and an HEF is a forward graph. So `adapt` runs on the 780M or the
3090; the forward-only work that QZO exists for is what the Hailo is for.

### The AMD XDNA NPU is blocklisted as an execution target

The 7840U carries an XDNA1 NPU, `PCI\VEN_1022&DEV_1502`, driver 32.0.203.280, which nothing in
this workspace knew about until a device scan turned it up. It is blocklisted as a target.

**Decided, on toolchain surface rather than on speed.** Reaching it means AMD Quark for
ONNX-to-ONNX quantisation and the VitisAI execution provider to run the result -- a second
compiler and a second runtime beside Hailo's Dataflow Compiler, for a second device, on the
same desk. The workspace consolidated the edge target on Hailo and on the format Hailo's own
compiler is moving to; adding XDNA re-splits it.

**Nothing about it has been measured here, and that is not the reason.** No Ryzen AI runtime
is installed, no ONNX Runtime is present, and Windows registers no performance counter set for
it, so its published ~10 TOPS INT8 stands as what `gpu_tops.py` calls "a ranking and not a
budget". Whether XDNA1 gets AMD's INT4 flows or those target XDNA2 only is also unestablished.
A row resting on unmeasured performance would invite the next reader to measure it, find it
adequate, and drop the row; this rests on not maintaining two edge toolchains.

**What it costs.** AMD publishes NPU-ready exports -- `amd/gemma-4-e4b-npu-eager` splits a
model into embedding, decoder, vision encoder and audio encoder, built with Microsoft Olive --
and that decomposition is a useful reference for how a VLM partitions for an accelerator, whoever
compiles it. The reference stays readable; the device stays untargeted. That repository also
states no licence and ships a `.zip`, so it was not usable as a source regardless.

### IREE is blocklisted as a build target, and it differs from XLA

IREE is a compiler, not an execution provider. It lowers a model ahead of time
and hands back an artifact for its own runtime, so adopting it means adopting a
second toolchain beside the one that already reaches the hardware, and owning the
lowering for every target rather than calling a vendor's.

**The second clause of that title carries the weight.** An earlier draft of
the plan behind this entry treated IREE and XLA as one family and concluded from
this row that the datacenter TPU was out of reach. That was wrong, and the error
is recorded because the two are easy to conflate:

|          | what it is                                                                                    |
| -------- | --------------------------------------------------------------------------------------------- |
| **XLA**  | Google's compiler, with **PJRT** under it. What Cloud TPU runs, driven by JAX or PyTorch/XLA. |
| **IREE** | a separate MLIR compiler that _ingests_ StableHLO, an XLA dialect.                            |

They are neighbours in input format and nothing else. **This entry constrains XLA
not at all**, and the Cloud TPU route -- tapping the StableHLO that `litert-torch`
already builds, one stage upstream of the flatbuffer -- is unaffected by it. Any
future reader who reaches for that route should not be stopped by this row.

### `24yearsold/metricdepth3d_tmp` is blocklisted, and unreadable terms are why

`https://huggingface.co/24yearsold/metricdepth3d_tmp` returns **HTTP 401**. No model
card, no stated licence, no named author, and a repository name ending `_tmp`.

CLAUDE.md already settles this shape of case for datasets and the reasoning carries: a
set behind a registration form is not licence-clean, because terms that cannot be read
without accepting them cannot be gated on. A 401 is that condition at its strongest --
there is nothing to read, so nothing can be checked against the commercial-use and
derivatives bar `filter_coco_licenses.py` applies to images.

**It is not hypothetical.** `seethrough-layerdiff`, `seethrough-marigold-depth`,
`seethrough-partseg` and `seethrough-vae` all reference it, so four checked-out projects
load a checkpoint whose terms nobody here has seen. It was found by reading what the code
loads rather than what the repository's own LICENSE says, which is the only method that
finds this class of problem.

**What this row does not claim.** Not that the weights are unlicensed or that anyone did
anything wrong -- the repository may be private, renamed or withdrawn. The claim is
narrower and sufficient: an artifact whose terms cannot be read cannot enter a corpus or
a deliverable here.

**Removing it is a separate question from replacing it.** See-Through's depth stage also
loads `prs-eth/marigold-depth-v1-1`, which is CreativeML Open RAIL++-M and blocked by the
OpenRAIL-M row, so the obvious fallback is blocked too. The replacement search is in
RFD 1166.

### SMPL and every variant are blocklisted, and SOMA-X to ANNY is the bypass

The SMPL family -- SMPL, SMPL-H, SMPL-X and the later Max Planck body models built on
them -- is free for non-commercial research and requires a separate licence from the
Max Planck Gesellschaft for commercial use. That is the bar RFD 1028 sets for anything
shipped to paying users, so **the whole family is out, not just the one variant somebody
happens to be looking at.** A row naming only `SMPL` invites the next reader to conclude
that `SMPL-X` was considered and allowed.

**SOMA-X is the sanctioned bypass, and it is a real code path rather than an intention.**
Motion reaches deliverables as SOMA-X to ANNY to Godot Humanoid to VRM, pivoting on
`meshula/LabRCSF`'s `joints.csv` canonical joint table. RFD 1122 records
`AlternativeTopology` as `smplx`, `smpl`, `soma`, `anny_from_soma`, `notoes` and three
collapse variants -- `anny_from_soma` is the conversion this row depends on, and it
exists. Nothing on that path carries a SMPL topology.

**This row writes down a standing decision rather than making a new one, and that it was
unwritten is the finding.** Nothing in this repository recorded it. `SMPL` appeared only
as a topology name in that RFD 1122 list and in two logbook notes about Kimodo's
checkpoints; neither the blocklist table nor RFD 1028's own detail mentioned the family
at all. A constraint that lives only in memory is exactly the drift the anti-entropy
check exists to catch, and it went unnoticed because no gate reads a rule nobody wrote.

**It is also why one Kimodo checkpoint can be ignored rather than argued about.**
`Kimodo-SMPLX-RP-v1` carries NVIDIA's Internal Scientific Research and Development
licence, which is not commercial. That would matter if the checkpoint were reachable, and
it is not: it is a SMPL-X checkpoint, SMPL-X is blocklisted by this row, and the rig route
does not pass through it. `Kimodo-SOMA-*` is under the NVIDIA Open Model Licence, permits
commercial use, and matches the rig. `logbook-rfd1016-model-repos.md` reached the same
conclusion and warned against swapping checkpoints without re-checking RFD 1028.

### See-Through's checkpoints are blocklisted, and the taxonomy is kept instead

The repository is Apache-2.0 and that covers its code. Every checkpoint its inference
scripts actually load is hosted separately and carries no grant:

| checkpoint                                    | state                                                                    |
| --------------------------------------------- | ------------------------------------------------------------------------ |
| `layerdifforg/seethroughv0.0.1_marigold`      | no licence stated                                                        |
| `layerdifforg/seethroughv0.0.2_layerdiff3d`   | labels apache-2.0, but SDXL fine-tune -- RAIL++-M propagates (see below) |
| `24yearsold/l2d_sam_iter2`                    | no licence stated                                                        |
| `24yearsold/seethroughv0.0.2_layerdiff3d_nf4` | no licence stated                                                        |
| `24yearsold/metricdepth3d_tmp`                | HTTP 401, unreadable                                                     |

**No stated licence is not a permissive licence.** Absent a grant the default is all
rights reserved, so these fail RFD 1028's commercial bar on their own, before anything
upstream is considered.

**Shipping beside Apache-2.0 code does not extend it to weights.** That assumption was
made and checked: the LICENSE is the stock Apache text with no weights clause and the
README never mentions licensing. Projects that do intend it say so -- NVIDIA states the
weights licence for every Kimodo checkpoint separately from the code's Apache-2.0.

**A fine-tune does not reset an upstream licence.** The depth checkpoint is a fine-tune
of `prs-eth/marigold-depth-v1-1`, which is CreativeML Open RAIL++-M over
`stable-diffusion-2`. RAIL requires its use restrictions to travel into derivatives --
the same propagation the OpenRAIL-M row above is written for -- and nobody downstream can
relicense away restrictions they do not hold. An Apache-2.0 label on that checkpoint
would be ineffective rather than merely missing.

**BOTH WAYS IN ARE CLOSED, AND THE SECOND WAS ONLY CHECKED LATER.**
RFD 1166's rubric asks two questions of any candidate: `ask`, whether an
answer can be got out of it, and `adapt`, whether this desk can train,
tune or LoRA it. See-Through fails both, for different reasons.

**`ask` is closed by the weights.** Every checkpoint the inference
scripts load states no licence, so there is nothing to run.

**`adapt` is closed by the base model, which is the part that had not
been looked at.** The repository ships training scripts for all four
models -- LayerDiff, the Marigold depth stage, the VAE and the body-part
segmentation -- under its Apache-2.0. That looks at first like a way
around the weights: train our own. It is not. LayerDiff is
"diffusion-based transparent layer generation (SDXL)", crediting
LayerDiffuse, and SDXL is CreativeML Open RAIL++-M -- the row above.
Training code being permissive does not change what it trains from, and
use-restrictions propagate into anything trained on the output.

So the two routes fail independently, and closing one would not open the
other. A licence on the released weights would answer `ask` and leave
`adapt` exactly where it is.

**What is kept needs no weights.** See-Through remains a reference for layer taxonomy.
`common/live2d/scrap_model.py` carries `VALID_BODY_PARTS_V3`, 23 parts, and the
V2-to-V3 change is the valuable one: hair splits into front and back, and the eye into
irides, eyewhite, eyelash and eyebrow. That split is what CLAUDE.md points at when it
says a photograph has no ground-truth front-hair/back-hair, and it is why the blinded
COCO holdout cannot validate this task.

RFD 1166 dropped See-Through from the candidate ranking on this basis, taking it from
twelve rows to eleven.

### AnimeGAN is blocklisted, and CycleGAN is the on-hand substitute

Both AnimeGANv2 and AnimeGANv3 close both ways, same shape as See-Through.

**Ask closed.** The licence reads verbatim: _"This repo is made freely available to
academic and non-academic entities for non-commercial purposes such as academic
research, teaching, scientific publications. Regarding the request for commercial use,
please contact us via email to help you obtain the authorization letter."_ Non-commercial
only, same bar RFD 1028 rejects for shipping.

**Adapt closed.** The published checkpoints train on three named directors' theatrical
work. Naming those directors in workspace docs would violate CLAUDE.md's "Trademarks
Stay Out of Shipping Artifacts" rule, and retraining on the same source is the same
provenance close. A retrain would need a licence-clean anime style corpus this workspace
does not have.

**The substitute we already own.** `3-interactor/cyclegan-style-transfer` (BSD-2 / BSD-3,
CycleGAN by junyanz, 11.4M params per direction) plays the photo-to-stylized role
AnimeGAN was chosen for. Pretrained `style_monet` and `style_ukiyoe` ship with it;
`style_ukiyoe` is Japanese woodblock, adjacent to anime but not identical. Training a
new photo-to-anime direction is tractable on the 3090 with an unpaired anime collection
this workspace can source cleanly. The Sinew RFD 2036 packaging convention already
wraps it.

**Why this row exists.** RFD 2183 (MaskScore-driven layer decomposition on OmniGen2)
and RFD 2187 (identity overlay on ANNY via OmniGen2) briefly considered AnimeGAN as
the photo-to-anime stylizer that would produce identity-training anchors. The finding
belongs next to the See-Through row because it is the same double-close pattern and the
same recovery path (own substitute, train from clean data if the on-hand pretrained is
not quite what is needed).

### Mermaid is blocklisted as a published-figure format, and the layout solver is why

RFD 2136's network went through both formats in one day, so the
comparison is a matched pair on the same figure. The hand-authored SVG
places the critical path on a time axis, annotates each slack edge
with its days, shades the one-sigma finish window, and colours by the
house tokens. The Mermaid flowchart of the same network hands all of
that to its layout solver: nodes land where the solver puts them, the
time axis does not exist, edge labels collide at the solver's mercy,
and the theme is a global it fights the site's tokens over. The
operator's verdict on the render was the whole review.

The objection is structural, not aesthetic taste. A figure in this
workspace depicts a mechanism, and the mechanism's geometry -- what is
parallel, what waits, how long the window is -- is the content. A
format whose solver owns the geometry can express the graph but not
the claim.

What replaces it costs little: raw inline SVG inside the `.qmd`, which
Quarto passes through untouched. That keeps the source rule intact --
an SVG is text, diffable and editable like `.usda` -- while the
rendered page gets the same figure the artifact delivery shows.
`apparatus/2136-the-gacha-critical-path/page.qmd` is the reference case.

The blocklist covers figures that are published: RFD pages, logbook
entries, artifact reports. A throwaway sketch in a PR description or
an issue comment is not a published figure and is not covered.

### LLaDA is blocklisted — block diffusion is 25x too slow for real-time avatar

**Measured, 2026-08-31, RTX 3090.** LLaDA-o NF4 on the 3090 produced 64 tokens
in 5.76 s at steps=128 (11.1 tok/s), 9.3 GiB resident. The RFD 1170 presence
loop targets sub-500 ms first-packet latency for the avatar; an autoregressive
VLM (Qwen3-VL-4B per RFD 1173) streams from the first forward pass.

Block diffusion generates all positions in parallel per step and iterates to
convergence. At 128 steps the wall time is 5.76 s for a 64-token block; at 8
steps it is still 9.95 s (step count is not the bottleneck — the parallel
decode over the full block is). An autoregressive VLM streams tokens one at a
time, so first-packet latency is one forward pass rather than a convergence
loop.

**What is blocked.** LLaDA-o, iLLaDA, and LLaDA-1.5 — every variant of the
block-diffusion family — as a thinker, corpus generator, or deployment model.
The latency measurement was on NF4; bf16 does not fit 24 GiB without CPU
offload, which is itself blocklisted.

**What replaces it.** Qwen3-VL (dense, Apache 2.0) is the RFD 1173 shared VLM
for text and image; the audio path is a separate stack per RFD 1170 (Qwen3-ASR
for input, Qwen3-TTS-12Hz for output). One VLM serves both MaskScore reward
scoring (via the EditScore LoRA per RFD 1157) and the avatar's understanding.

**The MaskScore technique is not blocked.** MaskScore (mask a latent region,
reconstruct, score the decoded output) works with any denoiser. The technique
was prototyped on LLaDA-o's masking mechanism and transfers to Qwen3-VL and
the flow-matching stages (Wan-VACE, Pixal3D, VoxHammer) without architectural
change — the masking operates on latents, not on the model that fills them.

**The measurement scripts remain.** `smoke_test_lladao.py`,
`sweep_quality_lladao.py`, and `measure_context_vram.py` stay in
`llada-diffusion-lm` as the evidence behind this row. The numbers they produced
are the reason LLaDA is here.

### RunPod is blocklisted as rented compute — no budget

The operator does not have money for per-invocation or per-second GPU
billing. RunPod Serverless is capable technically (endpoint-queue-based,
cold-start-per-request, matches the shape a batched MaskScore corpus
scoring pass would take), and its 72B EditScore fit was priced at ~$150-250
for the full three-dataset pass. That is money the workspace does not have.

The credential path is also stalled: the RunPod-token → OpenBao migration
cannot complete without a client cert signed by "chibifire.com Intermediate
CA v2" that nobody has minted. So even a small trial run cannot land under
production hygiene.

**What is blocked.** RunPod as an execution target for corpus generation,
model serving, or any interactor path. The `transport-runpod` interactor
(v-sekai-fabric) is archived alongside this row.

**What replaces it.** The local desktop GPU (RTX 3090). Corpus generation
lands here too: small models at fp16 (Qwen3-VL-4B fits with room to
spare), large models at NF4 (Wan-VACE, VoxHammer).

`spot-broker` (managed Vast/RunPod deploys) is archived alongside this
row.

### Vast.ai is blocklisted as rented compute — no budget

Same reason. The operator does not have money for per-hour spot rentals.
Vast.ai was the workspace's active rented-compute path (`spot-broker`
service, `vast-market-snapshots` corpus of pricing data, three ETNF
Parquet snapshots recording ~40% churn per ~12 min at the hot
$0.18-0.22 band). Neither survives the funding constraint.

The Vast.ai pass this row retracts was estimated at ~$60-115 for a 115
GPU-hour EditScore-72B corpus scoring run — cheaper than RunPod's
per-second billing but still money the workspace does not have.

**What is blocked.** Vast.ai as an execution target for corpus
generation, model serving, or any interactor path.

**What replaces it.** Same as RunPod above: local desktop GPU only. The
precision-policy retraction (Condition 5 gone 2026-09-02) makes corpus
generation on the 3090 real; the funding constraint on rented compute
stays regardless.

`spot-broker` and `vast-market-snapshots` are archived alongside this
row. The HF dataset `chibifire/vast-market-snapshots` stays as
historical record of Vast pricing during the period the workspace
observed it — the numbers stopped being actionable when the funding
did.

### bnb NF4 4-bit is blocklisted as a QAFT / QAT path

We want real 4-bit QAFT: a training loop where the base weights are
genuinely 4-bit throughout, and the artifact that ships is a single
4-bit checkpoint. bnb NF4 with a LoRA adapter is a different shape
than that, and it fails in two ways that together make it the wrong
tool.

**Shipping shape.** bnb NF4 quantizes the base once and trains a
higher-precision LoRA on top. The artifact is (nf4 base) + (bf16 LoRA)
— two files, two dtypes, no single 4-bit checkpoint. That is
post-training-quantized base with adapter, not QAFT. It runs at 4-bit
memory but ships as two pieces, and the LoRA half never sees the same
quantization the base does.

**Kernel path.** Even if you accept the two-piece shape, bnb's fast
NF4 dequant kernel requires quantized-tensor last dims to be a
multiple of 64. When they are not, bnb silently falls back to a slow
generic path — the model runs, the LoRA trains, but per-step time
balloons. Measured on OmniGen2 (hidden_size=2520, not 64-aligned)
versus Lumina-Image-2.0 (hidden_size=2304, 64-aligned) under identical
LoRA config: Lumina2 trained at roughly 0.35 s per step, OmniGen2 was
killed after 10 minutes with no step 1/50 completed. Different kernel
path by construction, not a bug we can patch around.

**Approved 4-bit path is real QAT only.** See the two rows below for
what "real QAT" means and what specifically is blocked (post-quantization
fine-tuning as a pattern; post-training quantization as an alternative
to training-loop quantization). Between the three rows, the approved
shape is: a training loop where weights are quantized in the forward
pass throughout, with straight-through estimation on the backward, and
the artifact that saves is a single 4-bit checkpoint that was actually
trained under quantization.

**What is blocked.** bnb NF4 4-bit for any workflow described as QAFT,
QAT, distillation, or "4-bit training" — including with LoRA. The
apparent 4-bit path is a bf16-adapter-over-nf4-base pattern that ships
as two pieces at two precisions.

**What is not blocked.** bnb NF4 for inference-only decoding of a
model somebody else trained end-to-end at 4-bit. **Also not blocked:
QAT 4-bit combined with adapter and/or projector training in one
loop**, when the adapter + projector see quantized forward (fake-quant
or truly-quantized) throughout training and pass gradients through
the quantization node via STE the same way the base does. Operator
directive 2026-09-04 during coordination of RFD 2199's projector-fork
work: "you can combine QAT 4bit and adapter/projector training." The
failure this row blocks (adapter never sees quantization, distribution
mismatch at merge) is closed by construction when adapter + projector
train under quantized forward — same STE loop as the base, three
parameter groups under one Torchao Int4WeightOnlyQuantizer wrap.

Distinguishes cleanly from the bnb NF4 shape above: bnb NF4 pairs
a frozen 4-bit base with a bf16 adapter (two files, two precisions,
merge is lossy); the QAT+adapter/projector path keeps every tensor
quantization-aware in one optimizer, and merges to a single INT4
checkpoint OR ships the three tensors separately at INT4 alongside
the base — the deployment-shape call is a downstream choice, both
are compliant.

Recorded here rather than as its own logbook entry because it is a
general property of the bnb NF4 + LoRA pattern, not a model-specific
measurement.

### Post-quantization fine-tuning is blocklisted as a pattern

Any workflow that (a) quantizes a pretrained checkpoint, then (b)
trains an adapter on top of the quantized base is a specific pattern
we do not want, regardless of what tool implements it. The bnb NF4 +
LoRA row above is one instance; QLoRA-shaped pipelines built on other
quantizers are others. Blocklisting only the tool would leave the
pattern open for the next Q-something-adapter framework that
implements the same failure mode.

Two problems, both structural.

**Two-precision shipping.** The base carries quantization noise; the
adapter is trained at higher precision to compensate for it. The
artifact is two files at two dtypes, and nothing in the pipeline
produces a single quantized checkpoint. What ships is not a 4-bit
model, it is a 4-bit-with-a-bf16-crutch model.

**Adapter never sees quantization during training.** The adapter half
stays at bf16 (or fp32) throughout, so its parameters are fit against
the quantized base's noise, not against the noise of a
similarly-quantized adapter. Post-training you can quantize the
adapter separately, but the fit was to a different distribution than
the deployed one.

**Approved pattern for a 4-bit deployable checkpoint.** See the
`Post-training quantization` row below — the fine-tune-then-quantize
pattern this row used to recommend is itself blocklisted for the same
reason as post-quantization fine-tuning: the training saw fp32/bf16,
and the shipped 4-bit weights were never fit against quantization
noise. Real QAT means quantization in the forward path during
training, with straight-through estimation on the backward.

If genuine quantization-aware training is needed at any bit width,
use a framework that quantizes both base and gradient path throughout
AND produces a single quantized checkpoint on save. Torchao's
`Int4WeightOnlyQuantizer` with fake-quant during training is one
starting library; a custom STE loop is another. This is a bigger
project than the workspace currently owns; it is the compliant
alternative to the blocked shapes above.

**What is blocked.** Quantize-first-then-adapt as a pattern.
Includes: bnb NF4 + LoRA (see row above), bnb 8-bit + LoRA framed as
"QLoRA at 8-bit", any "QLoRA on X" pipeline that produces a two-piece
artifact, and future Q-something-adapter frameworks that implement
the same shape.

**What is not blocked.** Real QAT (quantization during training loop
with STE backward and single-checkpoint save). Inference-only
quantization of a model somebody else trained end-to-end at 4-bit.

This row and the bnb NF4 row above are separate on purpose: the tool
is not the pattern.

### Post-training quantization is blocklisted as an alternative to QAT

Post-training quantization runs on a checkpoint that was trained
end-to-end in fp32 or bf16, then quantizes the final weights to 4-bit
(or lower) as a final pass. GPTQ, AWQ, HQQ, and Torchao 4-bit are all
this shape. Real QAT — quantization in the forward pass throughout
training — is not.

The two rows above (bnb NF4 as QAFT path; post-quantization
fine-tuning as pattern) covered specific failure shapes. This one is
the general-position rule they leave open: even if you avoid both, a
train-then-quantize pipeline still produces a model that was optimized
against a different weight distribution than the one it ships with.

The shape of the failure.

**Training saw one distribution, deployment sees another.** The
finished bf16 weights are the optimum of a bf16 loss. Quantizing them
to 4-bit moves every weight to a nearby-but-different value, and the
loss at those new values is not the loss the training optimized. The
gap is usually small on well-conditioned tasks and large on
poorly-conditioned ones; either way, it was not measured until
inference.

**Approved shape: real QAT.** A training loop where the forward pass
quantizes weights (fake-quant or truly-quantized), the backward passes
gradients through the quantization node via straight-through estimation
(STE) or a learned surrogate, and the shipped artifact is a single
4-bit checkpoint. Torchao's Int4WeightOnlyQuantizer with fake-quant
during training is one path; a custom STE loop is another; PACT and
LSQ-style learned quantization are variants.

**What is blocked.** Any workflow where quantization happens after
training. GPTQ, AWQ, HQQ, Torchao 4-bit-as-post-pass, and any
"quantize the finished bf16 checkpoint" pipeline.

**What is not blocked.** Real QAT (quantization during training).
Loading a model somebody else trained end-to-end at 4-bit (their
training was QAT, we are inference-only).

**Cost of the ban.** Real QAT is not a standard workflow. There is no
one-line "here is the config" for OmniGen2 or Lumina2 today; the
frameworks (Torchao QAT, torchao's Int4WeightOnlyQuantizer) exist but
model-specific integration is a real project. This row is a decision
that we prefer that cost over shipping a model whose deployed weights
were never actually trained.

Recorded here rather than as a logbook entry because it is a
pattern-level rule.

### Lumina-Image-2.0 is blocklisted as an image-edit base — no native image path

Lumina-Image-2.0 is a text-to-image DiT with no native image-input path.
Every image-edit path we tried through it went through SDEdit (encode
source to latent, blend with noise at strength s, run text-conditioned
denoise), which the row above also blocklists. The two rows go together;
either one alone would still leave the other open.

The measurement: n=1000 pairs from `chibifire/editscore-reward-train`,
2-epoch Flow-LCM + teacher-endpoint LoRA on nf4 Lumina2, held-out on 20
unseen pairs from shard 90 at 4/10/30-step SDEdit. Base scored 0.716 /
0.244 / 0.862 on the 0-25 EditScore `overall` scale. LoRA scored 0.655
/ 0.689 / 0.556. The best cell in the matrix is base-Lumina2 nf4 at
30-step SDEdit, 0.862 mean, and it is still low — 14/20 pairs both arms
score 0.00 because 4-step Lumina2 SDEdit does not produce
EditScore-scoring edits on background, tone_transfer, or most
color_alter regardless of adapter or step count. See
`logbook-lumina2-flow-lcm-distill-probe.md` for the n=10 probe and
`logbook-lumina2-distill-n1000-shelved.md` for the scale-up.

**OmniGen2 is the approved exception, and the reason is architecture,
not weight lineage.** OmniGen2 is built on the Lumina2 backend but adds
a Qwen2.5-VL vision path so the model consumes the source image
natively, not through a partial-noise workaround. The inference call is
`pipeline(prompt=instruction, input_images=[source], ...)` and the
transformer sees the source through the MLLM's vision encoder at every
step. That is a different mechanism from Lumina2 + SDEdit, and it is
what RFD 2186 specifies.

**What is blocked.** Lumina-Image-2.0 as a base for image-edit training
or inference. **What is not blocked.** OmniGen2 (or any other model that
gives Lumina2's backend a native image-input path). Text-to-image
generation with base Lumina2 is out of scope for this workspace and
therefore not what the row addresses; a future project needing pure
text-to-image is free to revisit.

### SDEdit is blocklisted as an image-edit sampler — measured under-performance

SDEdit encodes the source to a latent, adds noise at strength s to
produce a partial-noise starting point, and runs a text-conditioned
denoise to produce the edited image. On our shard-90 held-out (20
pairs, seed 20260903) it produced zero-scoring edits on 14/20 pairs at
every step count we tried (4, 10, 30), and its best mean of 0.862 (base
Lumina2 nf4 at 30 steps) is still 20-30x below what a native
image-input model like OmniGen2 would need to score to justify the
substitution — the shape of the failure is source-and-instruction do
not co-condition strongly enough at any strength × step-count we
sampled.

**What is blocked.** SDEdit as an image-edit sampler for RFD 2186's
dressing overlay, and by extension any edit task that would score
against EditScore. **What is not blocked.** SDEdit for other purposes
(refinement of an already-conditioned generation, seed-fixing sampling
tricks) where the measurement above does not apply.

The measurement lives in `logbook-lumina2-distill-n1000-shelved.md`.
Any future proposal to use SDEdit for image editing should first ladder
against OmniGen2's native path on the same held-out slice; if it does
not clear that bar, this row still holds.

### rf-detr object detection is blocklisted, keypoints and segmentation stay

RF-DETR ships three heads: keypoints, segmentation, and object detection.
RFD 1102 names keypoints as the workspace's actual task; segmentation is
already used in the See-Through pipeline. The object-detection head is not
a task any RFD names, but the shipped weights invite whoever picks up the
repo to also invoke detection — that is scope drift, and downstream it
invites the whole detection ecosystem (NMS tuning, mAP metrics, COCO
detection evaluation) into a workspace that has been kept deliberately
clear of those.

This row blocks the object-detection head, not the checkpoint. Keypoints
and segmentation-head usage stay: `rf-detr-cpp` and the See-Through
segmentation path are unaffected. `rf-detr-detection-data` and
`rf-detr-segmentation-data` are unaffected. Both remain approved corpora
for their respective heads.

The failure this row prevents is a downstream reader building an
object-detection pipeline on the RF-DETR weights, calling it "already
approved because RF-DETR is approved", and thereby introducing detection
as a workspace task by accident. Kept as a row rather than a comment
because a row is the shape the workspace uses to say "this is a bounded
no", and comments are silent (rule 3).

### Apple's convention name for the 52-target facial-action blendshape set is blocked as a shipping-artifact word, and FACS action-unit vocabulary is the substitute

The 52 facial-action blendshape targets ANNY ships under
`3-interactor/anny/src/anny/data/faceunits01/targets/faceunits/*.target` are
the shape Apple's face-tracking API popularised with a specific convention
name. The shapes themselves are fine — they are what anny already exposes,
and `anny.models.facial_actions.FACIAL_ACTION_LABELS` names them by their
on-disk file identifiers. What is blocked is the trademarked convention
name for the set: invoking it in code comments, docstrings, RFDs, logbook
entries, PR descriptions, or user-facing prose implies affiliation the
workspace does not have, and it invites the legal question CLAUDE.md's
"Trademarks Stay Out of Shipping Artifacts" section already refuses.

**Substitute vocabulary.** Describe the set as "the 52 facial-action
blendshapes" or "the 52 FACS-derived blendshapes". Describe individual
shapes by their FACS action unit or the underlying muscle motion:
"jaw-open (AU 26)", "lip-corner puller (AU 12)", "brow lowerer (AU 4)",
"lid closer (AU 43)". Melinda Ozel's cheat sheet at
https://melindaozel.com/arkit-to-facs-cheat-sheet/ carries the full
mapping and is the reference the operator cited when the rule was
invoked.

**File and identifier names stay verbatim.** The `.target` filenames
(`jawOpen.target`, `mouthSmileLeft.target`, `browInnerUp.target`, and so
on) are the package's own on-disk identifiers. Code that opens them by
name is naming a file, not invoking the mark. Same for
`FACIAL_ACTION_LABELS` values in Python that reads or writes them, and
for the identifier keys in a phoneme-to-blend-weight mapping like
`3-interactor/anny/src/anny/data/phoneme_viseme_facial_action.json`.

**What triggered the row.** Task #66's face-anchor build leaned on the 52
targets as region evidence for the 68 iBUG face landmarks; the operator
caught the mark in scratchpad memory files before the code drafted.
SIDEKICK's `results-anny-viseme-check.json` carried the mark similarly.
Both stripped before publish. The row lands so future reflexive uses
across the fleet are catchable via a shared workspace reference rather
than a coordination round each time.

**What the row does not block.** Working ANNY with the 52 blendshape
shapes themselves (they are the on-disk file identifiers, not
trademarked). Grading someone else's model that uses the mark
internally — inference-only use of a third-party artefact is not
shipping our own artefact under that name. Naming the mark once in this
argument to state what is being blocked, the same shape the
`Square Enix` paragraph in CLAUDE.md's trademark section uses.

Recorded here rather than as a logbook entry because it is a naming
rule that applies to every future artefact touching the facial-action
blendshape set.

### Three.js is blocklisted as an in-browser 3D runtime

Three.js itself is MIT-licensed — the objection is not licence, it is
runtime story. The workspace ships ANNY through Godot; a three.js
path forks that story: a second scene-graph, material pipeline,
animation graph, and lighting model. Each fork is a place the two
runtimes render the same scene differently, and each difference is
a bug nothing reports.

**Substitute:** Godot as a native binary per platform, from
`3-interactor/entities-godot-sandbox` (see RFD 2211 for the
tree-choice reason). Vulkan renderer (MoltenVK on macOS). Godot's
own MToon support and its glTF/VRM importers (via godot-vrm as a
godot-sandbox ELF per RFD 2213) cover the three-vrm role.

**What this costs.**

- `7-service/service-sqlar-cas/docs/{vrm.js,index.html}` renders
  the Starforged VRM portrait per RFD 2206; moves to Godot or
  retires.
- `3-interactor/motion-bricks-cpp/demo/web/app.js` renders
  motion-bricks previews; moves to Godot or retires.
- `1-transport/usd-viewer/src/render-delegate.ts` targets THREE —
  gone with this entry; USD viewing routes through Godot's own
  USD importer.
- `6-datasource/anny-render-corpus/mtoon-reference/` compared MToon
  shades against three-vrm; comparison target moves to a Godot
  MToon renderer or retires.

**Carve-outs.**

- **Vendored upstream demos are exempt.**
  `3-interactor/moge-upstream/moge/utils/gradio_3d_viewer/`,
  `3-interactor/taskweft/thirdparty/gltf/extensions/.../examples/`,
  `3-interactor/physics/thirdparty/mujoco/wasm/`, and
  `3-interactor/mujoco-mjx/wasm/` carry three.js as part of an
  upstream we track by pin; touching them is upstream's decision.
- **A third-party viewer we do not ship is exempt.** Reading
  someone else's three.js viewer to check a glTF export is not a
  shipped artefact.

**What the row does not cover.** It does not ban WebGL as such.
WebGPU is separately blocklisted below. This row bans the three.js
runtime and the `@pixiv/three-vrm` plugin as our chosen renderer.

### Gemma 3 is blocklisted as an on-device model; only Gemma 4 is allowlisted

Operator directive 2026-09-05, verbatim: _"gemma3 is blockedlisted
only gemma4 is allowlisted"_.

The workspace's on-device Gemma line is **Gemma 4 (E2B / E4B)**
only, per RFD 2199's SIDEKICK survey and the HAILO llama.cpp fork
(`upgrade-with-hailo` branch). Gemma 3 (any variant, including
Gemma 3 270M) does not enter shipping artefacts.

**First-ship pick.** **Gemma 4 E2B @ Q4 (~750 MB)** is the smallest
Gemma 4 family member the workspace has fetched (SIDEKICK task
#86 / #92 / #94 measurements).

**What the row does not cover.** Gemma 4 as such is not blocked;
it is the sanctioned Gemma line. Reading Gemma 3 outputs from
existing HF datasets we do not own is not a shipping artefact and
is not covered here.

**Related allowlist note (2026-09-05):** operator confirmed
verbatim _"edit score's qwen3-vl is allowedlist"_ — EditScore-7B's
**Qwen3-VL base** is explicitly allowlisted. This is orthogonal to
the Gemma 3 row above (different model family, different vendor);
recorded here so a reader wondering whether the workspace's
`on-device VLM` line is entirely blocked answers "no — the
EditScore Qwen3-VL is the sanctioned VLM base". RFDs 1102 and 2193
name Qwen3-VL as EditScore's fine-tune base; those citations stand.

**Related allowlist note (2026-09-05):** operator confirmed
verbatim _"omnigen2 is allowlisted as is"_ — OmniGen2 (RFD 2183
corpus generator, `interactor-omnigen2`) stays allowlisted with no
carve-out changes; recorded here so a reader sweeping through the
2026-09-05 model allowlist/blocklist directives does not need to
guess whether OmniGen2 was implicitly affected. It was not.

### ONNX Runtime Web and TensorFlow.js are blocklisted as browser inference runtimes

Operator directive 2026-09-05, verbatim: _"onnx runtime web tfjs
is blocklisted"_.

The workspace's inference stack is **ggml** (RFD 2188 canonical
source), linked with ggml's Vulkan backend in the native binary.
A second browser inference runtime would fork the model
conversion path, the quantization story, and the debugging
surface for nothing this workspace needs. TFJS and ORT-Web do
not enter shipping artefacts regardless of backend (WebGL,
WebGPU, or WASM).

**What the row does not cover.** ORT and TFJS as native training
runtimes on the server are not what this row is about; nothing
in the workspace uses them there either, but this row is scoped
to browser inference. Reading someone else's TFJS or ORT-Web demo
to understand a technique is not shipping.

Substitute: ggml with its Vulkan backend, linked into the native
binary as one shared `modules/ggml/` module per RFD 2230.

### WebGPU is blocklisted as a workspace render / compute target

Operator directive 2026-09-05, verbatim: _"wait a second if we're
native we can blocklist webgpu and only use vulkan which has more
quality assurance hours in production"_ + _"vulkan on mac,
windows and linux has more quality assurance hours than webgpu"_.

**Why Vulkan wins on all three targets.** On Linux and Windows,
Vulkan removes one translation layer that WebGPU-native adds. On
macOS the raw hop-count favours WebGPU (Dawn → Metal, one hop vs
MoltenVK's two), but MoltenVK is battle-tested — shipped in
Godot since 3.x, used by every Vulkan macOS game — while Dawn's
macOS backend is much newer. Godot 4's primary renderer is
Vulkan-based (`RenderingDevice` driver); using anything else
means fighting the engine. Production-QA hours: Vulkan 1.0
shipped 2016 (~10 years); WebGPU stable in Chrome late 2023
(~2 years).

**What this blocks.** `Ggml.WebGPU=ON` and any successor flag;
Dawn / wgpu-native as a build dependency; Godot forks whose sole
purpose is a WebGPU renderer. ORT-Web + TFJS WebGPU execution
providers are already covered by the ORT-Web / TFJS row above;
this row generalises to any WebGPU-first inference stack.

**What the row does not cover.** Reading a WebGPU spec or example
to understand a Vulkan concept. WebGPU code on a third-party
site the workspace does not ship (tutorial pages, reference
docs). ggml's Vulkan backend, which is what replaces WebGPU. A
Godot engine fork carrying a WebGPU RenderingDevice driver
alongside Vulkan (RFD 2245, operator directive 2026-09-11) — the
row blocks WebGPU as the _workspace deployment target_, not
WebGPU code inside a Godot engine tree; the atelier binary still
selects Vulkan at boot and the shipping surface stays
`entities-godot-sandbox` with MoltenVK on macOS.

**Substitute:** ggml Vulkan backend + Godot's native Vulkan
renderer + MoltenVK on macOS.

### CorridorKey keys a screen plate, and its licence is non-commercial share-alike

**Asked, 2026-09-08.** The operator asked whether CorridorKey could replace
the matting model that produces the dress-on garment alphas, noting the tool
may be used for dataset generation but not resold as a hosted service. Two
findings, and the first settles it without the second.

**It is not the same task.** CorridorKey takes two inputs: a green or blue
screen plate, and a coarse alpha hint that something else produced. What it
does is unmix the screen colour out of edge pixels, so hair, motion blur and
translucency come out with a straight-colour foreground and a linear alpha.
Isolating a subject on an arbitrary background is a different job, and the
tool does not do it. The garment photographs in the second-hand fashion set
are studio and marketplace product shots on white, grey and room backgrounds;
there is no screen colour to unmix. The repository makes the relationship
plain: it ships a `BiRefNetModule` wrapper as one of its optional AlphaHint
generators, so the matting model is upstream of it, not replaced by it. Its
heavier hint options want about 80 GB of VRAM, which no desk here has.

**The licence propagates.** CORRIDOR KEY LICENCE version 1.0 is the Creative
Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License
plus additional terms that take precedence: no repackaging, redistribution,
sublicensing or resale as a standalone or competing product; no paid API or
inference service, directly or indirectly; and a separate written agreement
required to incorporate the tool into a commercial software package or
inference service. The operator's reading of the resale clause is correct.
The workspace binds tighter than the licence does, in two rows that already
exist. **CC-BY-SA** is refused above for share-alike exposure, and NC-SA is
share-alike with a use restriction on top. **OpenRAIL-M as a generator** is
refused because use restrictions propagate into anything trained on the
output, with passthrough use exempt. A matte that ships inside a CC-BY-4.0
corpus, on both the rank1 and rank3 arms of every dress-on row, is generator
use rather than passthrough. The installer also drives `uv`, refused above
for project environments.

**What this row blocks.** CorridorKey and CorridorKeyBlue checkpoints as a
source of any alpha, matte or mask that reaches a corpus, a published dataset
or a shipped asset; the tool as a dependency of any pipeline in the manifest.

**What the row does not cover.** Reading the repository to understand
screen-colour unmixing. A passthrough pass over screen-plate footage whose
derived mattes are never published or trained on, which the tool's own terms
permit and this row leaves alone; no such footage is in the workspace today.
The GVM and VideoMaMa weights it can optionally call, which carry their own
licences and are out of scope here.

**Substitute:** the matting model already in the dress-on pipeline, pinned to
a revision sha, with the model name, that sha and the input photograph's sha
recorded per matte. RFD 2239 carries the argument in full.

### FFmpeg is blocklisted, and the single-binary export is why

**The licence decides this, not the capability.** FFmpeg can encode CineForm;
`libavcodec/cfhdenc.c` exists and this workspace's own `scripts/cfhd_probe.py`
once drove it with `-c:v cfhd -quality film3+`. Capability was never the
question. FFmpeg is LGPL-2.1-or-later, and what this workspace ships is one
native binary per platform out of a Godot fork, with every module linked in.
The LGPL asks that a user be able to relink the covered library with their own
build. A single statically linked export cannot offer that, so taking FFmpeg
into the shipping tree takes on an obligation we cannot meet.

**The alternative is not a compromise.** The GoPro CineForm SDK is
`Apache-2.0 OR MIT`, matching our own code, and it holds both an encoder and a
decoder, so one dependency covers both directions. RFD 1123 made that choice
and RFD 1137's pair does the work today: `transport-cineform-tui` sends a job,
`interactor-cineform` encodes, `service-cineform` owns the bus and the runtime.
Inside the engine the same codec is `modules/cineform`, a `MovieWriter` and a
`VideoStream` on the fork.

**Operator directive, 2026-09-08, on being asked:** "remember ffmpeg is still
banned." This row was overdue; RFD 1175 had asserted the ban since it was
written and no row carried it, which is exactly the drift
`check_blocklist_detail.py` exists to catch in the other direction.

**Measured on this desk the same day, correcting a claim made an hour
earlier.** "FFmpeg is not on this desk" was wrong. It is not installed and not
on `PATH`, and two runnable copies sit in package caches, reachable by absolute
path: `imageio_ffmpeg`'s bundled build under the `uv` cache and a second under
the rattler cache. The one that runs reports `ffmpeg version
7.1-essentials_build`, configured `--enable-gpl --enable-version3`, and lists
`VF...D cfhd  GoPro CineForm HD` among its encoders. So the cached build is
**GPL**, not the LGPL the argument above is written against, which fails the
test harder rather than softer.

**Nothing in the workspace depends on it, and this row breaks no build.** Every
`ffmpeg` line in `taskweft-nmm-personas`, `tropes-removal-model` and
`voxhammer-upstream`'s lock files is an optional extra of `imageio`'s own
metadata (`extra == 'ffmpeg'`), never a selected package; no `pixi.lock` here
locks an ffmpeg package, and no `.pixi/envs` tree contains the binary. The
caches are residue, not a dependency.

**What this row blocks.** FFmpeg, libav\* and any wrapper over them
(`imageio-ffmpeg`, `av`, `moviepy`) as a dependency of anything the workspace
ships or of any pipeline in the manifest; `ffmpeg` or `ffprobe` invoked as a
build-time or corpus-time tool, because a corpus tool that nobody else can run
is not reproducible and the CineForm pair already runs here.

**What the row does not cover.** Reading FFmpeg's source to understand a
container or a codec. A measurement already recorded that used it, which stays
in the record as a measurement rather than being retracted. A third party's
own use of it outside anything we ship.

**Substitute:** the CineForm SDK for the codec, `interactor-cineform` for
batch encoding, `modules/cineform` for the engine's `--write-movie`, and
Matroska as the container (RFD 1123 measured why, and RFD 2240 restates it).

### Mitsuba 3's CPU variants are blocklisted, and the silent fallback is why

**The number is the argument.** RFD 1137 measured the same 96 frames of a
1024x1024 render two ways: 0.34 seconds a frame on the card, and 78 seconds a
frame through `llvm_ad_rgb`. A factor of 230. The six-shot try-on list is 1,970
frames, which is eleven minutes on the card and about forty-three hours on the
processor. Those are not two settings of one thing; they are a render and a
refusal to render, and only one of them finishes inside a working day.

**What made it a rule rather than a preference is that nothing failed.**
`render_hammersley.py` tried `cuda_ad_rgb`, then `llvm_ad_rgb`, then
`scalar_rgb`, swallowing each exception and printing one line naming the
winner. A desk under memory pressure, a driver hiccup, a card busy with
something else: any of those and the sweep would have kept going on the
processor, for days, producing frames indistinguishable from the fast ones and
a corpus nobody could tell apart afterwards. That is rule 3 again, a silent
skip reading exactly like a pass, and it is the same shape as the DirectML
fallback the CPU row above already argues.

Worse than the recorded numbers suggest: measured on this desk 2026-09-08, the
LLVM backend does not initialise at all (`jitc_llvm_init(): LLVM API
initialization failed`), so the old chain would not have landed on the 78-second
path. It would have fallen through to `scalar_rgb`, which is slower still.

**What this row blocks.** `llvm_ad_*` and `scalar_*` variants as the renderer
for anything that produces a corpus, a published dataset, a shipped clip or a
measurement the workspace reports; and any fallback that reaches them without
saying so. A renderer that cannot get the card stops and names what it tried.

**What the row does not cover.** Measuring the CPU path on purpose, which is
where the 78-second figure came from and is how the factor of 230 is known.
Running the renderer on a desk that has no card, deliberately and with the
variant recorded, which is a different act from drifting onto it. Reading
Mitsuba's source. Everything that is not a render: the interpreter, the mesh
loading, the scene construction and the file writing run on the processor and
always will, exactly as the CPU row above says of orchestration.

**Substitute:** `cuda_ad_rgb` on an owned card, required rather than preferred,
with the variant, the renderer version and the samples per pixel recorded in
the render's own manifest so a corpus states which one made it.

### `giraffe.glb` is blocked because nothing states where it came from

`3-interactor/skintokens-upstream/examples/giraffe.glb` is the auto-rigger's
demo mesh, and it is what first light was measured on -- 51 joints, a
(14807, 51) skin. It is blocked as a **corpus and comparison asset**, not as a
thing to look at.

The repository's `LICENSE` is MIT, "Copyright (c) 2025 VAST-AI-Research". That
is a licence over the code. It is not an assertion that the maintainers hold
rights in a 6.3 MB art asset sitting in `examples/`, and example meshes in
model repos are routinely somebody else's work carried along.

The file itself says nothing. Its glTF asset block is
`{"generator": "Khronos glTF Blender I/O v4.3.47", "version": "2.0"}` -- no
author, no copyright, no licence, no source URL, and an empty `extras`. A
Blender exporter string records the tool, not the provenance.

This is the same standard already applied to the seethrough checkpoints, which
are blocked on "no licence stated" rather than on anything known to be wrong
with them. Absence of a stated licence is the finding; no claim is made that the
asset is encumbered.

**What it costs us is small, which is why this is cheap to honour.** The giraffe
was a smoke test: does the rigger return a skeleton and a skin of the right
shape for a non-humanoid mesh. Nothing downstream depends on that particular
animal, and the numbers taken from it were never a result, only a sign of life.

**The replacement has to be better than a swap.** A demo asset with no ground
truth can only ever answer "did it run". Two things replace it:

- the Khronos glTF sample assets (`RiggedSimple`, `RiggedFigure`) for the
  same smoke test -- that repository exists to be redistributable test data
  and states a licence per model, which is the property the giraffe lacks;
  check the specific model's stated licence before adding it, since they are
  not uniform.
- a **procedurally generated tube** for anything that is supposed to be a
  measurement. A tube around a known bone chain has analytic ground-truth
  weights, so a predicted rig can be scored against the right answer instead
  of against "it produced something". That is a strictly better comparison
  than the giraffe ever was, and it is ours.

### WSL is blocked as a way to run anything, and a real failure is why

Operator directive, 2026-09-12. Not a licence row and not a quality judgement
about WSL. It is blocked because using it hides the defect it is reached for.

The occasion: `cloth-fit`'s published Windows binary would not run. Under WSL
the Linux build ran the same retarget end to end in 81.5 seconds -- about as
long as a microwave takes to reheat a mug of coffee -- and that success is
precisely the problem. It answers "does the solver work", which was never in
doubt, while leaving "does the shipped Windows binary work" untouched. Three
separate Windows defects were sitting behind it:

- the bridge imports `libc++.dll` and `libunwind.dll`, which are llvm-mingw
  toolchain files rather than build outputs and so never reached the artifact;
- the PolyFEM spec directory is compiled in as `D:/a/cloth-fit/cloth-fit/json-specs`,
  the path on the GitHub runner that built it;
- the polysolve specs likewise, under that runner's own CPM cache.

Every one of them is invisible from a Linux run, and a fourth -- `-static-libstdc++`
sending clang's mingw driver after a `libmsvcprt.a` that llvm-mingw does not
ship -- was only found by linking on Windows with the real toolchain.

**The rule.** A Windows binary that only runs under a Linux kernel is not a
Windows binary. When the Windows path fails, fix the Windows path. The desk has
llvm-mingw and MSVC installed and `pixi` declares the rest, so there is a local
build for exactly this.

**The narrow exemption, stated so it is not smuggled wider.** Reaching for a
Linux run to CONFIRM a diagnosis -- to establish that the failure is packaging
rather than the code, before spending a build on it -- is allowed, and that is
what the 81.5 seconds bought here. Shipping it, testing against it, or reporting
a WSL run as evidence the thing works is not.

### `jp.lilxyzw.ndmfmeshsimplifier` is blocked, and the reason is when it runs

Operator directive, 2026-09-12. The package is MIT (lilxyzw, 2024) and vendors
UnityMeshSimplifier, also MIT (Mattias Edlund, 2017-2020), so this is not a
licence row. It is blocked on where it sits in the pipeline.

It is an NDMF plugin: `InPhase(BuildPhase.Optimizing).Run("Simplify meshes")`,
driven by a `NDMFMeshSimplifier` MonoBehaviour carrying a quality slider. The
mesh that ships is therefore not the mesh in the scene, and the polygon count
cannot be read from the avatar -- only from a build.

That is exactly the property removed from this avatar on the same day. Sixteen
feature components were resolved only at build time, so every count was of the
authored scene rather than of what uploads; baking them out is what made the
performance categories directly measurable. Adding a build-time decimator puts
the largest remaining category back behind a build step.

**The technique is not what is blocked.** Quadric error decimation with
blendshape and skin-weight carry-over is a reasonable algorithm for a mesh with
448 shapes. What is required is that the decimation happens once and its output
is written out as an asset, so the shipping mesh is the mesh on disk.

**The sanctioned path is Mitsuba plus MuJoCo. Blender stays blocked with no
exemption** -- a carve-out for it was recorded and withdrawn the same day,
2026-09-12. The substitution is better on the argument the Blender entry was
written on rather than merely different: `mitsuba == 3.9.1` with
`drjit == 1.5.0`, and `mujoco`, are pinned in `pixi.toml` files the next desk
rebuilds, and `3-interactor/motion-bricks-cpp/mujoco/pixi.toml` carries both in
one environment. "Pinned by nothing" was the objection; these are pinned.

The two cover the two things a retopology has to preserve. Mitsuba scores the
SHAPE differentiably, so a candidate mesh is driven towards the original instead
of being eyeballed -- and its CPU variants are themselves blocked, so this runs
`cuda_ad_rgb`. MuJoCo scores the MOTION, the half a still frame cannot show: a
mesh that matches at rest can still deform wrongly once the bones move
([[openusd-intermediate-and-quad-recovery]]). Blendshape transfer is the hard
part and neither tool does it for free.

**Consequence for the polygon budget.** The avatar is 78,154 triangles against a
70,000 limit. 57,666 of those live in eight meshes carrying 530 blendshapes
between them, and 17,282 in seven meshes carrying none. Cutting only the
blendshape-free meshes needs a 47.2% reduction of them, which is a lot to ask of
garment silhouettes; deleting the two inactive meshes first (3,206 triangles)
drops that to 28.6%. The blendshaped meshes stay reachable only through an
edit-time decimator that preserves shapes.
