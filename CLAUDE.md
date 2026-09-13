# Working agreements

Working agreements for every project in the Weftspun workspace, and the
capability rules for the agent that works in them.

The file lives in `weftspun/request-for-discussion` and reaches the workspace
root through `default.xml`:

    <linkfile src="CLAUDE.md" dest="CLAUDE.md" />
    <linkfile src="CITATION.cff" dest="CITATION.cff" />

Two links to two files, each reaching the root under its own name.

It has a repository of its own — `weftspun/dot-claude`, checked out at `.claude`.
What the arrangement buys is at the end under "Why a link after all".

`weftspun/logbook` is archived and its 145 commits are here, alongside the
RFDs. The `logbook-*.md` entries kept their names, so an entry is still
findable by the thing it measured rather than by where it used to live.

Standing constraints follow. Each carries a cost behind it; the incident sits
alongside this file (`KEYPOINTS.md` for the narrative, `PITFALLS.md` for the
recurring failure modes and the guards that catch them).

## Hard Constraints

**Compute.** GPUs the operator owns are the only compute — the local desktop
GPU and Thunderbolt-attached owned eGPUs both count. Rented GPU providers are
blocklisted (see the RunPod and Vast.ai rows below): no budget for per-hour or
per-invocation billing, and no way to run corpora on machines the operator does
not own. Work that matters is pushed when it is produced. Nothing reports
uncommitted results on a local GPU.

**Archive formats.** OpenUSD `.usda` if we want to remain text editable and ZStandard
parquet for bulk storage. **zip is not acceptable**, and neither is gzip;
compress and verify payload hashes before deleting an original.

**usdz is exempt from the zip ban.** A usdz is a STORED zip — the entries are
uncompressed by specification — used as USD's interchange package, so nothing
this rule protects against happens inside one: no compression to silently
corrupt, and the payload crate reads in place without extraction. Decided
2026-08-30, when the canonical ANNY fixture's 317 blendshapes took its text
form to 92 MB and the packaged crate to 23.6 MB. The generators stay the
text-form source of truth; usdz is a delivery container, not an archive.

**Normal form.** Data is in **Essential Tuple Normal Form**: interned
vocabularies, satellite relations rather than nullable columns, **no nulls**, no
derivable columns. A value like `-1` for "no parent" is a value; a NULL is not.

**Data hygiene.** Training data only — validation and test splits are strictly
held out from training, tuning, and selection.

Synthetic data is two classes, and the distinction is the whole rule:

_Constructed_ synthetic is **rendered deterministically from source assets we
hold** — Live2D drawables, ANNY rigs, BVH poses. The labels are true by
construction rather than inferred, the same seed reproduces the corpus, and
nothing was sampled from a learned distribution. This is ordinary training data
and always has been; `syn_data.py`'s Live2D renders are the reference case.

_Generated_ synthetic is **sampled from a generative model** — diffusion
outputs, GAN style transfer, a teacher's predictions. Permitted in a training
corpus only when all four hold:

1. the generating model, checkpoint and prompt/conditioning are recorded with
   the data, so the corpus can be regenerated and its provenance answered later;
2. it is stored and manifested separately from constructed and real data, never
   merged into an undifferentiated pool;
3. it is not the sole distribution for a model that will be deployed on real
   inputs — mix in real or constructed data, because the failure this rule
   exists to prevent is a student that is excellent on its teacher's output and
   mediocre on the world;
4. Evaluation uses real or constructed data only. A model measured on its own
   generation distribution has not been measured.

`EasyDiffusion outputs` and `seethrough PSDs` stay blocklisted below —
those are secondary generation with no recorded provenance, which is
condition 1 failing.

**The blinded holdout.** `coco_person_commercial_val2017` — 523 license-filtered
COCO person images — is a **blinded** validation set. Blinded means more than
unused for gradient steps: it is not inspected while developing, not used to
pick a checkpoint, a hyperparameter, a threshold, or a stopping point, and not
looked at to decide whether an approach is working. A holdout consulted
repeatedly during development has been trained on by hand, just slowly.

It is real photographs, so it satisfies condition 4 above where a generated set
would not. That is precisely why it is worth protecting.

Two corollaries that are easy to violate without noticing:

- **Never generate from it.** If `train2017` feeds a generation pipeline, `val2017`
  must not — an image generated from a held-out photo carries that photo's
  content into training.
- **Anything derived from `val2017` inherits its status.** The COCO-OOD stylized
  sets (`6-datasource/coco-ood-eval`) are `val2017` restyled, so they are
  evaluation-only twice over: derived from the holdout, and generated.

Real photographs validate the pose pipeline, not the layer-decomposition task —
a photograph has no ground-truth `front hair` / `back hair` split. Validating
See-Through itself still needs held-out illustrations, and this set does not
supply them.

**Deployment.** glTF exports carry **pure data only** — skin weights, animation
samplers, morph targets. No runtime modifiers, drivers, constraints, or custom
extensions. An export that only looks right because the consumer runs our code
is not portable.

**Skinning.** Dual-quaternion skinning is **blocklisted**. Delta Mush and Direct
Delta Mush are approved. Note DDM bakes the smoothing but not the pose
dependence, so it suits renders and baked clips and is not an option for live
avatars.

**Pose sources.** From ANNY/SOMA's own pose library, synthetic, or a
licence-clean third-party motion set. No scraped or unlicensed pose references.

Two axes decide it, and both must hold.

**License.** The set carries a readable license permitting commercial use and
derivatives — the same bar `filter_coco_licenses.py` applies to images.
`CITATION.cff` alongside the data, naming the license and the source record, is
the evidence. A set behind a registration form is not license-clean: terms that
cannot be read without accepting them cannot be gated on.

**Role.** A pose may be used as a **control** — conditioning a generation whose
output is then verified back against the pose it was given — or targeted into
an asset we ship. The first is transient: the pose shapes a render and the check
confirms the body matches. The second embeds someone else's motion in a
deliverable, which is what the rule was written to stop. Control use is
permitted for license-clean sets; shipping targeted third-party motion is not,
whatever the license.

The verification is not optional decoration. A pose used as a control and never
checked is a pose we assumed was followed, and `pose-consensus`'s referee exists
to do that checking — fit the generated result and confirm the body matches the
pose that conditioned it.

**Latents.** Stages pass latents; VAE decode happens once, at final output.
Never `encode(decode(z))`.

**Repo layout.** One standalone repo per model, not one repo with many model
folders.

**Sides.** Every repository sits on a side of the hexagon, and the `default.xml`
of the goal manifest it is checked out through is what decides which. There is
**one live goal manifest**, `weftspun/weftspun-keypoint`. A new repository is
placed when it is added, not later: an unplaced project is the drift the six
words exist to stop.

**One live manifest, and a repository is placed when it appears in that
one.** `repo list` and the org's archived set are the two things to read.
`TRELLIS.2`, `Pixal3D`, `VoxHammer` and `MoGe` are pinned at bare commit
SHAs in the manifest; placement is satisfied by the manifest entry,
provenance rides with the SHA.

**Deliverables.** Video-ready assets land as PSD or a video/image intermediate
with `.cff` title and metadata, before any pod tear down. PSD because it carries
lossless vector and raster layers.

## How Measurements Are Reported

Pair every physical measurement with a household-object equivalent. "4.3 mm"
does not tell a reader whether an error matters; "about three stacked pennies"
does. Useful anchors: credit card 0.76 mm, penny 1.52 mm, pencil 7 mm, AAA 10.5
mm, AA 14.5 mm, nickel 21.2 mm, golf ball 42.7 mm, adult wrist 57 mm, soda can
66 mm.

Where a script prints measurements repeatedly, give it a helper rather than
relying on recall.

## How Work Is Verified

These recur often enough to state as rules:

1. **Measure the physical quantity, not the convenient proxy.** The proxy is
   always the one that is easy to read, and it lies at five sites here.
2. **A check that passes on known-broken input is decoration** — it certifies
   the defect. Every gate ships with a negative control asserting the broken
   input fails.
3. **A silent skip reads exactly like a pass.** An unmet precondition is a FAIL.
   Unchecked things are named and counted, never omitted.
4. **A number without a baseline is not a measurement.** Report the floor in the
   same table.
5. **State the detection floor.** A sampled check only sees defects larger than
   ~3/n. For a _fixed_ population, enumerate rather than estimate.
6. **Conventions are data.** Parse rotation order, up axis, and units; never
   assume them.
7. **Bugs live at interfaces**, not inside components. Name the interfaces and
   check each.

## How Prose Density Is Gated

Trope density does not rise. `scripts/check_tropes.py` scans `rfd/*/README.md`,
`rfd/*/DETAILS.md`, and `logbook/*.md`, counts hits for the tells the
`prose-detrope` subagent removes most often (em-dash joins, counting
announcements, reasoning leaks, pompous copulas, `exact` intensifiers on
soft nouns), and refuses a commit that raises a changed file's hits per
non-blank line. Same diff-based shape as `check_comment_ladder.py`; the
working agreements (`CLAUDE.md`, `BLOCKLIST.md`, `PITFALLS.md`,
`KEYPOINTS.md`) stay off it because they carry named tells verbatim.

    python scripts/check_tropes.py                              # report
    python scripts/check_tropes.py --base origin/main           # gate
    python scripts/check_tropes.py --self-test                  # 8 controls

## How Commit Messages Are Written

Commit subjects on our own repos are sentence-case prose with no
Conventional-Commits prefix. `Add the macOS and Windows release
workflows` and `RFD 2200: ReBAC agent roles as tuples in relationships/
KV` are the shape; `feat: add release workflow` and `chore(deps):
bump` are not. No trailing period. The body, when there is one,
states what the change makes true of the system and why. RFD 2026
carries the argument.

Forks — anything whose git remote points at somewhere other than
`github.com/weftspun/...` — follow the upstream's convention. A
Conventional-Commits upstream gets Conventional-Commits subjects on
its fork here, because the fork's diff goes back one day and needs
to fit.

`scripts/check_commit_style.py` gates it. Detects the fork case from
git remotes and skips silently there. Both directions carry a
control (six subject controls, four URL-classification controls).

    python scripts/check_commit_style.py --base origin/main
    python scripts/check_commit_style.py --self-test

## How Session-Bundle Work Is Landed

Coordinator-authored session-bundle work lands as **one PR**, not
as N parallel branches. What this rule prevents is splitting a
single coordinated session's work across parallel branches that
then race each other into rebase-conflict cascades. Unrelated
in-flight PRs on separate subjects are fine.

Operator directive 2026-09-05, verbatim: _"can you bundle the
merges together and allow admin merging"_. This rule is the
bundle half.

**This repository has no ruleset and no branch protection.**
Earlier text here described a merge queue under ruleset 21131040
with `MERGE` method and `ALLGREEN` grouping, and an admin bypass
at `RepositoryRole 5`. The repository carries zero rulesets and
that id returns 404, so nothing required a green check and
nothing was bypassed. Retracted 2026-09-12, measured with
`scripts/check_rulesets.py`, which now fails when a document
names a ruleset the repository does not carry.

Merging is therefore unguarded, and the cost is recorded rather
than implied: RFD 2245 landed with six of nine checks red and
stopped `mix rfd.render` for all 318 RFD sources until it was
trimmed. Read the checks before merging, because nothing else
will.

A queue is not the fix while the checks themselves do not run.
Every pull request on 2026-09-11 and 2026-09-12 sat `queued` on
GitHub-hosted runners, several for over half an hour, and an
ALLGREEN queue waits on exactly those checks. Enabling one now
would stop every merge rather than gate it. Runner capacity
comes first; PITFALLS 11 carries the rest of the argument.

A session bundle is a set of changes that carry each other's
reasoning: three RFDs whose bodies cite each other, a blocklist
row plus its BLOCKLIST.md section, a SERIALS backfill for the
RFDs added in the same session. Landing them separately means
one PR lands the row while another lands the section, and the
`check_blocklist_detail.py` gate is red for the interval between.
Bundling puts them on one PR that lands together or not at all.

What this rule does not cover: unrelated in-flight work by peers
(HERO's Kimodo port, ANCHOR's shepherd gates, SIDEKICK's Gemma-4
measurements) still opens its own PR. This rule is about
coordinator-authored work that shares a subject, not about
serializing every PR through one branch.

## How Our Own C++ Is Typed

C++ we write uses no `auto`. The code this workspace writes in C++ sits at
wire and ABI edges — NIFs, bus endpoints, VFS shims — where the reader should
see the struct being held, not deduce it from the initializer. The rule is
prospective: code written before it, and vendored code, is not swept in.

`scripts/check_no_auto.py` gates it, keyword-only — comments, strings and
identifiers like `autopilot` do not count, and both directions carry a
control.

    python scripts/check_no_auto.py <paths...>
    python scripts/check_no_auto.py --self-test

## Trademarks Stay Out of Shipping Artifacts

Third-party trademarks do not appear in code, comments, docstrings, RFDs,
logbook entries, or user-facing prose. A shipping artifact that names one
invites a legal question the workspace does not need and reads as if the
document is claiming affiliation. Describe the underlying design language,
technique, or genre by its generic terms — "isometric tactical menus,"
"parchment chrome with beveled corners," "wish-altar gacha," "social VR
avatar hub" — and leave the branded exemplar out. Comparisons in a private
conversation with the operator are fine; the moment a decision lands in a
file, the trademark comes out.

If a rewrite in generic vocabulary would lose the meaning, the meaning
was leaning on the mark.

## How Our Own Code Is Commented

Use comments extremely sparingly. Most should be at the request of the user.
When something warrants one, keep it to one or two lines: what the code does and
why it is necessary. No background narrative, no replaying the investigation or
the failure mode, nothing a test name or the commit message already says. If a
comment needs a paragraph, make the code clearer instead.

This covers code and the specifications that describe it. It does not cover the
documents — an RFD, a logbook entry and this file carry the measurement and the
retraction that produced them, and that is what they are for.

`check_comment_ladder.py` measures it. The rungs are 3, 5, 10, 15, 20, 25, 30,
35 and 40 per cent, and a changed file may not leave the rung it sits on. The
3% rung is the median comment density of `entities-godot-main` measured on
2026-08-31 across 1341 files of 200+ non-blank lines with vendored trees
excluded (median 3.27%, rounded down; mean 5.01%, p90 10.55%, p95 14.65%). It
replaces a 12% rung floated earlier the same day: 12% was an intuition, 3% is
the measurement, and a rung derived from what a peer codebase actually holds
carries an argument the intuition did not.

**Add a comment line and the density you already had is the ceiling.** A file at
30.2% sits on the 30% rung, and the gap up to 35% is where that rung ends rather
than room to grow into. Density holds or falls.

The rung covers the case where the ratio rose without a comment being added.
Density is comments over non-blank lines, so deleting code raises it: 40 comment
lines over 180 code lines is 18.2%, and deleting 60 lines of code makes the same
file 25.0%. Failing that commit would teach people to pass the gate with
`--no-verify`, so the rung leaves room for it, and the control `deleting code
past the rung is rejected` bounds how much.

A new file enters at 10 per cent, the rung `scripts/mi_bench.py` already
occupies.

**Docstrings count.** Across this repository's 31 Python and Elixir files over
100 lines, counting `#` alone puts the median at 7.4%; counting docstrings puts
it at 25.1%. That is rule 1 above: the easy proxy understated by more than three
times, and a gate counting `#` alone is satisfied by moving the paragraph into a
docstring.

    python scripts/check_comment_ladder.py --baseline
    python scripts/check_comment_ladder.py --self-test

## How Other People's Codebases Are Edited

Where a weftspun file does carry the measurement and the retraction that
produced it, it is commented accordingly. Another project did not ask for that.
Pushing our density into theirs makes a diff that reads as noise to the people
who maintain it.

So a change matches the density of the code it edits.
`check_comment_density.py` measures it and fails when a changed file
goes above the greater of its own density before the change and the p90 of its
peers. Peers are files with the same extension under the same top-level
directory.

    python check_comment_density.py <repo> --base <ref> --self-test

Measured on godotengine/godot at 4.7.0-beta, across the 68 files in `servers/`
over 200 lines: median 3.7%, mean 4.6%, p90 9.3%. A first edit to
`movie_writer.cpp` took that file from 6.1% to 10.4% and the gate now rejects
it.

The reasoning does not disappear, it moves. A commit message and a pull request
description carry it, which is where those projects already keep it.

**Configuration goes in the host's own mechanism, not the environment.** An
environment variable is invisible to the editor, absent from the project file,
and gone the next time somebody runs the thing. Godot has project settings, so a
Godot change uses `GLOBAL_DEF` and a GDExtension registers under its own group.
The same rule holds anywhere else: use the configuration system the project
already has.

## How the Logbook Is Written

An entry records the **measurement** rather than the intention, and clips the
experimental apparatus — enough to re-run the test, not merely its conclusion.

**Retractions stay in place, next to what they retract.** Several entries exist
only to withdraw an earlier number, and that is the point: a reader who knows
which roads are dead ends is better off than one who only knows the current
answer.

Documentation carries the same obligation. Where a document states a number or a
rule, that statement should be machine-checked against live code, so drift fails
a command rather than being discovered six months later.
`request-for-discussion/scripts/check-rfd-structure.py` is the reference case:
it reads its state list and its README line limit out of RFD 1000 rather than
restating them, so the document and the gate cannot disagree.

## How Retracted RFD Topics Are Deleted

A retracted RFD topic deletes its body. Conventional deletion is the
default — git history preserves every dropped paragraph, and the
successor RFD's `## Related` section preserves the "why". A retracted
RFD file stays on disk because its SERIALS entry names it; the file
shrinks to title + `**State:** abandoned` + canary, no explanatory
prose. Amendment paragraphs are not stacked mid-body across reversals;
the RFD is rewritten to say the current answer.

**Keep a specific-citation pointer** only when a live citation from
outside the workspace's git history names the retracted section by its
wording, and the successor RFD does not carry the same claim. That is
rare. When kept, the pointer is one line, of the form:

    **Lumina2 distillation as primary:** retracted 2026-09-04, see
    `logbook-lumina2-distill-n1000-shelved.md`.

**The logbook** is the one carve-out: it keeps its "retractions stay in
place next to what they retract" shape because it records events, and
the retracted measurement is itself an event.

## How AI-drafted RFDs are attested

An RFD drafted with AI help carries one sentence, verbatim, in either its
README.md or its DETAILS.md:

    This RFD was drafted by an AI and read by a human before it shipped.

The sentence is a compliance canary in the M&M's-clause sense. A session that
read `CLAUDE.md` before drafting adds it; one that skipped `CLAUDE.md` will not,
and `scripts/check_rfd_canary.py` fails the CI job on the omission. The gate
scopes to RFD directories that did not exist on the base branch, so an existing
RFD edited later is outside it.

An RFD drafted alone by a human, without an AI in the loop, carries the human
counterpart instead:

    This RFD was drafted by a human without AI help.

The gate accepts either sentence and rejects a directory with neither, so the
attestation stays truthful in both directions. A misspelled sentence is
rejected, which is what a self-test control asserts.

This is attestation, not attribution. It records what happened to the
document, not who wrote the current line. A human who edits an AI-drafted
RFD keeps the AI sentence in place because the drafting did happen; the
byline separately stays where git records it.

## How Project READMEs Are Bounded

A project's README opens with the tagline a reader sees before scrolling.
`scripts/check_project_readme_length.py` bounds the first non-blank line at
144 characters. A tagline is small on purpose: it forces the writer to pick
what the project is rather than hedge.

Silent on projects with no README, counted so the skip does not read as a
pass; forks are exempt (their first line is upstream's, not ours) with the
exempt list inline in the script.

    python scripts/check_project_readme_length.py
    python scripts/check_project_readme_length.py --self-test

## How Responses Are Bounded

Session budget is finite. A reply carries the answer or the code, not the walk
that produced it — the reasoning is what an RFD, a logbook entry, or a commit
message is for, and none of the three is a conversation reply. The bound is
3 sentences or 60 words, whichever the answer fits (about 20 words a
sentence, matching a comfortable spoken clause); a code change ships as the
modified block, not a full-file rewrite.

The bound holds against style pressure in both directions. A run that
summarises what it did in the last five turns has spent budget the next five
turns will need; a run that pads a one-line answer into a paragraph has done
the same. Where a check or a measurement lives in a file, cite the file
rather than restate what it says.

This bound does not cover flagging — a suspicious edit, an unmet precondition,
or a check that would pass on known-broken input is named and counted, never
elided to fit the cap. Rule 3 in _How Work Is Verified_ settles that: a silent
skip reads exactly like a pass.

## How the Merge Policy Is Checked

A gate that is red at merge time stops nothing. RFD 2245 merged with six of
nine checks failing; its README rendered to 55 lines against RFD 1000's 40,
the DSL validates on module load, and all 318 RFD sources stopped rendering
until it was trimmed. Three later pull requests merged with all nine checks
still queued. The gates were correct throughout and none of them was
consulted.

`scripts/check_rulesets.py` reads every ruleset id named in this file and
in `PITFALLS.md` and asks the repository whether it carries them, so a
ruleset that is deleted or never created fails a command instead of leaving
two documents asserting a merge policy nothing applies. Reading the claim
out of the document rather than restating it is the same shape as
`check-rfd-structure.py` reading its line limit out of RFD 1000.

A retraction is not a claim. An id in a paragraph that retracts it stays
readable in place, per _How Retracted RFD Topics Are Deleted_, and the gate
passes over it. Recreating that ruleset means deleting the retraction, which
is what makes the claim live again.

An unreadable API is a FAIL, never a skip; nine controls carry both
directions.

    python scripts/check_rulesets.py --self-test
    python scripts/check_rulesets.py --repo <owner>/<name>

## Blocklists

Sources excluded from corpora, with the reason:

| source                                                                      | reason                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CMU mocap                                                                   | provenance                                                                                                                                                                                                                                                         |
| Mixamo animation packs                                                      | licensing                                                                                                                                                                                                                                                          |
| posemaniacs                                                                 | third-party pose scraping                                                                                                                                                                                                                                          |
| CC-BY-SA                                                                    | share-alike exposure                                                                                                                                                                                                                                               |
| **OpenRAIL-M** as a _generator_                                             | use-restrictions propagate into anything trained on the output — **passthrough use is exempt**, see below                                                                                                                                                          |
| **FLUX.1**                                                                  | the conditionable half is non-commercial; the permissive half cannot be conditioned — see below                                                                                                                                                                    |
| generators with no licence-clean **depth** control                          | HiDream-I1, SANA — see below                                                                                                                                                                                                                                       |
| **hosted-API generators** as a corpus source                                | Nano-banana / Gemini and any API-only model — condition 1 cannot be satisfied without a checkpoint, see below                                                                                                                                                      |
| DeepFashion                                                                 | re-export of a research-only corpus                                                                                                                                                                                                                                |
| AddBiomechanics `.b3d` as an identity source                                | lab volunteers — narrow and inequitable population                                                                                                                                                                                                                 |
| `caldata_*_jc.parquet`                                                      | pre-cut derivatives; use originals                                                                                                                                                                                                                                 |
| EasyDiffusion outputs, seethrough PSDs                                      | secondary generation                                                                                                                                                                                                                                               |
| **Blender**                                                                 | renders are not reproducible across versions — see below                                                                                                                                                                                                           |
| **Qwen-Image-Edit** (2509/2511)                                             | 20.4B: runs here only quantised, and quantised it corrupts — see below                                                                                                                                                                                             |
| **P3-SAM / Hunyuan3D-Part**                                                 | territory-restricted licence: excludes EU, UK and South Korea — see below                                                                                                                                                                                          |
| **Krea 2 / krea2-turbo**                                                    | revenue-gated licence, and the planned deployment was Q4 — see below                                                                                                                                                                                               |
| **BRIA RMBG**                                                               | gated and non-commercial — see below                                                                                                                                                                                                                               |
| **abliterated weights**                                                     | refusal removal by weight edit, unmeasured elsewhere — see below                                                                                                                                                                                                   |
| `alfredplpl/anime-with-caption-cc0`                                         | hand quality — **images** blocked, captions permitted                                                                                                                                                                                                              |
| **`giraffe.glb`** (SkinTokens example asset)                                | bundled art with no stated provenance; the repo's MIT covers its code — see below                                                                                                                                                                                  |
| **`jp.lilxyzw.ndmfmeshsimplifier`**                                         | operator directive 2026-09-12: decimation deferred to build time, which is the property just removed from the avatar — see below                                                                                                                                   |
| **git submodules**                                                          | a second dependency mechanism `repo status` cannot see — use `default.xml`, see below                                                                                                                                                                              |
| **WSL** as a way to run anything                                            | operator directive 2026-09-12: a Windows binary that only runs under a Linux kernel is not a Windows binary — fix the Windows build, see below                                                                                                                     |
| **`uv` for project environments**                                           | an environment nothing declares and nobody can rebuild — use `pixi`; **an embedded interpreter pinning its deps in source is exempt**, see below                                                                                                                   |
| ~~**tinygrad NVIDIA eGPU** (TinyGPU dext) as compute~~                      | **unblocked 2026-09-03**: compute rule widened to include owned eGPUs; the three failure modes stand and are accepted, see below                                                                                                                                   |
| **onnxruntime GPU providers on macOS**                                      | CoreML EP is the same Metal path Core ML gives; WebGPU EP measured 0.27x of it — see below                                                                                                                                                                         |
| **Apple Neural Engine** as an execution target                              | 2 GiB weight ceiling at 2^31 bytes, against Metal's 8 GiB+ on the same part — see below                                                                                                                                                                            |
| `weftspun/rf-detr-keypoint-data`                                            | **val2017-derived** — carries the whole blinded holdout, and 78% of it is licence-dirty. Validation only, never training. See below                                                                                                                                |
| **ggml** and GGUF as a model format                                         | GGUF carries no graph to convert out of — **a vendor's own runtime and an on-device single binary are exempt**, see below                                                                                                                                          |
| **IREE** as a build target                                                  | a compiler rather than an execution provider, and it is not XLA — see below                                                                                                                                                                                        |
| `24yearsold/metricdepth3d_tmp`                                              | gated: HTTP 401, no readable licence and no model card — see below                                                                                                                                                                                                 |
| **See-Through checkpoints**                                                 | every one states no licence, and the depth one derives from OpenRAIL++-M — see below                                                                                                                                                                               |
| **SMPL and every variant** as a body model                                  | non-commercial without an MPG licence; SOMA-X to ANNY is the sanctioned bypass — see below                                                                                                                                                                         |
| **AMD XDNA NPU** as an execution target                                     | a second accelerator toolchain, nothing measured and no runtime installed — see below                                                                                                                                                                              |
| **the CPU** as a model execution target                                     | orchestration and the **DFC runtime** are exempt; a silent DirectML fallback is the trap — see below                                                                                                                                                               |
| **Mermaid** as a published-figure format                                    | the layout solver owns the picture and the house sheet cannot reach it — hand-authored inline SVG instead, see below                                                                                                                                               |
| **LLaDA** (LLaDA-o, iLLaDA, LLaDA-1.5)                                      | block diffusion measured 5.76s / 64 tokens — 25x too slow for real-time avatar; RFD 1170 presence loop targets sub-500 ms — see below                                                                                                                              |
| **RunPod** as rented compute                                                | no budget for per-invocation billing; `spot-broker` and `transport-runpod` archived alongside this row — see below                                                                                                                                                 |
| **Vast.ai** as rented compute                                               | no budget for per-hour billing; `spot-broker` and `vast-market-snapshots` archived alongside this row — see below                                                                                                                                                  |
| **AnimeGAN** (v2, v3) as a photo-to-anime stylizer                          | non-commercial licence; checkpoints trained on copyrighted films; CycleGAN is the on-hand substitute — see below                                                                                                                                                   |
| **bnb NF4 4-bit** as a QAFT / QAT path                                      | bf16-adapter-over-nf4-base pattern; adapter never sees quantization; slow-kernel fallback on non-64-aligned shapes (OmniGen2's 2520); real QAT with quantized forward instead — see below                                                                          |
| **Post-quantization fine-tuning** (quantize-first, adapt-after)             | trains an adapter that never sees quantization; ships as two files at two precisions. Real QAT with quantized forward during training instead — see below                                                                                                          |
| **Post-training quantization** (train-then-quantize, no QAT loop)           | GPTQ / AWQ / HQQ / Torchao 4-bit as final passes over a bf16 checkpoint — the shipped 4-bit weights were never optimized against quantization noise. Real QAT — see below                                                                                          |
| **rf-detr object detection**                                                | keypoints and segmentation heads are approved; object-detection head is not a workspace task and the shipped weights invite scope drift into a task RFD 1102 does not include — see below                                                                          |
| **Lumina-Image-2.0 as an image-edit base**                                  | no native image-input path; every path we tried through SDEdit under-scored on held-out. OmniGen2 on the same backend is approved — see below                                                                                                                      |
| **SDEdit** as an image-edit sampler                                         | source-noise blend + text-conditioned denoise: measured 0/20 wins on shard-90 held-out at 30 steps, both arms mostly zero. Use native image-input pipelines instead — see below                                                                                    |
| **Apple's convention name for the 52-target facial-action blendshape set**  | trademark; naming it in shipping artifacts implies affiliation the workspace does not have; the shapes themselves are permitted (anny ships them under `data/faceunits01/`), only the naming is blocked. FACS action-unit vocabulary is the substitute — see below |
| **Three.js** as an in-browser 3D runtime                                    | JS/npm-runtime lock-in on a stack we don't fully control; the same scene ships from `entities-godot-sandbox` as a native binary with Godot's Vulkan renderer (MoltenVK on macOS); RFD 1170 already picks Godot over three.js — see below                           |
| **Gemma 3** family as an on-device model                                    | operator directive 2026-09-05: Gemma 3 blocklisted, Gemma 4 allowlisted; workspace ships against the Gemma 4 line (E2B / E4B) only — see below                                                                                                                     |
| **ONNX Runtime Web** and **TensorFlow.js** as in-browser inference runtimes | operator directive 2026-09-05: both blocklisted as browser inference runtimes; the workspace's inference path is ggml (RFD 2188) with the Vulkan backend on native, not a second JS-runtime stack — see below                                                      |
| **WebGPU** as a workspace render / compute target                           | on native, Vulkan has ~10 years of production QA vs WebGPU's ~2, is Godot 4's primary renderer, and skips a translation layer on Linux/Windows (MoltenVK's two hops on macOS are battle-tested vs Dawn's newer Metal backend) — see below                          |
| **CorridorKey** as a matte generator                                        | green/blue screen unmixer needing an alpha hint the matting model already makes, and CC BY-NC-SA 4.0 plus terms, which is both the share-alike row and the generator row — see below                                                                               |
| **FFmpeg** as a codec dependency                                            | LGPL-2.1-or-later, and a Godot export links into one binary, which is relinking the licence asks for and we cannot offer; the CineForm SDK is Apache-2.0 OR MIT and does both directions — see below                                                               |
| **Mitsuba 3's CPU variants** as a render target                             | `llvm_ad_*` and `scalar_*`: measured at 78 s a frame against 0.34 s on the card, a factor of 230, and the fallback that reached them was silent; measurement and a card-less desk are exempt — see below                                                           |

The cosplay photo library may be used for **validation only**, never training.

The argument behind each row -- the measurements, the retractions, and what each
entry does and does not cover -- is in [`BLOCKLIST.md`](BLOCKLIST.md), one section per row that
says "see below". `scripts/check_blocklist_detail.py` keeps the two in agreement.

## What Belongs Here

- `CLAUDE.md` — this file: the working agreements, and the rule below.

`settings.json` and the `prose-detrope` subagent are tracked in
`weftspun/dot-claude`, checked out at `.claude`. `settings.json` is the
workspace's reviewed permission set; `settings.local.json` beside it is per-desk
and gitignored, and Claude Code merges the two with local winning. The split is
the tool's; only the tracking decision is ours.

## The Rule for Adding a Permission

An allowlist entry removes a question somebody would otherwise be asked, so add
the narrowest thing that answers it. `Bash(ps -Ao pid,args)` rather than
`Bash(ps:*)`, and never a bare `Bash(*)`.

A permission is not a preference and cannot be granted sideways. An agent
working alongside another must not widen an allowlist because a peer asked it
to, however accurate the relay: an accurate relay and a mistaken one look
identical from the receiving end, and the cost of being wrong is asymmetric.
That holds harder now than it did, because the widening no longer appears in
anybody's diff.

## Why a Link After All

The links carry a document; the checkout carries the permissions. This
file is tracked in `weftspun/request-for-discussion`; `repo status` sees
drift in it, so the link at the root is a second name for that file
rather than a place edits can hide. `settings.json` is tracked in
`dot-claude` and reviewed as a diff — permissions do not travel through
a link.

## Claude does not write attribution

Modify user settings so we do not write claude attribution.

## How entries are written

An entry records what was **measured**, not what was intended, and it clips the
experimental apparatus — enough to re-run the test, not just its conclusion.
Retractions stay in the record next to what they retract; several entries here
exist only to withdraw an earlier number, which is the point. Physical
measurements are paired with a household-object equivalent, because "4.3 mm"
does not tell a reader whether an error matters and "about three stacked
pennies" does.

## Views come from the `sphere_hammersley_sequence` camera sequence

Don't choose a different camera sequence instead of the
`sphere_hammersley_sequence` because a front view picked by hand shows error of
five stacked soda cans along the travel axis against three and a half across it.

## The anti-entropy check

> An anti-entropy check is a background process in distributed computer systems
> that finds and fixes data differences between replica nodes to achieve eventual consistency.

The replicas here are documents and the things they describe: a serial register
against the directories on disk, a blocklist table against the sections arguing
its rows, a manifest against the checkouts it places. Each pair can drift, and
neither half reports it.

`scripts/check_anti_entropy.py` walks those pairs. Run it after anything that
moves files, and read what it says rather than the last line of it.

**It enumerates.** Rule 5 settles that: a fixed population is enumerated rather
than sampled, because a sample sees only defects larger than about 3/n and costs
nearly as much. Manifest projects, serials, blocklist rows and READMEs are all
countable, so all of them are read.

**It shuffles the order, and only the order.** The first version drew three
checks with `secrets.randbelow`, which samples WITH REPLACEMENT: one run returned
two distinct checks from three draws, and nothing bounds how long an item goes
unvisited. A shuffled full pass visits every item once and still surfaces
anything order-dependent. The pass asserts its own coverage.

**Every counter carries a control.** A counter that has never found a
planted row has yet to show it can find a real one.
